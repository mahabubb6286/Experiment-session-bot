import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from database.config_db import get_system_config, update_system_config
from utils.keyboards import bot_settings_keyboard

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    admins = config.get("admins", [])
    return user_id in admins

@Client.on_callback_query(filters.regex("^admin_bot_settings$"))
async def callback_bot_settings(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    config = await get_system_config()
    await callback.message.edit_text(
        "⚙️ **Manage Bot Operational Toggles:**",
        reply_markup=bot_settings_keyboard(config)
    )

@Client.on_callback_query(filters.regex("^toggle_"))
async def callback_toggle_settings(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    action = callback.data.replace("toggle_", "")
    config = await get_system_config()
    
    key_mapping = {
        "bot_status": "bot_status",
        "withdrawals": "withdrawals_enabled",
        "device_check": "device_check",
        "spam_check": "spam_check",
        "two_fa": "two_fa_add",
        "name_change": "name_change",
        "bio_change": "bio_change"
    }
    
    if action in key_mapping:
        db_key = key_mapping[action]
        current_val = config.get(db_key, False)
        await update_system_config({db_key: not current_val})
        
        updated_config = await get_system_config()
        await callback.message.edit_text(
            "⚙️ **Manage Bot Operational Toggles:**",
            reply_markup=bot_settings_keyboard(updated_config)
        )
        await callback.answer("Setting updated successfully!")
