import os
import logging
from database.mongo import get_db

logger = logging.getLogger(__name__)

async def init_config_db():
    """Initializes default system configurations in database if not present."""
    db = get_db()
    
    # Read core config from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    mongo_uri = os.getenv("MONGODB_URI")
    main_admin_id = os.getenv("MAIN_ADMIN_ID")
    
    if not bot_token or not mongo_uri or not main_admin_id:
        logger.error("⚠️ CRITICAL ERROR: BOT_TOKEN, MONGODB_URI, or MAIN_ADMIN_ID is missing in ENV!")
    
    # Convert MAIN_ADMIN_ID to integer safely if possible
    admin_list = []
    if main_admin_id and main_admin_id.isdigit():
        admin_list.append(int(main_admin_id))
        
    system_config = await db.system_config.find_one({"config_id": "main_config"})
    
    if not system_config:
        default_config = {
            "config_id": "main_config",
            "bot_status": True,
            "withdrawals_enabled": False,
            "device_check": True,
            "spam_check": True,
            "two_fa_add": True,
            "name_change": True,
            "bio_change": True,
            "api_id": int(os.getenv("API_ID")) if os.getenv("API_ID") and os.getenv("API_ID").isdigit() else None,
            "api_hash": os.getenv("API_HASH"),
            "two_fa_password": "Experiment247*",
            "min_withdraw": 1.0,
            "proxy_type": "DataImpulse",
            "proxy_host": "",
            "proxy_port": "",
            "proxy_user": "",
            "proxy_pass": "",
            "update_channel": "",
            "backup_channel": "",
            "withdraw_channel": "",
            "activity_channel": "",
            "admins": admin_list
        }
        await db.system_config.insert_one(default_config)
        logger.info("Default system configurations initialized successfully in MongoDB.")
        return default_config
        
    return system_config

async def get_system_config():
    db = get_db()
    system_config = await db.system_config.find_one({"config_id": "main_config"})
    
    if not system_config:
        # Fallback if config is missing dynamically
        return await init_config_db()
        
    return system_config

async def update_system_config(update_data: dict):
    db = get_db()
    await db.system_config.update_one(
        {"config_id": "main_config"},
        {"$set": update_data},
        upsert=True
    )
