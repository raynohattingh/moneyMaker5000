# Single pair trading (legacy)
PAIR = "USDTZAR"  # Default pair for single-pair mode
ORDER_VOLUME = 10
SLEEP_INTERVAL = 10
LOG_FILE = "trading_bot.log"
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Trading Strategy Configuration
STRATEGY = "hybrid_aggressive"  # Options: "mean_reversion", "conservative", "momentum", "scalping", "breakout", "fear_greed", "volume_surge", "hybrid_aggressive"
DEVIATION_THRESHOLD = 0.005  # 0.5% for mean reversion strategy
MIN_SPREAD_PCT = 0.002  # 0.2% minimum spread for conservative strategy

# Aggressive strategy parameters
MOMENTUM_THRESHOLD = 0.02  # 2% momentum threshold for momentum strategy
MOMENTUM_LOOKBACK = 5  # periods to look back for momentum calculation
SCALPING_MIN_PROFIT = 0.005  # 0.5% minimum profit target for scalping
BREAKOUT_THRESHOLD = 0.015  # 1.5% breakout threshold
CONSOLIDATION_PERIODS = 20  # periods to determine consolidation
FEAR_THRESHOLD = 25  # Buy when fear index <= 25 (extreme fear)
GREED_THRESHOLD = 75  # Sell when fear index >= 75 (extreme greed)
VOLUME_SURGE_THRESHOLD = 2.0  # Volume surge multiplier

# Risk management for aggressive strategies
MAX_POSITION_SIZE_PCT = 0.3  # Max 30% of portfolio per position
STOP_LOSS_PCT = 0.05  # 5% stop loss
TAKE_PROFIT_PCT = 0.15  # 15% take profit

# Enhanced risk management parameters
ENABLE_RISK_MANAGEMENT = True  # Enable risk management system
ENABLE_PERFORMANCE_MONITORING = True  # Enable performance monitoring
RISK_CHECK_INTERVAL = 1  # Check risk every N cycles
VOLATILITY_LOOKBACK_PERIODS = 20  # Periods to calculate volatility for dynamic risk adjustment
MIN_VOLATILITY_THRESHOLD = 0.01  # Minimum volatility to trigger risk adjustment
MAX_VOLATILITY_THRESHOLD = 0.05  # Maximum volatility to trigger tighter risk controls

# Performance monitoring parameters
DOUBLING_TARGET = 1.0  # 100% growth target (doubling)
PERFORMANCE_LOG_INTERVAL = 10  # Log performance summary every N cycles
PERFORMANCE_DATA_FILE = "performance_data.json"  # File to store performance data
TRADE_HISTORY_FILE = "trade_history.json"  # File to store trade history

# Risk management data files
POSITIONS_FILE = "positions.json"  # File to store active positions
RISK_LOG_FILE = "risk_management.log"  # Risk management log file

# Multi-pair trading configuration
ENABLE_MULTI_PAIR = True  # Set to False to use single-pair mode

# Position-based filtering configuration
FILTER_PAIRS_BY_HOLDINGS = True  # Only evaluate pairs where we have holdings in at least one asset

# Assets we want to trade (pairs will be dynamically discovered)
TRADING_ASSETS = [
    # Fiat currency
    "ZAR",
    # Stablecoins
    # "USDT", "USDC", 
    # Major cryptocurrencies
    "XBT", "ETH", "XRP",
    # Alt coins (add more as needed)
    "DOGE"
]

# Asset Discovery Configuration
ASSET_DISCOVERY = 'config_based'  # Options: 'api_based', 'config_based', 'hybrid'

# Asset allocation weights (will be converted to pair weights dynamically)
ASSET_WEIGHTS = {
    "ZAR": 0.05,    # Keep some ZAR as base currency
    "XBT": 0.35,   # Bitcoin - largest allocation
    "ETH": 0.25,   # Ethereum - second largest
    "XRP": 0.1,   # Smaller positions in other cryptos
    "DOGE": 0.15,
    "SOL": 0.1,

    # Add more assets as needed, ensure total = 1.0
}

# Order volume per asset (will be adjusted by asset weights)
BASE_ORDER_VOLUME = 100  # Base volume in ZAR equivalent

# Minimum order sizes by asset (dynamic pair minimums will be calculated)
MIN_ORDER_SIZE_BY_ASSET = {
    "ZAR": 10,
    "USDT": 10,
    "USDC": 10,
    "XBT": 0.0001,
    "ETH": 0.001,
    "XRP": 1,
    "LTC": 0.01,
    "BCH": 0.001,
    "ADA": 1,
}

# Pair evaluation criteria
MIN_VOLUME_24H = 1000  # Minimum 24h volume to consider trading
MIN_SPREAD_TO_TRADE = 0.001  # Minimum spread (0.1%) to consider profitable
MAX_PAIRS_TO_TRADE = 5  # Maximum number of pairs to trade simultaneously
PORTFOLIO_BALANCE_THRESHOLD = 0.1  # Rebalance when allocation deviates by more than 10%

# Pair rotation system
REBALANCE_COUNTER = 1  # Rebalance every 5 cycles if needed
MAX_CYCLES_WITHOUT_TRADE = 4  # Advance to next pair set after this many cycles without trades

# Enhanced pair rotation for more opportunities
AGGRESSIVE_ROTATION = True  # Enable faster pair rotation
CYCLES_WITHOUT_TRADE_AGGRESSIVE = 1  # Rotate after 3 cycles instead of default

