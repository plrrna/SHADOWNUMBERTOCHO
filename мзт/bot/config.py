import os
from dotenv import load_dotenv, find_dotenv

# Try multiple locations for .env to be robust on Windows/Cyrillic paths
# 1) Current working directory
load_dotenv(find_dotenv(usecwd=True))

# 2) Project root next to this file's parent (../.env)
_this_dir = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_this_dir, os.pardir))
_env_path_root = os.path.join(_project_root, ".env")
if os.path.exists(_env_path_root):
	load_dotenv(_env_path_root, override=False)

# 3) Explicitly try .env inside bot folder
_env_path_bot = os.path.join(_this_dir, ".env")
if os.path.exists(_env_path_bot):
	load_dotenv(_env_path_bot, override=False)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN", os.getenv("CRYPTOBOT_TOKEN", ""))

if not BOT_TOKEN:
	raise RuntimeError("BOT_TOKEN is not set. Put it into .env")
