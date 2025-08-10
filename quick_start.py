#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick start version - Flask opens port IMMEDIATELY for Render
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
from threading import Thread
import time

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000))

# Bot status
bot_status = {'running': False, 'error': None}

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'bot': bot_status['running'],
        'port': PORT
    }), 200

@app.route('/health')
def health():
    # ALWAYS return 200 for Render
    return jsonify({
        'status': 'healthy',
        'bot': bot_status['running'],
        'error': bot_status['error']
    }), 200

def run_bot():
    """Run the Telegram bot in background"""
    async def bot_main():
        try:
            logger.info("Starting Telegram bot...")
            
            # Import bot components
            from bot import BOT_TOKEN
            if not BOT_TOKEN:
                logger.error("No BOT_TOKEN!")
                bot_status['error'] = 'No token'
                return
                
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
            from bot import (
                start, button_handler, handle_text, handle_contact_process,
                admin_command, export_leads
            )
            
            # Create bot
            application = Application.builder().token(BOT_TOKEN).build()
            
            # Remove webhook
            await application.bot.delete_webhook(drop_pending_updates=True)
            
            # Add handlers
            application.add_handler(CommandHandler('start', start))
            application.add_handler(CommandHandler('admin', admin_command))
            application.add_handler(CommandHandler('export_leads', export_leads))
            application.add_handler(CallbackQueryHandler(button_handler))
            application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                lambda u, c: handle_contact_process(u, c) if any(
                    key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
                ) else handle_text(u, c)
            ))
            
            # Start bot
            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)
            
            bot_status['running'] = True
            logger.info("✅ Bot is running!")
            
            # Keep running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            bot_status['error'] = str(e)
    
    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_main())

if __name__ == '__main__':
    # STEP 1: Start Flask IMMEDIATELY (this opens the port for Render)
    logger.info(f"Opening port {PORT} for Render...")
    flask_thread = Thread(
        target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False),
        daemon=True
    )
    flask_thread.start()
    
    # STEP 2: Wait a moment for Flask to bind
    time.sleep(1)
    logger.info(f"✅ Port {PORT} is now open!")
    
    # STEP 3: Start bot in background
    logger.info("Starting Telegram bot in background...")
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Keep running
    while True:
        time.sleep(60)