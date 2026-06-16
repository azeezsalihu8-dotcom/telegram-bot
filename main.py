import os
import json
import random
import string
import logging
import shutil
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

OWNER_ID = 7874825323
SECRET_KEY = "cookie75"

DB_FILE = "database.json"
PHONE_FILE = "phones.json"

REQUEST_COST = 0.10

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- BACKUP ----------------
def backup_db():
    try:
        if os.path.exists(DB_FILE):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(DB_FILE, f"backup_{ts}.json")
    except Exception as e:
        logging.error(f"Backup error: {e}")

# ---------------- FILES ----------------
def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

db = load_json(DB_FILE, {"users": {}, "codes": {}})
phones = load_json(PHONE_FILE, {})

# ---------------- USER ----------------
def get_user(user_id):
    user_id = str(user_id)

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "activated": False,
            "balance": 0.0,
        }
        save_json(DB_FILE, db)

    return db["users"][user_id]

# ---------------- MENU ----------------
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Activate", callback_data="activate")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📖 Help", callback_data="help")]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Welcome\nUse /help",
        reply_markup=menu()
    )

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 SERVICE PLAN\n\n"
        "🔓 Activation: FREE\n"
        "💰 Price: $0.10 per line\n\n"
        "💳 BTC ONLY:\n"
        "bc1qh0jqcxkez9hu33u66y6j03dw60gdazuqzw9e6q\n"
        "(Tap & hold to copy)\n\n"
        "⚠️ Payment must be done within 1 hour\n\n"
        "Commands:\n"
        "/activate <code>\n"
        "/balance\n"
        "/phone <model>\n"
        "/myid\n"
        "/support"
    )

# ---------------- SUPPORT ----------------
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 SUPPORT\n\n"
        "@tariq_jam75\n"
        "For payment or access issues"
    )

# ---------------- MY ID ----------------
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 {update.message.from_user.id}")

# ---------------- BALANCE ----------------
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    await update.message.reply_text(f"💰 Balance: ${round(user['balance'], 2)}")

# ---------------- OWNER CODE ----------------
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    if not context.args or context.args[0] != SECRET_KEY:
        await update.message.reply_text("❌ Wrong key")
        return

    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    db["codes"][new_code] = {"used": False, "user": None}
    save_json(DB_FILE, db)
    backup_db()

    await update.message.reply_text(f"CODE:\n{new_code}")

# ---------------- OWNER CREDIT ----------------
async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Use /credit <user_id> <amount>")
        return

    user_id = context.args[0]
    amount = float(context.args[1])

    user = get_user(user_id)
    user["balance"] += amount

    save_json(DB_FILE, db)
    backup_db()

    await update.message.reply_text(f"✅ Added ${amount}")

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

    db["codes"][code] = {"used": True, "user": user_id}
    user["activated"] = True

    save_json(DB_FILE, db)
    backup_db()

    await update.message.reply_text("🔥 Activated!")

# ---------------- PHONE ----------------
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    is_owner = update.message.from_user.id == OWNER_ID

    if not user["activated"] and not is_owner:
        await update.message.reply_text("🚫 Activate first")
        return

    if not context.args:
        await update.message.reply_text("Use /phone <model>")
        return

    model = " ".join(context.args).lower()

    if model not in phones:
        await update.message.reply_text("❌ Not found")
        return

    data = phones[model]

    lines = len(data)
    cost = lines * REQUEST_COST

    if not is_owner and user["balance"] < cost:
        await update.message.reply_text(
            f"💰 Need ${round(cost, 2)} but you have ${round(user['balance'], 2)}"
        )
        return

    if not is_owner:
        user["balance"] -= cost
        save_json(DB_FILE, db)
        backup_db()

    text = f"📱 {model.upper()}\n\n"

    for k, v in data.items():
        text += f"{k}: {v}\n"

    text += "\n💳 Pay using BTC:\n"
    text += "bc1qh0jqcxkez9hu33u66y6j03dw60gdazuqzw9e6q\n"
    text += "(Tap & hold to copy)\n"
    text += "⚠️ Pay within 1 hour\n"

    await update.message.reply_text(text)

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if query.data == "activate":
        await query.message.reply_text("Use /activate <code>")

    elif query.data == "balance":
        await query.message.reply_text(f"💰 Balance: ${round(user['balance'], 2)}")

    elif query.data == "help":
        await help_cmd(update, context)

# ---------------- HANDLERS ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("activate", activate))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("credit", credit))
application.add_handler(CommandHandler("phone", phone))
application.add_handler(CommandHandler("myid", myid))
application.add_handler(CommandHandler("support", support))
application.add_handler(CallbackQueryHandler(buttons))

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
    return {"status": "running"}