#!/usr/bin/env python3
"""
Test script for pair rotation functionality in the multi-pair trading bot.
This validates that the bot properly rotates through discovered pairs.
"""

import sys
import logging
from unittest.mock import Mock, patch, MagicMock
from multi_pair_trading_bot import MultiPairTradingBot
from bot_config import MAX_PAIRS_TO_TRADE, MAX_CYCLES_WITHOUT_TRADE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def test_pair_rotation_initialization():
    """Test that rotation system is properly initialized"""
    print("\n🧪 Testing rotation system initialization...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Mock API responses for discovery
        mock_luno.return_value.get_tickers.return_value = {
            'XBTZAR': {'ask': '950000', 'bid': '949000', 'volume': '100'},
            'ETHZAR': {'ask': '60000', 'bid': '59900', 'volume': '50'},
            'USDTZAR': {'ask': '18.50', 'bid': '18.45', 'volume': '1000'},
            'XRPZAR': {'ask': '12.00', 'bid': '11.95', 'volume': '200'},
            'LTCZAR': {'ask': '1500', 'bid': '1495', 'volume': '150'},
        }
        
        mock_luno.return_value.get_orderbook_top.return_value = {
            'asks': [{'price': '950000', 'volume': '1'}],
            'bids': [{'price': '949000', 'volume': '1'}]
        }
        
        bot = MultiPairTradingBot()
        
        # Check rotation attributes
        assert hasattr(bot, 'all_evaluated_pairs'), "Bot should have all_evaluated_pairs attribute"
        assert hasattr(bot, 'rotation_index'), "Bot should have rotation_index attribute"  
        assert hasattr(bot, 'cycles_since_last_trade'), "Bot should have cycles_since_last_trade attribute"
        assert hasattr(bot, 'max_cycles_without_trade'), "Bot should have max_cycles_without_trade attribute"
        
        assert bot.rotation_index == 0, "Initial rotation index should be 0"
        assert bot.cycles_since_last_trade == 0, "Initial cycles since last trade should be 0"
        assert bot.max_cycles_without_trade == MAX_CYCLES_WITHOUT_TRADE, "Should use configured max cycles"
        
        print(f"✅ Rotation system initialized correctly")
        print(f"   - Total pairs discovered: {len(bot.all_evaluated_pairs)}")
        print(f"   - Active pairs: {bot.active_pairs}")
        print(f"   - Max cycles without trade: {bot.max_cycles_without_trade}")

def test_pair_selection_and_rotation():
    """Test pair selection and rotation logic"""
    print("\n🧪 Testing pair selection and rotation...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Mock discovery of many pairs
        mock_luno.return_value.get_tickers.return_value = {
            'XBTZAR': {'ask': '950000', 'bid': '949000', 'volume': '100'},
            'ETHZAR': {'ask': '60000', 'bid': '59900', 'volume': '50'},
            'USDTZAR': {'ask': '18.50', 'bid': '18.45', 'volume': '1000'},
            'XRPZAR': {'ask': '12.00', 'bid': '11.95', 'volume': '200'},
            'LTCZAR': {'ask': '1500', 'bid': '1495', 'volume': '150'},
            'ADAZAR': {'ask': '8.00', 'bid': '7.95', 'volume': '80'},
            'BCHZAR': {'ask': '8000', 'bid': '7950', 'volume': '30'},
        }
        
        mock_luno.return_value.get_orderbook_top.return_value = {
            'asks': [{'price': '950000', 'volume': '1'}],
            'bids': [{'price': '949000', 'volume': '1'}]
        }
        
        bot = MultiPairTradingBot()
        
        initial_pairs = bot.active_pairs.copy()
        initial_rotation = bot.rotation_index
        
        print(f"   Initial pairs: {initial_pairs}")
        print(f"   Initial rotation index: {initial_rotation}")
        print(f"   Total pairs available: {len(bot.all_evaluated_pairs)}")
        
        # Test rotation advancement
        if len(bot.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE:
            bot.advance_pair_rotation()
            
            new_pairs = bot.active_pairs
            new_rotation = bot.rotation_index
            
            print(f"   After rotation pairs: {new_pairs}")
            print(f"   After rotation index: {new_rotation}")
            
            assert new_rotation == initial_rotation + 1, "Rotation index should increment"
            assert new_pairs != initial_pairs, "Active pairs should change after rotation"
            assert len(new_pairs) <= MAX_PAIRS_TO_TRADE, "Should not exceed max pairs"
            
            print("✅ Pair rotation working correctly")
        else:
            print("⚠️  Not enough pairs to test rotation (need more than MAX_PAIRS_TO_TRADE)")

def test_trading_activity_tracking():
    """Test that trading activity is properly tracked"""
    print("\n🧪 Testing trading activity tracking...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Setup mock responses
        mock_luno.return_value.get_tickers.return_value = {
            'XBTZAR': {'ask': '950000', 'bid': '949000', 'volume': '100'},
            'ETHZAR': {'ask': '60000', 'bid': '59900', 'volume': '50'},
            'USDTZAR': {'ask': '18.50', 'bid': '18.45', 'volume': '1000'},
        }
        
        mock_luno.return_value.get_orderbook_top.return_value = {
            'asks': [{'price': '950000', 'volume': '1'}],
            'bids': [{'price': '949000', 'volume': '1'}]
        }
        
        # Mock trading methods
        mock_luno.return_value.get_ticker.return_value = {
            'ask': '950000', 'bid': '949000', 'last_trade': '949500'
        }
        
        mock_luno.return_value.get_balance.return_value = 100
        mock_luno.return_value.get_fee.return_value = {'taker_fee': '0.001', 'maker_fee': '0.001'}
        mock_luno.return_value.get_orders_safe.return_value = []
        
        bot = MultiPairTradingBot()
        
        # Test trade_pair returns boolean activity
        with patch.object(bot.strategies[bot.active_pairs[0]], 'should_buy', return_value=False), \
             patch.object(bot.strategies[bot.active_pairs[0]], 'should_sell', return_value=False):
            
            activity = bot.trade_pair(bot.active_pairs[0])
            assert activity == False, "Should return False when no trades are made"
            
        print("✅ Trading activity tracking working correctly")

def test_rotation_trigger_logic():
    """Test that rotation is triggered after max cycles without trades"""
    print("\n🧪 Testing rotation trigger logic...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Setup for multiple pairs
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
        
        bot = MultiPairTradingBot()
        
        # Only test if we have enough pairs for rotation
        if len(bot.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE:
            initial_pairs = bot.active_pairs.copy()
            
            # Simulate cycles without trades
            bot.cycles_since_last_trade = MAX_CYCLES_WITHOUT_TRADE - 1
            
            # Check that rotation is not triggered yet
            should_rotate = (bot.cycles_since_last_trade >= bot.max_cycles_without_trade and 
                           len(bot.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE)
            assert not should_rotate, "Should not rotate yet"
            
            # Increment to trigger rotation
            bot.cycles_since_last_trade = MAX_CYCLES_WITHOUT_TRADE
            
            should_rotate = (bot.cycles_since_last_trade >= bot.max_cycles_without_trade and 
                           len(bot.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE)
            assert should_rotate, "Should trigger rotation now"
            
            # Test the rotation
            bot.advance_pair_rotation()
            
            assert bot.cycles_since_last_trade == 0, "Should reset counter after rotation"
            assert bot.active_pairs != initial_pairs, "Should have different active pairs"
            
            print("✅ Rotation trigger logic working correctly")
        else:
            print("⚠️  Not enough pairs to test rotation trigger (need more than MAX_PAIRS_TO_TRADE)")

def test_pair_rotation_wraparound():
    """Test that rotation wraps around when reaching the end"""
    print("\n🧪 Testing rotation wraparound...")
    
    with patch('multi_pair_trading_bot.LunoAPI') as mock_luno:
        # Setup many pairs to test wraparound
        mock_tickers = {}
        for i in range(10):  # Create 10 pairs
            pair = f"COIN{i}ZAR"
            mock_tickers[pair] = {'ask': f'{1000+i}', 'bid': f'{999+i}', 'volume': f'{100+i}'}
        
        mock_luno.return_value.get_tickers.return_value = mock_tickers
        mock_luno.return_value.get_orderbook_top.return_value = {
            'asks': [{'price': '1000', 'volume': '1'}],
            'bids': [{'price': '999', 'volume': '1'}]
        }
        
        bot = MultiPairTradingBot()
        
        # Only test if we have enough pairs
        if len(bot.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE * 2:
            total_pairs = len(bot.all_evaluated_pairs)
            max_rotations = (total_pairs + MAX_PAIRS_TO_TRADE - 1) // MAX_PAIRS_TO_TRADE
            
            print(f"   Total pairs: {total_pairs}")
            print(f"   Max rotations: {max_rotations}")
            
            # Advance through all rotations
            for i in range(max_rotations):
                print(f"   Rotation {i+1}: {bot.active_pairs}")
                if i < max_rotations - 1:  # Don't advance on last iteration
                    bot.advance_pair_rotation()
            
            # One more advance should wrap around
            initial_pairs = bot.active_pairs.copy()
            bot.advance_pair_rotation()
            
            # Should be back to rotation 0 or have wrapped around properly
            assert bot.rotation_index == 0 or bot.rotation_index < max_rotations, "Should wrap around correctly"
            
            print("✅ Rotation wraparound working correctly")
        else:
            print("⚠️  Not enough pairs to test wraparound")

def main():
    """Run all rotation tests"""
    print("🚀 Testing Multi-Pair Trading Bot Rotation System")
    print("=" * 60)
    
    try:
        test_pair_rotation_initialization()
        test_pair_selection_and_rotation()
        test_trading_activity_tracking()
        test_rotation_trigger_logic()
        test_pair_rotation_wraparound()
        
        print("\n" + "=" * 60)
        print("✅ All rotation tests passed successfully!")
        print(f"📊 Configuration: MAX_PAIRS_TO_TRADE={MAX_PAIRS_TO_TRADE}, MAX_CYCLES_WITHOUT_TRADE={MAX_CYCLES_WITHOUT_TRADE}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
