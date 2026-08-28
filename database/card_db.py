from database.mongo import get_db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def init_card_db():
    """Initializes card database indexes if not present."""
    db = get_db()
    # Create unique or regular index on card_name for faster lookups
    await db.cards.create_index("card_name", unique=True)
    await db.withdrawals.create_index("user_id")
    logger.info("Card and withdrawal database indexes initialized successfully.")

async def create_card(card_name: str, owner_id: int, payment_method: str, details: str):
    db = get_db()
    card_data = {
        "card_name": card_name,
        "owner_id": owner_id,
        "payment_method": payment_method,
        "details": details,
        "created_at": datetime.utcnow()
    }
    await db.cards.update_one({"card_name": card_name}, {"$set": card_data}, upsert=True)

async def get_card(card_name: str):
    db = get_db()
    return await db.cards.find_one({"card_name": card_name})

async def log_withdrawal_request(user_id: int, card_name: str, amount: float, countries_summary: str, message_id: int = None):
    db = get_db()
    log = {
        "user_id": user_id,
        "card_name": card_name,
        "amount": amount,
        "countries_summary": countries_summary,
        "status": "pending",
        "message_id": message_id,
        "timestamp": datetime.utcnow()
    }
    result = await db.withdrawals.insert_one(log)
    return result.inserted_id

async def mark_withdrawal_paid(withdrawal_id):
    db = get_db()
    from bson.objectid import ObjectId
    await db.withdrawals.update_one({"_id": ObjectId(withdrawal_id)}, {"$set": {"status": "paid"}})
