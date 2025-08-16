import os
from dotenv import load_dotenv

load_dotenv()

print("CRICKDATA_API_KEY:", os.getenv("CRICKDATA_API_KEY"))
print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
