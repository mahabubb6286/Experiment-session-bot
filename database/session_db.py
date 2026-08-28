import logging
from database.mongo import get_db

logger = logging.getLogger(__name__)

async def init_session_db():
    """Initializes session database indexes if not present."""
    db = get_db()
    # Create indexes for fast query handling
    await db.sessions.create_index("user_id")
    logger.info("Session database indexes initialized successfully.")

async def add_session(user_id: int, session_string: str, phone_number: str = None):
    db = get_db()
    session_data = {
        "user_id": user_id,
        "session_string": session_string,
        "phone_number": phone_number,
        "status": "active"
    }
    await db.sessions.insert_one(session_data)

async def get_user_sessions(user_id: int):
    db = get_db()
    sessions = []
    async for s in db.sessions.find({"user_id": user_id}):
        sessions.append(s)
    return sessions

async def delete_session(user_id: int, session_string: str):
    db = get_db()
    await db.sessions.delete_one({"user_id": user_id, "session_string": session_string})

async def get_all_sessions():
    db = get_db()
    sessions = []
    async for s in db.sessions.find({}):
        sessions.append(s)
    return sessions
