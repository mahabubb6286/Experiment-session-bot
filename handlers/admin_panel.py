import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database.config_db import get_system_config
from database.user_db import get_all_users
from utils.keyboards import main_admin_keyboard, return_to_dashboard_button

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    admins = config.get("admins", [])
    return user_id in admins

@Client.on_message(filters.command("admin") & filters.private)
async def admin_dashboard_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await is_admin(user_id):
        return
        
    admin_text = (
        f"⚡ **Welcome to Main Admin Dashboard**\n\n"
        f"Select an option below to manage bot settings, whitelist countries, export sessions, and handle withdrawal cards."
    )
    await message.reply_text(admin_text, reply_markup=main_admin_keyboard())

@Client.on_callback_query(filters.regex("^admin_dashboard$"))
async def callback_admin_dashboard(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    admin_text = (
        f"⚡ **Welcome to Main Admin Dashboard**\n\n"
        f"Select an option below to manage bot settings, whitelist countries, export sessions, and handle withdrawal cards."
    )
    await callback.message.edit_text(admin_text, reply_markup=main_admin_keyboard())

@Client.on_callback_query(filters.regex("^admin_stats$"))
async def callback_admin_stats(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    users = await get_all_users()
    total_users = len(users)
    blocked_users = len([u for u in users if u.get("is_blocked")])
    
    stats_text = (
        f"📊 **System Overall Statistics**\n\n"
        f"👥 **Total Registered Users:** `{total_users}`\n"
        f"🚫 **Blocked Users:** `{blocked_users}`\n\n"
        f"⚙️ System status is currently operational."
    )
    await callback.message.edit_text(stats_text, reply_markup=return_to_dashboard_button())
