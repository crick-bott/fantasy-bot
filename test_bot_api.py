import os
import requests

# Get bot token from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN in your environment")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    print("Status Code:", response.status_code)

    if "result" in data and len(data["result"]) > 0:
        print("Response JSON:", data)
    else:
        print("No updates available.")
except requests.RequestException as e:
    print(f"Error fetching updates: {e}")
