"""Analysis router — API endpoints for chart analysis."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.request import AnalysisRequest
from app.models.response import AnalysisResponse
from app.pipeline.orchestrator import analyze
from app.pipeline.data_fetcher import get_fetcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.get("/symbols", response_model=list[str])
async def get_symbols_endpoint() -> list[str]:
    """Get all available USDT trading symbols from Binance."""
    try:
        fetcher = get_fetcher()
        symbols = await fetcher.get_all_symbols()
        return symbols
    except Exception as e:
        logger.error("Failed to fetch symbols: %s", e)
        raise HTTPException(status_code=503, detail="Failed to fetch symbols from Binance")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_endpoint(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze candlestick data and return trading advice.

    Accepts a symbol, market type, and analysis mode.
    Returns structured trading advice with supporting details.
    """
    try:
        result = await analyze(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="Data source timed out. Please try again.",
        )
    except Exception as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Analysis failed. Please try again later.",
        )


@router.get("/health")
async def health_check() -> dict:
    """Service health check."""
    return {"status": "ok", "service": "LazyBrother"}
