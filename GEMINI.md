# 🧸 LazyBrother

歡迎來到 **LazyBrother** 專案目錄！這是一個結合技術分析與大型語言模型 (LLM) 的交易分析後端服務，附帶一個基於 Vue 3 + Vite 的前端偵錯介面。

## 🎯 專案概覽

**LazyBrother** 透過分析加密貨幣的 K 線圖 (Candlestick charts)，結合傳統型態識別、技術指標、聰明錢概念 (Smart Money Concepts, SMC)，並利用 LLM 產生結構化的投資建議。

**目前版本**：`v0.5.0`

### 核心功能

- 🕯️ **K 線型態識別**：涵蓋 12+ 種型態，分單蠟燭、雙蠟燭、三蠟燭
- 📊 **技術指標**：RSI(14)、MACD(12,26,9)、布林通道 Bollinger(20,2)、SMA(20)、EMA(50)
- 🧠 **聰明錢概念 (SMC)**：訂單塊 (Order Blocks)、公平價值缺口 (FVG)、BOS/CHoCH、流動性掠奪 (Liquidity Sweeps)
- 🤖 **LLM 綜合分析**：支援 OpenAI (`gpt-4o`)、Google Gemini (`gemini-2.0-flash`)、Anthropic Claude (`claude-sonnet-4-20250514`)
- 🔍 **動態商品選擇**：整合幣安 API 動態獲取所有 USDT 交易對，支援前端即時搜尋與商品持久化
- 🎛️ **自訂 Prompt**：提供 Prompt 管理介面與 API，支援即時附加指令或匯入 Markdown。
- 🔀 **多時間框架**：Scalping (1m/5m/15m)、Swing (15m/1h/4h)

## 🛠️ 技術棧

| 層次 | 技術 |
|---|---|
| **後端** | Python ≥3.12, FastAPI, Uvicorn |
| **資料處理** | pandas, pandas-ta |
| **資料源** | python-binance（加密貨幣）|
| **AI 整合** | openai, google-generativeai, anthropic |
| **設定管理** | pydantic + pydantic-settings |
| **套件管理** | `uv` |
| **前端** | Vue 3, Vite |

## 🚀 開發與運行指南

### 後端

```bash
# 安裝依賴
uv sync

# 設定環境變數
cp .env.example .env  # 填入 API Keys

# 啟動開發伺服器
uv run uvicorn app.main:app --reload
```

API 文件：`http://localhost:8000/docs`

### 前端（偵錯用）

```bash
cd frontend
npm install
npm run dev
```

前端介面：`http://localhost:5173`

## 📂 目錄結構

```
LazyBrother/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # pydantic-settings 設定
│   ├── models/
│   │   ├── request.py       # AnalysisRequest (移除 MarketType)
│   │   ├── response.py      # AnalysisResponse, TradingAnalysis, 等
│   │   └── prompt.py        # PromptSnippet
│   ├── storage/
│   │   └── prompt_store.py  # JSON 持久化 CRUD
│   ├── pipeline/
│   │   ├── data_fetcher.py  # BaseFetcher, BinanceFetcher (新增 get_all_symbols)
│   │   ├── pattern_analyzer.py
│   │   ├── indicator_calc.py
│   │   ├── smc_analyzer.py
│   │   ├── llm_synthesizer.py
│   │   └── orchestrator.py     # analyze() 主流程 (僅限 Crypto)
│   ├── providers/
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   └── claude_provider.py
│   └── routers/
│       ├── analysis.py      # POST /analyze, GET /symbols, GET /health
│       └── prompts.py       # Prompt CRUD
├── frontend/                # Vue 3 + Vite 偵錯前端
│   └── src/
│       ├── App.vue
│       ├── api.js           # fetch-based API 客戶端
│       ├── style.css        # 深色主題 + glassmorphism
│       └── components/      # 各項 UI 元件 (含 PromptManager)
├── data/                    # JSON 資料儲存區
├── docs/                    # 規格與計畫文件
├── .agent/                  # AI Skills 與腳本工具
├── pyproject.toml           # 專案設定與依賴（使用 uv）
└── .env.example             # 環境變數範本
```

## ⚙️ 環境變數設定（`.env`）

| 變數 | 說明 | 預設值 |
|---|---|---|
| `LLM_PROVIDER` | `openai` / `gemini` / `claude` | `openai` |
| `LLM_MODEL` | 指定模型版本（留空使用預設） | `""` |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `GEMINI_API_KEY` | Google Gemini API Key | - |
| `ANTHROPIC_API_KEY` | Anthropic API Key | - |
| `BINANCE_API_KEY` | Binance API Key（加密貨幣資料） | - |
| `BINANCE_API_SECRET` | Binance API Secret | - |
| `HOST` | 伺服器 Host | `0.0.0.0` |
| `PORT` | 伺服器 Port | `8000` |

## 🔌 API 端點

| 方法 | 路徑 | 說明 |
|---|---|---|
| `POST` | `/api/v1/analyze` | 主分析端點（`symbol`, `mode`, `custom_prompt` 等） |
| `GET` | `/api/v1/symbols` | 獲取可用幣安交易對 |
| `GET` | `/api/v1/health` | 健康檢查 |
| `REST` | `/api/v1/prompts` | Prompt CRUD 操作 |
| `GET` | `/` | 服務資訊 |
| `GET` | `/docs` | Swagger 自動文件 |

### 分析模式

| Mode | 時間框架 |
|---|---|
| `scalping` | 1m, 5m, 15m |
| `swing` | 15m, 1h, 4h |

## 📝 開發規範

1. **語言**：所有交互、註釋與說明必須使用**正體繁體中文**
2. **安全**：絕對禁止提交 `.env` 或包含敏感金鑰的檔案至版本控制
3. **確認機制**：執行任何修改、刪除或影響系統狀態的指令前，須先獲得使用者明確確認
4. **模組化**：Pipeline 各階段（`DataFetcher`、`PatternAnalyzer`、`IndicatorCalc`、`SMCAnalyzer`、`LLMSynthesizer`）保持獨立且可測試
5. **非同步**：所有 Pipeline 階段使用 `async` 函式
6. **Pydantic v2**：Response models 使用 `model_dump()`
7. **LLM 回應**：期望純 JSON（無 Markdown），失敗時優雅降級（回傳 raw 資料，不含 `analysis` 欄位）
8. **錯誤碼**：`400`（錯誤輸入）、`502`（LLM 失敗）、`503`（資料源逾時）
