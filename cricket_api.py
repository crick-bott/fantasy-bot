import time
import traceback
import requests
import urllib3
import ssl
import json
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
import urllib3
import ssl

def fetch_with_compat_ssl(url):
    try:
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        http = urllib3.PoolManager(ssl_context=ctx)
        response = http.request("GET", url)
        if response.status == 200:
            return response.data.decode()
        else:
            print("❌ HTTP error:", response.status)
    except Exception as e:
        print("⚠️ fetch_with_compat_ssl error:", e)
    return None

API_KEY = "d7e83232-90d1-4588-bd4f-4884717df392"
CACHE_DURATION = timedelta(seconds=30)

# Caches
cached_next_data = None
cached_today_data = None
cached_teams_data = None
last_next_fetch = None
last_today_fetch = None
last_teams_fetch = None

# 🔧 Fetch wrapper
def fetch_data(url):
    try:
        response = requests.get(url)
        time.sleep(1)  # Respect API limits
        if response.status_code == 200:
            data = response.json()
            if data.get("status") != "success":
                print(f"❌ API error: {data}")
                return None
            return data
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None
    except Exception:
        print("❗ Exception during fetch:")
        traceback.print_exc()
        return None

# 📅 Upcoming Matches
def get_next_matches():
    global cached_next_data, last_next_fetch
    now = datetime.now(timezone.utc)

    if cached_next_data and last_next_fetch and (now - last_next_fetch) < CACHE_DURATION:
        print("⚡ Using cached NEXT match data")
        return cached_next_data

    print("📡 Fetching fresh NEXT match data...")
    url = f"https://api.cricapi.com/v1/matches?apikey={API_KEY}&offset=0"
    data = fetch_data(url)
    if data:
        cached_next_data = data
        last_next_fetch = now
    return data

# 📅 Today's Matches (with India timezone)
def get_today_matches():
    global cached_today_data, last_today_fetch
    now_utc = datetime.now(timezone.utc)
    IST = pytz_timezone("Asia/Kolkata")
    today_date = datetime.now(IST).date()

    today_matches = []

    if cached_today_data and last_today_fetch and (now_utc - last_today_fetch) < CACHE_DURATION:
        print("⚡ Using cached TODAY match data")
        matches = cached_today_data.get("data", [])
    else:
        print("📡 Fetching fresh TODAY match data...")
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={API_KEY}&offset=0"
        data = fetch_data(url)
        if not data:
            return {"status": "error", "message": "Failed to fetch match data"}
        cached_today_data = data
        last_today_fetch = now_utc
        matches = data.get("data", [])

    for match in matches:
        match_date_str = match.get("date")
        print(f"🌐 Raw match date string: {match_date_str}")
        if not match_date_str:
            continue
        try:
            match_date = datetime.fromisoformat(match_date_str.replace("Z", "+00:00")).astimezone(IST).date()
            print(f"🗓️ Converted IST match date: {match_date}")
            if match_date == today_date:
                print(f"✅ Match found for today: {match.get('name')}")
                today_matches.append(match)
        except Exception as e:
            print("⚠️ Error parsing date:", match_date_str, e)

    return {
        "status": "success",
        "data": today_matches
    }

# 🧢 Teams List
def get_teams_list():
    global cached_teams_data, last_teams_fetch
    now = datetime.now(timezone.utc)

    if cached_teams_data and last_teams_fetch and (now - last_teams_fetch) < CACHE_DURATION:
        print("⚡ Using cached TEAM list")
        return cached_teams_data

    print("📡 Fetching fresh TEAM list...")
    url = f"https://api.cricapi.com/v1/teams?apikey={API_KEY}"
    data = fetch_data(url)
    if data:
        cached_teams_data = data
        last_teams_fetch = now
    return data

# 🧠 Fantasy XI
def get_fantasy_xi(match_id):
    print(f"📊 Fetching Fantasy XI for match ID: {match_id}")
    url = f"https://api.cricapi.com/v1/match_scorecard?apikey={API_KEY}&id={match_id}"
    data = fetch_data(url)
    return data

# 👥 Player List
@lru_cache(maxsize=1)
def get_all_players(verbose=True):
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={API_KEY}&offset=0"
    all_players = {}

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            if verbose:
                print("❌ currentMatches API error:", response.status_code)
            return []

        data = response.json()
        if data.get("status") != "success":
            if verbose:
                print("❌ currentMatches Error:", data.get("message"))
            return []

        for match in data.get("data", []):
            match_id = match.get("id")
            if not match_id:
                continue

            scorecard_url = f"https://api.cricapi.com/v1/match_scorecard?apikey={API_KEY}&id={match_id}"
            try:
                scorecard_response = requests.get(scorecard_url, timeout=10)
                if scorecard_response.status_code != 200:
                    if verbose:
                        print(f"⚠️ Couldn't fetch scorecard for match {match_id}")
                    continue

                scorecard = scorecard_response.json()
                if scorecard.get("status") != "success":
                    if verbose:
                        print(f"⚠️ Scorecard error for {match_id}: {scorecard.get('message')}")
                    continue

                players = scorecard.get("data", {}).get("players", [])
                for player in players:
                    pid = player.get("id")
                    pname = player.get("name")
                    if pid and pname:
                        all_players[pid] = pname

            except Exception as scorecard_error:
                if verbose:
                    print(f"❌ Exception fetching scorecard: {scorecard_error}")
                continue

    except Exception as e:
        if verbose:
            print("❌ Exception:", e)

    return sorted(
        [{"id": pid, "name": pname} for pid, pname in all_players.items()],
        key=lambda x: x["name"]
    )

# 🆕 Matches by Series ID (using urllib3 + SSL fix)
def get_matches_by_series(series_id):
    url = f"https://api.cricketdata.org/v1/match_list?apikey={API_KEY}&series_id={series_id}"

    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")

    http = urllib3.PoolManager(ssl_context=ctx)

    try:
        response = http.request('GET', url)
        if response.status == 200:
            data = json.loads(response.data.decode())
            if data.get("status") != "success":
                print(f"❌ API error: {data}")
                return None
            return data
        else:
            print(f"❌ HTTP Error: {response.status}")
            return None
    except Exception as e:
        print("❗ Exception while fetching series matches:", e)
        return None

# ✅ Export functions
__all__ = [
    "get_next_matches",
    "get_today_matches",
    "get_teams_list",
    "get_fantasy_xi",
    "get_all_players",
    "get_matches_by_series"  # ✅ newly added
]
