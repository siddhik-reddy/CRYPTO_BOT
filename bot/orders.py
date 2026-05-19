from bot.client import BinanceClient
from bot.logging_config import get_logger

logger = get_logger(__name__)

ENDPOINT = "/fapi/v1/order"


def place_market_order(client: BinanceClient, symbol: str, side: str, quantity: float) -> dict:
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": "MARKET",
        "quantity": quantity,
    }
    logger.info(f"Placing MARKET order — {side} {quantity} {symbol}")
    return client.post(ENDPOINT, params)


def place_limit_order(client: BinanceClient, symbol: str, side: str, quantity: float, price: float) -> dict:
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": "LIMIT",
        "quantity": quantity,
        "price": price,
        "timeInForce": "GTC",   # Good Till Cancelled — standard default
    }
    logger.info(f"Placing LIMIT order — {side} {quantity} {symbol} @ {price}")
    return client.post(ENDPOINT, params)


def place_stop_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float
) -> dict:
    """
    STOP_LIMIT bonus order type.
    stop_price triggers the order; price is what it executes at.
    """
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": "STOP",
        "quantity": quantity,
        "price": price,
        "stopPrice": stop_price,
        "timeInForce": "GTC",
    }
    logger.info(f"Placing STOP_LIMIT order — {side} {quantity} {symbol} | stop={stop_price}, limit={price}")
    return client.post(ENDPOINT, params)


def format_response(response: dict) -> str:
    """
    Formats the raw Binance response into something readable for the terminal.
    Only shows fields that actually have values.
    """
    lines = [
        "",
        "  ─────────────────────────────",
        "   Order Response",
        "  ─────────────────────────────",
        f"   Order ID    : {response.get('orderId', 'N/A')}",
        f"   Symbol      : {response.get('symbol', 'N/A')}",
        f"   Side        : {response.get('side', 'N/A')}",
        f"   Type        : {response.get('type', 'N/A')}",
        f"   Status      : {response.get('status', 'N/A')}",
        f"   Quantity    : {response.get('origQty', 'N/A')}",
        f"   Executed    : {response.get('executedQty', '0')}",
    ]

    avg_price = response.get("avgPrice") or response.get("price")
    if avg_price and float(avg_price) > 0:
        lines.append(f"   Avg Price   : {avg_price}")

    lines += ["  ─────────────────────────────", ""]
    return "\n".join(lines)
