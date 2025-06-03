#!/usr/bin/env python3
"""
Test script for multi-pair trading bot functionality with dynamic discovery
"""
import logging
from luno_api import LunoAPI
from portfolio_manager import PortfolioManager
from trading_pair_discovery import TradingPairDiscovery
from bot_config import TRADING_ASSETS, ASSET_WEIGHTS

def test_api_connectivity():
    """Test basic API connectivity and dynamic pair discovery"""
    print("Testing API connectivity and pair discovery...")
    try:
        luno = LunoAPI()
        discovery = TradingPairDiscovery(luno)
        
        # Discover valid pairs from assets
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS[:4])  # Test with first 4 assets
        
        if not valid_pairs:
            print("❌ No valid trading pairs discovered")
            return False
        
        print(f"✓ Discovered {len(valid_pairs)} valid trading pairs")
        
        # Test a few pairs
        test_pairs = list(valid_pairs.keys())[:3]
        for pair in test_pairs:
            pair_info = valid_pairs[pair]['info']
            ask = pair_info.get('ask', 0)
            bid = pair_info.get('bid', 0)
            spread = pair_info.get('spread', 0) * 100
            volume = pair_info.get('volume_24h', 0)
            
            print(f"{pair}: Ask={ask}, Bid={bid}, Spread={spread:.3f}%, Volume={volume}")
        
        print("✓ API connectivity test passed")
        return True
        
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def test_fee_calculation():
    """Test fee calculation for discovered pairs"""
    print("\nTesting fee calculation...")
    try:
        luno = LunoAPI()
        discovery = TradingPairDiscovery(luno)
        
        # Discover a few pairs to test
        valid_pairs = discovery.discover_valid_pairs(['ZAR', 'USDT', 'XBT', 'ETH'])
        test_pairs = list(valid_pairs.keys())[:5]
        
        for pair in test_pairs:
            pair_info = valid_pairs[pair]['info']
            taker_fee = pair_info.get('taker_fee', 0)
            maker_fee = pair_info.get('maker_fee', 0)
            
            print(f"{pair}: Taker={taker_fee:.4f}, Maker={maker_fee:.4f}")
        
        print("✓ Fee calculation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Fee calculation test failed: {e}")
        return False

def test_pair_evaluation():
    """Test trading pair evaluation logic"""
    print("\nTesting pair evaluation...")
    try:
        luno = LunoAPI()
        discovery = TradingPairDiscovery(luno)
        
        # Discover pairs and get priority scores
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS[:5])
        
        print("Pair evaluation results:")
        sorted_pairs = discovery.get_sorted_pairs_by_priority()
        
        for i, pair in enumerate(sorted_pairs[:8]):  # Show top 8
            data = valid_pairs[pair]
            priority = data['priority']
            spread = data['info'].get('spread', 0)
            volume = data['info'].get('volume_24h', 0)
            
            print(f"  {pair}: Score={priority}, Spread={spread:.4f}, Volume={volume:.2f}")
        
        # Select top pairs
        max_pairs = 3
        selected_pairs = sorted_pairs[:max_pairs]
        print(f"\nTop {max_pairs} pairs for trading:")
        for pair in selected_pairs:
            priority = valid_pairs[pair]['priority']
            print(f"  {pair} (score: {priority})")
        
        print("✓ Pair evaluation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Pair evaluation test failed: {e}")
        return False

def test_portfolio_manager():
    """Test portfolio manager functionality"""
    print("\nTesting portfolio manager...")
    try:
        luno = LunoAPI()
        discovery = TradingPairDiscovery(luno)
        pm = PortfolioManager(luno)
        
        # Discover valid pairs
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS[:5])
        trading_pairs = list(valid_pairs.keys())
        
        # Test getting all balances
        balances = pm.get_all_balances(trading_pairs)
        print(f"Current balances: {balances}")
        
        # Test portfolio value calculation
        portfolio_values, total_value = pm.get_portfolio_value_in_zar(trading_pairs)
        print(f"Portfolio values in ZAR: {portfolio_values}")
        print(f"Total portfolio value: {total_value:.2f} ZAR")
        
        # Test allocation calculation
        allocations = pm.calculate_allocation_percentages(portfolio_values, total_value)
        print(f"Current allocations: {allocations}")
        
        # Convert asset weights to pair weights
        pair_weights = discovery.convert_asset_weights_to_pair_weights(ASSET_WEIGHTS)
        
        # Test rebalancing actions
        actions = pm.get_rebalancing_actions(allocations, pair_weights, total_value, threshold=5.0)
        if actions:
            print(f"Rebalancing actions needed: {len(actions)}")
            for action in actions:
                print(f"  {action['action']} {action['currency']}: "
                      f"{action['current_pct']:.1f}% -> {action['target_pct']:.1f}% "
                      f"(deviation: {action['deviation']:.1f}%)")
        else:
            print("No rebalancing actions needed")
        
        # Test portfolio summary
        summary = pm.get_portfolio_summary(trading_pairs)
        print(f"Portfolio summary: {summary}")
        
        print("✓ Portfolio manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Portfolio manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Dynamic Multi-Pair Trading Bot Test Suite")
    print("=" * 45)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    tests = [
        test_api_connectivity,
        test_fee_calculation,
        test_pair_evaluation,
        test_portfolio_manager
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Dynamic multi-pair bot is ready to run.")
        print("\nKey improvements:")
        print("  • No hardcoded trading pairs")
        print("  • Dynamic pair discovery from assets")
        print("  • Automatic priority-based selection")
        print("  • Asset-centric configuration")
        print("\nTo start the bot:")
        print("  python multi_pair_trading_bot.py")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and API connectivity.")

if __name__ == "__main__":
    main()
