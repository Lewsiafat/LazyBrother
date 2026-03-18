# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LazyBrother** (`v0.6.0`) is a Python/FastAPI backend service that analyzes candlestick charts for cryptocurrency. It combines classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice. It features a dynamic symbol selection system using the Binance API and a walk-forward backtesting system for signal validation.

## Tech Stack

| Layer | Technology |
|---|---|
| **Python** | 3.12+ |
| **Web Framework** | FastAPI + Uvicorn |
| **Data** | pandas + pandas-ta |
| **Crypto Data** | python-binance (Spot USDT pairs) |
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
├── main.py              # FastAPI entry point
├── config.py            # pydantic-settings singleton
├── models/
│   ├── request.py       # AnalysisMode, TIMEFRAME_PRESETS, AnalysisRequest (market removed)
│   ├── response.py      # AnalysisResponse, TradingAnalysis, IndicatorData, SMCData, etc.
│   ├── prompt.py        # PromptSnippet CRUD models
│   └── snapshot.py      # AnalysisSnapshot / SnapshotCreate models
├── pipeline/
│   ├── data_fetcher.py  # BinanceFetcher (fetch_candles, get_all_symbols)
│   ├── pattern_analyzer.py
│   ├── indicator_calc.py
│   ├── smc_analyzer.py
│   ├── llm_synthesizer.py
│   └── orchestrator.py     # analyze() 5-step pipeline (hardcoded to crypto)
├── backtest/
│   ├── data_loader.py      # Binance historical candle loader
│   ├── signal_generator.py # Rule-based scoring (RSI, MACD, SMC, patterns)
│   ├── simulator.py        # Walk-forward trade simulation with partial TP exits
│   ├── evaluator.py        # Win rate, profit factor, drawdown metrics
│   └── runner.py           # BacktestRunner (run, dump_prompts, run_from_snapshots)
├── storage/
│   └── snapshot_store.py   # JSON persistence for snapshots (data/snapshots.json)
├── providers/
│   ├── base.py          # LLMProvider ABC
│   ├── openai_provider.py
│   ├── gemini_provider.py
│   └── claude_provider.py
└── routers/
    ├── analysis.py      # POST /analyze, GET /symbols, GET /health
    ├── prompts.py       # CRUD operations and markdown import
    └── snapshots.py     # GET/POST/DELETE /api/v1/snapshots
frontend/                # Vue 3 + Vite debug client
├── src/App.vue
├── src/api.js           # fetchSymbols(), analyzeSymbol(), saveSnapshot(), listSnapshots()
└── src/components/      # AnalysisForm (searchable symbol select + localStorage)
backtest_run.py          # Backtest CLI entry point
start.sh                 # One-command backend + frontend launcher
```

### Pipeline Modules (`app/pipeline/`)

| Module | Key Function | Notes |
|---|---|---|
| `data_fetcher.py` | `fetch_all_timeframes()` | 200 candles per TF from Binance |
| `pattern_analyzer.py` | `analyze_patterns()` | 12+ patterns: doji, hammer, engulifing, stars, etc. |
| `indicator_calc.py` | `calculate_all_timeframes()` | RSI(14), MACD, Bollinger, SMA(20), EMA(50) |
| `smc_analyzer.py` | `analyze_smc_all_timeframes()` | OB, FVG, BOS/CHoCH, Sweeps |
| `llm_synthesizer.py` | `synthesize_analysis()` | Builds prompt → calls LLM → parses JSON → returns `(analysis, prompt)` |
| `orchestrator.py` | `analyze()` | Full 5-step pipeline. |

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Main analysis (`symbol`, `mode`, `custom_prompt`, `prompt_ids`) |
| `GET` | `/api/v1/symbols` | Get all available USDT symbols from Binance |
| `GET` | `/api/v1/health` | Health check |
| `*` | `/api/v1/prompts` | Prompt snippet CRUD |
| `GET` | `/api/v1/snapshots` | List saved analysis snapshots |
| `POST` | `/api/v1/snapshots` | Save an analysis snapshot |
| `DELETE` | `/api/v1/snapshots/{id}` | Delete a snapshot |

## Commands

```bash
# Setup
uv sync                              # install backend deps
cp .env.example .env                  # configure API keys

# Run backend
uv run uvicorn app.main:app --reload  # http://localhost:8000

# Run both (backend + frontend)
./start.sh                            # http://localhost:8000 + :5173

# Debug frontend
cd frontend && npm install && npm run dev  # http://localhost:5173

# Backtest
uv run python backtest_run.py --symbol BTCUSDT --mode swing --start 2024-01-01 --end 2024-12-31
uv run python backtest_run.py --from-snapshots
```

## Conventions

- All pipeline stages are **async** functions
- Response models use **Pydantic v2** with `model_dump()`
- LLM responses are expected as **JSON only**
- Frontend uses **localStorage** to persist `last_selected_symbol` and `backend_port`
- Symbol selector in frontend is a **custom searchable dropdown**
- Backwards Compatibility: `AnalysisResponse` still contains `market: "crypto"` for frontend compatibility
