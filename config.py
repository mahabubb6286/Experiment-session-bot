import os
from dotenv import load_dotenv

load_dotenv()

# Mandatory Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
MONGO_URI = os.getenv("MONGO_URI", "").strip()

# Main Admin ID
try:
    MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "0").strip())
except ValueError:
    MAIN_ADMIN_ID = 0

if not BOT_TOKEN or not MONGO_URI or not MAIN_ADMIN_ID:
    print("⚠️ CRITICAL ERROR: BOT_TOKEN, MONGO_URI, or MAIN_ADMIN_ID is missing in ENV!")
