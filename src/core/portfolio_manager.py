import logging
from typing import Dict, List, Tuple, Optional, Set
from luno_api import LunoAPI, LimitOrderSide
from trading_utils import parse_trading_pair, LOG_EMOJI

class PortfolioManager:
    def __init__(self, luno_api: LunoAPI):
        self.luno = luno_api
        self._discovered_currencies: Set[str] = set()
        
    def extract_currencies_from_pairs(self, trading_pairs: List[str]) -> Set[str]:
        """Extract all unique currencies from trading pairs"""
        currencies = set()
        
        for pair in trading_pairs:
            base, quote = self._parse_trading_pair(pair)
            currencies.add(base)
            currencies.add(quote)
            
        self._discovered_currencies = currencies
        return currencies
        
    def get_all_balances(self, trading_pairs: List[str] = None) -> Dict[str, float]:
        """Get all non-zero balances for currencies discovered from trading pairs"""
        balances = {}
        
        # If trading pairs provided, extract currencies from them
        if trading_pairs:
            currencies = self.extract_currencies_from_pairs(trading_pairs)
        else:
            # Use previously discovered currencies or fallback to common ones
            currencies = self._discovered_currencies or {'ZAR', 'USDT', 'USDC', 'XBT', 'ETH', 'XRP', 'LTC', 'BCH'}
        
        for currency in currencies:
            try:
                balance = self.luno.get_balance(currency)
                if balance > 0:
                    balances[currency] = balance
            except Exception as e:
                # Currency might not exist in account or not supported
                logging.debug(f"Could not get balance for {currency}: {e}")
                
        return balances
    
    def get_portfolio_value_in_zar(self, trading_pairs: List[str]) -> Tuple[Dict[str, float], float]:
        """Calculate portfolio value in ZAR for all holdings"""
        balances = self.get_all_balances(trading_pairs)
        portfolio_values = {}
        total_value = 0
        
        # ZAR balance (base currency)
        zar_balance = balances.get('ZAR', 0)
        portfolio_values['ZAR'] = zar_balance
        total_value += zar_balance
        
        # Convert other currencies to ZAR
        for currency, balance in balances.items():
            if currency == 'ZAR' or balance <= 0:
                continue
                
            # Find appropriate trading pair to convert to ZAR
            pair = self._find_trading_pair(currency, trading_pairs)
            if pair:
                try:
                    ticker = self.luno.get_ticker(pair)
                    price = float(ticker['last_trade'])
                    
                    # Parse pair to understand conversion direction
                    base_curr, quote_curr = self._parse_trading_pair(pair)
                    
                    if quote_curr == 'ZAR':
                        # Direct conversion: currency/ZAR
                        value_zar = balance * price
                    elif base_curr == 'ZAR':
                        # Inverse conversion: ZAR/currency
                        value_zar = balance / price if price > 0 else 0
                    else:
                        # Indirect conversion via USDT (if available)
                        value_zar = self._convert_via_bridge(currency, balance, trading_pairs)
                    
                    portfolio_values[currency] = value_zar
                    total_value += value_zar
                    logging.debug(f"{currency}: {balance} = {value_zar:.2f} ZAR (via {pair})")
                    
                except Exception as e:
                    logging.error(f"Error getting price for {pair}: {e}")
                    # Fallback: assume 0 value for unknown currencies
                    portfolio_values[currency] = 0
            else:
                logging.warning(f"No trading pair found for {currency}")
                portfolio_values[currency] = 0
                    
        return portfolio_values, total_value
    
    def _find_trading_pair(self, currency: str, trading_pairs: List[str]) -> Optional[str]:
        """Find the appropriate trading pair for a currency"""
        # Priority order: ZAR pairs first, then USDT pairs
        quote_priorities = ['ZAR', 'USDT', 'USDC', 'XBT', 'ETH']
        
        for quote in quote_priorities:
            for pair in trading_pairs:
                base, quote_curr = self._parse_trading_pair(pair)
                if base == currency and quote_curr == quote:
                    return pair
                # Also check reverse pairs (e.g., ZARXBT)
                if quote_curr == currency and base == quote:
                    return pair
                        
        return None
    
    def _parse_trading_pair(self, pair: str) -> tuple:
        """Parse trading pair to get base and quote currencies"""
        return parse_trading_pair(pair)
    
    def _convert_via_bridge(self, currency: str, balance: float, trading_pairs: List[str]) -> float:
        """Convert currency to ZAR via bridge currency (USDT)"""
        try:
            # Step 1: Convert currency to USDT
            currency_usdt_pair = self._find_pair_with_quote(currency, 'USDT', trading_pairs)
            if not currency_usdt_pair:
                return 0
            
            ticker1 = self.luno.get_ticker(currency_usdt_pair)
            base1, quote1 = self._parse_trading_pair(currency_usdt_pair)
            
            if base1 == currency:
                usdt_value = balance * float(ticker1['last_trade'])
            else:
                usdt_value = balance / float(ticker1['last_trade'])
            
            # Step 2: Convert USDT to ZAR
            usdt_zar_pair = self._find_pair_with_quote('USDT', 'ZAR', trading_pairs)
            if not usdt_zar_pair:
                return 0
                
            ticker2 = self.luno.get_ticker(usdt_zar_pair)
            zar_value = usdt_value * float(ticker2['last_trade'])
            
            logging.debug(f"Bridge conversion: {balance} {currency} -> {usdt_value:.6f} USDT -> {zar_value:.2f} ZAR")
            return zar_value
            
        except Exception as e:
            logging.error(f"Error in bridge conversion for {currency}: {e}")
            return 0
    
    def _find_pair_with_quote(self, base: str, quote: str, trading_pairs: List[str]) -> Optional[str]:
        """Find a trading pair with specific base and quote currencies"""
        for pair in trading_pairs:
            pair_base, pair_quote = self._parse_trading_pair(pair)
            if pair_base == base and pair_quote == quote:
                return pair
        return None
    
    def calculate_allocation_percentages(self, portfolio_values: Dict[str, float], 
                                       total_value: float) -> Dict[str, float]:
        """Calculate current allocation percentages"""
        allocations = {}
        for currency, value in portfolio_values.items():
            allocations[currency] = (value / total_value * 100) if total_value > 0 else 0
        return allocations
    
    def get_rebalancing_actions(self, current_allocations: Dict[str, float], 
                               target_weights: Dict[str, float], 
                               total_value: float,
                               threshold: float = 5.0) -> List[Dict]:
        """
        Determine what trades are needed to rebalance portfolio
        
        Args:
            current_allocations: Current % allocation by currency
            target_weights: Target % allocation by currency (pair -> weight)
            total_value: Total portfolio value in ZAR
            threshold: Rebalancing threshold in percentage points
            
        Returns:
            List of rebalancing actions: [{'action': 'buy/sell', 'pair': 'XBTZAR', 'amount': 1000}]
        """
        actions = []
        
        # Convert pair weights to currency weights and find available trading pairs
        currency_targets = {}
        currency_to_pairs = {}
        
        for pair, weight in target_weights.items():
            # Parse the trading pair to get base and quote currencies
            base_currency, quote_currency = self._parse_trading_pair(pair)
            
            # Store the currency target weight
            currency_targets[base_currency] = weight * 100  # Convert to percentage
            
            # Map currency to its trading pairs for later lookup
            if base_currency not in currency_to_pairs:
                currency_to_pairs[base_currency] = []
            currency_to_pairs[base_currency].append(pair)
        
        # Calculate deviations and required actions
        for currency, target_pct in currency_targets.items():
            # Try both the original currency and its mapped version for lookups
            current_pct = current_allocations.get(currency, 0)
            
            deviation = current_pct - target_pct
            
            if abs(deviation) > threshold:
                # Find the best trading pair for this currency
                available_pairs = currency_to_pairs.get(currency, [])
                
                if not available_pairs:
                    logging.warning(f"No trading pairs found for currency {currency}")
                    continue
                
                # Choose the first available pair (could be enhanced with preference logic)
                # Priority: ZAR pairs first, then USDT, then others
                pair = None
                for pref_quote in ['ZAR', 'USDT', 'USDC', 'XBT']:
                    for candidate_pair in available_pairs:
                        _, quote = self._parse_trading_pair(candidate_pair)
                        if quote == pref_quote:
                            pair = candidate_pair
                            break
                    if pair:
                        break
                
                # If no preferred pair found, use the first available
                if not pair:
                    pair = available_pairs[0]
                
                # Calculate amount difference
                target_value = (target_pct / 100) * total_value
                current_value = current_allocations.get(currency, 0) / 100 * total_value
                amount_difference = target_value - current_value
                
                # Get quote currency for this pair to determine amount currency
                _, quote_currency = self._parse_trading_pair(pair)
                
                # Convert amount difference to quote currency if not ZAR
                if quote_currency != 'ZAR':
                    # Convert ZAR amount to quote currency for proper trading
                    amount_quote = self._convert_amount_to_quote_currency(
                        abs(amount_difference), quote_currency, list(target_weights.keys())
                    )
                    amount_key = 'amount_quote'
                else:
                    amount_quote = abs(amount_difference)
                    amount_key = 'amount_zar'  # Keep for compatibility
                
                action = {
                    'pair': pair,
                    'currency': currency,
                    'quote_currency': quote_currency,
                    'current_pct': current_pct,
                    'target_pct': target_pct,
                    'deviation': deviation,
                    amount_key: amount_quote,
                    'action': 'buy' if amount_difference > 0 else 'sell'
                }
                actions.append(action)
                
                logging.info(f"Rebalancing needed for {currency} via {pair}: "
                           f"current {current_pct:.1f}% vs target {target_pct:.1f}% "
                           f"(deviation: {deviation:.1f}%)")
        
        # Sort by largest deviation first
        actions.sort(key=lambda x: abs(x['deviation']), reverse=True)
        return actions
    
    def execute_rebalancing_trade(self, action: Dict, trading_pairs: List[str], valid_pairs: Dict[str, Dict]) -> bool:
        """
        Execute a single rebalancing trade
        
        Args:
            action: Rebalancing action from get_rebalancing_actions()
            trading_pairs: List of available trading pairs
            
        Returns:
            True if trade was executed successfully, False otherwise
        """
        try:
            pair = action['pair']
            if pair not in trading_pairs:
                logging.error(f"Trading pair {pair} not in current active pairs {trading_pairs}")
                return False
            
            # Get current market data
            ticker = self.luno.get_ticker(pair)
            ask = float(ticker['ask'])
            bid = float(ticker['bid'])
            
            # Parse the trading pair to understand quote currency
            base_currency, quote_currency = self._parse_trading_pair(pair)
            quote_currency = action.get('quote_currency', quote_currency)
            
            # Get the amount to trade (could be in ZAR or quote currency)
            if 'amount_quote' in action:
                trade_amount = action['amount_quote']
                amount_in_quote = True
            else:
                trade_amount = action['amount_zar']
                amount_in_quote = (quote_currency == 'ZAR')
            
            if action['action'] == 'buy':
                # Buy the base currency (sell quote currency)
                # Use ask price (we're taking liquidity)
                if amount_in_quote:
                    # Amount is already in quote currency
                    required_quote = trade_amount
                    volume = required_quote / ask
                else:
                    # Amount is in ZAR, need to convert
                    volume = trade_amount / ask
                    required_quote = volume * ask
                
                # Check if we have enough quote currency
                quote_balance = self.luno.get_balance(quote_currency)
                
                if quote_balance < required_quote:
                    logging.warning(f"Insufficient {quote_currency} balance for rebalancing buy: need {required_quote:.6f}, have {quote_balance:.6f}")
                    return False
                
                price = ask * 0.999  # Slightly below ask to ensure order fills
                
                logging.info(f"Rebalancing BUY: {volume:.6f} {action['currency']} with {required_quote:.6f} {quote_currency} at {price}")
                result = self.luno.place_limit_order(pair, price, volume, LimitOrderSide.BID)
                
            else:  # sell
                # Sell the base currency (get quote currency)
                base_currency = action['currency']
                
                if amount_in_quote:
                    # Amount is in quote currency - calculate volume needed
                    expected_quote = trade_amount
                    volume = expected_quote / bid
                else:
                    # Amount is in ZAR
                    volume = trade_amount / bid
                    expected_quote = volume * bid
                
                price = bid * 1.001  # Slightly above bid
                
                # Check if we have enough of the base currency
                base_balance = self.luno.get_balance(base_currency)
                if base_balance < volume:
                    logging.warning(f"Insufficient {base_currency} balance for rebalancing sell: need {volume:.6f}, have {base_balance:.6f}")
                    return False
                
                logging.info(f"Rebalancing SELL: {volume:.6f} {base_currency} for {expected_quote:.6f} {quote_currency} at {price}")
                result = self.luno.place_limit_order(pair, price, volume, LimitOrderSide.ASK)
            
            logging.info(f"Rebalancing order placed: {result}")
            return True
        
        except Exception as e:
            logging.error(f"Error executing rebalancing trade: {e}")
            return False
    
    def get_portfolio_summary(self, trading_pairs: List[str]) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            portfolio_values, total_value = self.get_portfolio_value_in_zar(trading_pairs)
            allocations = self.calculate_allocation_percentages(portfolio_values, total_value)
            
            # Get actual asset balances (not converted to ZAR)
            actual_balances = self.get_all_balances(trading_pairs)
            
            # Calculate conversion rates for display
            conversion_rates = {}
            for currency in actual_balances.keys():
                conversion_rates[currency] = self._get_zar_conversion_rate(currency, trading_pairs)
            
            summary = {
                'total_value_zar': total_value,
                'holdings_zar': portfolio_values,  # Values in ZAR
                'holdings_actual': actual_balances,  # Actual asset amounts
                'conversion_rates': conversion_rates,  # ZAR per unit
                'allocations_pct': allocations,
                'num_positions': len([v for v in portfolio_values.values() if v > 0])
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating portfolio summary: {e}")
            return {}
    
    def log_portfolio_status(self, trading_pairs: List[str]):
        """Log current portfolio status with both actual balances and ZAR values"""
        summary = self.get_portfolio_summary(trading_pairs)
        
        if summary:
            logging.info(f"📊 Portfolio Summary:")
            logging.info(f"  💰 Total Value: {summary['total_value_zar']:.2f} ZAR")
            logging.info(f"  📈 Active Positions: {summary['num_positions']}")
            logging.info(f"")
            logging.info(f"  Asset Holdings:")
            
            for currency, allocation in summary['allocations_pct'].items():
                if allocation > 0:  # Only show currencies with actual holdings
                    actual_balance = summary['holdings_actual'].get(currency, 0)
                    zar_value = summary['holdings_zar'].get(currency, 0)
                    conversion_rate = summary['conversion_rates'].get(currency, 1.0)
                    
                    if currency == 'ZAR':
                        logging.info(f"    💵 {currency}: {actual_balance:.2f} ZAR ({allocation:.1f}%)")
                    else:
                        logging.info(f"    🪙 {currency}: {actual_balance:.6f} = {zar_value:.2f} ZAR ({allocation:.1f}%) @ {conversion_rate:.2f} ZAR/{currency}")
            
            logging.info(f"")
    
    def _get_zar_conversion_rate(self, currency: str, trading_pairs: List[str]) -> float:
        """Get conversion rate from currency to ZAR"""
        try:
            if currency == 'ZAR':
                return 1.0
                
            pair = self._find_pair_with_quote(currency, 'ZAR', trading_pairs)
            if pair:
                ticker = self.luno.get_ticker(pair)
                return float(ticker['last_trade'])
            else:
                # Try bridge conversion via USDT
                if currency == 'USDT':
                    usdt_zar_pair = self._find_pair_with_quote('USDT', 'ZAR', trading_pairs)
                    if usdt_zar_pair:
                        ticker = self.luno.get_ticker(usdt_zar_pair)
                        return float(ticker['last_trade'])
                return 1.0  # Fallback
        except Exception:
            return 1.0
    
    def _convert_amount_to_quote_currency(self, amount_zar: float, target_quote: str, trading_pairs: List[str]) -> float:
        """Convert ZAR amount to target quote currency for rebalancing"""
        if target_quote == 'ZAR':
            return amount_zar
        
        try:
            # Find a trading pair to convert ZAR to target quote currency
            quote_zar_pair = self._find_pair_with_quote(target_quote, 'ZAR', trading_pairs)
            
            if quote_zar_pair:
                ticker = self.luno.get_ticker(quote_zar_pair)
                # If pair is QUOTEZAR, then price is in ZAR per QUOTE
                # amount_quote = amount_zar / price
                price = float(ticker['last_trade'])
                return amount_zar / price
            else:
                # Try via USDT bridge
                usdt_zar_pair = self._find_pair_with_quote('USDT', 'ZAR', trading_pairs)
                target_usdt_pair = self._find_pair_with_quote(target_quote, 'USDT', trading_pairs)
                
                if usdt_zar_pair and target_usdt_pair:
                    # Convert ZAR to USDT
                    usdt_zar_ticker = self.luno.get_ticker(usdt_zar_pair)
                    usdt_price = float(usdt_zar_ticker['last_trade'])
                    amount_usdt = amount_zar / usdt_price
                    
                    # Convert USDT to target currency
                    target_usdt_ticker = self.luno.get_ticker(target_usdt_pair)
                    target_price = float(target_usdt_ticker['last_trade'])
                    return amount_usdt / target_price
                
            logging.warning(f"Could not convert ZAR amount to {target_quote}, using ZAR equivalent")
            return amount_zar
            
        except Exception as e:
            logging.error(f"Error converting amount to {target_quote}: {e}")
            return amount_zar
