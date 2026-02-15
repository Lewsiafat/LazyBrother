# LazyBrother — Specification

## 1. System Purpose

LazyBrother is a candlestick chart analysis backend that ingests live market data, runs multi-layer technical analysis, and uses an LLM to synthesize a structured trading recommendation. It supports both cryptocurrency and stock markets.

---

## 2. Supported Markets & Data Sources

| Market | Data Source | Auth Required | Notes |
|--------|-----------|---------------|-------|
| Crypto | Binance API (`python-binance`) | Optional (public endpoints work) | Real-time OHLCV klines |
| Stock | Yahoo Finance (`yfinance`) | No | Free, rate-limited. 4h candles resampled from 1h |
| Stock | Alpha Vantage (`httpx`) | Yes (API key) | Reserved for future use |

---

## 3. Analysis Pipeline

### 3.1 Data Fetcher

- Fetches OHLCV candles for all timeframes in the selected mode
- Returns `dict[timeframe, DataFrame]` with columns: `open, high, low, close, volume`
- 200 candles per timeframe by default

### 3.2 Pattern Analyzer

Detects patterns from the **most recent candles** in each timeframe:

| Category | Patterns |
|----------|----------|
| Single-candle | Doji, Hammer, Inverted Hammer, Shooting Star, Spinning Top |
| Dual-candle | Bullish Engulfing, Bearish Engulfing, Piercing Line, Dark Cloud Cover |
| Triple-candle | Morning Star, Evening Star, Three White Soldiers, Three Black Crows |

### 3.3 Technical Indicators

| Indicator | Parameters | Library |
|-----------|-----------|---------|
| RSI | period=14 | pandas-ta |
| MACD | fast=12, slow=26, signal=9 | pandas-ta |
| Bollinger Bands | length=20, std=2 | pandas-ta |
| SMA | period=20 | pandas-ta |
| EMA | period=50 | pandas-ta |

### 3.4 Smart Money Concepts (SMC)

| Concept | Detection Method |
|---------|-----------------|
| **Order Blocks** | Last bearish candle before strong bullish move (bullish OB) and vice versa. Strength threshold: 1.5× body ratio |
| **Fair Value Gaps** | Three-candle gaps where `candle[i-1].high < candle[i+1].low` (bullish) or reverse |
| **Break of Structure (BOS)** | Higher highs + higher lows = bullish BOS; lower highs + lower lows = bearish BOS |
| **Change of Character (CHoCH)** | First structural break against the trend (e.g., first lower high in an uptrend) |
| **Liquidity Sweeps** | Price briefly breaks a swing level then reverses back |

Swing points detected using a **5-candle lookback window** on both sides.

### 3.5 LLM Synthesis

- Builds a structured prompt containing all pattern, indicator, and SMC data across all timeframes
- Requests JSON-only output from the LLM
- Parses response into `TradingAnalysis` model
- Falls back to returning raw data if LLM call fails

---

## 4. Analysis Modes

| Mode | Timeframes | Use Case |
|------|-----------|----------|
| `scalping` | 1m, 5m, 15m | Day trading, quick entries/exits |
| `swing` | 15m, 1h, 4h | Multi-day positions, trend following |

---

## 5. API Specification

### `POST /api/v1/analyze`

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "market": "crypto",    // "crypto" | "stock"
  "mode": "scalping"     // "scalping" | "swing"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Echo of requested symbol |
| `market` | string | "crypto" or "stock" |
| `mode` | string | "scalping" or "swing" |
| `timestamp` | datetime | UTC timestamp of analysis |
| `analysis` | TradingAnalysis \| null | LLM-generated advice (null if LLM failed) |
| `details` | AnalysisDetails | Raw pattern/indicator/SMC data |

**TradingAnalysis fields:**

| Field | Type | Description |
|-------|------|-------------|
| `trading_thesis` | string | 交易論點 — core reason for recommendation |
| `confidence_level` | string | 信號強度 — "high", "medium", "low" |
| `confidence_reason` | string | Why this confidence level |
| `direction` | string | 交易方向 — "long" or "short" |
| `entry_zone` | {low, high} | 入場價格區間 |
| `stop_loss` | {price, reason} | 止損價格 with structural reasoning |
| `take_profit_targets` | [{label, price, reason}] | 止盈目標 — at least TP1, TP2, TP3 |

### Error Responses

| Code | Condition | Behavior |
|------|-----------|----------|
| 400 | Invalid symbol/params | Clear error message |
| 502 | LLM failure | May still return `details` without `analysis` |
| 503 | Data source timeout | 10s timeout, retry suggestion |

---

## 6. Configuration

All via `.env` file using `pydantic-settings`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | "openai", "gemini", or "claude" |
| `LLM_MODEL` | (per-provider) | Specific model version (empty = default) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `ANTHROPIC_API_KEY` | — | Anthropic Claude API key |
| `BINANCE_API_KEY` | — | Binance API key |
| `BINANCE_API_SECRET` | — | Binance API secret |
| `ALPHA_VANTAGE_API_KEY` | — | Alpha Vantage API key |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

**Default models per provider:**

| Provider | Default Model |
|----------|--------------|
| OpenAI | `gpt-4o` |
| Gemini | `gemini-2.0-flash` |
| Claude | `claude-sonnet-4-20250514` |

---

## 7. Future Development Roadmap

### Phase 2: Enhanced Analysis
- [ ] Volume Profile analysis (POC, VAH, VAL)
- [ ] Fibonacci retracement/extension auto-detection
- [ ] Multi-timeframe confluence scoring (weighted signal strength)
- [ ] Support for additional candlestick patterns (Tweezer Top/Bottom, Three Inside Up/Down)

### Phase 3: Data & Caching
- [ ] Redis caching for candle data (avoid redundant API calls)
- [ ] Historical analysis storage (PostgreSQL)
- [ ] Webhooks / scheduled analysis (cron-style)
- [ ] Alpha Vantage integration for stocks (as alternative to yFinance)

### Phase 4: Advanced Features
- [ ] Backtesting engine — test strategy performance on historical data
- [ ] Portfolio-level analysis (multi-symbol correlation)
- [ ] Risk/reward ratio calculator
- [ ] Custom indicator support (user-defined formulas)

### Phase 5: Deployment & Ops
- [ ] Docker containerization
- [ ] Rate limiting middleware
- [ ] API key authentication
- [ ] Prometheus metrics / health monitoring
- [ ] CI/CD pipeline with automated tests

### Phase 6: Frontend (Optional)
- [ ] Web dashboard for visual chart display
- [ ] Real-time WebSocket updates
- [ ] Alert system (Telegram/Discord/Email notifications)
