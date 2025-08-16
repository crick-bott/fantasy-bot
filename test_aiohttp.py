import asyncio
import aiohttp
import os

API_KEY = os.getenv("CRICKDATA_API_KEY")  # Correct env var name here

async def test():
    url = "https://api.cricketdata.org/matches?date=2025-08-09"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(text[:500])  # print first 500 chars of response
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
