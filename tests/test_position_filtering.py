#!/usr/bin/env python3
"""
Test script to verify the position-based pair filtering functionality
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luno_api import LunoAPI
from portfolio_manager import PortfolioManager
from trading_pair_discovery import TradingPairDiscovery
from multi_pair_trading_bot import MultiPairTradingBot
from bot_config import TRADING_ASSETS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_position_based_filtering():
    """Test that pairs are filtered based on actual holdings"""
    print("🧪 Testing Position-Based Pair Filtering...")
    
    try:
        # Initialize components
        luno = LunoAPI()
        portfolio_manager = PortfolioManager(luno)
        discovery = TradingPairDiscovery(luno)
        print("✅ Components initialized")
        
        # Get current balances to understand what we have
        print("\n📊 Current Portfolio Status:")
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS)
        current_balances = portfolio_manager.get_all_balances(list(valid_pairs.keys()))
        
        print(f"Current holdings: {current_balances}")
        print(f"Total discovered pairs: {len(valid_pairs)}")
        
        # Initialize the trading bot to test filtering
        print("\n🔍 Testing Pair Filtering Logic:")
        bot = MultiPairTradingBot()
        
        # The evaluate_trading_pairs method now includes position-based filtering
        evaluated_pairs = bot.evaluate_trading_pairs()
        
        print(f"\n📈 Pair Evaluation Results:")
        print(f"Pairs after filtering: {len(evaluated_pairs)}")
        
        if evaluated_pairs:
            print("\nTop pairs with position filtering:")
            for i, (pair, score) in enumerate(evaluated_pairs[:10]):
                base, quote = bot.parse_trading_pair(pair)
                has_base = current_balances.get(base, 0) > 0
                has_quote = current_balances.get(quote, 0) > 0
                
                status = ""
                if has_base and has_quote:
                    status = f"(✓ {base}, ✓ {quote})"
                elif has_base:
                    status = f"(✓ {base})"
                elif has_quote:
                    status = f"(✓ {quote})"
                else:
                    status = "(⚠️ No holdings - should be filtered!)"
                
                print(f"  {i+1:2}. {pair:10} - Score: {score:6.2f} {status}")
        
        # Verify filtering worked correctly
        print(f"\n✅ Verification:")
        filtered_out_count = 0
        for pair in valid_pairs.keys():
            base, quote = bot.parse_trading_pair(pair)
            has_base = current_balances.get(base, 0) > 0
            has_quote = current_balances.get(quote, 0) > 0
            
            is_in_results = any(p[0] == pair for p in evaluated_pairs)
            
            if not (has_base or has_quote):
                filtered_out_count += 1
                if is_in_results:
                    print(f"❌ ERROR: {pair} should have been filtered out (no holdings in {base} or {quote})")
                    return False
            else:
                if not is_in_results:
                    print(f"⚠️  WARNING: {pair} has holdings but was filtered out")
        
        print(f"✅ Filtering working correctly!")
        print(f"   - {len(evaluated_pairs)} pairs have at least one holding")
        print(f"   - {filtered_out_count} pairs correctly filtered out (no holdings)")
        print(f"   - Total pairs checked: {len(valid_pairs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_position_based_filtering()
    if success:
        print("\n🎉 Position-based pair filtering test passed!")
    else:
        print("\n💥 Position-based pair filtering test failed!")
        sys.exit(1)
