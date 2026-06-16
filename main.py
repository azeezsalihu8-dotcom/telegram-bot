import os
import logging
import random
import string
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

SECRET_KEY = "cookie75"

# ---------------- APP ----------------
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- MEMORY ----------------
approved_users = set()
all_users = set()
activation_codes = {}

# ---------------- HELPERS ----------------
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def register(user_id):
    all_users.add(str(user_id))

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔓 Activate", callback_data="activate")],
        [InlineKeyboardButton("ℹ️ Instructions", callback_data="info")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/tariq_jam75")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)
    register(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "🚫 You are not registered.\nContact support to get access.",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text(
        "🔥 Welcome back",
        reply_markup=main_menu()
    )

# ---------------- CALLBACK BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    register(user_id)

    if query.data == "info":
        await query.message.reply_text(
            "📌 HOW IT WORKS:\n\n"
            "1. Get approved\n"
            "2. Use /activate <code>\n"
            "3. Start using bot",
            reply_markup=main_menu()
        )

    elif query.data == "activate":
        await query.message.reply_text(
            "Send:\n/activate <your_code>",
            reply_markup=main_menu()
        )

# ---------------- MESSAGE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)
    register(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "🚫 Not registered. Contact support.",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text("✔️ Working...")

# ---------------- CODE GENERATOR ----------------
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args or context.args[0] != SECRET_KEY:
        await update.message.reply_text("Wrong key ❌")
        return

    new_code = generate_code()
    activation_codes[new_code] = "valid"

    await update.message.reply_text(f"CODE:\n{new_code}")

# ---------------- APPROVE USER ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Use /approve <user_id>")
        return

    target = context.args[0]
    approved_users.add(target)

    await update.message.reply_text(f"Approved {target} ✔️")

# ---------------- ACTIVATE ----------------
async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Use /activate <code>")
        return

    code = context.args[0]

    if code not in activation_codes:
        await update.message.reply_text("Invalid code ❌")
        return

    if activation_codes[code] == "used":
        await update.message.reply_text("Already used ❌")
        return

    user_id = str(update.message.from_user.id)
    approved_users.add(user_id)
    activation_codes[code] = "used"

    await update.message.reply_text("🔥 Activated successfully!")

# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("approve", approve))
application.add_handler(CommandHandler("activate", activate))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()

    if WEBHOOK_URL:
        await application.bot.set_webhook(WEBHOOK_URL)

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

# ---------------- HOME ----------------
@app.get("/")
async def home():
    return {"bot": "running"}