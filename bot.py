import os
import asyncio
import logging
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from cricket_api import (
    get_today_matches,        # ✅ use the correct one you already have
    get_fantasy_xi,
    get_teams_list,
    get_next_matches
)

# ✅ Load environment variables
load_dotenv()

# ✅ Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ API keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")

# ✅ Validate critical keys
if not TELEGRAM_BOT_TOKEN or not RAPIDAPI_KEY:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or RAPIDAPI_KEY in .env file")

HEADERS = {
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "X-RapidAPI-Key": RAPIDAPI_KEY
}
# ✅ Logging setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 🚫 Avoid printing API keys in production
if os.getenv("DEBUG", "false").lower() == "true":
    print("🔐 RAPIDAPI_KEY:", RAPIDAPI_KEY)

# 📶 Match status emojis
STATUS_EMOJIS = {
    "LIVE": "🟢",
    "COMPLETED": "🔴",
    "UPCOMING": "🟡",
    "UNKNOWN": "⚪️"
}

# 🌍 Team flag emojis
FLAG_EMOJIS = {
    "India": "🇮🇳", "Pakistan": "🇵🇰", "Australia": "🇦🇺", "England": "🏴",
    "New Zealand": "🇳🇿", "South Africa": "🇿🇦", "Sri Lanka": "🇱🇰",
    "Bangladesh": "🇧🇩", "Afghanistan": "🇦🇫", "West Indies": "🌴"
}

# 🏏 Team ID mappings (used for API lookups and human-readable names)
TEAM_IDS = [
    2, 96, 27, 3, 4, 5, 6, 9, 10, 11, 12, 13, 71, 72, 77, 161, 185,
    190, 287, 298, 300, 303, 304, 343, 527, 529, 541, 44, 26, 7, 8,
    14, 15, 23, 24, 25, 675
]

TEAM_NAMES = {
    2: "India", 96: "Afghanistan", 27: "Ireland", 3: "Pakistan", 4: "Australia",
    5: "Sri Lanka", 6: "Bangladesh", 9: "England", 10: "West Indies", 11: "South Africa",
    12: "Zimbabwe", 13: "New Zealand", 71: "Malaysia", 72: "Nepal", 77: "Germany",
    161: "Namibia", 185: "Denmark", 190: "Singapore", 287: "Papua New Guinea",
    298: "Kuwait", 300: "Vanuatu", 303: "Jersey", 304: "Oman", 343: "Fiji",
    527: "Italy", 529: "Botswana", 541: "Belgium", 44: "Uganda", 26: "Canada",
    7: "United Arab Emirates", 8: "Hong Kong", 14: "Kenya", 15: "USA",
    23: "Scotland", 24: "Netherlands", 25: "Bermuda", 675: "Iran"
}
# ✅ Extract all teams' players from match data
def extract_all_teams_players(data):
    result = {}

    # Ensure team data is present
    teams = data.get("team", [])
    for team in teams:
        team_name = team.get("teamName") or "Unknown Team"
        players = team.get("players", {})

        # Initialize player structure
        team_data = {
            "playingXI": [],
            "bench": []
        }

        # Extract playing XI
        for player in players.get("playingXI", []):
            name = player.get("fullName") or "Unknown"
            team_data["playingXI"].append(name)

        # Extract bench players
        for player in players.get("bench", []):
            name = player.get("fullName") or "Unknown"
            team_data["bench"].append(name)

        # Add to result
        result[team_name] = team_data

    return result
async def show_all_teams_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match_id = "74836"  # 🔁 TODO: Make dynamic using context.args or live match lookup
    url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS)

        if response.status_code != 200:
            await update.message.reply_text(f"❌ API Error: {response.status_code}")
            return

        data = response.json()
        teams = {}

        # ✅ Extract team names and IDs
        for team in (data["matchHeader"]["team1"], data["matchHeader"]["team2"]):
            team_id = team["id"]
            team_name = team["name"]
            teams[team_id] = {
                "name": team_name,
                "playingXI": [],
                "bench": []
            }

        # ✅ Extract players into Playing XI and Bench
        for squad in data.get("teamSquad", []):
            team_id = squad["team"]["id"]
            players = squad.get("players", [])
            for i, player in enumerate(players):
                pname = player.get("name", "Unknown")
                if i < 11:
                    teams[team_id]["playingXI"].append(pname)
                else:
                    teams[team_id]["bench"].append(pname)

        # ✅ Format the output message
        message = ""
        for team in teams.values():
            message += f"🏏 *{team['name']}* - Playing XI:\n"
            for p in team["playingXI"]:
                message += f"• {p}\n"
            if team["bench"]:
                message += f"\n🪑 *Bench:*\n"
                for b in team["bench"]:
                    message += f"• {b}\n"
            message += "\n"

        await update.message.reply_text(
            message.strip() or "⚠️ No teams or players found.",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Exception: {e}")
        logging.exception("Error in show_all_teams_players")

async def get_matches():
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=HEADERS)

        logging.info(f"[get_matches] API Status: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"❌ Error fetching data: {response.text}")
            return None

        data = response.json()

        # Optional: Only show summary in production, full dump in debug mode
        logging.debug("📄 FULL MATCH DATA:\n%s", json.dumps(data, indent=2))

        return data

    except Exception as e:
        logging.exception("⚠️ Exception while fetching matches")
        return None

async def get_upcoming_matches():
    data = await get_matches()  # Now async call
    if not data or 'typeMatches' not in data:
        return "⚠️ Couldn't load match data."

    now = datetime.utcnow()
    upcoming_matches = []

    try:
        for match_type in data.get('typeMatches', []):
            for series in match_type.get('seriesMatches', []):
                for match in series.get('matches', []):
                    match_info = match.get('matchInfo', {})
                    state = match_info.get('state', '').lower()
                    start_date_ms = match_info.get('startDate')

                    if not start_date_ms:
                        continue

                    match_time = datetime.utcfromtimestamp(int(start_date_ms) / 1000)

                    if match_time > now and "upcoming" in state:
                        team1 = match_info.get('team1', {}).get('teamName', 'Team A')
                        team2 = match_info.get('team2', {}).get('teamName', 'Team B')
                        venue_info = match_info.get('venueInfo', {})
                        venue = venue_info.get('ground', 'Unknown Venue')
                        city = venue_info.get('city', '')
                        formatted_time = match_time.strftime("%d %b %Y %H:%M UTC")

                        upcoming_matches.append(
                            f"🆚 *{team1}* vs *{team2}*\n📅 {formatted_time} | 🏟️ {venue}, {city}"
                        )
    except Exception as e:
        logging.exception("⚠️ Error while processing upcoming matches")

    if not upcoming_matches:
        return "📭 No upcoming matches found."

    return "📅 *Upcoming Matches:*\n\n" + "\n\n".join(upcoming_matches)
import logging
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

# ✅ Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text("⚠️ Something went wrong. Please try again later.")
        except Exception as e:
            logging.error(f"⚠️ Failed to send error message to user: {e}")

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action=ChatAction.TYPING)
    await update.message.reply_text(
        "👋 Welcome to *FantasyBot!*\n\n"
        "Type /help to see all available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action=ChatAction.TYPING)  # 👈 Add this
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
""", parse_mode=ParseMode.MARKDOWN
    )
import aiohttp  # keep imports at the top

# ✅ Message splitter (for long text with debug logs)
def split_message(text: str, limit: int = 4000) -> list[str]:
    """
    Safely splits a long message by line without breaking HTML formatting.
    Includes debug output.
    """
    print(f"🔍 Splitting message of total length: {len(text)} | Limit: {limit}")

    lines = text.splitlines(keepends=True)
    chunks = []
    chunk = ""
    count = 0

    for line in lines:
        if len(chunk) + len(line) > limit:
            print(f"📦 Chunk {count + 1} created | Length: {len(chunk)}")
            chunks.append(chunk)
            chunk = line
            count += 1
        else:
            chunk += line

    if chunk:
        print(f"📦 Final Chunk {count + 1} created | Length: {len(chunk)}")
        chunks.append(chunk)

    print(f"✅ Total Chunks: {len(chunks)}")
    return chunks

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.cricapi.com/v1/currentMatches?apikey=d7e83232-90d1-4588-bd4f-4884717df392"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except Exception as e:
        print(f"❌ Error in /score: {e}")
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
        if any(word in status for word in ["live", "won", "stumps", "tied"]):
            team_info = match.get("teamInfo", [])
            team1 = team_info[0].get("name", "Team 1") if len(team_info) > 0 else "Team 1"
            team2 = team_info[1].get("name", "Team 2") if len(team_info) > 1 else "Team 2"

            scores = match.get("score", [])
            score1 = (
                f"{scores[0].get('r', '-')}/{scores[0].get('w', '-')} ({scores[0].get('o', '-')} ov)"
                if len(scores) > 0 else "N/A"
            )
            score2 = (
                f"{scores[1].get('r', '-')}/{scores[1].get('w', '-')} ({scores[1].get('o', '-')} ov)"
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
from typing import List
from datetime import datetime, timezone
from dateutil import parser

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

                # Parse start time
                start_time = info.get("startDate")
                time_str = ""
                if start_time:
                    try:
                        # If start_time is timestamp in ms
                        dt = datetime.fromtimestamp(int(start_time) / 1000, tz=timezone.utc)
                        time_str = dt.strftime("%d %b %Y, %I:%M %p UTC")
                    except Exception:
                        try:
                            # If start_time is ISO string or other format
                            dt = parser.parse(start_time)
                            time_str = dt.strftime("%d %b %Y, %I:%M %p")
                        except Exception:
                            time_str = ""

                if time_str:
                    status += f" (⏰ {time_str})"

                result_line = f"{team1} vs {team2} | {series_name} | {status}"
                results.append(result_line)
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from pytz import timezone as pytz_timezone
from dateutil import parser

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📡 Fetching fresh TODAY match data...")

    IST = pytz_timezone("Asia/Kolkata")
    UTC = pytz_timezone("UTC")
    today_date = datetime.now(IST).date()
    print(f"🕒 IST Today Date: {today_date}")

    data = get_today_matches()
    if not data:
        await update.message.reply_text("❌ Could not fetch today's matches.")
        return

    matches = data.get("data", [])
    live = []
    upcoming = []
    completed = []

    for match in matches:
        match_date_str = match.get("dateTimeGMT")
        if not match_date_str:
            continue

        try:
            utc_match_datetime = parser.isoparse(match_date_str)
            match_date_ist = utc_match_datetime.astimezone(IST).date()
            print(f"🌐 Raw match date string: {match_date_str}")
            print(f"🗓️ Converted IST match date: {match_date_ist}")
        except Exception as e:
            print(f"⚠️ Date parse error: {e}")
            continue

        if match_date_ist != today_date:
            continue

        teams = match.get("teamInfo", [])
        team1 = teams[0].get("name", "Team 1") if len(teams) > 0 else "Team 1"
        team2 = teams[1].get("name", "Team 2") if len(teams) > 1 else "Team 2"
        line = f"{team1} 🆚 {team2}"

        # Match time
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

        # Match status
        status = match.get("status", "").strip().lower()
        print(f"✅ Match found for today: {line}, Status: {status}")

        # Status classification
        if any(word in status for word in [
            "won", "lost", "draw", "tie", "abandoned", "completed", 
            "match ended", "no result", "concluded", "beat", "result"
        ]):
            completed.append(f"✅ *{line}*\n 🏆 _{status}_")

        elif any(word in status for word in [
            "live", "running", "in progress", "opt to bowl", "opted to field", 
            "won toss", "elected to field", "elected to bowl", 
            "fielding", "batting", "first innings", "second innings"
        ]):
            live.append(f"🔴 *{line}*\n 🎯 _{status}_")

        elif any(word in status for word in [
            "not started", "scheduled", "match yet to begin", "upcoming", "tbd"
        ]):
            upcoming.append(f"🟡 *{line}*\n 📅 _{status}_")

        else:
            # Unknown status – treat as upcoming
            upcoming.append(f"🟡 *{line}*\n 📅 _{status or 'Scheduled'}_")

    # Debug: print counts
    print(f"🟢 LIVE: {len(live)} matches")
    print(f"🕓 UPCOMING: {len(upcoming)} matches")
    print(f"✅ COMPLETED: {len(completed)} matches")

    # If no matches found
    if not (live or upcoming or completed):
        await update.message.reply_text("📭 No matches for today.")
        return

    # Build final message (showing all 3 categories even if empty)
    message = "*🏏 Matches Today:*\n\n"

    message += "🔴 *Live Matches:*\n"
    message += "\n\n".join(live) if live else " — No live matches.\n"
    message += "\n\n"

    message += "🟡 *Upcoming Matches:*\n"
    message += "\n\n".join(upcoming) if upcoming else " — No upcoming matches.\n"
    message += "\n\n"

    message += "✅ *Completed Matches:*\n"
    message += "\n\n".join(completed) if completed else " — No completed matches."

    # Send in chunks if too long
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")

async def fetch_team_name(team_id: str, api_key: str) -> str:
    """
    Searches current matches for a team name by ID using cricapi.
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
async def fantasy11(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    import httpx

    API_KEY = "d7e83232-90d1-4588-bd4f-4884717df392"
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
                match_list_url = f"https://api.cricketdata.org/v1/match_list?apikey={API_KEY}&series_id={series_id}"
                try:
                    res = await client.get(match_list_url)
                    res.raise_for_status()
                    data = (await res.json()).get("data", [])
                    if data:
                        all_matches.extend(data)
                except Exception as e:
                    print(f"⚠️ Failed to fetch for series {series_id}: {e}")
                    continue

            if not all_matches:
                await update.message.reply_text("⚠️ No matches found in available series.")
                return

            best_match = None
            for match in all_matches:
                match_id = match.get("match_id")
                if not match_id:
                    continue

                scorecard_url = f"https://api.cricketdata.org/v1/match_scorecard?apikey={API_KEY}&match_id={match_id}"
                print("🔗 Scorecard URL:", scorecard_url)

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

        match_info, batsmen_data = best_match
        team1 = match_info.get("team1", {}).get("name", "Team 1")
        team2 = match_info.get("team2", {}).get("name", "Team 2")

        top_batsmen = sorted(batsmen_data, key=lambda x: x.get("sr", 0), reverse=True)[:11]

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

async def get_all_matches():
    url = "https://api.cricapi.com/v1/matches?apikey=5cc2f540-b58e-4070-916e-ea237c661ac6"
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
import html
from collections import defaultdict
from datetime import datetime

async def next_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📦 Fetching upcoming match data...")

    matches_data = get_next_matches()
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

            match_date = datetime.strptime(start_time_str, "%Y-%m-%d").date()
            if match_date < today:
                continue

            team1_raw = match.get("team1", "").strip()
            team2_raw = match.get("team2", "").strip()
            venue_raw = match.get("venue", "Unknown Venue")
            status_raw = match.get("status", "🕒 Time TBD")
            desc_raw = match.get("name", "")

            # 🔍 Extract from title if needed
            if not team1_raw or not team2_raw or team1_raw.upper() == "TBC" or team2_raw.upper() == "TBC":
                title_clean = desc_raw.split(",")[0]  # e.g., "India vs Australia"
                title_parts = title_clean.split(" vs ")
                if len(title_parts) == 2:
                    team1_raw, team2_raw = title_parts[0].strip(), title_parts[1].strip()

            # 🚫 Skip if still incomplete after parsing
            if not team1_raw or not team2_raw or team1_raw.upper() == "TBC" or team2_raw.upper() == "TBC":
                continue

            # ✅ Escape HTML-safe content
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

    # 🧾 Compose grouped messages
    message_parts = []
    for date in sorted(grouped_matches.keys()):
        header = f"📅 <b>{date.strftime('%B %d, %Y')}</b>\n"
        matches_text = "\n".join(grouped_matches[date])
        message_parts.append(header + matches_text + "\n")

    full_message = "\n".join(message_parts).strip()

    # ✂️ Split large messages
    for part in split_message(full_message):
        await update.message.reply_text(part, parse_mode="HTML")

from functools import lru_cache
import requests

# 🧠 /playerstats Command
async def playerstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a player name.\n\nUsage: /playerstats Rohit Sharma"
        )
        return

    input_name = " ".join(context.args).strip().lower()

    # ✅ Fetch all players (cached or async version if used)
    players = get_all_players()
    if not players:
        await update.message.reply_text("⚠️ Could not fetch player list.")
        return

    # 🔍 Try fuzzy match
    name_to_player = {p["name"].lower(): p for p in players}
    close_matches = difflib.get_close_matches(
        input_name, list(name_to_player.keys()), n=1, cutoff=0.6
    )

    if not close_matches:
        await update.message.reply_text("👤 No matching player found.")
        return

    matched_name = close_matches[0]
    matched_player = name_to_player[matched_name]

    # 📊 Get player stats
    stats = get_player_stats(matched_player["id"])
    if not stats:
        await update.message.reply_text("📭 No stats available for this player.")
        return

    # 📝 Format reply
    message = (
        f"📊 <b>{matched_player['name']}</b> - Player Stats:\n\n"
        f"🏏 Matches: <b>{stats.get('matches', 'N/A')}</b>\n"
        f"🧢 Runs: <b>{stats.get('runs', 'N/A')}</b>\n"
        f"🎯 Average: <b>{stats.get('average', 'N/A')}</b>\n"
        f"💥 Strike Rate: <b>{stats.get('strike_rate', 'N/A')}</b>"
    )

    await update.message.reply_text(message, parse_mode="HTML")
import httpx
from telegram import Update
from telegram.ext import ContextTypes

CRICKETDATA_API_KEY = "your_api_key_here"

# 📡 /live_matches Command
async def live_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.cricketdata.org/v1/match/live?apikey={CRICKETDATA_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to fetch live match data.")
            return

        matches_data = response.json()
        print("📡 Live matches API response:", matches_data)

        message = "📡 <b>Live Matches:</b>\n\n"
        found = False

        for match in matches_data.get("data", []):
            teams = match.get("teams", "Unknown vs Unknown")
            status = match.get("status", "Unknown status")
            score = match.get("score", "No score available")

            message += (
                f"🏏 <b>{teams}</b>\n"
                f"📊 {score}\n"
                f"🟢 Status: {status}\n\n"
            )
            found = True

        if not found:
            message += "⚠️ No active live matches at the moment."

        await update.message.reply_text(message.strip(), parse_mode="HTML")

    except Exception as e:
        print("❌ Exception in live_matches:", e)
        await update.message.reply_text("⚠️ Something went wrong while fetching live matches.")
from dateutil import parser
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from pytz import timezone, UTC

IST = timezone("Asia/Kolkata")

async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📡 Fetching fresh TEAMS data...")

    data = get_today_matches()
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
            if now_utc < match_dt_utc:
                upcoming_matches.append(entry)
            elif now_utc >= match_dt_utc:
                live_matches.append(entry)
        elif match_day_utc < today_utc:
            completed_matches.append(entry)

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

import logging
import os

if __name__ == "__main__":
    # 🪵 Logging setup
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # 🔒 Show API keys only in dev
    if os.getenv("ENV") != "production":
        print("✅ TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)
        print("🔐 RAPIDAPI_KEY:", RAPIDAPI_KEY)

    # 🤖 App creation
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ⌨️ Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler(["teams", "team"], teams))
    app.add_handler(CommandHandler("next", next_match))
    app.add_handler(CommandHandler("fantasy11", fantasy11))
    app.add_handler(CommandHandler("playerstats", playerstats))
    app.add_handler(CommandHandler("live", live_matches))
    app.add_handler(CommandHandler("about", lambda update, context: update.message.reply_text(
        "🏏 FantasyCrick Bot v1.0\nPowered by CricketData & Telegram API\nDeveloper: @YourUsername"
    )))

    # 🚀 Start polling
    logger.info("🚀 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()
import requests

def search_player_by_name(name):
    url = f"https://api.cricapi.com/v1/players?apikey={API_KEY}&offset=0&search={name}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes

        data = response.json()
        players = data.get("data", [])

        if not players:
            print(f"🔍 No player found for: {name}")
            return None

        return players[0]  # Return the first/best match

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except ValueError:
        print("⚠️ Failed to parse JSON response.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

    return None
import requests

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

        # 🎯 Customize format here (e.g., "ODI", "Test", "T20I")
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
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

def register_handlers(app):
    # ✅ General commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # 🏏 Match-related commands
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("live", live_matches))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("next", next_match))
    app.add_handler(CommandHandler(["teams", "team"], show_all_teams_players))

    # 🧠 Fantasy & Player Stats
    app.add_handler(CommandHandler("fantasy11", fantasy11))
    app.add_handler(CommandHandler("playerstats", playerstats))

    # ⚠️ Error & unknown command handlers
    app.add_error_handler(error_handler)

    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Unknown command. Use /help to see available options.")

    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Register the error handler globally
    app.add_error_handler(error_handler)

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
