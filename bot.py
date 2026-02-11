import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- Etats simples par utilisateur ---
# on stocke où en est le client (choix paiement / attente lien)
USER_STATE = {}  # user_id -> dict

INFO_MSG = (
    "ℹ️ Infos importantes :\n"
    "• Les restaurants sans Uber One ne sont malheureusement pas éligibles à la réduction -50%.\n"
    "• Tu peux préparer plusieurs paniers dans le même restaurant si tu veux cumuler.\n"
    "• Les offres Uber Eats (ex : 1 acheté = 1 offert) restent valables avec la réduction."
)

def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛒 Commander")],
            [KeyboardButton("📞 Contacter admin")],
        ],
        resize_keyboard=True
    )

def pay_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🪙 Crypto")],
            [KeyboardButton("💳 Revolut")],
            [KeyboardButton("🏦 Virement instantané")],
            [KeyboardButton("⬅️ Retour")],
        ],
        resize_keyboard=True
    )

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pas de “message de bienvenue” long -> juste le menu direct
    await update.message.reply_text("Choisis une option :", reply_markup=main_menu())

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    user = update.effective_user
    chat_id = update.effective_chat.id

    # sécurité
    if not user:
        return

    uid = user.id
    state = USER_STATE.get(uid, {})

    # --- boutons menu principal ---
    if txt == "🛒 Commander":
        USER_STATE[uid] = {"step": "choose_pay"}
        await update.message.reply_text("Choisis ton moyen de paiement :", reply_markup=pay_menu())
        return

    if txt == "📞 Contacter admin":
        # notif admin
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📞 Demande admin\n👤 {user.full_name}\n🆔 {uid}\n💬 Le client veut te parler."
            )
        await update.message.reply_text("✅ Admin contacté. Un admin va te répondre ici.", reply_markup=main_menu())
        return

    # --- menu paiement ---
    if txt == "⬅️ Retour":
        USER_STATE.pop(uid, None)
        await update.message.reply_text("Choisis une option :", reply_markup=main_menu())
        return

    if state.get("step") == "choose_pay" and txt in ["🪙 Crypto", "💳 Revolut", "🏦 Virement instantané"]:
        USER_STATE[uid] = {"step": "wait_link", "pay": txt}
        await update.message.reply_text(INFO_MSG)
        await update.message.reply_text(
            "🔗 Envoie maintenant ton *lien Uber Eats de commande groupée*.\n"
            "👉 C’est le lien que Uber Eats te donne quand tu fais “commande groupée / partager le panier”.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    # --- attente du lien ---
    if state.get("step") == "wait_link":
        link = txt

        # envoie à l’admin
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🛒 Nouvelle commande\n"
                    f"👤 {user.full_name}\n"
                    f"🆔 {uid}\n"
                    f"💰 Paiement: {state.get('pay')}\n"
                    f"🔗 Lien: {link}"
                )
            )

        USER_STATE.pop(uid, None)
        await update.message.reply_text("✅ Lien reçu. Un admin va répondre ici.", reply_markup=main_menu())
        return

    # si le mec écrit un truc random
    await update.message.reply_text("Choisis une option :", reply_markup=main_menu())

def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN manquant dans les variables Render")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # IMPORTANT: polling unique
    app.run_polling(drop_pending_updates=True)
