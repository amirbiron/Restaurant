#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized version for Render deployment
Combines Flask server and Telegram bot using asyncio with enhanced error handling
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
from threading import Thread
import signal
import time
from typing import Optional

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
bot_error_count = 0
last_error_time = None

@app.route('/')
def index():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return jsonify({
        'status': 'running',
        'bot_active': bot_running,
        'service': 'telegram-bot',
        'error_count': bot_error_count
    }), 200

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    logger.info("Health check endpoint accessed")
    if bot_running:
        return jsonify({
            'status': 'healthy',
            'bot': 'running',
            'service': 'telegram-bot',
            'error_count': bot_error_count
        }), 200
    else:
        return jsonify({
            'status': 'starting',
            'bot': 'initializing',
            'service': 'telegram-bot',
            'error_count': bot_error_count
        }), 503

async def run_telegram_bot():
    """Run the telegram bot with enhanced error handling and retry logic"""
    global bot_app, bot_running, bot_error_count, last_error_time
    
    max_retries = 5
    retry_count = 0
    base_delay = 5  # Start with 5 seconds delay
    
    while retry_count < max_retries:
        try:
            # Import bot components
            from bot import BOT_TOKEN
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
            from telegram.error import NetworkError, TimedOut, RetryAfter
            
            # Import handlers
            from bot import (
                start, button_handler, handle_text, handle_contact_process,
                admin_command, export_leads
            )
            
            if not BOT_TOKEN:
                logger.error("BOT_TOKEN is not set!")
                return
            
            logger.info(f"Initializing Telegram bot (attempt {retry_count + 1}/{max_retries})...")
            
            # Create application with custom settings for better resilience
            bot_app = (
                Application.builder()
                .token(BOT_TOKEN)
                .connect_timeout(30.0)  # Increase connection timeout
                .read_timeout(30.0)     # Increase read timeout
                .write_timeout(30.0)    # Increase write timeout
                .pool_timeout(30.0)     # Increase pool timeout
                .build()
            )

            # Ensure webhook is removed before starting polling
            logger.info("Removing any existing webhooks...")
            try:
                await bot_app.bot.delete_webhook(drop_pending_updates=True)
                logger.info("Webhook removed successfully")
            except Exception as e:
                logger.warning(f"Could not remove webhook: {e}")
            
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
            
            # Add error handler
            async def error_handler(update, context):
                """Handle errors in the bot"""
                global bot_error_count, last_error_time
                bot_error_count += 1
                last_error_time = time.time()
                
                error = context.error
                logger.error(f"Bot error occurred: {type(error).__name__}: {error}")
                
                if isinstance(error, NetworkError):
                    logger.warning("Network error detected, will retry...")
                elif isinstance(error, TimedOut):
                    logger.warning("Request timed out, will retry...")
                elif isinstance(error, RetryAfter):
                    logger.warning(f"Rate limited, retry after {error.retry_after} seconds")
                    await asyncio.sleep(error.retry_after)
                else:
                    import traceback
                    logger.error(f"Unexpected error: {traceback.format_exc()}")
            
            bot_app.add_error_handler(error_handler)
            
            # Initialize and start
            await bot_app.initialize()
            await bot_app.start()
            
            logger.info("Starting bot polling with enhanced settings...")
            
            # Start polling with custom parameters for better resilience
            await bot_app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=None,  # Receive all update types
                poll_interval=1.0,      # Check for updates every second
                timeout=30,             # Timeout for long polling
                bootstrap_retries=3,    # Retry bootstrap 3 times
                read_timeout=30.0,      # Read timeout
                write_timeout=30.0,     # Write timeout
                connect_timeout=30.0,   # Connect timeout
                pool_timeout=30.0       # Pool timeout
            )
            
            bot_running = True
            retry_count = 0  # Reset retry count on successful start
            bot_error_count = 0  # Reset error count
            logger.info("✅ Telegram bot is running successfully!")
            
            # Keep running
            await asyncio.Event().wait()
            
        except Exception as e:
            bot_running = False
            retry_count += 1
            bot_error_count += 1
            last_error_time = time.time()
            
            logger.error(f"Bot error (attempt {retry_count}/{max_retries}): {e}")
            import traceback
            traceback.print_exc()
            
            if retry_count < max_retries:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** retry_count), 60) + (time.time() % 5)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
                
                # Clean up the previous bot instance if it exists
                if bot_app:
                    try:
                        logger.info("Cleaning up previous bot instance...")
                        await bot_app.updater.stop()
                        await bot_app.stop()
                        await bot_app.shutdown()
                    except Exception as cleanup_error:
                        logger.warning(f"Error during cleanup: {cleanup_error}")
                    finally:
                        bot_app = None
            else:
                logger.error(f"Max retries ({max_retries}) reached. Bot will not restart automatically.")
                break
    
    # Final cleanup
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