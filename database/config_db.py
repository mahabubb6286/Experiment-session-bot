from database.mongo import get_db
import config

async def get_system_config():
    db = get_db()
    system_config = await db.system_config.find_one({"config_id": "main_config"})
    
    if not system_config:
        # Default empty initial structure
        default_config = {
            "config_id": "main_config",
            "bot_status": True,
            "withdrawals_enabled": False,
            "device_check": True,
            "spam_check": True,
            "two_fa_add": True,
            "name_change": True,
            "bio_change": True,
            "api_id": None,
            "api_hash": None,
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
            "admins": [config.MAIN_ADMIN_ID]
        }
        await db.system_config.insert_one(default_config)
        return default_config
    
    return system_config

async def update_system_config(update_data: dict):
    db = get_db()
    await db.system_config.update_one(
        {"config_id": "main_config"},
        {"$set": update_data},
        upsert=True
    )
