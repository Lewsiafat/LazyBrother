# 🧸 LazyBrother

> Your lazy brother who still gives you solid trading advice.

**LazyBrother** (`v0.6.0`) is a backend service that analyzes candlestick charts for **cryptocurrency**, combining classical pattern recognition, technical indicators, Smart Money Concepts (SMC), and LLM-powered reasoning to produce structured investment advice — with a built-in backtesting system to validate signal quality.

## Features

- 🕯️ **Candlestick Pattern Detection** — Doji, Hammer, Engulfing, Morning/Evening Star, Three White Soldiers, and more
- 📊 **Technical Indicators** — RSI, MACD, Bollinger Bands, SMA, EMA
- 🧠 **Smart Money Concepts** — Order Blocks, Fair Value Gaps, BOS/CHoCH, Liquidity Sweeps
- 🤖 **LLM Synthesis** — AI-powered analysis combining all signals into actionable trading advice
- 🔍 **Dynamic Symbol Selection** — Integrated with Binance API to fetch available USDT pairs dynamically
- 🎛️ **Custom Prompts** — Inject your own custom instructions or strategies into the LLM pipeline
- 🔀 **Multi-Timeframe** — Scalping (1m/5m/15m) and Swing (15m/1h/4h) modes
- 🔌 **Multi-Provider** — OpenAI, Google Gemini, or Anthropic Claude
- 🖥️ **Debug Frontend** — Vue 3 visual client for testing the API with structured result cards
- 📸 **Snapshot & Backtest** — Save analysis results and validate signals with walk-forward backtesting
- 🚀 **One-Command Start** — `./start.sh` launches backend and frontend together

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run everything

```bash
./start.sh   # starts backend + frontend together
```

Or run separately:

```bash
uv run uvicorn app.main:app --reload   # backend only
```

### 4. Run the debug frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the visual debug client.

### 5. Try via curl

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "mode": "scalping"}'
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## API

### `POST /api/v1/analyze`

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading symbol (e.g. `BTCUSDT`, `ETHUSDT`) |
| `mode` | string | `scalping` (1m/5m/15m) or `swing` (15m/1h/4h) |
| `custom_prompt` | string | Optional inline prompt / instructions |
| `prompt_ids` | list | Optional saved prompt IDs to include |

**Response** includes:
- **Trading Thesis** — core reason for the recommendation
- **Confidence Level** — high/medium/low with reasoning
- **Direction** — long or short
- **Entry Zone** — suggested price range
- **Stop-Loss** — price with reasoning
- **Take-Profit Targets** — TP1, TP2, TP3 with reasoning
- **Raw Details** — patterns, indicators, and SMC data

### `GET /api/v1/symbols`

Returns a list of all available Spot USDT trading pairs from Binance.

### `GET /api/v1/health`

Returns service health status.

### `GET / POST / PUT / DELETE /api/v1/prompts`

CRUD endpoints for managing saved custom prompt snippets. Support importing `.md` files.

### `GET / POST / DELETE /api/v1/snapshots`

Save, list, and delete analysis snapshots for backtesting.

## Backtesting

```bash
# Walk-forward backtest (rule-based, no LLM)
uv run python backtest_run.py --symbol BTCUSDT --mode swing --start 2024-01-01 --end 2024-12-31

# Backtest saved LLM snapshots
uv run python backtest_run.py --from-snapshots

# Dump LLM prompts at each signal point
uv run python backtest_run.py --symbol BTCUSDT --mode swing --start 2024-01-01 --end 2024-01-31 --dump-prompts
```

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

## Architecture

```
Request → DataFetcher → PatternAnalyzer → IndicatorCalc → SMCAnalyzer → LLMSynthesizer → Response
```

Each stage is a separate, testable module. The orchestrator wires them together.

## License

MIT
