import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:

    def __init__(self, api_key: str, api_secret: str):
        self.api_key    = api_key
        self.api_secret = api_secret
        self._sync_time()

    def _sync_time(self):
        """Synchronize time with Binance server"""
        try:
            r = requests.get(f"{BASE_URL}/fapi/v1/time")
            self._server_time = r.json()["serverTime"]
            self._fetched_at  = int(time.time() * 1000)
            logger.debug(f"Time synced. Offset: {self._server_time - self._fetched_at}ms")
        except Exception as e:
            logger.warning(f"Failed to sync time: {e}")
            self._server_time = int(time.time() * 1000)
            self._fetched_at = self._server_time

    def _now(self) -> int:
        """Get current timestamp synchronized with Binance server"""
        elapsed = int(time.time() * 1000) - self._fetched_at
        return self._server_time + elapsed

    def get_exchange_info(self) -> dict:
        """Get exchange info (no auth required)"""
        resp = requests.get(f"{BASE_URL}/fapi/v1/exchangeInfo")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get exchange info: {resp.text}")
        return resp.json()

    def get_account_info(self) -> dict:
        """Get account information"""
        return self.get("/fapi/v2/account")

    def get_balance_for_asset(self, asset: str = "USDT") -> float:
        """Get available balance for a specific asset"""
        try:
            balances = self.get("/fapi/v2/balance")
            for b in balances:
                if b.get("asset") == asset:
                    return float(b.get("availableBalance", 0))
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    def get_current_price(self, symbol: str) -> float:
        """Get current mark price for a symbol"""
        try:
            data = self.get("/fapi/v1/premiumIndex", {"symbol": symbol})
            return float(data.get("markPrice", 0))
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0.0

    def get(self, endpoint: str, params: dict = None) -> dict:
        """GET request with signature"""
        if params is None:
            params = {}
        
        params["timestamp"] = self._now()
        params["recvWindow"] = 5000
        
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{BASE_URL}{endpoint}?{query}&signature={signature}"
        
        resp = requests.get(url, headers={"X-MBX-APIKEY": self.api_key})
        
        if resp.status_code != 200:
            try:
                err = resp.json()
                code = err.get("code", "unknown")
                msg = err.get("msg", resp.text)
                logger.error(f"Binance API error [{code}]: {msg}")
                raise RuntimeError(f"Binance error {code}: {msg}")
            except RuntimeError:
                raise
            except Exception:
                raise RuntimeError(resp.text)
        
        return resp.json()

    def post(self, endpoint: str, params: dict) -> dict:
        """POST request with signature"""
        current_time = int(time.time() * 1000)
        if current_time - self._fetched_at > 3600000:
            self._sync_time()

        params["timestamp"] = self._now()
        params["recvWindow"] = 5000

        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        url = f"{BASE_URL}{endpoint}?{query}&signature={signature}"

        try:
            resp = requests.post(url, headers={"X-MBX-APIKEY": self.api_key})
            
            if resp.status_code != 200:
                try:
                    err = resp.json()
                    code = err.get("code", "unknown")
                    msg = err.get("msg", resp.text)
                    
                    if code == -1021:
                        logger.warning("Time sync error, re-syncing...")
                        self._sync_time()
                        params["timestamp"] = self._now()
                        query = urlencode(params)
                        signature = hmac.new(
                            self.api_secret.encode("utf-8"),
                            query.encode("utf-8"),
                            hashlib.sha256
                        ).hexdigest()
                        url = f"{BASE_URL}{endpoint}?{query}&signature={signature}"
                        resp = requests.post(url, headers={"X-MBX-APIKEY": self.api_key})
                        
                        if resp.status_code != 200:
                            logger.error(f"Binance API error [{code}]: {msg}")
                            raise RuntimeError(f"Binance error {code}: {msg}")
                        return resp.json()
                    
                    logger.error(f"Binance API error [{code}]: {msg}")
                    raise RuntimeError(f"Binance error {code}: {msg}")
                except RuntimeError:
                    raise
                except Exception as e:
                    logger.error(f"Failed to parse error response: {e}")
                    raise RuntimeError(resp.text)

            return resp.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            raise