#!/usr/bin/env python3
"""
Keep-Alive Script for Render Free Tier
=====================================

This script pings your deployed health endpoint to prevent the service from sleeping.
Useful for Render's free tier which sleeps after 15 minutes of inactivity.

Usage:
    python keep_alive.py

Environment Variables:
    BACKEND_URL: Your deployed backend URL (e.g., https://your-service.onrender.com)
    PING_INTERVAL: Interval between pings in seconds (default: 300 = 5 minutes)

Note: This script is optional and should only be used if you need your service
to stay awake. Consider the environmental impact of keeping services running
unnecessarily.
"""

import os
import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'https://your-backend-service.onrender.com')
PING_INTERVAL = int(os.getenv('PING_INTERVAL', 300))  # 5 minutes default
HEALTH_ENDPOINT = f"{BACKEND_URL}/health/"

def ping_service():
    """Ping the health endpoint to keep the service awake."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=30)
        if response.status_code == 200:
            logger.info(f"✅ Service is awake - Status: {response.status_code}")
            return True
        else:
            logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error("⏰ Request timed out - service might be sleeping")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return False

def main():
    """Main keep-alive loop."""
    logger.info(f"🚀 Starting keep-alive service for {BACKEND_URL}")
    logger.info(f"⏱️ Ping interval: {PING_INTERVAL} seconds")
    logger.info(f"🎯 Health endpoint: {HEALTH_ENDPOINT}")
    
    while True:
        try:
            logger.info(f"📡 Pinging service at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            ping_service()
            
            logger.info(f"😴 Sleeping for {PING_INTERVAL} seconds...")
            time.sleep(PING_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Keep-alive service stopped by user")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            logger.info(f"🔄 Retrying in {PING_INTERVAL} seconds...")
            time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    # Validate configuration
    if BACKEND_URL == 'https://your-backend-service.onrender.com':
        logger.error("❌ Please set the BACKEND_URL environment variable to your actual service URL")
        logger.info("Example: export BACKEND_URL=https://your-service.onrender.com")
        exit(1)
    
    main()