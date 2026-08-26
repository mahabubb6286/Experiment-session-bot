import os
import zipfile

from pyrogram import filters
from pyrogram.types import Message, ReplyKeyboardRemove

import keyboards as kb


def register_admin_handlers(bot, config, tg_engine, admin_state):
    @bot.on_message(filters.command("admin") & filters.private)
    async def admin_command_handler(client, message: Message):
        user_id = message.from_user.id
        if user_id in config.admin_ids:
            await message.reply_text(
                "👑 **Admin Control Panel**",
                reply_markup=kb.get_main_admin_keyboard(),
            )
        else:
            await message.reply_text("❌ You are not authorized to use admin commands.")

    @bot.on_message(filters.private & filters.text)
    async def admin_message_handler(client, message: Message):
        user_id = message.from_user.id
        if user_id not in config.admin_ids:
            await message.continue_propagation()
            return

        text = message.text.strip()

        if text in ["❌ Cancel Process", "/cancel"]:
            admin_state[user_id] = None
            await message.reply_text(
                "❌ Process cancelled successfully.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if text == "❌ Close Panel":
            admin_state[user_id] = None
            await message.reply_text(
                "🔒 Admin panel closed.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if text == "⬅️ Back to Main Menu":
            admin_state[user_id] = None
            await message.reply_text(
                "🔙 Main Menu",
                reply_markup=kb.get_main_admin_keyboard(),
            )
            return

        if text == "⚙️ 2FA Management":
            await message.reply_text(
                "⚙️ **2FA Settings Menu**",
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if text.startswith("2FA Status:"):
            config.use_2fa = not config.use_2fa
            status_str = "Enabled ✅" if config.use_2fa else "Disabled ❌"
            await message.reply_text(
                f"2FA Protection is now **{status_str}**",
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if text == "🔑 Set 2FA Password":
            admin_state[user_id] = "SET_2FA"
            await message.reply_text(
                f"Current Password: `{config.custom_2fa_password}`\nSend new password:"
            )
            return

        if text == "🌐 Allowed Countries":
            await message.reply_text(
                "🌐 **Country Management Menu**",
                reply_markup=kb.get_country_keyboard(),
            )
            return

        if text == "📋 List Countries":
            await message.reply_text(
                f"Allowed Countries: `{', '.join(config.allowed_countries)}`"
            )
            return

        if text == "➕ Add Country":
            admin_state[user_id] = "ADD_COUNTRY"
            await message.reply_text(
                "Send ISO Country Code to Add (e.g., `CL`, `US`, `BD`):"
            )
            return

        if text == "➖ Remove Country":
            admin_state[user_id] = "REMOVE_COUNTRY"
            await message.reply_text(
                "Send ISO Country Code to Remove (e.g., `CL`, `US`, `BD`):"
            )
            return

        if text == "📦 Import All Sessions":
            await export_sessions(message, tg_engine, kb, mode="ALL")
            return

        if text == "🌍 Country Wise Import":
            await show_country_stats(message, tg_engine)
            admin_state[user_id] = "EXPORT_COUNTRY"
            return

        state = admin_state.get(user_id)
        if state == "SET_2FA":
            config.custom_2fa_password = text
            admin_state[user_id] = None
            await message.reply_text(
                f"✅ 2FA Password updated to: `{text}`",
                reply_markup=kb.get_2fa_keyboard(config.use_2fa),
            )
            return

        if state == "ADD_COUNTRY":
            country_code = text.upper()
            if country_code not in config.allowed_countries:
                config.allowed_countries.append(country_code)
            admin_state[user_id] = None
            await message.reply_text(
                f"✅ Country `{country_code}` Added!",
                reply_markup=kb.get_country_keyboard(),
            )
            return

        if state == "REMOVE_COUNTRY":
            country_code = text.upper()
            if country_code in config.allowed_countries:
                config.allowed_countries.remove(country_code)
                await message.reply_text(
                    f"✅ Country `{country_code}` Removed!",
                    reply_markup=kb.get_country_keyboard(),
                )
            else:
                await message.reply_text(
                    f"❌ Country `{country_code}` is not in the allowed list.",
                    reply_markup=kb.get_country_keyboard(),
                )
            admin_state[user_id] = None
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

    return admin_message_handler


async def show_country_stats(message: Message, tg_engine):
    base_dir = tg_engine.storage_dir
    if not os.path.exists(base_dir):
        await message.reply_text("📁 No sessions found.")
        return

    text = "📊 **Available Sessions by Country:**\n\n"
    found = False
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            count = len(
                [file for file in os.listdir(item_path) if file.endswith(".session")]
            )
            text += f"🏁 **Country `{item}`**: `{count}` accounts\n"
            found = True

    if not found:
        text = "📂 Database is empty."
    else:
        text += "\n👇 **Type/Send the Country Code (e.g., CL, BD, US) to export:**"

    await message.reply_text(text)


async def export_sessions(
    message: Message,
    tg_engine,
    keyboard_module,
    mode="ALL",
    country_code=None,
):
    base_dir = tg_engine.storage_dir
    target_dir = (
        base_dir
        if mode == "ALL"
        else os.path.join(base_dir, country_code or "")
    )

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
        caption=f"✅ Exported Mode: `{mode}` | Code: `{country_code or 'ALL'}`",
    )
    os.remove(zip_name)
    await msg.delete()