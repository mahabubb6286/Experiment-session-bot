import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.config_db import get_system_config
from database.country_db import get_all_countries, update_country, delete_country
from utils.keyboards import return_to_dashboard_button

logger = logging.getLogger(__name__)

# Temporary states for admin input
ADMIN_STATES = {}

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    return user_id in config.get("admins", [])

@Client.on_callback_query(filters.regex("^admin_countries$"))
async def callback_countries_menu(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    countries = await get_all_countries()
    text = "🌍 **Active Countries & Pricing**\n\n"
    
    if not countries:
        text += "No countries configured yet."
    else:
        for c in countries:
            text += f"▪️ {c['name']} ({c['code']}): ${c['price']}\n"
            
    text += "\n\n_To update or add a country, send a message in this format:_\n`+1 = 0.50`"
    
    # Store state to expect country input
    ADMIN_STATES[callback.from_user.id] = "waiting_for_country_price"
    
    await callback.message.edit_text(text, reply_markup=return_to_dashboard_button())

@Client.on_message(
    filters.text
    & filters.private
    & ~filters.command(["start", "help", "admin"])
)
async def handle_admin_text_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_STATES or not await is_admin(user_id):
        return
        
    state = ADMIN_STATES[user_id]
    text = message.text.strip()
    
    if state == "waiting_for_country_price":
        if "=" not in text:
            await message.reply_text("❌ Invalid format. Use: `+Code = Price` (e.g. `+1 = 0.50`)")
            return
            
        try:
            parts = text.split("=")
            code = parts[0].strip()
            price = float(parts[1].strip())
            
            if not code.startswith("+"):
                code = f"+{code}"
                
            await update_country(code, "Unknown", price)
            await message.reply_text(f"✅ **Country Updated:**\nCode: {code}\nPrice: ${price:.2f}", reply_markup=return_to_dashboard_button())
            del ADMIN_STATES[user_id]
        except ValueError:
            await message.reply_text("❌ Invalid price format. Must be a number.")
