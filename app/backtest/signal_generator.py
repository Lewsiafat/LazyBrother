"""Rule-based signal generator — scores market conditions without LLM.

Scoring uses patterns, indicators, and SMC data to produce a directional bias.
Positive score → long candidate; negative score → short candidate.
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.models.response import IndicatorData, SMCData

# ── Pattern classification ──────────────────────────────────────────────────

BULLISH_PATTERNS = {
    "hammer",
    "inverted_hammer",
    "bullish_engulfing",
    "piercing_line",
    "morning_star",
    "three_white_soldiers",
}

BEARISH_PATTERNS = {
    "shooting_star",
    "bearish_engulfing",
    "dark_cloud_cover",
    "evening_star",
    "three_black_crows",
}

# ── Signal dataclass ─────────────────────────────────────────────────────────

@dataclass
class TradeSignal:
    direction: str       # "long" or "short"
    entry_low: float
    entry_high: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    score: float
    signal_time: datetime


# ── Scoring logic ────────────────────────────────────────────────────────────

def _score_indicators(indicators: IndicatorData, current_price: float) -> float:
    score = 0.0

    # RSI
    if indicators.rsi_14 is not None:
        rsi = indicators.rsi_14
        if rsi < 30:
            score += 2.0
        elif rsi < 40:
            score += 1.0
        elif rsi > 70:
            score -= 2.0
        elif rsi > 60:
            score -= 1.0

    # MACD histogram direction
    if indicators.macd is not None:
        hist = indicators.macd.histogram
        if hist > 0:
            score += 1.0
        elif hist < 0:
            score -= 1.0

    # Price vs SMA20
    if indicators.sma_20 is not None:
        if current_price > indicators.sma_20:
            score += 0.5
        else:
            score -= 0.5

    # Price vs EMA50
    if indicators.ema_50 is not None:
        if current_price > indicators.ema_50:
            score += 0.5
        else:
            score -= 0.5

    # Price relative to Bollinger Bands
    if indicators.bollinger is not None:
        bb = indicators.bollinger
        if current_price <= bb.lower:
            score += 1.5   # oversold — near lower band
        elif current_price >= bb.upper:
            score -= 1.5   # overbought — near upper band

    return score


def _score_patterns(patterns_by_tf: dict[str, list[str]], lowest_tf: str) -> float:
    """Score based on patterns detected — weight lowest TF patterns more."""
    score = 0.0
    for tf, patterns in patterns_by_tf.items():
        weight = 1.5 if tf == lowest_tf else 0.8
        for p in patterns:
            if p in BULLISH_PATTERNS:
                score += weight
            elif p in BEARISH_PATTERNS:
                score -= weight
    return score


def _score_smc(smc_by_tf: dict[str, SMCData], current_price: float) -> float:
    score = 0.0
    for tf, smc in smc_by_tf.items():
        # Market structure
        if smc.structure == "BOS_bullish":
            score += 2.0
        elif smc.structure == "CHoCH_bullish":
            score += 1.5
        elif smc.structure == "BOS_bearish":
            score -= 2.0
        elif smc.structure == "CHoCH_bearish":
            score -= 1.5

        # Near order block
        proximity = current_price * 0.005  # within 0.5%
        for ob in smc.order_blocks:
            ob_low, ob_high = ob.zone[0], ob.zone[1]
            if ob_high + proximity >= current_price >= ob_low - proximity:
                if ob.type == "bullish":
                    score += 1.5
                else:
                    score -= 1.5

        # Bullish FVG below price (support / unfilled gap)
        for fvg in smc.fair_value_gaps:
            fvg_low, fvg_high = fvg.zone[0], fvg.zone[1]
            if fvg.type == "bullish" and fvg_high < current_price:
                score += 0.8
            elif fvg.type == "bearish" and fvg_low > current_price:
                score -= 0.8

        # Liquidity sweeps
        for sweep in smc.liquidity_sweeps:
            if "sell-side" in sweep:
                score += 1.0   # sell-side swept → bullish reversal potential
            elif "buy-side" in sweep:
                score -= 1.0

    return score


def _get_swing_extremes(df: pd.DataFrame, lookback: int = 5) -> tuple[list[float], list[float]]:
    """Return recent swing lows and highs from a DataFrame."""
    swing_lows: list[float] = []
    swing_highs: list[float] = []

    for i in range(lookback, len(df) - lookback):
        window = df["low"].iloc[i - lookback: i + lookback + 1]
        if df["low"].iloc[i] == window.min():
            swing_lows.append(float(df["low"].iloc[i]))

        window_h = df["high"].iloc[i - lookback: i + lookback + 1]
        if df["high"].iloc[i] == window_h.max():
            swing_highs.append(float(df["high"].iloc[i]))

    return swing_lows, swing_highs


def generate_signal(
    patterns_by_tf: dict[str, list[str]],
    indicators_by_tf: dict[str, IndicatorData],
    smc_by_tf: dict[str, SMCData],
    timeframes: list[str],
    candles_by_tf: dict[str, pd.DataFrame],
    signal_time: datetime,
    min_score: float = 3.0,
) -> TradeSignal | None:
    """Score market conditions and return a TradeSignal if threshold is met.

    Args:
        patterns_by_tf: output of analyze_patterns()
        indicators_by_tf: output of calculate_all_timeframes()
        smc_by_tf: output of analyze_smc_all_timeframes()
        timeframes: ordered list of TFs (lowest first, highest last)
        candles_by_tf: raw OHLCV windows for each TF
        signal_time: timestamp of the analysis point
        min_score: absolute score threshold to generate a signal

    Returns:
        TradeSignal or None if no clear bias.
    """
    lowest_tf = timeframes[0]
    primary_tf = timeframes[-1]

    # Current price = last close of lowest TF
    exec_df = candles_by_tf.get(lowest_tf)
    if exec_df is None or exec_df.empty:
        return None
    current_price = float(exec_df.iloc[-1]["close"])

    # Primary TF indicators drive the main bias
    primary_indicators = indicators_by_tf.get(primary_tf, IndicatorData())

    score = 0.0
    score += _score_indicators(primary_indicators, current_price)
    score += _score_patterns(patterns_by_tf, lowest_tf)
    score += _score_smc(smc_by_tf, current_price)

    if abs(score) < min_score:
        return None

    direction = "long" if score > 0 else "short"

    # Entry zone: ±0.15% around current price
    spread = current_price * 0.0015
    entry_low = current_price - spread
    entry_high = current_price + spread

    # Stop loss: nearest swing extreme beyond the entry, fallback to fixed %
    exec_window = candles_by_tf.get(lowest_tf, exec_df)
    swing_lows, swing_highs = _get_swing_extremes(exec_window)

    if direction == "long":
        # SL below recent swing low
        candidates = [sl for sl in swing_lows if sl < current_price]
        if candidates:
            stop_loss = max(candidates[-3:]) if len(candidates) >= 3 else candidates[-1]
            stop_loss = min(stop_loss, current_price * 0.985)  # cap at 1.5% away
        else:
            stop_loss = current_price * 0.985
        risk = current_price - stop_loss
        tp1 = current_price + risk * 1.0
        tp2 = current_price + risk * 2.0
        tp3 = current_price + risk * 3.0
    else:
        # SL above recent swing high
        candidates = [sh for sh in swing_highs if sh > current_price]
        if candidates:
            stop_loss = min(candidates[:3]) if len(candidates) >= 3 else candidates[0]
            stop_loss = max(stop_loss, current_price * 1.015)  # cap at 1.5% away
        else:
            stop_loss = current_price * 1.015
        risk = stop_loss - current_price
        tp1 = current_price - risk * 1.0
        tp2 = current_price - risk * 2.0
        tp3 = current_price - risk * 3.0

    return TradeSignal(
        direction=direction,
        entry_low=entry_low,
        entry_high=entry_high,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        score=round(score, 2),
        signal_time=signal_time,
    )
