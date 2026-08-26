import asyncio

import nest_asyncio


try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client

from config_engine import ConfigEngine
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
from telegram_engine import TelegramEngine

config = ConfigEngine()
tg_engine = TelegramEngine(config)

bot = Client(
    "bot_controller",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
)

user_sessions = {}
admin_state = {}

# ১. আগে Admin Handlers রেজিস্টার করতে হবে
register_admin_handlers(
    bot,
    config,
    tg_engine,
    admin_state,
)

# ২. তারপর User Handlers রেজিস্টার করতে হবে
register_user_handlers(
    bot,
    config,
    tg_engine,
    user_sessions,
    admin_state,
)

if __name__ == "__main__":
    print("🤖 Upgraded Admin Panel Bot Running...")
    bot.run()
