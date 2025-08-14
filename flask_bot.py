#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask-only version for Render - with singleton pattern and conflict handling
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify
import threading
import time
import signal

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

# Bot status and singleton lock
bot_status = {"running": False, "error": None, "last_start_attempt": None}
bot_lock = threading.Lock()
bot_instance = None
bot_thread = None

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
    # Always return 200 for Render, include status details in payload
    status_payload = {'service': 'telegram-bot', 'port': PORT}
    if bot_status['running']:
        status_payload['status'] = 'healthy'
        return jsonify(status_payload), 200
    elif bot_status['error']:
        status_payload['status'] = 'error'
        status_payload['error'] = str(bot_status['error'])
        return jsonify(status_payload), 200
    else:
        status_payload['status'] = 'starting'
        return jsonify(status_payload), 200

async def cleanup_bot(telegram_app):
    """Properly cleanup bot resources"""
    if telegram_app:
        try:
            logger.info("Stopping bot updater...")
            await telegram_app.updater.stop()
            logger.info("Stopping bot application...")
            await telegram_app.stop()
            logger.info("Shutting down bot...")
            await telegram_app.shutdown()
            logger.info("Bot cleanup completed")
        except Exception as e:
            logger.error(f"Error during bot cleanup: {e}")

def run_bot_async():
    """Run bot in separate thread with event loop and retry on conflict"""
    global bot_instance, bot_status
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_bot_with_retry():
        global bot_instance, bot_status
        
        max_retries = 5
        retry_count = 0
        base_delay = 5
        
        while retry_count < max_retries:
            bot_status['error'] = None
            bot_status['last_start_attempt'] = time.time()
            
            try:
                from bot import BOT_TOKEN
                if not BOT_TOKEN:
                    bot_status['error'] = 'BOT_TOKEN not set'
                    logger.error("BOT_TOKEN not set")
                    return
                
                telegram_app = None
                
                # Calculate exponential backoff
                if retry_count > 0:
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Waiting {delay} seconds before retry {retry_count + 1}/{max_retries}...")
                    await asyncio.sleep(delay)
                
                logger.info(f"Creating bot application (attempt {retry_count + 1}/{max_retries})...")
                from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
                from bot import (
                    start, button_handler, handle_text, handle_contact_process,
                    admin_command, export_leads, export_appointments
                )

                # Build application with proper configuration
                telegram_app = (
                    Application.builder()
                    .token(BOT_TOKEN)
                    .connect_timeout(30.0)
                    .read_timeout(30.0)
                    .write_timeout(30.0)
                    .pool_timeout(30.0)
                    .get_updates_read_timeout(20.0)
                    .get_updates_connect_timeout(20.0)
                    .get_updates_pool_timeout(20.0)
                    .build()
                )

                # Delete webhook with retry
                logger.info("Removing any existing webhooks...")
                webhook_deleted = False
                for i in range(3):
                    try:
                        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
                        webhook_deleted = True
                        logger.info("Webhook removed successfully")
                        break
                    except Exception as e:
                        logger.warning(f"Webhook removal attempt {i+1} failed: {e}")
                        if i < 2:
                            await asyncio.sleep(2)
                
                if not webhook_deleted:
                    logger.warning("Could not remove webhook, continuing anyway...")

                # Add handlers
                telegram_app.add_handler(CommandHandler('start', start))
                telegram_app.add_handler(CommandHandler('admin', admin_command))
                telegram_app.add_handler(CommandHandler('export_leads', export_leads))
                telegram_app.add_handler(CommandHandler('export_appointments', export_appointments))
                telegram_app.add_handler(CallbackQueryHandler(button_handler))
                telegram_app.add_handler(MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    lambda u, c: handle_contact_process(u, c) if any(
                        key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
                    ) else handle_text(u, c)
                ))

                # Initialize bot
                logger.info("Initializing bot...")
                await telegram_app.initialize()
                await telegram_app.start()
                
                # Start polling with conflict handling
                logger.info("Starting polling with conflict protection...")
                try:
                    await telegram_app.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=None,
                        error_callback=lambda update, context: logger.error(f"Polling error: {context.error}")
                    )
                except Exception as poll_error:
                    if "Conflict" in str(poll_error):
                        logger.error(f"Conflict detected: {poll_error}")
                        # Wait longer before retry on conflict
                        await asyncio.sleep(30)
                        retry_count += 1
                        await cleanup_bot(telegram_app)
                        continue
                    else:
                        raise

                bot_instance = telegram_app
                bot_status['running'] = True
                bot_status['error'] = None
                logger.info("✅ Bot started successfully!")

                # Keep running until canceled
                await asyncio.Event().wait()

            except asyncio.CancelledError:
                logger.info("Bot task cancelled")
                break
            except Exception as e:
                bot_status['running'] = False
                bot_status['error'] = str(e)
                logger.error(f"Bot error: {e}")
                
                # Check if it's a conflict error
                if "Conflict" in str(e) or "terminated by other getUpdates" in str(e):
                    logger.error("Conflict error detected - another instance may be running")
                    retry_count += 1
                    
                    # Cleanup before retry
                    if telegram_app:
                        await cleanup_bot(telegram_app)
                        telegram_app = None
                    
                    # Wait longer for conflicts
                    await asyncio.sleep(30)
                else:
                    # For other errors, use standard retry
                    retry_count += 1
                    if telegram_app:
                        await cleanup_bot(telegram_app)
                        telegram_app = None

            finally:
                if telegram_app and retry_count >= max_retries:
                    await cleanup_bot(telegram_app)
                    bot_instance = None
        
        if retry_count >= max_retries:
            logger.error(f"Failed to start bot after {max_retries} attempts")
            bot_status['error'] = f"Failed after {max_retries} attempts"

    try:
        loop.run_until_complete(start_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("Bot thread interrupted")
    finally:
        loop.close()

def start_bot_if_needed():
    """Start bot thread only if not already running"""
    global bot_thread
    
    with bot_lock:
        if bot_thread is None or not bot_thread.is_alive():
            logger.info("Starting new bot thread...")
            bot_thread = threading.Thread(target=run_bot_async, daemon=True)
            bot_thread.start()
            return True
        else:
            logger.info("Bot thread already running")
            return False

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if bot_instance:
        # Try to stop the bot gracefully
        try:
            asyncio.run(cleanup_bot(bot_instance))
        except:
            pass
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Initialize bot when module loads (for gunicorn workers)
# This ensures only one instance per worker
with app.app_context():
    logger.info("Initializing bot on module load...")
    start_bot_if_needed()

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {PORT}")
    # Start bot before running Flask in development
    start_bot_if_needed()
    app.run(host='0.0.0.0', port=PORT, debug=False)