"""Request models for the analysis API."""

from enum import Enum
from pydantic import BaseModel, Field


class AnalysisMode(str, Enum):
    """Analysis timeframe modes."""
    SCALPING = "scalping"  # 1m, 5m, 15m
    SWING = "swing"        # 15m, 1h, 4h


# Timeframe presets for each mode
TIMEFRAME_PRESETS = {
    AnalysisMode.SCALPING: ["1m", "5m", "15m"],
    AnalysisMode.SWING: ["15m", "1h", "4h"],
}


class AnalysisRequest(BaseModel):
    """Request body for the /api/v1/analyze endpoint."""

    symbol: str = Field(
        ...,
        description="Trading symbol, e.g. 'BTCUSDT', 'ETHUSDT'",
        examples=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    )
    mode: AnalysisMode = Field(
        ...,
        description="Analysis mode: 'scalping' (1m/5m/15m) or 'swing' (15m/1h/4h)",
    )
    custom_prompt: str | None = Field(
        None,
        description="Optional custom instructions to append to the LLM prompt",
    )
    prompt_ids: list[str] | None = Field(
        None,
        description="Optional list of saved prompt snippet IDs to include",
    )
