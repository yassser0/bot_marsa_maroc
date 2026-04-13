from motor.motor_asyncio import AsyncIOMotorClient
import os

# Database configuration
MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)

database = client.bot_builder

bot_collection = database.get_collection("bots_collection")

# Helper to format MongoDB document
def bot_helper(bot) -> dict:
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "url": bot["url"],
        "api_key": bot.get("api_key"),
        "prompt": bot.get("prompt"),
    }
