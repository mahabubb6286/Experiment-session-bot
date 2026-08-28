from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel Process", callback_data="user:cancel")]]
    )


def get_main_admin_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📦 Import All Sessions", callback_data="admin:export_all"),
                InlineKeyboardButton("🌍 Country Wise Import", callback_data="admin:export_country"),
            ],
            [
                InlineKeyboardButton("⚙️ 2FA Management", callback_data="admin:2fa"),
                InlineKeyboardButton("🌐 Allowed Countries", callback_data="admin:countries"),
            ],
            [InlineKeyboardButton("❌ Close Panel", callback_data="admin:close")],
        ]
    )


def get_2fa_keyboard(use_2fa: bool):
    status_text = "✅ 2FA is ON" if use_2fa else "❌ 2FA is OFF"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(status_text, callback_data="admin:2fa_toggle")],
            [InlineKeyboardButton("🔑 Set 2FA Password", callback_data="admin:2fa_set")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="admin:back")],
        ]
    )


def get_country_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 List Countries", callback_data="admin:countries_list"),
                InlineKeyboardButton("➕ Add Country", callback_data="admin:country_add"),
            ],
            [InlineKeyboardButton("➖ Remove Country", callback_data="admin:country_remove")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="admin:back")],
        ]
    )


def get_back_to_main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="admin:back")]]
    )
