import os
import sys
import traceback
import asyncio
import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler,
)
import json
import logging
import asyncio
from datetime import datetime
from utils import split_message
from collections import defaultdict
from typing import List
from dotenv import load_dotenv

import aiohttp
import pytz
import httpx
import requests
from dateutil import parser
from pytz import timezone, UTC
from pytz import timezone as pytz_timezone

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import Forbidden
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from cricket_api import (
    get_today_matches,
    get_fantasy_xi,
    get_teams_list,
    get_next_matches,
)

# Load environment variables once
load_dotenv()
CRICKDATA_API_KEY = os.getenv("CRICKDATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("CRICKDATA_API_KEY:", CRICKDATA_API_KEY)
print("TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Quiet HTTPX logs

# Match status emojis
STATUS_EMOJIS = {
    "LIVE": "🟢",
    "COMPLETED": "🔴",
    "UPCOMING": "🟡",
    "UNKNOWN": "⚪️",
}

# Team flag emojis (add more as needed)
FLAG_EMOJIS = {
    "India": "🇮🇳",
    "Pakistan": "🇵🇰",
    "Australia": "🇦🇺",
    "England": "🏴",
    "New Zealand": "🇳🇿",
    "South Africa": "🇿🇦",
    "Sri Lanka": "🇱🇰",
    "Bangladesh": "🇧🇩",
    "Afghanistan": "🇦🇫",
    "West Indies": "🌴",
}

# Team IDs and Names
TEAM_IDS = [
    2, 96, 27, 3, 4, 5, 6, 9, 10, 11, 12, 13, 71, 72, 77, 161, 185,
    190, 287, 298, 300, 303, 304, 343, 527, 529, 541, 44, 26, 7, 8,
    14, 15, 23, 24, 25, 675,
]

TEAM_NAMES = {
    2: "India",
    96: "Afghanistan",
    27: "Ireland",
    3: "Pakistan",
    4: "Australia",
    5: "Sri Lanka",
    6: "Bangladesh",
    9: "England",
    10: "West Indies",
    11: "South Africa",
    12: "Zimbabwe",
    13: "New Zealand",
    71: "Malaysia",
    72: "Nepal",
    77: "Germany",
    161: "Namibia",
    185: "Denmark",
    190: "Singapore",
    287: "Papua New Guinea",
    298: "Kuwait",
    300: "Vanuatu",
    303: "Jersey",
    304: "Oman",
    343: "Fiji",
    527: "Italy",
    529: "Botswana",
    541: "Belgium",
    44: "Uganda",
    26: "Canada",
    7: "United Arab Emirates",
    8: "Hong Kong",
    14: "Kenya",
    15: "USA",
    23: "Scotland",
    24: "Netherlands",
    25: "Bermuda",
    675: "Iran",
}

def get_flag(team_name: str) -> str:
    """Return flag emoji or a default icon if missing."""
    return FLAG_EMOJIS.get(team_name, "🏏")

def format_match_status(status: str) -> str:
    """Return a colored emoji for match status."""
    return STATUS_EMOJIS.get(status.upper(), STATUS_EMOJIS["UNKNOWN"])

HEADERS = {
    "X-API-Key": CRICKDATA_API_KEY,
}
import json
import logging
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import ContextTypes

# Example function to fetch today matches using updated API URL & headers
async def fetch_today_matches():
    url = "https://api.cricketdata.org/v1/match/today"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                print("📅 Today's matches API response:")
                print(json.dumps(json_data, indent=2))
                return json_data
            else:
                logger.error(f"Error fetching today's matches: {response.status}")
                return None

def extract_all_teams_players(data: dict) -> dict:
    """
    Extracts players grouped by team from the match data.

    Returns:
        Dict[team_name, {playingXI: list, bench: list}]
    """
    result = {}

    teams = data.get("team", [])
    for team in teams:
        team_name = team.get("teamName") or "Unknown Team"
        players = team.get("players", {})

        team_data = {"playingXI": [], "bench": []}

        for player in players.get("playingXI", []):
            team_data["playingXI"].append(player.get("fullName", "Unknown"))

        for player in players.get("bench", []):
            team_data["bench"].append(player.get("fullName", "Unknown"))

        result[team_name] = team_data

    return result


async def show_all_teams_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /teams command triggered")
    match_id = "74836"  # TODO: make dynamic
    url = f"https://cricketdata.org/api/v1/matches/{match_id}"  # Confirm exact URL with API docs

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=HEADERS)

        if response.status_code != 200:
            await update.message.reply_text(f"❌ API Error: {response.status_code}")
            return

        data = response.json()
        print("🔍 Teams API response:")
        print(json.dumps(data, indent=2))

        teams = {}

        # Adjust parsing to CricketData.org response structure:
        for team in data.get("teams", []):
            team_id = team.get("id")
            team_name = team.get("name")
            teams[team_id] = {"name": team_name, "playingXI": [], "bench": []}

            players = team.get("players", [])
            for i, player in enumerate(players):
                pname = player.get("name", "Unknown")
                if i < 11:
                    teams[team_id]["playingXI"].append(pname)
                else:
                    teams[team_id]["bench"].append(pname)

        message_parts = []
        for team in teams.values():
            part = f"🏏 *{team['name']}* - Playing XI:\n"
            part += "\n".join(f"• {p}" for p in team["playingXI"])
            if team["bench"]:
                part += f"\n\n🪑 *Bench:*\n"
                part += "\n".join(f"• {b}" for b in team["bench"])
            message_parts.append(part)

        message = "\n\n".join(message_parts)
        if not message.strip():
            message = "⚠️ No players found for this match."

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logging.exception("Error in show_all_teams_players")
        await update.message.reply_text(f"❌ Exception: {e}")


async def get_matches() -> dict | None:
    """
    Fetches live matches data from CricketData.org API.

    Returns:
        Parsed JSON dictionary on success, None on failure.
    """
    url = "https://cricketdata.org/api/v1/matches/live"  # Confirm this endpoint

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=HEADERS)

        logging.info(f"[get_matches] API Status: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"❌ Error fetching data: {response.text}")
            return None

        data = response.json()
        print("📄 FULL MATCH DATA:")
        print(json.dumps(data, indent=2))
        logging.debug("📄 FULL MATCH DATA:\n%s", json.dumps(data, indent=2))

        return data

    except Exception:
        logging.exception("⚠️ Exception while fetching matches")
        return None


async def get_upcoming_matches() -> str:
    """
    Parses and returns a formatted string of upcoming matches.

    Returns:
        A markdown string to send in Telegram.
    """
    data = await get_matches()
    if not data or "typeMatches" not in data:
        return "⚠️ Couldn't load match data."

    now = datetime.utcnow()
    upcoming_matches = []

    try:
        for match_type in data.get("typeMatches", []):
            for series in match_type.get("seriesMatches", []):
                for match in series.get("matches", []):
                    match_info = match.get("matchInfo", {})
                    state = match_info.get("state", "").lower()
                    start_date_ms = match_info.get("startDate")

                    if not start_date_ms:
                        continue

                    match_time = datetime.utcfromtimestamp(int(start_date_ms) / 1000)

                    if match_time > now and "upcoming" in state:
                        team1 = match_info.get("team1", {}).get("teamName", "Team A")
                        team2 = match_info.get("team2", {}).get("teamName", "Team B")
                        venue_info = match_info.get("venueInfo", {})
                        venue = venue_info.get("ground", "Unknown Venue")
                        city = venue_info.get("city", "")
                        formatted_time = match_time.strftime("%d %b %Y %H:%M UTC")

                        upcoming_matches.append(
                            f"🆚 *{team1}* vs *{team2}*\n"
                            f"📅 {formatted_time} | 🏟️ {venue}, {city}"
                        )
    except Exception:
        logging.exception("⚠️ Error while processing upcoming matches")

    if not upcoming_matches:
        return "📭 No upcoming matches found."

    return "📅 *Upcoming Matches:*\n\n" + "\n\n".join(upcoming_matches)

import logging
from datetime import datetime, timezone
from dateutil import parser
from typing import List
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

# Centralized error handler for all exceptions in handlers
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error_type = type(context.error).__name__
    error_msg = str(context.error) or repr(context.error)

    logging.error(f"❌ Error in handler: {error_type} → {error_msg}")
    logging.error("📜 Traceback:", exc_info=context.error)

    # Optional: Send detailed error only to admins or in DEBUG mode
    user_message = "⚠️ Something went wrong. Please try again later."
    DEBUG = True
    if DEBUG and isinstance(update, Update) and update.message:
        user_message = f"⚠️ {error_type}: {error_msg}"

    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(user_message)
        except Exception as e:
            logging.error(f"⚠️ Failed to send error message to user: {e}")

# /start command handler with typing action and error handling
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.send_action(action=ChatAction.TYPING)
    except Forbidden:
        # User blocked the bot, can't send typing action; ignore
        pass

    try:
        await update.message.reply_text(
            "👋 Welcome to *FantasyBot!*\n\n"
            "Type /help to see all available commands.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Forbidden:
        pass  # User blocked the bot, ignore

# /help command handler with typing action
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.send_action(action=ChatAction.TYPING)
        await update.message.reply_text(
            """📖 *Available Commands:*

*`/start`* – Welcome message  
*`/help`* – Show this help message  
*`/today`* – Today's matches  
*`/score`* – Live scores  
*`/teams`* – Playing XIs  
*`/next`* – Upcoming matches  
*`/fantasy11`* – Fantasy XI suggestions  
*`/playerstats <name>`* – Player statistics  
""",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Forbidden:
        pass

# Helper: get match summaries from matches data dict
def get_recent_match_summaries(data: dict) -> List[str]:
    results = []

    for type_match in data.get("typeMatches", []):
        for series in type_match.get("seriesMatches", []):
            series_info = series.get("seriesAdWrapper", {})
            series_name = series_info.get("seriesName", "Unknown Series")
            matches = series_info.get("matches", [])

            for match in matches:
                info = match.get("matchInfo", {})
                team1 = info.get("team1", {}).get("teamName", "TBD")
                team2 = info.get("team2", {}).get("teamName", "TBD")
                status = info.get("status", "Match status unknown")

                start_time = info.get("startDate")
                time_str = ""
                if start_time:
                    try:
                        # Timestamp in ms -> datetime
                        dt = datetime.fromtimestamp(int(start_time) / 1000, tz=timezone.utc)
                        time_str = dt.strftime("%d %b %Y, %I:%M %p UTC")
                    except Exception:
                        try:
                            # Parse ISO or other string format fallback
                            dt = parser.parse(start_time)
                            time_str = dt.strftime("%d %b %Y, %I:%M %p")
                        except Exception:
                            time_str = ""

                if time_str:
                    status += f" (⏰ {time_str})"

                result_line = f"{team1} vs {team2} | {series_name} | {status}"
                results.append(result_line)

    return results
import asyncio
import json
import logging
import aiohttp
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Example synchronous function placeholder (you need to define this)
def get_today_matches():
    # Your existing synchronous logic here
    # Return dict with keys: status and data
    return {
        "status": "success",
        "data": [
            {"name": "Match 1", "teams": ["Team A", "Team B"], "status": "Live"},
            {"name": "Match 2", "teams": ["Team C", "Team D"], "status": "Scheduled"},
        ]
    }

async def today_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Run synchronous function in thread to avoid blocking
        data = await asyncio.to_thread(get_today_matches)

        if data.get("status") != "success" or not data.get("data"):
            await update.message.reply_text("No match data available.")
            return

        matches = data["data"]
        if not matches:
            await update.message.reply_text("No matches scheduled for today.")
            return

        lines = []
        for m in matches:
            name = m.get("name", "Unknown match")
            teams = m.get("teams", ["N/A", "N/A"])
            status = m.get("status", "Status unavailable")

            line = f"*{name}*\n{teams[0]} 🆚 {teams[1]}\nStatus: {status}"
            lines.append(line)

        message = "\n\n".join(lines)
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception:
        logging.exception("Error in today_command_handler")
        await update.message.reply_text("Sorry, something went wrong while fetching matches.")


async def fetch_team_name(team_id: str, api_key: str) -> str:
    """
    Search current matches for a team name by ID using cricapi.
    Returns "Unknown" if not found or error occurs.
    """
    try:
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={api_key}&offset=0"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"❌ API Error {response.status}")
                    return "Unknown"

                data = await response.json()
                if data.get("status") != "success":
                    print("❌ API returned error:", data.get("message"))
                    return "Unknown"

                for match in data.get("data", []):
                    for team in match.get("teamInfo", []):
                        if str(team.get("id")) == str(team_id):
                            return team.get("name", "Unknown")
                return "Unknown"

    except Exception as e:
        print(f"⚠️ Exception for team ID {team_id}: {e}")
        return "Unknown"


async def get_all_matches():
    url = "https://api.cricapi.com/v1/matches?CRICKDATA_API_KEY=06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            print(f"[get_all_matches] API Status: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Error fetching data: {response.text}")
                return None

            data = response.json()
            if data.get("status") != "success":
                print(f"❌ API Error: {data.get('message')}")
                return None

            print("📄 ALL MATCHES DATA:")
            print(json.dumps(data, indent=2))

            return data.get("data", [])

    except Exception as e:
        print(f"⚠️ Exception in get_all_matches(): {e}")
        return None


async def fetch_rankings():
    # Example static/mock data - replace with real API calls
    return {
        "teams": [
            {"rank": 1, "name": "India", "points": 1250},
            {"rank": 2, "name": "Australia", "points": 1180},
            {"rank": 3, "name": "England", "points": 1100},
        ],
        "batsmen": [
            {"rank": 1, "name": "Virat Kohli", "rating": 900},
            {"rank": 2, "name": "Steve Smith", "rating": 890},
            {"rank": 3, "name": "Joe Root", "rating": 870},
        ],
        "bowlers": [
            {"rank": 1, "name": "Jasprit Bumrah", "rating": 850},
            {"rank": 2, "name": "Pat Cummins", "rating": 830},
            {"rank": 3, "name": "Kagiso Rabada", "rating": 820},
        ]
    }
import aiohttp
import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

NEWS_API_KEY = "5c28844499ac4f928a3586860cead8ce"
API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"  # Example API key for cricapi

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (
        "https://newsapi.org/v2/top-headlines?"
        "category=sports&"
        "q=cricket&"
        "language=en&"
        f"apiKey={NEWS_API_KEY}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        if data.get("status") != "ok" or not data.get("articles"):
            await update.message.reply_text("⚠️ Couldn't fetch news right now. Try again later.")
            return

        articles = data["articles"][:5]  # Top 5 news articles
        message = "📰 *Latest Cricket News:*\n\n"

        for article in articles:
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown source")
            url = article.get("url", "")
            message += f"• [{title}]({url}) — _{source}_\n"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text("⚠️ Failed to fetch news due to an error.")
        print(f"Error fetching news: {e}")

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching latest cricket rankings...")

    try:
        rankings = await fetch_rankings()  # Replace with real API call if available

        msg = "🏆 *ICC Cricket Rankings*\n\n"

        msg += "🌍 *Top Teams:*\n"
        for team in rankings.get("teams", []):
            msg += f"{team['rank']}. {team['name']} - {team['points']} points\n"

        msg += "\n🏏 *Top Batsmen:*\n"
        for batsman in rankings.get("batsmen", []):
            msg += f"{batsman['rank']}. {batsman['name']} - Rating: {batsman['rating']}\n"

        msg += "\n🎯 *Top Bowlers:*\n"
        for bowler in rankings.get("bowlers", []):
            msg += f"{bowler['rank']}. {bowler['name']} - Rating: {bowler['rating']}\n"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text("⚠️ Failed to fetch rankings. Please try again later.")
        print(f"Error fetching rankings: {e}")

def search_player_by_name(name):
    url = f"https://api.cricapi.com/v1/players?apikey={API_KEY}&offset=0&search={name}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        players = data.get("data", [])

        if not players:
            print(f"🔍 No player found for: {name}")
            return None

        return players[0]  # Return the first matching player
    except Exception as e:
        print(f"❌ Error searching player {name}: {e}")
        return None

def get_player_stats(player_id):
    url = f"https://api.cricapi.com/v1/playerStats?apikey={API_KEY}&id={player_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        stats = data.get("data", {}).get("stats", {})
        if not stats:
            print("⚠️ No stats found for player.")
            return None

        # Customize format here (e.g., "ODI", "Test", "T20I")
        format = "T20I"
        batting = stats.get("batting", {}).get(format, {})

        return {
            "format": format,
            "matches": batting.get("Mat", "N/A"),
            "runs": batting.get("Runs", "N/A"),
            "average": batting.get("Ave", "N/A"),
            "strike_rate": batting.get("SR", "N/A")
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except ValueError:
        print("⚠️ Failed to parse JSON.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

    return None
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from dateutil import parser
from datetime import datetime
import pytz

from cricket_api import get_today_matches  # async function

IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.UTC

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📡 Fetching fresh TODAY match data...")

    # Await async API call directly (no run_in_executor)
    data = await get_today_matches()

    print("DEBUG: Raw API response:", data)

    if not data or "data" not in data:
        await update.message.reply_text("❌ Could not fetch today's matches.")
        return

    today_date = datetime.now(IST).date()

    matches = data["data"]

    live, upcoming, completed = [], [], []

    for match in matches:
        # Extract teams robustly
        teams = match.get("teamInfo") or match.get("teams") or []
        if isinstance(teams, list):
            if teams and isinstance(teams[0], dict):
                team1 = teams[0].get("name", "Team 1") if len(teams) > 0 else "Team 1"
                team2 = teams[1].get("name", "Team 2") if len(teams) > 1 else "Team 2"
            else:
                team1 = teams[0] if len(teams) > 0 else "Team 1"
                team2 = teams[1] if len(teams) > 1 else "Team 2"
        else:
            team1, team2 = "Team 1", "Team 2"

        line = f"{team1} 🆚 {team2}"

        # Parse match start time
        start_time_str = match.get("matchTime") or match.get("start_time") or match.get("dateTimeGMT")
        time_str = ""
        if start_time_str:
            try:
                start_dt = parser.isoparse(start_time_str)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=UTC)
                start_dt_ist = start_dt.astimezone(IST)
                time_str = start_dt_ist.strftime("%I:%M %p")
                line += f" — 🕒 {time_str}"
            except Exception as e:
                print(f"⚠️ Could not parse time: {e}")

        # Score or summary info
        score_summary = match.get("matchSummaryText") or match.get("score") or ""

        status = (match.get("status") or "").strip().lower()
        print(f"✅ Match found: {line}, Status: {status}")

        if any(word in status for word in [
            "won", "lost", "draw", "tie", "abandoned", "completed",
            "match ended", "no result", "concluded", "beat", "result"
        ]):
            completed.append(f"✅ *{line}*\n 🏆 _{status}_\n 📊 {score_summary}")

        elif any(word in status for word in [
            "live", "running", "in progress", "opt to bowl", "opted to field",
            "won toss", "elected to field", "elected to bowl",
            "fielding", "batting", "first innings", "second innings"
        ]):
            live.append(f"🔴 *{line}*\n 🎯 _{status}_\n 📊 {score_summary}")

        else:
            upcoming.append(f"🟡 *{line}*\n 📅 _{status or 'Scheduled'}_")

    print(f"🟢 LIVE: {len(live)} matches")
    print(f"🕓 UPCOMING: {len(upcoming)} matches")
    print(f"✅ COMPLETED: {len(completed)} matches")

    if not (live or upcoming or completed):
        await update.message.reply_text("📭 No matches for today.")
        return

    message = "*🏏 Matches Today:*\n\n"

    message += "🔴 *Live Matches:*\n"
    message += "\n\n".join(live) if live else " — No live matches.\n"
    message += "\n\n"

    message += "🟡 *Upcoming Matches:*\n"
    message += "\n\n".join(upcoming) if upcoming else " — No upcoming matches.\n"
    message += "\n\n"

    message += "✅ *Completed Matches:*\n"
    message += "\n\n".join(completed) if completed else " — No completed matches."

    # Telegram message chunking (~4000 chars max per message)
    chunks = [message[i:i + 4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")

import aiohttp
import logging
from datetime import datetime
from dateutil import parser
import pytz
from telegram import Update
from telegram.ext import ContextTypes

UTC = pytz.timezone("UTC")
IST = pytz.timezone("Asia/Kolkata")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.cricapi.com/v1/currentMatches?CRICKDATA_API_KEY=06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except Exception as e:
        logging.error(f"❌ Error in /score: {e}")
        await update.message.reply_text("❌ Failed to fetch live scores.")
        return

    matches = data.get("data", [])
    if not matches:
        await update.message.reply_text("📭 No live scores or recent results found.")
        return

    message = "🏏 <b>Live Match Scores:</b>\n\n"
    found = False

    for match in matches:
        status = match.get("status", "").lower()
        if any(keyword in status for keyword in ["live", "won", "stumps", "tied"]):
            team_info = match.get("teamInfo", [])
            team1 = team_info[0].get("name", "Team 1") if len(team_info) > 0 else "Team 1"
            team2 = team_info[1].get("name", "Team 2") if len(team_info) > 1 else "Team 2"

            scores = match.get("score", [])
            score1 = (
                f"{scores[0].get('r', '-')}/{scores[0].get('w', '-')}"
                f" ({scores[0].get('o', '-')}" + " ov)"
                if len(scores) > 0 else "N/A"
            )
            score2 = (
                f"{scores[1].get('r', '-')}/{scores[1].get('w', '-')}"
                f" ({scores[1].get('o', '-')}" + " ov)"
                if len(scores) > 1 else "N/A"
            )

            message += (
                f"<b>{team1}</b> vs <b>{team2}</b>\n"
                f"🔹 {team1}: {score1}\n"
                f"🔸 {team2}: {score2}\n"
                f"📝 {match.get('status')}\n\n"
            )
            found = True

    if not found:
        message = "📭 No live scores or recent results found."

    for chunk in split_message(message.strip()):
        await update.message.reply_text(chunk, parse_mode="HTML")

from datetime import datetime
from dateutil import parser
import pytz
from telegram import Update
from telegram.ext import ContextTypes

# Define timezones
UTC = pytz.UTC
IST = pytz.timezone('Asia/Kolkata')

async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📡 Fetching fresh TEAMS data...")

    # Make sure get_today_matches() is async and defined elsewhere
    data = await get_today_matches()
    if not data:
        await update.message.reply_text("❌ Could not fetch match data.")
        return

    matches = data.get("data", [])
    now_utc = datetime.now(UTC)
    today_utc = now_utc.date()

    upcoming_matches = []
    live_matches = []
    completed_matches = []

    for match in matches:
        match_date_str = match.get("dateTimeGMT")
        if not match_date_str:
            continue

        try:
            match_dt_utc = parser.isoparse(match_date_str).astimezone(UTC)
        except Exception:
            try:
                match_dt_utc = datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
            except Exception:
                print(f"⚠️ Failed to parse date: {match_date_str}")
                continue

        match_dt_ist = match_dt_utc.astimezone(IST)
        match_day_utc = match_dt_utc.date()

        teams = match.get("teamInfo", [])
        if len(teams) >= 2:
            team1 = teams[0].get("name", "Team 1")
            team2 = teams[1].get("name", "Team 2")
        else:
            team1 = "Unknown"
            team2 = "Unknown"

        vs_line = f"🏏 *{team1}* vs *{team2}*"
        time_line = f"🕒 {match_dt_ist.strftime('%d %b, %I:%M %p IST')}"
        entry = f"{vs_line}\n{time_line}"

        if match_day_utc == today_utc:
            status = match.get("status", "").lower()
            if any(keyword in status for keyword in ["live", "in progress", "running"]):
                live_matches.append(entry)
            elif now_utc < match_dt_utc:
                upcoming_matches.append(entry)
            else:
                completed_matches.append(entry)
        elif match_day_utc < today_utc:
            completed_matches.append(entry)
        else:
            # Future matches on other days can be ignored or handled if needed
            pass

    response = ""

    if live_matches:
        response += "🔴 *Live Matches:*\n" + "\n\n".join(live_matches) + "\n\n"
    else:
        response += "📭 *No live matches right now.*\n\n"

    if upcoming_matches:
        response += "⏳ *Upcoming Matches (Today):*\n" + "\n\n".join(upcoming_matches) + "\n\n"
    else:
        response += "📭 *No upcoming matches today.*\n\n"

    if completed_matches:
        response += "✅ *Completed Matches:*\n" + "\n\n".join(completed_matches)
    else:
        response += "📭 *No completed matches.*"

    await update.message.reply_text(response.strip(), parse_mode="Markdown")

import html
import asyncio
from collections import defaultdict
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

import httpx 

async def next_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📦 Fetching upcoming match data...")

    matches_data = get_next_matches()  # sync function assumed; await if async
    if not matches_data:
        await update.message.reply_text("⚠️ Could not fetch upcoming matches.")
        return

    today = datetime.now().date()
    grouped_matches = defaultdict(list)

    for match in matches_data.get("data", []):
        try:
            start_time_str = match.get("date", "")
            if not start_time_str:
                continue

            try:
                match_date = datetime.strptime(start_time_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"⚠️ Could not parse date: {start_time_str}")
                continue

            if match_date < today:
                continue

            team1_raw = match.get("team1", "").strip()
            team2_raw = match.get("team2", "").strip()
            venue_raw = match.get("venue", "Unknown Venue")
            status_raw = match.get("status", "🕒 Time TBD")
            desc_raw = match.get("name", "")

            # Extract teams from title if incomplete
            if not team1_raw or not team2_raw or team1_raw.upper() == "TBC" or team2_raw.upper() == "TBC":
                title_clean = desc_raw.split(",")[0]  # e.g., "India vs Australia"
                title_parts = title_clean.split(" vs ")
                if len(title_parts) == 2:
                    team1_raw, team2_raw = title_parts[0].strip(), title_parts[1].strip()

            if not team1_raw or not team2_raw or team1_raw.upper() == "TBC" or team2_raw.upper() == "TBC":
                continue

            team1 = html.escape(team1_raw)
            team2 = html.escape(team2_raw)
            venue = html.escape(venue_raw)
            status = html.escape(status_raw)
            desc = html.escape(desc_raw)

            flag1 = FLAG_EMOJIS.get(team1_raw, "")
            flag2 = FLAG_EMOJIS.get(team2_raw, "")

            match_info = (
                f"🆚 {flag1} <b>{team1}</b> vs {flag2} <b>{team2}</b>\n"
                f"📍 <i>{venue}</i>\n"
                f"🕒 <code>{match_date} - {status}</code>\n"
                f"📌 <i>{desc}</i>\n"
            )

            grouped_matches[match_date].append(match_info)

        except Exception as e:
            print(f"⚠️ Skipping a match due to error: {e}")
            continue

    if not grouped_matches:
        await update.message.reply_text("📭 No upcoming or today's matches found.")
        return

    message_parts = []
    for date in sorted(grouped_matches.keys()):
        header = f"📅 <b>{date.strftime('%B %d, %Y')}</b>\n"
        matches_text = "\n".join(grouped_matches[date])
        message_parts.append(header + matches_text + "\n")

    full_message = "\n".join(message_parts).strip()

    for part in split_message(full_message):
        await update.message.reply_text(part, parse_mode="HTML")


async def fantasy11(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"
    SERIES_IDS = [
        "d93bf50f-b2ce-4290-b74f-daf9a8c80a80",  # The Hundred Men's
        "9e97eb69-ee99-422b-b413-e54e4d43f8c7",  # The Hundred Women's
        "6a8f17a7-ca70-4775-aeb2-05b155b3bd9b",  # Delhi Premier League
        "67cfd113-c5e6-4631-9dd5-3c1b0540f674",  # Andhra Premier League
        "acf767fe-641d-463a-8dff-b27c7e2f19ea"   # Pakistan tour of West Indies
    ]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            all_matches = []

            for series_id in SERIES_IDS:
                url = f"https://api.cricketdata.org/v1/match_list?apikey={CRICKDATA_API_KEY}&series_id={series_id}"
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = await response.json()
                    if data.get("data"):
                        all_matches.extend(data["data"])
                except Exception as e:
                    print(f"⚠️ Failed to fetch matches for series {series_id}: {e}")
                    continue

            if not all_matches:
                await update.message.reply_text("⚠️ No matches found in available series.")
                return

            best_match = None
            for match in all_matches:
                match_id = match.get("match_id")
                if not match_id:
                    continue

                scorecard_url = f"https://api.cricketdata.org/v1/match_scorecard?apikey={CRICKDATA_API_KEY}&match_id={match_id}"
                print(f"🔗 Fetching scorecard: {scorecard_url}")

                try:
                    score_res = await client.get(scorecard_url)
                    score_res.raise_for_status()
                    score_data = (await score_res.json()).get("data", {})
                    innings = score_data.get("innings", [])
                    if innings and innings[0].get("batsmen"):
                        best_match = (match, innings[0]["batsmen"])
                        break
                except httpx.RequestError as inner_err:
                    print(f"⚠️ Error fetching scorecard: {inner_err}")
                    await asyncio.sleep(1)
                    continue

        if not best_match:
            await update.message.reply_text("⚠️ No recent match with batsmen data found.")
            return

        match_info, batsmen = best_match
        team1 = match_info.get("team1", {}).get("name", "Team 1")
        team2 = match_info.get("team2", {}).get("name", "Team 2")

        top_batsmen = sorted(batsmen, key=lambda x: x.get("sr", 0), reverse=True)[:11]

        message = f"🎯 <b>Fantasy XI</b>\n<code>{team1} vs {team2}</code>\n\n"
        for i, player in enumerate(top_batsmen, 1):
            name = player.get("batsman_name", "Unknown")
            runs = player.get("r", 0)
            balls = player.get("b", 0)
            sr = player.get("sr", 0.0)
            message += f"{i}. {name} - {runs} runs ({balls} balls), SR: {sr}\n"

        for chunk in split_message(message.strip()):
            await update.message.reply_text(chunk, parse_mode="HTML")

    except httpx.ConnectError as ce:
        print(f"🔌 Connection error: {ce}")
        await update.message.reply_text("🚫 API connection lost. Please try again later.")
    except httpx.HTTPError as e:
        print(f"🌐 Request failed: {e}")
        await update.message.reply_text("⚠️ Could not fetch match data due to a request error.")
    except Exception as e:
        print(f"❌ Fantasy XI Error: {e}")
        await update.message.reply_text("🚫 Could not generate Fantasy XI due to an error.")
    
CRICKDATA_API_KEY="06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"

async def playerstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fetch all players (make sure this is async if fetching from API)
    players = await get_all_players()
    if not players:
        await update.message.reply_text("⚠️ Could not fetch player list.")
        return

    # We'll build a message listing all players' stats
    messages = []

    for player in players:
        stats = await get_player_stats(player["id"])
        if not stats:
            continue  # skip players with no stats

        message = (
            f"📊 <b>{html.escape(player['name'])}</b> - Player Stats:\n"
            f"🏏 Matches: <b>{stats.get('matches', 'N/A')}</b>\n"
            f"🧢 Runs: <b>{stats.get('runs', 'N/A')}</b>\n"
            f"🎯 Average: <b>{stats.get('average', 'N/A')}</b>\n"
            f"💥 Strike Rate: <b>{stats.get('strike_rate', 'N/A')}</b>\n"
            "---------------------------"
        )
        messages.append(message)

    if not messages:
        await update.message.reply_text("📭 No stats available for any players.")
        return

    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="HTML")
import json
import traceback
import html
import httpx
from telegram import Update
from telegram.ext import ContextTypes

CRICKDATA_API_KEY="06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"
import httpx
import html
import json
import traceback
from telegram import Update
from telegram.ext import ContextTypes

async def live_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.cricketdata.org/v1/match/live?apikey={CRICKDATA_API_KEY}"

    try:
        print(f"🔍 Requesting: {url}")

        response = None
        for attempt in range(2):  # Try twice
            try:
                async with httpx.AsyncClient(timeout=10, verify=False) as client:  # Set verify=True for production!
                    response = await client.get(url)
                print(f"✅ Attempt {attempt+1} succeeded.")
                break  # Exit retry loop
            except httpx.RequestError as e:
                print(f"⚠️ Attempt {attempt+1} failed: {e}")
                if attempt == 1:  # Last attempt failed
                    raise

        if response is None:
            await update.message.reply_text("❌ No response from API.")
            return

        print(f"📡 Status Code: {response.status_code}")
        print(f"📦 Raw Response: {response.text[:500]}...")  # Print first 500 chars for safety

        if response.status_code != 200:
            await update.message.reply_text(f"❌ Failed to fetch live match data. Status: {response.status_code}")
            return

        try:
            matches_data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            await update.message.reply_text("⚠️ API returned invalid JSON.")
            return

        print("📡 Parsed JSON:", json.dumps(matches_data, indent=2)[:1000])  # limit output size

        message = "📡 <b>Live Matches:</b>\n\n"
        found = False

        for match in matches_data.get("data", []):
            teams_info = match.get("teams", {})
            team1 = teams_info.get("team1", {}).get("name", "Team1") if isinstance(teams_info, dict) else "Team1"
            team2 = teams_info.get("team2", {}).get("name", "Team2") if isinstance(teams_info, dict) else "Team2"
            teams_str = f"{team1} vs {team2}"

            score = match.get("score", "No score available")
            if isinstance(score, dict):
                score = score.get("display", "No score available")
            status = match.get("status", "Unknown status")

            safe_teams_str = html.escape(teams_str)
            safe_score = html.escape(str(score))
            safe_status = html.escape(str(status))

            message += (
                f"🏏 <b>{safe_teams_str}</b>\n"
                f"📊 {safe_score}\n"
                f"🟢 Status: {safe_status}\n\n"
            )
            found = True

        if not found:
            message += "⚠️ No active live matches at the moment."

        await update.message.reply_text(message.strip(), parse_mode="HTML")

    except Exception as e:
        print("❌ Exception in live_matches:", e)
        traceback.print_exc()
        await update.message.reply_text(f"⚠️ Something went wrong: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from telegram import Update
from telegram.ext import ContextTypes

async def matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await fetch_api()
    matches = response["data"]

    if not matches:
        message = "No matches found for today."
    else:
        lines = []
        for match in matches:
            lines.append(f"{match['name']}")
            lines.append(f"Status: {match['status']}")
            lines.append(f"Venue: {match['venue']}")
            lines.append(f"Date: {match['date']}")
            lines.append("")  # blank line for separation

        message = "\n".join(lines)

    await update.message.reply_text(message)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Handle the callback data here
    data = query.data
    await query.edit_message_text(text=f"Button pressed: {data}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Unknown command. Use /help to see available options.")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler(["teams", "team"], teams))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("next", next_match))
    app.add_handler(CommandHandler("fantasy11", fantasy11))
    app.add_handler(CommandHandler("playerstats", playerstats))
    app.add_handler(CommandHandler("live", live_matches))
    app.add_handler(CommandHandler("about", lambda update, context: update.message.reply_text(
        "🏏 FantasyCrick Bot v1.0\nPowered by CricketData & Telegram API\nDeveloper: @YourUsername"
    )))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

import sys
import asyncio
from telegram.ext import ApplicationBuilder

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TELEGRAM_BOT_TOKEN = "8391514200:AAE3DLKQbPiobZTnqUGC4skF3vWdZMe2Isk"

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    register_handlers(app)  # Your function to add all handlers

    app.run_polling()

if __name__ == "__main__":
    main()
