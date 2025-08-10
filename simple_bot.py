#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple polling version for Render - more reliable
"""

import os
import sys
import logging
import signal
from flask import Flask
from threading import Thread
import time

# Import bot functionality
from bot import main as bot_main, BOT_TOKEN

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000))

# Global flag for shutdown
shutdown_flag = False

@app.route('/')
def index():
    """Root endpoint"""
    return 'Telegram Bot is running!', 200

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return {'status': 'healthy', 'service': 'telegram-bot'}, 200

def run_bot():
    """Run the bot in a separate thread"""
    global shutdown_flag
    
    try:
        logger.info("Starting Telegram bot in polling mode...")
        # Run the original bot main function
        bot_main()
    except Exception as e:
        logger.error(f"Bot error: {e}")
        shutdown_flag = True

def run_flask():
    """Run Flask server for health checks"""
    logger.info(f"Starting health check server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info("Received shutdown signal, stopping bot...")
    shutdown_flag = True
    sys.exit(0)

def main():
    """Main function"""
    # Check for BOT_TOKEN
    if not BOT_TOKEN:
        logger.error("ERROR: BOT_TOKEN environment variable is not set!")
        logger.error("Please add BOT_TOKEN in Render dashboard:")
        logger.error("1. Go to your service in Render")
        logger.error("2. Click on 'Environment' tab")
        logger.error("3. Add BOT_TOKEN with your bot token from BotFather")
        sys.exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot in background thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(2)
    
    # Run Flask server (blocks)
    run_flask()

if __name__ == '__main__':
    main()