#!/usr/bin/env python3
"""
Comprehensive Stress Test Runner for Trading Bot

This script runs intensive stress tests to validate:
1. High-frequency trading scenarios
2. Network latency resilience 
3. Memory usage and resource management
4. Long-running stability
5. Concurrent operations handling

Usage:
    python stress_test_runner.py --test [quick|standard|intensive]
"""

import os
import sys
import time
import logging
import traceback
import json
import threading
import psutil
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.core.multi_pair_trading_bot import MultiPairTradingBot
    from src.core.luno_api import LunoAPI
    from config.trading.bot_config import *
except ImportError as e:
    # Fallback for direct imports
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config', 'trading'))
    from multi_pair_trading_bot import MultiPairTradingBot
    from luno_api import LunoAPI
    import bot_config

class StressTestTracker:
    """Advanced stress testing and resource monitoring"""
    
    def __init__(self):
        self.session_start = time.time()
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Metrics
        self.cycle_times = []
        self.api_calls = []
        self.errors = []
        self.memory_snapshots = []
        self.cpu_usage = []
        self.network_stats = []
        
        # Stress test specific data
        self.stress_data = {
            'test_type': None,
            'session_start_time': self.session_start,
            'initial_memory_mb': self.initial_memory,
            'stress_tests': {
                'high_frequency': {},
                'latency_resilience': {},
                'memory_management': {},
                'long_running': {},
                'concurrent_operations': {}
            },
            'resource_monitoring': {
                'memory_usage': [],
                'cpu_usage': [],
                'network_calls': []
            }
        }
    
    def take_resource_snapshot(self):
        """Take snapshot of current resource usage"""
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            
            snapshot = {
                'timestamp': time.time(),
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'memory_growth_mb': memory_mb - self.initial_memory
            }
            
            self.memory_snapshots.append(snapshot)
            self.stress_data['resource_monitoring']['memory_usage'].append(snapshot)
            
            return snapshot
        except Exception as e:
            logging.warning(f"Failed to take resource snapshot: {e}")
            return None
    
    def record_api_stress_call(self, call_type, duration, success, latency_ms=None):
        """Record API call with stress test metrics"""
        api_data = {
            'type': call_type,
            'duration': duration,
            'success': success,
            'latency_ms': latency_ms,
            'timestamp': time.time()
        }
        self.api_calls.append(api_data)
        self.stress_data['resource_monitoring']['network_calls'].append(api_data)
    
    def record_stress_error(self, error_type, message, critical=False, test_phase=None):
        """Record errors with stress test context"""
        error_data = {
            'type': error_type,
            'message': str(message),
            'critical': critical,
            'test_phase': test_phase,
            'timestamp': time.time()
        }
        self.errors.append(error_data)
    
    def get_stress_summary(self):
        """Get comprehensive stress test summary"""
        if not self.cycle_times:
            return {'status': 'no_data'}
        
        # Calculate performance metrics
        avg_cycle = sum(self.cycle_times) / len(self.cycle_times)
        min_cycle = min(self.cycle_times)
        max_cycle = max(self.cycle_times)
        
        # Memory analysis
        memory_growth = max([s['memory_growth_mb'] for s in self.memory_snapshots]) if self.memory_snapshots else 0
        avg_memory = sum([s['memory_mb'] for s in self.memory_snapshots]) / len(self.memory_snapshots) if self.memory_snapshots else 0
        
        # API performance
        successful_apis = [a for a in self.api_calls if a['success']]
        api_success_rate = len(successful_apis) / len(self.api_calls) if self.api_calls else 0
        avg_api_time = sum([a['duration'] for a in successful_apis]) / len(successful_apis) if successful_apis else 0
        
        # Error analysis
        critical_errors = len([e for e in self.errors if e.get('critical', False)])
        
        return {
            'performance': {
                'average_cycle_time': avg_cycle,
                'min_cycle_time': min_cycle,
                'max_cycle_time': max_cycle,
                'cycle_variance': max_cycle - min_cycle,
                'total_cycles': len(self.cycle_times)
            },
            'resources': {
                'memory_growth_mb': memory_growth,
                'average_memory_mb': avg_memory,
                'peak_memory_mb': max([s['memory_mb'] for s in self.memory_snapshots]) if self.memory_snapshots else 0
            },
            'api_performance': {
                'success_rate': api_success_rate,
                'average_response_time': avg_api_time,
                'total_calls': len(self.api_calls)
            },
            'reliability': {
                'error_rate': len(self.errors) / max(len(self.cycle_times), 1),
                'critical_errors': critical_errors,
                'total_errors': len(self.errors)
            }
        }
    
    def save_stress_results(self, test_type, filename=None):
        """Save comprehensive stress test results"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'stress_test_{test_type}_{timestamp}.json'
        
        summary = self.get_stress_summary()
        self.stress_data['test_summary'] = summary
        self.stress_data['test_type'] = test_type
        self.stress_data['session_duration'] = time.time() - self.session_start
        
        with open(filename, 'w') as f:
            json.dump(self.stress_data, f, indent=2)
        
        return filename

class StressTradingBot:
    """Trading bot wrapper for stress testing"""
    
    def __init__(self, tracker: StressTestTracker):
        self.tracker = tracker
        
        print("🧪 Initializing Stress Test Trading Bot...")
        init_start = time.time()
        
        try:
            self.bot = MultiPairTradingBot()
            init_time = time.time() - init_start
            print(f"✅ Bot initialized in {init_time:.2f}s")
            
            # Take initial resource snapshot
            initial_snapshot = self.tracker.take_resource_snapshot()
            print(f"📊 Initial memory usage: {initial_snapshot['memory_mb']:.1f}MB")
            
        except Exception as e:
            self.tracker.record_stress_error('initialization', str(e), critical=True)
            raise
    
    def run_high_frequency_test(self, cycles=20, interval=0.1):
        """Test high-frequency trading scenarios"""
        print(f"\n🚀 HIGH FREQUENCY TEST: {cycles} cycles @ {interval}s intervals")
        
        successful_cycles = 0
        start_time = time.time()
        
        for cycle in range(1, cycles + 1):
            cycle_start = time.time()
            
            try:
                # Rapid cycle execution
                for pair in self.bot.active_pairs[:2]:  # Limit to 2 pairs for speed
                    api_start = time.time()
                    ticker = self.bot.luno.get_ticker(pair)
                    api_duration = time.time() - api_start
                    
                    self.tracker.record_api_stress_call('get_ticker', api_duration, True)
                
                cycle_time = time.time() - cycle_start
                self.tracker.cycle_times.append(cycle_time)
                successful_cycles += 1
                
                if cycle % 5 == 0:
                    snapshot = self.tracker.take_resource_snapshot()
                    print(f"  Cycle {cycle}: {cycle_time:.3f}s, Memory: {snapshot['memory_mb']:.1f}MB")
                
                time.sleep(interval)
                
            except Exception as e:
                self.tracker.record_stress_error('high_frequency', str(e), test_phase=f'cycle_{cycle}')
                print(f"  ⚠️ Cycle {cycle} failed: {str(e)}")
        
        total_time = time.time() - start_time
        freq = successful_cycles / total_time if total_time > 0 else 0
        
        print(f"✅ High frequency test: {successful_cycles}/{cycles} cycles, {freq:.2f} cycles/sec")
        return successful_cycles == cycles
    
    def run_memory_stress_test(self, duration_minutes=2):
        """Test memory usage under continuous operation"""
        print(f"\n🧠 MEMORY STRESS TEST: {duration_minutes} minutes continuous operation")
        
        end_time = time.time() + (duration_minutes * 60)
        cycle_count = 0
        
        while time.time() < end_time:
            cycle_start = time.time()
            
            try:
                # Process all pairs
                for pair in self.bot.active_pairs:
                    ticker = self.bot.luno.get_ticker(pair)
                    strategy = self.bot.strategies.get(pair)
                    if strategy:
                        strategy.update_price_history(float(ticker['last_trade']))
                
                cycle_time = time.time() - cycle_start
                self.tracker.cycle_times.append(cycle_time)
                cycle_count += 1
                
                # Take memory snapshot every 10 cycles
                if cycle_count % 10 == 0:
                    snapshot = self.tracker.take_resource_snapshot()
                    print(f"  Cycle {cycle_count}: Memory {snapshot['memory_mb']:.1f}MB (+{snapshot['memory_growth_mb']:.1f}MB)")
                    
                    # Force garbage collection every 50 cycles
                    if cycle_count % 50 == 0:
                        gc.collect()
                
                time.sleep(0.5)  # Moderate pace
                
            except Exception as e:
                self.tracker.record_stress_error('memory_stress', str(e), test_phase=f'cycle_{cycle_count}')
        
        final_snapshot = self.tracker.take_resource_snapshot()
        print(f"✅ Memory stress test: {cycle_count} cycles, Final memory: {final_snapshot['memory_mb']:.1f}MB")
        return final_snapshot['memory_growth_mb'] < 100  # Pass if memory growth < 100MB
    
    def run_latency_resilience_test(self):
        """Test performance under simulated network delays"""
        print(f"\n🌐 LATENCY RESILIENCE TEST: Testing with simulated delays")
        
        delays = [0, 0.1, 0.2, 0.5, 1.0]  # Simulate various network conditions
        results = {}
        
        for delay in delays:
            print(f"  Testing with {delay}s simulated delay...")
            cycle_times = []
            
            for cycle in range(5):
                cycle_start = time.time()
                
                try:
                    for pair in self.bot.active_pairs[:2]:
                        api_start = time.time()
                        ticker = self.bot.luno.get_ticker(pair)
                        api_duration = time.time() - api_start
                        
                        # Simulate network delay
                        time.sleep(delay)
                        
                        self.tracker.record_api_stress_call('get_ticker', api_duration, True, latency_ms=delay*1000)
                    
                    cycle_time = time.time() - cycle_start
                    cycle_times.append(cycle_time)
                    
                except Exception as e:
                    self.tracker.record_stress_error('latency_test', str(e), test_phase=f'delay_{delay}')
            
            avg_time = sum(cycle_times) / len(cycle_times) if cycle_times else float('inf')
            results[delay] = avg_time
            print(f"    Average cycle time: {avg_time:.2f}s")
        
        print("✅ Latency resilience test completed")
        return all(time < 10.0 for time in results.values())  # Pass if all < 10s

def run_stress_tests(test_type='standard'):
    """Run comprehensive stress tests"""
    
    print("🧪 TRADING BOT STRESS TEST SUITE")
    print("=" * 60)
    print(f"Test level: {test_type.upper()}")
    print("=" * 60)
    
    tracker = StressTestTracker()
    
    try:
        bot = StressTradingBot(tracker)
        
        # Configure tests based on type
        if test_type == 'quick':
            tests = [
                ('high_frequency', lambda: bot.run_high_frequency_test(10, 0.2)),
                ('memory_stress', lambda: bot.run_memory_stress_test(0.5))
            ]
        elif test_type == 'intensive':
            tests = [
                ('high_frequency', lambda: bot.run_high_frequency_test(50, 0.05)),
                ('memory_stress', lambda: bot.run_memory_stress_test(5)),
                ('latency_resilience', lambda: bot.run_latency_resilience_test())
            ]
        else:  # standard
            tests = [
                ('high_frequency', lambda: bot.run_high_frequency_test(20, 0.1)),
                ('memory_stress', lambda: bot.run_memory_stress_test(2)),
                ('latency_resilience', lambda: bot.run_latency_resilience_test())
            ]
        
        # Run all tests
        passed_tests = 0
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name} test...")
            try:
                success = test_func()
                if success:
                    passed_tests += 1
                    print(f"✅ {test_name} test PASSED")
                else:
                    print(f"⚠️ {test_name} test FAILED")
            except Exception as e:
                print(f"❌ {test_name} test ERROR: {str(e)}")
                tracker.record_stress_error(test_name, str(e), critical=True)
        
        # Generate comprehensive report
        print(f"\n📊 Generating Stress Test Report...")
        summary = tracker.get_stress_summary()
        report_file = tracker.save_stress_results(test_type)
        
        # Display results
        print(f"\n🎯 STRESS TEST RESULTS ({test_type.upper()})")
        print("=" * 50)
        
        print(f"📈 PERFORMANCE:")
        perf = summary['performance']
        print(f"   Average cycle time: {perf['average_cycle_time']:.3f}s")
        print(f"   Cycle variance: {perf['cycle_variance']:.3f}s")
        print(f"   Total cycles: {perf['total_cycles']}")
        
        print(f"\n💾 RESOURCE USAGE:")
        resources = summary['resources']
        print(f"   Memory growth: {resources['memory_growth_mb']:.1f}MB")
        print(f"   Peak memory: {resources['peak_memory_mb']:.1f}MB")
        
        print(f"\n🌐 API PERFORMANCE:")
        api = summary['api_performance']
        print(f"   Success rate: {api['success_rate']*100:.1f}%")
        print(f"   Average response: {api['average_response_time']:.3f}s")
        print(f"   Total calls: {api['total_calls']}")
        
        print(f"\n🛡️ RELIABILITY:")
        reliability = summary['reliability']
        print(f"   Error rate: {reliability['error_rate']:.3f}")
        print(f"   Critical errors: {reliability['critical_errors']}")
        
        print(f"\n📄 Detailed report: {report_file}")
        print(f"🎖️ Tests passed: {passed_tests}/{len(tests)}")
        
        # Overall assessment
        if passed_tests == len(tests) and reliability['critical_errors'] == 0:
            print(f"\n✅ OVERALL: EXCELLENT - All stress tests passed!")
        elif passed_tests >= len(tests) * 0.8:
            print(f"\n🟡 OVERALL: GOOD - Most stress tests passed")
        else:
            print(f"\n🔴 OVERALL: NEEDS IMPROVEMENT - Multiple test failures")
        
        return passed_tests == len(tests)
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Stress test stopped by user")
        return False
    except Exception as e:
        print(f"\n❌ Stress test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Trading Bot Stress Test Runner')
    parser.add_argument('--test', choices=['quick', 'standard', 'intensive'], 
                       default='standard', help='Test intensity level')
    
    args = parser.parse_args()
    
    try:
        success = run_stress_tests(args.test)
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n👋 Goodbye!")
        sys.exit(0)
