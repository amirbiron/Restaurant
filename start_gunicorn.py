#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn startup script with better error handling
"""

import os
import sys
import subprocess

def main():
    port = os.environ.get('PORT', '10000')
    
    print(f"Starting Telegram Bot Service...")
    print(f"Port: {port}")
    print(f"Workers: 1 (singleton mode)")
    
    # Try different module configurations
    module_configs = [
        "app:application",
        "app:app",
        "flask_bot:app",
    ]
    
    gunicorn_cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "--workers", "1",
        "--threads", "1",
        "--timeout", "120",
        "--log-level", "info",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--preload",
        "--max-requests", "1000",
        "--max-requests-jitter", "50",
        "--worker-class", "sync"
    ]
    
    # Try each module configuration
    for module_config in module_configs:
        try:
            print(f"Trying to start with module: {module_config}")
            cmd = gunicorn_cmd + [module_config]
            subprocess.run(cmd, check=True)
            break  # If successful, exit
        except subprocess.CalledProcessError as e:
            print(f"Failed to start with {module_config}: {e}")
            if module_config == module_configs[-1]:
                print("All module configurations failed!")
                sys.exit(1)
            continue

if __name__ == "__main__":
    main()