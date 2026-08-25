import asyncio
import nest_asyncio

# Python 3.14 Event Loop Patch
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from telegram_engine import TelegramEngine
from converter_engine import ConverterEngine

# বাকি কোড অপরিবর্তিত থাকবে...

# Environment variables load
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")

# Bot initialization
app = Client("session_generator_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

tg_engine = TelegramEngine()
conv_engine = ConverterEngine()

# User session State Store
user_states = {}

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    text = (
        "👋 **Welcome to Telegram Session Generator Bot!**\n\n"
        "Please send your phone number with country code.\n"
        "**Example:** `+8801700000000`"
    )
    await message.reply_text(text)

@app.on_message(filters.private & filters.text)
async def message_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Step 1: Phone number input handling
    if text.startswith("+"):
        msg = await message.reply_text("🔄 Connecting Proxy & Sending OTP...")
        try:
            res = await tg_engine.send_otp(text)
            user_states[user_id] = {
                "step": "WAITING_OTP",
                "phone": text,
                "client": res["client"],
                "phone_hash": res["phone_hash"]
            }
            await msg.edit_text("✅ OTP sent successfully!\n\nPlease enter the OTP code you received:")
        except Exception as e:
            await msg.edit_text(f"❌ Error sending OTP: {str(e)}")
        return

    # Step 2: OTP input handling
    if user_id in user_states and user_states[user_id]["step"] == "WAITING_OTP":
        state = user_states[user_id]
        otp_code = text
        msg = await message.reply_text("🔄 Verifying OTP & Setting up 2FA...")

        try:
            res = await tg_engine.complete_login(
                client=state["client"],
                phone_number=state["phone"],
                phone_hash=state["phone_hash"],
                otp_code=otp_code
            )

            if res.get("status") == "error":
                await msg.edit_text(f"❌ Login Failed: {res.get('message')}")
                return

            await msg.edit_text("📦 Converting Session to Tdata & Creating ZIP Package...")
            
            # Zip file package creation
            zip_file = await conv_engine.create_zip_package(
                session_string=res["session_string"],
                api_id=API_ID,
                api_hash=API_HASH,
                phone_number=state["phone"],
                two_fa_password=res["two_fa_password"]
            )

            # Send zip file to user
            caption = f"✅ **Session Created Successfully!**\n\n📌 Phone: `{state['phone']}`\n🔑 2FA Password: `{res['two_fa_password']}`"
            await message.reply_document(document=zip_file, caption=caption)
            await msg.delete()

            # Cleanup
            if os.path.exists(zip_file):
                os.remove(zip_file)
            del user_states[user_id]

        except Exception as e:
            await msg.edit_text(f"❌ Processing Error: {str(e)}")
        return

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run()
