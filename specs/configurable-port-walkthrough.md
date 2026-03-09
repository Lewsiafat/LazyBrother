# Walkthrough: Configurable Backend Port

**Branch**: `feature/configurable-port`
**Date**: 2026-03-09
**Merged to**: `master`

## Summary

為 LazyBrother Debug Client 新增「可指定 port」功能：前端 Dev Server 可透過環境變數指定自己的 port，前端 UI 可在執行期間動態修改連線的後端 port，設定值持久化儲存於 localStorage。

## Changed Files

| 檔案 | 說明 |
|---|---|
| `frontend/vite.config.js` | 新增 `server.port`，支援 `VITE_PORT` 環境變數（預設 5173） |
| `frontend/src/api.js` | 將靜態 `BASE_URL` 改為動態 `getBaseUrl()`，新增 `getBackendPort()` / `setBackendPort()` 讀寫 localStorage |
| `frontend/src/components/AnalysisForm.vue` | 新增 Backend Port 輸入欄位，修改即存 localStorage 並即時觸發 health re-check，emit `port-updated` 事件 |
| `frontend/src/App.vue` | Footer 動態顯示當前 backend port（響應 `port-updated` 事件） |

## Implementation Details

- **localStorage key**: `lazybrother_backend_port`，預設值 `8000`
- **VITE_API_URL 優先**: 若有設定 `VITE_API_URL` 環境變數，仍優先使用，不讀 localStorage
- **Health re-check**: port 變更時立即重置 `backendOk = null` 並重新呼叫 `/api/v1/health`
- **事件傳遞**: `AnalysisForm` → `emit('port-updated')` → `App.vue` 的 `onPortUpdated()` 同步 footer 顯示

## Usage

```bash
# 後端：指定 port（已有支援）
uv run uvicorn app.main:app --reload --port 8000
# 或
PORT=9000 uv run uvicorn app.main:app --reload

# 前端 Dev Server：指定 port
cd frontend && npm run dev              # 預設 5173
VITE_PORT=3000 npm run dev             # 指定 3000

# 前端 UI：直接在 Backend Port 輸入框修改（即時生效，頁面重整後保留）
```
