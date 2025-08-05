import requests

API_KEY = "d7e83232-90d1-4588-bd4f-4884717df392"
SERIES_ID = "d93bf50f-b2ce-4290-b74f-daf9a8c80a80"
url = f"https://api.cricketdata.org/v1/match_list?apikey={API_KEY}&series_id={SERIES_ID}"

try:
    res = requests.get(url, timeout=10)
    print("✅ Status:", res.status_code)
    print("📦 Response:", res.text)
except Exception as e:
    print("❌ ERROR:", e)
