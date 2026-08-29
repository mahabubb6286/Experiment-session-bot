import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.user_db import create_user, get_user
from database.config_db import get_system_config
from database.country_db import get_all_countries, get_country
from database.card_db import get_card, log_withdrawal_request
from database.session_db import save_session
from services.telegram_engine import TelegramEngine
from utils.helpers import parse_phone_details, format_withdraw_report

logger = logging.getLogger(__name__)

# Temporary in-memory state for user OTP flow
USER_OTP_STATES = {}

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await create_user(user_id, username, first_name)
    config = await get_system_config()
    
    if not config.get("bot_status", True) and user_id not in config.get("admins", []):
        await message.reply_text("🔴 **Bot is currently under maintenance.** Please check back later.")
        return

    welcome_text = (
        f"👋 **Welcome {first_name}!**\n\n"
        f"🤖 **Telegram Session & OTP Automation Bot**\n"
        f"Send any valid Telegram phone number with country code (e.g., `+1234567890`) to start generating session."
    )
    
    buttons = [
        [InlineKeyboardButton("💳 My Balance & Cards", callback_data="user_balance")]
    ]

    update_channel = str(config.get("update_channel") or "").strip()
    if update_channel.startswith(("https://", "http://")):
        buttons.append([InlineKeyboardButton("📢 Updates Channel", url=update_channel)])

    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "admin"]))
async def handle_user_text_input(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    user_data = await get_user(user_id)
    if user_data and user_data.get("is_blocked"):
        await message.reply_text("🚫 **Your account has been restricted from using this bot.**")
        return

    # 1. OTP INPUT FLOW
    if user_id in USER_OTP_STATES:
        state = USER_OTP_STATES[user_id]
        phone_number = state["phone"]
        engine = state["engine"]
        
        status_msg = await message.reply_text("🔄 **Verifying OTP and analyzing account status...**")
        
        try:
            result = await engine.process_account_login(text, user_id)
            
            if result["status"] == "rejected":
                await status_msg.edit_text(result["message"])
                del USER_OTP_STATES[user_id]
                return
                
            if result["status"] == "success":
                account_type = result["account_type"]
                session_str = result["session_str"]
                phone_info = parse_phone_details(phone_number)
                
                country_code = phone_info["country_code"] if phone_info else "Unknown"
                
                # Save session to database
                await save_session(
                    phone_number=phone_number,
                    country_code=country_code,
                    session_str=session_str,
                    account_type=account_type,
                    user_id=user_id,
                    status="valid"
                )
                
                await status_msg.edit_text(
                    f"✅ **Account Processed Successfully!**\n\n"
                    f"📱 **Phone:** `{phone_number}`\n"
                    f"🏷 **Type:** `{account_type.upper()}`\n"
                    f"🔐 **2FA Password Set:** Enabled"
                )
                del USER_OTP_STATES[user_id]
                return

        except Exception as e:
            logger.error(f"Error processing OTP: {e}")
            await status_msg.edit_text("❌ **Invalid OTP Code or expired session.** Please try again.")
            del USER_OTP_STATES[user_id]
            return

    # 2. PHONE NUMBER INPUT FLOW
    if text.startswith("+") or text.isdigit():
        phone_info = parse_phone_details(text)
        if not phone_info:
            await message.reply_text("❌ **Invalid phone number format.** Example: `+1234567890`")
            return
            
        country = await get_country(phone_info["country_code"])
        if not country:
            await message.reply_text(f"⚠️ **Country {phone_info['country_code']} is not whitelisted by Admin.**")
            return

        status_msg = await message.reply_text(f"⚡ **Sending OTP to {phone_info['phone']}...**")
        
        try:
            engine = TelegramEngine(phone_info["phone"])
            await engine.send_otp()
            
            USER_OTP_STATES[user_id] = {
                "phone": phone_info["phone"],
                "engine": engine
            }
            
            await status_msg.edit_text(
                f"📩 **OTP Sent to {phone_info['phone']}!**\n\n"
                f"Please reply with the 5-digit code received on Telegram."
            )
        except Exception as e:
            logger.error(f"OTP send error: {e}")
            await status_msg.edit_text(f"❌ **Failed to send OTP:** {str(e)}")
