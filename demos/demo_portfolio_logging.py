#!/usr/bin/env python3
"""
Simple test to demonstrate enhanced portfolio logging
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luno_api import LunoAPI
from portfolio_manager import PortfolioManager
from trading_pair_discovery import TradingPairDiscovery
from bot_config import TRADING_ASSETS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simple format to see the enhanced output clearly
)

def main():
    """Demonstrate enhanced portfolio logging"""
    print("🚀 Enhanced Portfolio Logging Demo")
    print("="*50)
    
    # Initialize components
    luno = LunoAPI()
    portfolio_manager = PortfolioManager(luno)
    discovery = TradingPairDiscovery(luno)
    
    # Discover valid pairs
    valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS)
    print(f"Using {len(valid_pairs)} discovered trading pairs\n")
    
    # Show enhanced portfolio logging
    portfolio_manager.log_portfolio_status(list(valid_pairs.keys()))

if __name__ == "__main__":
    main()
