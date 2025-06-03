#!/usr/bin/env python3
"""
Aggressive Trading Configuration
Use this configuration to maximize growth potential
"""

# Copy this to your bot_config.py to enable aggressive trading

# AGGRESSIVE STRATEGY SETTINGS
# ============================

# 1. Choose an aggressive strategy
STRATEGY = "hybrid_aggressive"  # Recommended for maximum growth
# STRATEGY = "momentum"         # Good for trending markets
# STRATEGY = "scalping"         # Best for volatile markets
# STRATEGY = "fear_greed"       # Contrarian approach
# STRATEGY = "volume_surge"     # Trade on volume spikes

# 2. Aggressive rotation settings
AGGRESSIVE_ROTATION = True
CYCLES_WITHOUT_TRADE_AGGRESSIVE = 2  # Rotate every 2 cycles (very aggressive)
MAX_PAIRS_TO_TRADE = 5  # Trade more pairs simultaneously

# 3. Increase trading frequency
SLEEP_INTERVAL = 30  # Check every 30 seconds instead of 60

# 4. More aggressive thresholds
MOMENTUM_THRESHOLD = 0.015  # 1.5% instead of 2% (more sensitive)
SCALPING_MIN_PROFIT = 0.003  # 0.3% instead of 0.5% (take smaller profits)
BREAKOUT_THRESHOLD = 0.01   # 1% instead of 1.5% (catch smaller breakouts)
FEAR_THRESHOLD = 30         # Buy at moderate fear instead of extreme fear
GREED_THRESHOLD = 70        # Sell at moderate greed instead of extreme greed

# 5. Increase position sizes (be careful!)
BASE_ORDER_VOLUME = 150     # Increase from 100 to 150 ZAR equivalent
MAX_POSITION_SIZE_PCT = 0.4 # Up to 40% of portfolio per position

# 6. Enable all trading assets
TRADING_ASSETS = [
    "ZAR", "USDT", "USDC",
    "XBT", "ETH", "XRP", "LTC", "BCH", "ADA",
    "SOL", "DOGE", "TRX"  # Add more volatile assets
]

# 7. More balanced asset allocation
ASSET_WEIGHTS = {
    "ZAR": 0.05,    # Keep minimal ZAR
    "USDT": 0.15,   # Moderate stable coin
    "XBT": 0.25,    # Bitcoin
    "ETH": 0.20,    # Ethereum  
    "SOL": 0.10,    # High-growth potential
    "XRP": 0.10,    # Regulatory clarity
    "ADA": 0.05,    # Smaller position
    "LTC": 0.05,    # Diversification
    "DOGE": 0.05,   # Meme coin volatility
}

# 8. Aggressive rebalancing
REBALANCE_COUNTER = 1       # Rebalance every cycle
PORTFOLIO_BALANCE_THRESHOLD = 0.05  # Rebalance at 5% deviation

print("🚀 AGGRESSIVE TRADING CONFIGURATION LOADED")
print("⚠️  WARNING: This configuration is designed for maximum growth")
print("    but also carries higher risk. Start with small amounts!")
print(f"    Strategy: {STRATEGY}")
print(f"    Rotation: Every {CYCLES_WITHOUT_TRADE_AGGRESSIVE} cycles")
print(f"    Check interval: {SLEEP_INTERVAL} seconds")
print(f"    Max pairs: {MAX_PAIRS_TO_TRADE}")
