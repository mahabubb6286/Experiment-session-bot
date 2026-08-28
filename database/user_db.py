from database.mongo import get_db

async def get_user(user_id: int):
    db = get_db()
    return await db.users.find_one({"user_id": user_id})

async def create_user(user_id: int, username: str = None, first_name: str = None):
    db = get_db()
    user = await get_user(user_id)
    if not user:
        new_user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "balance": 0.0,
            "is_blocked": False,
            "total_accounts": 0,
            "confirmed_new": 0,
            "confirmed_free": 0,
            "withdrawals_paid": 0.0,
            "withdrawal_requests": 0.0
        }
        await db.users.insert_one(new_user)
        return new_user
    return user

async def update_user_balance(user_id: int, amount: float, operation: str = "add"):
    db = get_db()
    user = await get_user(user_id)
    if user:
        new_balance = user["balance"] + amount if operation == "add" else user["balance"] - amount
        new_balance = max(0.0, round(new_balance, 4))
        await db.users.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
        return new_balance
    return 0.0

async def set_user_block_status(user_id: int, status: bool):
    db = get_db()
    await db.users.update_one({"user_id": user_id}, {"$set": {"is_blocked": status}})

async def get_all_users():
    db = get_db()
    return await db.users.find({}).to_list(length=None)
