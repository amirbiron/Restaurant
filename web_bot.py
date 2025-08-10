#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook version of the Telegram bot for Render deployment
"""

import os
import sys
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import asyncio
from threading import Thread

# Import the bot handlers from bot.py
from bot import (
    start, catalog, quick_qa, contact, appointment, human_support,
    button_handler, handle_text, handle_contact_process,
    DataManager, BOT_TOKEN
)

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for webhook
app = Flask(__name__)

# Get port from environment or use default
PORT = int(os.environ.get('PORT', 10000))

# Get Render URL
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')

# Telegram application
telegram_app = None

@app.route('/')
def index():
    """Health check endpoint"""
    return 'Bot is running!', 200

@app.route('/health')
def health():
    """Health check for Render"""
    return {'status': 'healthy', 'bot': 'running'}, 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    """Handle webhook updates from Telegram"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        
        # Process update in background
        asyncio.create_task(telegram_app.process_update(update))
        
        return 'OK', 200

async def setup_webhook():
    """Set up webhook for Telegram"""
    if not RENDER_EXTERNAL_URL:
        logger.error("RENDER_EXTERNAL_URL not set, cannot setup webhook")
        return False
    
    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    
    try:
        # Delete old webhook
        await telegram_app.bot.delete_webhook()
        
        # Set new webhook
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return False

def run_async_setup():
    """Run async setup in new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())

def main():
    """Main function to start the webhook server"""
    global telegram_app
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    
    # Create application
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("catalog", catalog))
    telegram_app.add_handler(CommandHandler("qa", quick_qa))
    telegram_app.add_handler(CommandHandler("contact", contact))
    telegram_app.add_handler(CommandHandler("appointment", appointment))
    telegram_app.add_handler(CommandHandler("human", human_support))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda u, c: handle_contact_process(u, c) if any(
            key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
        ) else handle_text(u, c)
    ))
    
    # Initialize application
    telegram_app.initialize()
    
    # Setup webhook in background
    if RENDER_EXTERNAL_URL:
        Thread(target=run_async_setup).start()
        logger.info("Using webhook mode")
    else:
        logger.warning("RENDER_EXTERNAL_URL not set, webhook not configured")
    
    # Start Flask server
    logger.info(f"Starting server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()