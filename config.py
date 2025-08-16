import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env file

API_KEY = os.getenv("CRICKDATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not API_KEY:
    raise ValueError("⚠️ CRICKDATA_API_KEY environment variable is missing!")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN environment variable is missing!")
