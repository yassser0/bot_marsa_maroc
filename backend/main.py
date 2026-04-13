from fastapi import FastAPI, HTTPException, Body
from datetime import datetime
import time
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from bson import ObjectId
from database import bot_collection, bot_helper, messages_collection, message_helper, client

app = FastAPI(title="Bot Builder API", version="1.1.0")

# Allow requests from the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    try:
        await client.admin.command('ping')
        print("✅ MongoDB est connecté !")
    except Exception as e:
        print("❌ ERREUR : Impossible de se connecter à MongoDB. Vérifiez Docker.")

class BotCreate(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"
    prompt: Optional[str] = None

class MessageRequest(BaseModel):
    bot_id: str  # Updated to str for MongoDB ObjectId
    message: str

@app.get("/bots")
async def get_bots():
    bots = []
    async for bot in bot_collection.find():
        bots.append(bot_helper(bot))
    return bots

@app.get("/bots/{bot_id}/messages")
async def get_bot_messages(bot_id: str):
    messages = []
    async for msg in messages_collection.find({"bot_id": bot_id}).sort("timestamp", 1):
        messages.append(message_helper(msg))
    return messages

@app.post("/bots/")
async def create_bot(bot: BotCreate):
    new_bot = bot.dict()
    result = await bot_collection.insert_one(new_bot)
    created_bot = await bot_collection.find_one({"_id": result.inserted_id})
    return bot_helper(created_bot)

@app.post("/chat")
async def chat_with_bot(req: MessageRequest):
    try:
        obj_id = ObjectId(req.bot_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Bot ID format")

    bot = await bot_collection.find_one({"_id": obj_id})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Mock API handling
    if bot["url"] == "mock_api":
        return {
            "reply": f"Ceci est une réponse simulée par le bot {bot['name']}. Vous avez dit : '{req.message}'"
        }

    # PERSISTENT MEMORY: Fetch context
    history = []
    async for msg in messages_collection.find({"bot_id": req.bot_id}).sort("timestamp", -1).limit(10):
        # Backward compatibility: map 'bot' to 'assistant'
        role = "assistant" if msg["role"] == "bot" else msg["role"]
        history.append({"role": role, "content": msg["content"]})
    history.reverse()

    # Save User message
    await messages_collection.insert_one({
        "bot_id": req.bot_id,
        "role": "user",
        "content": req.message,
        "timestamp": datetime.now()
    })

    try:
        headers = {}
        if bot.get("api_key"):
            api_key = bot["api_key"].strip()
            if not api_key.startswith("Bearer "):
                api_key = f"Bearer {api_key}"
            headers["Authorization"] = api_key
            
        # Prepare context payload
        messages_payload = [{"role": "system", "content": bot.get("prompt", "")}]
        messages_payload.extend(history)
        messages_payload.append({"role": "user", "content": req.message})

        async with httpx.AsyncClient() as client_http:
            payload = {
                "model": bot.get("model_name", "gpt-3.5-turbo"),
                "messages": messages_payload
            }
            response = await client_http.post(bot["url"], json=payload, headers=headers, timeout=15.0)
            
            if response.status_code != 200:
                print(f"API ERROR: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="API Error")

            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", str(data))

            # Save Bot reply
            await messages_collection.insert_one({
                "bot_id": req.bot_id,
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now()
            })

            return {"reply": reply}
    except Exception as e:
        print(f"DEBUG API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur système: {str(e)}")

@app.post("/simulate-ai")
async def simulate_ai(payload: dict = Body(...)):
    """Simule une réponse d'IA au format standard (OpenAI compatible)"""
    user_message = "..."
    # On essaie d'extraire le message envoyé pour l'inclure dans la réponse
    messages = payload.get("messages", [])
    if messages:
        user_message = messages[-1].get("content", "...")
    
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": f"[SIMULATION IA] J'ai bien reçu votre message : '{user_message}'. Je suis configuré pour répondre via l'endpoint de test de Marsa Maroc."
                }
            }
        ]
    }

@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    try:
        obj_id = ObjectId(bot_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Bot ID format")
    
    result = await bot_collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {"message": "Bot supprimé avec succès"}

@app.get("/")
def read_root():
    return {"message": "SaaS Bot Builder API (MongoDB Mode) en ligne."}
