"""Indicator calculator — computes classical technical indicators."""

import pandas as pd
import pandas_ta as ta

from app.models.response import IndicatorData, MACDData, BollingerData


def calculate_indicators(df: pd.DataFrame) -> IndicatorData:
    """Calculate technical indicators from OHLCV data.

    Computes RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(20), EMA(50)
    on the most recent candle data.

    Args:
        df: OHLCV DataFrame with at least 50 rows for reliable results.

    Returns:
        IndicatorData with the latest indicator values.
    """
    if df.empty or len(df) < 14:
        return IndicatorData()

    result = IndicatorData()

    # RSI(14)
    rsi = ta.rsi(df["close"], length=14)
    if rsi is not None and not rsi.empty:
        result.rsi_14 = round(float(rsi.iloc[-1]), 2)

    # MACD(12, 26, 9)
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        cols = macd_df.columns
        macd_val = float(macd_df[cols[0]].iloc[-1])
        signal_val = float(macd_df[cols[1]].iloc[-1])
        hist_val = float(macd_df[cols[2]].iloc[-1])
        result.macd = MACDData(
            value=round(macd_val, 2),
            signal=round(signal_val, 2),
            histogram=round(hist_val, 2),
        )

    # Bollinger Bands(20, 2)
    bbands = ta.bbands(df["close"], length=20, std=2)
    if bbands is not None and not bbands.empty:
        cols = bbands.columns
        result.bollinger = BollingerData(
            lower=round(float(bbands[cols[0]].iloc[-1]), 2),
            middle=round(float(bbands[cols[1]].iloc[-1]), 2),
            upper=round(float(bbands[cols[2]].iloc[-1]), 2),
        )

    # SMA(20)
    sma = ta.sma(df["close"], length=20)
    if sma is not None and not sma.empty:
        result.sma_20 = round(float(sma.iloc[-1]), 2)

    # EMA(50)
    if len(df) >= 50:
        ema = ta.ema(df["close"], length=50)
        if ema is not None and not ema.empty:
            result.ema_50 = round(float(ema.iloc[-1]), 2)

    return result


def calculate_all_timeframes(
    candles: dict[str, pd.DataFrame],
) -> dict[str, IndicatorData]:
    """Calculate indicators for all timeframes.

    Args:
        candles: dict mapping timeframe to OHLCV DataFrame.

    Returns:
        dict mapping timeframe to IndicatorData.
    """
    return {tf: calculate_indicators(df) for tf, df in candles.items()}
