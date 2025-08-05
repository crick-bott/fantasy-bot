import httpx
import asyncio
import traceback

async def test_series():
    API_KEY = "d7e83232-90d1-4588-bd4f-4884717df392"
    SERIES_ID = "d93bf50f-b2ce-4290-b74f-daf9a8c80a80"
    url = f"https://api.cricketdata.org/v1/match_list?apikey={API_KEY}&series_id={SERIES_ID}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.get(url)
            print("✅ Status code:", res.status_code)
            print("📦 Response text:", res.text)
        except Exception as e:
            print("❌ Exception caught:")
            traceback.print_exc()

asyncio.run(test_series())
