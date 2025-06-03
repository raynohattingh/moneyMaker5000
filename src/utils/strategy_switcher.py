#!/usr/bin/env python3
"""
Strategy Configuration Switcher
Easily switch between different aggressive trading strategies
"""

import os
import shutil
from datetime import datetime

# Strategy configurations
STRATEGIES = {
    "conservative": {
        "STRATEGY": "conservative",
        "AGGRESSIVE_ROTATION": False,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 10,
        "SLEEP_INTERVAL": 60,
        "BASE_ORDER_VOLUME": 100,
        "MAX_PAIRS_TO_TRADE": 3,
        "description": "Safe, low-risk trading with minimal activity"
    },
    
    "momentum": {
        "STRATEGY": "momentum",
        "MOMENTUM_THRESHOLD": 0.015,
        "MOMENTUM_LOOKBACK": 5,
        "AGGRESSIVE_ROTATION": True,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 3,
        "SLEEP_INTERVAL": 45,
        "BASE_ORDER_VOLUME": 120,
        "MAX_PAIRS_TO_TRADE": 4,
        "description": "Trend-following strategy for bullish markets"
    },
    
    "scalping": {
        "STRATEGY": "scalping",
        "SCALPING_MIN_PROFIT": 0.003,
        "AGGRESSIVE_ROTATION": True,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 2,
        "SLEEP_INTERVAL": 30,
        "BASE_ORDER_VOLUME": 100,
        "MAX_PAIRS_TO_TRADE": 5,
        "description": "High-frequency trading for volatile markets"
    },
    
    "fear_greed": {
        "STRATEGY": "fear_greed",
        "FEAR_THRESHOLD": 30,
        "GREED_THRESHOLD": 70,
        "AGGRESSIVE_ROTATION": False,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 5,
        "SLEEP_INTERVAL": 60,
        "BASE_ORDER_VOLUME": 130,
        "MAX_PAIRS_TO_TRADE": 3,
        "description": "Contrarian trading based on market sentiment"
    },
    
    "volume_surge": {
        "STRATEGY": "volume_surge",
        "VOLUME_SURGE_THRESHOLD": 1.8,
        "AGGRESSIVE_ROTATION": True,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 3,
        "SLEEP_INTERVAL": 45,
        "BASE_ORDER_VOLUME": 110,
        "MAX_PAIRS_TO_TRADE": 4,
        "description": "News-driven trading on volume spikes"
    },
    
    "hybrid_aggressive": {
        "STRATEGY": "hybrid_aggressive",
        "AGGRESSIVE_ROTATION": True,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 2,
        "SLEEP_INTERVAL": 30,
        "BASE_ORDER_VOLUME": 150,
        "MAX_PAIRS_TO_TRADE": 5,
        "MOMENTUM_THRESHOLD": 0.015,
        "FEAR_THRESHOLD": 30,
        "GREED_THRESHOLD": 70,
        "description": "🚀 MAXIMUM GROWTH: Combines all aggressive signals"
    },
    
    "breakout": {
        "STRATEGY": "breakout",
        "BREAKOUT_THRESHOLD": 0.01,
        "CONSOLIDATION_PERIODS": 20,
        "AGGRESSIVE_ROTATION": True,
        "CYCLES_WITHOUT_TRADE_AGGRESSIVE": 4,
        "SLEEP_INTERVAL": 45,
        "BASE_ORDER_VOLUME": 115,
        "MAX_PAIRS_TO_TRADE": 4,
        "description": "Trades breakouts from consolidation periods"
    }
}

def backup_current_config():
    """Backup the current bot_config.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"bot_config_backup_{timestamp}.py"
    
    if os.path.exists("bot_config.py"):
        shutil.copy2("bot_config.py", backup_file)
        print(f"📁 Current config backed up to: {backup_file}")
        return backup_file
    return None

def update_config_file(strategy_name, config):
    """Update bot_config.py with new strategy settings"""
    
    # Read current config
    with open("bot_config.py", "r") as f:
        lines = f.readlines()
    
    # Update lines
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        line_updated = False
        for key, value in config.items():
            if line.strip().startswith(f"{key} ="):
                if isinstance(value, str):
                    updated_lines.append(f'{key} = "{value}"\n')
                else:
                    updated_lines.append(f'{key} = {value}\n')
                updated_keys.add(key)
                line_updated = True
                break
        
        if not line_updated:
            updated_lines.append(line)
    
    # Add any missing keys
    for key, value in config.items():
        if key not in updated_keys and key != "description":
            if isinstance(value, str):
                updated_lines.append(f'{key} = "{value}"\n')
            else:
                updated_lines.append(f'{key} = {value}\n')
    
    # Write updated config
    with open("bot_config.py", "w") as f:
        f.writelines(updated_lines)

def show_strategies():
    """Display available strategies"""
    print("\n📊 Available Trading Strategies:")
    print("=" * 60)
    
    for i, (name, config) in enumerate(STRATEGIES.items(), 1):
        risk_level = "🟢 LOW" if name == "conservative" else "🟡 MEDIUM" if name in ["fear_greed"] else "🔴 HIGH"
        print(f"{i}. {name.upper()}")
        print(f"   Risk: {risk_level}")
        print(f"   {config['description']}")
        print(f"   Sleep: {config.get('SLEEP_INTERVAL', 60)}s, Pairs: {config.get('MAX_PAIRS_TO_TRADE', 3)}")
        print()

def main():
    """Main configuration switcher"""
    print("🎛️  Trading Strategy Configuration Switcher")
    print("=" * 50)
    
    show_strategies()
    
    try:
        choice = input("Enter strategy number (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            return
        
        strategy_names = list(STRATEGIES.keys())
        
        if choice.isdigit() and 1 <= int(choice) <= len(strategy_names):
            strategy_name = strategy_names[int(choice) - 1]
            config = STRATEGIES[strategy_name]
            
            print(f"\n🎯 Selected: {strategy_name.upper()}")
            print(f"Description: {config['description']}")
            
            # Show configuration details
            print(f"\nConfiguration details:")
            for key, value in config.items():
                if key != "description":
                    print(f"  {key}: {value}")
            
            confirm = input(f"\nApply this configuration? (y/N): ").strip().lower()
            
            if confirm == 'y':
                # Backup current config
                backup_file = backup_current_config()
                
                # Update config
                update_config_file(strategy_name, config)
                
                print(f"\n✅ Configuration updated successfully!")
                print(f"🚀 Strategy: {strategy_name.upper()}")
                print(f"📝 Backup saved: {backup_file}")
                print(f"\nTo start trading with this strategy:")
                print(f"  python multi_pair_trading_bot.py")
                
                # Show warning for aggressive strategies
                if strategy_name in ["hybrid_aggressive", "scalping", "momentum"]:
                    print(f"\n⚠️  WARNING: This is an aggressive strategy!")
                    print(f"   - Start with small BASE_ORDER_VOLUME")
                    print(f"   - Monitor closely for the first few hours")
                    print(f"   - Be prepared for higher volatility")
                    
            else:
                print("❌ Configuration not applied")
                
        else:
            print("❌ Invalid choice. Please enter a number from the list.")
            
    except KeyboardInterrupt:
        print("\n👋 Configuration cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
