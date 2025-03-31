import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Credentials
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Admins
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 5000))

# User Info
USERNAME = os.getenv("USERNAME", "")
NAME = os.getenv("NAME", "")

# Approved Users (stored as JSON string with user_id as key and name as value)
try:
    APPROVED_USERS = json.loads(os.getenv("APPROVED_USERS", "{}"))
    # Convert string keys to integers (JSON only supports string keys)
    APPROVED_USERS = {int(k): v for k, v in APPROVED_USERS.items()}
except:
    APPROVED_USERS = {}

# Define paths for Render compatibility
TEMP_DIR = "/tmp/bot_temp" if os.path.exists("/tmp") else "temp"
DATA_FILE = "/tmp/bot_data.json" if os.path.exists("/tmp") else "bot_data.json"
