import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from bot import register_handlers  # 👈 function from bot.py

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    print("✅ Starting bot from main.py...")
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )

    register_handlers(app)  # ✅ All handlers from bot.py

    print("✅ Bot is running...")
    app.run_polling(drop_pending_updates=True)
