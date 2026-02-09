import os
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import Forbidden


# ======================
# ENV
# ======================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN manquant dans .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID manquant dans .env")


# ======================
# MENUS (client)
# ======================
MENU = ReplyKeyboardMarkup(
    [
        ["Commander 🍔"],
        ["Contacter admin 👨‍🍳"],
    ],
    resize_keyboard=True
)

PAY_MENU = ReplyKeyboardMarkup(
    [
        ["Crypto 🪙"],
        ["Virement instantané ⚡️"],
        ["Revolut 💳"],
        ["Retour ↩️"],
    ],
    resize_keyboard=True
)


# ======================
# Helpers (state)
# ======================
def _store(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Stockage global (tant que le bot tourne)."""
    bd = context.application.bot_data
    bd.setdefault("users", {})  # users[user_id] = {...}
    bd.setdefault("admin_ready", False)
    bd.setdefault("admin_msg_to_client", {})  # admin_message_id -> client_id
    return bd


def get_user_state(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> dict:
    bd = _store(context)
    bd["users"].setdefault(user_id, {
        "step": None,        # None / PAY / WAIT_LINK / WAIT_ADMIN / CHAT_OPEN
        "payment": None,     # "Crypto" / "Virement" / "Revolut"
        "ordered": False,
    })
    return bd["users"][user_id]


def user_tag(user) -> str:
    return f"@{user.username}" if user.username else "(sans @)"


async def safe_send_admin(context: ContextTypes.DEFAULT_TYPE, text: str, buttons=None) -> bool:
    """Envoie un message à l'admin. Retourne False si admin n'a jamais /start (Forbidden)."""
    try:
        msg = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            reply_markup=buttons
        )
        # On marque que l'admin est joignable si l'envoi passe
        _store(context)["admin_ready"] = True
        return True
    except Forbidden:
        # L'admin n'a pas ouvert le bot /start ou a bloqué le bot
        print("⚠️ Admin non joignable. L'admin doit ouvrir le bot et faire /start.")
        return False


def admin_status_buttons(client_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Paiement reçu", callback_data=f"status|{client_id}|PAY_OK"),
            InlineKeyboardButton("🍳 Commande en cours", callback_data=f"status|{client_id}|COOKING"),
        ],
        [
            InlineKeyboardButton("🚗 Livreur en route", callback_data=f"status|{client_id}|ON_THE_WAY"),
            InlineKeyboardButton("📦 Livré", callback_data=f"status|{client_id}|DELIVERED"),
        ],
    ])


def status_text(code: str) -> str:
    mapping = {
        "PAY_OK": "✅ Paiement reçu. On s’occupe de ta commande.",
        "COOKING": "🍳 Commande en cours de préparation.",
        "ON_THE_WAY": "🚗 Livreur en route.",
        "DELIVERED": "📦 Commande livrée. Merci !",
    }
    return mapping.get(code, "✅ Mise à jour.")


# ======================
# Commands
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Si c'est l'admin : on le rend "joignable"
    if user.id == ADMIN_ID:
        _store(context)["admin_ready"] = True
        await update.message.reply_text("✅ Admin connecté. Tu recevras les commandes ici.")
        return

    # Client
    st = get_user_state(context, user.id)
    st["step"] = None
    st["payment"] = None
    st["ordered"] = False

    await update.message.reply_text(
        "Bienvenue sur FoodDealzz 🍔\nClique sur « Commander » pour commencer.",
        reply_markup=MENU
    )# ======================
# Admin reply by "Reply"
# ======================
def extract_client_id_from_admin_context(reply_text: str) -> int | None:
    # On met toujours une ligne: "ID: 12345"
    if not reply_text:
        return None
    for line in reply_text.splitlines():
        line = line.strip()
        if line.startswith("ID:"):
            try:
                return int(line.replace("ID:", "").strip())
            except:
                return None
    return None


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quand l'admin répond (en reply) à un message reçu, on renvoie au bon client."""
    admin_msg = update.message
    if not admin_msg:
        return

    if not admin_msg.reply_to_message:
        await admin_msg.reply_text("Réponds en utilisant « Répondre » sur le message du client.")
        return

    replied = admin_msg.reply_to_message.text or ""
    client_id = extract_client_id_from_admin_context(replied)

    # fallback: mapping par message_id (si jamais)
    if not client_id:
        client_id = _store(context)["admin_msg_to_client"].get(admin_msg.reply_to_message.message_id)

    if not client_id:
        await admin_msg.reply_text("Impossible de retrouver le client. Réponds sur un message qui contient 'ID: ...'.")
        return

    # Ouvre le chat
    st = get_user_state(context, client_id)
    st["step"] = "CHAT_OPEN"

    await context.bot.send_message(chat_id=client_id, text=f"👨‍🍳 Admin :\n{admin_msg.text}")
    await admin_msg.reply_text("✅ Envoyé au client.")


# ======================
# Client flow
# ======================
UBER_LINK_HELP = (
    "🔗 **Lien Uber Eats (commande groupée)**\n\n"
    "1) Fais ton panier sur Uber Eats\n"
    "2) Choisis l’option **Commande groupée**\n"
    "3) Copie le lien d’invitation et colle-le ici\n\n"
    "✅ Colle le lien dès que tu l’as."
)

async def handle_client_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    user = update.effective_user
    st = get_user_state(context, user.id)

    # Boutons menu
    if text == "Commander 🍔":
        st["step"] = "PAY"
        await msg.reply_text("Quel est le mode de paiement ?", reply_markup=PAY_MENU)
        return

    if text == "Retour ↩️":
        st["step"] = None
        await msg.reply_text("Menu :", reply_markup=MENU)
        return

    if text == "Contacter admin 👨‍🍳":
        # On autorise la demande admin, mais on ne doit pas déclencher "commande reçue"
        st["step"] = "WAIT_ADMIN"
        ok = await safe_send_admin(
            context,
            "💬 Demande admin\n"
            f"Nom: {user.full_name}\n"
            f"User: {user_tag(user)}\n"
            f"ID: {user.id}\n\n"
            "Le client veut être contacté."
        )
        if ok:
            await msg.reply_text("✅ C’est noté. Un admin va te répondre bientôt.")
        else:
            await msg.reply_text("✅ Demande prise en compte. (Admin doit faire /start sur le bot pour recevoir les notifs.)")
        return

    # Choix paiement
    if st["step"] == "PAY":
        if text == "Crypto 🪙":
            st["payment"] = "Crypto"
        elif text == "Virement instantané ⚡️":
            st["payment"] = "Virement instantané"
        elif text == "Revolut 💳":
            st["payment"] = "Revolut"
        else:
            await msg.reply_text("Choisis un paiement dans le menu.", reply_markup=PAY_MENU)
            return

        st["step"] = "WAIT_LINK"
        await msg.reply_text("Parfait ✅ Maintenant envoie ton lien Uber Eats.", reply_markup=MENU)
        await msg.reply_text(UBER_LINK_HELP)
        return

    # Réception lien
    if st["step"] == "WAIT_LINK":
        link = text
        st["ordered"] = True
        st["step"] = "WAIT_ADMIN"  # on attend la réponse admin avant d'ouvrir le chat

        await msg.reply_text("✅ Commande reçue. Un admin va te répondre bientôt.")

        admin_text = (
            "🛒 Nouvelle commande\n\n"f"Nom: {user.full_name}\n"
            f"User: {user_tag(user)}\n"
            f"ID: {user.id}\n"
            f"Paiement: {st['payment']}\n\n"
            f"Lien Uber:\n{link}\n\n"
            "➡️ Réponds en faisant « Répondre » à ce message."
        )

        ok = await safe_send_admin(context, admin_text, buttons=admin_status_buttons(user.id))
        if ok:
            # mapping message_id -> client_id pour les statuts / fallback
            # (on ne récupère pas l'objet msg ici, donc on ne mappe pas, mais le texte contient ID:)
            pass
        else:
            await msg.reply_text("⚠️ L’admin doit faire /start sur le bot pour recevoir les commandes.")
        return

    # Messages après commande mais avant réponse admin
    if st["step"] == "WAIT_ADMIN" and st["ordered"]:
        await msg.reply_text("⏳ Bien reçu. Un admin va te répondre bientôt.")
        return

    # Chat ouvert : on forward à l’admin
    if st["step"] == "CHAT_OPEN":
        admin_text = (
            "💬 Message client\n\n"
            f"Nom: {user.full_name}\n"
            f"User: {user_tag(user)}\n"
            f"ID: {user.id}\n\n"
            f"Message:\n{text}"
        )
        ok = await safe_send_admin(context, admin_text)
        if ok:
            await msg.reply_text("✅ Bien reçu.")
        else:
            await msg.reply_text("✅ Bien reçu. (Admin doit faire /start sur le bot pour recevoir.)")
        return

    # Par défaut (anti-spam)
    await msg.reply_text("Clique sur « Commander 🍔 » pour commencer.", reply_markup=MENU)


# ======================
# Callback (status buttons)
# ======================
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return

    user = update.effective_user
    if user.id != ADMIN_ID:
        await q.answer("Réservé à l’admin.", show_alert=True)
        return

    data = q.data or ""
    parts = data.split("|")
    if len(parts) != 3 or parts[0] != "status":
        await q.answer()
        return

    client_id = int(parts[1])
    code = parts[2]

    # Ouvre le chat (statut = réponse admin)
    st = get_user_state(context, client_id)
    st["step"] = "CHAT_OPEN"

    await context.bot.send_message(chat_id=client_id, text=status_text(code))
    await q.answer("Envoyé au client ✅")


# ======================
# Router
# ======================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    if user.id == ADMIN_ID:
        await handle_admin_message(update, context)
    else:
        await handle_client_message(update, context)


# ======================
# Run
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("Bot en ligne ✅")
    print("⚠️ IMPORTANT: l’admin doit faire /start au moins 1 fois sur le bot.")
    app.run_polling()


if __name__ == "__main__":
    main()