"""Input validation for order placement."""

from dataclasses import dataclass
from typing import Optional

VALID_SIDES = frozenset({"BUY", "SELL"})
VALID_ORDER_TYPES = frozenset({"MARKET", "LIMIT"})


class ValidationError(Exception):
    """Raised when user input fails validation."""


@dataclass(frozen=True)
class OrderParams:
    """Validated order parameters ready for the API layer."""

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None


def _require_non_empty(value: str, field_name: str) -> str:
    """Ensure a string field is present and non-empty."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} is required and cannot be empty.")
    return str(value).strip()


def _parse_positive_float(value, field_name: str) -> float:
    """Parse and validate a positive numeric value."""
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid positive number.") from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")

    return parsed


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
) -> OrderParams:
    """
    Validate CLI / programmatic order inputs.

    Args:
        symbol: Trading pair (e.g. BTCUSDT).
        side: BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity: Order quantity.
        price: Limit price (required for LIMIT orders).

    Returns:
        OrderParams with normalized values.

    Raises:
        ValidationError: If any field is invalid.
    """
    symbol_clean = _require_non_empty(symbol, "symbol").upper()
    side_clean = _require_non_empty(side, "side").upper()
    type_clean = _require_non_empty(order_type, "type").upper()

    if side_clean not in VALID_SIDES:
        raise ValidationError(f"side must be one of: {', '.join(sorted(VALID_SIDES))}")

    if type_clean not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"type must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}"
        )

    qty = _parse_positive_float(quantity, "quantity")

    price_value: Optional[float] = None
    if type_clean == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders.")
        price_value = _parse_positive_float(price, "price")
    elif price is not None:
        raise ValidationError("price should only be provided for LIMIT orders.")

    return OrderParams(
        symbol=symbol_clean,
        side=side_clean,
        order_type=type_clean,
        quantity=qty,
        price=price_value,
    )
