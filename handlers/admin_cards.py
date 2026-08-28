import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from database.config_db import get_system_config
from database.card_db import get_all_cards, add_card, delete_card
from utils.keyboards import return_to_dashboard_button

logger = logging.getLogger(__name__)

# Temporary states handled globally or imported if shared
ADMIN_STATES = {}

async def is_admin(user_id: int) -> bool:
    config = await get_system_config()
    return user_id in config.get("admins", [])

@Client.on_callback_query(filters.regex("^admin_cards$"))
async def callback_cards_menu(client: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Unauthorized!", show_alert=True)
        
    cards = await get_all_cards()
    text = "💳 **Withdrawal Cards Management**\n\n"
    
    if not cards:
        text += "No cards available."
    else:
        for idx, card in enumerate(cards):
            status = "🟢 Active" if card.get("is_active", True) else "🔴 Disabled"
            card_name = card.get('card_name', 'Unknown')
            min_amt = card.get('min_amount', 0)
            fee = card.get('fee_percentage', 0)
            text += f"{idx+1}. **{card_name}**\n   Min: ${min_amt} | Fee: {fee}%\n   Status: {status}\n\n"
            
    text += "_To add a new card, send a message in this format:_\n`Name | Min Amount | Fee %`\nExample: `Binance Pay | 5.0 | 2`"
    
    # Store state
    ADMIN_STATES[callback.from_user.id] = "waiting_for_card_add"
    
    await callback.message.edit_text(text, reply_markup=return_to_dashboard_button())

@Client.on_message(filters.text & filters.private, group=1)
async def handle_card_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_STATES or not await is_admin(user_id):
        return
        
    state = ADMIN_STATES[user_id]
    text = message.text.strip()
    
    if state == "waiting_for_card_add":
        try:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) != 3:
                raise ValueError
                
            name = parts[0]
            min_amt = float(parts[1])
            fee = float(parts[2])
            
            await add_card(name, min_amt, fee)
            await message.reply_text(f"✅ **Card Added:** {name}", reply_markup=return_to_dashboard_button())
            del ADMIN_STATES[user_id]
        except ValueError:
            await message.reply_text("❌ Invalid format. Use: `Name | Min Amount | Fee %`")
