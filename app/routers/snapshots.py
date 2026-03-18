"""Snapshots router — save and retrieve tagged analysis results."""

from fastapi import APIRouter, HTTPException

from app.models.snapshot import AnalysisSnapshot, SnapshotCreate
from app.storage.snapshot_store import list_snapshots, create_snapshot, delete_snapshot

router = APIRouter(prefix="/api/v1/snapshots", tags=["snapshots"])


@router.get("", response_model=list[AnalysisSnapshot])
async def list_snapshots_endpoint() -> list[AnalysisSnapshot]:
    """Return all saved analysis snapshots."""
    return list_snapshots()


@router.post("", response_model=AnalysisSnapshot, status_code=201)
async def create_snapshot_endpoint(req: SnapshotCreate) -> AnalysisSnapshot:
    """Save an analysis result as a backtest snapshot."""
    try:
        return create_snapshot(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{snapshot_id}", status_code=200)
async def delete_snapshot_endpoint(snapshot_id: str) -> dict:
    """Delete a snapshot by ID."""
    if not delete_snapshot(snapshot_id):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"deleted": snapshot_id}
