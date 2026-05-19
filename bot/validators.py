"""
Input validation for order parameters
"""
from bot.symbol_info import SymbolInfo

def validate_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
    stop_price: float = None,
    client=None
):
    """Validate all order inputs"""
    if side not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Must be BUY or SELL")
    
    if order_type not in ["MARKET", "LIMIT", "STOP_LIMIT"]:
        raise ValueError(f"Invalid order type: {order_type}")
    
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    
    if order_type in ["LIMIT", "STOP_LIMIT"]:
        if price is None or price <= 0:
            raise ValueError(f"Price must be positive for {order_type} orders")
    
    if order_type == "STOP_LIMIT":
        if stop_price is None or stop_price <= 0:
            raise ValueError("Stop price must be positive for STOP_LIMIT orders")
    
    # If client is provided, validate against exchange rules
    if client:
        symbol_info = SymbolInfo(client)
        
        # Validate and adjust quantity
        quantity = symbol_info.validate_quantity(symbol, quantity)
        
        # Validate and adjust price
        if price:
            price = symbol_info.validate_price(symbol, price)
        
        if stop_price:
            stop_price = symbol_info.validate_price(symbol, stop_price)
        
        # Check minimum notional
        if price:
            notional = quantity * price
            min_notional = symbol_info.get_min_notional(symbol)
            if notional < min_notional:
                raise ValueError(
                    f"Order notional {notional:.2f} USDT is below minimum "
                    f"{min_notional} USDT for {symbol}"
                )
    
    return quantity, price, stop_price