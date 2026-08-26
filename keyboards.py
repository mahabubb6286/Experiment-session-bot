from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("❌ Cancel Process")]],
        resize_keyboard=True
    )

def get_main_admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📦 Import All Sessions"), KeyboardButton("🌍 Country Wise Import")],
            [KeyboardButton("⚙️ 2FA Management"), KeyboardButton("🌐 Allowed Countries")],
            [KeyboardButton("❌ Close Panel")]
        ],
        resize_keyboard=True
    )

def get_2fa_keyboard(use_2fa: bool):
    status_icon = "✅" if use_2fa else "❌"
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(f"2FA Status: {status_icon}"), KeyboardButton("🔑 Set 2FA Password")],
            [KeyboardButton("⬅️ Back to Main Menu")]
        ],
        resize_keyboard=True
    )

def get_country_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📋 List Countries"), KeyboardButton("➕ Add Country")],
            [KeyboardButton("➖ Remove Country"), KeyboardButton("⬅️ Back to Main Menu")]
        ],
        resize_keyboard=True
    )
