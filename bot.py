import os
import asyncio
import threading
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ====== ENV ======
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_STR = os.getenv("ADMIN_ID", "").strip()
WHATSAPP_URL = os.getenv("WHATSAPP_URL", "").strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN manquant (Render > Environment).")
if not ADMIN_ID_STR:
    raise RuntimeError("ADMIN_ID manquant (Render > Environment).")

ADMIN_ID = int(ADMIN_ID_STR)

# ====== Global thread state ======
_bot_thread: Optional[threading.Thread] = None
_started = False

# ====== Simple in-memory state (par user) ======
# state: None | "WAIT_UBER_LINK"
USER_STATE = {}  # user_id -> state
USER_PAYMENT = {}  # user_id -> "CB" | "ESPECES"

# ====== Keyboards ======
def kb_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Commander", callback_data="go_order")],
        [InlineKeyboardButton("📞 Appeler un admin", callback_data="call_admin")],
    ])

def kb_payment() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Carte bancaire", callback_data="pay_card")],
        [InlineKeyboardButton("💶 Espèces", callback_data="pay_cash")],
        [InlineKeyboardButton("↩️ Retour", callback_data="back_home")],
    ])

def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Retour", callback_data="back_home")],
    ])

def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Voir mon ADMIN_ID", callback_data="admin_id")],
    ])

# ====== Commands ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    # Reset state quand on fait /start
    USER_STATE.pop(user.id, None)
    USER_PAYMENT.pop(user.id, None)

    # Admin
    if user.id == ADMIN_ID:
        await update.message.reply_text("🛠️ Admin panel", reply_markup=kb_admin())
        return

    # Client : menu direct (pas de message "welcome" long)
    await update.message.reply_text("Choisis une option :", reply_markup=kb_home())

# ====== Callbacks ======
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()

    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    data = q.data or ""

    # Admin
    if user.id == ADMIN_ID and data == "admin_id":
        await q.edit_message_text(f"✅ Ton ADMIN_ID = {ADMIN_ID}")
        return

    # Client flow
    if data == "back_home":
        USER_STATE.pop(user.id, None)
        USER_PAYMENT.pop(user.id, None)
        await q.edit_message_text("Choisis une option :", reply_markup=kb_home())
        return

    if data == "go_order":
        USER_STATE.pop(user.id, None)
        USER_PAYMENT.pop(user.id, None)
        await q.edit_message_text("Choisis ton mode de paiement :", reply_markup=kb_payment())
        return

    if data in ("pay_card", "pay_cash"):
        USER_PAYMENT[user.id] = "CB" if data == "pay_card" else "ESPECES"
        USER_STATE[user.id] = "WAIT_UBER_LINK"
        await q.edit_message_text(
            "✅ Ok.\n"
            "Maintenant, envoie ton lien Uber Eats ici (un lien qui commence par http).\n\n"
            "Exemple : https://...",
            reply_markup=kb_back(),
        )
        return

    if data == "call_admin":
        username = f"@{user.username}" if user.username else "(pas de username)"
        msg_admin = (
            "📞 Un client demande un admin\n"
            f"• Nom: {user.first_name}\n"
            f"• Username: {username}\n"
            f"• User ID: {user.id}\n"
            f"• Chat ID: {chat.id}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin)

        if WHATSAPP_URL:
            await q.edit_message_text(
                "✅ Ok. Clique ici pour contacter l’admin :",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 Contacter l’admin", url=WHATSAPP_URL)],
                    [InlineKeyboardButton("↩️ Retour", callback_data="back_home")],
                ]),
                disable_web_page_preview=True,
            )
        else:
            await q.edit_message_text("✅ Ok. Un admin va te contacter.", reply_markup=kb_home())
        return

# ====== Messages (réception du lien Uber Eats) ======
def _looks_like_url(text: str) -> bool:
    t = text.strip().lower()
    return t.startswith("http://") or t.startswith("https://")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.message
    if not user or not chat or not msg or not msg.text:
        return

    # Admin: on ignore ici (tu peux ajouter commandes admin plus tard)
    if user.id == ADMIN_ID:
        return

    state = USER_STATE.get(user.id)

    # Si le client n'est pas en "commande", on ne répond pas (comme tu veux)
    if state != "WAIT_UBER_LINK":
        return

    text = msg.text.strip()

    if not _looks_like_url(text):
        await msg.reply_text(
            "⚠️ Envoie un lien valide (qui commence par http).\n"
            "Sinon clique ↩️ Retour.",
            reply_markup=kb_back(),
        )
        return

    payment = USER_PAYMENT.get(user.id, "N/A")
    username = f"@{user.username}" if user.username else "(pas de username)"

    # Envoi à l'admin
    msg_admin = (
        "🛒 Nouvelle commande (lien client)\n"
        f"• Paiement: {payment}\n"
        f"• Client: {user.first_name} ({username})\n"
        f"• User ID: {user.id}\n"
        f"• Lien Uber Eats: {text}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, disable_web_page_preview=True)

    # Confirmation courte au client (pas de welcome/deals)
    await msg.reply_text("✅ Reçu.", reply_markup=kb_home())

    # Reset state
    USER_STATE.pop(user.id, None)
    USER_PAYMENT.pop(user.id, None)

# ===== Bot runner (thread-safe) =====
async def _run_bot_async():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    await asyncio.Event().wait()

def _thread_main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run_bot_async())

def run_bot():
    global _bot_thread, _started
    if _started:
        return
    _started = True
    _bot_thread = threading.Thread(target=_thread_main, daemon=True)
    _bot_thread.start()
