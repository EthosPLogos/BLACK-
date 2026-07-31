"""
Alpaca Markets integration — real-time stock data, options chains, account info.

Free tier: real-time SIP stock quotes, historical data, paper trading.
Options data (Greeks, IV surface, open interest): requires Alpaca options subscription.
Account/positions endpoints work on both paper and live accounts.

Set ALPACA_LIVE=true in .env to switch from paper to live trading API.
All execution (orders) requires explicit owner approval — this module is read-only.
"""
import time
from datetime import datetime, timedelta, timezone

import httpx

from app.config import ALPACA_API_KEY, ALPACA_LIVE, ALPACA_SECRET_KEY

_DATA_BASE = "https://data.alpaca.markets"
_TRADING_BASE = "https://api.alpaca.markets" if ALPACA_LIVE else "https://paper-api.alpaca.markets"
_TIMEOUT = 8.0
_CACHE_TTL = 60  # 1-minute cache — Alpaca has generous rate limits but no need to spam
_HISTORY_CACHE_TTL = 3600  # 1-hour cache for historical bars — data doesn't change intraday

_snapshot_cache: dict[str, tuple[float, dict]] = {}
_options_cache: dict[str, tuple[float, list]] = {}
_history_cache: dict[str, tuple[float, dict]] = {}
_account_cache: tuple[float, dict] | None = None


def is_configured() -> bool:
    return bool(ALPACA_API_KEY and ALPACA_SECRET_KEY)


def _headers() -> dict:
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    }


def _stale(ts: float, ttl: float = _CACHE_TTL) -> bool:
    return time.time() - ts > ttl


# ── Stock data ─────────────────────────────────────────────────────────────────

def get_snapshot(symbol: str) -> dict | None:
    """
    Full snapshot: latest quote, trade, OHLCV bar, and daily change.
    Returns None if Alpaca is not configured or symbol is invalid.
    """
    if not is_configured():
        return None

    if symbol in _snapshot_cache:
        ts, data = _snapshot_cache[symbol]
        if not _stale(ts):
            return data

    try:
        r = httpx.get(
            f"{_DATA_BASE}/v2/stocks/{symbol}/snapshot",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        raw = r.json()
        quote = raw.get("latestQuote", {})
        trade = raw.get("latestTrade", {})
        bar = raw.get("dailyBar", {})
        prev = raw.get("prevDailyBar", {})

        price = trade.get("p") or quote.get("ap")  # last trade or ask price
        prev_close = prev.get("c")
        change = None
        change_pct = None
        if price and prev_close:
            change = round(float(price) - float(prev_close), 4)
            change_pct = round((change / float(prev_close)) * 100, 2)

        result = {
            "symbol": symbol,
            "price": price,
            "bid": quote.get("bp"),
            "ask": quote.get("ap"),
            "bid_size": quote.get("bs"),
            "ask_size": quote.get("as"),
            "volume": bar.get("v"),
            "open": bar.get("o"),
            "high": bar.get("h"),
            "low": bar.get("l"),
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "vwap": bar.get("vw"),
        }
        _snapshot_cache[symbol] = (time.time(), result)
        return result
    except Exception:
        return None


def get_price_history(symbol: str, days: int = 90) -> dict | None:
    """
    Fetch daily OHLCV bars for the past `days` days.
    Returns a compact summary (first/last close, high/low, % return) rather than
    the full bar list — keeps the context window manageable for LLM synthesis.
    Full bars are available under 'bars' key if needed.
    """
    if not is_configured():
        return None

    cache_key = f"{symbol}:{days}"
    if cache_key in _history_cache:
        ts, data = _history_cache[cache_key]
        if not _stale(ts, _HISTORY_CACHE_TTL):
            return data

    try:
        start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = httpx.get(
            f"{_DATA_BASE}/v2/stocks/{symbol}/bars",
            headers=_headers(),
            params={"timeframe": "1Day", "start": start, "limit": days + 5},
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return None

        bars = r.json().get("bars", [])
        if not bars:
            return None

        closes = [b["c"] for b in bars if "c" in b]
        highs = [b["h"] for b in bars if "h" in b]
        lows = [b["l"] for b in bars if "l" in b]
        volumes = [b["v"] for b in bars if "v" in b]

        first_close = closes[0] if closes else None
        last_close = closes[-1] if closes else None
        period_return = None
        if first_close and last_close and first_close > 0:
            period_return = round(((last_close - first_close) / first_close) * 100, 2)

        result = {
            "symbol": symbol,
            "days_requested": days,
            "bars_returned": len(bars),
            "period_start": bars[0].get("t", "")[:10] if bars else None,
            "period_end": bars[-1].get("t", "")[:10] if bars else None,
            "open_price": bars[0].get("o") if bars else None,
            "latest_close": last_close,
            "period_high": max(highs) if highs else None,
            "period_low": min(lows) if lows else None,
            "period_return_pct": period_return,
            "avg_daily_volume": round(sum(volumes) / len(volumes)) if volumes else None,
        }
        _history_cache[cache_key] = (time.time(), result)
        return result
    except Exception:
        return None


def get_multiple_snapshots(symbols: list[str]) -> dict[str, dict]:
    """Batch snapshot for up to 100 symbols."""
    if not is_configured() or not symbols:
        return {}
    try:
        r = httpx.get(
            f"{_DATA_BASE}/v2/stocks/snapshots",
            params={"symbols": ",".join(symbols)},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return {}
        return r.json()
    except Exception:
        return {}


# ── Options data ───────────────────────────────────────────────────────────────

def get_options_chain(underlying: str, expiration_date: str | None = None, limit: int = 50) -> list[dict]:
    """
    Options chain snapshot with Greeks for a given underlying symbol.
    Requires Alpaca options data subscription — returns [] on free tier.
    expiration_date: "YYYY-MM-DD" filter, or None for nearest expiry.
    """
    if not is_configured():
        return []

    cache_key = f"{underlying}:{expiration_date}"
    if cache_key in _options_cache:
        ts, data = _options_cache[cache_key]
        if not _stale(ts, ttl=120):
            return data

    params: dict = {"feed": "indicative", "limit": limit}
    if expiration_date:
        params["expiration_date_gte"] = expiration_date
        params["expiration_date_lte"] = expiration_date

    try:
        r = httpx.get(
            f"{_DATA_BASE}/v1beta1/options/snapshots/{underlying}",
            params=params,
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []

        raw_contracts = r.json().get("snapshots", {})
        results = []
        for contract_sym, snap in raw_contracts.items():
            greeks = snap.get("greeks", {})
            details = snap.get("details", {})
            quote = snap.get("latestQuote", {})
            trade = snap.get("latestTrade", {})
            results.append({
                "symbol": contract_sym,
                "type": details.get("type"),          # "call" | "put"
                "strike": details.get("strike_price"),
                "expiration": details.get("expiration_date"),
                "bid": quote.get("bp"),
                "ask": quote.get("ap"),
                "last": trade.get("p"),
                "iv": snap.get("impliedVolatility"),
                "delta": greeks.get("delta"),
                "gamma": greeks.get("gamma"),
                "theta": greeks.get("theta"),
                "vega": greeks.get("vega"),
                "open_interest": snap.get("openInterest"),
                "volume": snap.get("dailyBar", {}).get("v"),
            })

        results.sort(key=lambda x: (x.get("expiration") or "", float(x.get("strike") or 0)))
        _options_cache[cache_key] = (time.time(), results)
        return results
    except Exception:
        return []


# ── Account & positions ────────────────────────────────────────────────────────

def get_account() -> dict | None:
    """Portfolio value, buying power, cash, P&L for today."""
    global _account_cache
    if not is_configured():
        return None
    if _account_cache:
        ts, data = _account_cache
        if not _stale(ts, ttl=30):
            return data
    try:
        r = httpx.get(
            f"{_TRADING_BASE}/v2/account",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        a = r.json()
        result = {
            "portfolio_value": a.get("portfolio_value"),
            "cash": a.get("cash"),
            "buying_power": a.get("buying_power"),
            "equity": a.get("equity"),
            "unrealized_pl": a.get("unrealized_pl"),
            "unrealized_plpc": a.get("unrealized_plpc"),
            "day_trade_count": a.get("daytrade_count"),
            "account_type": "live" if ALPACA_LIVE else "paper",
        }
        _account_cache = (time.time(), result)
        return result
    except Exception:
        return None


def get_positions() -> list[dict]:
    """All open positions with current P&L."""
    if not is_configured():
        return []
    try:
        r = httpx.get(
            f"{_TRADING_BASE}/v2/positions",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        return [
            {
                "symbol": p.get("symbol"),
                "qty": p.get("qty"),
                "avg_cost": p.get("avg_entry_price"),
                "current_price": p.get("current_price"),
                "market_value": p.get("market_value"),
                "unrealized_pl": p.get("unrealized_pl"),
                "unrealized_plpc": p.get("unrealized_plpc"),
                "side": p.get("side"),
            }
            for p in r.json()
        ]
    except Exception:
        return []


# ── Formatting ─────────────────────────────────────────────────────────────────

def format_snapshot_for_context(snap: dict) -> str:
    if not snap:
        return ""
    chg = f"{snap['change']:+.2f} ({snap['change_pct']:+.2f}%)" if snap.get("change") is not None else "N/A"
    return (
        f"{snap['symbol']}: ${snap['price']} | {chg} | "
        f"Bid {snap['bid']} × {snap['bid_size']} / Ask {snap['ask']} × {snap['ask_size']} | "
        f"Vol {snap['volume']} | VWAP {snap['vwap']} | "
        f"O {snap['open']} H {snap['high']} L {snap['low']} | Prev close {snap['prev_close']}"
    )


def format_options_for_context(contracts: list[dict], max_contracts: int = 20) -> str:
    if not contracts:
        return "Options data unavailable (requires Alpaca options subscription)."
    lines = ["Strike | Type | Bid | Ask | IV | Delta | Gamma | Theta | Vega | OI | Vol | Exp"]
    for c in contracts[:max_contracts]:
        iv = f"{float(c['iv'])*100:.1f}%" if c.get("iv") else "N/A"
        delta = f"{float(c['delta']):.3f}" if c.get("delta") else "N/A"
        gamma = f"{float(c['gamma']):.4f}" if c.get("gamma") else "N/A"
        theta = f"{float(c['theta']):.3f}" if c.get("theta") else "N/A"
        vega = f"{float(c['vega']):.3f}" if c.get("vega") else "N/A"
        lines.append(
            f"{c.get('strike')} | {c.get('type','?').upper()} | "
            f"{c.get('bid')} | {c.get('ask')} | {iv} | {delta} | {gamma} | {theta} | {vega} | "
            f"{c.get('open_interest')} | {c.get('volume')} | {c.get('expiration')}"
        )
    return "\n".join(lines)


def format_account_for_context(account: dict, positions: list[dict]) -> str:
    if not account:
        return ""
    acct_type = account["account_type"].upper()
    lines = [
        f"[{acct_type} ACCOUNT]",
        f"Portfolio value: ${account['portfolio_value']} | Cash: ${account['cash']} | "
        f"Buying power: ${account['buying_power']}",
        f"Unrealized P&L: ${account['unrealized_pl']} ({account['unrealized_plpc']}%)",
    ]
    if positions:
        lines.append("Open positions:")
        for p in positions:
            pl = f"${p['unrealized_pl']} ({float(p['unrealized_plpc'])*100:.2f}%)" if p.get("unrealized_pl") else "N/A"
            lines.append(
                f"  {p['symbol']} {p['side'].upper()} {p['qty']} @ avg ${p['avg_cost']} | "
                f"Now ${p['current_price']} | MV ${p['market_value']} | P&L {pl}"
            )
    return "\n".join(lines)
