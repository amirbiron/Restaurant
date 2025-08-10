#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook version for Render - Avoids polling conflicts completely
"""

import os
import sys
import logging
import asyncio
from flask import Flask, request, jsonify
import hashlib
import hmac

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000))

# Get webhook URL from environment or construct it
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
WEBHOOK_PATH = '/telegram-webhook'
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else None

# Bot application instance
bot_app = None
bot_initialized = False

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'online',
        'mode': 'webhook',
        'bot_initialized': bot_initialized,
        'service': 'telegram-bot',
        'port': PORT
    }), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'webhook',
        'bot_initialized': bot_initialized,
        'webhook_url': WEBHOOK_URL if WEBHOOK_URL else 'not_configured'
    }), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
async def telegram_webhook():
    """Handle incoming Telegram updates via webhook"""
    global bot_app
    
    if not bot_app:
        logger.error("Bot not initialized")
        return jsonify({'error': 'Bot not initialized'}), 503
    
    try:
        # Get update data
        update_data = request.get_json(force=True)
        
        # Process update
        from telegram import Update
        update = Update.de_json(update_data, bot_app.bot)
        
        # Process update asynchronously
        await bot_app.process_update(update)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return jsonify({'error': str(e)}), 500

async def setup_webhook():
    """Setup webhook for Telegram bot"""
    global bot_app, bot_initialized
    
    try:
        from bot import BOT_TOKEN
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not set")
            return False
        
        if not WEBHOOK_URL:
            logger.error("RENDER_EXTERNAL_URL not set - cannot use webhook mode")
            logger.info("Set RENDER_EXTERNAL_URL in Render environment variables")
            return False
        
        logger.info("Setting up Telegram bot with webhook...")
        
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
        from bot import (
            start, button_handler, handle_text, handle_contact_process,
            admin_command, export_leads
        )
        
        # Create application
        bot_app = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )
        
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
        
        # Initialize application
        await bot_app.initialize()
        await bot_app.start()
        
        # Set webhook
        logger.info(f"Setting webhook to: {WEBHOOK_URL}")
        await bot_app.bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        
        # Verify webhook
        webhook_info = await bot_app.bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        
        bot_initialized = True
        logger.info("✅ Bot initialized with webhook successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        bot_initialized = False
        return False

@app.before_first_request
def initialize_bot():
    """Initialize bot on first request"""
    if not bot_initialized:
        # Run async setup in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(setup_webhook())
        finally:
            loop.close()

if __name__ == '__main__':
    logger.info(f"Starting Flask server with webhook mode on port {PORT}")
    logger.info(f"Webhook URL will be: {WEBHOOK_URL}")
    
    # Initialize bot before starting server in development
    if not bot_initialized:
        asyncio.run(setup_webhook())
    
    app.run(host='0.0.0.0', port=PORT, debug=False)