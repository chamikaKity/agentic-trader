from agentic_trader.models.signal import IndicatorSet, RuleEngineResult


def evaluate(indicators: IndicatorSet) -> RuleEngineResult:
    """Apply deterministic rules to pre-filter trading signals."""
    rsi = indicators.rsi
    price = indicators.current_price
    ema20 = indicators.ema20
    atr = indicators.atr
    hist = indicators.macd_histogram
    hist_prev = indicators.macd_histogram_prev

    crosses_positive = hist > 0 and hist_prev <= 0
    crosses_negative = hist < 0 and hist_prev >= 0

    reasoning: list[str] = []

    if rsi < 35 and crosses_positive and price > ema20:
        reasoning.append(f"RSI={rsi:.2f} < 35 (oversold)")
        reasoning.append(
            f"MACD histogram crossed positive ({hist_prev:.4f} → {hist:.4f})"
        )
        reasoning.append(f"Price {price:.2f} > EMA20 {ema20:.2f}")
        return RuleEngineResult(signal="STRONG_BUY", rule_reasoning=reasoning)

    if rsi > 65 and crosses_negative and price < ema20:
        reasoning.append(f"RSI={rsi:.2f} > 65 (overbought)")
        reasoning.append(
            f"MACD histogram crossed negative ({hist_prev:.4f} → {hist:.4f})"
        )
        reasoning.append(f"Price {price:.2f} < EMA20 {ema20:.2f}")
        return RuleEngineResult(signal="STRONG_SELL", rule_reasoning=reasoning)

    no_crossover = not crosses_positive and not crosses_negative
    if 40 <= rsi <= 60 and no_crossover and atr / price < 0.02:
        reasoning.append(f"RSI={rsi:.2f} in neutral range 40–60")
        reasoning.append("No MACD crossover")
        reasoning.append(f"ATR/price={atr / price:.4f} < 2%")
        return RuleEngineResult(signal="HOLD", rule_reasoning=reasoning)

    reasoning.append(
        f"RSI={rsi:.2f}, MACD hist={hist:.4f} (prev={hist_prev:.4f}),"
        f" price={price:.2f}, EMA20={ema20:.2f}"
    )
    reasoning.append("No deterministic rule matched — forwarding to decision engine")
    return RuleEngineResult(signal="AMBIGUOUS", rule_reasoning=reasoning)
