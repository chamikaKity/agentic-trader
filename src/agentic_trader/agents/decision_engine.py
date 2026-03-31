import json

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

from agentic_trader.config import settings
from agentic_trader.models.signal import IndicatorSet, LLMDecision, NewsResult

_MODEL = "claude-sonnet-4-20250514"

# fmt: off
_SYSTEM_PROMPT = (
    "You are a quantitative crypto trading analyst. You will be given:\n"
    "1. Technical indicators for a crypto asset\n"
    "2. Recent news sentiment summary\n"
    "3. Current price context\n"
    "\n"
    "Your task is to reason step-by-step and output a JSON object with:\n"
    '- decision: "BUY" | "SELL" | "HOLD"\n'
    "- confidence: 0.0\u20131.0\n"
    "- reasoning: a 2-3 sentence explanation\n"
    '- risk_flags: list of concern strings (e.g. "high volatility", "bearish news divergence")\n'  # noqa: E501
    "\n"
    "Be conservative. When in doubt, output HOLD.\n"
    "Respond ONLY with valid JSON."
)
# fmt: on

_SAFE_DEFAULT = LLMDecision(
    action="HOLD",
    confidence=0.5,
    reasoning="LLM response could not be parsed",
    risk_flags=["llm_parse_error"],
)


def _build_user_message(indicators: IndicatorSet, news: NewsResult) -> str:
    news_summary = (
        f"sentiment_score={news.sentiment_score:.2f}, items={len(news.items)}"
        if news.available
        else "unavailable"
    )
    headlines = (
        "\n".join(f"  - {item.title}" for item in news.items[:5])
        if news.available and news.items
        else "  (none)"
    )
    macd_line = (
        f"MACD histogram: {indicators.macd_histogram:.4f}"
        f" (prev: {indicators.macd_histogram_prev:.4f})"
    )
    bb_line = (
        f"Bollinger Bands: upper={indicators.bb_upper:.2f}"
        f", lower={indicators.bb_lower:.2f}"
        f", position={indicators.bb_position}"
    )
    return (
        f"Symbol: {indicators.symbol}  Interval: {indicators.interval}\n"
        f"Current price: {indicators.current_price}\n"
        f"RSI(14): {indicators.rsi:.2f}\n"
        f"{macd_line}\n"
        f"{bb_line}\n"
        f"EMA20: {indicators.ema20:.2f}  EMA50: {indicators.ema50:.2f}\n"
        f"ATR(14): {indicators.atr:.2f}\n"
        f"News: {news_summary}\n"
        f"Headlines:\n{headlines}"
    )


async def decide(indicators: IndicatorSet, news: NewsResult) -> LLMDecision:
    """Call Claude to resolve an AMBIGUOUS rule-engine signal.

    Never raises — returns _SAFE_DEFAULT on any failure.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_message(indicators, news)}
            ],
        )
        block = message.content[0]
        if not isinstance(block, TextBlock):
            return _SAFE_DEFAULT
        parsed = json.loads(block.text)
        return LLMDecision(
            action=parsed["decision"],
            confidence=float(parsed["confidence"]),
            reasoning=str(parsed["reasoning"]),
            risk_flags=list(parsed.get("risk_flags", [])),
        )
    except Exception:  # noqa: BLE001
        return _SAFE_DEFAULT
