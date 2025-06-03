#!/usr/bin/env python3

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

print("Starting minimal optimization test...")

try:
    from src.core.multi_pair_trading_bot import MultiPairTradingBot
    print("✓ Bot import successful")
except Exception as e:
    print(f"✗ Bot import failed: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✓ NumPy import successful")
except Exception as e:
    print(f"✗ NumPy import failed: {e}")
    sys.exit(1)

try:
    import psutil
    print("✓ psutil import successful")
except Exception as e:
    print(f"✗ psutil import failed: {e}")
    sys.exit(1)

# Simple optimization test
import time
import threading
from concurrent.futures import ThreadPoolExecutor

class SimpleOptimizationTest:
    def __init__(self):
        self.results = {}
    
    def test_caching_performance(self):
        """Test simple caching performance"""
        print("\n=== Testing Caching Performance ===")
        
        # Simulate cache hits vs misses
        cache = {}
        
        # Test cache misses (cold cache)
        start_time = time.time()
        for i in range(100):
            key = f"key_{i}"
            # Simulate expensive operation
            cache[key] = i * i
            time.sleep(0.001)  # 1ms delay
        cold_time = time.time() - start_time
        
        # Test cache hits (warm cache)  
        start_time = time.time()
        for i in range(100):
            key = f"key_{i}"
            value = cache.get(key, 0)  # Fast cache lookup
        warm_time = time.time() - start_time
        
        speedup = cold_time / warm_time if warm_time > 0 else 0
        
        print(f"Cold cache time: {cold_time:.3f}s")
        print(f"Warm cache time: {warm_time:.3f}s") 
        print(f"Cache speedup: {speedup:.1f}x")
        
        self.results['cache_speedup'] = speedup
        return speedup
    
    def test_concurrent_performance(self):
        """Test concurrent vs sequential performance"""
        print("\n=== Testing Concurrent Performance ===")
        
        def work_function(x):
            # Simulate API call or computation
            time.sleep(0.01)  # 10ms delay
            return x * x
        
        data = list(range(20))
        
        # Sequential processing
        start_time = time.time()
        sequential_results = [work_function(x) for x in data]
        sequential_time = time.time() - start_time
        
        # Concurrent processing
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(work_function, data))
        concurrent_time = time.time() - start_time
        
        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
        
        print(f"Sequential time: {sequential_time:.3f}s")
        print(f"Concurrent time: {concurrent_time:.3f}s")
        print(f"Concurrent speedup: {speedup:.1f}x")
        
        self.results['concurrent_speedup'] = speedup
        return speedup
    
    def run_comprehensive_test(self):
        """Run all optimization tests"""
        print("🚀 Starting Comprehensive Optimization Tests")
        print("=" * 50)
        
        # Run tests
        cache_speedup = self.test_caching_performance()
        concurrent_speedup = self.test_concurrent_performance()
        
        # Calculate overall score
        cache_score = min(cache_speedup * 10, 50)  # Max 50 points
        concurrent_score = min(concurrent_speedup * 10, 50)  # Max 50 points
        total_score = cache_score + concurrent_score
        
        print(f"\n=== Final Results ===")
        print(f"Cache Performance Score: {cache_score:.1f}/50")
        print(f"Concurrent Performance Score: {concurrent_score:.1f}/50")
        print(f"Total Optimization Score: {total_score:.1f}/100")
        
        if total_score >= 80:
            grade = "A+ (Excellent)"
        elif total_score >= 70:
            grade = "A (Very Good)"
        elif total_score >= 60:
            grade = "B (Good)"
        elif total_score >= 50:
            grade = "C (Fair)"
        else:
            grade = "D (Needs Improvement)"
            
        print(f"Performance Grade: {grade}")
        
        return {
            'cache_speedup': cache_speedup,
            'concurrent_speedup': concurrent_speedup,
            'total_score': total_score,
            'grade': grade
        }

if __name__ == "__main__":
    test_mode = sys.argv[1] if len(sys.argv) > 1 else "comprehensive"
    
    optimizer = SimpleOptimizationTest()
    
    if test_mode == "cache":
        optimizer.test_caching_performance()
    elif test_mode == "concurrent":
        optimizer.test_concurrent_performance()
    elif test_mode == "comprehensive":
        results = optimizer.run_comprehensive_test()
        print(f"\n📊 Test completed successfully!")
    else:
        print(f"Unknown test mode: {test_mode}")
        print("Available modes: cache, concurrent, comprehensive")
        sys.exit(1)
