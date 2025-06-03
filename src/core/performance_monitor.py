#!/usr/bin/env python3
"""
Performance Monitoring System
Tracks trading performance, win rates, and portfolio growth
"""

import logging
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class Trade:
    """Represents a completed trade"""
    pair: str
    timestamp: float
    entry_price: float
    exit_price: float
    volume: float
    side: str  # 'buy' or 'sell'
    strategy: str
    pnl_zar: float
    pnl_pct: float
    duration_minutes: float
    fees_paid: float = 0.0

@dataclass
class PerformanceMetrics:
    """Performance metrics for a trading session"""
    start_time: float
    end_time: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    total_pnl_zar: float
    total_pnl_pct: float
    best_trade_pct: float
    worst_trade_pct: float
    average_trade_duration_hours: float
    total_fees_paid: float
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None

class PerformanceMonitor:
    """Monitor and track trading performance"""
    
    def __init__(self, data_file: str = "trading_performance.json"):
        self.data_file = data_file
        self.trades: List[Trade] = []
        self.portfolio_snapshots: List[Dict] = []
        self.session_start_time = time.time()
        self.initial_portfolio_value = 0.0
        
        # Load existing data if available
        self.load_data()
        
        logging.info(f"Performance Monitor initialized - tracking to {data_file}")
    
    def set_initial_portfolio_value(self, value: float):
        """Set the initial portfolio value for this session"""
        self.initial_portfolio_value = value
        logging.info(f"Initial portfolio value set: {value:.2f} ZAR")
    
    def record_trade(self, pair: str, entry_price: float, exit_price: float, 
                    volume: float, side: str, strategy: str, duration_minutes: float, 
                    fees_paid: float = 0.0):
        """Record a completed trade"""
        try:
            # Calculate P&L
            if side == 'buy':
                # For buy trades, profit when exit > entry
                pnl_zar = (exit_price - entry_price) * volume - fees_paid
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            else:
                # For sell trades, profit when entry > exit
                pnl_zar = (entry_price - exit_price) * volume - fees_paid
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100
            
            trade = Trade(
                pair=pair,
                timestamp=time.time(),
                entry_price=entry_price,
                exit_price=exit_price,
                volume=volume,
                side=side,
                strategy=strategy,
                pnl_zar=pnl_zar,
                pnl_pct=pnl_pct,
                duration_minutes=duration_minutes,
                fees_paid=fees_paid
            )
            
            self.trades.append(trade)
            
            # Log the trade
            logging.info(f"📝 Trade Recorded: {pair} {side.upper()}")
            logging.info(f"   {entry_price:.2f} → {exit_price:.2f} ({pnl_pct:+.2f}%)")
            logging.info(f"   P&L: {pnl_zar:+.2f} ZAR, Duration: {duration_minutes:.1f}min")
            logging.info(f"   Strategy: {strategy}")
            
            # Save to disk
            self.save_data()
            
        except Exception as e:
            logging.error(f"Error recording trade: {e}")
    
    def record_portfolio_snapshot(self, total_value: float, allocations: Dict[str, float]):
        """Record a portfolio snapshot for tracking growth"""
        try:
            snapshot = {
                'timestamp': time.time(),
                'total_value': total_value,
                'allocations': allocations,
                'growth_from_start': ((total_value - self.initial_portfolio_value) / self.initial_portfolio_value * 100) if self.initial_portfolio_value > 0 else 0
            }
            
            self.portfolio_snapshots.append(snapshot)
            
            # Keep only last 1000 snapshots to avoid file bloat
            if len(self.portfolio_snapshots) > 1000:
                self.portfolio_snapshots = self.portfolio_snapshots[-1000:]
            
        except Exception as e:
            logging.error(f"Error recording portfolio snapshot: {e}")
    
    def get_performance_metrics(self, timeframe_hours: Optional[int] = None) -> PerformanceMetrics:
        """Calculate performance metrics for specified timeframe"""
        try:
            # Filter trades by timeframe if specified
            if timeframe_hours:
                cutoff_time = time.time() - (timeframe_hours * 3600)
                filtered_trades = [t for t in self.trades if t.timestamp >= cutoff_time]
            else:
                filtered_trades = self.trades
            
            if not filtered_trades:
                return PerformanceMetrics(
                    start_time=self.session_start_time,
                    end_time=time.time(),
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate_pct=0,
                    total_pnl_zar=0,
                    total_pnl_pct=0,
                    best_trade_pct=0,
                    worst_trade_pct=0,
                    average_trade_duration_hours=0,
                    total_fees_paid=0
                )
            
            # Calculate metrics
            total_trades = len(filtered_trades)
            winning_trades = len([t for t in filtered_trades if t.pnl_zar > 0])
            losing_trades = len([t for t in filtered_trades if t.pnl_zar < 0])
            win_rate_pct = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl_zar = sum(t.pnl_zar for t in filtered_trades)
            total_volume = sum(t.entry_price * t.volume for t in filtered_trades)
            total_pnl_pct = (total_pnl_zar / total_volume * 100) if total_volume > 0 else 0
            
            best_trade_pct = max((t.pnl_pct for t in filtered_trades), default=0)
            worst_trade_pct = min((t.pnl_pct for t in filtered_trades), default=0)
            
            avg_duration = sum(t.duration_minutes for t in filtered_trades) / len(filtered_trades) / 60  # Convert to hours
            total_fees = sum(t.fees_paid for t in filtered_trades)
            
            # Calculate Sharpe ratio (simplified)
            if len(filtered_trades) > 1:
                returns = [t.pnl_pct for t in filtered_trades]
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_dev = variance ** 0.5
                sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate max drawdown from portfolio snapshots
            max_drawdown_pct = self.calculate_max_drawdown()
            
            return PerformanceMetrics(
                start_time=filtered_trades[0].timestamp if filtered_trades else self.session_start_time,
                end_time=filtered_trades[-1].timestamp if filtered_trades else time.time(),
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate_pct=win_rate_pct,
                total_pnl_zar=total_pnl_zar,
                total_pnl_pct=total_pnl_pct,
                best_trade_pct=best_trade_pct,
                worst_trade_pct=worst_trade_pct,
                average_trade_duration_hours=avg_duration,
                total_fees_paid=total_fees,
                sharpe_ratio=sharpe_ratio,
                max_drawdown_pct=max_drawdown_pct
            )
            
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(
                start_time=self.session_start_time,
                end_time=time.time(),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0,
                total_pnl_zar=0,
                total_pnl_pct=0,
                best_trade_pct=0,
                worst_trade_pct=0,
                average_trade_duration_hours=0,
                total_fees_paid=0
            )
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from portfolio snapshots"""
        try:
            if len(self.portfolio_snapshots) < 2:
                return 0.0
            
            peak_value = self.portfolio_snapshots[0]['total_value']
            max_drawdown = 0.0
            
            for snapshot in self.portfolio_snapshots[1:]:
                current_value = snapshot['total_value']
                
                # Update peak if we have a new high
                if current_value > peak_value:
                    peak_value = current_value
                
                # Calculate drawdown from peak
                drawdown = (peak_value - current_value) / peak_value * 100
                
                # Update max drawdown
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return max_drawdown
            
        except Exception as e:
            logging.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def get_strategy_performance(self) -> Dict[str, Dict]:
        """Get performance breakdown by strategy"""
        try:
            strategy_stats = {}
            
            for trade in self.trades:
                strategy = trade.strategy
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_pnl_zar': 0,
                        'total_pnl_pct': 0,
                        'best_trade': 0,
                        'worst_trade': 0
                    }
                
                stats = strategy_stats[strategy]
                stats['trades'] += 1
                stats['total_pnl_zar'] += trade.pnl_zar
                stats['total_pnl_pct'] += trade.pnl_pct
                
                if trade.pnl_zar > 0:
                    stats['wins'] += 1
                else:
                    stats['losses'] += 1
                
                if trade.pnl_pct > stats['best_trade']:
                    stats['best_trade'] = trade.pnl_pct
                
                if trade.pnl_pct < stats['worst_trade']:
                    stats['worst_trade'] = trade.pnl_pct
            
            # Calculate win rates
            for strategy, stats in strategy_stats.items():
                stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
                stats['avg_pnl_pct'] = stats['total_pnl_pct'] / stats['trades'] if stats['trades'] > 0 else 0
            
            return strategy_stats
            
        except Exception as e:
            logging.error(f"Error calculating strategy performance: {e}")
            return {}
    
    def log_performance_summary(self, timeframe_hours: Optional[int] = None):
        """Log comprehensive performance summary"""
        try:
            metrics = self.get_performance_metrics(timeframe_hours)
            
            timeframe_str = f"Last {timeframe_hours}h" if timeframe_hours else "All Time"
            
            logging.info(f"")
            logging.info(f"📊 PERFORMANCE SUMMARY ({timeframe_str})")
            logging.info(f"=" * 50)
            logging.info(f"Total Trades: {metrics.total_trades}")
            logging.info(f"Win Rate: {metrics.win_rate_pct:.1f}% ({metrics.winning_trades}W/{metrics.losing_trades}L)")
            logging.info(f"Total P&L: {metrics.total_pnl_zar:+.2f} ZAR ({metrics.total_pnl_pct:+.2f}%)")
            logging.info(f"Best Trade: {metrics.best_trade_pct:+.2f}%")
            logging.info(f"Worst Trade: {metrics.worst_trade_pct:+.2f}%")
            logging.info(f"Avg Duration: {metrics.average_trade_duration_hours:.1f} hours")
            logging.info(f"Total Fees: {metrics.total_fees_paid:.2f} ZAR")
            
            if metrics.sharpe_ratio is not None:
                logging.info(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            
            if metrics.max_drawdown_pct is not None:
                logging.info(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
            
            # Portfolio growth
            if self.portfolio_snapshots:
                latest = self.portfolio_snapshots[-1]
                growth = latest['growth_from_start']
                logging.info(f"Portfolio Growth: {growth:+.2f}%")
            
            logging.info(f"=" * 50)
            
            # Strategy breakdown
            strategy_stats = self.get_strategy_performance()
            if strategy_stats:
                logging.info(f"📈 STRATEGY BREAKDOWN:")
                for strategy, stats in strategy_stats.items():
                    logging.info(f"  {strategy}: {stats['trades']} trades, "
                               f"{stats['win_rate']:.1f}% win rate, "
                               f"{stats['total_pnl_zar']:+.2f} ZAR")
            
            logging.info(f"")
            
        except Exception as e:
            logging.error(f"Error logging performance summary: {e}")
    
    def is_doubling_goal_achieved(self) -> Tuple[bool, float]:
        """Check if the doubling goal has been achieved"""
        try:
            if not self.portfolio_snapshots or self.initial_portfolio_value == 0:
                return False, 0.0
            
            latest_value = self.portfolio_snapshots[-1]['total_value']
            growth_pct = ((latest_value - self.initial_portfolio_value) / self.initial_portfolio_value) * 100
            
            return growth_pct >= 100.0, growth_pct
            
        except Exception as e:
            logging.error(f"Error checking doubling goal: {e}")
            return False, 0.0
    
    def get_daily_performance(self) -> List[Dict]:
        """Get daily performance breakdown"""
        try:
            daily_stats = {}
            
            for trade in self.trades:
                date_str = datetime.fromtimestamp(trade.timestamp).strftime('%Y-%m-%d')
                
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        'date': date_str,
                        'trades': 0,
                        'pnl_zar': 0,
                        'pnl_pct': 0,
                        'fees': 0
                    }
                
                daily_stats[date_str]['trades'] += 1
                daily_stats[date_str]['pnl_zar'] += trade.pnl_zar
                daily_stats[date_str]['pnl_pct'] += trade.pnl_pct
                daily_stats[date_str]['fees'] += trade.fees_paid
            
            return sorted(daily_stats.values(), key=lambda x: x['date'])
            
        except Exception as e:
            logging.error(f"Error calculating daily performance: {e}")
            return []
    
    def export_performance_report(self, filename: Optional[str] = None) -> str:
        """Export comprehensive performance report to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"performance_report_{timestamp}.json"
            
            metrics = self.get_performance_metrics()
            strategy_stats = self.get_strategy_performance()
            daily_stats = self.get_daily_performance()
            
            report = {
                'generated_at': time.time(),
                'session_start': self.session_start_time,
                'initial_portfolio_value': self.initial_portfolio_value,
                'current_portfolio_value': self.portfolio_snapshots[-1]['total_value'] if self.portfolio_snapshots else 0,
                'overall_metrics': asdict(metrics),
                'strategy_breakdown': strategy_stats,
                'daily_performance': daily_stats,
                'total_trades': len(self.trades),
                'doubling_achieved': self.is_doubling_goal_achieved()[0],
                'growth_percentage': self.is_doubling_goal_achieved()[1]
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logging.info(f"📄 Performance report exported to {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error exporting performance report: {e}")
            return ""
    
    def save_data(self):
        """Save performance data to disk"""
        try:
            data = {
                'session_start_time': self.session_start_time,
                'initial_portfolio_value': self.initial_portfolio_value,
                'trades': [asdict(trade) for trade in self.trades],
                'portfolio_snapshots': self.portfolio_snapshots
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logging.error(f"Error saving performance data: {e}")
    
    def load_data(self):
        """Load performance data from disk"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.session_start_time = data.get('session_start_time', time.time())
                self.initial_portfolio_value = data.get('initial_portfolio_value', 0.0)
                
                # Load trades
                self.trades = []
                for trade_data in data.get('trades', []):
                    trade = Trade(**trade_data)
                    self.trades.append(trade)
                
                # Load portfolio snapshots
                self.portfolio_snapshots = data.get('portfolio_snapshots', [])
                
                logging.info(f"Loaded {len(self.trades)} trades and {len(self.portfolio_snapshots)} snapshots")
                
        except Exception as e:
            logging.error(f"Error loading performance data: {e}")
    
    def reset_session(self):
        """Reset the current trading session"""
        self.trades = []
        self.portfolio_snapshots = []
        self.session_start_time = time.time()
        self.initial_portfolio_value = 0.0
        
        logging.info("📊 Performance monitoring session reset")
