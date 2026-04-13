from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from bson import ObjectId
from database import bot_collection, bot_helper

app = FastAPI(title="Bot Builder API", version="1.1.0")

# Allow requests from the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # External API Integration
    try:
        headers = {}
        if bot.get("api_key"):
            api_key = bot["api_key"].strip()
            if not api_key.startswith("Bearer "):
                api_key = f"Bearer {api_key}"
            headers["Authorization"] = api_key
            
        async with httpx.AsyncClient() as client:
            payload = {
                "model": bot.get("model_name", "gpt-3.5-turbo"),
                "messages": [
                    {"role": "system", "content": bot.get("prompt", "")},
                    {"role": "user", "content": req.message}
                ]
            }
            response = await client.post(bot["url"], json=payload, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_detail = response.json()
                except:
                    pass
                print(f"GROQ ERROR ({response.status_code}): {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=f"Erreur Groq: {error_detail}")

            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
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
