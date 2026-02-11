import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# états utilisateur
STATE_NONE = 0
STATE_WAIT_PAYMENT = 1
STATE_WAIT_LINK = 2

USER_STATE = {}

INFO_MSG = (
"📌 Infos importantes :\n\n"
"• Les restaurants sans Uber One ne sont pas éligibles à la réduction -50%\n"
"• Vous pouvez faire plusieurs paniers dans le même restaurant\n"
"• Les offres Uber Eats (1 acheté = 1 offert) restent valables\n"
)

# --- clavier principal ---
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛒 Commander")],
            [KeyboardButton("📞 Contacter admin")],
        ],
        resize_keyboard=True
    )

# --- clavier paiement ---
def payment_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💎 Crypto")],
            [KeyboardButton("💳 Revolut")],
            [KeyboardButton("🏦 Virement instantané")],
        ],
        resize_keyboard=True
    )

# --- start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_STATE[update.effective_user.id] = {"state": STATE_NONE}
    await update.message.reply_text(
        "Bienvenue 👋\nClique sur commander pour envoyer ton lien.",
        reply_markup=main_keyboard()
    )

# --- message handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    st = USER_STATE.get(user_id, {"state": STATE_NONE})
    state = st.get("state", STATE_NONE)

    # bouton commander
    if text == "🛒 Commander":
        USER_STATE[user_id] = {"state": STATE_WAIT_PAYMENT}
        await update.message.reply_text(
            INFO_MSG + "\nChoisis ton moyen de paiement 👇",
            reply_markup=payment_keyboard()
        )
        return

    # bouton contacter admin
    if text == "📞 Contacter admin":
        await update.message.reply_text(
            "📩 Envoie ton message, un admin va répondre.",
            reply_markup=ReplyKeyboardRemove()
        )
        USER_STATE[user_id] = {"state": STATE_NONE}
        return

    # choix paiement
    if state == STATE_WAIT_PAYMENT:
        USER_STATE[user_id] = {
            "state": STATE_WAIT_LINK,
            "payment": text
        }
        await update.message.reply_text(
            "🔗 Envoie ton lien Uber Eats (commande groupée).\n"
            "Si tu ne sais pas : clique sur 'commander en groupe' sur Uber Eats et copie le lien.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # attente lien
    if state == STATE_WAIT_LINK:
        payment = st.get("payment", "Non précisé")

        await update.message.reply_text(
            "✅ Lien reçu. Un admin va répondre ici.",
            reply_markup=main_keyboard()
        )

        # notif admin
        if ADMIN_ID != 0:
            name = update.effective_user.full_name
            msg = (
                f"🛒 Nouvelle commande\n"
                f"👤 {name}\n"
                f"🆔 {user_id}\n"
                f"💰 {payment}\n"
                f"🔗 {text}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

        USER_STATE[user_id] = {"state": STATE_NONE}
        return


# --- lancement ---
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("BOT LANCÉ")
    app.run_polling()
