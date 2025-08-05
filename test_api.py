import httpx
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# ✅ Use env variable name (not the key itself)
CRICKETDATA_API_KEY = os.getenv("CRICKETDATA_API_KEY")

# 🔗 API endpoint
url = f"https://api.cricketdata.org/v1/match/live?apikey={CRICKETDATA_API_KEY}"

try:
    response = httpx.get(url, timeout=10)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        print("✅ Response JSON:", response.json())
    else:
        print("❌ Error:", response.text)

except Exception as e:
    print("❗ Exception occurred:", e)
