"""Order placement service — business logic separated from CLI."""

import logging
from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient
from bot.exceptions import BinanceAPIError, BinanceClientError, BinanceRequestError
from bot.validators import OrderParams, ValidationError, validate_order_params

logger = logging.getLogger("trading_bot.orders")


class OrderPlacementError(Exception):
    """Raised when order placement fails after validation."""


def _format_quantity(quantity: float) -> str:
    """Format quantity for Binance API (avoids scientific notation)."""
    return format(quantity, "f").rstrip("0").rstrip(".") or "0"


def _format_price(price: float) -> str:
    """Format price for Binance API."""
    return format(price, "f").rstrip("0").rstrip(".") or "0"


def build_order_request(params: OrderParams) -> Dict[str, Any]:
    """
    Build the POST /fapi/v1/order payload from validated params.

    Args:
        params: Validated OrderParams.

    Returns:
        Dict ready for BinanceFuturesClient.create_order.
    """
    request: Dict[str, Any] = {
        "symbol": params.symbol,
        "side": params.side,
        "type": params.order_type,
        "quantity": _format_quantity(params.quantity),
    }

    if params.order_type == "LIMIT":
        request["price"] = _format_price(params.price)  # type: ignore[arg-type]
        request["timeInForce"] = "GTC"

    return request


def format_order_summary(params: OrderParams) -> str:
    """Human-readable summary of the order about to be sent."""
    lines = [
        "-" * 50,
        "  ORDER REQUEST SUMMARY",
        "-" * 50,
        f"  Symbol   : {params.symbol}",
        f"  Side     : {params.side}",
        f"  Type     : {params.order_type}",
        f"  Quantity : {params.quantity}",
    ]
    if params.price is not None:
        lines.append(f"  Price    : {params.price}")
    lines.append("-" * 50)
    return "\n".join(lines)


def format_order_result(response: Dict[str, Any], success: bool) -> str:
    """Format Binance order response for console output."""
    order_id = response.get("orderId", "N/A")
    status = response.get("status", "N/A")
    executed_qty = response.get("executedQty", response.get("cumQty", "0"))
    avg_price = response.get("avgPrice")

    lines = [
        "",
        "-" * 50,
        "  ORDER RESULT",
        "-" * 50,
        f"  Order ID     : {order_id}",
        f"  Status       : {status}",
        f"  Executed Qty : {executed_qty}",
    ]

    if avg_price and str(avg_price) not in ("0", "0.0", "0.00000"):
        lines.append(f"  Avg Price    : {avg_price}")
    elif response.get("price"):
        lines.append(f"  Price        : {response.get('price')}")

    lines.append("-" * 50)
    if success:
        lines.append("  [OK] Order placed successfully")
    else:
        lines.append("  [FAIL] Order placement failed")
    lines.append("-" * 50)

    return "\n".join(lines)


def dry_run_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
) -> Dict[str, Any]:
    """Validate inputs and show payload without calling Binance."""
    params = validate_order_params(symbol, side, order_type, quantity, price)
    payload = build_order_request(params)

    print(format_order_summary(params))
    print("\n  [DRY RUN] No HTTP order sent (direct REST not called).\n")
    print("  POST https://testnet.binancefuture.com/fapi/v1/order")
    print(f"  Body params: {payload}\n")

    return payload


class OrderService:
    """High-level service for validating and placing futures orders via REST."""

    def __init__(self, client: Optional[BinanceFuturesClient] = None) -> None:
        self._client = client

    def _get_client(self) -> BinanceFuturesClient:
        if self._client is None:
            self._client = BinanceFuturesClient()
        return self._client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity,
        price=None,
    ) -> Dict[str, Any]:
        """Validate inputs, place order via REST, return response."""
        try:
            params = validate_order_params(symbol, side, order_type, quantity, price)
        except ValidationError:
            logger.warning("Validation failed for order inputs")
            raise

        print(format_order_summary(params))

        request_payload = build_order_request(params)
        logger.info("Placing order | %s %s %s", params.side, params.quantity, params.symbol)

        try:
            client = self._get_client()
            response = client.create_order(request_payload)
            print(format_order_result(response, success=True))
            return response

        except ValidationError:
            raise

        except BinanceAPIError as exc:
            print(format_order_result({"orderId": "N/A", "status": "REJECTED"}, success=False))
            print(f"\n  Error: [{exc.code}] {exc.message}\n")
            logger.error("Binance rejected order: %s", exc.message)
            raise

        except BinanceRequestError as exc:
            print(format_order_result({"orderId": "N/A", "status": "NETWORK_ERROR"}, success=False))
            print(f"\n  Error: Network failure - {exc}\n")
            logger.error("Network error: %s", exc)
            raise OrderPlacementError(str(exc)) from exc

        except BinanceClientError as exc:
            print(format_order_result({"orderId": "N/A", "status": "CLIENT_ERROR"}, success=False))
            print(f"\n  Error: {exc}\n")
            logger.error("Client error: %s", exc)
            raise OrderPlacementError(str(exc)) from exc

        except Exception as exc:
            print(format_order_result({"orderId": "N/A", "status": "ERROR"}, success=False))
            print(f"\n  Error: Unexpected failure - {exc}\n")
            logger.exception("Unexpected error in place_order")
            raise OrderPlacementError(f"Unexpected error: {exc}") from exc
