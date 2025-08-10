#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized version for Render deployment
Combines Flask server and Telegram bot using asyncio
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
from threading import Thread
import signal

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000))

# Global bot application
bot_app = None
bot_running = False

@app.route('/')
def index():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return jsonify({
        'status': 'running',
        'bot_active': bot_running,
        'service': 'telegram-bot'
    }), 200

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    logger.info("Health check endpoint accessed")
    if bot_running:
        return jsonify({
            'status': 'healthy',
            'bot': 'running',
            'service': 'telegram-bot'
        }), 200
    else:
        return jsonify({
            'status': 'starting',
            'bot': 'initializing',
            'service': 'telegram-bot'
        }), 503

async def run_telegram_bot():
    """Run the telegram bot"""
    global bot_app, bot_running
    
    try:
        # Import bot components
        from bot import BOT_TOKEN
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
        
        # Import handlers
        from bot import (
            start, button_handler, handle_text, handle_contact_process,
            admin_command, export_leads
        )
        
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN is not set!")
            return
        
        logger.info("Initializing Telegram bot...")
        
        # Create application
        bot_app = Application.builder().token(BOT_TOKEN).build()

        # Ensure webhook is removed before starting polling
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        
        # Add handlers
        bot_app.add_handler(CommandHandler('start', start))
        bot_app.add_handler(CommandHandler('admin', admin_command))
        bot_app.add_handler(CommandHandler('export_leads', export_leads))
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        bot_app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            lambda u, c: handle_contact_process(u, c) if any(
                key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
            ) else handle_text(u, c)
        ))
        
        # Initialize and start
        await bot_app.initialize()
        await bot_app.start()
        
        logger.info("Starting bot polling...")
        await bot_app.updater.start_polling(drop_pending_updates=True)
        
        bot_running = True
        logger.info("✅ Telegram bot is running successfully!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()
        bot_running = False
    finally:
        if bot_app:
            try:
                await bot_app.updater.stop()
                await bot_app.stop()
                await bot_app.shutdown()
            except:
                pass

def run_bot_thread():
    """Run bot in thread with its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_telegram_bot())
    except Exception as e:
        logger.error(f"Bot thread error: {e}")
    finally:
        loop.close()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping...")
    sys.exit(0)

def main():
    """Main function"""
    logger.info("=" * 50)
    logger.info("Starting Telegram Bot Service for Render")
    logger.info(f"Port: {PORT}")
    logger.info("=" * 50)
    
    # Check BOT_TOKEN
    from bot import BOT_TOKEN
    if not BOT_TOKEN:
        logger.error("❌ ERROR: BOT_TOKEN is not set!")
        logger.error("Please set BOT_TOKEN in Render Environment Variables")
        sys.exit(1)
    
    logger.info("✅ BOT_TOKEN found")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot in background thread
    logger.info("Starting Telegram bot thread...")
    bot_thread = Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # Wait a bit for bot to initialize
    import time
    time.sleep(3)
    
    # Start Flask server
    logger.info(f"Starting Flask server on port {PORT}...")
    logger.info(f"Health check URL: http://0.0.0.0:{PORT}/health")
    
    try:
        # Run Flask with explicit settings
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Flask error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()