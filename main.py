import os
import json
import random
import logging
import shutil

from datetime import datetime
from fastapi import FastAPI, Request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from pymongo import MongoClient

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =====================================================
# CONFIG
# =====================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

OWNER_ID = 7874825323

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)

db = client["poetry_bot"]
users = db["users"]



POEMS_FOLDER = "poems"

LINE_COST = 1

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI()

application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

# =====================================================
# USER
# =====================================================

def get_user(user_id):

    try:

        user = users.find_one(
            {"user_id": str(user_id)}
        )

        if user is None:

            user = {
                "user_id": str(user_id),
                "balance": 0,
                "transactions": []
            }

            users.insert_one(user)

        return user

    except Exception as e:

        logging.exception(e)

        return {
            "user_id": str(user_id),
            "balance": 0,
            "transactions": []
        }

# =====================================================
# POEM READER
# =====================================================

def read_poems(category):

    path = os.path.join(

        POEMS_FOLDER,

        f"{category}.txt"

    )

    if not os.path.exists(path):

        return []

    with open(path, "r", encoding="utf-8") as f:

        text = f.read()

    poems = [

        poem.strip()

        for poem in text.split("===")

        if poem.strip()

    ]

    return poems


def random_poem(category):

    poems = read_poems(category)

    if not poems:

        return None

    return random.choice(poems)


def poem_lines(poem):

    return len(

        [

            line

            for line in poem.splitlines()

            if line.strip()

        ]

    )

# =====================================================
# MENU
# =====================================================

def menu():

    return InlineKeyboardMarkup(

        [

            [

                InlineKeyboardButton(

                    "📝 Get Bin",

                    callback_data="menu_poem"

                )

            ],

            [

                InlineKeyboardButton(

                    "💰 Balance",

                    callback_data="menu_balance"

                )

            ],

            [

                InlineKeyboardButton(

                    "📖 Help",

                    callback_data="menu_help"

                )

            ]

        ]

    )

# =====================================================
# COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    get_user(update.effective_user.id)

    await update.message.reply_text(

        "🎭 Welcome to the Cookie Bin Bot.\n\n"

        "Every Bin is charged based on the number of lines.\n\n"

        "Choose an option below.",

        reply_markup=menu()

    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "📖 Commands\n\n"

        "/start\n"

        "/balance\n"

        "/Bin\n\n"

        "1 credit = 1 line."

    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    await update.message.reply_text(

        f"💰 Balance: {user['balance']} credits"

    )
# =====================================================
# CATEGORY KEYBOARD
# =====================================================

def category_menu():

    return InlineKeyboardMarkup(

        [

            [

                InlineKeyboardButton(
                    "Buy_Bin",
                    callback_data="love"
                ),

                InlineKeyboardButton(
                    "Buy_Bin2",
                    callback_data="sad"
                )

            ],

            [

                InlineKeyboardButton(
                    "Buy_Bin3",
                    callback_data="motivation"
                ),

                InlineKeyboardButton(
                    "Buy_Bin4",
                    callback_data="friendship"
                )

            ]

        ]

    )


# =====================================================
# SEND RANDOM POEM
# =====================================================

async def send_poem(query, category):

    poem = random_poem(category)

    if poem is None:

        await query.message.reply_text(

            "❌ No bins found in this category."

        )

        return

    user = get_user(query.from_user.id)

    lines = poem_lines(poem)

    cost = lines * LINE_COST

    if user["balance"] < cost:

        await query.message.reply_text(

            f"❌ You need {cost} credits.\n"
            f"Current balance: {user['balance']}."

        )

        return

    user["balance"] -= cost

    user["transactions"].append(

        {

            "date": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),

            "category": category,

            "lines": lines,

            "cost": cost

        }

    )

    users.update_one(
    {"user_id": str(query.from_user.id)},
    {
        "$set": {
            "balance": user["balance"],
            "transactions": user["transactions"]
        }
    }
)
    await query.message.reply_text(

        f"{poem}\n\n"

        f"━━━━━━━━━━━━━━\n"

        f"📝 Lines: {lines}\n"

        f"💸 Charged: {cost} credits\n"

        f"💰 Remaining: {user['balance']} credits"

    )


# =====================================================
# /POETRY
# =====================================================

async def poetry(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "Choose a category.",

        reply_markup=category_menu()

    )


# =====================================================
# BUTTON HANDLER
# =====================================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "menu_poem":

        await query.message.reply_text(

            "Choose a category.",

            reply_markup=category_menu()

        )

    elif query.data == "menu_balance":

        user = get_user(query.from_user.id)

        await query.message.reply_text(

            f"💰 Balance: {user['balance']} credits"

        )

    elif query.data == "menu_help":

        await query.message.reply_text(

            "📖 Commands\n\n"

            "/Bin\n"

            "/balance\n\n"

            "1 credit = 1 line."

        )

    elif query.data in (

        "love",

        "sad",

        "motivation",

        "friendship"

    ):

        await send_poem(

            query,

            query.data

        )
# =====================================================
# OWNER COMMANDS
# =====================================================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        str(update.effective_user.id)
    )
async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n/credit <user_id> <credits>"
        )
        return

    user_id = context.args[0]

    try:
        credits = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Credits must be a number.")
        return

    user = get_user(user_id)

    user["balance"] += credits

    users.update_one(
        {"user_id": str(user_id)},
        {
            "$set": {
                "balance": user["balance"],
                "transactions": user["transactions"]
            }
        }
    )

    await update.message.reply_text(
        f"✅ Added {credits} credits.\n\n"
        f"User: {user_id}\n"
        f"Balance: {user['balance']}"
    )

# =====================================================
# HANDLERS
# =====================================================

application.add_handler(
    CommandHandler("start", start)
)

application.add_handler(
    CommandHandler("help", help_cmd)
)

application.add_handler(
    CommandHandler("balance", balance)
)

application.add_handler(
    CommandHandler("poetry", poetry)
)

application.add_handler(
    CommandHandler("credit", credit)
)

application.add_handler(
    CommandHandler("myid", myid)
)

application.add_handler(
    CallbackQueryHandler(buttons)
)

# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
async def startup():

    await application.initialize()

    await application.start()

    if WEBHOOK_URL:

        await application.bot.set_webhook(
            WEBHOOK_URL
        )

# =====================================================
# SHUTDOWN
# =====================================================

@app.on_event("shutdown")
async def shutdown():

    await application.stop()

    await application.shutdown()


# =====================================================
# WEBHOOK
# =====================================================

@app.post("/")
async def webhook(request: Request):

    data = await request.json()

    update = Update.de_json(
        data,
        application.bot
    )

    await application.process_update(update)

    return {"ok": True}


# =====================================================
# HOME
# =====================================================

@app.get("/")
async def home():

    return {
        "status": "running"
    }