"""File-based snapshot storage (JSON persistence)."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from app.models.snapshot import AnalysisSnapshot, SnapshotCreate

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SNAPSHOTS_FILE = _DATA_DIR / "snapshots.json"


def _ensure_file() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _SNAPSHOTS_FILE.exists():
        _SNAPSHOTS_FILE.write_text("[]", encoding="utf-8")


def _load_all() -> list[dict]:
    _ensure_file()
    try:
        data = json.loads(_SNAPSHOTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load snapshots file: %s", e)
        return []


def _save_all(items: list[dict]) -> None:
    _ensure_file()
    _SNAPSHOTS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def list_snapshots() -> list[AnalysisSnapshot]:
    return [AnalysisSnapshot(**item) for item in _load_all()]


def create_snapshot(req: SnapshotCreate) -> AnalysisSnapshot:
    snapshot = AnalysisSnapshot(
        id=str(uuid.uuid4()),
        saved_at=datetime.now(),
        label=req.label,
        data=req.data,
    )
    items = _load_all()
    items.append(snapshot.model_dump(mode="json"))
    _save_all(items)
    logger.info(
        "Saved snapshot %s — %s %s @ %s",
        snapshot.id, snapshot.data.symbol, snapshot.data.mode,
        snapshot.data.timestamp,
    )
    return snapshot


def delete_snapshot(snapshot_id: str) -> bool:
    items = _load_all()
    new_items = [item for item in items if item.get("id") != snapshot_id]
    if len(new_items) == len(items):
        return False
    _save_all(new_items)
    logger.info("Deleted snapshot %s", snapshot_id)
    return True
