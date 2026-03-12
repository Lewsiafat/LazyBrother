# Walkthrough: 商品選擇系統與幣安產品列表整合

- **分支名稱**: `feat/add-symbol-selection-system`
- **日期**: 2026-03-12
- **狀態**: 已完成 (Completed)

## 任務摘要
移除 Yahoo Finance (Stocks) 支援，全面專注於幣安 (Binance) 加密貨幣。實作動態產品清單 API 並在前端提供搜尋選擇器，同時支援最後選擇的 Symbol 持久化。

## 變更檔案清單

### 後端 (Backend)
- `pyproject.toml`: 移除 `yfinance` 依賴。
- `app/models/request.py`: 移除 `MarketType.STOCK`，簡化 `AnalysisRequest`。
- `app/pipeline/data_fetcher.py`: 
  - 移除 `YFinanceFetcher` 邏輯。
  - `BinanceFetcher` 新增 `get_all_symbols()`，獲取所有 USDT 交易對。
  - 簡化 `get_fetcher()` 與 `fetch_all_timeframes()`。
- `app/pipeline/orchestrator.py`: 移除市場判定邏輯，內部與回應硬編碼為 "crypto"。
- `app/routers/analysis.py`: 新增 `GET /api/v1/symbols` 端點。

### 前端 (Frontend)
- `frontend/src/api.js`: 
  - 新增 `fetchSymbols()` 呼叫後端 API。
  - `analyzeSymbol()` 移除 `market` 參數。
- `frontend/src/components/AnalysisForm.vue`:
  - 實作自定義、可搜尋的 Symbol 下拉選單。
  - 移除 Market 切換與股票相關 Quick Picks。
  - 實作 `localStorage` 紀錄並載入最後選擇的商品。
- `frontend/src/components/ResultPanel.vue`: 維持顯示 `market` 標籤（由後端回傳 "crypto"）。

### 文件 (Docs)
- `GEMINI.md` / `CLAUDE.md`: 更新版本至 `v0.4.0`，反映架構變動。
- `specs/add-symbol-selection-system.md`: 更新任務清單。

## 技術細節
1. **Symbol 搜尋與快取**: `BinanceFetcher` 內建簡單的成員變數快取，避免短時間內頻繁呼叫 Binance `exchange_info`。
2. **前端搜尋邏輯**: 使用 `computed` property 對所有產品進行即時過濾，並限制顯示前 50 筆以保持效能。
3. **兼容性**: 為了不破壞現有的 `AnalysisResponse` 模型及前端 ResultPanel 的顯示邏輯，後端在回應中仍會填充 `market: "crypto"` 欄位。

## 驗證結果
- [x] 後端 `/api/v1/symbols` 回傳正確交易對。
- [x] 前端可正常搜尋並選擇商品。
- [x] 重新整理後，自動選中上次選擇的商品。
- [x] 分析管線在移除 yfinance 後依然運作正常 (Binance Only)。
