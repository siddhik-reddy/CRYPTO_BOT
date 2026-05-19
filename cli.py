#!/usr/bin/env python3
"""
Binance Futures Testnet — Trading Bot
Author: Siddhik Reddy
"""

import itertools
import sys
import threading
import time

from bot.client import BinanceClient
from bot.logging_config import get_logger
from bot.orders import format_response, place_limit_order, place_market_order, place_stop_limit_order
from bot.validators import validate_inputs
from bot.symbol_info import SymbolInfo

logger = get_logger(__name__)

# ─── Colors ───────────────────────────────────────────────────────────────────

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Regular colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

# Enable/disable colors
USE_COLORS = sys.stdout.isatty()  # Auto-detect if terminal supports colors

def colorize(text: str, color: str) -> str:
    """Apply color to text if colors are enabled"""
    if USE_COLORS:
        return f"{color}{text}{Colors.RESET}"
    return text

def c_green(text): return colorize(text, Colors.BRIGHT_GREEN)
def c_red(text): return colorize(text, Colors.BRIGHT_RED)
def c_yellow(text): return colorize(text, Colors.BRIGHT_YELLOW)
def c_cyan(text): return colorize(text, Colors.BRIGHT_CYAN)
def c_blue(text): return colorize(text, Colors.BRIGHT_BLUE)
def c_magenta(text): return colorize(text, Colors.BRIGHT_MAGENTA)
def c_bold(text): return colorize(text, Colors.BOLD)
def c_dim(text): return colorize(text, Colors.DIM)


# ─── Credentials (loaded from config.py — never hardcoded here) ───────────────
try:
    from config import API_KEY, API_SECRET
except ImportError:
    print(f"\n  {c_red('[error]')} config.py not found.")
    print("  Create config.py in the project root with:")
    print('    API_KEY    = "your_key"')
    print('    API_SECRET = "your_secret"')
    print("  Add config.py to .gitignore so it never gets committed.\n")
    sys.exit(1)


# ─── Data ─────────────────────────────────────────────────────────────────────

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "MATICUSDT",
    "LTCUSDT",
    "LINKUSDT",
    "Enter manually",
]

ABOUT = f"""
  ╔══════════════════════════════════════════════╗
  ║                   About                     ║
  ╠══════════════════════════════════════════════╣
  ║  Binance Futures Testnet Trading Bot        ║
  ║  Built for Primetrade.ai internship task    ║
  ╠══════════════════════════════════════════════╣
  ║  Author  :  Siddhik Reddy                  ║
  ║  Email   :  siddhikreddy440@gmail.com       ║
  ║  Phone   :  +91 8897350151                 ║
  ║                                             ║
  ║  For any queries feel free to reach out.   ║
  ╚══════════════════════════════════════════════╝
"""

HELP = f"""
  ╔══════════════════════════════════════════════╗
  ║                    Help                     ║
  ╠══════════════════════════════════════════════╣
  ║  How to use this bot:                       ║
  ║                                             ║
  ║  1. Run:  python cli.py                     ║
  ║  2. Pick a symbol from the menu             ║
  ║  3. Choose BUY or SELL                      ║
  ║  4. Choose order type:                      ║
  ║       MARKET    — executes immediately      ║
  ║       LIMIT     — executes at your price    ║
  ║       STOP_LIMIT— triggers at stop price    ║
  ║  5. Enter quantity (e.g. 0.01 for BTC)      ║
  ║  6. Confirm and the order is placed         ║
  ║                                             ║
  ║  Credentials:                               ║
  ║    Edit config.py with your testnet keys.   ║
  ║    Never share or commit config.py.         ║
  ║                                             ║
  ║  Logs are saved to the logs/ folder.        ║
  ╚══════════════════════════════════════════════╝
"""


# ─── Spinner ──────────────────────────────────────────────────────────────────

class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str):
        self.message     = message
        self._stop_event = threading.Event()
        self._thread     = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop_event.is_set():
                break
            sys.stdout.write(f"\r  {c_cyan(frame)}  {self.message}")
            sys.stdout.flush()
            time.sleep(0.08)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, *_):
        self._stop_event.set()
        self._thread.join()
        sys.stdout.write(f"\r{' ' * (len(self.message) + 8)}\r")
        sys.stdout.flush()


def step(label: str, ok: bool = True):
    icon = c_green("✓") if ok else c_red("✗")
    print(f"  {icon}  {label}")


# ─── Menu helpers ──────────────────────────────────────────────────────────────

def divider():
    print(f"  {c_dim('──────────────────────────────────────────')}")


def header():
    print()
    print(f"  {c_bold(c_cyan('╔══════════════════════════════════════════╗'))}")
    print(f"  {c_bold(c_cyan('║'))}     {c_bold('Binance Futures Testnet Bot')}          {c_bold(c_cyan('║'))}")
    print(f"  {c_bold(c_cyan('║'))}     {c_dim('Author: Siddhik Reddy')}                {c_bold(c_cyan('║'))}")
    print(f"  {c_bold(c_cyan('╚══════════════════════════════════════════╝'))}")
    print()


def pick(prompt: str, options: list) -> str:
    print(f"\n  {c_bold(prompt)}")
    divider()
    for i, opt in enumerate(options, 1):
        if opt == "Enter manually":
            print(f"    {c_dim(f'[{i:>2}]')}  {c_yellow(opt)}")
        elif opt in ["Exit", "Cancel"]:
            print(f"    {c_dim(f'[{i:>2}]')}  {c_red(opt)}")
        else:
            print(f"    {c_dim(f'[{i:>2}]')}  {opt}")
    divider()
    while True:
        try:
            raw = input(f"  {c_cyan('Choose:')} ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"  {c_yellow('Enter a number between 1 and ' + str(len(options)) + '.')}")
        except (ValueError, KeyboardInterrupt):
            print(f"\n  {c_yellow('Cancelled.')}\n")
            sys.exit(0)


def ask(prompt: str, cast=str, allow_back: bool = True):
    """Ask for input with validation and option to go back"""
    while True:
        try:
            raw = input(f"  {c_cyan(prompt)}: ").strip()
            if not raw:
                print(f"  {c_yellow(\"Can't be empty, try again.\")}")
                continue
            if allow_back and raw.lower() == 'back':
                return None
            return cast(raw)
        except ValueError:
            print(f"  {c_yellow(f'Invalid {cast.__name__} value, try again.')}")
        except KeyboardInterrupt:
            print(f"\n  {c_yellow('Cancelled.')}\n")
            sys.exit(0)


# ─── API Status Test ──────────────────────────────────────────────────────────

def test_api_status():
    """Test API connection and credentials"""
    print()
    divider()
    print(f"   {c_bold('API Status Test')}")
    divider()
    
    client = BinanceClient(API_KEY, API_SECRET)
    
    # Test 1: Server Time
    with Spinner("Testing server connectivity..."):
        time.sleep(0.3)
        try:
            import requests
            response = requests.get("https://testnet.binancefuture.com/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                server_time = response.json()["serverTime"]
                step("Server connectivity", ok=True)
                logger.info(f"Server time: {server_time}")
            else:
                step("Server connectivity", ok=False)
                logger.error(f"Server time request failed: {response.status_code}")
        except Exception as e:
            step("Server connectivity", ok=False)
            logger.error(f"Server connectivity error: {e}")
    
    # Test 2: Exchange Info (no auth required)
    with Spinner("Testing exchange info..."):
        time.sleep(0.3)
        try:
            response = requests.get("https://testnet.binancefuture.com/fapi/v1/exchangeInfo", timeout=5)
            if response.status_code == 200:
                data = response.json()
                symbols_count = len(data.get("symbols", []))
                step(f"Exchange info ({symbols_count} symbols available)", ok=True)
                logger.info(f"Exchange info retrieved: {symbols_count} symbols")
            else:
                step("Exchange info", ok=False)
                logger.error(f"Exchange info request failed: {response.status_code}")
        except Exception as e:
            step("Exchange info", ok=False)
            logger.error(f"Exchange info error: {e}")
    
    # Test 3: Account Balance (requires auth)
    with Spinner("Testing API authentication..."):
        time.sleep(0.3)
        try:
            balance = client.get("/fapi/v2/balance")
            total_assets = 0
            non_zero_assets = []
            
            for asset in balance:
                balance_val = float(asset.get("balance", 0))
                if balance_val > 0:
                    total_assets += 1
                    non_zero_assets.append(f"{asset['asset']}: {balance_val}")
            
            if non_zero_assets:
                step(f"API authentication {c_green('(✓)')} — {total_assets} assets with balance", ok=True)
                logger.info(f"Account balance retrieved: {total_assets} non-zero assets")
            else:
                step(f"API authentication {c_green('(✓)')} — No balance found (expected on testnet)", ok=True)
                logger.info("Account balance retrieved: no non-zero balances")
                
        except Exception as e:
            step("API authentication", ok=False)
            logger.error(f"Authentication failed: {e}")
    
    # Test 4: Position Information (requires auth)
    with Spinner("Testing position info..."):
        time.sleep(0.3)
        try:
            positions = client.get("/fapi/v2/positionRisk")
            open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
            
            if open_positions:
                step(f"Position info {c_green('(✓)')} — {len(open_positions)} open position(s)", ok=True)
                for pos in open_positions:
                    print(f"         {pos['symbol']}: {pos['positionAmt']} ({pos['unRealizedProfit']} USDT)")
            else:
                step(f"Position info {c_green('(✓)')} — No open positions", ok=True)
            logger.info(f"Position info retrieved: {len(open_positions)} open positions")
                
        except Exception as e:
            step("Position info", ok=False)
            logger.error(f"Position info error: {e}")
    
    # Summary
    print()
    divider()
    print(f"   {c_bold('API Status Summary')}")
    divider()
    print(f"   {c_green('✓')} All tests completed")
    print(f"   {c_green('✓')} Using Binance Futures Testnet")
    print(f"   {c_green('✓')} API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print()
    
    try:
        input(f"  {c_dim('Press Enter to go back...')}")
    except KeyboardInterrupt:
        print(f"\n  {c_yellow('Cancelled.')}\n")
        sys.exit(0)
    
    main_menu()


# ─── Order History ────────────────────────────────────────────────────────────

def show_order_history():
    """Show recent order history"""
    print()
    divider()
    print(f"   {c_bold('Order History')}")
    divider()
    
    client = BinanceClient(API_KEY, API_SECRET)
    
    # Get symbol for history
    symbol_choice = pick("Select Symbol", SYMBOLS)
    if symbol_choice == "Enter manually":
        symbol = ask("Type symbol (e.g. AVAXUSDT)", allow_back=True)
        if symbol is None:
            main_menu()
            return
        symbol = symbol.upper()
    else:
        symbol = symbol_choice
    
    # Get number of orders to show
    while True:
        limit = ask("Number of recent orders to show (1-100, default 20)", cast=str, allow_back=True)
        if limit is None:
            main_menu()
            return
        if limit == "":
            limit = 20
            break
        try:
            limit = int(limit)
            if 1 <= limit <= 100:
                break
            else:
                print(f"  {c_yellow('Please enter a number between 1 and 100.')}")
        except ValueError:
            print(f"  {c_yellow('Please enter a valid number.')}")
    
    with Spinner(f"Fetching order history for {symbol}..."):
        time.sleep(0.3)
        try:
            # Get all orders for the symbol
            orders = client.get("/fapi/v1/allOrders", {
                "symbol": symbol,
                "limit": limit
            })
            
            if not orders:
                step("No orders found", ok=True)
                print(f"\n  No orders found for {c_bold(symbol)}")
            else:
                step(f"Found {len(orders)} order(s)")
                
                print(f"\n  {c_bold('Recent Orders for ' + symbol + ':')}")
                print(f"  {c_dim('─' * 80)}")
                print(f"  {'Time':<20} {'Side':<6} {'Type':<12} {'Price':<12} {'Qty':<10} {'Status':<12}")
                print(f"  {c_dim('─' * 80)}")
                
                for order in orders:
                    order_time = time.strftime(
                        '%Y-%m-%d %H:%M:%S',
                        time.localtime(order.get('time', 0) / 1000)
                    )
                    side = order.get('side', '')
                    order_type = order.get('type', '')
                    price = order.get('price', '0')
                    orig_qty = order.get('origQty', '0')
                    status = order.get('status', '')
                    
                    # Color code side and status
                    side_colored = c_green(side) if side == "BUY" else c_red(side)
                    status_colored = c_green(status) if status == "FILLED" else c_yellow(status) if status == "NEW" else c_red(status)
                    
                    price_display = f"{float(price):.2f}" if float(price) > 0 else "MARKET"
                    
                    print(f"  {c_dim(order_time):<20} {side_colored:<6} {order_type:<12} {price_display:<12} {orig_qty:<10} {status_colored:<12}")
                
                print(f"  {c_dim('─' * 80)}")
                
                # Show order statistics
                total_orders = len(orders)
                filled_orders = [o for o in orders if o.get('status') == 'FILLED']
                cancelled_orders = [o for o in orders if o.get('status') == 'CANCELED']
                
                print(f"\n  {c_bold('Summary:')}")
                print(f"    Total Orders:    {total_orders}")
                print(f"    Filled Orders:   {c_green(len(filled_orders))}")
                print(f"    Cancelled Orders: {c_red(len(cancelled_orders))}")
                
                if filled_orders:
                    total_volume = sum(
                        float(o.get('origQty', 0)) * float(o.get('avgPrice', 0))
                        for o in filled_orders
                    )
                    print(f"    Total Volume:    {c_cyan(f'{total_volume:.2f} USDT')}")
        
        except Exception as e:
            step("Failed to fetch orders", ok=False)
            print(f"\n  {c_red('[error]')} {e}")
            logger.error(f"Failed to fetch order history: {e}")
    
    print()
    try:
        input(f"  {c_dim('Press Enter to go back...')}")
    except KeyboardInterrupt:
        print(f"\n  {c_yellow('Cancelled.')}\n")
        sys.exit(0)
    
    main_menu()


# ─── Account Info ─────────────────────────────────────────────────────────────

def show_account_info():
    """Show account information"""
    print()
    divider()
    print(f"   {c_bold('Account Information')}")
    divider()
    
    client = BinanceClient(API_KEY, API_SECRET)
    
    # Get account balance
    with Spinner("Fetching account balance..."):
        time.sleep(0.3)
        try:
            balance = client.get("/fapi/v2/balance")
            step("Balance fetched")
            
            print(f"\n  {c_bold('Asset Balances:')}")
            print(f"  {c_dim('─' * 50)}")
            print(f"  {'Asset':<10} {'Balance':<15} {'Available':<15}")
            print(f"  {c_dim('─' * 50)}")
            
            assets_with_balance = []
            total_usdt = 0
            
            for asset in balance:
                balance_val = float(asset.get("balance", 0))
                available_val = float(asset.get("availableBalance", 0))
                
                if balance_val > 0:
                    assets_with_balance.append(asset)
                    print(f"  {c_bold(asset['asset']):<10} {balance_val:<15.8f} {c_green(available_val):<15.8f}")
                    if asset['asset'] == 'USDT':
                        total_usdt = balance_val
            
            if not assets_with_balance:
                print(f"  {c_yellow('No assets with balance')}")
            else:
                print(f"  {c_dim('─' * 50)}")
                print(f"  {c_bold('Total USDT:')} {c_green(f'{total_usdt:.2f}')}")
            
        except Exception as e:
            step("Failed to fetch balance", ok=False)
            print(f"\n  {c_red('[error]')} {e}")
            logger.error(f"Failed to fetch balance: {e}")
    
    # Get open positions
    with Spinner("Fetching open positions..."):
        time.sleep(0.3)
        try:
            positions = client.get("/fapi/v2/positionRisk")
            open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
            
            if open_positions:
                step(f"Found {len(open_positions)} open position(s)")
                print(f"\n  {c_bold('Open Positions:')}")
                print(f"  {c_dim('─' * 80)}")
                print(f"  {'Symbol':<12} {'Side':<6} {'Size':<10} {'Entry':<12} {'PnL':<12}")
                print(f"  {c_dim('─' * 80)}")
                
                for pos in open_positions:
                    symbol = pos.get('symbol', '')
                    amt = float(pos.get('positionAmt', 0))
                    side = "LONG" if amt > 0 else "SHORT"
                    entry = float(pos.get('entryPrice', 0))
                    pnl = float(pos.get('unRealizedProfit', 0))
                    
                    side_colored = c_green(side) if side == "LONG" else c_red(side)
                    pnl_colored = c_green(f'{pnl:.4f}') if pnl >= 0 else c_red(f'{pnl:.4f}')
                    
                    print(f"  {c_bold(symbol):<12} {side_colored:<6} {abs(amt):<10.3f} {entry:<12.4f} {pnl_colored:<12}")
                
                print(f"  {c_dim('─' * 80)}")
            else:
                step("No open positions")
                
        except Exception as e:
            step("Failed to fetch positions", ok=False)
            print(f"\n  {c_red('[error]')} {e}")
            logger.error(f"Failed to fetch positions: {e}")
    
    print()
    try:
        input(f"  {c_dim('Press Enter to go back...')}")
    except KeyboardInterrupt:
        print(f"\n  {c_yellow('Cancelled.')}\n")
        sys.exit(0)
    
    main_menu()


# ─── Main menu ────────────────────────────────────────────────────────────────

def main_menu():
    header()
    choice = pick("Main Menu", [
        "Place Order", 
        "Order History", 
        "Account Info", 
        "Test API Status", 
        "Help", 
        "About", 
        "Exit"
    ])

    if choice == "Help":
        print(HELP)
        input(f"  {c_dim('Press Enter to go back...')}")
        main_menu()

    elif choice == "About":
        print(ABOUT)
        input(f"  {c_dim('Press Enter to go back...')}")
        main_menu()

    elif choice == "Exit":
        print(f"\n  {c_green('Goodbye.')}\n")
        sys.exit(0)

    elif choice == "Place Order":
        place_order_flow()
        
    elif choice == "Test API Status":
        test_api_status()
    
    elif choice == "Order History":
        show_order_history()
    
    elif choice == "Account Info":
        show_account_info()


# ─── Order flow helpers ──────────────────────────────────────────────────────

def get_validated_symbol(client):
    """Get and validate symbol with retry"""
    while True:
        symbol_choice = pick("Select Symbol", SYMBOLS)
        if symbol_choice == "Enter manually":
            symbol = ask("Type symbol (e.g. AVAXUSDT)", allow_back=True)
            if symbol is None:
                return None
            symbol = symbol.upper()
        else:
            symbol = symbol_choice
        
        # Validate symbol exists
        try:
            symbol_info = SymbolInfo(client)
            symbol_info.get_symbol_filters(symbol)
            print(symbol_info.get_symbol_info_display(symbol))
            return symbol
        except ValueError as e:
            print(f"\n  {c_red('[error]')} {e}")
            print(f"  {c_yellow('Please select a valid symbol.')}")
            continue


def get_validated_price(client, symbol, price_type="Limit price"):
    """Get and validate price with retry"""
    symbol_info = SymbolInfo(client)
    min_price, max_price, tick_size = symbol_info.get_price_limits(symbol)
    
    while True:
        # Show price limits
        max_str = f"{max_price}" if max_price < 999999 else "No limit"
        print(f"  {c_dim(f'Price range: {min_price} to {max_str} (tick: {tick_size})')}")
        
        price = ask(f"{price_type} (or 'back' to return)", cast=float, allow_back=True)
        if price is None:
            return None
        
        try:
            validated_price = symbol_info.validate_price(symbol, price)
            if validated_price != price:
                print(f"  {c_yellow(f'{price_type} adjusted to: {validated_price}')}")
            return validated_price
        except ValueError as e:
            print(f"  {c_red('[error]')} {e}")
            print(f"  {c_yellow('Please enter a valid price.')}")
            continue


def get_validated_quantity(client, symbol, order_type, available_balance, leverage, current_price=0):
    """Get and validate quantity with retry"""
    symbol_info = SymbolInfo(client)
    min_qty, max_qty, step_size = symbol_info.get_quantity_limits(symbol, order_type)
    
    while True:
        # Show quantity limits
        max_str = f"{max_qty}" if max_qty < 999999 else "No limit"
        print(f"  {c_dim(f'Quantity range: {min_qty} to {max_str} (step: {step_size})')}")
        
        # Show margin-based max if price available
        if current_price > 0:
            max_by_margin = symbol_info.get_max_quantity_by_margin(
                symbol, current_price, available_balance * 0.95, leverage
            )
            max_display = min(max_by_margin, max_qty if max_qty < 999999 else max_by_margin)
            print(f"  {c_dim(f'Max affordable: {max_display:.6f} (based on {available_balance:.2f} USDT)')}")
        
        quantity = ask("Quantity (or 'back'/'max')", cast=str, allow_back=True)
        
        if quantity is None:
            return None
        
        if quantity.lower() == 'max' and current_price > 0:
            max_by_margin = symbol_info.get_max_quantity_by_margin(
                symbol, current_price, available_balance * 0.95, leverage
            )
            quantity = min(max_by_margin, max_qty if max_qty < 999999 else max_by_margin)
            print(f" 
