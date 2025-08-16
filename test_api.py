import asyncio
import aiohttp

CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"

async def test_api():
    url = f"https://api.cricketdata.org/v1/match/live?apikey={CRICKDATA_API_KEY}"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()  # Parse JSON directly
                    print(data)
                else:
                    print(f"Failed to fetch data: {resp.reason} (HTTP {resp.status})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
