import os
import re
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- états simples ---
STATE_MENU = "menu"
STATE_PAYMENT = "payment"
STATE_WAIT_LINK = "wait_link"
STATE_CONTACT_ADMIN = "contact_admin"

USER_STATE = {}  # user_id -> {"state": ..., "payment": ..., "last_menu_msg_id": ...}

# Ton message d’infos (celui que tu voulais ajouter)
INFO_MSG = (
    "ℹ️ *Infos importantes*\n"
    "• Les restaurants sans *Uber One* ne sont malheureusement pas éligibles à la réduction *-50%*.\n"
    "• Vous pouvez préparer plusieurs paniers dans le même restaurant si vous souhaitez cumuler vos commandes.\n"
    "• Les offres spéciales Uber Eats (ex: *1 acheté = 1 offert*) sont prises en charge et restent valables avec la réduction.\n"
)

def get_state(user_id: int):
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {"state": STATE_MENU, "payment": None, "last_menu_msg_id": None}
    return USER_STATE[user_id]

async def clean_previous_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Supprime l’ancien message menu du bot (pour pas spammer)."""
    user_id = update.effective_user.id
    st = get_state(user_id)
    msg_id = st.get("last_menu_msg_id")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except Exception:
            pass
        st["last_menu_msg_id"] = None

async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clean_previous_menu(update, context)

    keyboard = [["🛒 Commander"], ["📞 Contacter admin"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    sent = await update.effective_chat.send_message("Choisis une option :", reply_markup=markup)
    st = get_state(update.effective_user.id)
    st["state"] = STATE_MENU
    st["last_menu_msg_id"] = sent.message_id

async def send_payment_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clean_previous_menu(update, context)

    keyboard = [["₿ Crypto", "💳 Revolut"], ["⚡️ Virement instantané"], ["↩️ Retour"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    sent = await update.effective_chat.send_message("Choisis ton mode de paiement :", reply_markup=markup)
    st = get_state(update.effective_user.id)
    st["state"] = STATE_PAYMENT
    st["last_menu_msg_id"] = sent.message_id

def is_valid_link(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"https?://", text)) or ("uber" in text.lower())

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # On n’envoie PAS “Bot running” — on envoie direct le menu
    await update.message.reply_text(INFO_MSG, parse_mode="Markdown")
    await send_menu(update, context)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    user_id = user.id
    text = (update.message.text or "").strip()

    st = get_state(user_id)
    state = st["state"]

    # Bouton retour
    if text == "↩️ Retour":
        await send_menu(update, context)
        return

    # MENU
    if state == STATE_MENU:
        if text == "🛒 Commander":
            await send_payment_menu(update, context)
            return

        if text == "📞 Contacter admin":
            st["state"] = STATE_CONTACT_ADMIN
            await update.message.reply_text(
                "📩 Écris ton message ici, je le transfère à un admin.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        # Si le client écrit autre chose au menu => on renvoie le menu
        await send_menu(update, context)
        return

    # PAYMENT
    if state == STATE_PAYMENT:
        if text in ("₿ Crypto", "💳 Revolut", "⚡️ Virement instantané"):st["payment"] = text
            st["state"] = STATE_WAIT_LINK

            await update.message.reply_text(
                "🔗 Envoie ton *lien Uber Eats (commande groupée)*.\n\n"
                "👉 Astuce : sur Uber Eats, crée ton panier puis partage le lien de commande.",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        await send_payment_menu(update, context)
        return

    # WAIT LINK
        if state == STATE_WAIT_LINK:
        if is_valid_link(text):
            payment = st.get("payment") or "Non précisé"

            # Confirme au client
            await update.message.reply_text("✅ Lien reçu. Un admin va répondre ici.")

            # Notif admin instantanée
            if ADMIN_ID != 0:
                msg_admin = (
                    "🛒 *Nouvelle commande*\n"
                    f"👤 {user.full_name}\n"
                    f"🆔 `{user_id}`\n"
                    f"💳 Paiement : *{payment}*\n"
                    f"🔗 Lien : {text}"
                )
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, parse_mode="Markdown")
                except Exception:
                    pass

            # Retour menu
            await send_menu(update, context)
            return

        await update.message.reply_text("❌ Je n’ai pas reconnu le lien. Renvoie le lien Uber Eats stp.")
        return

    # CONTACT ADMIN
    if state == STATE_CONTACT_ADMIN:
        if ADMIN_ID != 0:
            msg_admin = (
                "📞 *Message client*\n"
                f"👤 {user.full_name}\n"
                f"🆔 `{user_id}`\n"
                f"💬 {text}"
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, parse_mode="Markdown")
            except Exception:
                pass

        await update.message.reply_text("✅ Message envoyé à un admin. On te répond ici.")
        await send_menu(update, context)
        return

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Évite crash silencieux
    try:
        print("ERROR:", context.error)
    except Exception:
        pass

def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN manquant dans les variables d’environnement Render")
        return
    if ADMIN_ID == 0:
        print("⚠️ ADMIN_ID manquant ou à 0 (tu ne recevras pas les notifs admin)")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    # IMPORTANT: polling (pas webhook)
    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
