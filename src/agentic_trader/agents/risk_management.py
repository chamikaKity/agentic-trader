from typing import Literal

from agentic_trader.models.signal import RiskResult


def compute(current_price: float, atr: float, confidence: float | None) -> RiskResult:
    stop_loss = current_price - (1.5 * atr)
    take_profit = current_price + (2.5 * atr)
    risk_reward = (take_profit - current_price) / (current_price - stop_loss)
    volatility: Literal["HIGH", "NORMAL"] = (
        "HIGH" if atr / current_price > 0.03 else "NORMAL"
    )
    position_warning: str | None = (
        "CAUTION"
        if volatility == "HIGH" and confidence is not None and confidence < 0.6
        else None
    )
    return RiskResult(
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward=risk_reward,
        volatility=volatility,
        position_warning=position_warning,
    )
