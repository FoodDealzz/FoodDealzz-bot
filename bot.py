import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Je suis en ligne !")

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN manquant dans Render (Environment Variables)")

    print("=== BOT: building application ===", flush=True)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("=== BOT: starting polling ===", flush=True)
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()
