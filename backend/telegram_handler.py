import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from database import bot_collection, bot_helper

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramManager:
    def __init__(self, process_message_func):
        self.process_message_func = process_message_func
        self.apps = {} # bot_id -> application
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
            # Construction de l'application Telegram
            app = ApplicationBuilder().token(token).build()
            
            # Handler pour tous les messages texte
            async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.text:
                    return
                
                user_msg = update.message.text
                logger.info(f"Telegram Bot {bot_id} reçu: {user_msg}")
                
                # Appel de la logique centrale (LLM + Tools)
                reply = await self.process_message_func(bot_id, user_msg)
                
                await update.message.reply_text(reply)

            app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), msg_handler))
            
            # Initialisation
            await app.initialize()
            await app.start()
            
            # On utilise le polling en tâche de fond
            task = asyncio.create_task(app.updater.start_polling())
            
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

# Instance globale (sera initialisée dans main.py)
telegram_manager = None
