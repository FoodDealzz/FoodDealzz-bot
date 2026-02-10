import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot running ✅")

def run_bot():
    if not TOKEN:
        print("❌ BOT_TOKEN manquant dans les variables d'environnement Render")
        return

    async def _main():
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))

        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # garde le bot vivant
        await asyncio.Event().wait()

    asyncio.run(_main())
