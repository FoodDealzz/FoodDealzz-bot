import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # Render env var

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot en ligne. Envoie /help si tu veux.")

def run_bot():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant dans les variables Render")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Lance le bot en polling
    app.run_polling()
