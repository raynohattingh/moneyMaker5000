#!/usr/bin/env python3
"""
Comprehensive Trading Bot Performance Test Runner

This script runs the trading bot and tracks key performance metrics:
1. Speed (cycle times, API response times)
2. Error handling (error rates, recovery)
3. Overall correctness (trading logic, portfolio management)

Usage:
    python performance_test_runner.py
"""

import os
import sys
import time
import logging
import traceback
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import signal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import bot modules
try:
    from src.core.multi_pair_trading_bot import MultiPairTradingBot
    from src.core.luno_api import LunoAPI
    from config.trading.bot_config import *
except ImportError as e:
    # Fallback for direct imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from multi_pair_trading_bot import MultiPairTradingBot
    from bot_config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("performance_test.log"),
        logging.StreamHandler()
    ]
)

class PerformanceTracker:
    """Tracks and analyzes bot performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'initialization': {},
            'speed': {
                'cycle_times': [],
                'api_response_times': [],
                'pair_processing_times': {}
            },
            'errors': {
                'total_errors': 0,
                'api_errors': 0,
                'trading_errors': 0,
                'error_details': []
            },
            'correctness': {
                'successful_api_calls': 0,
                'failed_api_calls': 0,
                'trading_decisions': [],
                'portfolio_values': []
            },
            'trading_activity': {
                'trades_attempted': 0,
                'trades_successful': 0,
                'pairs_processed': 0,
                'cycles_completed': 0
            }
        }
        self.running = True
        
    def record_initialization_time(self, duration: float):
        """Record bot initialization time"""
        self.metrics['initialization']['duration_seconds'] = duration
        
    def record_cycle_time(self, duration: float):
        """Record time for complete trading cycle"""
        self.metrics['speed']['cycle_times'].append(duration)
        
    def record_api_response_time(self, endpoint: str, duration: float, success: bool):
        """Record API call performance"""
        self.metrics['speed']['api_response_times'].append({
            'endpoint': endpoint,
            'duration': duration,
            'success': success,
            'timestamp': time.time()
        })
        
        if success:
            self.metrics['correctness']['successful_api_calls'] += 1
        else:
            self.metrics['correctness']['failed_api_calls'] += 1
            
    def record_pair_processing_time(self, pair: str, duration: float):
        """Record time to process a trading pair"""
        if pair not in self.metrics['speed']['pair_processing_times']:
            self.metrics['speed']['pair_processing_times'][pair] = []
        self.metrics['speed']['pair_processing_times'][pair].append(duration)
        
    def record_error(self, error_type: str, error_msg: str, details: Any = None):
        """Record an error"""
        self.metrics['errors']['total_errors'] += 1
        
        if 'api' in error_type.lower():
            self.metrics['errors']['api_errors'] += 1
        elif 'trading' in error_type.lower():
            self.metrics['errors']['trading_errors'] += 1
            
        self.metrics['errors']['error_details'].append({
            'type': error_type,
            'message': error_msg,
            'details': str(details) if details else None,
            'timestamp': time.time()
        })
        
    def record_trading_decision(self, pair: str, decision: str, price: float, volume: float = None):
        """Record a trading decision"""
        self.metrics['correctness']['trading_decisions'].append({
            'pair': pair,
            'decision': decision,
            'price': price,
            'volume': volume,
            'timestamp': time.time()
        })
        
        if decision in ['buy', 'sell']:
            self.metrics['trading_activity']['trades_attempted'] += 1
            
    def record_portfolio_value(self, value: float):
        """Record portfolio value snapshot"""
        self.metrics['correctness']['portfolio_values'].append({
            'value': value,
            'timestamp': time.time()
        })
        
    def generate_report(self) -> Dict:
        """Generate comprehensive performance report"""
        total_runtime = time.time() - self.start_time
        
        # Speed metrics
        avg_cycle_time = sum(self.metrics['speed']['cycle_times']) / len(self.metrics['speed']['cycle_times']) if self.metrics['speed']['cycle_times'] else 0
        max_cycle_time = max(self.metrics['speed']['cycle_times']) if self.metrics['speed']['cycle_times'] else 0
        min_cycle_time = min(self.metrics['speed']['cycle_times']) if self.metrics['speed']['cycle_times'] else 0
        
        api_times = [call['duration'] for call in self.metrics['speed']['api_response_times']]
        avg_api_time = sum(api_times) / len(api_times) if api_times else 0
        
        # Error rates
        total_api_calls = self.metrics['correctness']['successful_api_calls'] + self.metrics['correctness']['failed_api_calls']
        api_error_rate = self.metrics['correctness']['failed_api_calls'] / total_api_calls if total_api_calls > 0 else 0
        
        # Portfolio growth
        portfolio_growth = 0
        if len(self.metrics['correctness']['portfolio_values']) >= 2:
            start_value = self.metrics['correctness']['portfolio_values'][0]['value']
            end_value = self.metrics['correctness']['portfolio_values'][-1]['value']
            portfolio_growth = ((end_value - start_value) / start_value) * 100 if start_value > 0 else 0
        
        report = {
            'test_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_runtime_seconds': total_runtime,
                'cycles_completed': len(self.metrics['speed']['cycle_times'])
            },
            'speed_metrics': {
                'initialization_time': self.metrics['initialization'].get('duration_seconds', 0),
                'cycle_performance': {
                    'average_seconds': avg_cycle_time,
                    'min_seconds': min_cycle_time,
                    'max_seconds': max_cycle_time,
                    'total_cycles': len(self.metrics['speed']['cycle_times'])
                },
                'api_performance': {
                    'average_response_time': avg_api_time,
                    'total_calls': len(api_times),
                    'fastest_call': min(api_times) if api_times else 0,
                    'slowest_call': max(api_times) if api_times else 0
                }
            },
            'error_metrics': {
                'total_errors': self.metrics['errors']['total_errors'],
                'api_errors': self.metrics['errors']['api_errors'],
                'trading_errors': self.metrics['errors']['trading_errors'],
                'api_error_rate': api_error_rate,
                'error_rate_per_cycle': self.metrics['errors']['total_errors'] / len(self.metrics['speed']['cycle_times']) if self.metrics['speed']['cycle_times'] else 0
            },
            'correctness_metrics': {
                'api_success_rate': (self.metrics['correctness']['successful_api_calls'] / total_api_calls) if total_api_calls > 0 else 0,
                'trading_decisions': len(self.metrics['correctness']['trading_decisions']),
                'portfolio_growth_pct': portfolio_growth,
                'portfolio_snapshots': len(self.metrics['correctness']['portfolio_values'])
            },
            'trading_activity': self.metrics['trading_activity']
        }
        
        return report
        
    def print_live_stats(self):
        """Print live performance statistics"""
        if self.metrics['speed']['cycle_times']:
            avg_cycle = sum(self.metrics['speed']['cycle_times']) / len(self.metrics['speed']['cycle_times'])
            print(f"📊 Live Stats - Cycles: {len(self.metrics['speed']['cycle_times'])}, Avg Time: {avg_cycle:.2f}s, Errors: {self.metrics['errors']['total_errors']}")


class MonitoredTradingBot:
    """Wrapper around the trading bot to monitor performance"""
    
    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        self.bot = None
        
    def initialize(self):
        """Initialize the trading bot with performance tracking"""
        start_time = time.time()
        
        try:
            print("🤖 Initializing Trading Bot...")
            self.bot = MultiPairTradingBot()
            
            init_duration = time.time() - start_time
            self.tracker.record_initialization_time(init_duration)
            
            print(f"✅ Bot initialized in {init_duration:.4f} seconds")
            print(f"📊 Active pairs: {len(self.bot.active_pairs)}")
            print(f"🔧 Strategy: {STRATEGY}")
            print(f"💰 Multi-pair enabled: {ENABLE_MULTI_PAIR}")
            
            return True
            
        except Exception as e:
            self.tracker.record_error("initialization", f"Failed to initialize bot: {e}", e)
            print(f"❌ Bot initialization failed: {e}")
            traceback.print_exc()
            return False
            
    def run_performance_test(self, max_cycles: int = 5, timeout_minutes: int = 10):
        """Run the bot for performance testing"""
        if not self.bot:
            print("❌ Bot not initialized")
            return False
            
        print(f"\n🚀 Starting performance test: {max_cycles} cycles, {timeout_minutes} minute timeout")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        cycle_count = 0
        
        try:
            # Get initial portfolio value
            try:
                initial_value = self.bot._get_portfolio_value()
                self.tracker.record_portfolio_value(initial_value)
                print(f"💰 Initial portfolio value: {initial_value:.2f} ZAR")
            except Exception as e:
                self.tracker.record_error("portfolio", "Failed to get initial portfolio value", e)
                
            while cycle_count < max_cycles and (time.time() - start_time) < timeout_seconds:
                cycle_start_time = time.time()
                
                print(f"\n🔄 Cycle {cycle_count + 1}/{max_cycles}")
                
                try:
                    # Process each active pair
                    for pair in self.bot.active_pairs:
                        pair_start_time = time.time()
                        
                        try:
                            # Test API calls with timing
                            self._test_api_calls(pair)
                            
                            # Test trading logic (without actual trading)
                            self._test_trading_logic(pair)
                            
                        except Exception as e:
                            self.tracker.record_error("pair_processing", f"Error processing {pair}", e)
                            
                        finally:
                            pair_duration = time.time() - pair_start_time
                            self.tracker.record_pair_processing_time(pair, pair_duration)
                            self.tracker.metrics['trading_activity']['pairs_processed'] += 1
                    
                    # Get portfolio value after cycle
                    try:
                        current_value = self.bot._get_portfolio_value()
                        self.tracker.record_portfolio_value(current_value)
                    except Exception as e:
                        self.tracker.record_error("portfolio", "Failed to get portfolio value", e)
                        
                except Exception as e:
                    self.tracker.record_error("cycle", f"Error in cycle {cycle_count + 1}", e)
                
                cycle_duration = time.time() - cycle_start_time
                self.tracker.record_cycle_time(cycle_duration)
                self.tracker.metrics['trading_activity']['cycles_completed'] += 1
                
                print(f"✅ Cycle {cycle_count + 1} completed in {cycle_duration:.4f} seconds")
                
                cycle_count += 1
                
                # Print live stats every few cycles
                if cycle_count % 2 == 0:
                    self.tracker.print_live_stats()
                
                # Small delay between cycles
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            
        except Exception as e:
            self.tracker.record_error("test_runner", "Fatal error in performance test", e)
            print(f"❌ Fatal error: {e}")
            traceback.print_exc()
            
        print(f"\n✅ Performance test completed: {cycle_count} cycles in {time.time() - start_time:.2f} seconds")
        return True
        
    def _test_api_calls(self, pair: str):
        """Test API calls for a trading pair"""
        try:
            # Test ticker API
            api_start = time.time()
            ticker = self.bot.luno.get_ticker(pair)
            api_duration = time.time() - api_start
            self.tracker.record_api_response_time('get_ticker', api_duration, True)
            
            # Test balance API
            base_currency, quote_currency = self.bot.parse_trading_pair(pair)
            
            api_start = time.time()
            base_balance = self.bot.luno.get_balance(base_currency)
            api_duration = time.time() - api_start
            self.tracker.record_api_response_time('get_balance', api_duration, True)
            
            api_start = time.time()
            quote_balance = self.bot.luno.get_balance(quote_currency)
            api_duration = time.time() - api_start
            self.tracker.record_api_response_time('get_balance', api_duration, True)
            
        except Exception as e:
            self.tracker.record_api_response_time('api_call', 0, False)
            self.tracker.record_error("api", f"API call failed for {pair}", e)
            
    def _test_trading_logic(self, pair: str):
        """Test trading logic without executing trades"""
        try:
            strategy = self.bot.strategies.get(pair)
            if not strategy:
                return
                
            # Get market data
            ticker = self.bot.luno.get_ticker(pair)
            last_trade = float(ticker['last_trade'])
            
            # Update strategy
            strategy.update_price_history(last_trade)
            
            # Get balances
            base_currency, quote_currency = self.bot.parse_trading_pair(pair)
            base_balance = self.bot.luno.get_balance(base_currency)
            quote_balance = self.bot.luno.get_balance(quote_currency)
            
            balance_data = {base_currency: base_balance, quote_currency: quote_balance}
            
            # Test trading decisions
            should_sell = strategy.should_sell(last_trade, balance_data)
            should_buy = strategy.should_buy(last_trade, balance_data)
            
            if should_sell:
                self.tracker.record_trading_decision(pair, 'sell', last_trade, strategy.order_volume)
            elif should_buy:
                self.tracker.record_trading_decision(pair, 'buy', last_trade, strategy.order_volume)
            else:
                self.tracker.record_trading_decision(pair, 'hold', last_trade)
                
        except Exception as e:
            self.tracker.record_error("trading_logic", f"Trading logic error for {pair}", e)


def main():
    """Main performance test function"""
    print("🚀 Trading Bot Performance Test Runner")
    print("=" * 50)
    
    # Initialize performance tracker
    tracker = PerformanceTracker()
    
    # Initialize monitored bot
    monitored_bot = MonitoredTradingBot(tracker)
    
    # Run the test
    try:
        if not monitored_bot.initialize():
            print("❌ Failed to initialize bot")
            return False
            
        # Run performance test
        success = monitored_bot.run_performance_test(max_cycles=5, timeout_minutes=10)
        
        # Generate and display report
        report = tracker.generate_report()
        
        # Save detailed report
        with open('performance_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        # Display summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)
        
        print(f"⏱️  Total Runtime: {report['test_summary']['total_runtime_seconds']:.2f} seconds")
        print(f"🔄 Cycles Completed: {report['test_summary']['cycles_completed']}")
        print(f"🚀 Initialization Time: {report['speed_metrics']['initialization_time']:.4f} seconds")
        print(f"⚡ Average Cycle Time: {report['speed_metrics']['cycle_performance']['average_seconds']:.4f} seconds")
        print(f"🌐 Average API Response: {report['speed_metrics']['api_performance']['average_response_time']:.4f} seconds")
        print(f"❌ Total Errors: {report['error_metrics']['total_errors']}")
        print(f"📈 API Success Rate: {report['correctness_metrics']['api_success_rate']*100:.1f}%")
        print(f"💰 Portfolio Growth: {report['correctness_metrics']['portfolio_growth_pct']:.2f}%")
        
        # Performance assessment
        print("\n🏆 PERFORMANCE ASSESSMENT:")
        
        # Speed assessment
        avg_cycle = report['speed_metrics']['cycle_performance']['average_seconds']
        if avg_cycle < 2.0:
            print("✅ SPEED: Excellent")
        elif avg_cycle < 5.0:
            print("🟡 SPEED: Good")
        else:
            print("🔴 SPEED: Needs Improvement")
            
        # Error handling assessment
        error_rate = report['error_metrics']['error_rate_per_cycle']
        if error_rate == 0:
            print("✅ ERROR HANDLING: Excellent")
        elif error_rate < 0.1:
            print("🟡 ERROR HANDLING: Good")
        else:
            print("🔴 ERROR HANDLING: Needs Improvement")
            
        # Overall correctness
        api_success = report['correctness_metrics']['api_success_rate']
        if api_success >= 0.95 and error_rate < 0.1:
            print("✅ OVERALL CORRECTNESS: Excellent")
        elif api_success >= 0.85 and error_rate < 0.2:
            print("🟡 OVERALL CORRECTNESS: Good")
        else:
            print("🔴 OVERALL CORRECTNESS: Needs Improvement")
            
        print(f"\n📄 Detailed report saved to: performance_test_report.json")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
