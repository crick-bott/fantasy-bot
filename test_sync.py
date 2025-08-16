import requests

CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"
SERIES_ID = "d93bf50f-b2ce-4290-b74f-daf9a8c80a80"
url = f"https://api.cricketdata.org/v1/match_list?apikey={CRICKDATA_API_KEY}&series_id={SERIES_ID}"

try:
    res = requests.get(url, timeout=10)
    print("✅ Status:", res.status_code)

    # Check if request was successful
    if res.status_code == 200:
        try:
            data = res.json()
            print("📦 Response JSON:")
            print(data)
        except ValueError:
            print("⚠️ Failed to parse JSON response.")
    else:
        print("❌ Error fetching data:", res.text)

except requests.exceptions.RequestException as e:
    print("❌ Request Exception:", e)
except Exception as e:
    print("❌ Unexpected ERROR:", e)

