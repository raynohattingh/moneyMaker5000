#!/usr/bin/env python3
"""
Test script for API-based trading pair discovery
"""

import sys
import os
import logging

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'utils'))

from src.core.luno_api import LunoAPI
from src.utils.trading_pair_discovery import TradingPairDiscovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_api_discovery():
    """Test the new API-based discovery functionality"""
    print("🧪 Testing API-Based Trading Pair Discovery")
    print("=" * 50)
    
    try:
        # Initialize API
        luno = LunoAPI()
        
        # Test getting all available pairs from API
        print("1. Testing get_available_pairs()...")
        available_pairs = luno.get_available_pairs()
        print(f"   ✅ Found {len(available_pairs)} total pairs from API")
        print(f"   Sample pairs: {available_pairs[:10]}")
        print()
        
        # Test pair discovery with specific assets
        print("2. Testing filtered discovery...")
        discovery = TradingPairDiscovery(luno)
        test_assets = ['ZAR', 'XBT', 'ETH', 'USDT']
        
        valid_pairs = discovery.discover_valid_pairs(test_assets)
        print(f"   ✅ Found {len(valid_pairs)} relevant pairs for assets: {test_assets}")
        
        # Show discovered pairs by quote currency
        by_quote = {}
        for pair, data in valid_pairs.items():
            quote = data['quote']
            if quote not in by_quote:
                by_quote[quote] = []
            by_quote[quote].append(pair)
        
        for quote, pairs in sorted(by_quote.items()):
            print(f"   {quote} pairs ({len(pairs)}): {', '.join(sorted(pairs))}")
        
        print()
        
        # Test priority ranking
        print("3. Testing priority ranking...")
        top_pairs = discovery.get_sorted_pairs_by_priority()[:10]
        print(f"   Top 10 priority pairs:")
        for i, pair in enumerate(top_pairs, 1):
            priority = discovery.pair_priorities.get(pair, 0)
            data = valid_pairs[pair]
            print(f"   {i:2d}. {pair} (priority: {priority}, base: {data['base']}, quote: {data['quote']})")
        
        print()
        print("✅ API-based discovery test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api_discovery()
