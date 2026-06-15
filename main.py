import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("8735772930:AAFhqW6gp0WTPAC2my5oxeMH8MHfGxKYLbQ")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)

application = Application.builder().token(BOT_TOKEN).build()


# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Yo 👋 Bot is live.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "/start - start bot\n"
            "/help - help menu\n"
            "Send anything else and I’ll reply."
        )


# ---------------- MESSAGE HANDLER ----------------

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text("Bot is alive 🔥")


# register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))


# ---------------- WEBHOOK SETUP ----------------

@app.on_event("startup")
async def on_startup():
    await application.initialize()

    # set webhook only if URL exists
    if WEBHOOK_URL:
        await application.bot.set_webhook(url=WEBHOOK_URL)


@app.post("/")
async def webhook(req: Request):
    data = await req.json()

    update = Update.de_json(data, bot)
    await application.process_update(update)

    return {"ok": True}


@app.get("/")
async def home():
    return "Bot is running"