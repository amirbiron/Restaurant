#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized version for Render deployment - Flask starts FIRST
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
from threading import Thread
import signal
import time

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

# Global bot status
bot_app = None
bot_running = False
bot_initializing = False
bot_error = None

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'running',
        'bot_active': bot_running,
        'bot_initializing': bot_initializing,
        'service': 'telegram-bot',
        'port': PORT
    }), 200

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    # Always return 200 to keep Render happy
    # Even if bot is not ready yet
    status = {
        'flask': 'healthy',
        'port': PORT,
        'bot_status': 'running' if bot_running else ('initializing' if bot_initializing else 'stopped'),
        'service': 'telegram-bot'
    }
    
    if bot_error:
        status['last_error'] = str(bot_error)
    
    return jsonify(status), 200

async def run_telegram_bot():
    """Run the telegram bot"""
    global bot_app, bot_running, bot_initializing, bot_error
    
    bot_initializing = True
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Telegram bot initialization attempt {retry_count + 1}/{max_retries}")
            
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
                bot_error = "BOT_TOKEN not configured"
                bot_initializing = False
                return
            
            logger.info("Creating Telegram bot application...")
            
            # Create application with timeouts
            bot_app = (
                Application.builder()
                .token(BOT_TOKEN)
                .connect_timeout(20.0)
                .read_timeout(20.0)
                .build()
            )

            # Remove webhook
            logger.info("Removing any existing webhooks...")
            try:
                await bot_app.bot.delete_webhook(drop_pending_updates=True)
            except Exception as e:
                logger.warning(f"Webhook removal warning: {e}")
            
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
            await bot_app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=None
            )
            
            bot_running = True
            bot_initializing = False
            bot_error = None
            logger.info("✅ Telegram bot is running successfully!")
            
            # Keep running
            await asyncio.Event().wait()
            
        except Exception as e:
            retry_count += 1
            bot_error = str(e)
            logger.error(f"Bot error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in 10 seconds...")
                await asyncio.sleep(10)
                
                # Cleanup
                if bot_app:
                    try:
                        await bot_app.updater.stop()
                        await bot_app.stop()
                        await bot_app.shutdown()
                    except:
                        pass
                    bot_app = None
            else:
                logger.error("Max retries reached. Bot stopped.")
                bot_running = False
                bot_initializing = False
                break
    
    # Final cleanup
    bot_initializing = False
    if bot_app:
        try:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except:
            pass

def run_bot_in_background():
    """Run bot in background with new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_telegram_bot())
    except Exception as e:
        logger.error(f"Bot thread critical error: {e}")
    finally:
        loop.close()

def start_flask_server():
    """Start Flask server in main thread"""
    logger.info(f"Starting Flask server on port {PORT}...")
    logger.info(f"Flask is binding to 0.0.0.0:{PORT}")
    
    # This runs Flask in the main thread
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping...")
    sys.exit(0)

def main():
    """Main function - Flask starts IMMEDIATELY"""
    logger.info("=" * 50)
    logger.info("Starting Service for Render Deployment")
    logger.info(f"Port: {PORT}")
    logger.info("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # CRITICAL: Start Flask FIRST in a separate thread
    # This ensures Render sees an open port immediately
    logger.info("Starting Flask server FIRST (for Render port detection)...")
    flask_thread = Thread(target=start_flask_server, daemon=False)
    flask_thread.start()
    
    # Give Flask a moment to bind to the port
    time.sleep(2)
    logger.info(f"Flask server should now be listening on port {PORT}")
    
    # Now check for BOT_TOKEN and start bot in background
    try:
        from bot import BOT_TOKEN
        if BOT_TOKEN:
            logger.info("✅ BOT_TOKEN found, starting Telegram bot in background...")
            bot_thread = Thread(target=run_bot_in_background, daemon=True)
            bot_thread.start()
        else:
            logger.warning("⚠️ BOT_TOKEN not set - running without Telegram bot")
            global bot_error
            bot_error = "BOT_TOKEN not configured"
    except ImportError as e:
        logger.error(f"Could not import bot module: {e}")
        bot_error = f"Import error: {e}"
    
    # Keep main thread alive by joining Flask thread
    flask_thread.join()

if __name__ == '__main__':
    main()