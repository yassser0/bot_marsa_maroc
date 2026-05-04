import asyncio
import logging
import io
import httpx
import html
import base64
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import bot_collection, bot_helper

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL du projet d'optimisation
OPTIMIZATION_API_URL = "http://127.0.0.1:8000"

# ---------------------------------------------------------------------------
# State management per chat
# chat_id -> {"state": "awaiting_mode"|"awaiting_arrivals", "snapshot_bytes": bytes, "snapshot_name": str}
# ---------------------------------------------------------------------------
_chat_state: dict = {}


async def _forward_standard_csv(file_bytes: bytes, filename: str) -> str:
    """Envoie un seul CSV (mode standard) et retourne le rapport formaté."""
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            resp = await client.post(
                f"{OPTIMIZATION_API_URL}/containers/upload-csv",
                files={"file": (filename, io.BytesIO(file_bytes), "text/csv")},
            )
            resp.raise_for_status()
        except Exception as e:
            return f"❌ Erreur lors de l'envoi du fichier : {str(e)}"

        return await _poll_etl_status(client)


async def _forward_hybrid_csv(snapshot_bytes: bytes, snapshot_name: str,
                               arrivals_bytes: bytes, arrivals_name: str) -> str:
    """Envoie deux CSV (mode hybride) et retourne le rapport formaté."""
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            resp = await client.post(
                f"{OPTIMIZATION_API_URL}/containers/upload-dual-csv",
                files={
                    "snapshot": (snapshot_name, io.BytesIO(snapshot_bytes), "text/csv"),
                    "arrivals": (arrivals_name, io.BytesIO(arrivals_bytes), "text/csv"),
                },
            )
            resp.raise_for_status()
        except Exception as e:
            return f"❌ Erreur lors de l'envoi des fichiers : {str(e)}"

        return await _poll_etl_status(client)



def is_valid_bic(container_id: str) -> bool:
    """Validates a container ID according to ISO 6346"""
    import re
    # Remove spaces and hyphens
    cid = re.sub(r'[^A-Z0-9]', '', container_id.upper())
    if len(cid) != 11:
        return False
    
    # Check format: 4 letters + 7 numbers
    if not re.match(r'^[A-Z]{4}\d{7}$', cid):
        return False

    # Letter values
    letter_values = {
        'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
        'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
        'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
    }

    sum_val = 0
    for i in range(10):
        char = cid[i]
        val = letter_values[char] if char.isalpha() else int(char)
        sum_val += val * (2 ** i)

    check_digit = (sum_val % 11) % 10
    return check_digit == int(cid[10])

def preprocess_image(image_bytes: bytes) -> bytes:
    """Augmente le contraste de l'image via Pillow si disponible"""
    try:
        from PIL import Image, ImageEnhance
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to grayscale to remove color noise
        img = img.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Increase Sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        # Save back to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        return img_byte_arr.getvalue()
    except ImportError:
        logger.warning("Pillow non installé, traitement d'image ignoré.")
        return image_bytes

async def _forward_image_to_groq(image_bytes: bytes, api_key: str, model_name: str) -> str:
    """Envoie une image au modèle Vision pour l'OCR avec prétraitement et validation ISO."""
    # 1. Prétraitement de l'image (Pillow)
    processed_bytes = preprocess_image(image_bytes)
    base64_image = base64.b64encode(processed_bytes).decode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    # 2. Advanced Prompt Engineering
    base_prompt = (
        "Tu es un expert en logistique portuaire. Ta seule mission est d'extraire le matricule du conteneur (Container ID). "
        "Règles strictes : "
        "1. Le format est TOUJOURS : 4 lettres majuscules suivies de 7 chiffres. "
        "2. Fais très attention aux confusions classiques : ne confonds pas le S et le 5, le O et le 0, le I et le 1, le Z et le 2, le B et le 8. "
        "INTERDICTION FORMELLE DE DONNER DES EXPLICATIONS. RENVOIE UNIQUEMENT LE MATRICULE (ex: MSCU 123456 7) ET ABSOLUMENT RIEN D'AUTRE."
    )
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": base_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Première tentative
            payload = {"model": model_name, "messages": messages, "temperature": 0.0}
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                data = resp.json()
                err = data.get('error', {}).get('message', 'Inconnue') if isinstance(data.get('error'), dict) else data.get('error')
                return f"❌ Erreur API Vision : {err}"
                
            import re
            
            def extract_clean_id(text: str) -> str:
                # Cherche 4 lettres suivies de 7 chiffres (avec ou sans espaces)
                match = re.search(r'([A-Z]{4})[\s\-]*(\d{6})[\s\-]*(\d)', text.upper())
                if match:
                    return f"{match.group(1)} {match.group(2)} {match.group(3)}"
                return text.strip()

            raw_text = resp.json()['choices'][0]['message']['content'].strip()
            result_text = extract_clean_id(raw_text)
            
            # 3. Validation ISO
            if is_valid_bic(result_text):
                return f"📦 **Matricule détecté :** `{result_text}`"
            
            # Deuxième tentative (Correction) si invalide
            correction_prompt = (
                f"Le matricule '{result_text}' que tu as trouvé est invalide selon l'algorithme ISO 6346. "
                "Tu as probablement confondu un chiffre avec une lettre ou inversement (ex: 5 et S, 0 et O). "
                "Regarde à nouveau très attentivement l'image. "
                "INTERDICTION DE DONNER DES EXPLICATIONS. Renvoie uniquement le matricule corrigé (4 lettres, 7 chiffres)."
            )
            
            messages.append({"role": "assistant", "content": result_text})
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": correction_prompt}]
            })
            
            payload = {"model": model_name, "messages": messages, "temperature": 0.0}
            resp2 = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            
            if resp2.status_code == 200:
                raw_text2 = resp2.json()['choices'][0]['message']['content'].strip()
                result_text2 = extract_clean_id(raw_text2)
                return f"📦 **Matricule détecté :** `{result_text2}`"
            
            return f"📦 **Matricule détecté :** `{result_text}`"
                
        except Exception as e:
            return f"❌ Erreur de connexion avec l'API Vision : {str(e)}"


async def _poll_etl_status(client: httpx.AsyncClient) -> str:
    """Polls /containers/upload-status until done, returns formatted report."""
    attempt = 0
    while True:
        attempt += 1
        await asyncio.sleep(4)
        try:
            status_resp = await client.get(f"{OPTIMIZATION_API_URL}/containers/upload-status")
            status_data = status_resp.json()
            status = status_data.get("status", "unknown")

            if status == "success":
                result = status_data.get("result", {})
                snap   = result.get("snapshot_report", {})
                arr    = result.get("arrivals_report", {})
                gold   = result.get("gold_kpis", {})
                adv    = gold.get("advanced_analytics", {}) if gold else {}

                # Standard mode: snapshot has 0 fixed placements (all optimized)
                is_standard = snap.get("placed_fixed", 0) == 0

                if is_standard:
                    # Clean minimal report for Standard mode
                    lines = [
                        "✅ *Traitement ETL terminé avec succès !*",
                        f"📦 *Conteneurs placés* : {result.get('total_placed', 'N/A')}",
                        f"🏗️ *Taux d'occupation* : {result.get('yard_occupancy', 'N/A')}",
                        f"⏱️ *Durée* : {result.get('processing_time_ms', 'N/A')} ms",
                    ]
                    if adv:
                        lines += [
                            f"📈 *Score d'efficacité* : {adv.get('efficiency_score', 'N/A')}%",
                            f"🔄 *Rehandles évités* : {adv.get('rehandle_risk_count', 'N/A')}",
                        ]
                else:
                    # Full detailed report for Hybrid mode
                    lines = [
                        "✅ *Traitement ETL terminé avec succès !*\n",
                        f"📦 *Conteneurs placés* : {result.get('total_placed', 'N/A')}",
                        f"🏗️ *Taux d'occupation* : {result.get('yard_occupancy', 'N/A')}",
                        f"⏱️ *Durée* : {result.get('processing_time_ms', 'N/A')} ms\n",
                        "*📸 Snapshot (terminal actuel) :*",
                        f"  • Reçus : {snap.get('total_received', 'N/A')}",
                        f"  • Placés (fixe) : {snap.get('placed_fixed', 'N/A')}",
                        f"  • Redirigés optimiseur : {snap.get('rescued', 'N/A')}",
                        f"\n*🚢 Arrivées :*",
                        f"  • Reçus : {arr.get('total_received', 'N/A')}",
                        f"  • Placés (optimisé) : {arr.get('placed', 'N/A')}",
                        f"  • Échecs : {arr.get('failed', 'N/A')}",
                    ]
                    if adv:
                        lines += [
                            f"\n*📈 Score d'efficacité* : {adv.get('efficiency_score', 'N/A')}%",
                            f"*🔄 Rehandles évités* : {adv.get('rehandle_risk_count', 'N/A')}",
                        ]
                return "\n".join(lines)

            elif status == "error":
                return f"❌ Erreur lors du traitement : {status_data.get('message', 'Inconnue')}"

            elif status == "processing":
                logger.info(f"[CSV Poll] Tentative {attempt} — {status_data.get('message', '...')}")

        except Exception as e:
            logger.warning(f"[CSV Poll] Erreur de statut: {e}")


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

def _make_mode_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard to choose Standard or Hybrid mode."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Standard (1 fichier)", callback_data="mode_standard"),
            InlineKeyboardButton("🔀 Hybride (2 fichiers)", callback_data="mode_hybrid"),
        ]
    ])


class TelegramManager:
    def __init__(self, process_message_func):
        self.process_message_func = process_message_func
        self.apps = {}
        self._running_tasks = {}

    async def start_all_bots(self):
        """Démarre tous les bots qui ont un token configuré"""
        logger.info("Démarrage de la recherche des bots Telegram...")
        async for bot_doc in bot_collection.find({"telegram_token": {"$gt": ""}}):
            bot = bot_helper(bot_doc)
            await self.start_bot(bot["id"], bot["telegram_token"])

    async def start_bot(self, bot_id: str, token: str):
        """Initialise et démarre un bot spécifique"""
        if bot_id in self.apps:
            logger.info(f"Le bot {bot_id} est déjà en cours d'exécution.")
            return

        try:
            app = ApplicationBuilder().token(token).build()

            # --- Handler TEXTE ---
            async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.text:
                    return
                chat_id = update.effective_chat.id
                # If user types something while we are waiting for a file, cancel the flow
                if chat_id in _chat_state:
                    del _chat_state[chat_id]
                    await update.message.reply_text(
                        "❌ Flux CSV annulé. Comment puis-je vous aider ?"
                    )
                    return

                user_msg = update.message.text
                logger.info(f"Telegram Bot {bot_id} reçu: {user_msg}")
                reply = await self.process_message_func(bot_id, user_msg)
                await update.message.reply_text(reply)

            # --- Handler FICHIER ---
            async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.document:
                    return

                chat_id = update.effective_chat.id
                doc = update.message.document
                filename = doc.file_name or "upload.csv"

                if not filename.lower().endswith(".csv"):
                    await update.message.reply_text(
                        "⚠️ Seuls les fichiers `.csv` sont acceptés.\n"
                        "Veuillez envoyer un fichier CSV valide."
                    )
                    return

                state = _chat_state.get(chat_id, {})

                # ---- STEP 2 (Hybrid): receiving the arrivals file ----
                if state.get("state") == "awaiting_arrivals":
                    snapshot_bytes = state["snapshot_bytes"]
                    snapshot_name  = state["snapshot_name"]
                    del _chat_state[chat_id]

                    await update.message.reply_text(
                        f"📂 Fichier d'*arrivées* `{filename}` reçu !\n"
                        f"⚙️ Lancement du traitement *Hybride* (Snapshot + Arrivées)...\n"
                        f"_(Cela peut prendre 60 à 120 secondes)_",
                        parse_mode="Markdown"
                    )
                    tg_file = await context.bot.get_file(doc.file_id)
                    arrivals_bytes = bytes(await tg_file.download_as_bytearray())

                    result_msg = await _forward_hybrid_csv(
                        snapshot_bytes, snapshot_name,
                        arrivals_bytes, filename
                    )
                    await update.message.reply_text(result_msg, parse_mode="Markdown")
                    return

                # ---- STEP 1: first file received — ask mode ----
                logger.info(f"Telegram Bot {bot_id} reçu CSV: {filename}")
                tg_file = await context.bot.get_file(doc.file_id)
                file_bytes = bytes(await tg_file.download_as_bytearray())

                # Store the file temporarily and ask for mode
                _chat_state[chat_id] = {
                    "state": "awaiting_mode",
                    "first_bytes": file_bytes,
                    "first_name": filename,
                }

                await update.message.reply_text(
                    f"📂 Fichier *{filename}* reçu !\n\n"
                    f"Quel mode de traitement souhaitez-vous ?\n\n"
                    f"• *Standard* — Ce fichier contient toutes les données (arrivées).\n"
                    f"• *Hybride* — Ce fichier est le *Snapshot* (état actuel). "
                    f"Vous devrez ensuite envoyer un 2ème fichier *Arrivées*.",
                    parse_mode="Markdown",
                    reply_markup=_make_mode_keyboard()
                )

            # --- Handler CALLBACK (boutons inline) ---
            async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                query = update.callback_query
                await query.answer()
                chat_id = query.message.chat.id
                state = _chat_state.get(chat_id, {})

                if state.get("state") != "awaiting_mode":
                    await query.edit_message_text("⚠️ Session expirée. Veuillez renvoyer votre fichier CSV.")
                    return

                first_bytes = state["first_bytes"]
                first_name  = state["first_name"]

                if query.data == "mode_standard":
                    del _chat_state[chat_id]
                    await query.edit_message_text(
                        f"✅ Mode *Standard* sélectionné.\n"
                        f"⚙️ Traitement de `{first_name}` en cours...\n"
                        f"_(Cela peut prendre 60 à 90 secondes)_",
                        parse_mode="Markdown"
                    )
                    result_msg = await _forward_standard_csv(first_bytes, first_name)
                    await context.bot.send_message(chat_id=chat_id, text=result_msg, parse_mode="Markdown")

                elif query.data == "mode_hybrid":
                    _chat_state[chat_id] = {
                        "state": "awaiting_arrivals",
                        "snapshot_bytes": first_bytes,
                        "snapshot_name": first_name,
                    }
                    await query.edit_message_text(
                        f"✅ Mode *Hybride* sélectionné.\n"
                        f"📸 Snapshot `{first_name}` sauvegardé.\n\n"
                        f"📤 Envoyez maintenant le fichier *Arrivées* (CSV).",
                        parse_mode="Markdown"
                    )


            # --- Handler PHOTO ---
            async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.photo:
                    return
                
                await update.message.reply_text("📸 Analyse de l'image avec Llama-4-Scout en cours..")
                photo = update.message.photo[-1]
                
                image_bytes = None
                for attempt in range(3):
                    try:
                        # Augmenter le timeout pour Telegram et ajouter un retry
                        tg_file = await context.bot.get_file(photo.file_id, read_timeout=40, connect_timeout=40)
                        image_bytes = bytes(await tg_file.download_as_bytearray())
                        break
                    except Exception as e:
                        if attempt == 2:
                            await update.message.reply_text(f"❌ Erreur de téléchargement depuis Telegram (Timeout). Veuillez renvoyer l'image. ({str(e)})")
                            return
                        await asyncio.sleep(2)
                
                if not image_bytes:
                    return
                
                # Récupérer la clé API et le modèle Vision du bot dans la base de données
                bot_doc = await bot_collection.find_one({"_id": ObjectId(bot_id)})
                if bot_doc and bot_doc.get("api_key"):
                    api_key = bot_doc["api_key"]
                    vision_model = bot_doc.get("vision_model_name", "meta-llama/llama-4-scout-17b-16e-instruct")
                    result_msg = await _forward_image_to_groq(image_bytes, api_key, vision_model)
                else:
                    result_msg = "❌ Erreur : Clé API Groq non configurée pour ce bot."
                
                try:
                    await update.message.reply_text(result_msg, parse_mode="Markdown")
                except Exception:
                    # En cas de Markdown invalide généré par le LLM
                    await update.message.reply_text(result_msg)

            app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), msg_handler))
            app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
            app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
            app.add_handler(CallbackQueryHandler(callback_handler))

            await app.initialize()
            await app.start()
            await asyncio.sleep(1)
            task = asyncio.create_task(app.updater.start_polling(drop_pending_updates=True))

            self.apps[bot_id] = app
            self._running_tasks[bot_id] = task
            logger.info(f"✅ Bot Telegram {bot_id} démarré avec succès.")

        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du bot Telegram {bot_id}: {str(e)}")

    async def stop_bot(self, bot_id: str):
        """Arrête un bot spécifique"""
        if bot_id in self.apps:
            app = self.apps[bot_id]
            task = self._running_tasks.get(bot_id)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if app.updater.running:
                await app.updater.stop()
            await app.stop()
            await app.shutdown()
            del self.apps[bot_id]
            del self._running_tasks[bot_id]
            logger.info(f"🛑 Bot Telegram {bot_id} arrêté.")

    async def stop_all(self):
        """Arrête tous les bots"""
        ids = list(self.apps.keys())
        for bid in ids:
            await self.stop_bot(bid)


# Instance globale
telegram_manager = None
