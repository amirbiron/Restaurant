#!/usr/bin/env python3
"""
Main entry point for the Telegram Business Bot
This file is used by Render for deployment
"""

import sys
import os
import asyncio
import logging

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main async function to run the bot"""
    try:
        # Import bot after environment is set up
        from bot import main as bot_main
        
        logger.info("Starting Telegram bot...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Environment: {os.environ.get('RENDER', 'local')}")
        
        # Run the bot
        bot_main()
        
    except ImportError as e:
        logger.error(f"Error importing bot module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(f"Full error: {e.__class__.__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check if BOT_TOKEN is set
        if not os.environ.get('BOT_TOKEN'):
            logger.error("ERROR: BOT_TOKEN environment variable is not set!")
            logger.error("Please set BOT_TOKEN in Render dashboard under Environment Variables")
            sys.exit(1)
        
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)