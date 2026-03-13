"""Pipeline orchestrator — runs the full analysis pipeline."""

import logging
from datetime import datetime, timezone

from app.models.request import AnalysisRequest, AnalysisMode, TIMEFRAME_PRESETS
from app.models.response import (
    AnalysisResponse,
    AnalysisDetails,
    IndicatorData,
    SMCData,
)
from app.pipeline.data_fetcher import fetch_all_timeframes
from app.pipeline.pattern_analyzer import analyze_patterns
from app.pipeline.indicator_calc import calculate_all_timeframes
from app.pipeline.smc_analyzer import analyze_smc_all_timeframes
from app.pipeline.llm_synthesizer import synthesize_analysis
from app.storage.prompt_store import get_prompts_by_ids

logger = logging.getLogger(__name__)


async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """Run the full analysis pipeline.

    Steps:
        1. Fetch candle data for all timeframes
        2. Detect candlestick patterns
        3. Calculate technical indicators
        4. Run SMC analysis
        5. Synthesize with LLM (fallback: return raw data)

    Args:
        request: The analysis request with symbol, mode.

    Returns:
        AnalysisResponse with trading advice and raw details.
    """
    timeframes = TIMEFRAME_PRESETS[request.mode]

    # Step 1: Fetch candle data
    logger.info(
        "Fetching candles for %s — mode: %s",
        request.symbol, request.mode.value,
    )
    candles = await fetch_all_timeframes(
        request.symbol, request.mode
    )

    # Step 2: Detect candlestick patterns
    logger.info("Detecting candlestick patterns...")
    patterns = analyze_patterns(candles)

    # Flatten patterns across timeframes for response
    all_patterns = []
    for tf_patterns in patterns.values():
        all_patterns.extend(tf_patterns)
    all_patterns = list(set(all_patterns))

    # Step 3: Calculate technical indicators
    logger.info("Calculating technical indicators...")
    indicators_by_tf = calculate_all_timeframes(candles)

    # Use the highest timeframe indicators as the primary display values
    primary_tf = timeframes[-1]  # e.g. "15m" for scalping, "4h" for swing
    primary_indicators = indicators_by_tf.get(primary_tf, IndicatorData())

    # Step 4: SMC analysis
    logger.info("Running SMC analysis...")
    smc_by_tf = analyze_smc_all_timeframes(candles)

    # Merge SMC data across timeframes
    merged_smc = _merge_smc(smc_by_tf)

    # Step 5: LLM synthesis
    logger.info("Synthesizing analysis with LLM...")

    # Extract current price from the lowest timeframe's last candle
    current_price = 0.0
    if candles:
        # Lowest timeframe is the first one in the preset list (e.g., "1m" for scalping)
        lowest_tf = timeframes[0]
        if lowest_tf in candles and not candles[lowest_tf].empty:
            current_price = float(candles[lowest_tf].iloc[-1]["close"])

    # Build custom instructions from saved snippets + inline prompt
    custom_parts: list[str] = []
    if request.prompt_ids:
        snippets = get_prompts_by_ids(request.prompt_ids)
        for s in snippets:
            custom_parts.append(f"### {s.name}\n{s.content}")
    if request.custom_prompt:
        custom_parts.append(request.custom_prompt)
    custom_instructions = "\n\n".join(custom_parts) if custom_parts else None

    trading_analysis = await synthesize_analysis(
        symbol=request.symbol,
        market="crypto",
        mode=request.mode.value,
        timeframes=timeframes,
        patterns=patterns,
        indicators=indicators_by_tf,
        smc_data=smc_by_tf,
        custom_instructions=custom_instructions,
    )

    if trading_analysis is None:
        logger.warning("LLM synthesis failed — returning raw data only")

    # Build response
    return AnalysisResponse(
        symbol=request.symbol,
        market="crypto",
        mode=request.mode.value,
        timestamp=datetime.now(timezone.utc),
        current_price=current_price,
        analysis=trading_analysis,
        details=AnalysisDetails(
            patterns_detected=all_patterns,
            indicators=primary_indicators,
            smc=merged_smc,
            timeframes_analyzed=timeframes,
        ),
    )


def _merge_smc(smc_by_tf: dict[str, SMCData]) -> SMCData:
    """Merge SMC data from all timeframes into a single SMCData."""
    all_order_blocks = []
    all_fvgs = []
    all_sweeps = []
    structure = None

    for tf, smc in smc_by_tf.items():
        all_order_blocks.extend(smc.order_blocks)
        all_fvgs.extend(smc.fair_value_gaps)
        all_sweeps.extend(smc.liquidity_sweeps)
        # Use highest timeframe's structure as primary
        if smc.structure:
            structure = smc.structure

    return SMCData(
        order_blocks=all_order_blocks,
        fair_value_gaps=all_fvgs,
        structure=structure,
        liquidity_sweeps=all_sweeps,
    )
