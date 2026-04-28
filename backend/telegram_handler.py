import asyncio
import logging
import io
import httpx
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

            app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), msg_handler))
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
