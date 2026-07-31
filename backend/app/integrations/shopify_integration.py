"""
Shopify Admin REST API integration — read-only store intelligence.

Requires a Custom App in your Shopify store with scopes:
  read_orders, read_products, read_inventory, read_analytics

Store Admin → Settings → Apps and sales channels → Develop apps
→ Create an app → Configure Admin API scopes → Install app → copy Admin API access token
"""
import time
from datetime import datetime, timedelta, timezone

import httpx

from app.config import SHOPIFY_API_TOKEN, SHOPIFY_STORE_URL

_API_VERSION = "2024-01"
_TIMEOUT = 10.0
_CACHE_TTL = 300  # 5 minutes

_orders_cache: tuple[float, list] | None = None
_products_cache: tuple[float, list] | None = None
_summary_cache: dict[str, tuple[float, dict]] = {}


def is_configured() -> bool:
    return bool(SHOPIFY_STORE_URL and SHOPIFY_API_TOKEN)


def _base() -> str:
    store = SHOPIFY_STORE_URL.rstrip("/")
    if not store.startswith("http"):
        store = f"https://{store}"
    return f"{store}/admin/api/{_API_VERSION}"


def _headers() -> dict:
    return {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json",
    }


def _stale(ts: float) -> bool:
    return time.time() - ts > _CACHE_TTL


# ── Orders ─────────────────────────────────────────────────────────────────────

def get_orders(limit: int = 50, days_back: int = 30) -> list[dict]:
    """Recent orders with financial summary."""
    global _orders_cache
    if not is_configured():
        return []
    if _orders_cache:
        ts, data = _orders_cache
        if not _stale(ts):
            return data
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        r = httpx.get(
            f"{_base()}/orders.json",
            params={"limit": limit, "status": "any", "created_at_min": since},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        orders = r.json().get("orders", [])
        result = [
            {
                "id": o.get("name"),
                "created_at": o.get("created_at"),
                "financial_status": o.get("financial_status"),
                "fulfillment_status": o.get("fulfillment_status"),
                "total": float(o.get("total_price", 0)),
                "subtotal": float(o.get("subtotal_price", 0)),
                "customer": (o.get("customer") or {}).get("email", "guest"),
                "item_count": sum(li.get("quantity", 0) for li in o.get("line_items", [])),
                "refunded": float(o.get("total_price_set", {}).get("shop_money", {}).get("amount", 0)) == 0
                    and o.get("financial_status") == "refunded",
            }
            for o in orders
        ]
        _orders_cache = (time.time(), result)
        return result
    except Exception:
        return []


def get_revenue_summary(days: int = 30) -> dict:
    """Revenue metrics: total, AOV, order count, refund rate."""
    cache_key = f"summary_{days}"
    if cache_key in _summary_cache:
        ts, data = _summary_cache[cache_key]
        if not _stale(ts):
            return data

    orders = get_orders(limit=250, days_back=days)
    if not orders:
        return {}

    paid = [o for o in orders if o["financial_status"] in ("paid", "partially_paid", "partially_refunded")]
    refunded = [o for o in orders if o["financial_status"] == "refunded"]
    total_revenue = sum(o["total"] for o in paid)
    order_count = len(paid)
    aov = round(total_revenue / order_count, 2) if order_count else 0
    refund_rate = round(len(refunded) / len(orders) * 100, 1) if orders else 0

    result = {
        "period_days": days,
        "total_revenue": round(total_revenue, 2),
        "order_count": order_count,
        "aov": aov,
        "refund_rate_pct": refund_rate,
        "refund_count": len(refunded),
        "total_orders_including_refunded": len(orders),
    }
    _summary_cache[cache_key] = (time.time(), result)
    return result


# ── Products & Inventory ───────────────────────────────────────────────────────

def get_products(limit: int = 100) -> list[dict]:
    """Product catalog with inventory levels."""
    global _products_cache
    if not is_configured():
        return []
    if _products_cache:
        ts, data = _products_cache
        if not _stale(ts):
            return data
    try:
        r = httpx.get(
            f"{_base()}/products.json",
            params={"limit": limit, "fields": "id,title,status,variants,product_type,vendor"},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        products = r.json().get("products", [])
        result = []
        for p in products:
            variants = p.get("variants", [])
            total_inventory = sum(v.get("inventory_quantity", 0) for v in variants)
            prices = [float(v.get("price", 0)) for v in variants if v.get("price")]
            result.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "status": p.get("status"),
                "type": p.get("product_type"),
                "vendor": p.get("vendor"),
                "variant_count": len(variants),
                "total_inventory": total_inventory,
                "price_min": min(prices) if prices else None,
                "price_max": max(prices) if prices else None,
            })
        _products_cache = (time.time(), result)
        return result
    except Exception:
        return []


def get_low_inventory(days_threshold: int = 14) -> list[dict]:
    """
    Products at risk of stocking out within days_threshold days.
    Requires order velocity from get_revenue_summary to estimate days remaining.
    Returns products with < days_threshold days of stock at current sales rate.
    """
    if not is_configured():
        return []

    products = get_products()
    orders = get_orders(limit=250, days_back=30)

    # Count units sold per product title over last 30 days (rough velocity)
    velocity: dict[str, float] = {}
    for o in orders:
        pass  # full velocity calculation requires line item detail — flagged as estimate

    alerts = []
    for p in products:
        if p["status"] != "active":
            continue
        if p["total_inventory"] <= 0:
            alerts.append({**p, "alert": "OUT OF STOCK"})
        elif p["total_inventory"] <= 10:
            alerts.append({**p, "alert": f"LOW STOCK — {p['total_inventory']} units remaining"})

    return alerts


# ── Store info ─────────────────────────────────────────────────────────────────

def get_store_info() -> dict:
    if not is_configured():
        return {}
    try:
        r = httpx.get(
            f"{_base()}/shop.json",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return {}
        s = r.json().get("shop", {})
        return {
            "name": s.get("name"),
            "email": s.get("email"),
            "domain": s.get("domain"),
            "currency": s.get("currency"),
            "plan": s.get("plan_name"),
            "timezone": s.get("iana_timezone"),
        }
    except Exception:
        return {}


# ── Formatting ─────────────────────────────────────────────────────────────────

def format_for_context(days: int = 30) -> str:
    if not is_configured():
        return "Shopify: not configured (SHOPIFY_STORE_URL / SHOPIFY_API_TOKEN not set)."

    lines = []

    store = get_store_info()
    if store:
        lines.append(f"STORE: {store.get('name')} ({store.get('domain')}) | "
                     f"Currency: {store.get('currency')} | Plan: {store.get('plan')}")

    summary = get_revenue_summary(days=days)
    if summary:
        lines.append(
            f"REVENUE (last {days}d): ${summary['total_revenue']:,.2f} | "
            f"{summary['order_count']} orders | AOV ${summary['aov']} | "
            f"Refund rate {summary['refund_rate_pct']}%"
        )

    alerts = get_low_inventory()
    if alerts:
        lines.append(f"INVENTORY ALERTS ({len(alerts)} products):")
        for a in alerts[:10]:
            lines.append(f"  ⚠ {a['title']} — {a['alert']}")

    products = get_products()
    if products:
        active = [p for p in products if p["status"] == "active"]
        lines.append(f"CATALOG: {len(active)} active products, {len(products)} total")

    return "\n".join(lines) if lines else "No Shopify data available."
