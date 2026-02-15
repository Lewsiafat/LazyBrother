"""Pattern analyzer — detects candlestick patterns from OHLCV data."""

import pandas as pd
import pandas_ta as ta


def _detect_single_candle_patterns(df: pd.DataFrame) -> list[str]:
    """Detect single-candle patterns."""
    patterns = []
    if df.empty or len(df) < 2:
        return patterns

    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    upper_shadow = last["high"] - max(last["close"], last["open"])
    lower_shadow = min(last["close"], last["open"]) - last["low"]
    total_range = last["high"] - last["low"]

    if total_range == 0:
        return patterns

    body_ratio = body / total_range

    # Doji — very small body relative to range
    if body_ratio < 0.1:
        patterns.append("doji")

    # Hammer — small body at top, long lower shadow
    if (
        body_ratio < 0.35
        and lower_shadow > body * 2
        and upper_shadow < body * 0.5
    ):
        patterns.append("hammer")

    # Inverted Hammer
    if (
        body_ratio < 0.35
        and upper_shadow > body * 2
        and lower_shadow < body * 0.5
    ):
        patterns.append("inverted_hammer")

    # Shooting Star (bearish) — like inverted hammer but in uptrend
    if (
        body_ratio < 0.35
        and upper_shadow > body * 2
        and lower_shadow < body * 0.5
        and last["close"] < last["open"]  # bearish candle
    ):
        patterns.append("shooting_star")

    # Spinning Top — small body, shadows on both sides
    if body_ratio < 0.3 and upper_shadow > body and lower_shadow > body:
        patterns.append("spinning_top")

    return patterns


def _detect_dual_candle_patterns(df: pd.DataFrame) -> list[str]:
    """Detect two-candle patterns."""
    patterns = []
    if len(df) < 2:
        return patterns

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Bullish Engulfing
    if (
        prev["close"] < prev["open"]  # prev bearish
        and last["close"] > last["open"]  # current bullish
        and last["open"] <= prev["close"]  # opens below prev close
        and last["close"] >= prev["open"]  # closes above prev open
    ):
        patterns.append("bullish_engulfing")

    # Bearish Engulfing
    if (
        prev["close"] > prev["open"]  # prev bullish
        and last["close"] < last["open"]  # current bearish
        and last["open"] >= prev["close"]  # opens above prev close
        and last["close"] <= prev["open"]  # closes below prev open
    ):
        patterns.append("bearish_engulfing")

    # Piercing Line (bullish)
    if (
        prev["close"] < prev["open"]  # prev bearish
        and last["close"] > last["open"]  # current bullish
        and last["open"] < prev["low"]  # opens below prev low
        and last["close"] > (prev["open"] + prev["close"]) / 2  # closes above midpoint
    ):
        patterns.append("piercing_line")

    # Dark Cloud Cover (bearish)
    if (
        prev["close"] > prev["open"]  # prev bullish
        and last["close"] < last["open"]  # current bearish
        and last["open"] > prev["high"]  # opens above prev high
        and last["close"] < (prev["open"] + prev["close"]) / 2  # closes below midpoint
    ):
        patterns.append("dark_cloud_cover")

    return patterns


def _detect_triple_candle_patterns(df: pd.DataFrame) -> list[str]:
    """Detect three-candle patterns."""
    patterns = []
    if len(df) < 3:
        return patterns

    c3 = df.iloc[-1]  # most recent
    c2 = df.iloc[-2]
    c1 = df.iloc[-3]

    c1_body = abs(c1["close"] - c1["open"])
    c2_body = abs(c2["close"] - c2["open"])
    c3_body = abs(c3["close"] - c3["open"])
    c1_range = c1["high"] - c1["low"]

    # Morning Star (bullish reversal)
    if (
        c1["close"] < c1["open"]  # first bearish
        and c2_body < c1_body * 0.3  # second small body (star)
        and c3["close"] > c3["open"]  # third bullish
        and c3["close"] > (c1["open"] + c1["close"]) / 2  # closes above midpoint of first
    ):
        patterns.append("morning_star")

    # Evening Star (bearish reversal)
    if (
        c1["close"] > c1["open"]  # first bullish
        and c2_body < c1_body * 0.3  # second small body
        and c3["close"] < c3["open"]  # third bearish
        and c3["close"] < (c1["open"] + c1["close"]) / 2  # closes below midpoint
    ):
        patterns.append("evening_star")

    # Three White Soldiers (bullish)
    if (
        c1["close"] > c1["open"]
        and c2["close"] > c2["open"]
        and c3["close"] > c3["open"]
        and c2["close"] > c1["close"]
        and c3["close"] > c2["close"]
    ):
        patterns.append("three_white_soldiers")

    # Three Black Crows (bearish)
    if (
        c1["close"] < c1["open"]
        and c2["close"] < c2["open"]
        and c3["close"] < c3["open"]
        and c2["close"] < c1["close"]
        and c3["close"] < c2["close"]
    ):
        patterns.append("three_black_crows")

    return patterns


def analyze_patterns(candles: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """Detect candlestick patterns across all timeframes.

    Args:
        candles: dict mapping timeframe to OHLCV DataFrame.

    Returns:
        dict mapping timeframe to list of detected pattern names.
    """
    results: dict[str, list[str]] = {}

    for tf, df in candles.items():
        if df.empty:
            results[tf] = []
            continue

        patterns: list[str] = []
        patterns.extend(_detect_single_candle_patterns(df))
        patterns.extend(_detect_dual_candle_patterns(df))
        patterns.extend(_detect_triple_candle_patterns(df))

        # Deduplicate
        results[tf] = list(set(patterns))

    return results
