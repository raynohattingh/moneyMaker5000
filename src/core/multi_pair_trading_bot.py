import time
import logging
import json
import time
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add paths for configuration and other modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../config/trading'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../strategies'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))

from luno_api import LunoAPI, LimitOrderSide, OrderState, OrderType
from trading_utils import parse_trading_pair, LOG_EMOJI
import config.trading.bot_config as bot_config_module
import config.trading.bot_config as bot_config_module

# Get configuration values
ENABLE_MULTI_PAIR = bot_config_module.ENABLE_MULTI_PAIR
TRADING_ASSETS = getattr(bot_config_module, 'TRADING_ASSETS', [])
ASSET_WEIGHTS = getattr(bot_config_module, 'ASSET_WEIGHTS', {})
BASE_ORDER_VOLUME = getattr(bot_config_module, 'BASE_ORDER_VOLUME', 10)
MIN_ORDER_SIZE_BY_ASSET = getattr(bot_config_module, 'MIN_ORDER_SIZE_BY_ASSET', {})
SLEEP_INTERVAL = bot_config_module.SLEEP_INTERVAL
LOG_FILE = bot_config_module.LOG_FILE
LOG_LEVEL = bot_config_module.LOG_LEVEL
STRATEGY = bot_config_module.STRATEGY
DEVIATION_THRESHOLD = bot_config_module.DEVIATION_THRESHOLD
MIN_SPREAD_PCT = bot_config_module.MIN_SPREAD_PCT
MIN_VOLUME_24H = getattr(bot_config_module, 'MIN_VOLUME_24H', 1000000)
MIN_SPREAD_TO_TRADE = getattr(bot_config_module, 'MIN_SPREAD_TO_TRADE', 0.002)
MAX_PAIRS_TO_TRADE = getattr(bot_config_module, 'MAX_PAIRS_TO_TRADE', 10)
PORTFOLIO_BALANCE_THRESHOLD = getattr(bot_config_module, 'PORTFOLIO_BALANCE_THRESHOLD', 0.05)
PAIR = bot_config_module.PAIR
ORDER_VOLUME = bot_config_module.ORDER_VOLUME
REBALANCE_COUNTER = getattr(bot_config_module, 'REBALANCE_COUNTER', 5)
MAX_CYCLES_WITHOUT_TRADE = getattr(bot_config_module, 'MAX_CYCLES_WITHOUT_TRADE', 10)
FILTER_PAIRS_BY_HOLDINGS = getattr(bot_config_module, 'FILTER_PAIRS_BY_HOLDINGS', True)
MOMENTUM_THRESHOLD = bot_config_module.MOMENTUM_THRESHOLD
MOMENTUM_LOOKBACK = bot_config_module.MOMENTUM_LOOKBACK
SCALPING_MIN_PROFIT = bot_config_module.SCALPING_MIN_PROFIT
BREAKOUT_THRESHOLD = bot_config_module.BREAKOUT_THRESHOLD
CONSOLIDATION_PERIODS = bot_config_module.CONSOLIDATION_PERIODS
FEAR_THRESHOLD = bot_config_module.FEAR_THRESHOLD
GREED_THRESHOLD = bot_config_module.GREED_THRESHOLD
VOLUME_SURGE_THRESHOLD = bot_config_module.VOLUME_SURGE_THRESHOLD
AGGRESSIVE_ROTATION = getattr(bot_config_module, 'AGGRESSIVE_ROTATION', False)
CYCLES_WITHOUT_TRADE_AGGRESSIVE = getattr(bot_config_module, 'CYCLES_WITHOUT_TRADE_AGGRESSIVE', 3)
# Risk management and performance monitoring imports
ENABLE_RISK_MANAGEMENT = bot_config_module.ENABLE_RISK_MANAGEMENT
ENABLE_PERFORMANCE_MONITORING = bot_config_module.ENABLE_PERFORMANCE_MONITORING
STOP_LOSS_PCT = bot_config_module.STOP_LOSS_PCT
TAKE_PROFIT_PCT = bot_config_module.TAKE_PROFIT_PCT
MAX_POSITION_SIZE_PCT = bot_config_module.MAX_POSITION_SIZE_PCT
RISK_CHECK_INTERVAL = bot_config_module.RISK_CHECK_INTERVAL
VOLATILITY_LOOKBACK_PERIODS = bot_config_module.VOLATILITY_LOOKBACK_PERIODS
MIN_VOLATILITY_THRESHOLD = bot_config_module.MIN_VOLATILITY_THRESHOLD
MAX_VOLATILITY_THRESHOLD = bot_config_module.MAX_VOLATILITY_THRESHOLD
DOUBLING_TARGET = bot_config_module.DOUBLING_TARGET
PERFORMANCE_LOG_INTERVAL = bot_config_module.PERFORMANCE_LOG_INTERVAL
PERFORMANCE_DATA_FILE = bot_config_module.PERFORMANCE_DATA_FILE
TRADE_HISTORY_FILE = bot_config_module.TRADE_HISTORY_FILE
POSITIONS_FILE = bot_config_module.POSITIONS_FILE
RISK_LOG_FILE = bot_config_module.RISK_LOG_FILE
ASSET_DISCOVERY = getattr(bot_config_module, 'ASSET_DISCOVERY', 'api_based')
from trading_strategies import (
    MeanReversionStrategy, ConservativeStrategy, MomentumStrategy, ScalpingStrategy, 
    BreakoutStrategy, FearGreedStrategy, VolumeSurgeStrategy, HybridAggressiveStrategy
)
from portfolio_manager import PortfolioManager
from trading_pair_discovery import TradingPairDiscovery
from risk_manager import RiskManager
from performance_monitor import PerformanceMonitor

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class MultiPairTradingBot:
    def __init__(self):
        self.luno = LunoAPI()
        self.portfolio_manager = PortfolioManager(self.luno)
        
        # Create discovery configuration
        discovery_config = {
            'method': ASSET_DISCOVERY,
            'max_pairs_to_test': 50,
            'rate_limit_ms': 150,
            'timeout_seconds': 10,
            'asset_categories': {
                'fiat_currencies': ['ZAR', 'USD', 'EUR', 'GBP'],
                'stablecoins': ['USDT', 'USDC'],
                'major_cryptos': ['XBT', 'ETH', 'ADA', 'XRP'],
                'alt_cryptos': ['LTC', 'BCH', 'DOGE']
            }
        }
        self.pair_discovery = TradingPairDiscovery(self.luno, discovery_config)
        
        # Initialize risk management and performance monitoring
        if ENABLE_RISK_MANAGEMENT:
            self.risk_manager = RiskManager(
                luno=self.luno,
                stop_loss_pct=STOP_LOSS_PCT,
                take_profit_pct=TAKE_PROFIT_PCT
            )
            # Update additional risk parameters after initialization
            self.risk_manager.max_position_size_pct = MAX_POSITION_SIZE_PCT
            logging.info("Risk management system initialized")
        else:
            self.risk_manager = None
            
        print("DEBUG: Initializing performance monitoring...")
        if ENABLE_PERFORMANCE_MONITORING:
            self.performance_monitor = PerformanceMonitor(
                data_file=PERFORMANCE_DATA_FILE
            )
            logging.info("Performance monitoring system initialized")
        else:
            self.performance_monitor = None
        
        self.strategies = {}
        self.active_pairs = []
        self.valid_pairs = {}  # Discovered valid trading pairs
        self.pair_weights = {}  # Dynamic pair weights
        self.rebalance_counter = 0  # Counter to manage rebalancing frequency
        self.cycle_counter = 0  # Track total cycles for performance monitoring
        
        # Pair rotation system
        self.all_evaluated_pairs = []  # All pairs sorted by score
        self.rotation_index = 0  # Current position in rotation
        self.cycles_since_last_trade = 0  # Track cycles without trading activity
        
        # Use aggressive rotation if enabled
        if AGGRESSIVE_ROTATION:
            self.max_cycles_without_trade = CYCLES_WITHOUT_TRADE_AGGRESSIVE
            logging.info(f"Aggressive rotation enabled: will rotate after {self.max_cycles_without_trade} cycles without trades")
        else:
            self.max_cycles_without_trade = MAX_CYCLES_WITHOUT_TRADE
        
        # Discover trading pairs from assets
        if ENABLE_MULTI_PAIR:
            logging.info("Multi-pair trading mode enabled - discovering trading pairs...")
            self.valid_pairs = self.pair_discovery.discover_valid_pairs(TRADING_ASSETS)
            self.pair_weights = self.pair_discovery.convert_asset_weights_to_pair_weights(ASSET_WEIGHTS)
            self.pair_discovery.log_discovery_summary()
            self.setup_multi_pair_strategies()
        else:
            logging.info("Single-pair trading mode enabled")
            self.setup_single_pair_strategy()

    def setup_single_pair_strategy(self):
        """Setup strategy for single pair trading (legacy mode)"""
        pair = PAIR
        volume = ORDER_VOLUME
        
        strategy = self._create_strategy(pair, volume)
        self.strategies[pair] = strategy
        self.active_pairs = [pair]

    def _create_strategy(self, pair: str, volume: float):
        """Create a strategy instance based on configuration"""
        if STRATEGY == "mean_reversion":
            strategy = MeanReversionStrategy(pair, volume, DEVIATION_THRESHOLD)
            logging.info(f"Created Mean Reversion Strategy for {pair} with deviation threshold: {DEVIATION_THRESHOLD}")
        elif STRATEGY == "conservative":
            strategy = ConservativeStrategy(pair, volume, MIN_SPREAD_PCT)
            logging.info(f"Created Conservative Strategy for {pair} with min spread: {MIN_SPREAD_PCT}")
        elif STRATEGY == "momentum":
            strategy = MomentumStrategy(pair, volume, MOMENTUM_THRESHOLD, MOMENTUM_LOOKBACK)
            logging.info(f"Created Momentum Strategy for {pair} with threshold: {MOMENTUM_THRESHOLD}")
        elif STRATEGY == "scalping":
            strategy = ScalpingStrategy(pair, volume, SCALPING_MIN_PROFIT)
            logging.info(f"Created Scalping Strategy for {pair} with min profit: {SCALPING_MIN_PROFIT}")
        elif STRATEGY == "breakout":
            strategy = BreakoutStrategy(pair, volume, BREAKOUT_THRESHOLD, CONSOLIDATION_PERIODS)
            logging.info(f"Created Breakout Strategy for {pair} with threshold: {BREAKOUT_THRESHOLD}")
        elif STRATEGY == "fear_greed":
            strategy = FearGreedStrategy(pair, volume, FEAR_THRESHOLD, GREED_THRESHOLD)
            logging.info(f"Created Fear & Greed Strategy for {pair} (fear<={FEAR_THRESHOLD}, greed>={GREED_THRESHOLD})")
        elif STRATEGY == "volume_surge":
            strategy = VolumeSurgeStrategy(pair, volume, VOLUME_SURGE_THRESHOLD)
            logging.info(f"Created Volume Surge Strategy for {pair} with threshold: {VOLUME_SURGE_THRESHOLD}")
        elif STRATEGY == "hybrid_aggressive":
            strategy = HybridAggressiveStrategy(pair, volume)
            logging.info(f"Created Hybrid Aggressive Strategy for {pair}")
        else:
            raise ValueError(f"Unknown strategy: {STRATEGY}")
        
        return strategy

    def setup_multi_pair_strategies(self):
        """Setup strategies for multiple pairs with rotation system"""
        logging.info("Evaluating trading pairs...")
        self.all_evaluated_pairs = self.evaluate_trading_pairs()
        
        # Select current batch of pairs to trade
        self.select_current_trading_pairs()
        
        logging.info(f"Selected pairs for trading (rotation {self.rotation_index}): {self.active_pairs}")
        logging.info(f"Total discovered pairs: {len(self.all_evaluated_pairs)}")
        
        # Setup strategies for each selected pair
        for pair in self.active_pairs:
            volume = self.calculate_pair_volume(pair)
            strategy = self._create_strategy(pair, volume)
            self.strategies[pair] = strategy

    def select_current_trading_pairs(self):
        """Select current batch of pairs to trade based on rotation"""
        if not self.all_evaluated_pairs:
            logging.warning("No evaluated pairs available for selection")
            return
        
        total_pairs = len(self.all_evaluated_pairs)
        start_idx = self.rotation_index * MAX_PAIRS_TO_TRADE
        end_idx = min(start_idx + MAX_PAIRS_TO_TRADE, total_pairs)
        
        # If we've reached the end, wrap around to the beginning
        if start_idx >= total_pairs:
            self.rotation_index = 0
            start_idx = 0
            end_idx = min(MAX_PAIRS_TO_TRADE, total_pairs)
        
        selected_pairs = self.all_evaluated_pairs[start_idx:end_idx]
        self.active_pairs = [pair for pair, _ in selected_pairs]
        
        logging.info(f"Pair rotation: batch {self.rotation_index + 1} of {(total_pairs + MAX_PAIRS_TO_TRADE - 1) // MAX_PAIRS_TO_TRADE}")
        logging.info(f"Trading pairs {start_idx + 1}-{end_idx} out of {total_pairs} total pairs")

    def advance_pair_rotation(self):
        """Advance to the next batch of trading pairs"""
        old_pairs = self.active_pairs.copy()
        self.rotation_index += 1
        
        # Re-select pairs based on new rotation index
        self.select_current_trading_pairs()
        
        # Clear existing strategies and setup new ones
        self.strategies.clear()
        for pair in self.active_pairs:
            volume = self.calculate_pair_volume(pair)
            strategy = self._create_strategy(pair, volume)
            self.strategies[pair] = strategy
        
        logging.info(f"🔄 PAIR ROTATION: Advanced from {old_pairs} to {self.active_pairs}")
        self.cycles_since_last_trade = 0

    def evaluate_trading_pairs(self) -> List[Tuple[str, float]]:
        """Evaluate and rank trading pairs based on profitability criteria"""
        pair_scores = []
        
        # Get current balances to filter pairs by holdings (if enabled)
        current_balances = {}
        if FILTER_PAIRS_BY_HOLDINGS:
            try:
                current_balances = self.portfolio_manager.get_all_balances(list(self.valid_pairs.keys()))
                logging.info(f"Position filtering enabled. Current holdings: {list(current_balances.keys())}")
            except Exception as e:
                logging.error(f"Error getting balances for pair filtering: {e}")
                current_balances = {}
        else:
            logging.info("Position filtering disabled - evaluating all discovered pairs")
        
        pairs_evaluated = 0
        pairs_filtered_out = 0
        
        for pair in self.valid_pairs.keys():
            try:
                # Parse pair to get base and quote currencies
                base_currency, quote_currency = self.parse_trading_pair(pair)
                
                # Apply position-based filtering if enabled
                if FILTER_PAIRS_BY_HOLDINGS:
                    has_base = current_balances.get(base_currency, 0) > 0
                    has_quote = current_balances.get(quote_currency, 0) > 0
                    
                    if not (has_base or has_quote):
                        # Skip this pair - we don't have any holdings in either asset
                        logging.debug(f"Filtering out {pair} - no holdings in {base_currency} or {quote_currency}")
                        pairs_filtered_out += 1
                        continue
                
                # Get cached pair info from discovery
                pair_info = self.valid_pairs[pair]['info']
                
                ask = pair_info.get('ask', 0)
                bid = pair_info.get('bid', 0) 
                volume_24h = pair_info.get('volume_24h', 0)
                spread = pair_info.get('spread', 0)
                
                # Score based on volume and spread
                score = 0
                if volume_24h >= MIN_VOLUME_24H:
                    score += 1
                if spread >= MIN_SPREAD_TO_TRADE:
                    score += 1
                
                # Bonus for higher spreads (more profitable)
                score += min(spread * 1000, 2) # Cap bonus at 2 points
                
                # Bonus for having both assets vs just one (if filtering enabled)
                if FILTER_PAIRS_BY_HOLDINGS and current_balances:
                    has_base = current_balances.get(base_currency, 0) > 0
                    has_quote = current_balances.get(quote_currency, 0) > 0
                    
                    if has_base and has_quote:
                        score += 0.5  # Small bonus for having both assets
                        logging.debug(f"Bonus for {pair} - holdings in both {base_currency} and {quote_currency}")
                
                # Weight by configured pair weight
                if pair in self.pair_weights:
                    score *= self.pair_weights[pair]
                
                pair_scores.append((pair, score))
                pairs_evaluated += 1
                
                # Create holding status for logging (only if filtering enabled)
                holding_status = ""
                if FILTER_PAIRS_BY_HOLDINGS and current_balances:
                    has_base = current_balances.get(base_currency, 0) > 0
                    has_quote = current_balances.get(quote_currency, 0) > 0
                    
                    if has_base and has_quote:
                        holding_status = f"(holdings: {base_currency}✓ {quote_currency}✓)"
                    elif has_base:
                        holding_status = f"(holdings: {base_currency}✓)"
                    elif has_quote:
                        holding_status = f"(holdings: {quote_currency}✓)"
                
                logging.info(f"Pair {pair}: spread={spread:.4f}, volume_24h={volume_24h}, score={score:.2f} {holding_status}")
                
            except Exception as e:
                logging.error(f"Error evaluating pair {pair}: {e}")
                pair_scores.append((pair, 0))
                pairs_evaluated += 1
        
        # Sort by score (highest first)
        pair_scores.sort(key=lambda x: x[1], reverse=True)
        
        logging.info(f"📊 Pair evaluation summary: {pairs_evaluated} pairs evaluated, {pairs_filtered_out} pairs filtered out (no holdings)")
        
        return pair_scores

    def calculate_pair_volume(self, pair: str) -> float:
        """Calculate trading volume for a specific pair based on allocation"""
        if pair not in self.pair_weights:
            # Use minimum order size based on base currency
            base_currency, _ = self.parse_trading_pair(pair)
            return MIN_ORDER_SIZE_BY_ASSET.get(base_currency, 0.001)
        
        # Base volume adjusted by pair weight
        volume = BASE_ORDER_VOLUME * self.pair_weights[pair]
        
        # Ensure minimum order size based on base currency
        base_currency, _ = self.parse_trading_pair(pair)
        min_size = MIN_ORDER_SIZE_BY_ASSET.get(base_currency, 0.001)
        return max(volume, min_size)

    def get_portfolio_allocation(self) -> Dict[str, float]:
        """Get current portfolio allocation using portfolio manager"""
        try:
            portfolio_values, total_value = self.portfolio_manager.get_portfolio_value_in_zar(self.active_pairs)
            allocations = self.portfolio_manager.calculate_allocation_percentages(portfolio_values, total_value)
            return allocations
        except Exception as e:
            logging.error(f"Error calculating portfolio allocation: {e}")
            return {}

    def should_rebalance_portfolio(self) -> bool:
        """Check if portfolio needs rebalancing using portfolio manager"""
        try:
            portfolio_values, total_value = self.portfolio_manager.get_portfolio_value_in_zar(self.active_pairs)
            current_allocations = self.portfolio_manager.calculate_allocation_percentages(portfolio_values, total_value)
            
            # Check if any pair deviates significantly from target
            for pair in self.active_pairs:
                base_currency, quote_currency = self.parse_trading_pair(pair)
                
                current_pct = current_allocations.get(base_currency, 0)
                target_pct = self.pair_weights.get(pair, 0) * 100
                deviation = abs(current_pct - target_pct)
                
                if deviation > PORTFOLIO_BALANCE_THRESHOLD * 100:
                    logging.info(f"Portfolio rebalancing needed: {base_currency} has {current_pct:.1f}% vs target {target_pct:.1f}%")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking portfolio balance: {e}")
            return False

    def execute_portfolio_rebalancing(self):
        """Execute portfolio rebalancing using portfolio manager"""
        try:
            portfolio_values, total_value = self.portfolio_manager.get_portfolio_value_in_zar(self.active_pairs)
            current_allocations = self.portfolio_manager.calculate_allocation_percentages(portfolio_values, total_value)
            
            # Get rebalancing actions
            actions = self.portfolio_manager.get_rebalancing_actions(
                current_allocations, 
                self.pair_weights, 
                total_value,
                threshold=PORTFOLIO_BALANCE_THRESHOLD * 100
            )
            
            if actions:
                logging.info(f"Executing {len(actions)} rebalancing trades...")
                
                for action in actions[:2]:  # Limit to 2 rebalancing trades per cycle
                    success = self.portfolio_manager.execute_rebalancing_trade(action, self.active_pairs)
                    if success:
                        logging.info(f"Rebalancing trade executed: {action['action']} {action['currency']}")
                    time.sleep(2)  # Small delay between rebalancing trades
            else:
                logging.info("No rebalancing actions needed")
                
        except Exception as e:
            logging.error(f"Error executing portfolio rebalancing: {e}")

    def trade_pair(self, pair: str):
        """Execute trading logic for a specific pair with risk management"""
        try:
            strategy = self.strategies[pair]
            trading_activity = False  # Track if any trades were placed this cycle
            
            # Parse the trading pair to get base and quote currencies
            base_currency, quote_currency = self.parse_trading_pair(pair)
            
            # Get market data
            ticker = self.luno.get_ticker(pair)
            ask = float(ticker['ask'])
            bid = float(ticker['bid'])
            last_trade = float(ticker['last_trade'])
            
            # Reduced logging frequency for speed optimization
            if self.cycle_counter % 10 == 0:  # Log market data every 10 cycles
                logging.info(f"{pair} - Ask: {ask}, Bid: {bid}, Last: {last_trade}")
            
            # Update strategy with latest price
            strategy.update_price_history(last_trade)
            
            # Risk management: check positions and execute risk exits if needed
            if self.risk_manager:
                # Check if we need to exit due to stop loss or take profit
                risk_level = self.risk_manager.check_risk_levels(pair, last_trade)
                if risk_level:
                    success = self.risk_manager.execute_risk_exit(pair, last_trade, risk_level)
                    if success:
                        trading_activity = True
                        # Record the trade in performance monitor
                        if self.performance_monitor:
                            # The position is already closed by execute_risk_exit, so record the exit
                            self._record_completed_trade(pair, last_trade, risk_level)
                        return trading_activity
            
            # Get balances for both currencies
            base_balance = self.luno.get_balance(base_currency)
            quote_balance = self.luno.get_balance(quote_currency)
            
            balance_data = {base_currency: base_balance, quote_currency: quote_currency}
            # Reduced logging frequency for speed optimization
            if self.cycle_counter % 10 == 0:  # Log balances every 10 cycles
                logging.info(f"{pair} - Balances: {base_currency}={base_balance}, {quote_currency}={quote_balance}")
            
            # Get fee information
            fee_info = self.luno.get_fee(pair)
            taker_fee = float(fee_info.get('taker_fee', 0))
            maker_fee = float(fee_info.get('maker_fee', 0))
            
            # Get open orders for this pair
            try:
                orders_list = self.luno.get_orders_safe(pair=pair)
                
                open_sell_orders = [o for o in orders_list 
                                  if o['type'] == OrderType.ASK and o['state'] == OrderState.PENDING]
                open_buy_orders = [o for o in orders_list 
                                 if o['type'] == OrderType.BID and o['state'] == OrderState.PENDING]
                
            except Exception as e:
                logging.error(f"{pair} - Error getting orders: {e}")
                open_sell_orders = []
                open_buy_orders = []

            # SELL LOGIC (sell base currency for quote currency)
            if open_sell_orders:
                logging.info(f"{pair} - Open SELL order(s): {[o['order_id'] for o in open_sell_orders]}")
            else:
                if strategy.should_sell(last_trade, balance_data):
                    volume = strategy.order_volume
                    
                    # Risk management: check position size limits
                    if self.risk_manager:
                        portfolio_value = self._get_portfolio_value()
                        max_position_value = self.risk_manager.calculate_max_position_size(portfolio_value)
                        position_value = volume * last_trade
                        
                        if position_value > max_position_value:
                            volume = max_position_value / last_trade
                            logging.info(f"{pair} - Position size adjusted by risk management: {volume} {base_currency}")
                    
                    min_base_needed = volume * (1 + abs(taker_fee))
                    
                    if base_balance >= min_base_needed:
                        sell_price = strategy.get_sell_price(bid, ask)
                        logging.info(f"{pair} - Strategy recommends SELL: {volume} {base_currency} at {sell_price} {quote_currency}")
                        
                        try:
                            result = self.luno.place_limit_order(pair, sell_price, volume, LimitOrderSide.ASK)
                            logging.info(f"{LOG_EMOJI['TRADE_SELL']} {pair} - SELL order placed: {result}")
                            trading_activity = True
                            
                            # Risk management: open new position
                            if self.risk_manager:
                                self.risk_manager.open_position(
                                    pair=pair,
                                    entry_price=sell_price,
                                    volume=volume,
                                    side='short',  # Selling is a short position
                                    order_id=result.get('order_id') if result else None
                                )
                            
                            # Performance monitoring: record trade entry (we'll update with exit later)
                            if self.performance_monitor:
                                # Store trade entry info for later completion
                                self._store_trade_entry(pair, 'sell', sell_price, volume, STRATEGY, abs(taker_fee) * volume * sell_price)
                                
                        except Exception as e:
                            self._log_order_error(f"{pair} SELL", e)
                    else:
                        logging.info(f"{pair} - Insufficient {base_currency} balance for sell (need {min_base_needed:.6f}, have {base_balance:.6f})")
            
            # BUY LOGIC (buy base currency with quote currency)
            if open_buy_orders:
                logging.info(f"{pair} - Open BUY order(s): {[o['order_id'] for o in open_buy_orders]}")
            else:
                if strategy.should_buy(last_trade, balance_data):
                    volume = strategy.order_volume
                    buy_price = strategy.get_buy_price(bid, ask)
                    
                    # Risk management: check position size limits
                    if self.risk_manager:
                        portfolio_value = self._get_portfolio_value()
                        max_position_value = self.risk_manager.calculate_max_position_size(portfolio_value)
                        position_value = volume * buy_price
                        
                        if position_value > max_position_value:
                            volume = max_position_value / buy_price
                            logging.info(f"{pair} - Position size adjusted by risk management: {volume} {base_currency}")
                    
                    required_quote = volume * buy_price * (1 + abs(taker_fee))
                    
                    if quote_balance >= required_quote:
                        logging.info(f"{pair} - Strategy recommends BUY: {volume} {base_currency} with {required_quote:.6f} {quote_currency}")
                        
                        try:
                            result = self.luno.place_limit_order(pair, buy_price, volume, LimitOrderSide.BID)
                            logging.info(f"{pair} - BUY order placed: {result}")
                            trading_activity = True
                            
                            # Risk management: open new position
                            if self.risk_manager:
                                self.risk_manager.open_position(
                                    pair=pair,
                                    entry_price=buy_price,
                                    volume=volume,
                                    side='long',  # Buying is a long position
                                    order_id=result.get('order_id') if result else None
                                )
                            
                            # Performance monitoring: record trade entry (we'll update with exit later)
                            if self.performance_monitor:
                                # Store trade entry info for later completion
                                self._store_trade_entry(pair, 'buy', buy_price, volume, STRATEGY, abs(taker_fee) * required_quote)
                                
                        except Exception as e:
                            self._log_order_error(f"{pair} BUY", e)
                    else:
                        logging.info(f"{pair} - Insufficient {quote_currency} balance for buy (need {required_quote:.6f}, have {quote_balance:.6f})")
            
            return trading_activity
                        
        except Exception as e:
            logging.error(f"Error trading pair {pair}: {e}")
            return False

    def _log_order_error(self, order_type: str, exception: Exception):
        """Helper method to log order placement errors with formatted API responses"""
        if hasattr(exception, 'response') and hasattr(exception.response, 'text'):
            try:
                error_json = exception.response.json()
                formatted_error = json.dumps(error_json, indent=2)
                logging.error(f"Failed to place {order_type} order: {exception}. API response: {formatted_error}")
            except Exception:
                logging.error(f"Failed to place {order_type} order: {exception}. API response: {exception.response.text}")
        else:
            logging.error(f"Failed to place {order_type} order: {exception}")

    def _store_trade_entry(self, pair: str, side: str, entry_price: float, volume: float, strategy: str, fees: float):
        """Store trade entry information for later completion tracking"""
        # For now, we'll store this in a simple dictionary
        # In a full implementation, this could be stored in a database or file
        if not hasattr(self, '_pending_trades'):
            self._pending_trades = {}
        
        self._pending_trades[pair] = {
            'side': side,
            'entry_price': entry_price,
            'volume': volume,
            'strategy': strategy,
            'fees': fees,
            'entry_time': time.time()
        }
        
        logging.info(f"📊 Trade entry stored: {pair} {side.upper()} at {entry_price:.2f}")
    
    def _record_completed_trade(self, pair: str, exit_price: float, exit_reason: str):
        """Record a completed trade when it's closed by risk management"""
        try:
            if not self.performance_monitor:
                return
                
            # Get pending trade info
            if hasattr(self, '_pending_trades') and pair in self._pending_trades:
                trade_info = self._pending_trades[pair]
                
                # Calculate duration
                duration_minutes = (time.time() - trade_info['entry_time']) / 60
                
                # Record completed trade
                self.performance_monitor.record_trade(
                    pair=pair,
                    entry_price=trade_info['entry_price'],
                    exit_price=exit_price,
                    volume=trade_info['volume'],
                    side=trade_info['side'],
                    strategy=f"{trade_info['strategy']} ({exit_reason})",
                    duration_minutes=duration_minutes,
                    fees_paid=trade_info['fees']
                )
                
                # Remove from pending trades
                del self._pending_trades[pair]
                
                logging.info(f"✅ Trade completed and recorded: {pair} {exit_reason}")
            else:
                logging.warning(f"No pending trade found for {pair} to complete")
                
        except Exception as e:
            logging.error(f"Error recording completed trade for {pair}: {e}")
    
    def _get_portfolio_value(self) -> float:
        """Get total portfolio value in ZAR for risk management"""
        try:
            if ENABLE_MULTI_PAIR:
                portfolio_values, total_value = self.portfolio_manager.get_portfolio_value_in_zar(self.active_pairs)
                return total_value
            else:
                # Simple single pair portfolio value estimation
                base_currency, quote_currency = self.parse_trading_pair(PAIR)
                base_balance = self.luno.get_balance(base_currency)
                quote_balance = self.luno.get_balance(quote_currency)
                
                # Convert to ZAR (simplified)
                if quote_currency == 'ZAR':
                    ticker = self.luno.get_ticker(PAIR)
                    last_price = float(ticker['last_trade'])
                    return (base_balance * last_price) + quote_balance
                else:
                    return base_balance + quote_balance  # Fallback
                    
        except Exception as e:
            logging.error(f"Error getting portfolio value: {e}")
            return 1000.0  # Fallback value

    def run(self):
        """Main trading loop with integrated risk management and performance monitoring"""
        logging.info("Starting multi-pair trading bot with risk management and performance monitoring...")
        # Initialize performance monitoring session
        if self.performance_monitor:
            initial_portfolio_value = self._get_portfolio_value()
            self.performance_monitor.set_initial_portfolio_value(initial_portfolio_value)
            logging.info(f"Performance monitoring started with initial portfolio value: {initial_portfolio_value:.2f} ZAR")
        
        # Initial portfolio status
        if ENABLE_MULTI_PAIR:
            self.portfolio_manager.log_portfolio_status(self.active_pairs)
        
        while True:
            try:
                # Increment counters
                self.rebalance_counter += 1
                self.cycle_counter += 1
                cycle_had_trades = False  # Track if this cycle had any trading activity
                
                logging.info(f"Cycle {self.cycle_counter} (rebalance: {self.rebalance_counter}) - Active pairs: {self.active_pairs}")
                
                # Risk management: check all positions periodically
                if (self.risk_manager and 
                    ENABLE_RISK_MANAGEMENT and 
                    self.cycle_counter % RISK_CHECK_INTERVAL == 0):
                    
                    logging.info("Performing risk management check...")
                    risk_exits = 0
                    
                    for pair in self.active_pairs:
                        try:
                            ticker = self.luno.get_ticker(pair)
                            current_price = float(ticker['last_trade'])
                            
                            # Check for risk exits
                            risk_level = self.risk_manager.check_risk_levels(pair, current_price)
                            if risk_level:
                                success = self.risk_manager.execute_risk_exit(pair, current_price, risk_level)
                                if success:
                                    risk_exits += 1
                                    cycle_had_trades = True
                                    
                                    # Record trade completion
                                    if self.performance_monitor:
                                        self._record_completed_trade(pair, current_price, risk_level)
                                            
                        except Exception as e:
                            logging.error(f"Error during risk check for {pair}: {e}")
                    
                    if risk_exits > 0:
                        logging.info(f"Risk management executed {risk_exits} exits this cycle")
                
                # Performance monitoring: update portfolio snapshots and display summary
                if (self.performance_monitor and 
                    ENABLE_PERFORMANCE_MONITORING and 
                    self.cycle_counter % PERFORMANCE_LOG_INTERVAL == 0):
                    
                    current_portfolio_value = self._get_portfolio_value()
                    current_allocations = self.get_portfolio_allocation()
                    
                    # Record portfolio snapshot
                    self.performance_monitor.record_portfolio_snapshot(current_portfolio_value, current_allocations)
                    
                    # Get performance metrics and display compact summary
                    performance_metrics = self.performance_monitor.get_performance_metrics()
                    doubling_achieved, growth_pct = self.performance_monitor.is_doubling_goal_achieved()
                    
                    logging.info(f"📊 Performance Summary:")
                    logging.info(f"   💰 Portfolio: {current_portfolio_value:.2f} ZAR")
                    logging.info(f"   📈 Growth: {growth_pct:+.2f}% (Target: +100%)")
                    logging.info(f"   🎯 Progress to Doubling: {min(growth_pct, 100.0):.1f}%")
                    logging.info(f"   🏆 Win Rate: {performance_metrics.win_rate_pct:.1f}%")
                    logging.info(f"   📊 Total Trades: {performance_metrics.total_trades}")
                    logging.info(f"   💵 Total P&L: {performance_metrics.total_pnl_zar:+.2f} ZAR")
                    
                    if doubling_achieved:
                        logging.info(f"   🎉 DOUBLING GOAL ACHIEVED! ({growth_pct:.1f}% growth)")
                    
                    # Save performance data to disk
                    self.performance_monitor.save_data()
                
                # Check portfolio allocation and rebalance periodically
                if ENABLE_MULTI_PAIR and self.rebalance_counter >= REBALANCE_COUNTER:
                    self.rebalance_counter = 0
                    
                    if self.should_rebalance_portfolio():
                        logging.info("Executing portfolio rebalancing...")
                        self.execute_portfolio_rebalancing()
                    
                    # Log portfolio status periodically
                    self.portfolio_manager.log_portfolio_status(self.active_pairs)
                
                # Trade each active pair and track activity (optimized)
                for pair in self.active_pairs:
                    pair_had_trade = self.trade_pair(pair)
                    if pair_had_trade:
                        cycle_had_trades = True
                    # Removed unnecessary delay between pairs for speed optimization
                
                # Update cycles without trades counter
                if cycle_had_trades:
                    self.cycles_since_last_trade = 0
                    logging.info("✅ Trading activity detected this cycle")
                else:
                    self.cycles_since_last_trade += 1
                    logging.info(f"⏳ No trades this cycle ({self.cycles_since_last_trade}/{self.max_cycles_without_trade} cycles without trades)")
                
                # Check if we should rotate pairs due to inactivity
                if (ENABLE_MULTI_PAIR and 
                    self.cycles_since_last_trade >= self.max_cycles_without_trade and 
                    len(self.all_evaluated_pairs) > MAX_PAIRS_TO_TRADE):
                    
                    logging.info(f"🔄 Rotating pairs due to {self.cycles_since_last_trade} cycles without trading activity")
                    self.advance_pair_rotation()
                
            except Exception as e:
                logging.error(f"Main loop error: {e}")
            
            time.sleep(SLEEP_INTERVAL)

    def parse_trading_pair(self, pair: str) -> tuple:
        """Parse trading pair to get base and quote currencies"""
        return parse_trading_pair(pair)

def main():
    bot = MultiPairTradingBot()
    bot.run()

if __name__ == "__main__":
    main()
