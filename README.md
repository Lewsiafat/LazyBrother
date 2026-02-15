# 🧸 LazyBrother

> Your lazy brother who still gives you solid trading advice.

**LazyBrother** is a backend service that analyzes candlestick charts for **cryptocurrency** and **stocks**, combining classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice.

## Features

- 🕯️ **Candlestick Pattern Detection** — Doji, Hammer, Engulfing, Morning/Evening Star, Three White Soldiers, and more
- 📊 **Technical Indicators** — RSI, MACD, Bollinger Bands, SMA, EMA
- 🧠 **Smart Money Concepts** — Order Blocks, Fair Value Gaps, BOS/CHoCH, Liquidity Sweeps
- 🤖 **LLM Synthesis** — AI-powered analysis combining all signals into actionable trading advice
- 🔀 **Multi-Timeframe** — Scalping (1m/5m/15m) and Swing (15m/1h/4h) modes
- 🔌 **Multi-Provider** — OpenAI, Google Gemini, or Anthropic Claude

## Quick Start

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

### 4. Try it

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "market": "crypto", "mode": "scalping"}'
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## API

### `POST /api/v1/analyze`

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading symbol (e.g. `BTCUSDT`, `AAPL`) |
| `market` | string | `crypto` or `stock` |
| `mode` | string | `scalping` (1m/5m/15m) or `swing` (15m/1h/4h) |

**Response** includes:
- **Trading Thesis** — core reason for the recommendation
- **Confidence Level** — high/medium/low with reasoning
- **Direction** — long or short
- **Entry Zone** — suggested price range
- **Stop-Loss** — price with reasoning
- **Take-Profit Targets** — TP1, TP2, TP3 with reasoning
- **Raw Details** — patterns, indicators, and SMC data

### `GET /api/v1/health`

Returns service health status.

## Configuration

Set these in your `.env` file:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `openai`, `gemini`, or `claude` |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `BINANCE_API_KEY` | Binance API key |
| `BINANCE_API_SECRET` | Binance API secret |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key |

## Architecture

```
Request → DataFetcher → PatternAnalyzer → IndicatorCalc → SMCAnalyzer → LLMSynthesizer → Response
```

Each stage is a separate, testable module. The orchestrator wires them together.

## License

MIT
