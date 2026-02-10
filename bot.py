import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # mets ton ID dans Render


# --------- MENUS (BOUTONS) ---------

def client_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Commander", callback_data="order")],
        [InlineKeyboardButton("👤 Contacter un admin", callback_data="admin")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Voir demandes", callback_data="requests")],
        [InlineKeyboardButton("🛒 Tester menu client", callback_data="clientmenu")]
    ])


# --------- /start ---------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # CLIENT : pas de texte, uniquement les boutons
    if user_id != ADMIN_ID:
        await update.message.reply_text(" ", reply_markup=client_keyboard())
        return

    # ADMIN : menu admin
    await update.message.reply_text("👑 Menu Admin", reply_markup=admin_keyboard())


# --------- CLICS SUR BOUTONS ---------

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # obligatoire sinon Telegram “charge”

    user_id = query.from_user.id
    data = query.data

    # CLIENT
    if user_id != ADMIN_ID:
        if data == "order":
            # Ici tu remplaces par TON lien UberEats / site / formulaire
            await query.message.reply_text("🛒 Pour commander : (mets ton lien ici)")
        elif data == "admin":
            # Ici tu remplaces par TON @username admin ou un lien t.me/...
            await query.message.reply_text("👤 Admin : @TonUsername (ou mets ton lien t.me/...)")
        return

    # ADMIN
    if data == "requests":
        await query.message.reply_text("📩 (À faire) Ici on affichera les demandes.")
    elif data == "clientmenu":
        await query.message.reply_text("🧪 Menu client :", reply_markup=client_keyboard())


# --------- RUN ---------

async def main():
    if not TOKEN:
        print("❌ BOT_TOKEN manquant dans Render (Environment)")
        return
    if ADMIN_ID == 0:
        print("❌ ADMIN_ID manquant dans Render (Environment)")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
