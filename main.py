import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from bot import register_handlers

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN not found in environment variables.")
    exit(1)

if __name__ == "__main__":
    print("✅ Starting bot from main.py...")

    try:
        app = (
            ApplicationBuilder()
            .token(TOKEN)
            .read_timeout(30)
            .write_timeout(30)
            .connect_timeout(30)
            .build()
        )

        register_handlers(app)

        print("✅ Bot is running. Press Ctrl+C to stop.")
        app.run_polling(drop_pending_updates=True)

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")

    except Exception as e:
        print(f"❌ Exception during bot startup: {e}")

