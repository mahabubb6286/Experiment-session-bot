import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.config_db import get_system_config
from database.session_db import get_all_sessions
from utils.keyboards import return_to_dashboard_button

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    return user_id in config.get("admins", [])

@Client.on_callback_query(filters.regex("^admin_sessions$"))
async def callback_sessions_menu(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    sessions = await get_all_sessions()
    valid_sessions = [s for s in sessions if s.get("status") == "valid"]
    
    text = (
        f"🔐 **Session Vault**\n\n"
        f"📦 **Total Valid Sessions:** `{len(valid_sessions)}`\n\n"
        f"Choose an export option below:"
    )
    
    buttons = [
        [InlineKeyboardButton("⬇️ Download All (.zip)", callback_data="export_sessions_zip")],
        [InlineKeyboardButton("⬇️ Export by Country", callback_data="export_sessions_country")],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    
@Client.on_callback_query(filters.regex("^export_sessions_zip$"))
async def callback_export_zip(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    await callback.answer("Generating ZIP file... Please wait.", show_alert=False)
    # The actual ZIP generation logic utilizing utils.helpers.create_zip_in_memory will go here.
    # We will implement the full export logic later based on your preference.
    await callback.message.reply_text("ZIP export triggered (Placeholder).")
