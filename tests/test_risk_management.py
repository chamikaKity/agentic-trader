from agentic_trader.agents.risk_management import compute


def test_normal_volatility() -> None:
    # ATR/price = 0.02 (2%) → NORMAL
    result = compute(current_price=10_000.0, atr=200.0, confidence=None)
    assert result.volatility == "NORMAL"
    assert result.position_warning is None


def test_high_volatility_high_confidence() -> None:
    # ATR/price = 0.04 (4%) → HIGH, confidence >= 0.6 → no warning
    result = compute(current_price=10_000.0, atr=400.0, confidence=0.8)
    assert result.volatility == "HIGH"
    assert result.position_warning is None


def test_high_volatility_low_confidence_caution() -> None:
    # ATR/price = 0.04 (4%) → HIGH, confidence < 0.6 → CAUTION
    result = compute(current_price=10_000.0, atr=400.0, confidence=0.5)
    assert result.volatility == "HIGH"
    assert result.position_warning == "CAUTION"


def test_high_volatility_no_confidence() -> None:
    # ATR/price = 0.04 (4%) → HIGH, confidence=None (LLM not called) → no warning
    result = compute(current_price=10_000.0, atr=400.0, confidence=None)
    assert result.volatility == "HIGH"
    assert result.position_warning is None


def test_volatility_boundary_exact() -> None:
    # ATR/price = 0.03 exactly → NORMAL (spec uses strict >, not >=)
    result = compute(current_price=10_000.0, atr=300.0, confidence=None)
    assert result.volatility == "NORMAL"


def test_risk_reward_ratio() -> None:
    # stop distance = 1.5 * ATR, target distance = 2.5 * ATR
    # R/R = 2.5 / 1.5 ≈ 1.667
    result = compute(current_price=10_000.0, atr=200.0, confidence=None)
    assert result.stop_loss == 10_000.0 - 1.5 * 200.0
    assert result.take_profit == 10_000.0 + 2.5 * 200.0
    assert abs(result.risk_reward - (2.5 / 1.5)) < 0.001
