#!/usr/bin/env python3
"""
Trading Bot Launcher - Easy way to start the bot in different modes
"""
import sys
import subprocess
import os

def show_menu():
    print("\n🤖 Trading Bot Launcher")
    print("=" * 30)
    print("1. Run Multi-Pair Trading Bot (Recommended)")
    print("2. Run Single-Pair Trading Bot")  
    print("3. Run Test Suite")
    print("4. View Current Configuration")
    print("5. View Portfolio Status")
    print("6. View Recent Logs")
    print("0. Exit")
    print()

def run_multi_pair_bot():
    print("Starting Multi-Pair Trading Bot...")
    print("Press Ctrl+C to stop the bot")
    print("-" * 40)
    subprocess.run([sys.executable, "multi_pair_trading_bot.py"])

def run_single_pair_bot():
    print("Starting Single-Pair Trading Bot...")
    print("Press Ctrl+C to stop the bot")
    print("-" * 40)
    subprocess.run([sys.executable, "simple_trading_bot.py"])

def run_tests():
    print("Running Test Suite...")
    print("-" * 40)
    subprocess.run([sys.executable, "test_multi_pair.py"])

def view_config():
    print("Current Configuration:")
    print("-" * 40)
    try:
        with open("bot_config.py", "r") as f:
            content = f.read()
            # Extract key configuration values
            lines = content.split('\n')
            for line in lines:
                if any(key in line for key in ['ENABLE_MULTI_PAIR', 'TRADING_PAIRS', 'PAIR_WEIGHTS', 'STRATEGY', 'BASE_ORDER_VOLUME']):
                    if not line.strip().startswith('#') and '=' in line:
                        print(f"  {line.strip()}")
    except FileNotFoundError:
        print("  Configuration file not found!")

def view_portfolio():
    print("Getting Portfolio Status...")
    print("-" * 40)
    try:
        from luno_api import LunoAPI
        from portfolio_manager import PortfolioManager
        from bot_config import TRADING_PAIRS
        
        luno = LunoAPI()
        pm = PortfolioManager(luno)
        
        # Get portfolio summary
        summary = pm.get_portfolio_summary(TRADING_PAIRS)
        if summary:
            print(f"Total Portfolio Value: {summary['total_value_zar']:.2f} ZAR")
            print(f"Number of Positions: {summary['num_positions']}")
            print("\nCurrent Holdings:")
            for currency, allocation in summary['allocations_pct'].items():
                value = summary['holdings'][currency]
                print(f"  {currency}: {value:.2f} ZAR ({allocation:.1f}%)")
        else:
            print("Could not retrieve portfolio information")
            
    except Exception as e:
        print(f"Error retrieving portfolio: {e}")

def view_logs():
    print("Recent Log Entries (last 20 lines):")
    print("-" * 40)
    try:
        subprocess.run(["tail", "-20", "trading_bot.log"])
    except FileNotFoundError:
        print("No log file found. Run the bot first to generate logs.")

def main():
    while True:
        show_menu()
        try:
            choice = input("Select option (0-6): ").strip()
            
            if choice == "0":
                print("Goodbye! 👋")
                break
            elif choice == "1":
                run_multi_pair_bot()
            elif choice == "2":
                run_single_pair_bot()
            elif choice == "3":
                run_tests()
            elif choice == "4":
                view_config()
            elif choice == "5":
                view_portfolio()
            elif choice == "6":
                view_logs()
            else:
                print("Invalid choice. Please select 0-6.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
        except Exception as e:
            print(f"\nError: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
