import time
import logging
import json
from .luno_api import LunoAPI, LimitOrderSide, OrderState, OrderType
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.trading_utils import LOG_EMOJI

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'trading'))
from bot_config import PAIR, ORDER_VOLUME, SLEEP_INTERVAL, LOG_FILE, LOG_LEVEL, STRATEGY, DEVIATION_THRESHOLD, MIN_SPREAD_PCT
from ..strategies.trading_strategies import MeanReversionStrategy, ConservativeStrategy

def main():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Initialize strategy
    if STRATEGY == "mean_reversion":
        strategy = MeanReversionStrategy(PAIR, ORDER_VOLUME, DEVIATION_THRESHOLD)
        logging.info(f"Using Mean Reversion Strategy with deviation threshold: {DEVIATION_THRESHOLD}")
    elif STRATEGY == "conservative":
        strategy = ConservativeStrategy(PAIR, ORDER_VOLUME, MIN_SPREAD_PCT)
        logging.info(f"Using Conservative Strategy with min spread: {MIN_SPREAD_PCT}")
    else:
        raise ValueError(f"Unknown strategy: {STRATEGY}")
    
    luno = LunoAPI()
    while True:
        try:
            ticker = luno.get_ticker(PAIR)
            ask = float(ticker['ask'])
            bid = float(ticker['bid'])
            last_trade = float(ticker['last_trade'])
            logging.info(f"Current {PAIR} - Ask: {ask}, Bid: {bid}, Last: {last_trade}")

            # Update strategy with latest price
            strategy.update_price_history(last_trade)

            usdt_balance = luno.get_balance('USDT')
            zar_balance = luno.get_balance('ZAR')
            logging.info(f"USDT Balance: {usdt_balance}")
            logging.info(f"ZAR Balance: {zar_balance}")

            # Get latest fee for the pair
            fee_info = luno.get_fee(PAIR)
            taker_fee = float(fee_info.get('taker_fee', 0))
            maker_fee = float(fee_info.get('maker_fee', 0))
            logging.info(f"Taker fee: {taker_fee}, Maker fee: {maker_fee}")

            balance_data = {'USDT': usdt_balance, 'ZAR': zar_balance}

            # Get orders with null-safe handling
            orders_list = luno.get_orders_safe(pair=PAIR)
            
            open_sell_orders = [o for o in orders_list if o['type'] == OrderType.ASK and o['state'] == OrderState.PENDING]
            open_buy_orders = [o for o in orders_list if o['type'] == OrderType.BID and o['state'] == OrderState.PENDING]

            # --- SELL LOGIC ---
            if open_sell_orders:
                logging.info(f"Open SELL order(s) detected: {[o['order_id'] for o in open_sell_orders]}")
            else:
                if strategy.should_sell(last_trade, balance_data):
                    # Adjust for taker fee (worst case, to avoid insufficient funds)
                    min_usdt_needed = ORDER_VOLUME * (1 + abs(taker_fee))
                    if usdt_balance >= min_usdt_needed:
                        sell_price = strategy.get_sell_price(bid, ask)
                        logging.info(f"Strategy recommends SELL: Placing order for {ORDER_VOLUME} USDT at {sell_price} ZAR...")
                        try:
                            result = luno.place_limit_order(PAIR, sell_price, ORDER_VOLUME, LimitOrderSide.ASK)
                            logging.info(f"Order result: {result}")
                        except Exception as e:
                            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                                try:
                                    error_json = e.response.json()
                                    formatted_error = json.dumps(error_json, indent=2)
                                    logging.error(f"Failed to place SELL order: {e}. API response: {formatted_error}")
                                except Exception:
                                    logging.error(f"Failed to place SELL order: {e}. API response: {e.response.text}")
                            else:
                                logging.error(f"Failed to place SELL order: {e}")
                    else:
                        logging.info(f"Not enough USDT to place sell order (have {usdt_balance}, need {min_usdt_needed}).")
                else:
                    logging.info("Strategy does not recommend SELL at this time.")

            # --- BUY LOGIC ---
            if open_buy_orders:
                logging.info(f"Open BUY order(s) detected: {[o['order_id'] for o in open_buy_orders]}")
            else:
                if strategy.should_buy(last_trade, balance_data):
                    buy_price = strategy.get_buy_price(bid, ask)
                    # Adjust for taker fee (worst case, to avoid insufficient funds)
                    required_zar = ORDER_VOLUME * buy_price * (1 + abs(taker_fee))
                    if zar_balance >= required_zar:
                        logging.info(f"Strategy recommends BUY: Placing order for {ORDER_VOLUME} USDT at {buy_price} ZAR...")
                        try:
                            result = luno.place_limit_order(PAIR, buy_price, ORDER_VOLUME, LimitOrderSide.BID)
                            logging.info(f"Order result: {result}")
                        except Exception as e:
                            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                                try:
                                    error_json = e.response.json()
                                    formatted_error = json.dumps(error_json, indent=2)
                                    logging.error(f"Failed to place BUY order: {e}. API response: {formatted_error}")
                                except Exception:
                                    logging.error(f"Failed to place BUY order: {e}. API response: {e.response.text}")
                            else:
                                logging.error(f"Failed to place BUY order: {e}")
                    else:
                        logging.info(f"Not enough ZAR to place buy order (have {zar_balance}, need {required_zar}).")
                else:
                    logging.info("Strategy does not recommend BUY at this time.")
        except Exception as e:
            logging.error(f"Main loop error: {e}")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
