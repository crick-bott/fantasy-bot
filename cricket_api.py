import os
import traceback
from dateutil import parser
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
from typing import Optional, Dict
import aiohttp
import asyncio

CACHE_DURATION = timedelta(seconds=30)
_cached_today_data: Optional[Dict] = None
_last_today_fetch: Optional[datetime] = None

def get_api_key() -> str:
    key = os.getenv("CRICKDATA_API_KEY")
    if not key:
        raise EnvironmentError("❌ CRICKDATA_API_KEY is not set in environment variables.")
    return key
async def get_fantasy_xi(match_id: str) -> dict:
    print("⚠️ CricAPI doesn't support fantasy XI generation.")
    data = await get_today_matches()  # if you need to await here
    
    return {
        "fantasy_xi": [],
        "captain": None,
        "vice_captain": None,
    }

def get_teams_list(match_id: str) -> dict:
    print("⚠️ CricAPI does not support detailed team list for a match.")
    return {
        "team1": "",
        "team2": "",
        "players1": [],
        "players2": [],
    }

async def get_next_matches():
    # This is an async function that fetches upcoming matches
    import aiohttp
    from datetime import datetime

    API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"  # Replace or fetch from env

    url = "https://api.cricketdata.org/matches?date_from=" + datetime.now().strftime("%Y-%m-%d")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"❌ Exception in get_next_matches: {e}")
        return []

async def get_today_matches() -> dict:
    global _cached_today_data, _last_today_fetch

    API_KEY = get_api_key()

    now_utc = datetime.now(timezone.utc)
    IST = pytz_timezone("Asia/Kolkata")
    today_date = datetime.now(IST).date()

    if _cached_today_data and _last_today_fetch and (now_utc - _last_today_fetch) < CACHE_DURATION:
        print("⚡ Using cached TODAY match data")
        matches = _cached_today_data.get("matches", [])
    else:
        print("📡 Fetching fresh TODAY match data...")
        url = "https://api.cricapi.com/v1/currentMatches"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, params={"apikey": API_KEY}) as response:
                    response.raise_for_status()
                    data = await response.json()

                    print("🔍 Full API response:")
                    import json
                    print(json.dumps(data, indent=2))

                    _cached_today_data = data
                    _last_today_fetch = now_utc
                    matches = data.get("matches", [])
                    print(f"📊 Total matches fetched from API: {len(matches)}")
        except Exception as e:
            print("❗ Exception fetching today's matches:", e)
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    today_matches = []
    for match in matches:
        try:
            match_name = match.get("name")
            if match_name == "Not Covered match":
                continue

            start_time_str = match.get("dateTimeGMT")
            if not start_time_str:
                print(f"⚠️ Match '{match_name}' missing 'dateTimeGMT', skipping.")
                continue

            print(f"🕒 Match '{match_name}' dateTimeGMT: {start_time_str}")

            match_datetime_utc = parser.isoparse(start_time_str)
            match_datetime_ist = match_datetime_utc.astimezone(IST)

            print(f"    UTC datetime: {match_datetime_utc}")
            print(f"    IST datetime: {match_datetime_ist}")
            print(f"    IST date: {match_datetime_ist.date()} vs Today (IST): {today_date}")

            if match_datetime_ist.date() == today_date:
                today_matches.append(match)

        except Exception as e:
            print(f"⚠️ Error parsing match date for '{match.get('name')}': {e}")
            traceback.print_exc()

    print(f"✅ Total TODAY matches found: {len(today_matches)}")
    return {"status": "success", "data": today_matches}
