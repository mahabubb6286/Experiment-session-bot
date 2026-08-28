from database.mongo import get_db

async def add_or_update_country(country_code: str, country_name: str, short_name: str, new_price: float, free_price: float, capacity: int, verify_time: int):
    db = get_db()
    data = {
        "country_code": country_code,
        "country_name": country_name,
        "short_name": short_name,
        "new_price": float(new_price),
        "free_price": float(free_price),
        "capacity": int(capacity),
        "used_capacity": 0,
        "verify_time": int(verify_time),
        "spam_check": True,
        "contact_check": True,
        "use_proxy": True,
        "allowed_devices": {
            "android": True,
            "iphone": True,
            "win": True,
            "mac": True
        }
    }
    await db.countries.update_one({"country_code": country_code}, {"$set": data}, upsert=True)

async def get_country(country_code: str):
    db = get_db()
    return await db.countries.find_one({"country_code": country_code})

async def get_all_countries():
    db = get_db()
    return await db.countries.find({}).to_list(length=None)

async def remove_country(country_code: str):
    db = get_db()
    await db.countries.delete_one({"country_code": country_code})
