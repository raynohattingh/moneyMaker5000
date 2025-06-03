#!/usr/bin/env python3
"""
Trading Pair Discovery System

Dynamically discovers valid trading pairs from a list of assets and caches them
for efficient access during trading operations.
"""

import logging
import requests
import time
from typing import Dict, List, Set, Tuple, Optional
from itertools import combinations
from luno_api import LunoAPI
from trading_utils import parse_trading_pair, LOG_EMOJI

class TradingPairDiscovery:
    def __init__(self, luno_api: LunoAPI, discovery_config: Dict = None):
        self.luno = luno_api
        self.valid_pairs: Dict[str, Dict] = {}  # pair -> {base, quote, info}
        self.asset_to_pairs: Dict[str, Set[str]] = {}  # asset -> set of pairs containing it
        self.pair_priorities: Dict[str, int] = {}  # pair -> priority score
        
        # Load discovery configuration
        self.config = discovery_config or {}
        self.max_pairs_to_test = self.config.get('max_pairs_to_test', 50)
        self.rate_limit_ms = self.config.get('rate_limit_ms', 150)
        self.timeout_seconds = self.config.get('timeout_seconds', 10)
        
        # Asset categories from configuration (no hard-coding)
        self.asset_categories = self.config.get('asset_categories', {
            'fiat_currencies': ['ZAR', 'USD', 'EUR', 'GBP'],
            'stablecoins': ['USDT', 'USDC', 'DAI', 'BUSD'],
            'major_cryptos': ['XBT', 'ETH', 'ADA', 'XRP'],
            'alt_cryptos': ['LTC', 'BCH', 'LINK', 'UNI']
        })
        
        logging.info(f"Pair discovery initialized with config-based asset categories:")
        for category, assets in self.asset_categories.items():
            logging.info(f"  {category}: {assets}")
        
    def discover_valid_pairs(self, assets: List[str]) -> Dict[str, Dict]:
        """
        Discover all valid trading pairs from a list of assets using API-based approach
        
        Args:
            assets: List of asset tickers (e.g., ['ZAR', 'USDT', 'XBT', 'ETH'])
            
        Returns:
            Dictionary of valid pairs with their metadata
        """
        logging.info(f"Discovering trading pairs for assets: {assets}")
        logging.info(f"Using API-based discovery method")
        
        # Get all available pairs from Luno API
        available_pairs = self._fetch_available_pairs_from_api()

        # Generate pairs form assets in config
        generated_pairs = self._generate_pairs(assets)
        
        # Filter pairs based on desired assets
        # relevant_pairs = self._filter_pairs_by_assets(available_pairs, assets)
        
        # Get detailed information for each relevant pair

        self.valid_pairs = self._filter_invalid_pairs(available_pairs, generated_pairs)

        for pair in self.valid_pairs:
            pair_info = self._get_pair_info(pair)
            # if pair_info and pair_info.get('ask', 0) > 0 and pair_info.get('bid', 0) > 0:
            if pair_info:
                self.valid_pairs[pair] = {
                    'base': self.valid_pairs[pair]['base'],
                    'quote': self.valid_pairs[pair]['quote'],
                    'info': pair_info,
                    'priority': self._calculate_pair_priority(self.valid_pairs[pair], pair_info)
                }



        # valid_count = 0
        # for i, pair in enumerate(valid_asset_pairs):
        #     if i % 10 == 0 and i > 0:  # Progress update every 10 pairs
        #         logging.info(f"Progress: {i}/{len(valid_asset_pairs)} pairs processed, {valid_count} valid pairs found")
                
        #     base, quote = self._parse_trading_pair(pair)
        #     pair_info = self._get_pair_info(pair)
            
        #     if pair_info and pair_info.get('ask', 0) > 0 and pair_info.get('bid', 0) > 0:
        #         self.valid_pairs[pair] = {
        #             'base': base,
        #             'quote': quote,
        #             'info': pair_info,
        #             'priority': self._calculate_pair_priority(pair, base, quote, pair_info)
        #         }
                
        #         # Update asset to pairs mapping
        #         for asset in [base, quote]:
        #             if asset not in self.asset_to_pairs:
        #                 self.asset_to_pairs[asset] = set()
        #             self.asset_to_pairs[asset].add(pair)
                
        #         valid_count += 1
                
        logging.info(f"Discovery complete: {self.valid_pairs} valid pairs found")
        
        # Sort pairs by priority for efficient access
        self.pair_priorities = {pair: data['priority'] for pair, data in self.valid_pairs.items()}
        
        # Log discovered pairs summary
        self.log_discovery_summary()
        
        return self.valid_pairs
    
    def _filter_invalid_pairs(self, available_pairs: List[str], generated_pairs: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Filter out invalid pairs by testing their validity on Luno
        
        Args:
            pairs: List of trading pairs to validate
            
        Returns:
            List of valid trading pairs
        """
        valid_pairs = {}
        
        logging.info(f"Validating {len(generated_pairs)} trading pairs...")
        
        for pair in generated_pairs:
            if pair in available_pairs:
                valid_pairs[pair] = generated_pairs[pair]
            else:
                logging.debug(f"Invalid pair skipped: {pair}")
        
        logging.info(f"Validation complete: {len(valid_pairs)} valid pairs found")
        return valid_pairs
    
    def _generate_pairs(self, assets: List[str]) -> Dict[str, Dict]:
        """
        Generate all possible trading pairs from a list of assets
        
        Args:
            assets: List of asset tickers (e.g., ['ZAR', 'USDT', 'XBT', 'ETH'])
            
        Returns:
            List of generated trading pairs
        """
        if not assets:
            return []
        
        # Use dynamic pair generation based on asset categories
        generated_pairs = {}
    
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                cur1 = assets[i].upper()
                cur2 = assets[j].upper()
                
                generated_pairs[f"{cur1}{cur2}"] = {
                    'base': cur1,
                    'quote': cur2
                }

                generated_pairs[f"{cur2}{cur1}"] = {
                    'base': cur2,
                    'quote': cur1
                }
            
        
        logging.info(f"Generated {len(generated_pairs)} pairs from {len(assets)} assets")
        logging.debug(f"Generated pairs: {list(generated_pairs)[:20]}{'...' if len(generated_pairs) > 30 else ''}")
        return generated_pairs

    def _fetch_available_pairs_from_api(self) -> List[str]:
        """Fetch all available trading pairs from Luno API"""
        try:
            logging.info("Fetching available trading pairs from Luno API...")
            available_pairs = self.luno.get_available_pairs()
            logging.info(f"Successfully fetched {len(available_pairs)} pairs from API")
            return available_pairs
        except Exception as e:
            logging.error(f"Failed to fetch pairs from API: {e}")
            logging.warning("Falling back to config-based discovery")
            return self._generate_fallback_pairs()

    def _generate_fallback_pairs(self) -> List[str]:
        """Generate fallback pairs if API is unavailable"""
        # Fallback to common known pairs if API fails
        fallback_pairs = [
            'XBTZAR', 'ETHZAR', 'LTCZAR', 'XRPZAR', 
            'ADAZAR', 'BCHZAR', 'LINKZAR', 'UNIUSD',
            'XBTUSDT', 'ETHUSDT', 'LTCUSDT', 'XRPUSDT',
            'ETHXBT', 'LTCXBT', 'XRPXBT', 'ADAXBT'
        ]
        logging.info(f"Using fallback pairs: {fallback_pairs}")
        return fallback_pairs

    def _filter_pairs_by_assets(self, all_pairs: List[str], desired_assets: List[str]) -> List[str]:
        """Filter pairs to only include those containing desired assets"""
        if not desired_assets:
            return all_pairs
            
        desired_assets_upper = [asset.upper() for asset in desired_assets]
        relevant_pairs = []
        
        for pair in all_pairs:
            base, quote = self._parse_trading_pair(pair)
            
            # Include pair if either base or quote is in desired assets
            if base.upper() in desired_assets_upper or quote.upper() in desired_assets_upper:
                relevant_pairs.append(pair)
                
        logging.info(f"Filtered {len(all_pairs)} pairs down to {len(relevant_pairs)} relevant pairs")
        logging.debug(f"Relevant pairs: {relevant_pairs[:20]}{'...' if len(relevant_pairs) > 20 else ''}")
        
        return relevant_pairs
    
    def _classify_asset_by_market_data(self, asset: str) -> str:
        """Classify asset type based on market data and naming patterns"""
        asset = asset.upper()
        
        # Common fiat currency patterns
        fiat_patterns = ['ZAR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'KRW']
        if asset in fiat_patterns:
            return 'fiat'
        
        # Common stablecoin patterns  
        stablecoin_patterns = ['USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDP', 'FRAX']
        if asset in stablecoin_patterns or 'USD' in asset:
            return 'stablecoin'
        
        # Major crypto patterns (top market cap)
        major_crypto_patterns = ['XBT', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC']
        if asset in major_crypto_patterns:
            return 'major_crypto'
        
        # Everything else is alt crypto
        return 'alt_crypto'

    def _get_dynamic_asset_classification(self, assets: List[str]) -> Dict[str, List[str]]:
        """Dynamically classify assets into categories"""
        classification = {
            'fiat': [],
            'stablecoin': [],
            'major_crypto': [],
            'alt_crypto': []
        }
        
        for asset in assets:
            category = self._classify_asset_by_market_data(asset)
            classification[category].append(asset)
        
        return classification

    def _generate_prioritized_pairs(self, assets: List[str], max_combinations: int = 60) -> List[str]:
        """Generate all possible pair combinations dynamically, prioritized by likelihood"""
        pairs = []
        
        # No need to expand XBT/BTC assets - only use XBT
        expanded_assets = set(assets)
        if 'XBT' in assets:
            expanded_assets.add('XBT')
        
        assets_list = sorted(list(expanded_assets))
        
        # Dynamically classify assets instead of using hard-coded lists
        asset_categories = self._get_dynamic_asset_classification(assets_list)
        
        fiat_currencies = set(asset_categories['fiat'])
        stablecoins = set(asset_categories['stablecoin']) 
        major_cryptos = set(asset_categories['major_crypto'])
        alt_cryptos = set(asset_categories['alt_crypto'])
        
        # Generate all possible combinations with smart prioritization
        priority_groups = []
        
        # Group 1: Fiat pairs (highest priority)
        for fiat in fiat_currencies:
            if fiat in assets_list:
                for other in assets_list:
                    if other != fiat:
                        priority_groups.append((1, f"{other}{fiat}"))  # XBTZAR, ETHZAR, etc.
        
        # Group 2: Stablecoin pairs
        for stable in stablecoins:
            if stable in assets_list:
                for other in assets_list:
                    if other != stable and other not in fiat_currencies:
                        priority_groups.append((2, f"{other}{stable}"))  # XBTUSDT, ETHUSDT, etc.
        
        # Group 3: Major crypto pairs
        for major in major_cryptos:
            if major in assets_list:
                for other in assets_list:
                    if other != major and other not in fiat_currencies and other not in stablecoins:
                        priority_groups.append((3, f"{other}{major}"))  # ETHXBT, ADAXBT, etc.
        
        # Group 4: Cross-crypto pairs (alt to alt)
        for base in alt_cryptos:
            for quote in alt_cryptos:
                if base != quote:
                    priority_groups.append((4, f"{base}{quote}"))  # ADAXRP, LTCBCH, etc.
        
        # Group 5: Reverse pairs (lower priority but still valid)
        # Only generate reverse pairs for high-volume combinations
        high_volume_assets = fiat_currencies | stablecoins | major_cryptos
        for quote in high_volume_assets:
            if quote in assets_list:
                for base in high_volume_assets:
                    if base != quote and base in assets_list:
                        priority_groups.append((5, f"{quote}{base}"))  # ZARXBT, USDTETH, etc.
        
        # Sort by priority and remove duplicates
        priority_groups.sort(key=lambda x: x[0])
        seen = set()
        for priority, pair in priority_groups:
            if pair not in seen and len(pairs) < max_combinations:
                seen.add(pair)
                pairs.append(pair)
        
        logging.info(f"Generated {len(pairs)} dynamic pair combinations from {len(assets)} assets")
        logging.info(f"Asset categories: {len(fiat_currencies & set(assets_list))} fiat, "
                    f"{len(stablecoins & set(assets_list))} stablecoins, "
                    f"{len(major_cryptos & set(assets_list))} major cryptos, "
                    f"{len(alt_cryptos)} alt cryptos")
        
        return pairs
    
    def _test_pair_validity(self, pair: str) -> bool:
        """Test if a trading pair is valid on Luno"""
        try:
            # Add rate limiting to avoid overwhelming the API
            time.sleep(self.rate_limit_ms / 1000.0)  # Convert ms to seconds
            
            ticker = self.luno.get_ticker(pair)
            # If we can get ticker data, the pair exists
            valid = ticker is not None and 'ask' in ticker and 'bid' in ticker
            if valid:
                logging.debug(f"✅ Valid pair found: {pair}")
            return valid
            
        except requests.exceptions.Timeout:
            logging.debug(f"⏱️ Timeout testing pair {pair}")
            return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # 400 errors are expected for invalid pairs - don't log as warnings
                logging.debug(f"❌ Pair {pair} not found (400 error) - skipping")
            else:
                logging.warning(f"HTTP error testing pair {pair}: {e}")
            return False
        except requests.exceptions.RequestException as e:
            if "404" in str(e) or "NOT_FOUND" in str(e):
                # Pair doesn't exist - this is expected for many pairs
                logging.debug(f"❌ Pair {pair} not found - skipping")
            else:
                logging.warning(f"Request error testing pair {pair}: {e}")
            return False
        except Exception as e:
            # Pair doesn't exist or is not accessible
            logging.warning(f"Unexpected error testing pair {pair}: {e}")
            return False
    
    def _get_pair_info(self, pair: str) -> Dict:
        """Get market information for a trading pair"""
        try:
            # Add rate limiting for consistent API usage
            time.sleep(self.rate_limit_ms / 1000.0 / 2)  # Shorter delay for info calls
            
            ticker = self.luno.get_ticker(pair)
            
            # Try to get fee info, but don't fail if it's not available
            try:
                fee_info = self.luno.get_fee(pair)
                taker_fee = float(fee_info.get('taker_fee', 0))
                maker_fee = float(fee_info.get('maker_fee', 0))
            except Exception:
                # Use default fees if we can't get them
                taker_fee = 0.001  # 0.1% default
                maker_fee = 0.001  # 0.1% default
                thirty_day_volume = 0
            
            ask = float(ticker.get('ask', 0))
            bid = float(ticker.get('bid', 0))
            spread = (ask - bid) / bid if bid > 0 else 0
            
            return {
                'ask': ask,
                'bid': bid,
                'last_trade': float(ticker.get('last_trade', 0)),
                'volume_24h': float(ticker.get('rolling_24_hour_volume', 0)),
                'spread': spread,
                'taker_fee': taker_fee,
                'maker_fee': maker_fee
            }
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout getting pair info for {pair}")
            return {
                'ask': 0, 'bid': 0, 'last_trade': 0, 'volume_24h': 0,
                'spread': 0, 'taker_fee': 0.001, 'maker_fee': 0.001
            }
        except Exception as e:
            logging.error(f"Error getting pair info for {pair}: {e}")
            return {
                'ask': 0, 'bid': 0, 'last_trade': 0, 'volume_24h': 0,
                'spread': 0, 'taker_fee': 0.001, 'maker_fee': 0.001
            }
    
    def _calculate_pair_priority(self, pair: Dict[str, Dict], info: Dict) -> int:
        """Calculate priority score for a trading pair"""
        priority = 0
        quote = pair['quote']
        base = pair['base']
        logging.debug(f"Calculating priority for pair {pair['base']}/{pair['quote']} with info: {info}")
        
        # ZAR pairs get highest priority (direct fiat conversion)
        if quote == 'ZAR':
            priority += 100
        elif base == 'ZAR':
            priority += 90
        
        # USDT pairs get good priority (stable coin liquidity)
        elif quote == 'USDT':
            priority += 50
        elif base == 'USDT':
            priority += 45
        
        # Major crypto pairs
        if base in ['XBT'] or quote in ['XBT']:
            priority += 20
        if base == 'ETH' or quote == 'ETH':
            priority += 15
        
        # Volume and spread bonuses
        volume_24h = info.get('volume_24h', 0)
        spread = info.get('spread', 1)
        
        if volume_24h > 10000:
            priority += 10
        elif volume_24h > 1000:
            priority += 5
        
        if spread < 0.001:  # Less than 0.1% spread
            priority += 10
        elif spread < 0.005:  # Less than 0.5% spread
            priority += 5
        
        return priority
    
    def _parse_trading_pair(self, pair: str) -> Tuple[str, str]:
        """Parse trading pair to get base and quote currencies"""
        return parse_trading_pair(pair)
    
    def get_pairs_for_asset(self, asset: str) -> Set[str]:
        """Get all trading pairs that include a specific asset"""
        return self.asset_to_pairs.get(asset, set())
    
    def get_best_pair_for_conversion(self, from_asset: str, to_asset: str) -> Optional[str]:
        """Find the best trading pair for converting between two assets"""
        from_pairs = self.get_pairs_for_asset(from_asset)
        to_pairs = self.get_pairs_for_asset(to_asset)
        
        # Find pairs that contain both assets
        common_pairs = from_pairs.intersection(to_pairs)
        
        if not common_pairs:
            return None
        
        # Return the highest priority pair
        best_pair = max(common_pairs, key=lambda p: self.pair_priorities.get(p, 0))
        return best_pair
    
    def get_sorted_pairs_by_priority(self) -> List[str]:
        """Get all valid pairs sorted by priority (highest first)"""
        return sorted(self.valid_pairs.keys(), 
                     key=lambda p: self.pair_priorities.get(p, 0), 
                     reverse=True)
    
    def convert_asset_weights_to_pair_weights(self, asset_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Convert asset allocation weights to trading pair weights
        
        This is a simplified approach - in practice, you might want more sophisticated
        allocation logic based on liquidity, correlation, etc.
        """
        pair_weights = {}
        
        # For each asset pair combination, calculate a weight based on asset weights
        for pair, data in self.valid_pairs.items():
            base = data['base']
            quote = data['quote']
            
            base_weight = asset_weights.get(base, 0)
            quote_weight = asset_weights.get(quote, 0)
            
            # Simple approach: use average of the two asset weights
            # You could also use more sophisticated weighting schemes
            if base_weight > 0 and quote_weight > 0:
                pair_weight = (base_weight + quote_weight) / 2
                # Adjust by pair priority
                priority_multiplier = self.pair_priorities.get(pair, 50) / 100
                pair_weights[pair] = pair_weight * priority_multiplier
        
        # Normalize weights to sum to 1.0
        total_weight = sum(pair_weights.values())
        if total_weight > 0:
            pair_weights = {pair: weight / total_weight for pair, weight in pair_weights.items()}
        
        return pair_weights
    
    def log_discovery_summary(self):
        """Log a summary of discovered trading pairs"""
        logging.info("Trading Pair Discovery Summary:")
        logging.info(f"  Total valid pairs: {len(self.valid_pairs)}")
        
        # Group by quote currency
        by_priority = {}
        for pair, data in self.valid_pairs.items():
            priority = data['priority']
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(pair)
        
        for priority, pairs in sorted(by_priority.items()):
            logging.info(f"  {priority} pairs: {len(pairs)} ({', '.join(sorted(pairs))})")
        
        # Show top priority pairs
        top_pairs = self.get_sorted_pairs_by_priority()[:10]
        logging.info(f"  Top priority pairs: {', '.join(top_pairs)}")
