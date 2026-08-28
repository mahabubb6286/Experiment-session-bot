from database.mongo import get_db
from datetime import datetime

async def save_session(phone_number: str, country_code: str, session_str: str, account_type: str, user_id: int, status: str = "valid"):
    db = get_db()
    session_data = {
        "phone_number": phone_number,
        "country_code": country_code,
        "session_str": session_str,
        "account_type": account_type, # 'new' or 'free'
        "user_id": user_id,
        "status": status, # 'valid', 'spam', 'contact_restricted', 'frozen', 'bad'
        "exported": False,
        "added_at": datetime.utcnow()
    }
    await db.sessions.update_one({"phone_number": phone_number}, {"$set": session_data}, upsert=True)

async def get_sessions_by_country(country_code: str, account_type: str = None, exported: bool = False):
    db = get_db()
    query = {"country_code": country_code, "exported": exported}
    if account_type:
        query["account_type"] = account_type
    return await db.sessions.find(query).to_list(length=None)
