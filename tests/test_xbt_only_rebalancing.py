#!/usr/bin/env python3
"""
Test the updated rebalancing system to handle all trading pairs (XBT only, no BTC)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'core'))

from portfolio_manager import PortfolioManager
from unittest.mock import Mock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_rebalancing_with_xbt_only():
    """Test rebalancing actions with XBT-only (no BTC conversion)"""
    
    print("🧪 Testing Rebalancing System with XBT Only")
    print("=" * 50)
    
    # Mock Luno API
    mock_luno = Mock()
    
    # Create portfolio manager
    pm = PortfolioManager(mock_luno)
    
    # Test data - using XBT consistently
    current_allocations = {
        'XBT': 40.0,     # Current allocation: 40%
        'ETH': 25.0,     # Current allocation: 25%  
        'ZAR': 35.0      # Current allocation: 35%
    }
    
    target_weights = {
        'XBTZAR': 0.3,   # Target: 30% XBT
        'ETHZAR': 0.15,  # Target: 15% ETH
        'ZAR': 0.55      # Target: 55% ZAR (implicit)
    }
    
    total_value = 10000.0  # 10k ZAR portfolio
    
    print(f"📊 Portfolio: {total_value} ZAR")
    print(f"📈 Current Allocations: {current_allocations}")
    print(f"🎯 Target Weights: {target_weights}")
    print()
    
    # Test rebalancing actions
    actions = pm.get_rebalancing_actions(current_allocations, target_weights, total_value, threshold=5.0)
    
    print(f"🔧 Rebalancing Actions Generated: {len(actions)}")
    
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action['action'].upper()} {action['currency']} via {action['pair']}")
        print(f"     Current: {action['current_pct']:.1f}% → Target: {action['target_pct']:.1f}%")
        print(f"     Deviation: {action['deviation']:.1f}% (threshold: 5.0%)")
        
        # Check for presence of quote currency field
        if 'quote_currency' in action:
            print(f"     Quote Currency: {action['quote_currency']}")
        
        # Check for amount fields
        if 'amount_zar' in action:
            print(f"     Amount ZAR: {action['amount_zar']:.2f}")
        if 'amount_quote' in action:
            print(f"     Amount Quote: {action['amount_quote']:.2f}")
        print()
    
    # Verify expectations
    print(f"✅ Expected Actions:")
    
    # XBT: 40% → 30% = -10% (sell XBT)
    xbt_action = next((a for a in actions if a['currency'] == 'XBT'), None)
    if xbt_action and xbt_action['action'] == 'sell':
        print(f"   ✅ XBT SELL action found (40% → 30% = -10% deviation)")
    else:
        print(f"   ❌ XBT SELL action missing or incorrect: {xbt_action}")
    
    # ETH: 25% → 15% = -10% (sell ETH)
    eth_action = next((a for a in actions if a['currency'] == 'ETH'), None)
    if eth_action and eth_action['action'] == 'sell':
        print(f"   ✅ ETH SELL action found (25% → 15% = -10% deviation)")
    else:
        print(f"   ❌ ETH SELL action missing or incorrect: {eth_action}")
    
    # ZAR: 35% → 55% = +20% (but ZAR is quote currency, so no direct action)
    zar_action = next((a for a in actions if a['currency'] == 'ZAR'), None)
    if not zar_action:
        print(f"   ✅ No ZAR action (35% → 55% = 20% deviation, but ZAR is quote currency)")
    else:
        print(f"   ❌ Unexpected ZAR action: {zar_action}")
    
    print(f"\n🏁 Test Complete: {len(actions)} actions generated")
    
    # Test pair parsing separately
    print(f"\n🔍 Testing Pair Parsing (XBT only):")
    test_pairs = ['XBTZAR', 'ETHZAR', 'XRPUSDT', 'ETHXBT']
    
    for pair in test_pairs:
        base, quote = pm._parse_trading_pair(pair)
        print(f"   {pair} → {base}/{quote}")
        
        # Verify no BTC conversion
        if base == 'BTC' or quote == 'BTC':
            print(f"   ❌ ERROR: BTC found in parsing! Should be XBT only.")
        else:
            print(f"   ✅ No BTC references found")

if __name__ == "__main__":
    test_rebalancing_with_xbt_only()
