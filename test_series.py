import httpx
import asyncio
import traceback

async def test_series():
    CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"  # Verify this is correct
    SERIES_ID = "d93bf50f-b2ce-4290-b74f-daf9a8c80a80"
    url = f"https://api.cricketdata.org/v1/match_list?apikey={CRICKDATA_API_KEY}&series_id={SERIES_ID}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.get(url)
            print("✅ Status code:", res.status_code)
            res.raise_for_status()  # Raise error if response is not 2xx

            data = await res.json()
            print("📦 Response JSON:")
            print(data)

        except httpx.HTTPStatusError as http_err:
            print(f"❌ HTTP error occurred: {http_err}")
        except Exception as e:
            print("❌ Exception caught:")
            traceback.print_exc()

asyncio.run(test_series())


