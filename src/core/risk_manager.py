#!/usr/bin/env python3
"""
Risk Management System
Implements stop losses, take profits, and position sizing
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from luno_api import LunoAPI, LimitOrderSide
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from trading_utils import LOG_EMOJI

@dataclass
class Position:
    """Represents an open trading position"""
    pair: str
    entry_price: float
    volume: float
    timestamp: float
    side: str  # 'long' or 'short'
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    entry_order_id: Optional[str] = None

class RiskManager:
    """Risk management system for trading bot"""
    
    def __init__(self, luno: LunoAPI, stop_loss_pct: float = 0.05, take_profit_pct: float = 0.15):
        self.luno = luno
        self.stop_loss_pct = stop_loss_pct  # 5% default
        self.take_profit_pct = take_profit_pct  # 15% default
        self.positions: Dict[str, Position] = {}  # pair -> position
        self.max_position_size_pct = 0.3  # Max 30% of portfolio per position
        
        logging.info(f"Risk Manager initialized: stop_loss={stop_loss_pct*100}%, take_profit={take_profit_pct*100}%")
    
    def calculate_position_size(self, pair: str, current_price: float, portfolio_value: float, 
                              base_order_volume: float) -> float:
        """Calculate appropriate position size based on risk management rules"""
        try:
            # Maximum position value in ZAR
            max_position_value = portfolio_value * self.max_position_size_pct
            
            # Calculate volume based on max position size
            max_volume_zar = min(base_order_volume, max_position_value)
            
            # For crypto pairs, convert to base currency volume
            if pair.endswith('ZAR'):
                volume = max_volume_zar / current_price
            else:
                volume = max_volume_zar
            
            logging.info(f"Position sizing for {pair}: max_value={max_position_value:.2f} ZAR, "
                        f"volume={volume:.6f}, price={current_price}")
            
            return volume
            
        except Exception as e:
            logging.error(f"Error calculating position size for {pair}: {e}")
            return base_order_volume / current_price if pair.endswith('ZAR') else base_order_volume
    
    def open_position(self, pair: str, entry_price: float, volume: float, 
                     side: str = 'long', order_id: str = None):
        """Record a new position opening"""
        try:
            # Calculate stop loss and take profit levels
            if side == 'long':
                stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                take_profit_price = entry_price * (1 + self.take_profit_pct)
            else:  # short position
                stop_loss_price = entry_price * (1 + self.stop_loss_pct)
                take_profit_price = entry_price * (1 - self.take_profit_pct)
            
            position = Position(
                pair=pair,
                entry_price=entry_price,
                volume=volume,
                timestamp=time.time(),
                side=side,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                entry_order_id=order_id
            )
            
            self.positions[pair] = position
            
            logging.info(f"📊 Position opened: {pair} {side.upper()}")
            logging.info(f"   Entry: {entry_price:.2f}, Volume: {volume:.6f}")
            logging.info(f"   Stop Loss: {stop_loss_price:.2f} (-{self.stop_loss_pct*100:.1f}%)")
            logging.info(f"   Take Profit: {take_profit_price:.2f} (+{self.take_profit_pct*100:.1f}%)")
            
        except Exception as e:
            logging.error(f"Error opening position for {pair}: {e}")
    
    def check_risk_levels(self, pair: str, current_price: float) -> Optional[str]:
        """Check if current price hits stop loss or take profit levels"""
        if pair not in self.positions:
            return None
        
        position = self.positions[pair]
        
        try:
            if position.side == 'long':
                # Long position: stop loss below entry, take profit above
                if current_price <= position.stop_loss_price:
                    pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                    logging.warning(f"🛑 STOP LOSS triggered for {pair}")
                    logging.warning(f"   Entry: {position.entry_price:.2f} -> Current: {current_price:.2f}")
                    logging.warning(f"   P&L: {pnl_pct:.2f}%")
                    return "stop_loss"
                
                elif current_price >= position.take_profit_price:
                    pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                    logging.info(f"🎯 TAKE PROFIT triggered for {pair}")
                    logging.info(f"   Entry: {position.entry_price:.2f} -> Current: {current_price:.2f}")
                    logging.info(f"   P&L: {pnl_pct:.2f}%")
                    return "take_profit"
            
            else:  # short position
                # Short position: stop loss above entry, take profit below
                if current_price >= position.stop_loss_price:
                    pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                    logging.warning(f"🛑 STOP LOSS triggered for {pair} (SHORT)")
                    logging.warning(f"   Entry: {position.entry_price:.2f} -> Current: {current_price:.2f}")
                    logging.warning(f"   P&L: {pnl_pct:.2f}%")
                    return "stop_loss"
                
                elif current_price <= position.take_profit_price:
                    pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                    logging.info(f"🎯 TAKE PROFIT triggered for {pair} (SHORT)")
                    logging.info(f"   Entry: {position.entry_price:.2f} -> Current: {current_price:.2f}")
                    logging.info(f"   P&L: {pnl_pct:.2f}%")
                    return "take_profit"
            
            return None
            
        except Exception as e:
            logging.error(f"Error checking risk levels for {pair}: {e}")
            return None
    
    def execute_risk_exit(self, pair: str, current_price: float, risk_type: str) -> bool:
        """Execute stop loss or take profit order"""
        if pair not in self.positions:
            return False
        
        position = self.positions[pair]
        
        try:
            # Get current market data
            ticker = self.luno.get_ticker(pair)
            bid = float(ticker['bid'])
            ask = float(ticker['ask'])
            
            # Execute market order for immediate exit
            if position.side == 'long':
                # Sell at bid price for immediate execution
                order_price = bid
                side = LimitOrderSide.ASK
            else:
                # Buy to cover short at ask price
                order_price = ask
                side = LimitOrderSide.BID
            
            logging.info(f"💫 Executing {risk_type} order for {pair}")
            logging.info(f"   Volume: {position.volume:.6f}, Price: {order_price:.2f}")
            
            # Place market order (using limit order very close to market)
            result = self.luno.place_limit_order(pair, order_price, position.volume, side)
            
            if result:
                # Calculate final P&L
                if position.side == 'long':
                    pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                else:
                    pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                
                pnl_zar = pnl_pct * (position.entry_price * position.volume) / 100
                
                logging.info(f"✅ {risk_type.upper()} order executed for {pair}")
                logging.info(f"   Final P&L: {pnl_pct:.2f}% ({pnl_zar:+.2f} ZAR)")
                
                # Close the position
                self.close_position(pair)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error executing {risk_type} for {pair}: {e}")
            return False
    
    def close_position(self, pair: str):
        """Close an open position"""
        if pair in self.positions:
            position = self.positions[pair]
            del self.positions[pair]
            
            logging.info(f"📈 Position closed: {pair}")
            logging.info(f"   Duration: {(time.time() - position.timestamp)/3600:.1f} hours")
    
    def get_position_pnl(self, pair: str, current_price: float) -> Optional[Dict]:
        """Get current P&L for a position"""
        if pair not in self.positions:
            return None
        
        position = self.positions[pair]
        
        try:
            if position.side == 'long':
                pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                pnl_zar = (current_price - position.entry_price) * position.volume
            else:
                pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                pnl_zar = (position.entry_price - current_price) * position.volume
            
            return {
                'pair': pair,
                'side': position.side,
                'entry_price': position.entry_price,
                'current_price': current_price,
                'volume': position.volume,
                'pnl_pct': pnl_pct,
                'pnl_zar': pnl_zar,
                'duration_hours': (time.time() - position.timestamp) / 3600
            }
            
        except Exception as e:
            logging.error(f"Error calculating P&L for {pair}: {e}")
            return None
    
    def get_all_positions(self) -> List[Dict]:
        """Get all open positions with current P&L"""
        positions_status = []
        
        for pair in self.positions:
            try:
                ticker = self.luno.get_ticker(pair)
                current_price = float(ticker['last_trade'])
                pnl = self.get_position_pnl(pair, current_price)
                if pnl:
                    positions_status.append(pnl)
            except Exception as e:
                logging.error(f"Error getting status for position {pair}: {e}")
        
        return positions_status
    
    def log_positions_summary(self):
        """Log summary of all open positions"""
        positions = self.get_all_positions()
        
        if not positions:
            logging.info("📊 No open positions")
            return
        
        total_pnl_zar = sum(p['pnl_zar'] for p in positions)
        total_pnl_pct = sum(p['pnl_pct'] for p in positions) / len(positions)  # Average
        
        logging.info(f"📊 Open Positions Summary ({len(positions)} positions)")
        logging.info(f"   Total P&L: {total_pnl_zar:+.2f} ZAR ({total_pnl_pct:+.2f}% avg)")
        
        for pos in positions:
            logging.info(f"   {pos['pair']} {pos['side'].upper()}: "
                        f"{pos['pnl_pct']:+.2f}% ({pos['pnl_zar']:+.2f} ZAR) "
                        f"[{pos['duration_hours']:.1f}h]")
    
    def should_reduce_risk(self, portfolio_pnl_pct: float) -> bool:
        """Check if risk should be reduced based on portfolio performance"""
        # Reduce risk if portfolio is down more than 10%
        if portfolio_pnl_pct < -10:
            logging.warning(f"⚠️ Portfolio down {portfolio_pnl_pct:.1f}% - reducing risk")
            return True
        
        return False
    
    def adjust_risk_parameters(self, market_volatility: float):
        """Dynamically adjust risk parameters based on market conditions"""
        try:
            # Increase stop loss in high volatility markets
            if market_volatility > 0.05:  # 5% volatility
                self.stop_loss_pct = 0.08  # 8% stop loss
                self.max_position_size_pct = 0.2  # Reduce position size
                logging.info("📈 High volatility detected - tightening risk controls")
            elif market_volatility > 0.03:  # 3% volatility
                self.stop_loss_pct = 0.06  # 6% stop loss
                self.max_position_size_pct = 0.25
                logging.info("📊 Moderate volatility - adjusting risk parameters")
            else:
                # Normal volatility - use default parameters
                self.stop_loss_pct = 0.05  # 5% stop loss
                self.max_position_size_pct = 0.3
            
        except Exception as e:
            logging.error(f"Error adjusting risk parameters: {e}")

    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        positions = self.get_all_positions()
        
        if not positions:
            return {
                'open_positions': 0,
                'total_exposure': 0,
                'average_pnl_pct': 0,
                'total_pnl_zar': 0
            }
        
        total_exposure = sum(pos['entry_price'] * pos['volume'] for pos in positions)
        total_pnl_zar = sum(pos['pnl_zar'] for pos in positions)
        avg_pnl_pct = sum(pos['pnl_pct'] for pos in positions) / len(positions)
        
        return {
            'open_positions': len(positions),
            'total_exposure': total_exposure,
            'average_pnl_pct': avg_pnl_pct,
            'total_pnl_zar': total_pnl_zar,
            'stop_loss_pct': self.stop_loss_pct * 100,
            'take_profit_pct': self.take_profit_pct * 100,
            'max_position_size_pct': self.max_position_size_pct * 100
        }
