# Development Plan: Prompt 管理與自訂功能

## Objective
增強 LLM Prompt 系統，讓使用者能透過前端介面**自訂、管理、匯入** Prompt，以獲得更精細的交易分析指引。

## Requirements
- [ ] 後端支援接收自訂 Prompt 附加內容（隨 API 請求一起傳送）
- [ ] 後端新增 Prompt 模板 API（用戶端 CRUD 管理 Prompt 片段）
- [ ] 前端新增 Prompt 管理面板（查看/編輯/匯入 Markdown Prompt）
- [ ] 匯入 Markdown 檔案作為額外 Prompt 內容
- [ ] 現有 `_build_prompt()` 邏輯不受影響（自訂 Prompt 為附加，非取代）

## Phases

### Phase 1: 後端 — Prompt 儲存與 API
**Goal**: 建立 Prompt 片段的儲存機制與 CRUD API

**Tasks**:
- [ ] 新增 `app/models/prompt.py` — Prompt 片段的 Pydantic model
- [ ] 新增 `app/storage/prompt_store.py` — 基於檔案系統的 Prompt 儲存（JSON）
- [ ] 新增 `app/routers/prompts.py` — CRUD API 端點
- [ ] 在 `app/main.py` 註冊 prompts router

**Checkpoint**: API 可透過 `/docs` 測試 CRUD 操作

---

### Phase 2: 後端 — Prompt 整合至分析流程
**Goal**: 將自訂 Prompt 整合進 `_build_prompt()` 與分析請求

**Tasks**:
- [ ] 修改 `AnalysisRequest` 新增 `custom_prompt` 可選欄位
- [ ] 修改 `_build_prompt()` 支援附加自訂指引
- [ ] 修改 `orchestrator.py` 傳遞 custom_prompt
- [ ] 新增 Markdown 檔案上傳 API 端點

**Checkpoint**: 透過 `/docs` 測試帶自訂 Prompt 的分析請求

---

### Phase 3: 前端 — Prompt 管理面板
**Goal**: 建立前端 UI 讓使用者管理與匯入 Prompt

**Tasks**:
- [ ] 新增 `PromptManager.vue` 元件 — 管理已儲存的 Prompt 片段
- [ ] 在 `AnalysisForm.vue` 新增自訂 Prompt 輸入區域
- [ ] 支援匯入 `.md` 檔案
- [ ] 更新 `api.js` 新增 Prompt 相關 API 呼叫
- [ ] 整合至 `App.vue` 佈局

**Checkpoint**: 前端可完整操作 Prompt CRUD、匯入 Markdown、送出分析

---

## Success Criteria
- [ ] 使用者可新增/編輯/刪除 Prompt 片段
- [ ] 使用者可匯入 Markdown 檔案作為 Prompt
- [ ] 分析時可選擇附加自訂 Prompt
- [ ] 現有分析功能不受影響（未選自訂 Prompt 時行為不變）
