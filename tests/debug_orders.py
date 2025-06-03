#!/usr/bin/env python3
"""
Debug script to test the list_orders API call
"""
from luno_api import LunoAPI
import json

def test_list_orders():
    luno = LunoAPI()
    
    print("Testing list_orders API call...")
    
    try:
        # Test without pair filter
        all_orders = luno.list_orders()
        print(f"All orders response: {json.dumps(all_orders, indent=2)}")
        
        # Test with pair filter
        for pair in ["USDTZAR", "XBTZAR", "ETHZAR"]:
            try:
                pair_orders = luno.list_orders(pair=pair)
                print(f"\n{pair} orders response: {json.dumps(pair_orders, indent=2)}")
                
                if pair_orders and 'orders' in pair_orders:
                    orders = pair_orders['orders']
                    print(f"{pair} has {len(orders)} orders")
                else:
                    print(f"{pair} orders response is None or missing 'orders' key")
                    
            except Exception as e:
                print(f"Error getting orders for {pair}: {e}")
                
    except Exception as e:
        print(f"Error getting all orders: {e}")

if __name__ == "__main__":
    test_list_orders()
