import requests
from requests.auth import HTTPBasicAuth
import os
import logging
from typing import Dict, Tuple, Optional
from trading_utils import parse_trading_pair

class LunoAPI:
    def __init__(self, api_key=None, api_secret=None, environment=None):
        # Determine environment from parameter or environment variable
        self.environment = environment or os.getenv('ENV', 'PROD').upper()
        
        # Set API URLs based on environment
        if self.environment == 'DEV':
            self.base_url = 'https://api.staging.luno.com/api/1'
            self.exchange_base_url = 'https://api.staging.luno.com/api/exchange/1'
            # Use development credentials
            self.api_key = api_key or os.getenv('LUNO_API_KEY_ID_DEV')
            self.api_secret = api_secret or os.getenv('LUNO_API_SECRET_DEV')
            env_label = "STAGING/DEV"
        else:
            self.base_url = 'https://api.luno.com/api/1'
            self.exchange_base_url = 'https://api.luno.com/api/exchange/1'
            # Use production credentials
            self.api_key = api_key or os.getenv('LUNO_API_KEY_ID')
            self.api_secret = api_secret or os.getenv('LUNO_API_SECRET')
            env_label = "PRODUCTION"
        
        # Cache for market data to avoid repeated API calls
        self._market_cache = {}
        
        if not self.api_key or not self.api_secret:
            raise ValueError(f"LUNO API credentials are not set for {env_label} environment. "
                           f"Please set the appropriate environment variables.")
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info(f"LunoAPI initialized for {env_label} environment with dynamic market data support")
        
        if self.environment == 'DEV':
            logging.warning("⚠️  USING STAGING ENVIRONMENT - This is for testing only!")
        else:
            logging.info("✅ Using PRODUCTION environment")

    def get_order_book(self, pair):
        url = f"{self.base_url}/orderbook?pair={pair}"
        response = requests.get(url, timeout=10)  # 10 second timeout
        response.raise_for_status()
        return response.json()

    def get_ticker(self, pair):
        url = f"{self.base_url}/ticker?pair={pair}"
        response = requests.get(url, timeout=10)  # 10 second timeout
        response.raise_for_status()
        return response.json()

    def get_trades(self, pair, since=None):
        url = f"{self.base_url}/trades?pair={pair}"
        params = {}
        if since:
            params['since'] = since
        response = requests.get(url, params=params, timeout=10)  # 10 second timeout
        response.raise_for_status()
        return response.json()

    def list_orders(self, pair=None, limit=100, state=None):
        url = f"{self.base_url}/listorders"
        params = {'limit': limit}
        
        # Only add parameters if they're not None
        if pair is not None:
            params['pair'] = pair
        if state is not None:
            params['state'] = state
        
        response = requests.get(url, params=params, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        return response.json()

    def get_orders_safe(self, pair=None, limit=100, state=None):
        """Get orders with null-safe handling for the 'orders' field"""
        response = self.list_orders(pair, limit, state)
        orders_list = response.get('orders') if response else None
        return orders_list if orders_list is not None else []

    def cancel_order(self, order_id):
        url = f"{self.base_url}/stoporder"
        data = {'order_id': order_id}
        response = requests.post(url, data=data, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        return response.json()

    def get_transaction(self, account_id, transaction_id):
        url = f"{self.base_url}/accounts/{account_id}/transactions/{transaction_id}"
        response = requests.get(url, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        return response.json()

    def list_transactions(self, account_id, min_row=None, max_row=None):
        url = f"{self.base_url}/accounts/{account_id}/transactions"
        params = {}
        if min_row is not None:
            params['min_row'] = min_row
        if max_row is not None:
            params['max_row'] = max_row
        response = requests.get(url, params=params, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        return response.json()

    def validate_pair(self, pair):
        url = f"{self.base_url}/validate_pair"
        params = {'pair': pair}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_balance(self, asset):
        url = f"{self.base_url}/balance"
        response = requests.get(url, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        balances = response.json()['balance']
        for b in balances:
            if b['asset'] == asset:
                return float(b['balance'])
        return 0.0

    def place_limit_order(self, pair, price, volume, side):
        """
        Place limit order with dynamic validation and formatting
        """
        logging.info(f"🔄 Placing {side} order: {volume} {pair} @ {price}")
        
        try:
            # Validate and format using live market data
            formatted_price, formatted_volume, is_valid = self.validate_and_format_order(pair, price, volume)
            
            if not is_valid:
                raise ValueError(f"Order validation failed for {pair}")
            
            url = f"{self.base_url}/postorder"
            data = {
                'pair': pair,
                'type': side,
                'volume': formatted_volume,
                'price': formatted_price
            }
            
            logging.info(f"📤 Submitting order: {data}")
            
            response = requests.post(url, data=data, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=15)
            
            if response.status_code != 200:
                error_details = response.text
                logging.error(f"❌ Order failed with status {response.status_code}: {error_details}")
                
                # Parse Luno error for better user feedback
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    field_errors = error_data.get('field_errors', {})
                    
                    if field_errors:
                        field_details = ', '.join([f"{k}: {v}" for k, v in field_errors.items()])
                        logging.error(f"❌ Field validation errors: {field_details}")
                        
                except:
                    pass
                    
                response.raise_for_status()
            
            result = response.json()
            logging.info(f"✅ Order placed successfully: ID {result.get('order_id', 'N/A')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Network error placing order: {e}")
            raise
        except ValueError as e:
            logging.error(f"❌ Validation error: {e}")
            raise
        except Exception as e:
            logging.error(f"❌ Unexpected error placing order: {e}")
            raise

    def get_fee(self, pair):
        url = f"{self.base_url}/fee_info?pair={pair}"
        response = requests.get(url, auth=HTTPBasicAuth(self.api_key, self.api_secret), timeout=10)
        response.raise_for_status()
        return response.json()

    def get_tickers(self):
        """Get all available trading pairs and their latest ticker data"""
        url = f"{self.base_url}/tickers"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_available_pairs(self):
        """Get list of all available trading pairs"""
        tickers_data = self.get_tickers()
        return [ticker['pair'] for ticker in tickers_data.get('tickers', [])]
    
    def get_markets(self):
        """Get detailed market information including volume limits and precision"""
        try:
            url = f"{self.exchange_base_url}/markets"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching markets data: {e}")
            return {'markets': []}
    
    def get_market_info(self, pair: str) -> Dict:
        """Get specific market information for a trading pair"""
        try:
            # Check cache first
            if pair in self._market_cache:
                return self._market_cache[pair]
            
            markets_data = self.get_markets()
            
            for market in markets_data.get('markets', []):
                if market.get('market_id') == pair:
                    market_info = {
                        'pair': pair,
                        'min_volume': float(market.get('min_volume', 0)),
                        'max_volume': float(market.get('max_volume', 0)),
                        'volume_scale': int(market.get('volume_scale', 6)),
                        'price_scale': int(market.get('price_scale', 2)),
                        'fee_scale': int(market.get('fee_scale', 4)),
                        'trading_status': market.get('trading_status', 'UNKNOWN'),
                        'base_currency': market.get('base_currency', ''),
                        'counter_currency': market.get('counter_currency', ''),
                    }
                    
                    # Cache the result
                    self._market_cache[pair] = market_info
                    return market_info
            
            # Fallback to default limits if market not found
            logging.warning(f"Market info not found for {pair}, using default limits")
            return self._get_default_market_limits(pair)
            
        except Exception as e:
            logging.error(f"Error fetching market info for {pair}: {e}")
            return self._get_default_market_limits(pair)
    
    def _get_default_market_limits(self, pair: str) -> Dict:
        """Fallback market limits when API data is unavailable"""
        base, quote = self._parse_trading_pair(pair)
        
        # Default limits based on currency type
        if quote == 'ZAR':
            return {
                'pair': pair,
                'min_volume': 0.0001,
                'max_volume': 1000.0,
                'volume_scale': 6,
                'price_scale': 0,  # ZAR prices are whole numbers
                'fee_scale': 4,
                'trading_status': 'ACTIVE',
                'base_currency': base,
                'counter_currency': quote,
            }
        else:
            return {
                'pair': pair,
                'min_volume': 0.00001,
                'max_volume': 100.0,
                'volume_scale': 8,
                'price_scale': 6,
                'fee_scale': 4,
                'trading_status': 'ACTIVE',
                'base_currency': base,
                'counter_currency': quote,
            }
    
    def validate_and_format_order(self, pair: str, price: float, volume: float) -> Tuple[str, str, bool]:
        """
        Validate and format order parameters using live market data
        
        Returns:
            Tuple of (formatted_price, formatted_volume, is_valid)
        """
        try:
            # Get dynamic market info from Luno API
            market_info = self.get_market_info(pair)
            
            # Validate volume limits
            min_vol = market_info['min_volume']
            max_vol = market_info['max_volume']
            
            if volume < min_vol:
                logging.info(f"Volume {volume} below minimum {min_vol} for {pair}, setting volume to {min_vol}")
                volume = min_vol
                
            if volume > max_vol:
                logging.info(f"Volume {volume} above maximum {max_vol} for {pair}, setting volume to {max_vol}")
                volume = max_vol
            
            # Check if market is active
            if market_info['trading_status'] != 'ACTIVE':
                logging.error(f"Market {pair} is not active (status: {market_info['trading_status']})")
                return "", "", False
            
            # Format according to market precision
            volume_scale = market_info['volume_scale']
            price_scale = market_info['price_scale']
            
            formatted_volume = f"{volume:.{volume_scale}f}".rstrip('0').rstrip('.')
            formatted_price = f"{price:.{price_scale}f}".rstrip('0').rstrip('.')
            
            # Ensure ZAR prices are whole numbers
            if market_info['counter_currency'] == 'ZAR':
                formatted_price = str(int(round(float(formatted_price))))
            
            logging.info(f"Order validation for {pair}: "
                        f"Volume {volume} -> {formatted_volume} "
                        f"(range: {min_vol}-{max_vol}), "
                        f"Price {price} -> {formatted_price}")
            
            return formatted_price, formatted_volume, True
            
        except Exception as e:
            logging.error(f"Error validating order for {pair}: {e}")
            return "", "", False
        

    def _format_volume_for_pair(self, pair: str, base: str, volume: float) -> str:
        """Format volume according to Luno's precision requirements"""
        
        # Most crypto volumes: 6 decimal places maximum (0.000001 precision)
        if base in ['XBT', 'ETH', 'LTC', 'XRP', 'ADA', 'BCH']:
            return f"{volume:.6f}"
        
        # Smaller altcoins might allow more precision
        elif base in ['DOGE', 'SHIB']:
            return f"{volume:.8f}"
        
        # Fiat currencies: 2 decimal places
        elif base in ['ZAR', 'USD', 'EUR', 'GBP']:
            return f"{volume:.2f}"
        
        # Default: 6 decimal places
        else:
            return f"{volume:.6f}"
    
    # TODO: Remove this method, use pair Dict instead to get base and quote
    def _parse_trading_pair(self, pair: str) -> Tuple[str, str]:
        """Parse trading pair to get base and quote currencies"""
        return parse_trading_pair(pair)
    
    def clear_market_cache(self):
        """Clear the market data cache to force refresh"""
        self._market_cache.clear()
        logging.info("Market data cache cleared")
    
    def get_cached_markets(self) -> Dict:
        """Get all cached market data"""
        return self._market_cache.copy()
    
    def log_market_summary(self, pairs: list = None):
        """Log summary of market data for specified pairs"""
        if not pairs:
            pairs = ['XBTZAR', 'ETHZAR', 'XRPZAR']
        
        logging.info("📊 Market Data Summary:")
        for pair in pairs:
            try:
                market_info = self.get_market_info(pair)
                logging.info(f"  {pair}: "
                           f"Vol: {market_info['min_volume']}-{market_info['max_volume']}, "
                           f"Scales: P{market_info['price_scale']}/V{market_info['volume_scale']}, "
                           f"Status: {market_info['trading_status']}")
            except Exception as e:
                logging.error(f"  {pair}: Error getting market data - {e}")
    
    def get_environment_info(self) -> Dict[str, str]:
        """Get current environment configuration information"""
        return {
            'environment': self.environment,
            'base_url': self.base_url,
            'exchange_url': self.exchange_base_url,
            'is_staging': self.environment == 'DEV',
            'api_key_masked': f"{self.api_key[:8]}..." if self.api_key else "Not set"
        }
    
    def log_environment_status(self):
        """Log current environment status for debugging"""
        env_info = self.get_environment_info()
        logging.info("🔧 Luno API Environment Status:")
        logging.info(f"  Environment: {env_info['environment']}")
        logging.info(f"  Base URL: {env_info['base_url']}")
        logging.info(f"  Exchange URL: {env_info['exchange_url']}")
        logging.info(f"  API Key: {env_info['api_key_masked']}")
        
        if env_info['is_staging']:
            logging.warning("  ⚠️  STAGING MODE: Orders will be placed on test environment")
        else:
            logging.info("  ✅ PRODUCTION MODE: Orders will be placed on live exchange")

class LimitOrderSide(str):
    ASK = 'ASK'
    BID = 'BID'

# Keep old class for backward compatibility, but mark as deprecated
class LimitOderSide(LimitOrderSide):
    """
    @deprecated: Use LimitOrderSide instead.
    """
    pass

class OrderState:
    PENDING = 'PENDING'
    COMPLETE = 'COMPLETE'  # Fixed: API returns 'COMPLETE' not 'COMPLETED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'

class OrderType:
    BID = 'BID'      # Fixed: API uses 'BID' for buy orders
    ASK = 'ASK'      # Fixed: API uses 'ASK' for sell orders
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'