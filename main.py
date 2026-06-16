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

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# 🔐 secret access key (change this)
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

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    register(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "You are not registered. Please contact @tariq_jam75 to activate your account."
        )
        return

    await update.message.reply_text("Welcome back 🔥")

# ---------------- MESSAGE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    register(user_id)

    if user_id not in approved_users:
        await update.message.reply_text(
            "You are not registered. Please contact @tariq_jam75 to activate your account."
        )
        return

    await update.message.reply_text("Working ✔️")

# ---------------- GENERATE CODE ----------------
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if not context.args:
        await update.message.reply_text("Use /code <key>")
        return

    key = context.args[0]

    if key != SECRET_KEY:
        await update.message.reply_text("Wrong key ❌")
        return

    new_code = generate_code()
    activation_codes[new_code] = "valid"

    await update.message.reply_text(f"CODE:\n{new_code}")

# ---------------- APPROVE USER ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if not context.args:
        await update.message.reply_text("Use /approve <user_id>")
        return

    target = context.args[0]
    approved_users.add(target)

    await update.message.reply_text(f"Approved {target} ✔️")

# ---------------- USER LIST ----------------
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
application.add_handler(CommandHandler("code", code))
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

@app.get("/")
async def home():
    return {"bot": "running"}