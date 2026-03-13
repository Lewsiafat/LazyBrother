# 任務規格：在 Debug Client 增加顯示實時價格與分析時價格

- **分支名稱**: `feat/add-real-price-on-debug-client`
- **建立日期**: 2026-03-13
- **狀態**: 已完成

## 任務描述

在 LazyBrother 的前端 Debug Client (Vue 3) 中，使用者需要能直觀地比對「分析當時的幣價」與「目前的實時幣價」。

1. **後端 (Backend)**：在 API 回應中加入 `current_price` 欄位，代表送給 LLM 分析當下的最新價格。
2. **前端 (Frontend)**：
   - 顯示 API 回傳的「分析時價格」。
   - 透過 Binance WebSocket (`@ticker`) 建立即時連線，動態跳動顯示「目前實時價格」。
   - 處理 WebSocket 的生命週期（切換商品或卸載元件時關閉）。

## 技術方案

### 修改內容

#### 後端 (Python/FastAPI)
- `app/models/response.py`: `AnalysisResponse` 類別新增 `current_price: float` 欄位。
- `app/pipeline/orchestrator.py`: 在 `analyze()` 函式中，從抓取到的 candles (通常是最低 timeframe 的最後一筆) 提取最新收盤價，並填入 `AnalysisResponse`。

#### 前端 (Vue 3/Vite)
- `frontend/src/components/ResultPanel.vue`:
  - UI：在 `result-meta` 區塊新增顯示「分析時價格 (Analysis Price)」與「目前實時價格 (Real-time Price)」。
  - Logic：使用 `ref` 管理 `realTimePrice` 狀態。
  - WebSocket：
    - 當 `props.data` (分析結果) 改變時，根據 `symbol` 建立 `wss://stream.binance.com:9443/ws/<symbol>@ticker` 連線。
    - 監聽 `message` 事件更新 `realTimePrice`。
    - 確保在 `onUnmounted` 或 `symbol` 改變前關閉舊連線，避免記憶體洩漏或連線過多。

### 影響範圍
- API 回應結構增加一個欄位。
- 前端效能：WebSocket 連線會消耗微量頻寬，但不影響主流程。

## 任務清單 (Task Items)

- [x] **後端實作**
  - [x] 修改 `app/models/response.py` 定義，新增 `current_price: float`。
  - [x] 修改 `app/pipeline/orchestrator.py`，從 candles 提取最新收盤價並傳入 Response。
- [x] **前端實作**
  - [x] `ResultPanel.vue`: 新增 `realTimePrice` 的 `ref` 狀態。
  - [x] `ResultPanel.vue`: 實作 WebSocket 連線與訊息處理邏輯。
  - [x] `ResultPanel.vue`: 完善 WebSocket 生命週期管理 (Close on Unmount/Change)。
  - [x] `ResultPanel.vue`: 更新 Template，顯示分析時價格與實時跳動價格。
- [x] **驗證**
  - [x] 啟動後端，確認 `/api/v1/analyze` 有回傳 `current_price`。
  - [x] 開啟前端 Debug Client，確認幣價有隨交易所實時跳動，且與分析價格並列顯示。
