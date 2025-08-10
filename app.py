#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main application entry point for Gunicorn
This file serves as the WSGI entry point for the Flask application
"""

# Import the Flask app from flask_bot
from flask_bot import app

# Expose the app for Gunicorn
application = app

if __name__ == "__main__":
    # For local development
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)