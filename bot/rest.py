"""Direct REST calls to Binance Futures Testnet (no API keys required for public endpoints)."""

import logging
from typing import Any, Dict

import requests
from requests.exceptions import RequestException

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
FUTURES_TESTNET_API = f"{FUTURES_TESTNET_BASE_URL}/fapi/v1"

logger = logging.getLogger("trading_bot.rest")


class RestConnectionError(Exception):
    """Raised when a public REST health check fails."""


def ping_testnet(timeout: int = 10) -> Dict[str, Any]:
    """
    Call GET /fapi/v1/ping on the Futures Testnet.

    This is a **public** endpoint — no API key or account needed.

    Args:
        timeout: HTTP timeout in seconds.

    Returns:
        Dict with ok, url, and server_time fields.

    Raises:
        RestConnectionError: On network or non-2xx response.
    """
    ping_url = f"{FUTURES_TESTNET_API}/ping"
    time_url = f"{FUTURES_TESTNET_API}/time"

    logger.info("REST request | GET %s", ping_url)

    try:
        ping_resp = requests.get(ping_url, timeout=timeout)
        ping_resp.raise_for_status()

        logger.info("REST response | ping | status=%s", ping_resp.status_code)

        server_time = None
        time_resp = requests.get(time_url, timeout=timeout)
        time_resp.raise_for_status()
        server_time = time_resp.json().get("serverTime")
        logger.info("REST response | time | serverTime=%s", server_time)

        return {
            "ok": True,
            "base_url": FUTURES_TESTNET_BASE_URL,
            "ping_url": ping_url,
            "status_code": ping_resp.status_code,
            "server_time": server_time,
        }

    except RequestException as exc:
        logger.error("REST connection failed: %s", exc)
        raise RestConnectionError(
            f"Cannot reach Binance Futures Testnet at {FUTURES_TESTNET_BASE_URL}. "
            f"Check your internet or firewall. Detail: {exc}"
        ) from exc
