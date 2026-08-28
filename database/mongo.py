import logging
from motor.motor_asyncio import AsyncIOMotorClient
import config

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(config.MONGO_URI)
            self.db = self.client["telegram_automation_db"]
            logger.info("Successfully connected to MongoDB Atlas!")
            
            # Indexing for ultra-fast queries
            await self.db.users.create_index("user_id", unique=True)
            await self.db.countries.create_index("country_code", unique=True)
            await self.db.cards.create_index("card_name", unique=True)
            await self.db.sessions.create_index("phone_number", unique=True)
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

db_instance = MongoDB()

def get_db():
    return db_instance.db
