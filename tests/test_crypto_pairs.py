#!/usr/bin/env python3
"""
Test script to demonstrate crypto-to-crypto trading functionality
"""

from multi_pair_trading_bot import MultiPairTradingBot
from luno_api import LunoAPI
from bot_config import TRADING_PAIRS
import logging

def test_crypto_trading():
    """Test crypto-to-crypto trading functionality"""
    
    print("🚀 Testing Enhanced Multi-Pair Trading with Crypto-to-Crypto Pairs")
    print("=" * 70)
    
    # Initialize bot
    bot = MultiPairTradingBot()
    
    print(f"\n📊 Configured Trading Pairs: {TRADING_PAIRS}")
    print(f"🎯 Selected Active Pairs: {bot.active_pairs}")
    
    # Test trading logic for each pair type
    print(f"\n💱 Testing Trading Logic for Different Pair Types:")
    print("-" * 50)
    
    for pair in bot.active_pairs:
        try:
            base, quote = bot.parse_trading_pair(pair)
            
            # Get market data
            ticker = bot.luno.get_ticker(pair)
            spread = (float(ticker['ask']) - float(ticker['bid'])) / float(ticker['bid'])
            
            # Get balances
            base_balance = bot.luno.get_balance(base)
            quote_balance = bot.luno.get_balance(quote)
            
            print(f"\n{pair} ({base}/{quote}):")
            print(f"  💰 Balances: {base}={base_balance:.6f}, {quote}={quote_balance:.6f}")
            print(f"  📈 Spread: {spread*100:.3f}%")
            
            # Determine pair type
            if quote == 'ZAR':
                pair_type = "🏛️  Fiat-to-Crypto"
            elif base in ['BTC', 'ETH'] and quote in ['USDT', 'USDC']:
                pair_type = "🔄 Crypto-to-Crypto"
            else:
                pair_type = "🔀 Other"
                
            print(f"  📝 Type: {pair_type}")
            
            # Check if we can trade this pair
            strategy = bot.strategies.get(pair)
            if strategy:
                print(f"  ⚡ Strategy: {strategy.__class__.__name__}")
                print(f"  📦 Order Volume: {strategy.order_volume}")
                
                # Test strategy recommendations (without actually placing orders)
                balance_data = {base: base_balance, quote: quote_balance}
                last_trade = float(ticker['last_trade'])
                
                strategy.update_price_history(last_trade)
                
                should_buy = strategy.should_buy(last_trade, balance_data)
                should_sell = strategy.should_sell(last_trade, balance_data)
                
                print(f"  📊 Strategy Signals: BUY={should_buy}, SELL={should_sell}")
                
        except Exception as e:
            print(f"  ❌ Error testing {pair}: {e}")
    
    # Test portfolio management
    print(f"\n💼 Portfolio Management:")
    print("-" * 30)
    
    try:
        portfolio_values, total_value = bot.portfolio_manager.get_portfolio_value_in_zar(bot.active_pairs)
        allocations = bot.portfolio_manager.calculate_allocation_percentages(portfolio_values, total_value)
        
        print(f"📊 Total Portfolio Value: {total_value:.2f} ZAR")
        print(f"🏦 Current Allocations:")
        
        for currency, allocation in allocations.items():
            if allocation > 0:
                value = portfolio_values[currency]
                print(f"   {currency}: {value:.2f} ZAR ({allocation:.1f}%)")
        
    except Exception as e:
        print(f"❌ Portfolio management error: {e}")
    
    print(f"\n✅ Crypto-to-Crypto Trading Test Complete!")
    print(f"🎯 Key Benefits Demonstrated:")
    print(f"   • Multi-quote currency support (ZAR, USDT, etc.)")
    print(f"   • Enhanced spread opportunities on crypto pairs")
    print(f"   • Portfolio diversification across different pair types")
    print(f"   • Automatic pair evaluation and selection")

if __name__ == "__main__":
    # Set up minimal logging
    logging.basicConfig(level=logging.WARNING)
    test_crypto_trading()
