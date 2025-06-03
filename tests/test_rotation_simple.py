#!/usr/bin/env python3
"""
Simple rotation validation test
"""

import logging
logging.basicConfig(level=logging.CRITICAL)  # Suppress all logging

def test_basic_rotation():
    """Test basic rotation mechanics without API calls"""
    print("🧪 Testing basic rotation mechanics...")
    
    try:
        # Mock the bot initialization
        from unittest.mock import patch, MagicMock
        
        print("  Setting up mocks...")
        
        with patch('multi_pair_trading_bot.LunoAPI') as mock_luno, \
             patch('multi_pair_trading_bot.PortfolioManager') as mock_pm, \
             patch('multi_pair_trading_bot.TradingPairDiscovery') as mock_discovery:
            
            print("  Mocks created, configuring responses...")
            
            # Mock API
            mock_api = MagicMock()
            mock_luno.return_value = mock_api
            
            # Mock portfolio manager
            mock_portfolio_manager = MagicMock()
            mock_pm.return_value = mock_portfolio_manager
            
            # Mock discovery
            mock_pair_discovery = MagicMock()
            mock_discovery.return_value = mock_pair_discovery
            
            # Mock discovery results
            mock_pair_discovery.discover_valid_pairs.return_value = {
                'XBTZAR': {'score': 5.0, 'info': {}},
                'ETHZAR': {'score': 4.0, 'info': {}},
                'USDTZAR': {'score': 3.0, 'info': {}},
                'XRPZAR': {'score': 2.0, 'info': {}},
                'LTCZAR': {'score': 1.0, 'info': {}},
                'ADAZAR': {'score': 0.5, 'info': {}},
            }
            
            mock_pair_discovery.convert_asset_weights_to_pair_weights.return_value = {
                'XBTZAR': 0.3, 'ETHZAR': 0.25, 'USDTZAR': 0.2, 'XRPZAR': 0.15, 'LTCZAR': 0.1, 'ADAZAR': 0.05
            }
            
            print("  Importing bot...")
            # Import after mocking
            from multi_pair_trading_bot import MultiPairTradingBot
            
            print("  Creating bot instance...")
            # Create bot
            bot = MultiPairTradingBot()
            
            print("  Checking bot attributes...")
            # Check initial state
            assert hasattr(bot, 'rotation_index'), "Bot should have rotation_index"
            assert hasattr(bot, 'cycles_since_last_trade'), "Bot should have cycles_since_last_trade"
            assert hasattr(bot, 'all_evaluated_pairs'), "Bot should have all_evaluated_pairs"
            
            print(f"✅ Bot created successfully")
            print(f"   Rotation index: {bot.rotation_index}")
            print(f"   Cycles since last trade: {bot.cycles_since_last_trade}")
            print(f"   All evaluated pairs: {len(bot.all_evaluated_pairs) if bot.all_evaluated_pairs else 0}")
            print(f"   Active pairs: {bot.active_pairs}")
            
            # Test rotation if we have enough pairs
            if len(bot.all_evaluated_pairs) > 3:
                initial_pairs = bot.active_pairs.copy()
                initial_rotation = bot.rotation_index
                
                print("  Testing rotation...")
                # Test advance rotation
                bot.advance_pair_rotation()
                
                print(f"   After rotation:")
                print(f"     Rotation index: {bot.rotation_index}")
                print(f"     Active pairs: {bot.active_pairs}")
                print(f"     Pairs changed: {initial_pairs != bot.active_pairs}")
                
                assert bot.rotation_index == initial_rotation + 1, "Rotation index should increment"
                
            print("✅ Basic rotation test passed!")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_basic_rotation()
