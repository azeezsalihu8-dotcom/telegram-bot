import os
import logging
import random
import string
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

# 🔐 NEW: admin password (set this in Render)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD missing")

# ---------------- APP ----------------
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- MEMORY ----------------
users = {}
activation_codes = {}

# ---------------- HELPERS ----------------
def generate_code(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def is_authorized(password):
    return password == ADMIN_PASSWORD

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "active": False}

    await update.message.reply_text(
        "Welcome.\nUse /activate <code> to unlock bot."
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)
    user = users.get(user_id)

    if not user:
        await update.message.reply_text("Send /start first")
        return

    await update.message.reply_text(f"Balance: ${user['balance']}")


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Use /activate <code>")
        return

    user_id = str(update.message.from_user.id)
    code = context.args[0]

    if code not in activation_codes:
        await update.message.reply_text("Invalid code ❌")
        return

    if activation_codes[code] == "used":
        await update.message.reply_text("Code already used ❌")
        return

    users.setdefault(user_id, {"balance": 0, "active": False})
    users[user_id]["active"] = True

    activation_codes[code] = "used"

    await update.message.reply_text("Activated successfully 🔥")


# ---------------- NEW CODE GENERATOR ----------------
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Use /code <password>")
        return

    password = context.args[0]

    if not is_authorized(password):
        await update.message.reply_text("Wrong password ❌")
        return

    new_code = generate_code()
    activation_codes[new_code] = "valid"

    await update.message.reply_text(f"CODE:\n{new_code}")


# ---------------- MAIN HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    user = users.get(user_id)

    if not user:
        await update.message.reply_text("Send /start first")
        return

    if not user.get("active"):
        await update.message.reply_text("Activate bot first using /activate <code>")
        return

    await update.message.reply_text("Working ✔️")


# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("activate", activate))
application.add_handler(CommandHandler("code", code))
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