import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT FOODDEALZZ ACTIF 🔥")

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN manquant dans Render")

    print("=== BOT START ===", flush=True)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("=== POLLING START ===", flush=True)
    await app.run_polling()
