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
    """Test basic API connectivity"""
    print("Testing API connectivity...")
    luno = LunoAPI()
    
    try:
        # Test getting ticker for each trading pair
        for pair in TRADING_PAIRS:
            ticker = luno.get_ticker(pair)
            ask = float(ticker['ask'])
            bid = float(ticker['bid'])
            volume = float(ticker.get('rolling_24_hour_volume', 0))
            spread = (ask - bid) / bid * 100
            
            print(f"{pair}: Ask={ask:.2f}, Bid={bid:.2f}, Spread={spread:.3f}%, Volume={volume:.2f}")
            
        print("✓ API connectivity test passed")
        return True
        
    except Exception as e:
        print(f"✗ API connectivity test failed: {e}")
        return False

def test_portfolio_manager():
    """Test portfolio manager functionality"""
    print("\nTesting portfolio manager...")
    luno = LunoAPI()
    pm = PortfolioManager(luno)
    
    try:
        # Test getting all balances
        balances = pm.get_all_balances()
        print(f"Current balances: {balances}")
        
        # Test portfolio value calculation
        portfolio_values, total_value = pm.get_portfolio_value_in_zar(TRADING_PAIRS)
        print(f"Portfolio values in ZAR: {portfolio_values}")
        print(f"Total portfolio value: {total_value:.2f} ZAR")
        
        # Test allocation calculation
        allocations = pm.calculate_allocation_percentages(portfolio_values, total_value)
        print(f"Current allocations: {allocations}")
        
        # Test rebalancing actions
        actions = pm.get_rebalancing_actions(allocations, PAIR_WEIGHTS, total_value, threshold=5.0)
        if actions:
            print(f"Rebalancing actions needed: {len(actions)}")
            for action in actions:
                print(f"  {action['action']} {action['currency']}: "
                      f"{action['current_pct']:.1f}% -> {action['target_pct']:.1f}% "
                      f"(deviation: {action['deviation']:.1f}%)")
        else:
            print("No rebalancing actions needed")
        
        # Test portfolio summary
        summary = pm.get_portfolio_summary(TRADING_PAIRS)
        print(f"Portfolio summary: {summary}")
        
        print("✓ Portfolio manager test passed")
        return True
        
    except Exception as e:
        print(f"✗ Portfolio manager test failed: {e}")
        return False

def test_pair_evaluation():
    """Test trading pair evaluation logic"""
    print("\nTesting pair evaluation...")
    luno = LunoAPI()
    
    try:
        pair_scores = []
        
        for pair in TRADING_PAIRS:
            ticker = luno.get_ticker(pair)
            ask = float(ticker['ask'])
            bid = float(ticker['bid'])
            volume_24h = float(ticker.get('rolling_24_hour_volume', 0))
            
            spread = (ask - bid) / bid
            score = 0
            
            # Score based on volume and spread
            if volume_24h >= 1000:  # MIN_VOLUME_24H
                score += 1
            if spread >= 0.001:  # MIN_SPREAD_TO_TRADE
                score += 1
            
            # Bonus for higher spreads
            score += min(spread * 1000, 2)
            
            # Weight by configured pair weight
            if pair in PAIR_WEIGHTS:
                score *= PAIR_WEIGHTS[pair]
            
            pair_scores.append((pair, score, spread, volume_24h))
            
        # Sort by score
        pair_scores.sort(key=lambda x: x[1], reverse=True)
        
        print("Pair evaluation results:")
        for pair, score, spread, volume in pair_scores:
            print(f"  {pair}: Score={score:.2f}, Spread={spread:.4f}, Volume={volume:.2f}")
        
        # Select top pairs
        max_pairs = 3  # MAX_PAIRS_TO_TRADE
        selected_pairs = pair_scores[:max_pairs]
        print(f"\nTop {max_pairs} pairs for trading:")
        for pair, score, _, _ in selected_pairs:
            print(f"  {pair} (score: {score:.2f})")
        
        print("✓ Pair evaluation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Pair evaluation test failed: {e}")
        return False

def test_fee_calculation():
    """Test fee calculation for all pairs"""
    print("\nTesting fee calculation...")
    luno = LunoAPI()
    
    try:
        for pair in TRADING_PAIRS:
            fee_info = luno.get_fee(pair)
            taker_fee = float(fee_info.get('taker_fee', 0))
            maker_fee = float(fee_info.get('maker_fee', 0))
            
            print(f"{pair}: Taker={taker_fee:.4f}, Maker={maker_fee:.4f}")
        
        print("✓ Fee calculation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Fee calculation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Multi-Pair Trading Bot Test Suite")
    print("=" * 40)
    
    # Setup logging
    logging.basicConfig(level=logging.ERROR)  # Suppress debug logs during testing
    
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
        print("\n🎉 All tests passed! Multi-pair bot is ready to run.")
        print("\nTo start the bot:")
        print("  python multi_pair_trading_bot.py")
        print("\nTo run in single-pair mode:")
        print("  Set ENABLE_MULTI_PAIR = False in bot_config.py")
        print("  python simple_trading_bot.py")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and API connectivity.")

if __name__ == "__main__":
    main()
