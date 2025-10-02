from datetime import datetime
from typing import Optional
import pymongo
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.whispers = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client.whisper_bot
        self.whispers = self.db.whispers
        await self.whispers.create_index([("created_at", pymongo.DESCENDING)])
        await self.whispers.create_index([("whisper_id", pymongo.HASHED)])

    async def close(self):
        if self.client:
            self.client.close()

    async def create_whisper(self, from_user: dict, target_username: str, secret_text: str) -> str:
        whisper_id = str(ObjectId())
        
        whisper_data = {
            "whisper_id": whisper_id,
            "from_user": {
                "id": from_user["id"],
                "username": from_user.get("username"),
                "first_name": from_user.get("first_name"),
                "last_name": from_user.get("last_name")
            },
            "target_username": target_username.lower().replace("@", ""),
            "secret_text": secret_text,
            "created_at": datetime.utcnow(),
            "opened_at": None,
            "opened_by": None
        }
        
        await self.whispers.insert_one(whisper_data)
        return whisper_id

    async def get_whisper(self, whisper_id: str) -> Optional[dict]:
        return await self.whispers.find_one({"whisper_id": whisper_id})

    async def mark_whisper_opened(self, whisper_id: str, user_id: int):
        await self.whispers.update_one(
            {"whisper_id": whisper_id},
            {
                "$set": {
                    "opened_at": datetime.utcnow(),
                    "opened_by": user_id
                }
            }
        )

db = Database()
