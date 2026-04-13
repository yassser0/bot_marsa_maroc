from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx

app = FastAPI(title="Bot Builder API", version="1.0.0")

# Allow requests from the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database for quick start (To be replaced with SQLite/SQLAlchemy)
bots_db = [
    {"id": 1, "name": "Maroc-Assistant", "url": "mock_api", "api_key": "xxx", "prompt": "Tu es l'assistant de Marsa Maroc."}
]

class BotCreate(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None
    prompt: Optional[str] = None

class MessageRequest(BaseModel):
    bot_id: int
    message: str

@app.get("/bots")
def get_bots():
    return bots_db

@app.post("/bots/")
def create_bot(bot: BotCreate):
    new_bot = {
        "id": len(bots_db) + 1,
        "name": bot.name,
        "url": bot.url,
        "api_key": bot.api_key,
        "prompt": bot.prompt
    }
    bots_db.append(new_bot)
    return new_bot

@app.post("/chat")
async def chat_with_bot(req: MessageRequest):
    bot = next((b for b in bots_db if b["id"] == req.bot_id), None)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Si c'est notre bot de test local, on simule une réponse
    if bot["url"] == "mock_api":
        return {
            "reply": f"Ceci est une réponse simulée par le bot {bot['name']}. Vous avez dit : '{req.message}'"
        }

    # Si c'est une vraie API (ex: OpenAI), on fait la requête HTTP
    # C'est ici que l'agent prend le relais pour communiquer "comme un chatbot"
    try:
        headers = {}
        if bot["api_key"]:
            headers["Authorization"] = f"Bearer {bot['api_key']}"
            
        async with httpx.AsyncClient() as client:
            # Ex: Assuming the target is an OpenAI compatible endpoint
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": bot.get("prompt", "")},
                    {"role": "user", "content": req.message}
                ]
            }
            response = await client.post(bot["url"], json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            # Try to parse standard OpenAI response format, fallback to string dump
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
            return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de communication avec l'API externe: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "SaaS Bot Builder API en ligne."}
