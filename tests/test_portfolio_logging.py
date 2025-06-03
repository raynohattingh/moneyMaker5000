#!/usr/bin/env python3
"""
Test script to verify enhanced portfolio logging functionality
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

# Configure logging to see the output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_portfolio_logging():
    """Test the enhanced portfolio logging with dynamic pair discovery"""
    print("🧪 Testing Enhanced Portfolio Logging...")
    
    try:
        # Initialize Luno API and portfolio manager
        luno = LunoAPI()
        portfolio_manager = PortfolioManager(luno)
        print("✅ Portfolio manager initialized")
        
        # Initialize pair discovery
        discovery = TradingPairDiscovery(luno)
        print("✅ Trading pair discovery initialized")
        
        # Discover valid pairs using our trading assets
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS)
        print(f"✅ Discovered {len(valid_pairs)} valid trading pairs")
        
        # Test portfolio summary
        print("\n📊 Testing portfolio summary generation...")
        summary = portfolio_manager.get_portfolio_summary(list(valid_pairs.keys()))
        
        if summary:
            print("✅ Portfolio summary generated successfully")
            print(f"   Keys: {list(summary.keys())}")
            print(f"   Total value: {summary.get('total_value_zar', 0):.2f} ZAR")
            print(f"   Holdings actual: {summary.get('holdings_actual', {})}")
            print(f"   Holdings ZAR: {summary.get('holdings_zar', {})}")
        else:
            print("❌ Failed to generate portfolio summary")
            return False
        
        # Test enhanced logging
        print("\n📝 Testing enhanced portfolio logging...")
        print("=" * 60)
        portfolio_manager.log_portfolio_status(list(valid_pairs.keys()))
        print("=" * 60)
        
        print("✅ Portfolio logging test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_portfolio_logging()
    if success:
        print("\n🎉 All tests passed! Enhanced portfolio logging is working correctly.")
    else:
        print("\n💥 Tests failed! Please check the errors above.")
        sys.exit(1)
