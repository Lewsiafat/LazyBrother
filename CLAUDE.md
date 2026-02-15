# CLAUDE.md — Developer Reference

## Project Overview

**LazyBrother** is a Python/FastAPI backend service that analyzes candlestick charts for cryptocurrency and stocks. It combines classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice.

## Tech Stack

- **Python 3.12+** with **FastAPI** + **Uvicorn**
- **pandas** + **pandas-ta** for data manipulation and indicators
- **python-binance** for crypto data, **yfinance** for stock data
- **openai** / **google-generativeai** / **anthropic** for LLM synthesis
- **pydantic** + **pydantic-settings** for models and config
- **uv** for dependency management

## Architecture

Pipeline architecture — single FastAPI app with modular internal stages:

```
Request → DataFetcher → PatternAnalyzer → IndicatorCalc → SMCAnalyzer → LLMSynthesizer → Response
```

### Key Directories

```
app/
├── main.py              # FastAPI entry point, CORS, router registration
├── config.py            # pydantic-settings from .env (Settings singleton)
├── models/              # Pydantic request/response models
├── pipeline/            # Analysis pipeline stages + orchestrator
├── providers/           # LLM provider implementations (abstract base + 3 providers)
└── routers/             # API endpoint definitions
frontend/                # Vue 3 + Vite debug client
├── src/components/      # AnalysisForm, ResultPanel, RawJson, ErrorDisplay
├── src/api.js           # API client (fetch-based)
└── src/style.css        # Dark theme with glassmorphism
```

### Pipeline Modules (`app/pipeline/`)

| Module | Purpose |
|--------|---------|
| `data_fetcher.py` | `BinanceFetcher` (crypto) and `YFinanceFetcher` (stock) behind `BaseFetcher` ABC. Factory via `get_fetcher()` |
| `pattern_analyzer.py` | Detects 12+ candlestick patterns (single/dual/triple candle) |
| `indicator_calc.py` | RSI(14), MACD(12,26,9), Bollinger(20,2), SMA(20), EMA(50) via pandas-ta |
| `smc_analyzer.py` | Order Blocks, Fair Value Gaps, BOS/CHoCH, Liquidity Sweeps via swing point analysis |
| `llm_synthesizer.py` | Builds structured prompt, calls configured LLM, parses JSON response |
| `orchestrator.py` | `analyze()` runs full pipeline; merges multi-timeframe results |

### LLM Providers (`app/providers/`)

All implement `LLMProvider.synthesize(prompt) -> str`. Provider selected via `LLM_PROVIDER` env var, model via `LLM_MODEL`.

## API Endpoints

- `POST /api/v1/analyze` — main analysis (takes `symbol`, `market`, `mode`)
- `GET /api/v1/health` — health check
- `GET /` — service info
- `GET /docs` — auto-generated Swagger docs

## Analysis Modes

| Mode | Timeframes |
|------|-----------|
| `scalping` | 1m, 5m, 15m |
| `swing` | 15m, 1h, 4h |

## Running

```bash
uv sync                              # install backend deps
cp .env.example .env                  # configure
uv run uvicorn app.main:app --reload  # start backend

# Debug frontend (optional)
cd frontend && npm install && npm run dev
```

## Configuration

All config via `.env` file — see `.env.example` for all keys. Key vars: `LLM_PROVIDER`, `LLM_MODEL`, API keys for LLM and data sources.

## Conventions

- All pipeline stages are **async** functions
- Response models use **Pydantic v2** with `model_dump()`
- LLM responses are expected as **JSON only** (no markdown)
- If LLM fails, the API returns raw analysis data without the `analysis` field (graceful fallback)
- Error codes: 400 (bad input), 502 (LLM fail), 503 (data source timeout)
