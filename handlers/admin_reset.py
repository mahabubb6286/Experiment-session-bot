import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.config_db import get_system_config
from utils.keyboards import return_to_dashboard_button

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    return user_id in config.get("admins", [])

@Client.on_callback_query(filters.regex("^admin_reset$"))
async def callback_admin_reset_menu(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    text = (
        f"⚠️ **DANGER ZONE: System Data Reset**\n\n"
        f"Select an option below to reset database entries. This action **cannot be undone**."
    )
    
    buttons = [
        [InlineKeyboardButton("🗑 Reset All Sessions Data", callback_data="reset_confirm_sessions")],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^reset_confirm_sessions$"))
async def callback_reset_confirm(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    # Safety confirmation prompt
    await callback.answer("Action requires double confirmation.", show_alert=True)
    await callback.message.edit_text(
        "❓ **Are you absolutely sure you want to clear session database?**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data="reset_execute_sessions")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_reset")]
        ])
    )
