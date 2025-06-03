#!/usr/bin/env python3
"""
Trading Utilities Module

Common utility functions for the trading bot.
"""

import logging
from typing import Tuple, Dict, List, Optional
import os

def parse_trading_pair(pair: str) -> Tuple[str, str]:
    """
    Parse trading pair to get base and quote currencies.
    
    Args:
        pair (str): The trading pair (e.g., "XBTZAR", "ETHUSDT")
        
    Returns:
        Tuple[str, str]: A tuple containing (base_currency, quote_currency)
    """
    # Common quote currencies in order of priority (longer first to avoid conflicts)
    common_quotes = ['USDT', 'USDC', 'ZAR', 'XBT', 'ETH', 'XRP', 'LTC', 'USD', 'EUR', 'GBP']
    
    for quote in common_quotes:
        if pair.endswith(quote):
            base = pair[:-len(quote)]
            if base:  # Ensure we have a valid base currency
                return base, quote
    
    # Fallback: try different quote lengths
    for quote_len in [4, 3, 2]:
        if len(pair) > quote_len:
            potential_quote = pair[-quote_len:]
            potential_base = pair[:-quote_len]
            
            # Validate that both parts look like currency codes
            if len(potential_base) >= 2 and len(potential_quote) >= 2:
                return potential_base, potential_quote
    
    # Final fallback: assume equal split
    mid = len(pair) // 2
    base = pair[:mid]
    quote = pair[mid:]
        
    return base, quote

def get_env_variable(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable with proper error handling.
    
    Args:
        name (str): The name of the environment variable
        default (Optional[str]): Default value if not found
        required (bool): Whether the variable is required
        
    Returns:
        Optional[str]: The value of the environment variable or default
        
    Raises:
        ValueError: If the variable is required but not found
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value

def setup_logger(log_file: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with emoji support and colorful formatting.
    
    Args:
        log_file (str): Path to the log file
        log_level (str): Logging level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Map log levels to their numeric values
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    numeric_level = level_map.get(log_level.upper(), logging.INFO)
    
    # Configure logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Create formatter with emoji support
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set formatters
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Emoji mapping for log messages
LOG_EMOJI = {
    "INFO": "ℹ️",
    "DEBUG": "🔍",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🔥",
    "SUCCESS": "✅",
    "TRADE_BUY": "🔵",
    "TRADE_SELL": "🔴",
    "PORTFOLIO": "💼",
    "MARKET": "📊",
    "CONFIG": "🔧",
    "PERFORMANCE": "📈",
    "RISK": "⚖️",
    "API": "🌐",
    "SYSTEM": "🖥️"
}
