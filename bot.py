import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

user_state = {}

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🛒 Commander"],
        ["📞 Contacter admin"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choisis une option :", reply_markup=reply_markup)

# ===== BOUTONS =====
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name

    if text == "🛒 Commander":
        keyboard = [
            ["₿ Crypto"],
            ["💳 Revolut"],
            ["🏦 Virement instantané"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "💰 Choisis ton mode de paiement :",
            reply_markup=reply_markup
        )
        user_state[user_id] = "payment"

    elif text in ["₿ Crypto", "💳 Revolut", "🏦 Virement instantané"]:
        user_state[user_id] = "waiting_link"

        await update.message.reply_text(
            "📦 Envoie maintenant ton lien Uber Eats (commande groupée).\n\n"
            "Si tu ne sais pas :\n"
            "1. Va sur Uber Eats\n"
            "2. Crée ton panier\n"
            "3. Clique sur 'commande groupée'\n"
            "4. Envoie le lien ici"
        )

    elif text == "📞 Contacter admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 Un client demande à te parler :\n👤 {name}\n🆔 {user_id}"
        )
        await update.message.reply_text("✅ Admin contacté.")

# ===== LIEN CLIENT =====
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name
    text = update.message.text

    if user_state.get(user_id) == "waiting_link":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔥 NOUVELLE COMMANDE\n\n👤 {name}\n🆔 {user_id}\n🔗 {text}"
        )

        await update.message.reply_text("✅ Lien reçu. Un admin va traiter ta commande.")
        user_state[user_id] = None

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("BOT RUNNING 24/24 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
