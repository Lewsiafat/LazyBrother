"""LLM Synthesizer — builds prompt from analysis data, calls LLM, parses response."""

import json
import logging
from typing import Any

from app.config import settings
from app.models.response import (
    TradingAnalysis,
    EntryZone,
    StopLoss,
    TakeProfitTarget,
    IndicatorData,
    SMCData,
)
from app.providers.base import LLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.claude_provider import ClaudeProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """Factory: return the configured LLM provider."""
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "gemini":
        return GeminiProvider()
    elif provider == "claude":
        return ClaudeProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _build_prompt(
    symbol: str,
    market: str,
    mode: str,
    timeframes: list[str],
    patterns: dict[str, list[str]],
    indicators: dict[str, IndicatorData],
    smc_data: dict[str, SMCData],
) -> str:
    """Build the analysis prompt for the LLM."""

    # Serialize indicators
    indicators_text = ""
    for tf, ind in indicators.items():
        ind_dict = ind.model_dump(exclude_none=True)
        if ind_dict:
            indicators_text += f"\n  [{tf}]: {json.dumps(ind_dict)}"

    # Serialize SMC data
    smc_text = ""
    for tf, smc in smc_data.items():
        smc_dict = smc.model_dump(exclude_none=True)
        # Remove empty lists
        smc_dict = {k: v for k, v in smc_dict.items() if v}
        if smc_dict:
            smc_text += f"\n  [{tf}]: {json.dumps(smc_dict)}"

    # Serialize patterns
    patterns_text = ""
    for tf, pats in patterns.items():
        if pats:
            patterns_text += f"\n  [{tf}]: {', '.join(pats)}"

    prompt = f"""Analyze the following market data for {symbol} ({market}) in {mode} mode.
Timeframes analyzed: {', '.join(timeframes)}

## Candlestick Patterns Detected{patterns_text if patterns_text else " None"}

## Technical Indicators{indicators_text if indicators_text else " None"}

## Smart Money Concepts (SMC){smc_text if smc_text else " None"}

---

Based on the above multi-timeframe analysis, provide your trading advice as a JSON object with EXACTLY these fields:

{{
  "trading_thesis": "Brief summary of core reason for your recommendation (1-3 sentences)",
  "confidence_level": "high" | "medium" | "low",
  "confidence_reason": "Why this confidence level (1-2 sentences)",
  "direction": "long" | "short",
  "entry_zone": {{ "low": <number>, "high": <number> }},
  "stop_loss": {{ "price": <number>, "reason": "Why here (reference key levels)" }},
  "take_profit_targets": [
    {{ "label": "TP1", "price": <number>, "reason": "Based on..." }},
    {{ "label": "TP2", "price": <number>, "reason": "Based on..." }},
    {{ "label": "TP3", "price": <number>, "reason": "Based on..." }}
  ]
}}

Requirements:
- Use actual price levels from the data
- Reference specific patterns, indicators, and SMC levels in your reasoning
- Set stop-loss below/above key structural levels (order blocks, swing points)
- Take-profit targets should be based on FVGs, resistance/support, and Fibonacci levels
- Return ONLY the JSON object, no other text
"""
    return prompt


async def synthesize_analysis(
    symbol: str,
    market: str,
    mode: str,
    timeframes: list[str],
    patterns: dict[str, list[str]],
    indicators: dict[str, IndicatorData],
    smc_data: dict[str, SMCData],
) -> TradingAnalysis | None:
    """Build prompt, call LLM, parse response into TradingAnalysis.

    Returns None if the LLM call fails (caller should return raw data as fallback).
    """
    prompt = _build_prompt(
        symbol, market, mode, timeframes, patterns, indicators, smc_data
    )

    try:
        provider = get_llm_provider()
        raw_response = await provider.synthesize(prompt)

        # Parse JSON response
        data = json.loads(raw_response)

        return TradingAnalysis(
            trading_thesis=data["trading_thesis"],
            confidence_level=data["confidence_level"],
            confidence_reason=data["confidence_reason"],
            direction=data["direction"],
            entry_zone=EntryZone(**data["entry_zone"]),
            stop_loss=StopLoss(**data["stop_loss"]),
            take_profit_targets=[
                TakeProfitTarget(**tp) for tp in data["take_profit_targets"]
            ],
        )

    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s", e)
        return None
    except KeyError as e:
        logger.error("Missing expected field in LLM response: %s", e)
        return None
    except Exception as e:
        logger.error("LLM synthesis failed: %s", e)
        return None
