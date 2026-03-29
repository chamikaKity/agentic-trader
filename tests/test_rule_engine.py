from agentic_trader.agents.rule_engine import evaluate
from agentic_trader.models.signal import IndicatorSet


def make_indicators(**overrides: float | str) -> IndicatorSet:
    defaults: dict[str, float | str] = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "current_price": 50000.0,
        "rsi": 50.0,
        "macd_histogram": 0.5,
        "macd_histogram_prev": 0.3,
        "macd_line": 1.0,
        "signal_line": 0.5,
        "bb_upper": 52000.0,
        "bb_lower": 48000.0,
        "bb_position": "inside",
        "ema20": 49000.0,
        "ema50": 48000.0,
        "atr": 500.0,
        "volume_sma20": 100.0,
    }
    defaults.update(overrides)
    return IndicatorSet(**defaults)  # type: ignore[arg-type]


def test_strong_buy() -> None:
    indicators = make_indicators(
        rsi=30.0,
        macd_histogram=0.1,
        macd_histogram_prev=-0.1,
        current_price=50000.0,
        ema20=49000.0,
    )
    result = evaluate(indicators)
    assert result.signal == "STRONG_BUY"
    assert any("RSI" in r for r in result.rule_reasoning)
    assert any("crossed positive" in r for r in result.rule_reasoning)


def test_strong_sell() -> None:
    indicators = make_indicators(
        rsi=70.0,
        macd_histogram=-0.1,
        macd_histogram_prev=0.1,
        current_price=48000.0,
        ema20=49000.0,
    )
    result = evaluate(indicators)
    assert result.signal == "STRONG_SELL"
    assert any("RSI" in r for r in result.rule_reasoning)
    assert any("crossed negative" in r for r in result.rule_reasoning)


def test_hold() -> None:
    indicators = make_indicators(
        rsi=50.0,
        macd_histogram=0.3,
        macd_histogram_prev=0.2,  # no crossover — both positive
        current_price=50000.0,
        atr=100.0,  # atr/price = 0.002 < 2%
    )
    result = evaluate(indicators)
    assert result.signal == "HOLD"
    assert any("40" in r or "neutral" in r for r in result.rule_reasoning)


def test_ambiguous_oversold_but_bearish_macd() -> None:
    """RSI oversold but MACD hasn't crossed positive — conflicting signals."""
    indicators = make_indicators(
        rsi=30.0,
        macd_histogram=-0.5,  # still bearish
        macd_histogram_prev=-0.3,
        current_price=50000.0,
        ema20=49000.0,
    )
    result = evaluate(indicators)
    assert result.signal == "AMBIGUOUS"


def test_macd_edge_histogram_zero_no_crossover() -> None:
    """Histogram was negative, now exactly zero — crossover should NOT fire."""
    indicators = make_indicators(
        rsi=30.0,
        macd_histogram=0.0,  # exactly zero: not > 0, so no positive crossover
        macd_histogram_prev=-0.2,
        current_price=50000.0,
        ema20=49000.0,
    )
    result = evaluate(indicators)
    # No positive crossover means STRONG_BUY cannot fire
    assert result.signal != "STRONG_BUY"


def test_macd_edge_histogram_negative_to_positive_crossover() -> None:
    """Histogram was negative, now positive — crossover SHOULD fire."""
    indicators = make_indicators(
        rsi=30.0,
        macd_histogram=0.01,  # just crossed above zero
        macd_histogram_prev=-0.01,
        current_price=50000.0,
        ema20=49000.0,
    )
    result = evaluate(indicators)
    assert result.signal == "STRONG_BUY"
