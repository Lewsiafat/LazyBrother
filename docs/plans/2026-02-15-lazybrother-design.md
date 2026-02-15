# LazyBrother — Design Document

> **Date**: 2026-02-15  
> **Status**: Approved  
> **Stack**: Python · FastAPI · Pandas · LLM (OpenAI / Gemini / Claude)

## Overview

LazyBrother is a backend service that analyzes candlestick charts for **cryptocurrency** and **stocks**, combining classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice.

## Architecture — Pipeline

Single FastAPI app with a modular internal pipeline:

```
Request → DataFetcher → PatternAnalyzer → IndicatorCalc → SMCAnalyzer → LLMSynthesizer → Response
```

Each pipeline stage is its own module, testable in isolation. A central **Orchestrator** wires them together.

### Pipeline Stages

| Stage | Responsibility |
|-------|---------------|
| **DataFetcher** | Pull OHLCV candles from Binance (crypto) or yFinance/Alpha Vantage (stocks) |
| **PatternAnalyzer** | Detect candlestick patterns: Doji, Hammer, Engulfing, Morning Star, Head & Shoulders, etc. |
| **IndicatorCalc** | Compute RSI, MACD, Bollinger Bands, SMA, EMA |
| **SMCAnalyzer** | Identify Order Blocks, Fair Value Gaps, Break of Structure (BOS), Change of Character (CHoCH), Liquidity Sweeps |
| **LLMSynthesizer** | Send all analysis data to a configurable LLM, receive structured trading advice |
| **Orchestrator** | Wire stages together, run the full pipeline for a given request |

### Analysis Modes

| Mode | Timeframes |
|------|-----------|
| **Scalping** | 1m, 5m, 15m |
| **Swing** | 15m, 1h, 4h |

## API Design

### `POST /api/v1/analyze`

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "market": "crypto",
  "mode": "scalping"
}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "market": "crypto",
  "mode": "scalping",
  "timestamp": "2026-02-15T21:05:00Z",
  "analysis": {
    "trading_thesis": "BTC shows bullish engulfing on 5m with BOS confirmation...",
    "confidence_level": "high",
    "confidence_reason": "Multiple confluences: bullish pattern + SMC structure + oversold RSI bounce",
    "direction": "long",
    "entry_zone": { "low": 95300, "high": 95500 },
    "stop_loss": {
      "price": 94800,
      "reason": "Below the 15m order block and previous swing low"
    },
    "take_profit_targets": [
      { "label": "TP1", "price": 96200, "reason": "Previous 5m resistance / FVG fill" },
      { "label": "TP2", "price": 97000, "reason": "4h fair value gap upper boundary" },
      { "label": "TP3", "price": 98500, "reason": "Fibonacci 1.618 extension" }
    ]
  },
  "details": {
    "patterns_detected": ["bullish_engulfing", "morning_star"],
    "indicators": {
      "rsi_14": 32.5,
      "macd": { "value": -120, "signal": -95, "histogram": -25 },
      "bollinger": { "upper": 97000, "middle": 95800, "lower": 94600 },
      "sma_20": 95600,
      "ema_50": 95200
    },
    "smc": {
      "order_blocks": [{ "type": "bullish", "zone": [95000, 95200], "timeframe": "15m" }],
      "fair_value_gaps": [{ "type": "bullish", "zone": [95400, 95600], "timeframe": "5m" }],
      "structure": "BOS_bullish",
      "liquidity_sweeps": ["sell-side sweep at 94900"]
    },
    "timeframes_analyzed": ["1m", "5m", "15m"]
  }
}
```

### `GET /api/v1/health`

Returns service health status.

## Project Structure

```
LazyBrother/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Pydantic-settings from .env
│   ├── models/
│   │   ├── request.py           # Pydantic request models
│   │   └── response.py          # Pydantic response models
│   ├── routers/
│   │   └── analysis.py          # /api/v1/analyze endpoint
│   ├── pipeline/
│   │   ├── data_fetcher.py      # Binance + yFinance adapters
│   │   ├── pattern_analyzer.py  # Candlestick pattern detection
│   │   ├── indicator_calc.py    # Classical technical indicators
│   │   ├── smc_analyzer.py      # Smart Money Concepts
│   │   ├── llm_synthesizer.py   # LLM integration
│   │   └── orchestrator.py      # Pipeline orchestration
│   └── providers/
│       ├── base.py              # Abstract LLM provider
│       ├── openai_provider.py
│       ├── gemini_provider.py
│       └── claude_provider.py
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## Configuration (`.env`)

```env
# LLM Provider: "openai" | "gemini" | "claude"
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
ANTHROPIC_API_KEY=sk-ant-...

# Data Sources
BINANCE_API_KEY=
BINANCE_API_SECRET=
ALPHA_VANTAGE_API_KEY=

# Server
HOST=0.0.0.0
PORT=8000
```

## Error Handling

| Scenario | HTTP Code | Behavior |
|----------|-----------|----------|
| Invalid symbol | `400` | Clear error message |
| Data source timeout | `503` | 10s timeout, retry suggestion |
| LLM failure | `502` | Fallback: return raw patterns + indicators without LLM synthesis |
| Rate limiting | `429` | Respect exchange limits |

## Dependencies

| Library | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web framework + server |
| `pandas` | Candle data manipulation |
| `pandas-ta` | Technical indicators |
| `python-binance` | Binance API client |
| `yfinance` | Stock data |
| `openai` | OpenAI LLM client |
| `google-generativeai` | Gemini LLM client |
| `anthropic` | Claude LLM client |
| `pydantic-settings` | Config management |
| `httpx` | HTTP client |
| `pytest` | Testing |

## Testing Strategy

- **Unit tests**: Each pipeline module with fixture data
- **Integration tests**: Full pipeline with mocked external APIs
- **LLM tests**: Recorded responses (no real API calls in CI)
