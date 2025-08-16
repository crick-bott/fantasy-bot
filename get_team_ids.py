import os
import requests

# Use your API key here directly or from env
CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"

url = "https://rest.cricketapi.com/rest/v2/series/"

HEADERS = {
    "X-API-Key": "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f",  # Use your API key here correctly
}

try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()  # Raise HTTPError for bad responses
    data = response.json()  # Parse JSON response

    team_ids = []

    print("📋 List of International Teams with IDs:\n")
    for item in data.get("list", []):
        team_name = item.get("teamName")
        team_id = item.get("teamId")
        if team_name and team_id:
            print(f"✅ {team_name} — ID: {team_id}")
            team_ids.append(team_id)

    print("\n📌 Paste this line into your main code:\n")
    print(f"team_ids = {team_ids}")

except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch teams: {e}")
    if 'response' in locals() and response is not None:
        print("🔁 Response Text:", response.text)
