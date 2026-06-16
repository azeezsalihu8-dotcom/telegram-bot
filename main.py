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

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- MEMORY ----------------
approved_users = set()
all_users = set()
pending_users = set()
activation_codes = {}

# ---------------- HELPERS ----------------
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def register(user_id):
    all_users.add(str(user_id))

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔓 Request Access", callback_data="request")],
        [InlineKeyboardButton("ℹ️ Why ID?", callback_data="whyid")],
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
            "🚫 You are not registered. Please contact @tariq_jam75 to recive activation code.Send your id for approval as well.",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text("🔥 Welcome back")

# ---------------- ID COMMAND ----------------
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    await update.message.reply_text(
        f"👤 Your Telegram ID:\n{user_id}\n\n"
        "This ID is used so the system knows exactly who you are.\n"
        "Without it, we cannot approve or track your access."
    )

# ---------------- BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    register(user_id)

    # request access
    if query.data == "request":
        pending_users.add(user_id)

        await query.message.reply_text(
            "📩 Request sent.\n"
            "Wait for admin approval.\n\n"
            f"Your ID: {user_id}\n"
            "Send this ID if needed for verification.",
            reply_markup=main_menu()
        )

    # explain ID
    elif query.data == "whyid":
        await query.message.reply_text(
            "📌 WHY WE NEED YOUR ID\n\n"
            "Every Telegram user has a unique ID.\n"
            "We use it to:\n"
            "- identify your account\n"
            "- give access correctly\n"
            "- prevent fake accounts\n\n"
            "Without ID, we cannot approve you.",
            reply_markup=main_menu()
        )

# ---------------- AUTO APPROVE (ADMIN ONLY BUTTON FLOW) ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    # simple admin lock (you can keep or remove later)
    if not context.args:
        await update.message.reply_text("Use /approve <user_id>")
        return

    target = context.args[0]
    approved_users.add(target)

    if target in pending_users:
        pending_users.remove(target)

    await update.message.reply_text(f"Approved {target} ✔️")

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
application.add_handler(CommandHandler("myid", myid))
application.add_handler(CommandHandler("approve", approve))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("activate", activate))
application.add_handler(CallbackQueryHandler(button_handler))

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()

    if WEBHOOK_URL:
        await application.bot.set_webhook(WEBHOOK_URL)

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