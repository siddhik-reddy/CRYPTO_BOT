"""
Symbol information and validation helpers
"""
from typing import Dict, Tuple, Optional
import math
from bot.client import BinanceClient

class SymbolInfo:
    """Cache and validate trading rules for symbols"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self._cache = {}  # Cache exchange info
        
    def get_exchange_info(self) -> dict:
        """Get exchange info with caching"""
        if not self._cache:
            self._cache = self.client.get_exchange_info()
        return self._cache
    
    def get_symbol_filters(self, symbol: str) -> dict:
        """Get trading filters for a specific symbol"""
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                filters = {}
                for f in s["filters"]:
                    filter_type = f["filterType"]
                    filters[filter_type] = f
                return filters
        raise ValueError(f"Symbol {symbol} not found")
    
    def validate_price(self, symbol: str, price: float) -> float:
        """Validate and adjust price according to symbol rules"""
        filters = self.get_symbol_filters(symbol)
        price_filter = filters.get("PRICE_FILTER")
        
        if not price_filter:
            raise ValueError(f"No PRICE_FILTER found for {symbol}")
        
        min_price_val = float(price_filter.get("minPrice", 0))
        max_price_val = float(price_filter.get("maxPrice", 0))
        tick_size = float(price_filter.get("tickSize", 0))
        
        # Validate min/max price
        if price < min_price_val:
            raise ValueError(
                f"Price {price} is below minimum {min_price_val} for {symbol}"
            )
        if max_price_val > 0 and price > max_price_val:
            raise ValueError(
                f"Price {price} is above maximum {max_price_val} for {symbol}"
            )
        
        # Adjust to valid tick size
        if tick_size > 0:
            price = round(price / tick_size) * tick_size
            precision = abs(int(math.log10(tick_size)))
            price = round(price, precision)
        
        return price
    
    def validate_quantity(self, symbol: str, quantity: float, order_type: str = "LIMIT") -> float:
        """Validate and adjust quantity according to symbol rules"""
        filters = self.get_symbol_filters(symbol)
        lot_size = filters.get("LOT_SIZE")
        market_lot = filters.get("MARKET_LOT_SIZE", lot_size)
        
        # Use appropriate lot size based on order type
        active_lot = market_lot if order_type == "MARKET" else lot_size
        
        if not active_lot:
            raise ValueError(f"No LOT_SIZE filter found for {symbol}")
        
        min_qty = float(active_lot.get("minQty", 0))
        max_qty = float(active_lot.get("maxQty", 0))
        step_size = float(active_lot.get("stepSize", 0))
        
        # Validate min/max quantity
        if quantity < min_qty:
            raise ValueError(
                f"Quantity {quantity} is below minimum {min_qty} for {symbol}"
            )
        if max_qty > 0 and quantity > max_qty:
            raise ValueError(
                f"Quantity {quantity} is above maximum {max_qty} for {symbol}"
            )
        
        # Adjust to valid step size
        if step_size > 0:
            quantity = round(quantity / step_size) * step_size
            precision = abs(int(math.log10(step_size)))
            quantity = round(quantity, precision)
        
        return quantity
    
    def get_price_limits(self, symbol: str) -> tuple:
        """Get min and max price limits"""
        filters = self.get_symbol_filters(symbol)
        price_filter = filters.get("PRICE_FILTER", {})
        min_price = float(price_filter.get("minPrice", 0))
        max_price = float(price_filter.get("maxPrice", 999999))
        tick_size = float(price_filter.get("tickSize", 0.01))
        return min_price, max_price, tick_size
    
    def get_quantity_limits(self, symbol: str, order_type: str = "LIMIT") -> tuple:
        """Get min and max quantity limits"""
        filters = self.get_symbol_filters(symbol)
        lot_size = filters.get("LOT_SIZE", {})
        market_lot = filters.get("MARKET_LOT_SIZE", lot_size)
        
        active_lot = market_lot if order_type == "MARKET" else lot_size
        
        min_qty = float(active_lot.get("minQty", 0))
        max_qty = float(active_lot.get("maxQty", 999999))
        step_size = float(active_lot.get("stepSize", 0.001))
        
        return min_qty, max_qty, step_size
    
    def get_min_notional(self, symbol: str) -> float:
        """Get minimum notional value (price * quantity)"""
        filters = self.get_symbol_filters(symbol)
        min_notional = filters.get("MIN_NOTIONAL", {})
        return float(min_notional.get("notional", 0))
    
    def calculate_required_margin(self, symbol: str, quantity: float, price: float, leverage: int = 1) -> float:
        """Calculate required margin for an order"""
        notional = quantity * price
        return notional / leverage
    
    def get_max_quantity_by_margin(self, symbol: str, price: float, available_balance: float, leverage: int = 1) -> float:
        """Calculate maximum quantity based on available margin"""
        filters = self.get_symbol_filters(symbol)
        lot_size = filters.get("LOT_SIZE", {})
        step_size = float(lot_size.get("stepSize", 0.001))
        max_qty_allowed = float(lot_size.get("maxQty", 999999))
        
        # Calculate max quantity based on available balance
        max_notional = available_balance * leverage
        max_qty = max_notional / price
        
        # Adjust to step size
        if step_size > 0:
            max_qty = (max_qty // step_size) * step_size
            precision = abs(int(math.log10(step_size)))
            max_qty = round(max_qty, precision)
        
        # Don't exceed max quantity
        max_qty = min(max_qty, max_qty_allowed)
        
        return max_qty
    
    def get_symbol_info_display(self, symbol: str) -> str:
        """Get human-readable symbol info"""
        filters = self.get_symbol_filters(symbol)
        price_filter = filters.get("PRICE_FILTER", {})
        lot_size = filters.get("LOT_SIZE", {})
        min_notional = filters.get("MIN_NOTIONAL", {})
        
        min_price = float(price_filter.get('minPrice', 0))
        max_price = float(price_filter.get('maxPrice', 0))
        tick_size = float(price_filter.get('tickSize', 0))
        min_qty = float(lot_size.get('minQty', 0))
        max_qty = float(lot_size.get('maxQty', 0))
        step_size = float(lot_size.get('stepSize', 0))
        min_notional_val = float(min_notional.get('notional', 0))
        
        info = f"""
  Symbol Rules for {symbol}:
  ─────────────────────────────────────
  Min Price:     {min_price}
  Max Price:     {max_price if max_price > 0 else 'No limit'}
  Tick Size:     {tick_size}
  Min Quantity:  {min_qty}
  Max Quantity:  {max_qty if max_qty > 0 else 'No limit'}
  Step Size:     {step_size}
  Min Notional:  {min_notional_val} USDT
  ─────────────────────────────────────
"""
        return info