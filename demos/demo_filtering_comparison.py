#!/usr/bin/env python3
"""
Demonstrate the difference between filtered and unfiltered pair evaluation
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luno_api import LunoAPI
from portfolio_manager import PortfolioManager
from trading_pair_discovery import TradingPairDiscovery
from bot_config import TRADING_ASSETS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def demo_filtering_comparison():
    """Demonstrate filtering vs no filtering"""
    print("🔍 Position-Based Filtering Comparison Demo")
    print("=" * 50)
    
    try:
        # Initialize components
        luno = LunoAPI()
        portfolio_manager = PortfolioManager(luno)
        discovery = TradingPairDiscovery(luno)
        
        # Get valid pairs and current balances
        valid_pairs = discovery.discover_valid_pairs(TRADING_ASSETS)
        current_balances = portfolio_manager.get_all_balances(list(valid_pairs.keys()))
        
        print(f"📊 Portfolio Status:")
        print(f"   Total discovered pairs: {len(valid_pairs)}")
        print(f"   Current holdings: {list(current_balances.keys())}")
        print(f"   Holdings details: {current_balances}")
        print()
        
        # Analyze pairs by holdings
        pairs_with_holdings = []
        pairs_without_holdings = []
        
        for pair in valid_pairs.keys():
            # Simple parsing for demo
            if pair.endswith('ZAR'):
                base = pair.replace('ZAR', '')
                quote = 'ZAR'
            elif pair.endswith('USDT'):
                base = pair.replace('USDT', '')
                quote = 'USDT'
            elif pair.endswith('USDC'):
                base = pair.replace('USDC', '')
                quote = 'USDC'
            elif pair.endswith('XBT'):
                base = pair.replace('XBT', '')
                quote = 'XBT'
            else:
                base = pair[:3]
                quote = pair[3:]
            
            has_base = current_balances.get(base, 0) > 0
            has_quote = current_balances.get(quote, 0) > 0
            
            if has_base or has_quote:
                pairs_with_holdings.append(pair)
            else:
                pairs_without_holdings.append(pair)
        
        print(f"🎯 Filtering Analysis:")
        print(f"   WITH holdings (would be evaluated): {len(pairs_with_holdings)} pairs")
        for pair in pairs_with_holdings:
            print(f"     ✅ {pair}")
        
        print(f"\n   WITHOUT holdings (would be filtered): {len(pairs_without_holdings)} pairs")  
        for pair in pairs_without_holdings:
            print(f"     ❌ {pair}")
        
        print(f"\n📈 Benefits of Position-Based Filtering:")
        print(f"   - Reduces evaluation from {len(valid_pairs)} to {len(pairs_with_holdings)} pairs")
        print(f"   - Saves {len(pairs_without_holdings)} unnecessary evaluations")
        print(f"   - Focuses trading on assets you actually own")
        print(f"   - Improves efficiency by {(len(pairs_without_holdings)/len(valid_pairs)*100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    demo_filtering_comparison()
