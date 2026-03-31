from datetime import datetime
from typing import Any

import httpx

from agentic_trader.config import settings
from agentic_trader.models.signal import NewsItem, NewsResult

_BASE_URL = "https://cryptopanic.com/api/v1/posts/"
_TIMEOUT = 5.0
_LIMIT = 5


def _symbol_to_currency(symbol: str) -> str:
    """Convert trading pair symbol to base currency, e.g. BTCUSDT → BTC."""
    for quote in ("USDT", "BTC", "ETH", "BNB", "BUSD", "USDC"):
        if symbol.upper().endswith(quote):
            return symbol.upper()[: -len(quote)]
    return symbol.upper()


def _parse_item(item: dict[str, Any]) -> NewsItem | None:  # Any: httpx JSON is untyped
    """Parse a single CryptoPanic post dict into a NewsItem. Returns None on failure."""
    try:
        title: str = str(item["title"])
        source_obj: dict[str, Any] = item.get("source") or {}  # Any: JSON dict
        source: str = str(source_obj.get("domain", "unknown"))
        published_at: datetime = datetime.fromisoformat(
            str(item["published_at"]).replace("Z", "+00:00")
        )
        votes: dict[str, Any] = item.get("votes") or {}  # Any: JSON dict
        bullish: int = int(votes.get("positive", 0))
        bearish: int = int(votes.get("negative", 0))
        total: int = int(votes.get("total", 0))
        sentiment: float = (bullish - bearish) / max(total, 1)
        return NewsItem(
            title=title,
            source=source,
            published_at=published_at,
            sentiment=sentiment,
        )
    except Exception:  # noqa: BLE001
        return None


async def fetch_news(symbol: str) -> NewsResult:
    """Fetch top 5 CryptoPanic news items for the given trading symbol.

    Always returns a NewsResult — never raises. On any failure, returns
    NewsResult(available=False).
    """
    currency = _symbol_to_currency(symbol)
    params: dict[str, str] = {
        "auth_token": settings.cryptopanic_api_key,
        "currencies": currency,
        "kind": "news",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_BASE_URL, params=params)
            if response.status_code != 200:
                return NewsResult(available=False)

            data: dict[str, Any] = response.json()  # Any: httpx JSON is untyped
            raw_results: list[dict[str, Any]] = data.get("results", [])  # Any: JSON

            items: list[NewsItem] = []
            bullish_total = 0
            bearish_total = 0
            votes_total = 0

            for raw in raw_results[:_LIMIT]:
                parsed = _parse_item(raw)
                if parsed is not None:
                    items.append(parsed)
                votes: dict[str, Any] = raw.get("votes") or {}  # Any: JSON dict
                bullish_total += int(votes.get("positive", 0))
                bearish_total += int(votes.get("negative", 0))
                votes_total += int(votes.get("total", 0))

            if not items:
                return NewsResult(available=False)

            sentiment_score: float = (bullish_total - bearish_total) / max(
                votes_total, 1
            )

            return NewsResult(
                available=True,
                items=items,
                sentiment_score=sentiment_score,
            )

    except Exception:  # noqa: BLE001
        return NewsResult(available=False)
