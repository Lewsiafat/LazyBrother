---
name: archive-task
description: Archive DEVPLAN.md and walkthrough documents into docs/archive/ organized by task name. Use when the user says "archive", "archive task", "save devplan", "archive walkthrough", or wants to store completed task documentation for project history.
---

# Archive Task Skill

Archives completed task documents (`DEVPLAN.md`, walkthrough) into `docs/archive/<task-name>/` for project history.

## Workflow

1. **Identify the task name** — derive from the current git branch or ask the user
   - Strip prefix: `feature/foo-bar` → `foo-bar`, `refactor/my-thing` → `my-thing`
   - If no branch context, ask: "What should this archive be named?"

2. **Locate documents to archive** — check for:
   - `DEVPLAN.md` in project root
   - Walkthrough artifact in the conversation artifacts directory
   - Any other task docs the user mentions

3. **Create archive folder** and copy/move files:
   ```
   docs/archive/<task-name>/
   ├── DEVPLAN.md
   └── walkthrough.md
   ```

4. **Clean up** — delete the original `DEVPLAN.md` from project root (it now lives in the archive)

5. **Confirm** — tell the user what was archived and where

## Rules

- Always use lowercase-with-hyphens for folder names
- Add a `**Date**` and `**Branch**` header to walkthrough if not already present
- Never overwrite an existing archive folder — append a number if needed (e.g. `task-name-2`)
- Add `docs/archive/` to `.gitignore` only if the user explicitly asks
