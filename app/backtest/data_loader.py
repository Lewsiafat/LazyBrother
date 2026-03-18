"""Historical candle loader for backtesting — pulls full date-range data from Binance."""

import logging
import pandas as pd
from binance.client import Client as BinanceClient

from app.config import settings

logger = logging.getLogger(__name__)

BINANCE_INTERVALS = {
    "1m": BinanceClient.KLINE_INTERVAL_1MINUTE,
    "5m": BinanceClient.KLINE_INTERVAL_5MINUTE,
    "15m": BinanceClient.KLINE_INTERVAL_15MINUTE,
    "1h": BinanceClient.KLINE_INTERVAL_1HOUR,
    "4h": BinanceClient.KLINE_INTERVAL_4HOUR,
}


def _klines_to_df(klines: list) -> pd.DataFrame:
    """Convert raw Binance kline list to a typed OHLCV DataFrame."""
    if not klines:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = pd.DataFrame(
        klines,
        columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df[["open", "high", "low", "close", "volume"]]


def load_historical_candles(
    symbol: str,
    timeframes: list[str],
    start_date: str,
    end_date: str,
) -> dict[str, pd.DataFrame]:
    """Load historical OHLCV data for all timeframes across a date range.

    Args:
        symbol: e.g. "BTCUSDT"
        timeframes: list of interval strings, e.g. ["1m", "5m", "15m"]
        start_date: "YYYY-MM-DD" or Binance date string
        end_date: "YYYY-MM-DD" or Binance date string

    Returns:
        dict mapping timeframe → full historical DataFrame
    """
    client = BinanceClient(
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret,
    )

    result: dict[str, pd.DataFrame] = {}
    for tf in timeframes:
        binance_interval = BINANCE_INTERVALS.get(tf)
        if not binance_interval:
            logger.warning("Unsupported interval: %s — skipping", tf)
            continue

        logger.info("Loading %s %s candles (%s → %s)...", symbol, tf, start_date, end_date)
        try:
            klines = client.get_historical_klines(
                symbol=symbol,
                interval=binance_interval,
                start_str=start_date,
                end_str=end_date,
            )
            df = _klines_to_df(klines)
            logger.info("  → %d candles loaded", len(df))
            result[tf] = df
        except Exception as e:
            logger.error("Failed to load %s %s: %s", symbol, tf, e)
            result[tf] = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    return result
