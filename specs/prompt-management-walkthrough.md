# Prompt Management Feature Walkthrough

**Date:** 2026-03-09
**Branch:** feature/prompt-management

## Summary
實作了自訂 Prompt 管理功能，由三個主要階段構成：
1. **後端 Prompt 儲存與 CRUD API (`/api/v1/prompts`)**：支援新增、修改、刪除、條列，以及透過上傳 Markdown 檔案直接匯入 Prompt。儲存機制採用 JSON 持久化檔案 (`data/prompts.json`)。
2. **核心 Pipeline 整合**：修改了 `AnalysisRequest` 模型支援 `custom_prompt` 與 `prompt_ids`；更新了 `orchestrator.py` 在執行 `synthesize_analysis` 時附上 custom instructions；`_build_prompt` 現在能接受並直接附加自訂的提示詞指令到最終 LLM Prompt。
3. **前端 UI**：新增了可開合的 `PromptManager.vue` 獨立側邊欄元件，並將 `AnalysisForm.vue` 擴增了一區「📝 Custom Prompt / Instructions (Optional)」以直接送出自訂提示詞。

## Changed Files
- **Backend Models:**
  - `[NEW]` `app/models/prompt.py`: Pydantic models for prompt snippets (Create, Update).
  - `[MODIFY]` `app/models/request.py`: Added `custom_prompt` and `prompt_ids` to `AnalysisRequest`.
- **Backend Storage & Routing:**
  - `[NEW]` `app/storage/prompt_store.py`: Persistent storage layer for snippets (JSON based).
  - `[NEW]` `app/routers/prompts.py`: CRUD and Markdown import API endpoints.
  - `[MODIFY]` `app/main.py`: Registered new router; added `python-multipart` to `pyproject.toml` dependencies via `uv`.
- **Pipeline:**
  - `[MODIFY]` `app/pipeline/orchestrator.py`: Hydrate snippet contents and construct `custom_instructions`.
  - `[MODIFY]` `app/pipeline/llm_synthesizer.py`: `_build_prompt` and `synthesize_analysis` modified to accept custom instructions.
- **Frontend UI:**
  - `[NEW]` `frontend/src/components/PromptManager.vue`: Sidebar component for snippet CRUD and markdown import.
  - `[MODIFY]` `frontend/src/App.vue`: Wired `PromptManager` into layout and connected custom events.
  - `[MODIFY]` `frontend/src/components/AnalysisForm.vue`: Extended with available snippet checkboxes and inline text input for immediate custom constraints.
  - `[MODIFY]` `frontend/src/api.js`: All new fetch wrappers for prompt CRUD.

## Details
- Markdown 匯入功能採用 `multipart/form-data` 以利後端擷取檔案名稱當作內建的 Prompt Name (無縫匯入)。
- PromptManager 更新 `prompts` 清單後，會主動透過事件連通給 AnalysisForm 更新能勾選的清單。
- 使用者如果在 AnalysisForm 勾選多個 prompt_ids 且輸入 inline custom constraints，後端會將所有內容以 `\n\n` 串接放入 `custom_instructions` 並直接附在 "Requirements" 之後，由 LLM 合併處理。
