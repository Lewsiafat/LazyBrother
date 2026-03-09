# CLAUDE.md — Developer Reference

## Project Overview

**LazyBrother** (`v0.3.0`) is a Python/FastAPI backend service that analyzes candlestick charts for cryptocurrency and stocks. It combines classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice.

## Tech Stack

| Layer | Technology |
|---|---|
| **Python** | 3.12+ |
| **Web Framework** | FastAPI + Uvicorn |
| **Data** | pandas + pandas-ta |
| **Crypto Data** | python-binance |
| **Stock Data** | yfinance |
| **LLM** | openai / google-generativeai / anthropic |
| **Config** | pydantic-settings (BaseSettings → singleton `settings`) |
| **HTTP Client** | httpx |
| **Package Mgr** | uv |
| **Frontend** | Vue 3 + Vite (debug client) |

## Architecture

Pipeline architecture — single FastAPI app with modular internal stages:

```
Request → DataFetcher → PatternAnalyzer → IndicatorCalc → SMCAnalyzer → LLMSynthesizer → Response
```

All steps are orchestrated by `orchestrator.analyze()`. Primary timeframe = the **highest** timeframe in mode (e.g. `15m` for scalping, `4h` for swing) for indicator display.

### Key Directories

```
app/
├── main.py              # FastAPI entry point, CORS, router registration (version 0.3.0)
├── config.py            # pydantic-settings from .env (Settings singleton)
├── models/
│   ├── request.py       # MarketType, AnalysisMode, TIMEFRAME_PRESETS, AnalysisRequest (with custom prompts)
│   ├── response.py      # AnalysisResponse, TradingAnalysis, IndicatorData, SMCData, etc.
│   └── prompt.py        # PromptSnippet CRUD models
├── storage/             # prompt_store.py (JSON persistence)
├── pipeline/
│   ├── data_fetcher.py  # BaseFetcher ABC + BinanceFetcher + YFinanceFetcher + get_fetcher()
│   ├── pattern_analyzer.py  # Single/dual/triple candle patterns → analyze_patterns()
│   ├── indicator_calc.py    # RSI, MACD, Bollinger, SMA, EMA → calculate_all_timeframes()
│   ├── smc_analyzer.py      # OB, FVG, BOS/CHoCH, Sweeps → analyze_smc_all_timeframes()
│   ├── llm_synthesizer.py   # _build_prompt() + synthesize_analysis() + get_llm_provider()
│   └── orchestrator.py      # analyze() 5-step pipeline + _merge_smc()
├── providers/
│   ├── base.py          # LLMProvider ABC with async synthesize(prompt) → str
│   ├── openai_provider.py   # default: gpt-4o
│   ├── gemini_provider.py   # default: gemini-2.0-flash
│   └── claude_provider.py   # default: claude-sonnet-4-20250514
└── routers/
    ├── analysis.py      # POST /api/v1/analyze  +  GET /api/v1/health
    └── prompts.py       # CRUD operations and markdown import
frontend/                # Vue 3 + Vite debug client
├── src/App.vue
├── src/api.js           # fetch-based API client
├── src/style.css        # dark theme with glassmorphism
└── src/components/      # AnalysisForm, ResultPanel, RawJson, ErrorDisplay, PromptManager
```

### Pipeline Modules (`app/pipeline/`)

| Module | Key Function | Notes |
|---|---|---|
| `data_fetcher.py` | `fetch_all_timeframes()` | 200 candles per TF; yfinance 4h resampled from 1h |
| `pattern_analyzer.py` | `analyze_patterns()` | 12+ patterns: doji, hammer, inverted_hammer, shooting_star, spinning_top, bullish/bearish_engulfing, piercing_line, dark_cloud_cover, morning/evening_star, three_white_soldiers, three_black_crows |
| `indicator_calc.py` | `calculate_all_timeframes()` | RSI(14), MACD(12,26,9), Bollinger(20,2), SMA(20), EMA(50) |
| `smc_analyzer.py` | `analyze_smc_all_timeframes()` | OB, FVG, BOS/CHoCH, Liquidity Sweeps via swing point analysis |
| `llm_synthesizer.py` | `synthesize_analysis()` | Builds structured prompt → calls LLM → parses JSON → `TradingAnalysis` |
| `orchestrator.py` | `analyze()` | Full 5-step pipeline. `_merge_smc()` aggregates SMC across TFs |

### LLM Providers (`app/providers/`)

All implement `LLMProvider.synthesize(prompt) -> str`. Selected via `LLM_PROVIDER` env var.

| Provider | Env Value | Default Model |
|---|---|---|
| OpenAI | `openai` | `gpt-4o` |
| Gemini | `gemini` | `gemini-2.0-flash` |
| Claude | `claude` | `claude-sonnet-4-20250514` |

Override model via `LLM_MODEL` env var.

### Response Models (`app/models/response.py`)

```
AnalysisResponse
├── symbol, market, mode, timestamp
├── analysis: TradingAnalysis | None   ← None on LLM failure
│   ├── trading_thesis, confidence_level, confidence_reason, direction
│   ├── entry_zone: EntryZone (low, high)
│   ├── stop_loss: StopLoss (price, reason)
│   └── take_profit_targets: list[TakeProfitTarget] (label, price, reason)
└── details: AnalysisDetails
    ├── patterns_detected: list[str]
    ├── indicators: IndicatorData (rsi_14, macd, bollinger, sma_20, ema_50)
    ├── smc: SMCData (order_blocks, fair_value_gaps, structure, liquidity_sweeps)
    └── timeframes_analyzed: list[str]
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Main analysis (`symbol`, `market`, `mode`, `custom_prompt`, `prompt_ids`) |
| `GET` | `/api/v1/health` | Health check |
| `*` | `/api/v1/prompts` | Prompt snippet CRUD & markdown file import |
| `GET` | `/` | Service info |
| `GET` | `/docs` | Auto-generated Swagger docs |

## Analysis Modes

| Mode | Timeframes | Primary TF (for display) |
|---|---|---|
| `scalping` | 1m, 5m, 15m | 15m |
| `swing` | 15m, 1h, 4h | 4h |

## Running

```bash
uv sync                              # install backend deps
cp .env.example .env                  # configure
uv run uvicorn app.main:app --reload  # start backend (http://localhost:8000)

# Debug frontend (optional)
cd frontend && npm install && npm run dev  # http://localhost:5173
```

## Configuration (`.env`)

| Key | Values | Default |
|---|---|---|
| `LLM_PROVIDER` | `openai` / `gemini` / `claude` | `openai` |
| `LLM_MODEL` | e.g. `gpt-4o`, `gemini-2.5-pro` | `""` (use provider default) |
| `OPENAI_API_KEY` | OpenAI key | `""` |
| `GEMINI_API_KEY` | Gemini key | `""` |
| `ANTHROPIC_API_KEY` | Anthropic key | `""` |
| `BINANCE_API_KEY` | Binance key | `""` |
| `BINANCE_API_SECRET` | Binance secret | `""` |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage key (reserved) | `""` |
| `HOST` | server host | `0.0.0.0` |
| `PORT` | server port | `8000` |

## Conventions

- All pipeline stages are **async** functions
- Response models use **Pydantic v2** with `model_dump()`
- LLM responses are expected as **JSON only** (no markdown); parsed via `json.loads()`
- If LLM fails (`json.JSONDecodeError`, `KeyError`, or any exception), `synthesize_analysis()` returns `None` → API returns raw analysis data without the `analysis` field (graceful fallback)
- Error codes: `400` (bad input / unsupported symbol), `502` (LLM fail), `503` (data source timeout)
- yfinance does **not** support 4h natively — fetched as 1h and resampled via `df.resample("4h")`
- Binance Futures fallback: if Spot API fails, caller should retry with Futures endpoint (see data_fetcher)
