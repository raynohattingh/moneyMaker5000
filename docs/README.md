# Multi-Pair Trading Bot

A sophisticated Python trading bot that uses Luno's MCP (Model Context Protocol) tools to automatically place buy and sell orders across multiple trading pairs with intelligent portfolio management.

## Features

### Core Functionality
- **Multi-Pair Trading**: Trade multiple cryptocurrency pairs simultaneously (USDTZAR, XBTZAR, ETHZAR)
- **Strategy-Based Trading**: Configurable trading strategies (Mean Reversion, Conservative)
- **Portfolio Management**: Automatic portfolio rebalancing and allocation management
- **Smart Pair Selection**: Evaluates pairs based on volume, spread, and profitability
- **Fee-Aware Trading**: Calculates fees to prevent insufficient funds errors
- **Comprehensive Logging**: Detailed logging with JSON-formatted error responses

### Trading Strategies
1. **Mean Reversion Strategy**: Trades based on price deviation from historical average
2. **Conservative Strategy**: Only trades when spread conditions are favorable

### Portfolio Management
- **Dynamic Allocation**: Configurable weights for each trading pair
- **Automatic Rebalancing**: Rebalances portfolio when allocations deviate from targets
- **Risk Management**: Minimum order sizes and maximum pair limits
- **Real-time Monitoring**: Continuous portfolio value and allocation tracking

## Configuration

Edit `bot_config.py` to customize the bot behavior:

```python
# Multi-pair trading mode
ENABLE_MULTI_PAIR = True  # Set to False for single-pair mode

# Trading pairs and their allocations
TRADING_PAIRS = ["USDTZAR", "XBTZAR", "ETHZAR"]
PAIR_WEIGHTS = {
    "USDTZAR": 0.4,  # 40% allocation
    "XBTZAR": 0.4,   # 40% allocation  
    "ETHZAR": 0.2    # 20% allocation
}

# Trading strategy
STRATEGY = "mean_reversion"  # or "conservative"
BASE_ORDER_VOLUME = 100      # Base volume in ZAR equivalent

# Risk management
MAX_PAIRS_TO_TRADE = 3
MIN_SPREAD_TO_TRADE = 0.001  # 0.1% minimum spread
PORTFOLIO_BALANCE_THRESHOLD = 0.1  # 10% deviation triggers rebalancing
```

## Usage

### Testing the Setup
Before running the bot, test all functionality:
```bash
python test_multi_pair.py
```

### Running the Bot

**Multi-Pair Mode (Recommended):**
```bash
python multi_pair_trading_bot.py
```

**Single-Pair Mode:**
```bash
# Set ENABLE_MULTI_PAIR = False in bot_config.py
python simple_trading_bot.py
```

## File Structure

```
├── multi_pair_trading_bot.py    # Main multi-pair trading bot
├── simple_trading_bot.py        # Original single-pair bot
├── portfolio_manager.py         # Portfolio management and rebalancing
├── trading_strategies.py        # Trading strategy implementations
├── luno_api.py                 # Luno API wrapper with MCP tools
├── bot_config.py               # Configuration settings
├── test_multi_pair.py          # Test suite for validation
└── trading_bot.log             # Log file
```

## How It Works

### 1. Pair Evaluation
The bot evaluates trading pairs based on:
- 24-hour trading volume
- Bid-ask spread
- Configured pair weights
- Market conditions

### 2. Strategy Execution
For each selected pair, the bot:
- Updates price history for strategy calculations
- Checks current balances and open orders
- Applies buy/sell logic based on the selected strategy
- Places orders with fee-adjusted volumes

### 3. Portfolio Management
- Monitors portfolio allocation vs. target weights
- Triggers rebalancing when deviations exceed threshold
- Executes rebalancing trades to maintain target allocation
- Logs comprehensive portfolio status

### 4. Risk Management
- Minimum order sizes prevent dust trades
- Fee calculations avoid insufficient funds errors
- Maximum pair limits control complexity
- Spread requirements ensure profitability

## Sample Output

```
2025-05-30 10:15:30 INFO Multi-pair trading mode enabled
2025-05-30 10:15:31 INFO Evaluating trading pairs...
2025-05-30 10:15:32 INFO Pair USDTZAR: spread=0.0011, volume_24h=809995.05, score=1.24
2025-05-30 10:15:33 INFO Selected pairs for trading: ['USDTZAR', 'ETHZAR', 'XBTZAR']
2025-05-30 10:15:34 INFO Setup Mean Reversion Strategy for USDTZAR with volume: 40.0
2025-05-30 10:15:35 INFO Portfolio Summary:
2025-05-30 10:15:35 INFO   Total Value: 413.93 ZAR
2025-05-30 10:15:35 INFO   Positions: 3
2025-05-30 10:15:35 INFO   USDT: 183.03 ZAR (44.2%)
2025-05-30 10:15:35 INFO   ETH: 215.68 ZAR (52.1%)
```

## Advanced Features

### Portfolio Rebalancing
The bot automatically rebalances the portfolio when allocations deviate from targets:
- Monitors allocation percentages vs. configured weights
- Executes buy/sell orders to restore target allocation
- Limits rebalancing frequency to avoid overtrading

### Multi-Strategy Support
Easily extend with new trading strategies:
```python
class MyCustomStrategy(TradingStrategy):
    def should_buy(self, current_price, balance_data):
        # Your buy logic here
        return True
    
    def should_sell(self, current_price, balance_data):
        # Your sell logic here  
        return True
```

### Error Handling
- Comprehensive error logging with API response details
- Graceful handling of network issues and API errors
- Automatic retry logic for transient failures

## Monitoring

The bot provides extensive logging:
- Trade execution details
- Portfolio allocation changes
- Strategy decision rationale
- Error messages with API responses
- Performance metrics

Log files are written to `trading_bot.log` with both file and console output.

## Safety Notes

- **Start with small amounts**: Test thoroughly before deploying significant capital
- **Monitor actively**: Keep an eye on the bot's performance and market conditions
- **Set appropriate limits**: Configure reasonable order volumes and risk parameters
- **Backup strategy**: Have a plan for manual intervention if needed

## Requirements

- Python 3.7+
- Luno account with API access
- Required Python packages (see requirements.txt)
- Sufficient account balance for trading

## Support

For issues or questions:
1. Check the logs for error details
2. Run the test suite to validate configuration
3. Review the configuration settings
4. Ensure API connectivity and permissions
