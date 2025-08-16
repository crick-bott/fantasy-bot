from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import httpx
import asyncio

CRICKDATA_API_KEY = "06dcaf5e-a5bb-40c6-bc73-1ff5d97a7a5f"

async def series_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = f"https://api.cricketdata.org/v1/series?apikey={CRICKDATA_API_KEY}&offset=0"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            data = await resp.json()
            
            if data.get("status") != "success":
                await update.message.reply_text(f"Failed to fetch series list. Server response: {data}")
                return
            
            series_data = data.get("data", [])
            if not series_data:
                await update.message.reply_text("No series found.")
                return
            
            message_lines = []
            for series in series_data[:10]:  # limit to first 10 to avoid flooding
                line = f"{series['name']}\nFrom: {series.get('startDate', 'N/A')} To: {series.get('endDate', 'N/A')}\nMatches: {series.get('matches', 'N/A')}"
                message_lines.append(line)
            
            message = "\n\n".join(message_lines)
            await update.message.reply_text(message)
        
        except Exception as e:
            await update.message.reply_text(f"Error fetching data: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token("8391514200:AAE3DLKQbPiobZTnqUGC4skF3vWdZMe2Isk").build()
    app.add_handler(CommandHandler("series", series_list))
    print("Bot started...")
    app.run_polling()
