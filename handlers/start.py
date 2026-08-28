import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.user_db import create_user
from database.config_db import get_system_config

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = (
        f"❓ **How to use this Bot:**\n\n"
        f"1. Send any valid Telegram phone number with country code (e.g., `+1234567890`).\n"
        f"2. Wait for OTP confirmation message.\n"
        f"3. Send the received 5-digit code.\n"
        f"4. The bot will automatically set 2FA and generate a fresh session."
    )
    await message.reply_text(help_text)
