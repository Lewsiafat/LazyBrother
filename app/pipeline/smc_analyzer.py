"""SMC Analyzer — Smart Money Concepts detection.

Identifies Order Blocks, Fair Value Gaps, Break of Structure (BOS),
Change of Character (CHoCH), and Liquidity Sweeps.
"""

import pandas as pd

from app.models.response import SMCData, OrderBlock, FairValueGap


def _find_swing_highs_lows(
    df: pd.DataFrame, lookback: int = 5
) -> tuple[pd.Series, pd.Series]:
    """Identify swing highs and swing lows.

    A swing high occurs when a high is the highest within `lookback` candles
    on each side. A swing low is the opposite.
    """
    highs = pd.Series(False, index=df.index)
    lows = pd.Series(False, index=df.index)

    for i in range(lookback, len(df) - lookback):
        window_highs = df["high"].iloc[i - lookback : i + lookback + 1]
        window_lows = df["low"].iloc[i - lookback : i + lookback + 1]

        if df["high"].iloc[i] == window_highs.max():
            highs.iloc[i] = True
        if df["low"].iloc[i] == window_lows.min():
            lows.iloc[i] = True

    return highs, lows


def _detect_order_blocks(
    df: pd.DataFrame, swing_highs: pd.Series, swing_lows: pd.Series
) -> list[OrderBlock]:
    """Detect order blocks near swing points.

    A bullish order block is the last bearish candle before a strong bullish move.
    A bearish order block is the last bullish candle before a strong bearish move.
    """
    order_blocks: list[OrderBlock] = []

    for i in range(1, len(df) - 1):
        # Bullish OB: bearish candle followed by strong bullish candle
        if (
            df["close"].iloc[i] < df["open"].iloc[i]  # current bearish
            and df["close"].iloc[i + 1] > df["open"].iloc[i + 1]  # next bullish
            and (df["close"].iloc[i + 1] - df["open"].iloc[i + 1])
            > abs(df["close"].iloc[i] - df["open"].iloc[i]) * 1.5  # strong move
        ):
            order_blocks.append(
                OrderBlock(
                    type="bullish",
                    zone=[float(df["low"].iloc[i]), float(df["high"].iloc[i])],
                    timeframe="",  # filled by caller
                )
            )

        # Bearish OB: bullish candle followed by strong bearish candle
        if (
            i + 1 < len(df)
            and df["close"].iloc[i] > df["open"].iloc[i]  # current bullish
            and df["close"].iloc[i + 1] < df["open"].iloc[i + 1]  # next bearish
            and abs(df["close"].iloc[i + 1] - df["open"].iloc[i + 1])
            > (df["close"].iloc[i] - df["open"].iloc[i]) * 1.5
        ):
            order_blocks.append(
                OrderBlock(
                    type="bearish",
                    zone=[float(df["low"].iloc[i]), float(df["high"].iloc[i])],
                    timeframe="",
                )
            )

    # Return only the most recent order blocks (last 3 of each type)
    bullish = [ob for ob in order_blocks if ob.type == "bullish"][-3:]
    bearish = [ob for ob in order_blocks if ob.type == "bearish"][-3:]
    return bullish + bearish


def _detect_fair_value_gaps(df: pd.DataFrame) -> list[FairValueGap]:
    """Detect Fair Value Gaps (FVG).

    A bullish FVG: candle[i-1].high < candle[i+1].low (gap up).
    A bearish FVG: candle[i-1].low > candle[i+1].high (gap down).
    """
    fvgs: list[FairValueGap] = []

    for i in range(1, len(df) - 1):
        prev_high = df["high"].iloc[i - 1]
        next_low = df["low"].iloc[i + 1]
        prev_low = df["low"].iloc[i - 1]
        next_high = df["high"].iloc[i + 1]

        # Bullish FVG
        if prev_high < next_low:
            fvgs.append(
                FairValueGap(
                    type="bullish",
                    zone=[float(prev_high), float(next_low)],
                    timeframe="",
                )
            )

        # Bearish FVG
        if prev_low > next_high:
            fvgs.append(
                FairValueGap(
                    type="bearish",
                    zone=[float(next_high), float(prev_low)],
                    timeframe="",
                )
            )

    # Return only recent FVGs (last 3 of each type)
    bullish = [f for f in fvgs if f.type == "bullish"][-3:]
    bearish = [f for f in fvgs if f.type == "bearish"][-3:]
    return bullish + bearish


def _detect_structure(
    df: pd.DataFrame, swing_highs: pd.Series, swing_lows: pd.Series
) -> str | None:
    """Detect Break of Structure (BOS) or Change of Character (CHoCH).

    BOS: trend continuation — higher highs in uptrend or lower lows in downtrend.
    CHoCH: trend reversal — first lower low in uptrend or first higher high in downtrend.
    """
    high_indices = df.index[swing_highs]
    low_indices = df.index[swing_lows]

    if len(high_indices) < 2 or len(low_indices) < 2:
        return None

    # Get last two swing highs and lows
    last_sh = df.loc[high_indices[-1], "high"]
    prev_sh = df.loc[high_indices[-2], "high"]
    last_sl = df.loc[low_indices[-1], "low"]
    prev_sl = df.loc[low_indices[-2], "low"]

    # Determine structure
    if last_sh > prev_sh and last_sl > prev_sl:
        return "BOS_bullish"
    elif last_sh < prev_sh and last_sl < prev_sl:
        return "BOS_bearish"
    elif prev_sh > last_sh and prev_sl < last_sl:
        # Was making higher highs, now lower high = potential CHoCH
        return "CHoCH_bearish"
    elif prev_sh < last_sh and prev_sl > last_sl:
        # Was making lower lows, now higher low = potential CHoCH
        return "CHoCH_bullish"

    return None


def _detect_liquidity_sweeps(
    df: pd.DataFrame, swing_highs: pd.Series, swing_lows: pd.Series
) -> list[str]:
    """Detect liquidity sweeps — price briefly breaks a swing level then reverses."""
    sweeps: list[str] = []

    if len(df) < 3:
        return sweeps

    last = df.iloc[-1]
    high_indices = df.index[swing_highs]
    low_indices = df.index[swing_lows]

    # Check if recent price swept below a swing low then reversed up
    for idx in low_indices[-3:]:
        swing_low_price = df.loc[idx, "low"]
        if last["low"] < swing_low_price and last["close"] > swing_low_price:
            sweeps.append(f"sell-side sweep at {swing_low_price:.2f}")

    # Check if recent price swept above a swing high then reversed down
    for idx in high_indices[-3:]:
        swing_high_price = df.loc[idx, "high"]
        if last["high"] > swing_high_price and last["close"] < swing_high_price:
            sweeps.append(f"buy-side sweep at {swing_high_price:.2f}")

    return sweeps


def analyze_smc(df: pd.DataFrame, timeframe: str) -> SMCData:
    """Run full SMC analysis on a single timeframe's candle data.

    Args:
        df: OHLCV DataFrame.
        timeframe: Timeframe label (e.g. "15m") — attached to results.

    Returns:
        SMCData with detected order blocks, FVGs, structure, and liquidity sweeps.
    """
    if df.empty or len(df) < 12:
        return SMCData()

    swing_highs, swing_lows = _find_swing_highs_lows(df)

    # Detect components
    order_blocks = _detect_order_blocks(df, swing_highs, swing_lows)
    for ob in order_blocks:
        ob.timeframe = timeframe

    fvgs = _detect_fair_value_gaps(df)
    for fvg in fvgs:
        fvg.timeframe = timeframe

    structure = _detect_structure(df, swing_highs, swing_lows)
    liquidity_sweeps = _detect_liquidity_sweeps(df, swing_highs, swing_lows)

    return SMCData(
        order_blocks=order_blocks,
        fair_value_gaps=fvgs,
        structure=structure,
        liquidity_sweeps=liquidity_sweeps,
    )


def analyze_smc_all_timeframes(
    candles: dict[str, pd.DataFrame],
) -> dict[str, SMCData]:
    """Run SMC analysis across all timeframes.

    Returns:
        dict mapping timeframe to SMCData.
    """
    return {tf: analyze_smc(df, tf) for tf, df in candles.items()}
