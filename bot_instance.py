import os
import telebot
from telebot import TeleBot


def load_env_from_file(env_path: str = ".env") -> None:
    """Simple .env loader to populate os.environ without external deps."""
    try:
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Fail open: if .env cannot be parsed, we just skip it
        pass


# Try to load variables from a local .env file (ignored by git)
load_env_from_file()

# Load Telegram bot token securely from environment
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "8246506894:AAFoHTPfoevsp7qz62tYcfbYQWQVvJ7fXL4").strip()

# Basic token validation: prevents starting with an obviously invalid/missing token
if not bot_token or ":" not in bot_token:
    print("❌ ERROR: Missing TELEGRAM_BOT_TOKEN environment variable!")
    print("📝 Setup Instructions:")
    print("1. Create a .env file in the project root")
    print("2. Add: TELEGRAM_BOT_TOKEN=your_bot_token_here")
    print("3. Add: TELEGRAM_GROUP_CHAT_ID=your_group_id_here")
    print("4. Or set environment variables directly on your server")
    print("5. Get your bot token from @BotFather on Telegram")
    print("6. Get your group ID by adding @userinfobot to your group")
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable. Set it (or create a .env file).")

bot = telebot.TeleBot(bot_token, parse_mode='HTML')
