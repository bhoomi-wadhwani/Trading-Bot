# Binance Futures Testnet Trading Bot

A modular Python CLI bot for placing **USD-M Futures** orders on the **Binance Futures Testnet** only. Built for assignments and interviews: clean separation of concerns, validation, logging, and structured error handling.

**Testnet base URL:** `https://testnet.binancefuture.com`

---

## Assignment: python-binance OR direct REST?

Many assignments say you may use either:

- **python-binance** library, or  
- **direct REST calls** (`requests` / `httpx`)

### What this project uses

| Topic | This project |
|-------|----------------|
| HTTP client | **`requests` only** (direct REST) |
| Library | **No `python-binance`** — removed on purpose |
| Ping / health | `GET /fapi/v1/ping` and `GET /fapi/v1/time` |
| Place order | `POST /fapi/v1/order` with HMAC-SHA256 signature |

Both approaches are valid for the assignment. This repo implements the **REST** option clearly in `bot/client.py` and `bot/rest.py`.

### Critical distinction: REST ≠ no credentials

| Term | Meaning |
|------|---------|
| **REST / python-binance** | *How* your code talks to Binance (HTTP library) |
| **API keys in `.env`** | *Who* you are on Binance (account credentials) |

**Placing real orders always requires testnet API keys** — whether you use `python-binance` or raw `requests`.  
There is no way to place signed futures orders on Binance without keys.

Public endpoints (ping) do **not** need keys. Order placement does.

---

## What works WITHOUT `.env` keys

Use these if you cannot open the testnet website or do not have keys yet.

| Command | What it does | Keys? | Website login? |
|---------|----------------|-------|----------------|
| `python cli.py --check` | Calls public REST ping + server time | No | No |
| `python cli.py ... --dry-run` | Validates input + prints order payload | No | No |
| Real order (no `--dry-run`) | Signed `POST /fapi/v1/order` | **Yes** | Yes (to create keys) |

### Mental model

```
--check      →  public HTTP GET     (no login, no keys)
--dry-run    →  your code only      (no HTTP order sent)
real order   →  signed HTTP POST    (needs BINANCE_API_KEY + BINANCE_API_SECRET in .env)
```

For many assignments, **`--check` + `--dry-run` screenshots/logs are enough** if the testnet site is blocked.

---

## Features

- Place **MARKET** and **LIMIT** orders (via signed REST)
- Support **BUY** and **SELL** sides
- Input validation (symbol, side, type, quantity, limit price)
- Formatted console output (request summary + order result)
- File + console logging (`logs/trading_bot.log`)
- **`--check`** — test connectivity without keys
- **`--dry-run`** — validate and preview payload without keys
- Credentials via `.env` (only for real orders)

---

## Project structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Signed REST order placement (requests)
│   ├── rest.py            # Public REST ping/time (no keys)
│   ├── exceptions.py      # API / network / client errors
│   ├── orders.py          # Order logic + console formatting
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Logging setup
├── logs/
│   └── trading_bot.log    # Created at runtime
├── cli.py                 # CLI entry point (argparse)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requirements

- Python 3.8+
- `pip install -r requirements.txt`
- **Optional:** Binance Futures Testnet account + API keys (only for real orders)

Dependencies:

- `requests` — all HTTP calls to Binance
- `python-dotenv` — load `.env` credentials

---

## Setup

### 1. Go to project folder

```bash
cd trading_bot
```

Windows example:

```powershell
cd "c:\Users\bhoom\OneDrive\Documents\Projects\Primetrade.ai assinment\trading_bot"
```

### 2. Virtual environment (recommended)

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys (ONLY for real orders)

**Skip this step** if you only use `--check` and `--dry-run`.

```bash
copy .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

**Where to get keys:**

1. Open [testnet.binancefuture.com](https://testnet.binancefuture.com/)
2. Log in / register
3. **API Management** → Create API key
4. Paste key + secret into `.env`
5. Fund testnet wallet before trading

**If the website is blocked:** try VPN, mobile hotspot, or ask your instructor. You can still demo the bot with `--check` and `--dry-run` without keys.

---

## Usage

Run all commands from the `trading_bot` directory.

### Step A — Test connection (no keys, no website)

Proves your machine can reach the Futures Testnet API:

```bash
python cli.py --check
```

Expected: `CONNECTION OK`, HTTP status `200`, server time printed.

Uses:

- `GET https://testnet.binancefuture.com/fapi/v1/ping`
- `GET https://testnet.binancefuture.com/fapi/v1/time`

---

### Step B — Dry run (no keys)

Validates your order and shows the exact REST payload **without** sending it:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run
```

Limit example:

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000 --dry-run
```

---

### Step C — Validation test (no keys)

LIMIT orders require `--price`. This should fail with a clear message:

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001
```

Expected: `price is required for LIMIT orders.`

---

### Step D — Real orders (needs `.env` keys)

**Do not** add `--dry-run`. Requires valid `BINANCE_API_KEY` and `BINANCE_API_SECRET` in `.env`.

Market order (BUY):

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Limit order (SELL):

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
```

Console output includes:

- Order request summary  
- `orderId`, `status`, `executedQty`, `avgPrice` (when available)  
- `[OK] Order placed successfully` or `[FAIL]` with error details  

---

## CLI reference

| Argument | Required | Description |
|----------|----------|-------------|
| `--check` | No | Test testnet connectivity (public REST, no keys) |
| `--dry-run` | No | Validate only; do not send order |
| `--symbol` | For orders | Futures pair (e.g. `BTCUSDT`) |
| `--side` | For orders | `BUY` or `SELL` |
| `--type` | For orders | `MARKET` or `LIMIT` |
| `--quantity` | For orders | Positive number |
| `--price` | LIMIT only | Limit price (positive number) |

---

## Architecture

| Layer | Module | Responsibility |
|-------|--------|----------------|
| CLI | `cli.py` | `argparse`, `--check`, `--dry-run`, exit codes |
| Business | `bot/orders.py` | Validation, payloads, formatted output |
| Validation | `bot/validators.py` | Symbol, side, type, quantity, price rules |
| Public REST | `bot/rest.py` | Ping / time (no authentication) |
| Signed REST | `bot/client.py` | HMAC-signed `POST /fapi/v1/order` |
| Errors | `bot/exceptions.py` | `BinanceAPIError`, `BinanceRequestError`, etc. |
| Logging | `bot/logging_config.py` | Console + file logs |

**Endpoints used:**

| Action | HTTP | Path |
|--------|------|------|
| Health check | GET | `/fapi/v1/ping` |
| Server time | GET | `/fapi/v1/time` |
| Place order | POST | `/fapi/v1/order` (signed) |

**Not used:** Spot trading endpoints (`api.binance.com` spot APIs).

---

## Logging

Logs are written to:

- **Console** (stdout)
- **`logs/trading_bot.log`**

Logged events:

- REST requests and responses  
- Validation failures  
- Binance error codes and messages  
- Network errors  

---

## Error handling

| Scenario | What happens |
|----------|----------------|
| Invalid CLI input | `ValidationError` → exit code `1` |
| Binance rejects order | `BinanceAPIError` with code + message → exit `1` |
| Network failure | `BinanceRequestError` → exit `1` |
| Missing `.env` keys on real order | `BinanceClientError` → suggests `--check` or `--dry-run` |

---

## Troubleshooting

### `API credentials missing. Set BINANCE_API_KEY...`

**Cause:** You ran a **real order** without creating `.env`, or `.env` is empty.

**Fix (pick one):**

1. **No keys yet** — add `--dry-run` to your command, or run `python cli.py --check`
2. **Have keys** — `copy .env.example .env`, fill in keys, run again

### `price is required for LIMIT orders`

**Cause:** `--type LIMIT` without `--price`.

**Fix:** Add `--price 65000` (or use `--dry-run` to test).

### `Cannot reach Binance Futures Testnet`

**Cause:** Firewall, no internet, or regional blocking.

**Fix:** Check network, try VPN, run `python cli.py --check` again.

### Site testnet.binancefuture.com won't open

**You can still:**

- Run `python cli.py --check` (API may work even if the website UI does not)
- Run all orders with `--dry-run`
- Submit assignment with logs from `logs/trading_bot.log`

**For live orders:** you need keys from the website (VPN may help).

---

## Security notes

- Never commit `.env` or real API keys.
- Use **testnet keys only** — this project targets Futures Testnet, not mainnet.
- `.env` is in `.gitignore`.

---

## Quick command cheat sheet

```bash
# Install
pip install -r requirements.txt

# No keys needed
python cli.py --check
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run

# Keys required (.env)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
```

---

## License

MIT — use freely for learning and assignments.
