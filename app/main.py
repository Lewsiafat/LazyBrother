"""LazyBrother — FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analysis import router as analysis_router
from app.routers.prompts import router as prompts_router
from app.routers.snapshots import router as snapshots_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="LazyBrother",
    description=(
        "Candlestick chart analysis service providing structured "
        "investment advice for cryptocurrency and stocks."
    ),
    version="0.5.0",
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analysis_router)
app.include_router(prompts_router)
app.include_router(snapshots_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint — service info."""
    return {
        "service": "LazyBrother",
        "version": "0.5.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
