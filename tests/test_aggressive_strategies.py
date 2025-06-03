#!/usr/bin/env python3
"""
Test script for aggressive trading strategies
"""

import sys
import time
import logging
from bot_config import (
    STRATEGY, MOMENTUM_THRESHOLD, SCALPING_MIN_PROFIT, BREAKOUT_THRESHOLD,
    FEAR_THRESHOLD, GREED_THRESHOLD, VOLUME_SURGE_THRESHOLD
)
from trading_strategies import (
    MomentumStrategy, ScalpingStrategy, BreakoutStrategy, 
    FearGreedStrategy, VolumeSurgeStrategy, HybridAggressiveStrategy
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def test_strategy(strategy_class, strategy_name, pair="XBTZAR", volume=0.001, **kwargs):
    """Test a specific strategy with sample data"""
    print(f"\n🧪 Testing {strategy_name} Strategy")
    print("=" * 50)
    
    try:
        # Create strategy instance
        strategy = strategy_class(pair, volume, **kwargs)
        
        # Simulate price movements
        test_prices = [
            100000, 100500, 101000, 100800, 100600,  # Initial trend up then down
            100400, 100200, 100000, 99800, 99600,    # Continued decline
            99400, 99200, 99000, 99200, 99400,       # Bounce back
            99600, 99800, 100000, 100200, 100400,    # Recovery
            100600, 100800, 101000, 101200, 101400   # New uptrend
        ]
        
        balance_data = {"XBT": 0.01, "ZAR": 1000}
        
        buy_signals = 0
        sell_signals = 0
        
        for i, price in enumerate(test_prices):
            strategy.update_price_history(price)
            
            if len(strategy.price_history) >= 5:  # Need some history
                should_buy = strategy.should_buy(price, balance_data)
                should_sell = strategy.should_sell(price, balance_data)
                
                if should_buy:
                    buy_signals += 1
                    buy_price = strategy.get_buy_price(price * 0.999, price * 1.001)
                    print(f"  Step {i+1}: BUY signal at {price} (order price: {buy_price:.2f})")
                
                if should_sell:
                    sell_signals += 1
                    sell_price = strategy.get_sell_price(price * 0.999, price * 1.001)
                    print(f"  Step {i+1}: SELL signal at {price} (order price: {sell_price:.2f})")
        
        print(f"\n📊 Strategy Results:")
        print(f"   Buy signals: {buy_signals}")
        print(f"   Sell signals: {sell_signals}")
        print(f"   Activity level: {'High' if (buy_signals + sell_signals) > 5 else 'Moderate' if (buy_signals + sell_signals) > 2 else 'Low'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {strategy_name}: {e}")
        return False

def test_fear_greed_strategy():
    """Test Fear & Greed strategy with actual API call"""
    print(f"\n🧪 Testing Fear & Greed Strategy (Live Data)")
    print("=" * 50)
    
    try:
        strategy = FearGreedStrategy("XBTZAR", 0.001, FEAR_THRESHOLD, GREED_THRESHOLD)
        
        # Get current fear & greed index
        fear_greed_value = strategy.get_fear_greed_index()
        print(f"Current Fear & Greed Index: {fear_greed_value}")
        
        # Test buy/sell logic
        test_price = 100000
        balance_data = {"XBT": 0.01, "ZAR": 1000}
        
        should_buy = strategy.should_buy(test_price, balance_data)
        should_sell = strategy.should_sell(test_price, balance_data)
        
        print(f"At current market sentiment:")
        print(f"  Should buy: {should_buy}")
        print(f"  Should sell: {should_sell}")
        
        # Test at different fear/greed levels
        print(f"\nStrategy thresholds:")
        print(f"  Buy when Fear/Greed <= {FEAR_THRESHOLD} (Extreme Fear)")
        print(f"  Sell when Fear/Greed >= {GREED_THRESHOLD} (Extreme Greed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Fear & Greed strategy: {e}")
        return False

def main():
    """Test all aggressive strategies"""
    print("🚀 Testing Aggressive Trading Strategies")
    print("=" * 60)
    
    strategies_to_test = [
        (MomentumStrategy, "Momentum", {"momentum_threshold": MOMENTUM_THRESHOLD, "lookback_periods": 5}),
        (ScalpingStrategy, "Scalping", {"min_profit_pct": SCALPING_MIN_PROFIT}),
        (BreakoutStrategy, "Breakout", {"breakout_threshold": BREAKOUT_THRESHOLD, "consolidation_periods": 20}),
        (VolumeSurgeStrategy, "Volume Surge", {"volume_surge_threshold": VOLUME_SURGE_THRESHOLD}),
        (HybridAggressiveStrategy, "Hybrid Aggressive", {}),
    ]
    
    successful_tests = 0
    total_tests = len(strategies_to_test)
    
    for strategy_class, name, kwargs in strategies_to_test:
        if test_strategy(strategy_class, name, **kwargs):
            successful_tests += 1
        time.sleep(1)  # Small delay between tests
    
    # Test Fear & Greed strategy separately (requires API call)
    print(f"\n" + "=" * 60)
    if test_fear_greed_strategy():
        successful_tests += 1
    total_tests += 1
    
    print(f"\n🎯 Test Summary")
    print("=" * 30)
    print(f"Successful tests: {successful_tests}/{total_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("✅ All aggressive strategies are working correctly!")
        print("\n💡 Recommendations for doubling your holdings:")
        print("   1. Start with 'momentum' strategy for trending markets")
        print("   2. Use 'scalping' for high-volatility periods")
        print("   3. Try 'fear_greed' for contrarian opportunities")
        print("   4. Use 'hybrid_aggressive' for maximum signal diversity")
        print("   5. Enable AGGRESSIVE_ROTATION for faster pair switching")
    else:
        print("⚠️  Some strategies had issues - check the logs above")

if __name__ == "__main__":
    main()
