"""FastAPI application — wires all agents into the trading signal pipeline."""

from typing import Any, Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from agentic_trader.agents import (
    decision_engine,
    info_retrieval,
    market_analysis,
    risk_management,
    rule_engine,
)
from agentic_trader.models.signal import AnalysisResponse, IndicatorSet, LLMDecision

app = FastAPI(title="Agentic Trader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze(
    symbol: str,
    interval: str = Query(default="1h"),
) -> AnalysisResponse:
    agent_trace: list[str] = []

    # Step 1: Market analysis
    indicators = await market_analysis.fetch_indicators(symbol, interval)
    agent_trace.append(
        "MarketAnalysisModule: fetched 200 candles, computed 6 indicators"
    )

    # Step 2: Rule engine
    rule_result = rule_engine.evaluate(indicators)
    if rule_result.signal == "AMBIGUOUS":
        n = len(rule_result.rule_reasoning)
        agent_trace.append(f"RuleEngine: signal=AMBIGUOUS ({n} conflicting indicators)")
    else:
        agent_trace.append(f"RuleEngine: signal={rule_result.signal}")

    # Steps 3 & 4: AMBIGUOUS path only
    news = None
    llm_decision: LLMDecision | None = None
    llm_called = False
    confidence: float | None = None

    if rule_result.signal == "AMBIGUOUS":
        llm_called = True

        news = await info_retrieval.fetch_news(symbol)
        if news.available:
            agent_trace.append(
                f"InformationRetrievalModule: fetched {len(news.items)} news items,"
                f" sentiment={news.sentiment_score:.2f}"
            )
        else:
            agent_trace.append(
                "InformationRetrievalModule: news unavailable (fallback)"
            )

        llm_decision = await decision_engine.decide(indicators, news)
        agent_trace.append(
            f"DecisionEngine: LLM called, returned {llm_decision.action}"
            f" ({llm_decision.confidence:.2f} confidence)"
        )
        confidence = llm_decision.confidence
    else:
        # Map deterministic rule signal to a synthetic LLMDecision
        action: Literal["BUY", "SELL", "HOLD"]
        match rule_result.signal:
            case "STRONG_BUY":
                action = "BUY"
            case "STRONG_SELL":
                action = "SELL"
            case _:
                action = "HOLD"
        llm_decision = LLMDecision(
            action=action,
            confidence=1.0,
            reasoning="; ".join(rule_result.rule_reasoning),
            risk_flags=[],
        )

    # Step 5: Risk management
    risk = risk_management.compute(indicators.current_price, indicators.atr, confidence)
    agent_trace.append(
        f"RiskManagement: stop={risk.stop_loss:.0f},"
        f" target={risk.take_profit:.0f}, R/R={risk.risk_reward:.2f}"
    )

    return AnalysisResponse(
        symbol=symbol,
        interval=interval,
        indicators=indicators,
        rule_engine=rule_result,
        news=news,
        llm_decision=llm_decision,
        risk=risk,
        agent_trace=agent_trace,
        llm_called=llm_called,
    )


@app.get("/api/candles/{symbol}")
async def candles(
    symbol: str,
    interval: str = Query(default="1h"),
) -> list[dict[str, Any]]:  # Any: lightweight-charts mixed-value dicts
    return await market_analysis.fetch_candles(symbol, interval)


@app.get("/api/indicators/{symbol}", response_model=IndicatorSet)
async def indicators_endpoint(
    symbol: str,
    interval: str = Query(default="1h"),
) -> IndicatorSet:
    return await market_analysis.fetch_indicators(symbol, interval)
