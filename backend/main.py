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

class ToolConfig(BaseModel):
    name: str
    description: str
    url: str
    method: str = "GET"

class BotCreate(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"
    prompt: Optional[str] = None
    tools: Optional[List[ToolConfig]] = []

class MessageRequest(BaseModel):
    bot_id: str  # Updated to str for MongoDB ObjectId
    message: str

class UserTest(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    role: str
    status: Optional[str] = "Active"

# --- MOCK USER DATA ---
MOCK_USERS = [
    {"id": "1", "name": "Yassine", "email": "yassin@marsamaroc.ma", "role": "Admin", "status": "Active"},
    {"id": "2", "name": "Ahmed", "email": "ahmed@marsamaroc.ma", "role": "Operator", "status": "Active"},
    {"id": "3", "name": "Sara", "email": "sara@marsamaroc.ma", "role": "Logistics", "status": "Inactive"},
    {"id": "4", "name": "Khalid", "email": "khalid@marsamaroc.ma", "role": "IT Support", "status": "Active"},
    {"id": "5", "name": "Fatima", "email": "fatima@marsamaroc.ma", "role": "Management", "status": "Active"},
]

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

@app.delete("/bots/{bot_id}/messages")
async def delete_bot_messages(bot_id: str):
    await messages_collection.delete_many({"bot_id": bot_id})
    return {"message": "Historique supprimé avec succès"}

@app.post("/bots/")
async def create_bot(bot: BotCreate):
    new_bot = bot.dict()
    result = await bot_collection.insert_one(new_bot)
    created_bot = await bot_collection.find_one({"_id": result.inserted_id})
    return bot_helper(created_bot)

@app.put("/bots/{bot_id}")
async def update_bot(bot_id: str, bot_update: BotCreate):
    """Met à jour la configuration d'un bot existant"""
    try:
        obj_id = ObjectId(bot_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Bot ID format")
    
    # On ne garde que les champs renseignés
    update_data = {k: v for k, v in bot_update.dict().items() if v is not None}
    
    result = await bot_collection.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    updated_bot = await bot_collection.find_one({"_id": obj_id})
    return bot_helper(updated_bot)

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
    async for msg in messages_collection.find({"bot_id": req.bot_id}).sort("timestamp", -1).limit(15):
        # Map roles and include tool-calling metadata if present
        m = {
            "role": "assistant" if msg["role"] == "bot" else msg["role"], 
            "content": msg.get("content", "")
        }
        if "tool_calls" in msg:
            m["tool_calls"] = msg["tool_calls"]
        if "tool_call_id" in msg:
            m["tool_call_id"] = msg["tool_call_id"]
        if "name" in msg:
            m["name"] = msg["name"]
        
        history.append(m)
    history.reverse()

    # Save User message
    await messages_collection.insert_one({
        "bot_id": req.bot_id,
        "role": "user",
        "content": req.message,
        "timestamp": datetime.now()
    })

    try:
        # --- GENERIC MULTI-TOOLS DEFINITION ---
        bot_tools_config = bot.get("tools", [])
        llm_tools = None
        if bot_tools_config:
            llm_tools = []
            for t in bot_tools_config:
                llm_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.get("name", "tool"),
                        "description": t.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "L'argument de recherche ou l'ID"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                })

        headers = {}
        if bot.get("api_key"):
            api_key = bot["api_key"].strip()
            if not api_key.startswith("Bearer "):
                api_key = f"Bearer {api_key}"
            headers["Authorization"] = api_key

        messages_payload = [{"role": "system", "content": bot.get("prompt", "")}]
        messages_payload.extend(history)
        messages_payload.append({"role": "user", "content": req.message})

        async with httpx.AsyncClient() as client_http:
            # 1. Call LLM
            req_payload = {
                "model": bot.get("model_name", "gpt-3.5-turbo"),
                "messages": messages_payload
            }
            if llm_tools:
                req_payload["tools"] = llm_tools

            response = await client_http.post(bot["url"], json=req_payload, headers=headers, timeout=20.0)
            response.raise_for_status()
            message_obj = response.json().get("choices", [{}])[0].get("message", {})
            
            # 2. Handle Tool Calls (Multiple Support)
            tool_calls = message_obj.get("tool_calls")
            if tool_calls:
                # CRITICAL: Groq/OpenAI require 'content' in assistant message even if there are tool_calls
                if "content" not in message_obj or message_obj["content"] is None:
                    message_obj["content"] = ""
                
                # Strip internal fields not allowed in some strict APIs
                cleaned_assistant_msg = {
                    "role": "assistant",
                    "content": message_obj["content"],
                    "tool_calls": tool_calls
                }
                
                messages_payload.append(cleaned_assistant_msg) # Add to current conversation flow
                
                # PERSIST: Save the assistant's intent to use tools
                await messages_collection.insert_one({
                    "bot_id": req.bot_id,
                    "role": "assistant",
                    "content": cleaned_assistant_msg["content"],
                    "tool_calls": tool_calls,
                    "timestamp": datetime.now()
                })

                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_id = tool_call["id"]
                    
                    print(f"DEBUG: IA demande l'outil '{tool_name}' (ID: {tool_id})")

                    # Find tool
                    target_tool = next((t for t in bot_tools_config if t["name"] == tool_name), None)
                    
                    if target_tool:
                        try:
                            import json
                            args = json.loads(tool_call["function"]["arguments"])
                            query = args.get("query", "")
                            
                            t_url = target_tool["url"]
                            # Clean query
                            q_val = str(query).strip()
                            
                            if "{query}" in t_url:
                                t_url = t_url.replace("{query}", q_val)
                            elif "{id}" in t_url:
                                t_url = t_url.replace("{id}", q_val)
                            elif q_val and q_val.lower() not in ["", "none", "all"]:
                                # Path param support (e.g. /products/123)
                                if not t_url.endswith(q_val):
                                    t_url = f"{t_url.rstrip('/')}/{q_val}"

                            print(f"DEBUG: Appel API REST -> {t_url}")
                            
                            if target_tool.get("method", "GET") == "GET":
                                t_resp = await client_http.get(t_url, timeout=10.0)
                            else:
                                t_resp = await client_http.post(t_url, json={"query": query}, timeout=10.0)
                            
                            # Truncate if too long (max 2000 chars) to avoid LLM overflow
                            raw_res = t_resp.text
                            tool_result = (raw_res[:2000] + "...") if len(raw_res) > 2000 else raw_res
                            print(f"DEBUG: Réponse Reçue (Status {t_resp.status_code})")
                        except Exception as te:
                            tool_result = f"Erreur outil: {str(te)}"
                            print(f"DEBUG: Erreur Outil -> {str(te)}")
                    else:
                        tool_result = "Outil non configuré."

                    # Add each tool result to the stack for immediate synthesis
                    t_result_msg = {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": tool_result
                    }
                    messages_payload.append(t_result_msg)

                    # PERSIST: Save the tool's response to history
                    await messages_collection.insert_one({
                        "bot_id": req.bot_id,
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": tool_result,
                        "timestamp": datetime.now()
                    })

                # 3. Final call to LLM after ALL tool results are added
                print("DEBUG: Renvoi des données à l'IA pour synthèse finale...")
                final_payload = {
                    "model": bot.get("model_name", "gpt-3.5-turbo"),
                    "messages": messages_payload
                }
                # Optional: send tolls definition again if some models require it
                if llm_tools:
                    final_payload["tools"] = llm_tools

                final_resp = await client_http.post(bot["url"], json=final_payload, headers=headers, timeout=25.0)
                final_resp.raise_for_status()
                reply = final_resp.json().get("choices", [{}])[0].get("message", {}).get("content", "...")
            else:
                reply = message_obj.get("content", "...")

            # Save reply
            await messages_collection.insert_one({
                "bot_id": req.bot_id,
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now()
            })

            return {"reply": reply}

    except Exception as e:
        print(f"DEBUG CHAT ERROR: {str(e)}")
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

@app.get("/test/container/{container_id}")
async def test_container_api(container_id: str):
    """API de test pour simuler votre système d'optimisation"""
    # Simulation de données
    import random
    zones = ["Zone A", "Zone B", "Terminal Nord", "Quai 2"]
    status_list = ["Optimisé", "En attente de mouvement", "Mal placé", "Prêt pour chargement"]
    
    return {
        "id": container_id,
        "position": f"{random.choice(zones)}, Rangée {random.randint(1, 10)}",
        "status": random.choice(status_list),
        "score_optimisation": f"{random.randint(60, 99)}%",
        "derniere_mise_a_jour": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

@app.get("/test/port-info/{terminal_id}")
async def test_port_info_api(terminal_id: str):
    """API de test pour simuler le statut d'un terminal portuaire"""
    import random
    levels = ["Fluide", "Modéré", "Dense", "Congestionné"]
    return {
        "terminal": terminal_id.upper(),
        "trafic_actuel": random.choice(levels),
        "navires_a_quai": random.randint(0, 8),
        "capacite_disponible": f"{random.randint(100, 5000)} TEUs",
        "météo_portuaire": "Ciel dégagé, Vent 10 nœuds",
        "prochain_navire": "2h 30min"
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

@app.get("/test/users", tags=["Test API"])
async def get_test_users():
    """Returns a list of mock users for testing."""
    return MOCK_USERS

@app.get("/test/users/{user_id}", tags=["Test API"])
async def get_test_user(user_id: str):
    """Returns a specific mock user by ID."""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/test/users", tags=["Test API"])
async def create_test_user(user: UserTest):
    """Simulates creating a user."""
    new_user = user.dict()
    if not new_user.get("id"):
        import random
        new_user["id"] = str(random.randint(100, 999))
    return {"message": "Utilisateur créé avec succès (simulation)", "user": new_user}

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Si le dossier dist existe (ex: en prod dans le conteneur Docker unique)
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Sert index.html pour le routing côté client (React Router, etc)
        # Sauf s'il s'agit d'un appel direct à un fichier qui devrait exister mais qui a été manqué
        path = os.path.join("dist", full_path)
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse("dist/index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "SaaS Bot Builder API (MongoDB Mode) en ligne."}
