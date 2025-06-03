#!/usr/bin/env python3
"""
Test script for the new dynamic trading pair discovery system
"""

import logging
from trading_pair_discovery import TradingPairDiscovery
from luno_api import LunoAPI
from bot_config import TRADING_ASSETS, ASSET_WEIGHTS

def test_dynamic_discovery():
    """Test the dynamic trading pair discovery system"""
    
    print("🔍 Testing Dynamic Trading Pair Discovery System")
    print("=" * 60)
    
    # Set up minimal logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize discovery system
    luno = LunoAPI()
    discovery = TradingPairDiscovery(luno)
    
    print(f"\n📊 Configured Trading Assets: {TRADING_ASSETS}")
    print(f"🎯 Asset Weights: {ASSET_WEIGHTS}")
    
    # Discover valid trading pairs
    print(f"\n🔍 Discovering valid trading pairs...")
    valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS)
    
    print(f"\n✅ Discovery Results:")
    print(f"   Found {len(valid_pairs)} valid trading pairs")
    
    # Show some example pairs
    print(f"\n📈 Valid Trading Pairs:")
    for i, (pair, data) in enumerate(list(valid_pairs.items())[:10]):  # Show first 10
        base = data['base']
        quote = data['quote']
        priority = data['priority']
        info = data['info']
        spread = info.get('spread', 0) * 100
        volume = info.get('volume_24h', 0)
        
        print(f"   {i+1:2d}. {pair} ({base}/{quote}) - Priority: {priority}, Spread: {spread:.3f}%, Volume: {volume:.2f}")
        
        if i >= 9:  # Limit output
            break
    
    # Test asset-to-pair mapping
    print(f"\n🔗 Asset-to-Pair Mapping Examples:")
    test_assets = ['ZAR', 'USDT', 'XBT', 'ETH']
    for asset in test_assets:
        pairs = discovery.get_pairs_for_asset(asset)
        print(f"   {asset}: {len(pairs)} pairs ({', '.join(list(pairs)[:5])}{'...' if len(pairs) > 5 else ''})")
    
    # Test conversion pair finding
    print(f"\n💱 Best Conversion Pairs:")
    conversions = [
        ('ZAR', 'USDT'),
        ('XBT', 'USDT'), 
        ('ETH', 'ZAR'),
        ('USDT', 'XBT')
    ]
    
    for from_asset, to_asset in conversions:
        best_pair = discovery.get_best_pair_for_conversion(from_asset, to_asset)
        print(f"   {from_asset} → {to_asset}: {best_pair or 'No direct pair'}")
    
    # Test pair weight conversion
    print(f"\n⚖️  Converting Asset Weights to Pair Weights:")
    pair_weights = discovery.convert_asset_weights_to_pair_weights(ASSET_WEIGHTS)
    
    print(f"   Generated {len(pair_weights)} pair weights")
    top_pairs = sorted(pair_weights.items(), key=lambda x: x[1], reverse=True)[:8]
    
    for pair, weight in top_pairs:
        print(f"   {pair}: {weight:.4f} ({weight*100:.1f}%)")
    
    # Verify weights sum to 1.0
    total_weight = sum(pair_weights.values())
    print(f"\n   Total weight: {total_weight:.6f} (should be close to 1.0)")
    
    print(f"\n✅ Dynamic Trading Pair Discovery Test Complete!")
    print(f"🎯 Key Benefits:")
    print(f"   • No hardcoded trading pairs - fully dynamic")
    print(f"   • Auto-discovery of available pairs on Luno")
    print(f"   • Priority-based pair selection")
    print(f"   • Asset-centric configuration")
    print(f"   • Automatic weight distribution")

if __name__ == "__main__":
    test_dynamic_discovery()
