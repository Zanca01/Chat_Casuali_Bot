import logging
import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

# Configurazioni
TOKEN = "8131291256:AAGws2uy8rik7904BQUAOFPbjOvjcl9fELY"
WEBHOOK_URL = https://merry-reprieve-production.up.railway.app/webhook


# Inizializzazione
app = Flask(__name__)
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# Dizionario per gestire gli utenti in chat anonime
waiting_users = set()
active_chats = {}

# Gestore /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto! Usa /chat per iniziare una chat anonima.")

# Gestore /chat
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id in active_chats:
        await update.message.reply_text("Sei già in una chat! Usa /stop per terminare.")
        return

    if waiting_users:
        partner_id = waiting_users.pop()
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await bot.send_message(user_id, "Sei connesso con un utente! Digita per chattare.")
        await bot.send_message(partner_id, "Sei connesso con un utente! Digita per chattare.")
    else:
        waiting_users.add(user_id)
        await update.message.reply_text("In attesa di un altro utente...")

# Gestore /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await bot.send_message(partner_id, "L'altro utente ha terminato la chat.")
        await update.message.reply_text("Hai terminato la chat.")
    else:
        waiting_users.discard(user_id)
        await update.message.reply_text("Non sei in una chat attiva.")

# Gestore /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Utente segnalato. Il team esaminerà il caso.")

# Gestore dei messaggi
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if update.message.text:
            await bot.send_message(partner_id, update.message.text)
        elif update.message.photo:
            await bot.send_photo(partner_id, update.message.photo[-1].file_id)
        elif update.message.video:
            await bot.send_video(partner_id, update.message.video.file_id)
        elif update.message.audio:
            await bot.send_audio(partner_id, update.message.audio.file_id)

# Webhook per ricevere gli aggiornamenti di Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# Configurazione degli handler
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("chat", chat))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("report", report))
application.add_handler(MessageHandler(filters.ALL, handle_messages))

# Avvio del webhook
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )
