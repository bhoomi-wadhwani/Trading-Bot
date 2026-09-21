# Trading Bot

A Python CLI bot for placing futures orders on the Binance Futures Testnet. Deliberately built using direct REST calls instead of the python-binance library, so every part of the request signing and HTTP communication is visible in the code.

Targets USD-M Futures on the testnet only. Supports MARKET and LIMIT orders, BUY and SELL sides, a dry-run mode that validates and prints the payload without sending anything, and a connectivity check that hits the public ping endpoint without needing API keys.

## What it does

Takes order details from the CLI, validates them, builds a signed REST payload and POSTs it to the Binance Futures Testnet API. The signing follows Binance spec: parameters are URL-encoded, a timestamp and recvWindow are added, then the whole query string gets HMAC-SHA256 signed with the API secret and appended as a signature field.

## Stack

requests - the only HTTP library used. All calls to Binance, both the public ping endpoints and the signed order POST, go through a requests Session. No python-binance, intentionally.

python-dotenv - loads BINANCE_API_KEY and BINANCE_API_SECRET from a .env file into the environment. Keeps credentials out of the code.

hmac + hashlib - both from the Python stdlib. Used to generate the HMAC-SHA256 signature that Binance requires on all authenticated endpoints. The secret is used as the key, the URL-encoded query string is the message.

argparse - stdlib CLI parser. Handles all the flags: --symbol, --side, --type, --quantity, --price, --dry-run, --check.

## Module breakdown

cli.py - the entry point. Parses CLI args and routes to either a connectivity check, a dry run, or a real order.

bot/validators.py - validates every input before anything reaches the API. Symbol, side, type, quantity and price all go through here. Returns a frozen OrderParams dataclass or raises a ValidationError with a clear message.

bot/client.py - the signed REST client. Builds the HMAC signature, attaches the API key header and POSTs to /fapi/v1/order. Also handles the response, distinguishing between Binance API errors (which come back as JSON with a code field) and network failures.

bot/orders.py - the business logic layer between the CLI and the client. Builds the request payload from validated params, handles the dry-run path, formats the order summary and result for console output, and wraps client errors into cleaner messages.

bot/rest.py - public REST calls only. Ping and server time, no authentication needed. Used for the --check command.

bot/exceptions.py - three custom exceptions: BinanceAPIError for when Binance rejects the request, BinanceRequestError for network failures, BinanceClientError for credential and config issues.

bot/logging_config.py - sets up logging to both the console and a log file at logs/trading_bot.log. Every REST request, response and error gets logged.