import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id_str) for id_str in os.getenv("ADMIN_IDS", "").split(",") if id_str]
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

DATABASE_URL = os.getenv("DATABASE_URL")
