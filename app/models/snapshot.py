"""Snapshot models — persisted analysis results for backtesting."""

from datetime import datetime
from pydantic import BaseModel, Field

from app.models.response import AnalysisResponse


class SnapshotCreate(BaseModel):
    """Request body to save an analysis snapshot."""
    label: str | None = Field(None, description="Optional user note")
    data: AnalysisResponse


class AnalysisSnapshot(BaseModel):
    """A saved analysis result tagged for later backtesting."""
    id: str
    saved_at: datetime
    label: str | None = None
    data: AnalysisResponse
