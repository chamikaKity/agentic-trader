# PRD: Agentic AI Trading Signal System

**Version:** 1.2
**Domain:** Finance — Automated Crypto Trading
**Purpose:** Academic demonstration of an agentic AI workflow for a university assignment

-----

## 1. Problem Statement

Most retail traders make decisions in information overload — price charts, technical indicators, and news headlines all at once. This system demonstrates an **agentic AI workflow** that autonomously orchestrates multiple data sources, applies rule-based pre-filtering, and invokes an LLM reasoning engine only when the signal is genuinely ambiguous — producing an explainable BUY / SELL / HOLD decision with full reasoning transparency.

-----

## 2. Goals

| Goal   | Description                                                                 |
|--------|-----------------------------------------------------------------------------|
| **G1** | Demonstrate a multi-module agentic architecture (not a single model call)   |
| **G2** | Collect and process live crypto data from Binance API                       |
| **G3** | Generate explainable trading signals with visible reasoning                 |
| **G4** | Satisfy all 4 assignment rubric sections (Data, EDA, Problem Solving, Docs) |
| **G5** | Be runnable locally with minimal setup (no paid cloud required for demo)    |

### Non-Goals

- Actually executing real trades
- Being profitable (the strategy is illustrative, not optimised)
- Production-grade security or scalability

-----

## 3. System Architecture

```
User Input (symbol + timeframe)
        │
        ▼
┌─────────────────────────┐
│  1. Market Analysis     │  ← Binance API (OHLCV candles)
│     Module              │    Computes: RSI, MACD, Bollinger Bands,
│                         │    EMA20/50, ATR, Volume trend
└────────────┬────────────┘
             │  structured indicators dict
             ▼
┌─────────────────────────┐
│  2. Rule Engine         │  ← Deterministic pre-filter
│     (Pre-filter)        │    STRONG_BUY / STRONG_SELL → skip LLM
│                         │    AMBIGUOUS → pass to LLM
└────────────┬────────────┘
             │  signal_strength + reasoning_context
             ▼
┌─────────────────────────┐
│  3. Information         │  ← CryptoPanic API (free tier)
│     Retrieval Module    │    Fetches top 5 news items for asset
│                         │    Extracts: headline, sentiment votes,
│                         │    published_at, source
└────────────┬────────────┘
             │  news_summary
             ▼
┌─────────────────────────┐
│  4. Decision Engine     │  ← Claude API (claude-sonnet-4-20250514)
│     (LLM Brain)         │    Called ONLY if signal is AMBIGUOUS
│                         │    Input: indicators + news + price context
│                         │    Output: BUY/SELL/HOLD + confidence +
│                         │    reasoning paragraph + risk flags
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  5. Risk Management     │  ← Rule-based post-processor
│     Module              │    Computes: suggested stop-loss (ATR-based),
│                         │    take-profit, position size warning,
│                         │    volatility flag
└────────────┬────────────┘
             │  final signal object
             ▼
        FastAPI endpoint → Vite/React Frontend Dashboard
```

### Why Hybrid (not pure LLM)?

- **Cost control**: LLM is only called when indicators conflict.
- **Explainability**: Rule engine produces human-readable pre-reasoning; LLM adds nuance only where math alone is insufficient.
- **Assignment alignment**: Demonstrates understanding of *when* to delegate to an LLM vs. deterministic logic.
- **Latency**: Rule-filtered cases (~40-50% of signals) resolve in <200ms without an LLM call.

-----

## 4. Module Specifications

### 4.1 Market Analysis Module

**Data Source:** Binance REST API (`/api/v3/klines`)
**Library:** direct `httpx` calls (async)
**Authentication:** No API key required for public market data endpoints.
**Local dev note:** Binance API is geo-restricted in the UK. Run with a VPN for local development. The marker's environment is unaffected.

**Inputs:** `symbol` (e.g. BTCUSDT), `interval` (1h, 4h, 1d), `limit` (200 candles)

**Outputs (computed indicators):**

| Indicator              | Library     | Purpose                                     |
|------------------------|-------------|---------------------------------------------|
| RSI (14)               | `pandas-ta` | Momentum: oversold <30, overbought >70      |
| MACD (12,26,9)         | `pandas-ta` | Trend: signal line crossover                |
| Bollinger Bands (20,2) | `pandas-ta` | Volatility: price vs. bands                 |
| EMA 20 / EMA 50        | `pandas-ta` | Trend direction (golden/death cross)        |
| ATR (14)               | `pandas-ta` | Volatility magnitude (for stop-loss sizing) |
| Volume SMA (20)        | `pandas`    | Volume trend confirmation                   |

**Data cleaning:** Forward-fill any gaps, validate OHLCV integrity (high ≥ low, etc.).

-----

### 4.2 Rule Engine (Pre-filter)

```
STRONG_BUY  if:  RSI < 35  AND  MACD histogram crosses positive  AND  price > EMA20
STRONG_SELL if:  RSI > 65  AND  MACD histogram crosses negative  AND  price < EMA20
HOLD        if:  RSI 40–60  AND  no crossover  AND  ATR/price < 2%
AMBIGUOUS   if:  none of the above (indicators conflict)
```

"MACD histogram crosses positive" = current histogram > 0 and previous histogram ≤ 0.

**Output:** `{ signal: "STRONG_BUY" | "STRONG_SELL" | "AMBIGUOUS" | "HOLD", rule_reasoning: [...] }`

-----

### 4.3 Information Retrieval Module

**Data Source:** CryptoPanic API — free developer tier
**Endpoint:** `GET https://cryptopanic.com/api/v1/posts/?auth_token=TOKEN&currencies=BTC&kind=news`

- Fetch top 5 most recent news items; fields: `title`, `published_at`, `votes`, `source.domain`
- `sentiment_score = (bullish_votes - bearish_votes) / max(total_votes, 1)`
- **Fallback:** On any failure, return `NewsResult(available=False)` — do not raise.

-----

### 4.4 Decision Engine (LLM Brain)

**Model:** `claude-sonnet-4-20250514` via Anthropic API
**Called only when:** Rule Engine returns `AMBIGUOUS`

**System prompt:**

```
You are a quantitative crypto trading analyst. You will be given:
1. Technical indicators for a crypto asset
2. Recent news sentiment summary
3. Current price context

Your task is to reason step-by-step and output a JSON object with:
- decision: "BUY" | "SELL" | "HOLD"
- confidence: 0.0–1.0
- reasoning: a 2-3 sentence explanation
- risk_flags: list of concern strings (e.g. "high volatility", "bearish news divergence")

Be conservative. When in doubt, output HOLD.
Respond ONLY with valid JSON.
```

On JSON parse failure: return safe HOLD default with `confidence=0.5`, `risk_flags=["llm_parse_error"]`.

-----

### 4.5 Risk Management Module

| Output                | Formula                                             |
|-----------------------|-----------------------------------------------------|
| Stop-loss price       | `current_price - (1.5 × ATR)`                       |
| Take-profit price     | `current_price + (2.5 × ATR)`                       |
| Risk/Reward ratio     | `(take_profit - price) / (price - stop_loss)`       |
| Volatility flag       | `"HIGH"` if ATR/price > 3%, else `"NORMAL"`         |
| Position size warning | `"CAUTION"` if volatility HIGH and confidence < 0.6 |

-----

## 5. API Design (FastAPI Backend)

| Method | Path                       | Description                          |
|--------|----------------------------|--------------------------------------|
| `GET`  | `/api/analyze/{symbol}`    | Run full agent pipeline for a symbol |
| `GET`  | `/api/candles/{symbol}`    | Return raw OHLCV data for charting   |
| `GET`  | `/api/indicators/{symbol}` | Return computed indicators only      |
| `GET`  | `/api/health`              | Health check                         |

### `GET /api/analyze/{symbol}` Response Schema

```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2026-03-23T14:00:00Z",
  "current_price": 84200.50,
  "interval": "1h",
  "indicators": {
    "rsi": 48.3,
    "macd_histogram": -12.4,
    "bb_upper": 86400,
    "bb_lower": 81200,
    "ema20": 83900,
    "ema50": 82100,
    "atr": 1840,
    "volume_vs_avg": 1.2
  },
  "rule_signal": "AMBIGUOUS",
  "rule_reasoning": ["RSI neutral (48)", "MACD bearish histogram", "Price above EMA20 (bullish)"],
  "news": {
    "available": true,
    "sentiment_score": 0.31,
    "items": [
      { "title": "...", "source": "coindesk.com", "published_at": "...", "sentiment": "bullish" }
    ]
  },
  "llm_called": true,
  "decision": {
    "action": "HOLD",
    "confidence": 0.62,
    "reasoning": "Mixed signals with slight bearish MACD pressure despite positive news sentiment.",
    "risk_flags": ["neutral RSI zone", "low volume confirmation"]
  },
  "risk": {
    "stop_loss": 81440,
    "take_profit": 88800,
    "risk_reward": 2.5,
    "volatility": "NORMAL",
    "position_warning": null
  },
  "agent_trace": [
    "MarketAnalysisModule: fetched 200 candles, computed 6 indicators",
    "RuleEngine: signal=AMBIGUOUS (3 conflicting indicators)",
    "InformationRetrievalModule: fetched 5 news items, sentiment=0.31",
    "DecisionEngine: LLM called, returned HOLD (0.62 confidence)",
    "RiskManagement: stop=81440, target=88800, R/R=2.5"
  ]
}
```

-----

## 6. Frontend Design

**Stack:** Vite + React (`frontend/` at repo root, separate npm project)
**Charting:** `lightweight-charts` for candlestick + EMA overlays
**Aesthetic:** Dark terminal/trading-room — monospace accents, green/red signal colours

| Panel                   | Content                                                                                       |
|-------------------------|-----------------------------------------------------------------------------------------------|
| **Header**              | Symbol search input, interval selector (1h/4h/1d), "Analyse" button, last-updated timestamp  |
| **Price Chart**         | Candlestick chart, EMA20/50 overlays, BUY/SELL signal markers                                |
| **Indicators Panel**    | RSI gauge, MACD histogram bar, Bollinger Band position, ATR value                            |
| **Decision Card**       | Large BUY/SELL/HOLD badge, confidence meter, risk/reward ratio, stop-loss/take-profit prices |
| **News Feed**           | Top 5 headlines with sentiment badges, source and timestamp                                  |
| **Agent Reasoning Log** | Step-by-step agent_trace styled like a terminal                                              |

-----

## 7. Project File Structure

The repo root is the copier template root. `frontend/` and `notebooks/` are outside its scope.

```
agentic-trader/                  ← repo root = copier template root
├── src/
│   └── agentic_trader/
│       ├── agents/
│       │   ├── market_analysis.py
│       │   ├── rule_engine.py
│       │   ├── info_retrieval.py
│       │   ├── decision_engine.py
│       │   └── risk_management.py
│       ├── models/
│       │   └── signal.py
│       ├── config.py
│       └── main.py
├── tests/
│   ├── test_rule_engine.py
│   └── test_risk_management.py
├── frontend/                    ← Vite + React (outside copier scope)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │       ├── PriceChart.jsx
│   │       ├── IndicatorsPanel.jsx
│   │       ├── DecisionCard.jsx
│   │       ├── NewsFeed.jsx
│   │       └── AgentLog.jsx
│   ├── index.html
│   └── package.json
├── notebooks/
│   └── EDA.ipynb
├── docs/
│   ├── architecture_diagram.png
│   └── cloud_setup.md
├── .claude/
│   └── commands/
│       └── review.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── CLAUDE.md
└── README.md
```

-----

## 8. Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...
CRYPTOPANIC_API_KEY=...
# Binance: no key needed for public endpoints
```

-----

## 9. EDA Notebook Plan (Assignment Section 2)

1. Data collection walkthrough (Binance candles → DataFrame)
2. Missing value analysis and cleaning
3. Descriptive statistics (mean return, std, skew, kurtosis)
4. Time-series price visualisation
5. Volatility analysis (rolling std, ATR over time)
6. Correlation matrix (BTC vs ETH vs BNB)
7. K-Means clustering of candles by (RSI, MACD histogram, volume_vs_avg), k=3
8. Feature engineering demo (RSI/MACD/BB computation shown step-by-step)
9. Backtesting — apply rule engine to historical BTC data, reporting:
   - **Signal hit rate %** (directional accuracy over next 4 candles)
   - **Simulated P&L curve** (equity curve assuming fixed 1-unit position per signal)

-----

## 10. Cloud Architecture (Assignment Section 1)

| Component             | Local (Demo)           | Cloud Equivalent                           |
|-----------------------|------------------------|--------------------------------------------|
| Raw candle storage    | Local CSV / in-memory  | AWS S3 / Azure Blob                        |
| Backend compute       | `uvicorn` on localhost | AWS EC2 / Azure VM                         |
| Signal history DB     | SQLite                 | AWS RDS (Postgres) / Azure SQL             |
| Scheduled re-analysis | Manual trigger         | AWS Lambda + EventBridge / Azure Functions |
| Frontend hosting      | `npm run dev`          | AWS Amplify / Azure Static Web Apps        |

-----

## 11. Tech Stack Summary

| Layer       | Technology                                    | Reason                                          |
|-------------|-----------------------------------------------|-------------------------------------------------|
| Data        | Binance REST API                              | Free, no auth for public data, real-time        |
| Indicators  | `pandas-ta`                                   | One-liner technical indicators on DataFrames    |
| News        | CryptoPanic API                               | Free, crypto-specific, sentiment votes included |
| LLM         | Anthropic Claude (`claude-sonnet-4-20250514`) | Reasoning quality, structured JSON output       |
| Backend     | FastAPI + Pydantic                            | Fast, typed, auto-generates OpenAPI docs        |
| HTTP client | `httpx` (async)                               | Async-native, fits FastAPI's async model        |
| Packaging   | `uv` + Diamond copier template (repo root)    | Reproducible installs, enforced code quality    |
| Linting     | `ruff` + `pyright`                            | Consistent style and type safety                |
| Frontend    | Vite + React + `lightweight-charts`           | Candlestick charting, component-based, fast HMR |
| EDA         | Jupyter + pandas + matplotlib                 | Standard, assignment-friendly                   |

-----

## 12. Implementation Order

1. Scaffold repo root with Diamond copier template; add `frontend/`, `notebooks/`, `docs/` dirs
2. `src/agentic_trader/models/signal.py` — all Pydantic models
3. `src/agentic_trader/config.py` — env var loading
4. `src/agentic_trader/agents/market_analysis.py`
5. `src/agentic_trader/agents/rule_engine.py` + `tests/test_rule_engine.py`
6. `src/agentic_trader/agents/risk_management.py` + `tests/test_risk_management.py`
7. `src/agentic_trader/agents/info_retrieval.py`
8. `src/agentic_trader/agents/decision_engine.py`
9. `src/agentic_trader/main.py` — FastAPI pipeline wiring
10. Frontend scaffold + `PriceChart.jsx`
11. Remaining frontend components + `App.jsx` integration
12. `notebooks/EDA.ipynb`

-----

## 13. Key Design Decisions & Justifications

| Decision                        | Rationale                                                                                            |
|---------------------------------|------------------------------------------------------------------------------------------------------|
| Hybrid rule+LLM engine          | LLMs add cost and latency; only use when deterministic rules conflict. Shows architectural maturity. |
| `agent_trace` in every response | Makes the agentic workflow *visible* — critical for the assignment and for debugging                 |
| CryptoPanic over NewsAPI        | Crypto-specific, free, structured sentiment votes — no NLP needed                                   |
| Binance public API (no key)     | Zero friction setup; UK geo-restriction handled via VPN in local dev                                |
| `pandas-ta` for indicators      | Single dependency, DataFrame-native, covers all required indicators                                  |
| Pydantic response models        | Self-documenting, enables auto-generated OpenAPI spec for the writeup                                |
| ATR-based risk management       | Industry-standard volatility-adjusted sizing; more defensible than fixed %                           |
| Diamond copier template at root | Copier template is the Python project root — no nested backend/ wrapper needed                       |
| Vite app at repo root           | `lightweight-charts` requires npm; Vite lives alongside copier template, not inside it              |

-----

## 14. Limitations (for writeup honesty)

- Strategy is illustrative, not backtested for profitability
- CryptoPanic sentiment is vote-based (community), not NLP-derived
- No order execution (simulation only)
- LLM decisions are non-deterministic (same inputs may yield different outputs)
- Binance public API has rate limits (~1200 req/min weight)
- Binance API is geo-restricted in the UK; a VPN is required for local development
- News fetch adds ~500ms latency for ambiguous signals
