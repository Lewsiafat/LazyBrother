# 規格文件：商品選擇系統與幣安產品列表整合

- **分支名稱**: `feat/add-symbol-selection-system`
- **日期**: 2026-03-12
- **任務類型**: `feat`

## 任務描述
移除原本的股票 (Yahoo Finance) 支援，全面專注於加密貨幣。實作一個透過幣安 (Binance) API 動態取得可用交易對的系統，並在前端提供搜尋與選擇功能，同時自動紀錄使用者最後選擇的商品。

## 技術方案建議

### 1. 後端 (FastAPI)
- **移除 yfinance**: 刪除 `YFinanceFetcher` 相關邏輯，簡化 `data_fetcher.py`。
- **新增產品列表 API**: 
  - 在 `app/routers/analysis.py` 或新路由新增 `GET /api/v1/symbols`。
  - 呼叫 `binance-python` 的 `get_exchange_info()` 取得所有 `USDT` 交易對。
- **簡化模型**: 更新 `MarketType` 或移除 `market` 參數（若不再需要分市場）。

### 2. 前端 (Vue 3)
- **搜尋選擇器**:
  - 在 `AnalysisForm.vue` 中，將原本的 `input` 改為具有搜尋功能的 `select` 或自定義下拉選單。
  - 元件掛載時 (onMounted) 呼叫後端 API 取得產品清單。
- **本地紀錄**:
  - 使用 `localStorage` 儲存 `last_selected_symbol`。
  - 初始化時優先讀取該紀錄。
- **移除股票選項**: 調整 UI 移除 "Stock" 相關切換。

### 3. 持久化與優化
- **快取產品列表**: 後端可考慮簡單的記憶體快取，避免每次請求都呼叫幣安 API。

## 任務清單 (Checklist)

### 後端實作
- [x] 移除 `app/pipeline/data_fetcher.py` 中的 `YFinanceFetcher` 與 `yf` 依賴。
- [x] 修改 `app/models/request.py`，移除 `MarketType.STOCK`。
- [x] 在 `app/routers/analysis.py` 新增 `GET /symbols` 端點。
- [x] 實作 `BinanceFetcher.get_all_symbols()` 邏輯（僅限 USDT 對）。
- [x] 更新 `app/pipeline/orchestrator.py` 移除市場判定邏輯。

### 前端實作
- [x] 在 `frontend/src/api.js` 新增 `fetchSymbols` 函式。
- [x] 修改 `AnalysisForm.vue`:
    - [x] 呼叫 API 載入產品清單。
    - [x] 實作可搜尋的下拉選單 (Searchable Select)。
    - [x] 移除 Market 切換 UI。
    - [x] 實作 `localStorage` 儲存與讀取最後選擇的 Symbol。
- [x] 移除 `quickPicks` 中的股票項目。

### 測試與驗證
- [x] 驗證 `/api/v1/symbols` 回傳正確的 USDT 交易對。
- [x] 驗證前端能正確顯示、搜尋並選擇 Symbol。
- [x] 驗證重新整理後會自動選中上次選擇的 Symbol。
- [x] 驗證分析功能在移除 yfinance 後依然正常運作。
