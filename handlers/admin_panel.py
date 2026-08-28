import os
import zipfile
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from utils import keyboards as kb

def register_admin_handlers(bot, config, tg_engine, admin_state):
    @bot.on_message(filters.command("admin") & filters.private)
    async def admin_command_handler(client, message: Message):
        user_id = message.from_user.id
        if user_id in config.admin_ids:
            # অ্যাডমিন কমান্ড দিলে পূর্বের সব পেন্ডিং স্টেট রিসেট হবে
            admin_state[user_id] = None
            await message.reply_text(
                "👑 Admin Control Panel",
                reply_markup=kb.get_main_admin_keyboard(),
            )
        else:
            await message.reply_text("❌ You are not authorized to use admin commands.")

    @bot.on_callback_query(filters.regex(r"^admin:"))
    async def admin_callback_handler(client, query: CallbackQuery):
        user_id = query.from_user.id
        if user_id not in config.admin_ids:
            await query.answer("You are not authorized.", show_alert=True)
            return

        await query.answer()
        data = query.data
        message = query.message
        if message is None:
            return

        if data == "admin:close":
            admin_state[user_id] = None
            await message.edit_text("🔒 Admin panel closed.")
            return

        if data == "admin:back":
            admin_state[user_id] = None
            await message.edit_text(
                "🔙 Main Menu",
                reply_markup=kb.get_main_admin_keyboard(),
            )
            return

        if data == "admin:2fa":
            await message.edit_text(
                "⚙️ 2FA Settings Menu",
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if data == "admin:2fa_toggle":
            if config.use_2fa:
                config.use_2fa = False
                config.custom_2fa_password = None
                status = "❌ 2FA disabled and the runtime password was cleared."
            elif config.custom_2fa_password:
                config.use_2fa = True
                status = "✅ 2FA enabled with your runtime password."
            else:
                admin_state[user_id] = "SET_2FA"
                await message.edit_text(
                    "Send a new 2FA password. It will only exist until the bot restarts.",
                    reply_markup=kb.get_back_to_main_keyboard(),
                )
                return

            await message.edit_text(
                status,
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if data == "admin:2fa_set":
            admin_state[user_id] = "SET_2FA"
            await message.edit_text(
                "Send a new 2FA password. It will only exist until the bot restarts.",
                reply_markup=kb.get_back_to_main_keyboard(),
            )
            return

        if data == "admin:countries":
            await message.edit_text(
                "🌐 Country Management Menu",
                reply_markup=kb.get_country_keyboard(),
            )
            return

        if data == "admin:countries_list":
            countries = ", ".join(config.allowed_countries) or "No countries configured."
            await message.edit_text(
                f"🌐 Countries Management:\n{countries}",
                reply_markup=kb.get_country_keyboard(),
            )
            return

        if data == "admin:country_add":
            admin_state[user_id] = "ADD_COUNTRY"
            await message.edit_text(
                "Send country Name, ISO code (e.g., BD), or Dial code (e.g., +880):",
                reply_markup=kb.get_back_to_main_keyboard(),
            )
            return

        if data == "admin:country_remove":
            admin_state[user_id] = "REMOVE_COUNTRY"
            await message.edit_text(
                "Send country Name, ISO code, or Dial code to remove:",
                reply_markup=kb.get_back_to_main_keyboard(),
            )
            return

        if data == "admin:export_all":
            await export_sessions(message, tg_engine, kb, mode="ALL")
            return

        if data == "admin:export_country":
            admin_state[user_id] = "EXPORT_COUNTRY"
            await show_country_stats(message, tg_engine, edit=True)
            return

    @bot.on_message(filters.private & filters.text)
    async def admin_message_handler(client, message: Message):
        user_id = message.from_user.id
        
        # অ্যাডমিন না হলে অথবা অ্যাডমিনের কোনো সক্রিয় প্যানেল স্টেট না থাকলে ইউজার হ্যান্ডলারে পাস করে দেবে
        if user_id not in config.admin_ids or admin_state.get(user_id) is None:
            await message.continue_propagation()
            return

        text = message.text.strip()
        state = admin_state.get(user_id)

        if text in ["/cancel", "❌ Cancel Process"]:
            admin_state[user_id] = None
            await message.reply_text(
                "❌ Process cancelled.",
                reply_markup=kb.get_main_admin_keyboard(),
            )
            return

        if state == "SET_2FA":
            if not text:
                await message.reply_text("Password cannot be empty. Send it again.")
                return
            config.custom_2fa_password = text
            config.use_2fa = True
            admin_state[user_id] = None
            await message.reply_text(
                "✅ 2FA password set and 2FA enabled until the bot restarts.",
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if state == "ADD_COUNTRY":
            matched = config.search_country_for_whitelist(text)
            if not matched:
                await message.reply_text("❌ No country found! Try sending Name, Code (e.g., BD), or Calling Code (e.g., +880).")
                return

            added_list = []
            for c in matched:
                if c["code"].upper() not in config.allowed_countries:
                    config.allowed_countries.append(c["code"].upper())
                    added_list.append(f"{c['name']} {c['flag']} ({c['code']})")

            admin_state[user_id] = None
            if added_list:
                msg = "✅ Added to Whitelist:\n" + "\n".join(added_list)
            else:
                msg = "⚠️ Selected country/countries are already in the Whitelist."
            
            await message.reply_text(msg, reply_markup=kb.get_country_keyboard())
            return

        if state == "REMOVE_COUNTRY":
            matched = config.search_country_for_whitelist(text)
            if not matched:
                await message.reply_text("❌ No country found!")
                return

            removed_list = []
            for c in matched:
                iso = c["code"].upper()
                if iso in config.allowed_countries:
                    config.allowed_countries.remove(iso)
                    removed_list.append(f"{c['name']} {c['flag']}")

            admin_state[user_id] = None
            if removed_list:
                msg = "✅ Removed from Whitelist:\n" + "\n".join(removed_list)
            else:
                msg = "❌ None of the matched countries were in the Whitelist."

            await message.reply_text(msg, reply_markup=kb.get_country_keyboard())
            return

        if state == "EXPORT_COUNTRY":
            country_code = text.upper()
            admin_state[user_id] = None
            await export_sessions(
                message,
                tg_engine,
                kb,
                mode="COUNTRY",
                country_code=country_code,
            )
            return

        # অন্য যেকোনো অব্যাখ্যায়িত টেক্সটের ক্ষেত্রে মেসেজ આગળ প্রোপাগেট হতে দেবে
        await message.continue_propagation()

async def show_country_stats(message: Message, tg_engine, edit=False):
    base_dir = tg_engine.storage_dir
    if not os.path.exists(base_dir):
        text = "📁 No sessions found."
    else:
        lines = ["📊 Available Sessions by Country:", ""]
        found = False
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                count = len(
                    [file for file in os.listdir(item_path) if file.endswith(".session")]
                )
                lines.append(f"Country {item}: {count} accounts")
                found = True
        text = "\n".join(lines) if found else "📂 Database is empty."
        if found:
            text += "\n\nSend the country code to export."

    if edit:
        await message.edit_text(text, reply_markup=kb.get_back_to_main_keyboard())
    else:
        await message.reply_text(text, reply_markup=kb.get_back_to_main_keyboard())

async def export_sessions(message: Message, tg_engine, keyboard_module, mode="ALL", country_code=None):
    base_dir = tg_engine.storage_dir
    target_dir = base_dir if mode == "ALL" else os.path.join(base_dir, country_code or "")

    if not os.path.exists(target_dir) or not os.listdir(target_dir):
        await message.reply_text(
            "❌ No sessions found to export.",
            reply_markup=keyboard_module.get_main_admin_keyboard(),
        )
        return

    msg = await message.reply_text("📦 Creating ZIP...")
    zip_name = f"sessions_{country_code or 'ALL'}.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, base_dir)
                zipf.write(full_path, arcname)

    await message.reply_document(
        document=zip_name,
        caption=f"✅ Exported Mode: {mode} | Code: {country_code or 'ALL'}",
    )
    os.remove(zip_name)
    await msg.delete()
