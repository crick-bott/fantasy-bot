import httpx
import asyncio

async def test_connect():
    url = "https://api.cricapi.com/v1/series"
    params = {
        "apikey": "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f",
        "offset": 0
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            data = await resp.json()
            for series in data.get("data", []):
                print(f"{series['name']} ({series['startDate']} - {series['endDate']})")
        except Exception as e:
            print("Error:", e)

asyncio.run(test_connect())

