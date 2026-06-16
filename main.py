import os
import json
import random
import string
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

SECRET_KEY = "cookie75"
DB_FILE = "database.json"

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- DATABASE ----------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "codes": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

db = load_db()

def get_user(user_id):
    user_id = str(user_id)

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "activated": False,
            "balance": 0.0,
            "used_codes": []
        }
        save_db(db)

    return db["users"][user_id]

# ---------------- MENU ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Activate", callback_data="activate")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📖 Help", callback_data="help")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/tariq_jam75")]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)

    text = "🔥 Welcome to the system"

    if not user["activated"]:
        text = "🚫 You are not activated yet.  Please contact @tariq_jam75 to recive activation code."

    await update.message.reply_text(text, reply_markup=main_menu())

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 COMMANDS\n\n"
        "/start - menu\n"
        "/activate <code> - unlock access\n"
        "/balance - check wallet\n"
        "/code <key> - generate code\n"
    )

# ---------------- BALANCE ----------------
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    await update.message.reply_text(f"💰 Balance: ${user['balance']}")

# ---------------- CODE GENERATOR ----------------
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != SECRET_KEY:
        await update.message.reply_text("❌ Wrong key")
        return

    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    db["codes"][new_code] = {
        "used": False,
        "user": None
    }

    save_db(db)

    await update.message.reply_text(f"CODE:\n{new_code}")

# ---------------- ACTIVATE ----------------
async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use /activate <code>")
        return

    code = context.args[0]
    user_id = str(update.message.from_user.id)

    user = get_user(user_id)

    if code not in db["codes"]:
        await update.message.reply_text("❌ Invalid code")
        return

    if db["codes"][code]["used"]:
        await update.message.reply_text("❌ Code already used")
        return

    db["codes"][code] = {
        "used": True,
        "user": user_id
    }

    user["activated"] = True

    save_db(db)

    await update.message.reply_text("🔥 Activated successfully!")

# ---------------- MENU BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if query.data == "activate":
        await query.message.reply_text("Use /activate <code>")

    elif query.data == "balance":
        await query.message.reply_text(f"💰 Balance: ${user['balance']}")

    elif query.data == "help":
        await query.message.reply_text(
            "📌 HOW IT WORKS\n\n"
            "1. Get code\n"
            "2. Activate bot\n"
            "3. Use features\n\n"
            "/activate <code>\n"
            "/balance\n"
        )

# ---------------- MESSAGE HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)

    if not user["activated"]:
        await update.message.reply_text("🚫 Activate first using /activate <code>")
        return

    # future wallet deduction hook (step 2 ready)
    await update.message.reply_text("✔️ Working...")

# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("activate", activate))
application.add_handler(CommandHandler("code", code))
application.add_handler(CallbackQueryHandler(buttons))
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
    return {"status": "running"}