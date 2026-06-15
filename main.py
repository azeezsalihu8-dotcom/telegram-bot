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

# ---------------- ENV SAFETY ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in environment variables")

# ---------------- APP SETUP ----------------
app = FastAPI()
bot = Bot(token=BOT_TOKEN)

application = Application.builder().token(BOT_TOKEN).build()


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Yo 👋 bot is live.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "/start - start bot\n"
            "/help - help menu\n"
            "Send any message to test bot"
        )


# ---------------- NORMAL MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text("Bot is working 🔥")


# register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ---------------- LIFECYCLE ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()

    # set webhook only if provided
    if WEBHOOK_URL:
        await application.bot.set_webhook(WEBHOOK_URL)


@app.post("/")
async def webhook(req: Request):
    data = await req.json()

    update = Update.de_json(data, bot)
    await application.process_update(update)

    return {"ok": True}


@app.get("/")
async def home():
    return "Bot running"