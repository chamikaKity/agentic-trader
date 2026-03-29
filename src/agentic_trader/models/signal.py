from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class IndicatorSet(BaseModel):
    symbol: str
    interval: str
    current_price: float
    rsi: float
    macd_histogram: float
    macd_histogram_prev: float
    macd_line: float
    signal_line: float
    bb_upper: float
    bb_lower: float
    bb_position: Literal["above", "below", "inside"]
    ema20: float
    ema50: float
    atr: float
    volume_sma20: float


class RuleEngineResult(BaseModel):
    signal: Literal["STRONG_BUY", "STRONG_SELL", "HOLD", "AMBIGUOUS"]
    rule_reasoning: list[str]


class NewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    sentiment: float


class NewsResult(BaseModel):
    available: bool
    items: list[NewsItem] = []
    sentiment_score: float = 0.0


class LLMDecision(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasoning: str
    risk_flags: list[str]


class RiskResult(BaseModel):
    stop_loss: float
    take_profit: float
    risk_reward: float
    volatility: Literal["HIGH", "NORMAL"]
    position_warning: str | None


class AnalysisResponse(BaseModel):
    symbol: str
    interval: str
    indicators: IndicatorSet
    rule_engine: RuleEngineResult
    news: NewsResult | None = None
    llm_decision: LLMDecision | None = None
    risk: RiskResult
    agent_trace: list[str]
    llm_called: bool
