#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet trading bot.

Examples:
    python cli.py --check
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
"""

import argparse
import sys
from typing import List, Optional

from bot.exceptions import BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import OrderPlacementError, OrderService, dry_run_order
from bot.rest import RestConnectionError, ping_testnet
from bot.validators import ValidationError

logger = setup_logging()


def build_parser() -> argparse.ArgumentParser:
    """Configure and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Binance Futures Testnet Trading Bot — place MARKET or LIMIT orders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Test connection (NO API keys, NO website login needed):
    python cli.py --check

  Validate order only (NO API keys):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run

  Real order (needs .env API keys from testnet):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
        """,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Test Futures Testnet connectivity via public REST (no API keys)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print order payload without placing an order",
    )
    parser.add_argument(
        "--symbol",
        help="Futures trading pair (e.g. BTCUSDT)",
    )
    parser.add_argument(
        "--side",
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--quantity",
        type=float,
        help="Order quantity (must be > 0)",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required when --type is LIMIT)",
    )

    return parser


def _require_order_args(args: argparse.Namespace) -> None:
    """Ensure all order fields are present when placing or dry-running an order."""
    missing = []
    if not args.symbol:
        missing.append("--symbol")
    if not args.side:
        missing.append("--side")
    if not args.order_type:
        missing.append("--type")
    if args.quantity is None:
        missing.append("--quantity")

    if missing:
        raise ValidationError(
            f"Missing required arguments: {', '.join(missing)}. "
            "Or use --check to test connectivity without placing an order."
        )


def run_connection_check() -> int:
    """Ping the testnet using a public REST endpoint."""
    print("\n  Checking Binance Futures Testnet (public REST, no API keys)...\n")
    try:
        result = ping_testnet()
        print("-" * 50)
        print("  CONNECTION OK")
        print("-" * 50)
        print(f"  Base URL     : {result['base_url']}")
        print(f"  Ping URL     : {result['ping_url']}")
        print(f"  HTTP Status  : {result['status_code']}")
        print(f"  Server Time  : {result['server_time']}")
        print("-" * 50)
        print("  [OK] Testnet API is reachable from your machine\n")
        return 0
    except RestConnectionError as exc:
        print(f"\n  [FAIL] Connection failed: {exc}\n")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Parse CLI arguments and run check, dry-run, or live order.

    Returns:
        Exit code: 0 on success, non-zero on failure.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check:
        logger.info("CLI invoked | mode=check")
        return run_connection_check()

    try:
        _require_order_args(args)
    except ValidationError as exc:
        print(f"\n  Validation Error: {exc}\n")
        return 1

    logger.info(
        "CLI invoked | symbol=%s side=%s type=%s quantity=%s price=%s dry_run=%s",
        args.symbol,
        args.side,
        args.order_type,
        args.quantity,
        args.price,
        args.dry_run,
    )

    if args.dry_run:
        try:
            dry_run_order(
                symbol=args.symbol,
                side=args.side,
                order_type=args.order_type,
                quantity=args.quantity,
                price=args.price,
            )
            print("  [OK] Dry run successful - validation and payload look correct\n")
            return 0
        except ValidationError as exc:
            print(f"\n  Validation Error: {exc}\n")
            return 1

    service = OrderService()

    try:
        service.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
        return 0

    except ValidationError as exc:
        print(f"\n  Validation Error: {exc}\n")
        logger.warning("Validation error: %s", exc)
        return 1

    except BinanceAPIError:
        return 1

    except OrderPlacementError as exc:
        print(f"\n  Failed: {exc}\n")
        return 1

    except KeyboardInterrupt:
        print("\n  Operation cancelled by user.\n")
        logger.info("User cancelled operation")
        return 130

    except Exception as exc:
        print(f"\n  Unexpected error: {exc}\n")
        logger.exception("Unhandled exception in CLI")
        return 1


if __name__ == "__main__":
    sys.exit(main())
