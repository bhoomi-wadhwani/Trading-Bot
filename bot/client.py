"""Binance Futures Testnet client using direct REST calls (requests)."""

import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

from bot.exceptions import BinanceAPIError, BinanceClientError, BinanceRequestError
from bot.rest import FUTURES_TESTNET_API, ping_testnet

logger = logging.getLogger("trading_bot.client")

# Assignment base URL
FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
ORDER_ENDPOINT = f"{FUTURES_TESTNET_API}/order"


class BinanceFuturesClient:
    """
    USD-M Futures Testnet client via direct REST (no python-binance).

    Public endpoints (ping) work without credentials.
    Placing orders requires BINANCE_API_KEY + BINANCE_API_SECRET in .env.
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self._session = requests.Session()
        logger.info("REST client ready | base=%s", FUTURES_TESTNET_BASE_URL)

    def _require_credentials(self) -> None:
        if not self.api_key or not self.api_secret:
            raise BinanceClientError(
                "Testnet credentials missing in .env (BINANCE_API_KEY, BINANCE_API_SECRET). "
                "These are Binance account keys, not a Python library. "
                "Test without keys: python cli.py --check  OR  add --dry-run"
            )

    def _sign_params(self, params: Dict[str, Any]) -> str:
        """Build query string with HMAC-SHA256 signature (Binance Futures spec)."""
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{query}&signature={signature}"

    def ping(self) -> bool:
        """Public REST ping — no API keys required."""
        try:
            ping_testnet()
            return True
        except Exception as exc:
            raise BinanceClientError(f"Ping failed: {exc}") from exc

    def create_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /fapi/v1/order on Futures Testnet (signed REST request).

        Args:
            order_params: symbol, side, type, quantity, price, timeInForce, etc.

        Returns:
            Order JSON from Binance.
        """
        self._require_credentials()

        logger.info("REST request | POST %s | params=%s", ORDER_ENDPOINT, order_params)

        signed_query = self._sign_params(order_params)
        headers = {"X-MBX-APIKEY": self.api_key}

        try:
            response = self._session.post(
                ORDER_ENDPOINT,
                data=signed_query,
                headers=headers,
                timeout=15,
            )

            # Binance may return JSON error body with non-2xx status
            try:
                body = response.json()
            except ValueError:
                body = {"msg": response.text}

            if not response.ok:
                code = body.get("code", response.status_code)
                msg = body.get("msg", response.reason)
                logger.error("REST error | code=%s | msg=%s", code, msg)
                raise BinanceAPIError(code, msg)

            logger.info(
                "REST response | orderId=%s | status=%s",
                body.get("orderId"),
                body.get("status"),
            )
            return body

        except BinanceAPIError:
            raise
        except RequestException as exc:
            logger.error("REST network error: %s", exc)
            raise BinanceRequestError(f"Network failure: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected REST error")
            raise BinanceClientError(f"Order request failed: {exc}") from exc
