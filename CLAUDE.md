# CLAUDE.md — Agentic AI Trading Signal System

This file is the authoritative guide for Claude Code when building this project.
Read it fully before writing any code. Follow all constraints exactly.

---

## Project Overview

An agentic AI trading signal system built as a university assignment demonstrating
a multi-module pipeline that:

1. Fetches live crypto OHLCV data from Binance
2. Computes technical indicators (RSI, MACD, Bollinger Bands, EMA, ATR)
3. Applies a deterministic rule engine to pre-filter signals
4. Fetches news sentiment from CryptoPanic (only for ambiguous signals)
5. Calls Claude API to resolve ambiguous signals (only when rules conflict)
6. Applies ATR-based risk management post-processing
7. Exposes results via FastAPI, consumed by a Vite/React frontend

This is a **demonstration system** — no real trades are executed.

---

## Repository Layout

The repo root is the Diamond copier template root. The copier template manages
the Python package only. `frontend/` and `notebooks/` are entirely outside its scope.

```
agentic-trader/                  ← repo root = copier template root
├── src/
│   └── agentic_trader/          ← Python package (all backend code lives here)
├── tests/
├── frontend/                    ← Vite + React (separate npm project)
├── notebooks/                   ← Jupyter EDA notebook
├── docs/
├── .claude/
│   └── commands/
│       └── review.md
├── pyproject.toml
├── uv.lock
├── CLAUDE.md                    ← this file
└── README.md
```

Never put frontend or notebook code inside `src/agentic_trader/`.
Never put Python package code inside `frontend/`.

---

## Backend

### Package Structure

```
src/agentic_trader/
├── agents/
│   ├── market_analysis.py
│   ├── rule_engine.py
│   ├── info_retrieval.py
│   ├── decision_engine.py
│   └── risk_management.py
├── models/
│   └── signal.py
├── config.py
└── main.py
```

### Toolchain Constraints

- **Package manager:** `uv` only. Never use `pip install` directly.
  - Add deps: `uv add <package>`
  - Run server: `uv run uvicorn agentic_trader.main:app --reload`
  - Run tests: `uv run pytest`
- **Linting:** `ruff` — code must pass `ruff check .` with no errors.
- **Types:** `pyright` — all functions must have full type annotations. No `Any` unless
  unavoidable; comment why if used.
- **Python version:** 3.11+ (check `.python-version` in repo root).
- **Formatting:** `ruff format` (not black).

### Dependencies to Add

```bash
uv add fastapi uvicorn httpx pandas pandas-ta anthropic pydantic pydantic-settings python-dotenv
uv add --dev pytest pytest-asyncio respx
```

### Environment Variables

Access only through `config.py`. Never read `os.environ` directly elsewhere.
Never hardcode API keys.

```python
# src/agentic_trader/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    cryptopanic_api_key: str

    model_config = {"env_file": ".env"}

settings = Settings()
```

Required `.env` at repo root:
```
ANTHROPIC_API_KEY=sk-ant-...
CRYPTOPANIC_API_KEY=...
```

Binance requires no API key for public market data endpoints.

---

## Agent Module Specifications

### `agents/market_analysis.py`

- Fetch from `https://api.binance.com/api/v3/klines`
- Use `httpx.AsyncClient` — all I/O must be async
- Params: `symbol`, `interval` (`1h`/`4h`/`1d`), `limit=200`
- Build a `pandas.DataFrame` with columns: `open`, `high`, `low`, `close`, `volume`
- Compute indicators using `pandas_ta`:
  - RSI(14), MACD(12,26,9), Bollinger Bands(20,2), EMA(20), EMA(50), ATR(14)
  - Volume SMA(20) using pandas `.rolling(20).mean()`
- Validate: `high >= low` for all rows; forward-fill NaN gaps with `.ffill()`
- Return typed `IndicatorSet` Pydantic model
- **UK geo-restriction:** Binance blocks UK IPs. This is a known dev issue handled
  via VPN. Do not add any workaround code.

### `agents/rule_engine.py`

- Pure Python, zero external dependencies
- Input: `IndicatorSet`
- Logic:
  ```
  STRONG_BUY  if: RSI < 35 AND MACD histogram crosses positive AND price > EMA20
  STRONG_SELL if: RSI > 65 AND MACD histogram crosses negative AND price < EMA20
  HOLD        if: RSI 40–60 AND no crossover AND ATR/price < 2%
  AMBIGUOUS   if: none of the above
  ```
- "Crosses positive" = current histogram > 0 and previous histogram ≤ 0
- Return `RuleEngineResult` with:
  - `signal: Literal["STRONG_BUY", "STRONG_SELL", "HOLD", "AMBIGUOUS"]`
  - `rule_reasoning: list[str]`
- Must have full unit test coverage in `tests/test_rule_engine.py`

### `agents/risk_management.py`

- Pure Python, zero external dependencies
- Input: `current_price: float`, `atr: float`, `confidence: float | None`
- Formulas:
  - `stop_loss = current_price - (1.5 * atr)`
  - `take_profit = current_price + (2.5 * atr)`
  - `risk_reward = (take_profit - current_price) / (current_price - stop_loss)`
  - `volatility = "HIGH" if atr / current_price > 0.03 else "NORMAL"`
  - `position_warning = "CAUTION" if volatility == "HIGH" and confidence is not None and confidence < 0.6 else None`
- Return `RiskResult` Pydantic model
- Must have full unit test coverage in `tests/test_risk_management.py`

### `agents/info_retrieval.py`

- Fetch from `https://cryptopanic.com/api/v1/posts/`
- Params: `auth_token`, `currencies` (e.g. BTCUSDT → BTC), `kind=news`
- Fetch top 5 items; extract `title`, `published_at`, `votes`, `source.domain`
- `sentiment_score = (bullish_votes - bearish_votes) / max(total_votes, 1)`
- **Fallback:** On any failure (network error, non-200, parse error), return
  `NewsResult(available=False)`. Do not raise. The pipeline must continue.
- Use `httpx.AsyncClient` with a 5-second timeout

### `agents/decision_engine.py`

- Called **only** when rule engine returns `AMBIGUOUS`
- Use `anthropic.AsyncAnthropic` client
- Model: `claude-sonnet-4-20250514`
- System prompt (use exactly):
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
- On JSON parse failure: return safe default:
  `LLMDecision(action="HOLD", confidence=0.5, reasoning="Parse error", risk_flags=["llm_parse_error"])`
- Do not raise exceptions from this module

### `models/signal.py`

Define all Pydantic models here. Use `Literal` for constrained string fields.

- `IndicatorSet` — all computed indicator values (floats + bb_position string)
- `RuleEngineResult` — signal Literal + rule_reasoning list
- `NewsItem` — title, source, published_at, sentiment
- `NewsResult` — available bool + items list + sentiment_score
- `LLMDecision` — action Literal + confidence + reasoning + risk_flags
- `RiskResult` — stop_loss, take_profit, risk_reward, volatility Literal, position_warning
- `AnalysisResponse` — full `/api/analyze/{symbol}` response, including:
  - `agent_trace: list[str]`
  - `llm_called: bool`

### `main.py`

FastAPI application. Wire agents in sequence for `GET /api/analyze/{symbol}`:

1. `market_analysis.fetch_indicators(symbol, interval)` → append to `agent_trace`
2. `rule_engine.evaluate(indicators)` → append to `agent_trace`
3. If AMBIGUOUS: `info_retrieval.fetch_news(symbol)` → append to `agent_trace`
4. If AMBIGUOUS: `decision_engine.decide(indicators, news)` → append to `agent_trace`
5. `risk_management.compute(price, atr, confidence)` → append to `agent_trace`
6. Return `AnalysisResponse`

Also implement:
- `GET /api/candles/{symbol}` — raw OHLCV for charting
- `GET /api/indicators/{symbol}` — indicators only
- `GET /api/health` — `{"status": "ok"}`

Add CORS middleware allowing `http://localhost:5173` (Vite dev server default).

`agent_trace` entries must follow this format:
```
"MarketAnalysisModule: fetched 200 candles, computed 6 indicators"
"RuleEngine: signal=AMBIGUOUS (3 conflicting indicators)"
"InformationRetrievalModule: fetched 5 news items, sentiment=0.31"
"DecisionEngine: LLM called, returned HOLD (0.62 confidence)"
"RiskManagement: stop=81440, target=88800, R/R=2.5"
```

---

## Frontend

### Stack

- Vite + React (JSX, not TypeScript)
- `lightweight-charts` for the candlestick chart
- Plain CSS modules or inline styles — no Tailwind, no component libraries
- Fetches from FastAPI backend at `http://localhost:8000`

### Scaffold

```bash
cd frontend
npm create vite@latest . -- --template react
npm install lightweight-charts
```

### Component Structure

```
frontend/src/
├── App.jsx           ← layout, state, fetch orchestration
├── api.js            ← all fetch calls (BASE URL defined here only)
└── components/
    ├── PriceChart.jsx       ← lightweight-charts candlestick + EMA overlays
    ├── IndicatorsPanel.jsx  ← RSI gauge, MACD bar, BB position, ATR
    ├── DecisionCard.jsx     ← BUY/SELL/HOLD badge, confidence, risk/reward
    ├── NewsFeed.jsx         ← top 5 headlines with sentiment badges
    └── AgentLog.jsx         ← terminal-styled agent_trace display
```

### Design Constraints

- Background `#0d0d0d`, surface `#1a1a1a`, border `#2a2a2a`
- BUY `#00ff88`, SELL `#ff4444`, HOLD `#ffaa00`
- `JetBrains Mono` or `monospace` for agent log and indicator values
- **AgentLog:** dark background, green monospace text, each line prefixed with `>`
- **DecisionCard:** BUY/SELL/HOLD badge must be large and visually dominant
- No external UI libraries

### `api.js`

```javascript
const BASE = 'http://localhost:8000'

export const analyze = (symbol, interval) =>
  fetch(`${BASE}/api/analyze/${symbol}?interval=${interval}`).then(r => r.json())

export const candles = (symbol, interval) =>
  fetch(`${BASE}/api/candles/${symbol}?interval=${interval}`).then(r => r.json())
```

---

## EDA Notebook (`notebooks/EDA.ipynb`)

Standalone — no FastAPI dependency. Install deps separately in the notebook env.

Required sections in order:

1. **Data Collection** — fetch BTC, ETH, BNB daily candles; show DataFrame head
2. **Cleaning** — missing value check, OHLCV integrity validation, forward-fill
3. **Descriptive Statistics** — mean return, std, skew, kurtosis per asset
4. **Time-Series Visualisation** — price chart with volume subplot
5. **Volatility Analysis** — rolling 30-day std, ATR over time
6. **Correlation Matrix** — BTC/ETH/BNB daily returns heatmap
7. **K-Means Clustering** — cluster candles on (RSI, MACD histogram, volume_vs_avg),
   k=3, scatter plot with cluster colours
8. **Feature Engineering** — step-by-step RSI, MACD, Bollinger Band computation
9. **Backtesting** — apply rule engine signals to historical BTC 1h data:
   - Signal hit rate %: for each STRONG_BUY/STRONG_SELL, was price higher/lower
     after 4 candles?
   - Simulated P&L curve: equity curve with fixed 1-unit position per signal,
     plotted as a line chart

---

## Implementation Order

Follow this sequence. Each step should be committed before starting the next.

1. Scaffold repo root with copier template; create `frontend/`, `notebooks/`, `docs/` dirs
2. `src/agentic_trader/models/signal.py` — define all Pydantic models first
3. `src/agentic_trader/config.py`
4. `src/agentic_trader/agents/market_analysis.py`
5. `src/agentic_trader/agents/rule_engine.py` + `tests/test_rule_engine.py`
6. `src/agentic_trader/agents/risk_management.py` + `tests/test_risk_management.py`
7. `src/agentic_trader/agents/info_retrieval.py`
8. `src/agentic_trader/agents/decision_engine.py`
9. `src/agentic_trader/main.py`
10. Frontend scaffold + `PriceChart.jsx` (most complex component first)
11. Remaining frontend components + `App.jsx`
12. `notebooks/EDA.ipynb`

---

## Testing

- `uv run pytest` from repo root
- `tests/test_rule_engine.py`: cover STRONG_BUY, STRONG_SELL, HOLD, AMBIGUOUS,
  and the MACD crossover edge case (histogram was negative, now positive)
- `tests/test_risk_management.py`: cover NORMAL volatility, HIGH volatility,
  CAUTION warning trigger (HIGH + confidence < 0.6)
- Use `respx` to mock `httpx` calls for any tests hitting external APIs
- Do not write tests for `info_retrieval.py` or `decision_engine.py`

---

## Git Hygiene

- Commit after each implementation step
- Commit message format: `feat: <module> — <one line description>`
  e.g. `feat: rule_engine — deterministic signal pre-filter with 4 signal types`
- Never commit `.env`
- Always commit `uv.lock`

---

## Common Mistakes to Avoid

- Do not use `pip` — use `uv add`
- Do not call Claude API for STRONG_BUY, STRONG_SELL, or HOLD — only AMBIGUOUS
- Do not let `info_retrieval.py` or `decision_engine.py` raise exceptions
- Do not put frontend or notebook files inside `src/agentic_trader/`
- Do not skip type annotations — pyright will fail the pre-commit hook
- Do not hardcode `http://localhost:8000` in components — only in `api.js`
- Build `agent_trace` progressively through the pipeline, not at the end
