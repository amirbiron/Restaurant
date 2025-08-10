#!/usr/bin/env python3
"""
Main entry point for the Telegram Business Bot
This file is used by Render for deployment
"""

import sys
import os

# Import and run the bot
if __name__ == "__main__":
    try:
        from bot import *
        # The bot.py file should handle the bot initialization and running
        # when imported as the main module
    except ImportError as e:
        print(f"Error importing bot module: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running bot: {e}", file=sys.stderr)
        sys.exit(1)