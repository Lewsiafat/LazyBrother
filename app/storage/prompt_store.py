"""File-based prompt snippet storage (JSON persistence)."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.prompt import PromptSnippet, PromptSnippetCreate, PromptSnippetUpdate

logger = logging.getLogger(__name__)

# Default storage location
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_PROMPTS_FILE = _DATA_DIR / "prompts.json"


def _ensure_file() -> None:
    """Ensure the data directory and prompts file exist."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _PROMPTS_FILE.exists():
        _PROMPTS_FILE.write_text("[]", encoding="utf-8")


def _load_all() -> list[dict]:
    """Load all prompt snippets from disk."""
    _ensure_file()
    try:
        data = json.loads(_PROMPTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load prompts file: %s", e)
        return []


def _save_all(items: list[dict]) -> None:
    """Persist all prompt snippets to disk."""
    _ensure_file()
    _PROMPTS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def list_prompts() -> list[PromptSnippet]:
    """Return all stored prompt snippets."""
    return [PromptSnippet(**item) for item in _load_all()]


def get_prompt(prompt_id: str) -> Optional[PromptSnippet]:
    """Return a single prompt by ID, or None if not found."""
    for item in _load_all():
        if item.get("id") == prompt_id:
            return PromptSnippet(**item)
    return None


def get_prompts_by_ids(prompt_ids: list[str]) -> list[PromptSnippet]:
    """Return prompts matching the given IDs (preserves order)."""
    all_items = {item["id"]: item for item in _load_all()}
    results = []
    for pid in prompt_ids:
        if pid in all_items:
            results.append(PromptSnippet(**all_items[pid]))
    return results


def create_prompt(data: PromptSnippetCreate) -> PromptSnippet:
    """Create and persist a new prompt snippet."""
    now = datetime.now()
    snippet = PromptSnippet(
        id=str(uuid.uuid4()),
        name=data.name,
        content=data.content,
        category=data.category,
        is_active=data.is_active,
        created_at=now,
        updated_at=now,
    )
    items = _load_all()
    items.append(snippet.model_dump(mode="json"))
    _save_all(items)
    logger.info("Created prompt snippet: %s (%s)", snippet.name, snippet.id)
    return snippet


def update_prompt(prompt_id: str, data: PromptSnippetUpdate) -> Optional[PromptSnippet]:
    """Update an existing prompt snippet. Returns None if not found."""
    items = _load_all()
    for i, item in enumerate(items):
        if item.get("id") == prompt_id:
            update_fields = data.model_dump(exclude_none=True)
            if update_fields:
                update_fields["updated_at"] = datetime.now().isoformat()
                items[i] = {**item, **update_fields}
                _save_all(items)
                logger.info("Updated prompt snippet: %s", prompt_id)
            return PromptSnippet(**items[i])
    return None


def delete_prompt(prompt_id: str) -> bool:
    """Delete a prompt snippet by ID. Returns True if deleted."""
    items = _load_all()
    new_items = [item for item in items if item.get("id") != prompt_id]
    if len(new_items) == len(items):
        return False
    _save_all(new_items)
    logger.info("Deleted prompt snippet: %s", prompt_id)
    return True
