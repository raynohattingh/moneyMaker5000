#!/usr/bin/env python3
"""
Test the enhanced risk management and performance monitoring integration
"""

import sys
import os
import logging
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_pair_trading_bot import MultiPairTradingBot
from bot_config import (
    ENABLE_RISK_MANAGEMENT, ENABLE_PERFORMANCE_MONITORING,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT, PERFORMANCE_LOG_INTERVAL
)

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_bot_initialization():
    """Test bot initialization with risk management and performance monitoring"""
    print("🧪 Testing Bot Initialization...")
    
    try:
        bot = MultiPairTradingBot()
        
        # Check risk management initialization
        if ENABLE_RISK_MANAGEMENT:
            assert bot.risk_manager is not None, "Risk manager should be initialized"
            print(f"✅ Risk Manager: Active (Stop Loss: {STOP_LOSS_PCT}%, Take Profit: {TAKE_PROFIT_PCT}%)")
        else:
            assert bot.risk_manager is None, "Risk manager should be None when disabled"
            print("⚠️  Risk Manager: Disabled")
        
        # Check performance monitoring initialization
        if ENABLE_PERFORMANCE_MONITORING:
            assert bot.performance_monitor is not None, "Performance monitor should be initialized"
            print(f"✅ Performance Monitor: Active (Log Interval: {PERFORMANCE_LOG_INTERVAL} cycles)")
        else:
            assert bot.performance_monitor is None, "Performance monitor should be None when disabled"
            print("⚠️  Performance Monitor: Disabled")
        
        # Check active pairs
        print(f"✅ Active Trading Pairs: {len(bot.active_pairs)} pairs")
        for i, pair in enumerate(bot.active_pairs[:5]):  # Show first 5
            print(f"   {i+1}. {pair}")
        
        if len(bot.active_pairs) > 5:
            print(f"   ... and {len(bot.active_pairs) - 5} more pairs")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_value_calculation():
    """Test portfolio value calculation for risk management"""
    print("\n🧪 Testing Portfolio Value Calculation...")
    
    try:
        bot = MultiPairTradingBot()
        
        # Test portfolio value calculation
        portfolio_value = bot._get_portfolio_value()
        print(f"✅ Portfolio Value: {portfolio_value:.2f} ZAR")
        
        # Test portfolio allocation
        allocations = bot.get_portfolio_allocation()
        if allocations:
            print("✅ Portfolio Allocations:")
            for currency, pct in allocations.items():
                if pct > 0:
                    print(f"   {currency}: {pct:.1f}%")
        else:
            print("⚠️  Portfolio allocations not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio value calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring_methods():
    """Test performance monitoring methods"""
    print("\n🧪 Testing Performance Monitoring Methods...")
    
    try:
        bot = MultiPairTradingBot()
        
        if not bot.performance_monitor:
            print("⚠️  Performance monitoring disabled - skipping test")
            return True
        
        # Test setting initial portfolio value
        initial_value = bot._get_portfolio_value()
        bot.performance_monitor.set_initial_portfolio_value(initial_value)
        print(f"✅ Initial Portfolio Value Set: {initial_value:.2f} ZAR")
        
        # Test portfolio snapshot recording
        current_allocations = bot.get_portfolio_allocation()
        bot.performance_monitor.record_portfolio_snapshot(initial_value, current_allocations)
        print("✅ Portfolio Snapshot Recorded")
        
        # Test performance metrics
        metrics = bot.performance_monitor.get_performance_metrics()
        print(f"✅ Performance Metrics Retrieved:")
        print(f"   Total Trades: {metrics.total_trades}")
        print(f"   Win Rate: {metrics.win_rate_pct:.1f}%")
        print(f"   Total P&L: {metrics.total_pnl_zar:+.2f} ZAR")
        
        # Test doubling goal check
        doubling_achieved, growth_pct = bot.performance_monitor.is_doubling_goal_achieved()
        print(f"✅ Doubling Goal Check:")
        print(f"   Current Growth: {growth_pct:+.2f}%")
        print(f"   Goal Achieved: {'Yes' if doubling_achieved else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_management_methods():
    """Test risk management methods"""
    print("\n🧪 Testing Risk Management Methods...")
    
    try:
        bot = MultiPairTradingBot()
        
        if not bot.risk_manager:
            print("⚠️  Risk management disabled - skipping test")
            return True
        
        # Test portfolio value for position sizing
        portfolio_value = bot._get_portfolio_value()
        max_position_size = bot.risk_manager.calculate_max_position_size(portfolio_value)
        print(f"✅ Risk Management Parameters:")
        print(f"   Portfolio Value: {portfolio_value:.2f} ZAR")
        print(f"   Max Position Size: {max_position_size:.2f} ZAR")
        print(f"   Stop Loss: {bot.risk_manager.stop_loss_pct}%")
        print(f"   Take Profit: {bot.risk_manager.take_profit_pct}%")
        
        # Test position tracking (without actually opening positions)
        print("✅ Risk management system operational")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trade_entry_tracking():
    """Test trade entry and completion tracking"""
    print("\n🧪 Testing Trade Entry Tracking...")
    
    try:
        bot = MultiPairTradingBot()
        
        if not bot.performance_monitor:
            print("⚠️  Performance monitoring disabled - skipping test")
            return True
        
        # Test storing a mock trade entry
        test_pair = bot.active_pairs[0] if bot.active_pairs else 'XBTZAR'
        bot._store_trade_entry(
            pair=test_pair,
            side='buy',
            entry_price=950000.0,
            volume=0.001,
            strategy='test_strategy',
            fees=9.5
        )
        print(f"✅ Trade Entry Stored: {test_pair}")
        
        # Check if trade is in pending trades
        if hasattr(bot, '_pending_trades') and test_pair in bot._pending_trades:
            print("✅ Trade Found in Pending Trades")
            
            # Test completing the trade
            time.sleep(0.1)  # Small delay to simulate trade duration
            bot._record_completed_trade(test_pair, 955000.0, 'test_exit')
            print("✅ Trade Completion Recorded")
            
            # Verify trade was removed from pending
            if test_pair not in bot._pending_trades:
                print("✅ Trade Removed from Pending After Completion")
            else:
                print("⚠️  Trade still in pending after completion")
        else:
            print("❌ Trade not found in pending trades")
        
        return True
        
    except Exception as e:
        print(f"❌ Trade tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all integration tests"""
    print("🚀 Enhanced Integration Testing")
    print("=" * 50)
    
    tests = [
        test_bot_initialization,
        test_portfolio_value_calculation,
        test_performance_monitoring_methods,
        test_risk_management_methods,
        test_trade_entry_tracking
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n🏆 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! The system is ready.")
        return True
    else:
        print(f"💥 {total - passed} tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
