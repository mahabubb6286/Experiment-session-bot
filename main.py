import asyncio
import logging
from pyrogram import Client
from database.config_db import init_config_db, get_system_config
from database.user_db import init_user_db
from database.session_db import init_session_db
from database.country_db import init_country_db
from database.card_db import init_card_db

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing database connections...")
    
    # Initialize all database collections/tables
    await init_config_db()
    await init_user_db()
    await init_session_db()
    await init_country_db()
    await init_card_db()
    
    config = await get_system_config()
    bot_token = config.get("bot_token")
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    
    if not bot_token or not api_id or not api_hash:
        logger.warning("Bot token, API ID or API Hash not set in Config DB! Falling back to env variables...")
        import os
        bot_token = os.getenv("BOT_TOKEN")
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")

    logger.info("Starting Telegram Bot Application...")
    
    app = Client(
        "bot_session_manager",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        plugins=dict(root="handlers")
    )
    
    await app.start()
    logger.info("🤖 Bot is successfully online and listening for messages!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped successfully.")
