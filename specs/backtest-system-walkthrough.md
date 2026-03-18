# Backtest System — Walkthrough

- **分支:** `feat/backtest-system`
- **日期:** 2026-03-18

## 變更摘要
新增完整的回測系統（walk-forward backtesting），包含規則式訊號產生器、交易模擬器、績效評估器，以及 Snapshot 機制讓使用者從 UI 儲存 LLM 分析結果供回測驗證。同時新增 `start.sh` 一鍵啟動前後端。

## 修改的檔案

### 新增檔案
| 檔案 | 說明 |
|---|---|
| `app/backtest/__init__.py` | Backtest package init |
| `app/backtest/data_loader.py` | 從 Binance 載入歷史 K 線資料 |
| `app/backtest/signal_generator.py` | 規則式評分（RSI、MACD、SMC、patterns） |
| `app/backtest/simulator.py` | Walk-forward 交易模擬，支援部分止盈出場 |
| `app/backtest/evaluator.py` | 勝率、Profit Factor、Drawdown 等績效指標 |
| `app/backtest/runner.py` | BacktestRunner：`run()`、`dump_prompts()`、`run_from_snapshots()` |
| `app/models/snapshot.py` | AnalysisSnapshot / SnapshotCreate Pydantic models |
| `app/storage/snapshot_store.py` | JSON 檔案式 snapshot 儲存（`data/snapshots.json`） |
| `app/routers/snapshots.py` | REST API：GET/POST/DELETE `/api/v1/snapshots` |
| `backtest_run.py` | CLI 進入點，支援 walk-forward / snapshot / prompt-dump 三種模式 |
| `data/snapshots.json` | Snapshot 持久化檔案 |
| `start.sh` | 一鍵啟動 backend + frontend 的 shell script |

### 修改檔案
| 檔案 | 說明 |
|---|---|
| `app/main.py` | 註冊 snapshots router |
| `app/models/response.py` | `AnalysisResponse` 新增 `prompt` 欄位 |
| `app/pipeline/llm_synthesizer.py` | `synthesize_analysis()` 回傳 `(TradingAnalysis \| None, str)` 包含 prompt |
| `app/pipeline/orchestrator.py` | 接收 prompt 並寫入 response |
| `frontend/src/api.js` | 新增 `saveSnapshot()`、`listSnapshots()`、`deleteSnapshot()` |
| `frontend/src/components/ResultPanel.vue` | 新增「Save Snapshot」按鈕及 UI 狀態管理 |

## 技術細節

### 回測架構
Pipeline 維持不變，回測系統獨立於 `app/backtest/` 模組。兩種回測模式：
1. **Walk-forward**（規則式）：不呼叫 LLM，用 RSI/MACD/SMC/patterns 綜合評分產生訊號
2. **Snapshot**（LLM 驗證）：從 UI 儲存的真實 LLM 訊號載入，取得後續 K 線驗證是否獲利

### Prompt 回傳
`llm_synthesizer.synthesize_analysis()` 的回傳型別從 `TradingAnalysis | None` 改為 `tuple[TradingAnalysis | None, str]`，讓 orchestrator 能將 prompt 存入 response，供 snapshot 機制使用。

### Snapshot 儲存
使用 JSON 檔案（`data/snapshots.json`）而非資料庫，保持輕量。前端 ResultPanel 新增「Save Snapshot」按鈕，點擊後將完整 `AnalysisResponse`（含 prompt）送至後端儲存。
