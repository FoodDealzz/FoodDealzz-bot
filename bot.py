import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")  # doit être un nombre en texte, ex: "123456789"

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN manquant (Render > Environment)")
if not ADMIN_ID:
    raise RuntimeError("❌ ADMIN_ID manquant (Render > Environment)")

ADMIN_ID_INT = int(ADMIN_ID)

# --- Clavier en bas (comme photo 2) ---
MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 Commander")],
        [KeyboardButton("📞 Contacter admin")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# Petit “state” en mémoire : qui doit envoyer son lien
WAITING_LINK = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # IMPORTANT : pas de “Bot running” -> direct menu
    await update.message.reply_text(
        "Choisis une option :",
        reply_markup=MENU_KEYBOARD,
    )


async def commander(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    WAITING_LINK.add(chat_id)

    await update.message.reply_text(
        "📎 Envoie ton lien Uber Eats",
        reply_markup=ReplyKeyboardRemove(),  # retire le clavier le temps d’envoyer le lien
    )


async def contacter_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Message côté client
    await update.message.reply_text(
        "✅ Ok. Un admin va te répondre ici.",
        reply_markup=MENU_KEYBOARD,
    )

    # Notif côté admin
    txt = (
        "📞 Demande admin\n"
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"💬 ChatID: {update.effective_chat.id}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID_INT, text=txt)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = (update.message.text or "").strip()

    # Si il a cliqué sur les boutons (ReplyKeyboard) -> on route
    if text == "🛒 Commander":
        return await commander(update, context)
    if text == "📞 Contacter admin":
        return await contacter_admin(update, context)

    # Si on attend un lien Uber Eats
    if chat_id in WAITING_LINK:
        WAITING_LINK.discard(chat_id)

        # Envoie à l’admin
        admin_msg = (
            "🛒 Nouvelle commande\n"
            f"👤 {user.full_name}\n"
            f"🆔 {user.id}\n"
            f"🔗 {text}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID_INT, text=admin_msg)

        # Réponse client
        await update.message.reply_text(
            "✅ Lien reçu. Un admin va répondre ici.",
            reply_markup=MENU_KEYBOARD,
        )
        return

    # Sinon, on remet juste le menu
    await update.message.reply_text(
        "Choisis une option :",
        reply_markup=MENU_KEYBOARD,
    )


async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # garde le bot vivant
    await asyncio.Event().wait()
