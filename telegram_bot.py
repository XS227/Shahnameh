# telegram_bot.py
import os

import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API_BASE_URL = "https://api.shahnamehgamefi.ir/api"
user_tokens = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username or f"user_{telegram_id}"
    password = f"tg_{telegram_id}"

    async with aiohttp.ClientSession() as session:
        reg_response = await session.post(f"{API_BASE_URL}/register/", data={
            "username": username,
            "password": password
        })

        if reg_response.status == 201:
            await update.message.reply_text("Account created! Logging you in...")
        elif reg_response.status == 400:
            await update.message.reply_text("Account already exists. Logging you in...")
        else:
            await update.message.reply_text("Something went wrong during registration.")
            return

        login_response = await session.post(f"{API_BASE_URL}/login/", data={
            "username": username,
            "password": password
        })

        if login_response.status == 200:
            access_token = (await login_response.json()).get("access")
            user_tokens[telegram_id] = access_token
            await update.message.reply_text("✅ Logged in successfully!")
        else:
            await update.message.reply_text("❌ Login failed.")

async def run_bot_async():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is not set."
        )

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    print("Telegram bot is running...")
    await app.run_polling()

def run_bot():
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already running (like inside Django dev server), schedule as task
            loop.create_task(run_bot_async())
        else:
            loop.run_until_complete(run_bot_async())
    except RuntimeError:
        # In case no loop exists
        asyncio.run(run_bot_async())
