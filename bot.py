import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot OK (Render)")

async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN manquant dans les variables Render")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("=== BOT START ===")
    print("=== POLLING START ===")

    await app.run_polling()

if name == "__main__":
    import asyncio
    asyncio.run(main())
