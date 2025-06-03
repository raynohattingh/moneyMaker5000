#!/usr/bin/env python3
"""
Quick test to verify pair rotation functionality
"""

from unittest.mock import Mock, patch
import logging

# Setup minimal logging
logging.basicConfig(level=logging.ERROR)  # Reduce noise

def test_rotation_quickly():
    """Quick test of rotation functionality"""
    print("🧪 Quick rotation test...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Mock minimal responses
        mock_luno.return_value.get_tickers.return_value = {
            'XBTZAR': {'ask': '950000', 'bid': '949000', 'volume': '100'},
            'ETHZAR': {'ask': '60000', 'bid': '59900', 'volume': '50'},
            'USDTZAR': {'ask': '18.50', 'bid': '18.45', 'volume': '1000'},
            'XRPZAR': {'ask': '12.00', 'bid': '11.95', 'volume': '200'},
            'LTCZAR': {'ask': '1500', 'bid': '1495', 'volume': '150'},
            'ADAZAR': {'ask': '8.00', 'bid': '7.95', 'volume': '80'},
        }
        
        mock_luno.return_value.get_orderbook_top.return_value = {
            'asks': [{'price': '950000', 'volume': '1'}],
            'bids': [{'price': '949000', 'volume': '1'}]
        }
        
        # Import and test
        from multi_pair_trading_bot import MultiPairTradingBot
        
        bot = MultiPairTradingBot()
        
        print(f"✅ Bot initialized with {len(bot.all_evaluated_pairs)} pairs")
        print(f"   Active pairs: {bot.active_pairs}")
        print(f"   Rotation index: {bot.rotation_index}")
        print(f"   Cycles since last trade: {bot.cycles_since_last_trade}")
        print(f"   Max cycles without trade: {bot.max_cycles_without_trade}")
        
        # Test rotation if possible
        if len(bot.all_evaluated_pairs) > 3:
            old_pairs = bot.active_pairs.copy()
            bot.advance_pair_rotation()
            print(f"   After rotation: {bot.active_pairs}")
            print(f"   Pairs changed: {old_pairs != bot.active_pairs}")
            
        print("✅ Quick test completed successfully!")

if __name__ == "__main__":
    test_rotation_quickly()
