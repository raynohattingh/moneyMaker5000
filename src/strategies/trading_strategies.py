from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

class TradingStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, pair: str, order_volume: float):
        self.pair = pair
        self.order_volume = order_volume
        self.price_history: List[float] = []
        
    @abstractmethod
    def should_buy(self, current_price: float, balance_data: Dict) -> bool:
        """Determine if we should place a buy order"""
        pass
    
    @abstractmethod
    def should_sell(self, current_price: float, balance_data: Dict) -> bool:
        """Determine if we should place a sell order"""
        pass
    
    @abstractmethod
    def get_buy_price(self, current_bid: float, current_ask: float) -> float:
        """Get the price for buy order"""
        pass
    
    @abstractmethod
    def get_sell_price(self, current_bid: float, current_ask: float) -> float:
        """Get the price for sell order"""
        pass
    
    def update_price_history(self, price: float, max_history: int = 50):
        """Update price history for analysis"""
        self.price_history.append(price)
        if len(self.price_history) > max_history:
            self.price_history.pop(0)

class MeanReversionStrategy(TradingStrategy):
    """Simple mean reversion strategy"""
    
    def __init__(self, pair: str, order_volume: float, deviation_threshold: float = 0.005):
        super().__init__(pair, order_volume)
        self.deviation_threshold = deviation_threshold  # 0.5% deviation threshold
        # Extract base currency from pair (e.g., 'USDT' from 'USDTZAR')
        self.base_currency = pair.replace('ZAR', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'  # Only use XBT for Bitcoin
        
    def _get_average_price(self) -> Optional[float]:
        """Calculate average price from history"""
        if len(self.price_history) < 5:
            return None
        return sum(self.price_history) / len(self.price_history)
    
    def should_buy(self, current_price: float, balance_data: Dict) -> bool:
        """Buy when price is significantly below average"""
        avg_price = self._get_average_price()
        if avg_price is None:
            return False
            
        # Buy if current price is below average by threshold
        deviation = (avg_price - current_price) / avg_price
        should_buy = deviation > self.deviation_threshold
        
        if should_buy:
            logging.info(f"Mean reversion BUY signal: current={current_price}, avg={avg_price:.2f}, deviation={deviation:.3f}")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: Dict) -> bool:
        """Sell when price is significantly above average"""
        avg_price = self._get_average_price()
        if avg_price is None:
            return False
            
        # Sell if current price is above average by threshold
        deviation = (current_price - avg_price) / avg_price
        should_sell = deviation > self.deviation_threshold
        
        if should_sell:
            logging.info(f"Mean reversion SELL signal: current={current_price}, avg={avg_price:.2f}, deviation={deviation:.3f}")
        
        return should_sell
    
    def get_buy_price(self, current_bid: float, current_ask: float) -> float:
        """Place buy order at current bid (become maker)"""
        return current_bid
    
    def get_sell_price(self, current_bid: float, current_ask: float) -> float:
        """Place sell order at current ask (become maker)"""
        return current_ask

class ConservativeStrategy(TradingStrategy):
    """Conservative strategy that only trades on significant movements"""
    
    def __init__(self, pair: str, order_volume: float, min_spread_pct: float = 0.002):
        super().__init__(pair, order_volume)
        self.min_spread_pct = min_spread_pct  # Minimum 0.2% spread to trade
        # Extract base currency from pair (e.g., 'USDT' from 'USDTZAR')
        self.base_currency = pair.replace('ZAR', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'  # Only use XBT for Bitcoin
        
    def should_buy(self, current_price: float, balance_data: Dict) -> bool:
        """Only buy if we don't have enough base currency position"""
        base_balance = balance_data.get(self.base_currency, 0)
        return base_balance < self.order_volume
    
    def should_sell(self, current_price: float, balance_data: Dict) -> bool:
        """Only sell if we have sufficient base currency position"""
        base_balance = balance_data.get(self.base_currency, 0)
        return base_balance >= self.order_volume
    
    def get_buy_price(self, current_bid: float, current_ask: float) -> float:
        """Buy at bid price to get maker fee"""
        return current_bid
    
    def get_sell_price(self, current_bid: float, current_ask: float) -> float:
        """Sell at ask price to get maker fee"""
        return current_ask

class MomentumStrategy(TradingStrategy):
    """Aggressive momentum trading strategy that rides trends"""
    
    def __init__(self, pair: str, order_volume: float, momentum_threshold: float = 0.02, lookback_periods: int = 5):
        super().__init__(pair, order_volume)
        self.momentum_threshold = momentum_threshold
        self.lookback_periods = lookback_periods
        # Extract base currency from pair
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def calculate_momentum(self) -> float:
        """Calculate momentum based on price change over lookback period"""
        if len(self.price_history) < self.lookback_periods:
            return 0
        
        old_price = self.price_history[-self.lookback_periods]
        current_price = self.price_history[-1]
        return (current_price - old_price) / old_price
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Buy when momentum is positive and strong"""
        momentum = self.calculate_momentum()
        should_buy = momentum > self.momentum_threshold
        
        if should_buy:
            logging.info(f"Momentum BUY signal: momentum={momentum:.3f} > threshold={self.momentum_threshold}")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Sell when momentum turns negative"""
        momentum = self.calculate_momentum()
        should_sell = momentum < -self.momentum_threshold
        
        if should_sell:
            logging.info(f"Momentum SELL signal: momentum={momentum:.3f} < -{self.momentum_threshold}")
        
        return should_sell
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """More aggressive - closer to ask for quick execution"""
        return bid + (ask - bid) * 0.7
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """More aggressive - closer to bid for quick execution"""
        return ask - (ask - bid) * 0.7


class ScalpingStrategy(TradingStrategy):
    """High-frequency scalping strategy for quick profits"""
    
    def __init__(self, pair: str, order_volume: float, min_profit_pct: float = 0.005):
        super().__init__(pair, order_volume)
        self.min_profit_pct = min_profit_pct
        self.recent_prices = []
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def update_price_history(self, price: float, max_history: int = 20):
        """Keep shorter price history for scalping"""
        super().update_price_history(price, max_history)
        self.recent_prices = self.price_history[-10:]  # Last 10 prices
    
    def get_volatility(self) -> float:
        """Calculate recent volatility"""
        if len(self.recent_prices) < 3:
            return 0
        
        price_changes = []
        for i in range(1, len(self.recent_prices)):
            change = abs(self.recent_prices[i] - self.recent_prices[i-1]) / self.recent_prices[i-1]
            price_changes.append(change)
        
        return sum(price_changes) / len(price_changes) if price_changes else 0
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Buy on quick dips with sufficient volatility"""
        volatility = self.get_volatility()
        
        # Only trade if there's sufficient volatility
        if volatility < 0.001:  # 0.1% minimum volatility
            return False
        
        # Look for quick dips
        if len(self.recent_prices) >= 3:
            recent_drop = (self.recent_prices[-3] - current_price) / self.recent_prices[-3]
            should_buy = recent_drop > 0.002  # 0.2% quick drop
            
            if should_buy:
                logging.info(f"Scalping BUY signal: drop={recent_drop:.3f}, volatility={volatility:.3f}")
            
            return should_buy
        
        return False
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Sell on quick pumps"""
        volatility = self.get_volatility()
        
        if volatility < 0.001:
            return False
        
        # Look for quick pumps
        if len(self.recent_prices) >= 3:
            recent_pump = (current_price - self.recent_prices[-3]) / self.recent_prices[-3]
            should_sell = recent_pump > 0.002  # 0.2% quick pump
            
            if should_sell:
                logging.info(f"Scalping SELL signal: pump={recent_pump:.3f}, volatility={volatility:.3f}")
            
            return should_sell
        
        return False
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """Aggressive market making - place just above bid"""
        return bid + (ask - bid) * 0.1
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """Aggressive market making - place just below ask"""
        return ask - (ask - bid) * 0.1


class BreakoutStrategy(TradingStrategy):
    """Breakout strategy that trades price breakouts from consolidation"""
    
    def __init__(self, pair: str, order_volume: float, breakout_threshold: float = 0.015, consolidation_periods: int = 20):
        super().__init__(pair, order_volume)
        self.breakout_threshold = breakout_threshold
        self.consolidation_periods = consolidation_periods
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def is_consolidating(self) -> bool:
        """Check if price is in consolidation phase"""
        if len(self.price_history) < self.consolidation_periods:
            return False
        
        recent_prices = self.price_history[-self.consolidation_periods:]
        high = max(recent_prices)
        low = min(recent_prices)
        range_pct = (high - low) / low
        
        # Consider it consolidation if price range is small
        is_consolidating = range_pct < 0.01  # 1% range
        
        if is_consolidating:
            logging.debug(f"Price consolidating: range={range_pct:.3f}")
        
        return is_consolidating
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Buy on upward breakout from consolidation"""
        if not self.is_consolidating():
            return False
        
        resistance_level = max(self.price_history[-10:])  # Recent high
        breakout_price = resistance_level * (1 + self.breakout_threshold)
        should_buy = current_price > breakout_price
        
        if should_buy:
            logging.info(f"Breakout BUY signal: price={current_price} > breakout={breakout_price}")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Sell on downward breakdown from consolidation"""
        if not self.is_consolidating():
            return False
        
        support_level = min(self.price_history[-10:])  # Recent low
        breakdown_price = support_level * (1 - self.breakout_threshold)
        should_sell = current_price < breakdown_price
        
        if should_sell:
            logging.info(f"Breakout SELL signal: price={current_price} < breakdown={breakdown_price}")
        
        return should_sell
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """Market order on breakout - use ask price"""
        return ask
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """Market order on breakdown - use bid price"""
        return bid


class FearGreedStrategy(TradingStrategy):
    """Strategy based on CoinMarketCap Fear and Greed Index"""
    
    def __init__(self, pair: str, order_volume: float, fear_threshold: int = 25, greed_threshold: int = 75):
        super().__init__(pair, order_volume)
        self.fear_threshold = fear_threshold
        self.greed_threshold = greed_threshold
        self.last_fear_greed_check = 0
        self.current_fear_greed = 50  # Neutral default
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def get_fear_greed_index(self) -> int:
        """Get current Fear and Greed Index from CoinMarketCap with fallback"""
        try:
            # Only check every 10 minutes to avoid API rate limits
            import time
            current_time = time.time()
            if current_time - self.last_fear_greed_check < 600:  # 10 minutes
                return self.current_fear_greed
            
            # Try to import and use coinmarketcap_api
            try:
                from coinmarketcap_api import bb7_fearAndGreedLatest
                result = bb7_fearAndGreedLatest()
                if result and 'data' in result:
                    self.current_fear_greed = result['data']['value']
                    self.last_fear_greed_check = current_time
                    logging.info(f"Fear & Greed Index: {self.current_fear_greed} ({result['data']['value_classification']})")
                    return self.current_fear_greed
            except ImportError:
                # Graceful fallback when coinmarketcap_api is not available
                logging.debug("coinmarketcap_api not available, using market-based fear/greed estimation")
                # Use a simple market-based estimation as fallback
                self.current_fear_greed = self._estimate_market_sentiment()
                self.last_fear_greed_check = current_time
                return self.current_fear_greed
            
            return self.current_fear_greed
            
        except Exception as e:
            logging.warning(f"Error getting market sentiment: {e}")
            return self.current_fear_greed
    
    def _estimate_market_sentiment(self) -> int:
        """Estimate market sentiment based on price momentum (fallback method)"""
        try:
            momentum = self.calculate_momentum()
            # Convert momentum to fear/greed scale (0-100)
            if momentum > 0.05:  # Strong positive momentum
                return 75  # Greed
            elif momentum > 0.02:  # Moderate positive momentum
                return 60  # Slight greed
            elif momentum < -0.05:  # Strong negative momentum
                return 25  # Fear
            elif momentum < -0.02:  # Moderate negative momentum
                return 40  # Slight fear
            else:
                return 50  # Neutral
        except:
            return 50  # Default neutral
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Buy when market is in extreme fear (contrarian approach)"""
        fear_greed = self.get_fear_greed_index()
        should_buy = fear_greed <= self.fear_threshold
        
        if should_buy:
            logging.info(f"Fear & Greed BUY signal: index={fear_greed} <= {self.fear_threshold} (Extreme Fear)")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Sell when market is in extreme greed"""
        fear_greed = self.get_fear_greed_index()
        should_sell = fear_greed >= self.greed_threshold
        
        if should_sell:
            logging.info(f"Fear & Greed SELL signal: index={fear_greed} >= {self.greed_threshold} (Extreme Greed)")
        
        return should_sell
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """Conservative buy during fear - use bid price"""
        return bid
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """Conservative sell during greed - use ask price"""
        return ask


class VolumeSurgeStrategy(TradingStrategy):
    """Strategy that trades on volume surges using CoinMarketCap data"""
    
    def __init__(self, pair: str, order_volume: float, volume_surge_threshold: float = 2.0):
        super().__init__(pair, order_volume)
        self.volume_surge_threshold = volume_surge_threshold
        self.last_volume_check = 0
        self.avg_volume_24h = 0
        self.current_volume_24h = 0
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def get_volume_data(self) -> tuple:
        """Get volume data from CoinMarketCap with fallback"""
        try:
            # Only check every 5 minutes to avoid API rate limits
            import time
            current_time = time.time()
            if current_time - self.last_volume_check < 300:  # 5 minutes
                return self.current_volume_24h, self.avg_volume_24h
            
            # Try to use coinmarketcap_api if available
            try:
                from coinmarketcap_api import bb7_cryptoQuotesLatest
                
                # Map currency symbols for API
                symbol_map = {'XBT': 'BTC', 'ETH': 'ETH', 'XRP': 'XRP', 'LTC': 'LTC', 'ADA': 'ADA'}
                api_symbol = symbol_map.get(self.base_currency, self.base_currency)
                
                result = bb7_cryptoQuotesLatest(symbol=api_symbol)
                if result and 'data' in result and api_symbol in result['data']:
                    quote_data = result['data'][api_symbol]['quote']['USD']
                    self.current_volume_24h = quote_data['volume_24h']
                    self.avg_volume_24h = self.current_volume_24h  # Use as baseline
                    self.last_volume_check = current_time
                    
                    logging.info(f"{self.base_currency} 24h volume: ${self.current_volume_24h:,.0f}")
                    return self.current_volume_24h, self.avg_volume_24h
                    
            except ImportError:
                # Graceful fallback when coinmarketcap_api is not available
                logging.debug("coinmarketcap_api not available, using estimated volume data")
                # Use a reasonable estimate based on typical volumes
                self.current_volume_24h = self._estimate_volume()
                self.avg_volume_24h = self.current_volume_24h
                self.last_volume_check = current_time
                return self.current_volume_24h, self.avg_volume_24h
            
            return self.current_volume_24h, self.avg_volume_24h
            
        except Exception as e:
            logging.warning(f"Error getting volume data: {e}")
            return self.current_volume_24h, self.avg_volume_24h
    
    def _estimate_volume(self) -> float:
        """Estimate volume when API is not available"""
        # Use typical 24h volumes for major cryptocurrencies
        volume_estimates = {
            'XBT': 20000000000,  # $20B typical for BTC
            'ETH': 10000000000,  # $10B typical for ETH
            'XRP': 1000000000,   # $1B typical for XRP
            'LTC': 500000000,    # $500M typical for LTC
            'ADA': 300000000     # $300M typical for ADA
        }
        return volume_estimates.get(self.base_currency, 1000000000)  # Default $1B
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Buy on volume surge with price momentum"""
        current_vol, avg_vol = self.get_volume_data()
        
        if avg_vol == 0:
            return False
        
        volume_ratio = current_vol / avg_vol
        momentum = self.calculate_momentum()
        
        # Buy if volume surge + positive momentum
        should_buy = (volume_ratio > self.volume_surge_threshold and momentum > 0.01)
        
        if should_buy:
            logging.info(f"Volume surge BUY: volume_ratio={volume_ratio:.2f}, momentum={momentum:.3f}")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Sell when volume drops or momentum turns negative"""
        current_vol, avg_vol = self.get_volume_data()
        
        if avg_vol == 0:
            return False
        
        volume_ratio = current_vol / avg_vol
        momentum = self.calculate_momentum()
        
        # Sell if volume drops significantly or momentum turns very negative
        should_sell = (volume_ratio < 0.5 or momentum < -0.02)
        
        if should_sell:
            logging.info(f"Volume surge SELL: volume_ratio={volume_ratio:.2f}, momentum={momentum:.3f}")
        
        return should_sell
    
    def calculate_momentum(self) -> float:
        """Calculate short-term momentum"""
        if len(self.price_history) < 3:
            return 0
        
        old_price = self.price_history[-3]
        current_price = self.price_history[-1]
        return (current_price - old_price) / old_price
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """Aggressive buy on volume surge"""
        return bid + (ask - bid) * 0.8
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """Aggressive sell when volume drops"""
        return ask - (ask - bid) * 0.8


class HybridAggressiveStrategy(TradingStrategy):
    """Combines multiple aggressive signals for maximum growth potential"""
    
    def __init__(self, pair: str, order_volume: float):
        super().__init__(pair, order_volume)
        self.momentum_threshold = 0.015  # 1.5%
        self.fear_greed_last_check = 0
        self.current_fear_greed = 50
        self.base_currency = pair.replace('ZAR', '').replace('USDT', '').replace('USDC', '')
        if self.base_currency == 'XBT':
            self.base_currency = 'XBT'
    
    def get_market_sentiment(self) -> str:
        """Get overall market sentiment with fallback"""
        try:
            import time
            
            current_time = time.time()
            if current_time - self.fear_greed_last_check < 600:  # 10 minutes
                return self._classify_sentiment(self.current_fear_greed)
            
            # Try to use coinmarketcap_api if available
            try:
                from coinmarketcap_api import bb7_fearAndGreedLatest
                result = bb7_fearAndGreedLatest()
                if result and 'data' in result:
                    self.current_fear_greed = result['data']['value']
                    self.fear_greed_last_check = current_time
                    return self._classify_sentiment(self.current_fear_greed)
            except ImportError:
                # Graceful fallback when coinmarketcap_api is not available
                logging.debug("coinmarketcap_api not available, using estimated sentiment")
                self.current_fear_greed = self._estimate_market_sentiment()
                self.fear_greed_last_check = current_time
                return self._classify_sentiment(self.current_fear_greed)
            
            return self._classify_sentiment(self.current_fear_greed)
            
        except Exception as e:
            logging.warning(f"Error getting market sentiment: {e}")
            return "neutral"
    
    def _estimate_market_sentiment(self) -> int:
        """Estimate market sentiment based on price momentum (fallback method)"""
        try:
            momentum = self.calculate_momentum()
            # Convert momentum to fear/greed scale (0-100)
            if momentum > 0.05:  # Strong positive momentum
                return 75  # Greed
            elif momentum > 0.02:  # Moderate positive momentum
                return 60  # Slight greed
            elif momentum < -0.05:  # Strong negative momentum
                return 25  # Fear
            elif momentum < -0.02:  # Moderate negative momentum
                return 40  # Slight fear
            else:
                return 50  # Neutral
        except:
            return 50  # Default neutral
    
    def _classify_sentiment(self, value: int) -> str:
        """Classify fear/greed value into sentiment"""
        if value <= 20:
            return "extreme_fear"
        elif value <= 40:
            return "fear"
        elif value <= 60:
            return "neutral"
        elif value <= 80:
            return "greed"
        else:
            return "extreme_greed"
    
    def calculate_momentum(self) -> float:
        """Calculate momentum"""
        if len(self.price_history) < 5:
            return 0
        
        old_price = self.price_history[-5]
        current_price = self.price_history[-1]
        return (current_price - old_price) / old_price
    
    def get_volatility(self) -> float:
        """Calculate recent volatility"""
        if len(self.price_history) < 5:
            return 0
        
        recent_prices = self.price_history[-5:]
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            price_changes.append(change)
        
        return sum(price_changes) / len(price_changes) if price_changes else 0
    
    def should_buy(self, current_price: float, balance_data: dict) -> bool:
        """Aggressive buy logic combining multiple signals"""
        momentum = self.calculate_momentum()
        volatility = self.get_volatility()
        sentiment = self.get_market_sentiment()
        
        # Multiple buy conditions (OR logic for aggression)
        buy_signals = []
        
        # Strong positive momentum
        if momentum > self.momentum_threshold:
            buy_signals.append(f"momentum={momentum:.3f}")
        
        # Buy the dip during fear
        if sentiment in ["fear", "extreme_fear"] and momentum > -0.02:
            buy_signals.append(f"fear_dip_buy (sentiment={sentiment})")
        
        # Volatility breakout
        if volatility > 0.005 and momentum > 0.005:
            buy_signals.append(f"volatility_breakout (vol={volatility:.3f})")
        
        should_buy = len(buy_signals) > 0
        
        if should_buy:
            logging.info(f"Hybrid BUY signals: {', '.join(buy_signals)}")
        
        return should_buy
    
    def should_sell(self, current_price: float, balance_data: dict) -> bool:
        """Aggressive sell logic"""
        momentum = self.calculate_momentum()
        sentiment = self.get_market_sentiment()
        
        # Multiple sell conditions
        sell_signals = []
        
        # Strong negative momentum
        if momentum < -self.momentum_threshold:
            sell_signals.append(f"negative_momentum={momentum:.3f}")
        
        # Take profits during extreme greed
        if sentiment == "extreme_greed" and momentum < 0.01:
            sell_signals.append(f"greed_profit_taking (sentiment={sentiment})")
        
        should_sell = len(sell_signals) > 0
        
        if should_sell:
            logging.info(f"Hybrid SELL signals: {', '.join(sell_signals)}")
        
        return should_sell
    
    def get_buy_price(self, bid: float, ask: float) -> float:
        """Dynamic buy pricing based on momentum"""
        momentum = self.calculate_momentum()
        
        if momentum > 0.02:  # Strong momentum - be more aggressive
            return bid + (ask - bid) * 0.9  # Almost market price
        else:
            return bid + (ask - bid) * 0.6  # Moderate aggression
    
    def get_sell_price(self, bid: float, ask: float) -> float:
        """Dynamic sell pricing"""
        momentum = self.calculate_momentum()
        
        if momentum < -0.02:  # Strong negative momentum - sell quickly
            return ask - (ask - bid) * 0.9  # Almost market price
        else:
            return ask - (ask - bid) * 0.6  # Moderate aggression
