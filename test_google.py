import asyncio
import aiohttp

async def test_google():
    url = "https://www.google.com"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(text[:100])  # print first 100 chars
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_google())
