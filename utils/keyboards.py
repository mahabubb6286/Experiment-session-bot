from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_admin_keyboard():
    buttons = [
        [InlineKeyboardButton("📊 System Statistics", callback_data="admin_stats"), InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_bot_settings")],
        [InlineKeyboardButton("👥 Users Management", callback_data="admin_users"), InlineKeyboardButton("🌍 Countries Management", callback_data="admin_countries")],
        [InlineKeyboardButton("🔐 Session Vault", callback_data="admin_sessions"), InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🛠 Backend Controls", callback_data="admin_backend"), InlineKeyboardButton("💳 Card Management", callback_data="admin_cards")],
        [InlineKeyboardButton("📝 Edit Messages", callback_data="admin_edit_msg"), InlineKeyboardButton("📢 Channels", callback_data="admin_channels")],
        [InlineKeyboardButton("⚡ Functionality", callback_data="admin_functionality"), InlineKeyboardButton("🔑 API Manage", callback_data="admin_api")],
        [InlineKeyboardButton("🚫 Bad Account List", callback_data="admin_bad_accs"), InlineKeyboardButton("🔄 Reset Operations", callback_data="admin_reset_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def bot_settings_keyboard(config: dict):
    def get_status_str(val):
        return "🟢 Enabled" if val else "🔴 Disabled"

    buttons = [
        [InlineKeyboardButton(f"Bot Status: {'✅ ON' if config.get('bot_status') else '❌ OFF'}", callback_data="toggle_bot_status")],
        [InlineKeyboardButton(f"Withdrawals: {get_status_str(config.get('withdrawals_enabled'))}", callback_data="toggle_withdrawals")],
        [InlineKeyboardButton(f"Device Check: {get_status_str(config.get('device_check'))}", callback_data="toggle_device_check")],
        [InlineKeyboardButton(f"Spam Check: {get_status_str(config.get('spam_check'))}", callback_data="toggle_spam_check")],
        [InlineKeyboardButton(f"2FA Add: {get_status_str(config.get('two_fa_add'))}", callback_data="toggle_two_fa")],
        [InlineKeyboardButton(f"Name Change: {get_status_str(config.get('name_change'))}", callback_data="toggle_name_change")],
        [InlineKeyboardButton(f"Bio Change: {get_status_str(config.get('bio_change'))}", callback_data="toggle_bio_change")],
        [InlineKeyboardButton("🔙 Return to Dashboard", callback_data="admin_dashboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def return_to_dashboard_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return to Dashboard", callback_data="admin_dashboard")]])
