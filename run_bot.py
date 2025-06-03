#!/usr/bin/env python3
"""
Clean Trading Bot Entry Point
"""

import sys
import os
import time
import logging

# Add paths for all modules
current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(current_dir, 'src', 'core'))
sys.path.insert(0, os.path.join(current_dir, 'src', 'strategies'))
sys.path.insert(0, os.path.join(current_dir, 'src', 'utils'))
sys.path.insert(0, os.path.join(current_dir, 'config', 'trading'))

# Setup logging first
from bot_config import LOG_FILE, LOG_LEVEL

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s %(levelname)-8s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Now import the bot
from multi_pair_trading_bot import MultiPairTradingBot

def main():
    """Main entry point for the trading bot"""
    print("🚀 Starting Luno Trading Bot...")
    logging.info("🚀 Starting Luno Trading Bot...")
    
    try:
        bot = MultiPairTradingBot()
        logging.info("✅ Bot initialized successfully")
        bot.run()
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
        print("🛑 Bot stopped by user")
    except Exception as e:
        logging.error(f"❌ Bot failed: {e}")
        print(f"❌ Bot failed: {e}")
        raise

if __name__ == "__main__":
    main()
