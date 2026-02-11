import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # ton id telegram

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🛒 Commander"],
        ["📞 Contacter admin"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Choisis une option :",
        reply_markup=reply_markup
    )

# ================= CONTACT ADMIN =================

async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Un admin va te répondre ici.")

    user = update.message.from_user

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 Un client veut te contacter\n👤 {user.first_name}\n🆔 {user.id}"
    )

# ================= COMMANDER =================

async def commander(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🪙 Crypto"],
        ["💳 Revolut"],
        ["⚡️ Virement instantané"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "⚠️ CONDITIONS À LIRE\n\n"
        "• Restaurants sans Uber One ❌ non éligibles -50%\n"
        "• Offres Uber Eats (1 acheté = 1 offert) ✅ valables\n"
        "• Plusieurs paniers possibles dans 1 restaurant\n\n"
        "💰 Panier accepté uniquement entre 20€ et 23€ HT\n\n"
        "Choisis ton moyen de paiement 👇",
        reply_markup=reply_markup
    )

# ================= PAIEMENT CHOISI =================

async def paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choix = update.message.text

    await update.message.reply_text(
        f"💳 Paiement sélectionné : {choix}\n\n"
        "📎 Envoie maintenant ton lien Uber Eats (commande groupée)\n\n"
        "Si tu ne sais pas :\n"
        "1. Prépare ton panier Uber Eats\n"
        "2. Clique 'commander à plusieurs'\n"
        "3. Copie le lien\n"
        "4. Envoie-le ici"
    )

    context.user_data["attend_lien"] = True

# ================= RECEPTION LIEN CLIENT =================

async def recevoir_lien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attend_lien"):
        return

    lien = update.message.text
    user = update.message.from_user

    # message pour admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🛒 NOUVELLE COMMANDE\n\n"
            f"👤 {user.first_name}\n"
            f"🆔 {user.id}\n"
            f"🔗 {lien}"
        )
    )

    # confirmation client
    await update.message.reply_text(
        "✅ Lien reçu. Un admin prépare ta commande maintenant."
    )

    context.user_data["attend_lien"] = False

# ================= MAIN =================

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("📞 Contacter admin"), contact_admin))
    app.add_handler(MessageHandler(filters.Regex("🛒 Commander"), commander))
    app.add_handler(MessageHandler(filters.Regex("Crypto|Revolut|Virement"), paiement))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_lien))

    print("BOT FOODDEALZZ ACTIF 🚀")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
