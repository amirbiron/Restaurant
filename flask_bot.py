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

def run_bot_async():
    """Run bot in separate thread with event loop and retry on conflict"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_bot_with_retry():
        global bot_status
        retry_delay_seconds = 10
        while True:
            bot_status['error'] = None
            from bot import BOT_TOKEN
            if not BOT_TOKEN:
                bot_status['error'] = 'BOT_TOKEN not set'
                logger.error("BOT_TOKEN not set")
                await asyncio.sleep(retry_delay_seconds)
                continue

            telegram_app = None
            try:
                logger.info("Creating bot application...")
                from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
                from bot import (
                    start, button_handler, handle_text, handle_contact_process,
                    admin_command, export_leads
                )

                telegram_app = Application.builder().token(BOT_TOKEN).build()

                # Ensure webhook is removed before starting polling
                await telegram_app.bot.delete_webhook(drop_pending_updates=True)

                # Add handlers
                telegram_app.add_handler(CommandHandler('start', start))
                telegram_app.add_handler(CommandHandler('admin', admin_command))
                telegram_app.add_handler(CommandHandler('export_leads', export_leads))
                telegram_app.add_handler(CallbackQueryHandler(button_handler))
                telegram_app.add_handler(MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    lambda u, c: handle_contact_process(u, c) if any(
                        key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']
                    ) else handle_text(u, c)
                ))

                # Start bot
                logger.info("Initializing bot...")
                await telegram_app.initialize()
                await telegram_app.start()
                logger.info("Starting polling...")
                await telegram_app.updater.start_polling(drop_pending_updates=True)

                bot_status['running'] = True
                logger.info("✅ Bot started successfully!")

                # Keep running until canceled
                await asyncio.Event().wait()

            except Exception as e:
                bot_status['running'] = False
                bot_status['error'] = str(e)
                logger.error(f"Bot error: {e}")
                # Conflict happens if another getUpdates is running elsewhere. Retry.
                await asyncio.sleep(retry_delay_seconds)

            finally:
                if telegram_app:
                    try:
                        await telegram_app.updater.stop()
                        await telegram_app.stop()
                        await telegram_app.shutdown()
                    except Exception:
                        pass

    try:
        loop.run_until_complete(start_bot_with_retry())
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