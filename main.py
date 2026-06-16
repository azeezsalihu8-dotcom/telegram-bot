import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in environment variables")

# ---------------- APPS ----------------
app = FastAPI()

application = Application.builder().token(BOT_TOKEN).build()

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Bot is live 🔥")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "/start\n"
            "/help\n"
            "Send anything"
        )

# ---------------- MESSAGE HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text("Working ✔️")

# ---------------- ERROR HANDLER ----------------
async def error_handler(update, context):
    logger.error("Exception while handling update:", exc_info=context.error)

# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
)
application.add_error_handler(error_handler)

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()

    if WEBHOOK_URL:
        await application.bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to: {WEBHOOK_URL}")

# ---------------- SHUTDOWN ----------------
@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

# ---------------- WEBHOOK ----------------
@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------------- HOME ----------------
@app.get("/")
async def home():
    return {"message": "Bot running"}