"""Custom exceptions for Binance REST API errors."""


class BinanceClientError(Exception):
    """Configuration or client setup failure."""


class BinanceAPIError(Exception):
    """Binance returned an error response (4xx/5xx with error JSON)."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class BinanceRequestError(Exception):
    """Network or HTTP layer failure when calling Binance."""
