#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask-only version for Render - simplest approach
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
import threading

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000))

# Bot status
bot_status = {"running": False, "error": None}

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'online',
        'bot_running': bot_status['running'],
        'service': 'telegram-bot',
        'port': PORT
    }), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    if bot_status['running']:
        return jsonify({'status': 'healthy'}), 200
    elif bot_status['error']:
        return jsonify({'status': 'error', 'error': str(bot_status['error'])}), 503
    else:
        return jsonify({'status': 'starting'}), 503

def run_bot_async():
    """Run bot in separate thread with event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def start_bot():
        global bot_status
        try:
            logger.info("Importing bot modules...")
            from bot import BOT_TOKEN
            
            if not BOT_TOKEN:
                raise ValueError("BOT_TOKEN not set")
            
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
            from bot import (
                start, button_handler, handle_text, handle_contact_process,
                admin_command, export_leads
            )
            
            logger.info("Creating bot application...")
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Add handlers
            app.add_handler(CommandHandler('start', start))
            app.add_handler(CommandHandler('admin', admin_command))
            app.add_handler(CommandHandler('export_leads', export_leads))
            app.add_handler(CallbackQueryHandler(button_handler))
            app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda u, c: handle_contact_process(u, c) if any(
                    key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
                ) else handle_text(u, c)
            ))
            
            # Start bot
            logger.info("Initializing bot...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            
            bot_status['running'] = True
            logger.info("✅ Bot started successfully!")
            
            # Keep running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            bot_status['error'] = str(e)
            bot_status['running'] = False
    
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

# Start bot in background when module loads
logger.info("Starting bot thread...")
bot_thread = threading.Thread(target=run_bot_async, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)