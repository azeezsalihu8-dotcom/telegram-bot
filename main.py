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
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

# ---------------- APP ----------------
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- MEMORY ----------------
approved_users = set()
all_users = set()

# ---------------- HELPERS ----------------
def is_admin(user_id):
    return ADMIN_ID and str(user_id) == str(ADMIN_ID)

def register_user(user_id):
    all_users.add(str(user_id))

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)
    register_user(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "You are not registered. Please contact @tariq_jam75 to register your account."
        )
        return

    await update.message.reply_text("Welcome back 🔥")

# ---------------- MESSAGE HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    register_user(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "You are not registered. Please contact @tariq_jam75 to register your account."
        )
        return

    await update.message.reply_text("Working ✔️")

# ---------------- APPROVE USER ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    if not is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text("Use /approve <user_id>")
        return

    target = context.args[0]
    approved_users.add(target)

    await update.message.reply_text(f"Approved {target} ✔️")

# ---------------- USER LIST ----------------
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    if not is_admin(user_id):
        return

    if not all_users:
        await update.message.reply_text("No users yet.")
        return

    text = "📋 USERS:\n\n"
    for u in all_users:
        status = "✅" if u in approved_users else "❌"
        text += f"{u} {status}\n"

    await update.message.reply_text(text)

# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("approve", approve))
application.add_handler(CommandHandler("users", users_list))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()

    if WEBHOOK_URL:
        await application.bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set")

# ---------------- SHUTDOWN ----------------
@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

# ---------------- WEBHOOK ----------------
@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# ---------------- HEALTH ----------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------------- HOME ----------------
@app.get("/")
async def home():
    return {"bot": "running"}