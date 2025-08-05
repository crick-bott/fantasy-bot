import requests

# ✅ Your actual RapidAPI key (must be in quotes)
CRICKETDATA_API_KEY = "d7e83232-90d1-4588-bd4f-4884717df392"

url = "https://cricbuzz-cricket.p.rapidapi.com/teams/v1/international"
headers = {
    "X-RapidAPI-Key": CRICKETDATA_API_KEY,
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
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
else:
    print(f"❌ Failed to fetch teams: {response.status_code}")
    print("🔁 Response Text:", response.text)

