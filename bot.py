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
)

# ====== ENV ======
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_STR = os.getenv("ADMIN_ID", "").strip()

# Lien Uber Eats (à mettre dans Render > Environment)
UBER_EATS_URL = os.getenv("UBER_EATS_URL", "").strip()

# Optionnel : ton WhatsApp ou autre lien
WHATSAPP_URL = os.getenv("WHATSAPP_URL", "").strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN manquant (Render > Environment).")
if not ADMIN_ID_STR:
    raise RuntimeError("ADMIN_ID manquant (Render > Environment).")

ADMIN_ID = int(ADMIN_ID_STR)

# ====== Global thread state ======
_bot_thread: Optional[threading.Thread] = None
_started = False

# ====== Helpers UI ======
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

def kb_ubereats() -> InlineKeyboardMarkup:
    buttons = []
    if UBER_EATS_URL:
        buttons.append([InlineKeyboardButton("🍔 Ouvrir Uber Eats", url=UBER_EATS_URL)])
    else:
        buttons.append([InlineKeyboardButton("🍔 Ouvrir Uber Eats", callback_data="missing_ubereats")])

    buttons.append([InlineKeyboardButton("↩️ Retour", callback_data="back_home")])
    return InlineKeyboardMarkup(buttons)

def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Voir mon ADMIN_ID", callback_data="admin_id")],
    ])

# ====== Logic ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    # Admin
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "🛠️ Admin panel",
            reply_markup=kb_admin(),
            disable_web_page_preview=True,
        )
        return

    # Client : pas de message “welcome”, juste menu direct
    await update.message.reply_text(
        "Choisis une option :",
        reply_markup=kb_home(),
        disable_web_page_preview=True,
    )

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

    # ===== Admin callbacks =====
    if user.id == ADMIN_ID and data == "admin_id":
        await q.edit_message_text(f"✅ Ton ADMIN_ID = {ADMIN_ID}")
        return

    # ===== Client flow =====
    if data == "back_home":
        await q.edit_message_text("Choisis une option :", reply_markup=kb_home())
        return

    if data == "go_order":
        await q.edit_message_text("Choisis ton mode de paiement :", reply_markup=kb_payment())
        return

    if data in ("pay_card", "pay_cash"):
        pay_txt = "💳 Carte bancaire" if data == "pay_card" else "💶 Espèces"
        await q.edit_message_text(
            f"Paiement choisi : {pay_txt}\n\nMaintenant clique ici :",
            reply_markup=kb_ubereats(),
            disable_web_page_preview=True,
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
        )await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin)

        # Si tu veux ouvrir direct WhatsApp au client, sinon juste confirmation
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

    if data == "missing_ubereats":
        await q.edit_message_text(
            "⚠️ Lien Uber Eats non configuré.\n"
            "Ajoute UBER_EATS_URL dans Render > Environment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Retour", callback_data="back_home")]]),
        )
        return

# ===== Bot runner (thread-safe) =====
async def _run_bot_async():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))

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
