# /review — PR Code Review

You are performing a first-pass code review of a pull request for the Agentic AI Trading Signal System.

## Context

This is a university assignment project. The codebase is a FastAPI backend (Python, `uv`-managed,
Diamond copier template) + Vite/React frontend + Jupyter EDA notebook. Key constraints from CLAUDE.md:

- All backend I/O must be async (`httpx.AsyncClient`)
- `uv` only — no `pip`
- Full type annotations required (pyright)
- `ruff` formatting enforced
- `info_retrieval.py` and `decision_engine.py` must never raise exceptions — fallback only
- Claude API called only for AMBIGUOUS signals
- `agent_trace` must be built progressively through the pipeline
- Frontend: no external UI libraries, `BASE` URL only in `api.js`

## Review Instructions

Given the PR diff below, write a structured first-pass review covering:

### 1. Correctness
- Does the logic match the spec in CLAUDE.md and PRD.md?
- Check rule engine logic exactly: STRONG_BUY thresholds (RSI < 35), MACD crossover detection
  (current > 0 AND previous ≤ 0), STRONG_SELL thresholds (RSI > 65)
- Check risk management formulas: stop = price - 1.5×ATR, target = price + 2.5×ATR
- Check fallback behaviour in info_retrieval and decision_engine
- Check CORS is configured for `http://localhost:5173`

### 2. Type Safety & Code Quality
- Missing type annotations on function signatures?
- Any use of `Any` without a comment explaining why?
- `os.environ` accessed outside `config.py`?
- Hardcoded strings that should be constants?

### 3. Error Handling
- Any module that could raise an unhandled exception in the agent pipeline?
- httpx calls — do they have timeouts set?
- JSON parsing from LLM response — is there a try/except with safe default?

### 4. Test Coverage
- Are all 4 signal cases (STRONG_BUY, STRONG_SELL, HOLD, AMBIGUOUS) tested?
- Is the MACD crossover edge case covered (histogram was negative, now positive)?
- Are the risk management CAUTION threshold tests present?

### 5. Assignment Alignment
- Is `agent_trace` populated at every pipeline step?
- Is `llm_called: bool` correctly set?
- Does the response schema match the `AnalysisResponse` Pydantic model?

### 6. Minor / Nits
- Anything that would fail `ruff check` or `pyright`?
- Import ordering, unused imports, docstrings missing on public functions?

## Output Format

For each issue found, write:
```
**[SEVERITY] File: line range**
Description of the issue.
Suggested fix (code snippet if helpful).
```

Severity levels: `BLOCKER` (incorrect logic or broken fallback), `MAJOR` (type error or
missing test), `MINOR` (style or nit).

End with a one-paragraph summary: overall assessment, whether it's ready to merge,
and the top 1-2 things to fix first.

## Posting to GitHub

After writing the review, automatically post it as a comment on the open PR for the
current branch. Use this exact sequence:

1. Run `gh pr list --head $(git branch --show-current)` to find the PR number.
2. If a PR is found, post the full review body via:
   `gh pr comment <PR_NUMBER> --body "<review text>"`
3. Print the comment URL returned by `gh` so the user can see it.
4. If no open PR exists for the current branch, skip posting and say so.

---

$ARGUMENTS
