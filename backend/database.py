from motor.motor_asyncio import AsyncIOMotorClient
import os

# Database configuration
MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)

database = client.bot_builder

bot_collection = database.get_collection("bots_collection")
messages_collection = database.get_collection("messages")

# Helper to format MongoDB document
def bot_helper(bot) -> dict:
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "url": bot["url"],
        "api_key": bot.get("api_key"),
        "model_name": bot.get("model_name", "gpt-3.5-turbo"),
        "prompt": bot.get("prompt"),
        "tools": bot.get("tools", []), # Dynamic list of REST tools
    }

# Helper for messages
def message_helper(msg) -> dict:
    res = {
        "id": str(msg["_id"]),
        "bot_id": msg["bot_id"],
        "role": msg["role"], # 'user', 'assistant' or 'tool'
        "content": msg.get("content", ""),
        "timestamp": msg.get("timestamp")
    }
    if "tool_calls" in msg:
        res["tool_calls"] = msg["tool_calls"]
    if "tool_call_id" in msg:
        res["tool_call_id"] = msg["tool_call_id"]
    if "name" in msg:
        res["name"] = msg["name"]
    return res
