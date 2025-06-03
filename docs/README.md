# Multi-Pair Trading Bot

A sophisticated Python trading bot that uses Luno's API to automatically place buy and sell orders across multiple trading pairs with intelligent portfolio management, advanced risk management, and comprehensive performance monitoring.

## Features

### Core Functionality
- **Multi-Pair Trading**: Dynamically discover and trade multiple cryptocurrency pairs simultaneously
- **Asset Discovery**: Intelligent pair discovery based on configured assets (ZAR, XBT, ETH, XRP, DOGE)
- **Pair Rotation System**: Automatically rotates through trading pairs to maximize opportunities
- **Position-Based Filtering**: Only evaluates pairs where you have holdings in at least one asset
- **Fee-Aware Trading**: Calculates fees to prevent insufficient funds errors
- **Comprehensive Logging**: Detailed logging with emoji-based indicators and JSON-formatted error responses

### Advanced Trading Strategies
1. **Mean Reversion Strategy**: Trades based on price deviation from historical average
2. **Conservative Strategy**: Only trades when spread conditions are favorable
3. **Momentum Strategy**: Trades based on price momentum and trend analysis
4. **Scalping Strategy**: Quick profit-taking trades with tight margins
5. **Breakout Strategy**: Trades breakouts from consolidation patterns
6. **Fear & Greed Strategy**: Uses market sentiment indicators for timing
7. **Volume Surge Strategy**: Trades based on volume anomalies
8. **Hybrid Aggressive Strategy**: Combines multiple strategies for aggressive trading

### Risk Management System
- **Stop Loss & Take Profit**: Automatic position exits at configurable levels (5% stop loss, 15% take profit)
- **Position Size Management**: Limits position sizes to 30% of portfolio value
- **Dynamic Risk Adjustment**: Adjusts risk parameters based on market volatility
- **Real-time Risk Monitoring**: Continuous monitoring of all open positions
- **Risk Exit Execution**: Automatic execution of risk management orders

### Performance Monitoring
- **Portfolio Tracking**: Real-time portfolio value and allocation monitoring
- **Trade Performance**: Detailed tracking of all trades with P&L analysis
- **Growth Metrics**: Progress tracking toward doubling goal (100% growth target)
- **Win Rate Analysis**: Comprehensive statistics on trading success rates
- **Performance Snapshots**: Regular portfolio snapshots for trend analysis

### Portfolio Management
- **Dynamic Asset Discovery**: Automatically discovers valid trading pairs from configured assets
- **Intelligent Allocation**: Configurable weights for each asset converted to pair weights
- **Automatic Rebalancing**: Rebalances portfolio when allocations deviate from targets
- **Real-time Monitoring**: Continuous portfolio value and allocation tracking
- **Multi-Asset Support**: Supports fiat (ZAR), major cryptocurrencies (XBT, ETH), and altcoins (XRP, DOGE)

## Configuration

The bot is configured through `config/trading/bot_config.py`. Key configuration options:

```python
# Multi-pair trading mode
ENABLE_MULTI_PAIR = True  # Set to False for single-pair mode
FILTER_PAIRS_BY_HOLDINGS = True  # Only trade pairs where you have holdings

# Asset Configuration
TRADING_ASSETS = ["ZAR", "XBT", "ETH", "XRP", "DOGE"]
ASSET_WEIGHTS = {
    "ZAR": 0.05,    # Keep some ZAR as base currency
    "XBT": 0.35,    # Bitcoin - largest allocation
    "ETH": 0.25,    # Ethereum - second largest
    "XRP": 0.1,     # Smaller positions
    "DOGE": 0.15,
    "SOL": 0.1,
}

# Trading Strategy Configuration
STRATEGY = "hybrid_aggressive"  # Primary strategy
BASE_ORDER_VOLUME = 100  # Base volume in ZAR equivalent

# Risk Management
ENABLE_RISK_MANAGEMENT = True
STOP_LOSS_PCT = 0.05      # 5% stop loss
TAKE_PROFIT_PCT = 0.15    # 15% take profit
MAX_POSITION_SIZE_PCT = 0.3  # Max 30% of portfolio per position

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING = True
DOUBLING_TARGET = 1.0  # 100% growth target
PERFORMANCE_LOG_INTERVAL = 10  # Log every 10 cycles

# Pair Evaluation Criteria
MIN_VOLUME_24H = 1000      # Minimum 24h volume
MIN_SPREAD_TO_TRADE = 0.001  # Minimum spread (0.1%)
MAX_PAIRS_TO_TRADE = 5     # Maximum simultaneous pairs
PORTFOLIO_BALANCE_THRESHOLD = 0.1  # 10% deviation triggers rebalancing

# Aggressive Rotation Settings
AGGRESSIVE_ROTATION = True
CYCLES_WITHOUT_TRADE_AGGRESSIVE = 1  # Rotate after 1 cycle without trades
```

## Usage

### Quick Start
1. **Configure your credentials** in `config/environment.env`:
   ```bash
   LUNO_API_KEY_ID=your_api_key_id
   LUNO_API_SECRET=your_api_secret
   ```

2. **Run the bot**:
   ```bash
   python run_bot.py
   ```

### Advanced Usage

#### Performance Testing
Run comprehensive performance tests:
```bash
python tests/performance_test_runner.py
python tests/stress_test_runner.py
```

#### Optimization Analysis
Run advanced optimization tests:
```bash
python tests/advanced_optimization_test.py
```

#### Environment Switching
Switch between staging and production:
- Edit `config/environment.env` to set `LUNO_ENVIRONMENT=staging` or `LUNO_ENVIRONMENT=production`

## Architecture

### Core Components

1. **MultiPairTradingBot** (`src/core/multi_pair_trading_bot.py`)
   - Main trading engine with risk management and performance monitoring
   - Handles multi-pair discovery, rotation, and execution
   - Integrates all subsystems

2. **Risk Manager** (`src/core/risk_manager.py`)
   - Position tracking and risk level monitoring
   - Automatic stop loss and take profit execution
   - Dynamic risk parameter adjustment based on market volatility

3. **Performance Monitor** (`src/core/performance_monitor.py`)
   - Real-time performance tracking and portfolio snapshots
   - Trade history and P&L analysis
   - Progress tracking toward growth targets

4. **Portfolio Manager** (`src/core/portfolio_manager.py`)
   - Portfolio allocation and rebalancing logic
   - Multi-asset value calculation and conversion
   - Balance management across trading pairs

5. **Trading Pair Discovery** (`src/utils/trading_pair_discovery.py`)
   - Dynamic discovery of valid trading pairs
   - Pair evaluation and scoring based on volume/spread criteria
   - Asset weight conversion to pair weights

### Trading Strategies

All strategies are located in `src/strategies/trading_strategies.py`:

- **MeanReversionStrategy**: Trades price deviations from moving averages
- **ConservativeStrategy**: Only trades when spreads exceed thresholds
- **MomentumStrategy**: Follows price momentum trends
- **ScalpingStrategy**: Quick profit-taking with tight margins
- **BreakoutStrategy**: Trades breakouts from consolidation
- **FearGreedStrategy**: Uses market sentiment indicators
- **VolumeSurgeStrategy**: Trades volume anomalies
- **HybridAggressiveStrategy**: Combines multiple approaches

## Performance Optimization

The bot includes several performance optimizations:

### Speed Optimizations
- **Reduced Logging Frequency**: Market data and balances logged every 10 cycles instead of every cycle
- **Eliminated Unnecessary Delays**: Removed delays between pair processing for faster cycles
- **Intelligent Caching**: API response caching with 90% hit rate achieving 9.6x speedup
- **Concurrent Processing**: Parallel API calls with 2.5x speedup over sequential processing

### Memory Optimization
- **Stable Memory Usage**: Consistent ~35.6MB with minimal growth (+3.3MB over extended operation)
- **Efficient Data Structures**: Optimized data handling for long-running sessions
- **Garbage Collection**: Proper cleanup of temporary objects

### Performance Metrics
Based on recent stress testing:
- **Cycle Time**: Average 1.15s (87.8% improvement from 9.5s baseline)
- **API Performance**: 100% success rate, 0.24s average response time
- **Error Rate**: 0% across all stress test scenarios
- **Overall Grade**: A - Very Good (Score: 72.8/100)

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
/Users/raynohattingh/dev/bot/
├── run_bot.py                    # Main entry point
├── config/
│   ├── environment.env           # API credentials and environment settings
│   └── trading/
│       └── bot_config.py         # Main trading configuration
├── src/
│   ├── core/
│   │   ├── multi_pair_trading_bot.py    # Main trading engine
│   │   ├── luno_api.py                  # Luno API wrapper
│   │   ├── risk_manager.py              # Risk management system
│   │   ├── performance_monitor.py       # Performance tracking
│   │   └── portfolio_manager.py         # Portfolio management
│   ├── strategies/
│   │   └── trading_strategies.py        # All trading strategies
│   └── utils/
│       ├── trading_utils.py              # Utility functions
│       └── trading_pair_discovery.py    # Pair discovery system
├── tests/
│   ├── performance_test_runner.py       # Performance testing
│   ├── stress_test_runner.py            # Stress testing
│   └── advanced_optimization_test.py    # Optimization analysis
├── docs/                        # Documentation
└── logs/                        # Log files
```

## Configuration Files

### Main Configuration (`config/trading/bot_config.py`)
- Trading strategy selection and parameters
- Risk management settings
- Asset allocation and weights
- Performance monitoring configuration
- Pair discovery and rotation settings

### Environment Configuration (`config/environment.env`)
- API credentials (staging/production)
- Environment-specific settings
- External service configurations

## Monitoring and Logging

### Log Files
- `trading_bot.log`: Main trading activity log with emoji indicators
- `risk_management.log`: Risk management specific events
- `performance_data.json`: Portfolio performance snapshots
- `positions.json`: Active position tracking

### Real-time Monitoring
- Cycle-by-cycle trading activity
- Portfolio value and allocation tracking
- Risk management alerts and actions
- Performance metrics and goal progress

## Risk Management Features

### Position Monitoring
- Real-time P&L tracking for all open positions
- Automatic stop loss and take profit execution
- Position size limits based on portfolio percentage

### Dynamic Risk Adjustment
- Volatility-based risk parameter adjustment
- Market condition responsive position sizing
- Portfolio drawdown protection

### Risk Metrics
- Total portfolio exposure tracking
- Individual position performance
- Win rate and average P&L analysis

## API Integration

The bot integrates with Luno's API for:
- Getting market data (tickers, order books, fees)
- Placing and managing limit orders
- Retrieving account balances and transactions
- Monitoring order status and execution

### MCP Configuration
The bot can optionally use Luno's MCP (Model Context Protocol) server:
- Configure in `.vscode/mcp.json`
- Supports both staging and production environments
- Docker-based deployment available

## Troubleshooting

### Common Issues
1. **API Connection Issues**: Check credentials in `config/environment.env`
2. **Insufficient Balance**: Ensure adequate balances for minimum order sizes
3. **Pair Discovery Problems**: Verify asset configuration and holdings
4. **Permission Errors**: Ensure API keys have trading permissions

### Debug Mode
Enable debug logging by setting `LOG_LEVEL = "DEBUG"` in `bot_config.py`

### Performance Issues
- Monitor cycle times in logs
- Check API response times
- Review memory usage patterns
- Run stress tests to identify bottlenecks

### Error Recovery
- The bot includes automatic retry logic for API calls
- Graceful handling of network issues
- Comprehensive error logging with context

## Testing

### Unit Tests
Run the test suite to validate functionality:
```bash
python tests/test_bot_integration.py
python tests/test_multi_pair.py
python tests/test_orders_simple.py
```

### Performance Testing
```bash
# Quick performance test
python tests/performance_test_runner.py

# Comprehensive stress testing
python tests/stress_test_runner.py --level standard

# Advanced optimization analysis
python tests/advanced_optimization_test.py
```

### Mock Testing
Use mock data for safe testing:
```bash
python tests/test_mock_performance.py
```

## Security Considerations

### API Key Management
- Store credentials in environment variables only
- Never commit credentials to version control
- Use staging environment for testing
- Rotate API keys regularly

### Risk Controls
- Start with small position sizes
- Monitor continuously during initial deployment
- Set appropriate stop losses and take profits
- Have manual override procedures ready

## Performance Benchmarks

### Recent Test Results
- **Initialization Time**: 5.75s average
- **Cycle Processing**: 1.15s average (87.8% improvement)
- **Memory Usage**: Stable at ~35.6MB
- **API Success Rate**: 100% over extended testing
- **Error Rate**: 0% in stress testing scenarios

### Optimization Achievements
- **API Caching**: 90% hit rate, 9.6x speedup
- **Concurrent Processing**: 2.5x speedup over sequential
- **Memory Efficiency**: <5% growth over 2+ minute runs

## Future Roadmap

### Planned Enhancements
- Additional trading strategies
- Enhanced backtesting framework
- Real-time alerts and notifications
- Advanced portfolio analytics
- Machine learning integration

### Research Areas
- Sentiment analysis integration
- Cross-exchange arbitrage
- Options trading strategies
- DeFi yield farming integration

## Support and Community

For technical support:
1. Review the comprehensive logging output
2. Check configuration against this documentation
3. Run diagnostic tests to identify issues
4. Analyze performance metrics for optimization opportunities

## License and Disclaimer

This trading bot is provided for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss. Use at your own risk and never trade with funds you cannot afford to lose.
