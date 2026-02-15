"""Data fetcher module — pulls OHLCV candles from Binance and yFinance."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from binance.client import Client as BinanceClient

from app.config import settings
from app.models.request import MarketType, AnalysisMode, TIMEFRAME_PRESETS


# Binance interval mapping
BINANCE_INTERVALS = {
    "1m": BinanceClient.KLINE_INTERVAL_1MINUTE,
    "5m": BinanceClient.KLINE_INTERVAL_5MINUTE,
    "15m": BinanceClient.KLINE_INTERVAL_15MINUTE,
    "1h": BinanceClient.KLINE_INTERVAL_1HOUR,
    "4h": BinanceClient.KLINE_INTERVAL_4HOUR,
}

# yFinance interval mapping
YFINANCE_INTERVALS = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "1h",  # yfinance doesn't support 4h directly; we'll resample
}

# How many candles to fetch per timeframe
CANDLE_LIMITS = {
    "1m": 200,
    "5m": 200,
    "15m": 200,
    "1h": 200,
    "4h": 200,
}


class BaseFetcher(ABC):
    """Abstract base for data fetchers."""

    @abstractmethod
    async def fetch_candles(
        self, symbol: str, interval: str, limit: int = 200
    ) -> pd.DataFrame:
        """Fetch OHLCV candle data.

        Returns a DataFrame with columns: open, high, low, close, volume
        and a DatetimeIndex.
        """
        ...


class BinanceFetcher(BaseFetcher):
    """Fetches crypto candle data from Binance."""

    def __init__(self) -> None:
        self.client = BinanceClient(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
        )

    async def fetch_candles(
        self, symbol: str, interval: str, limit: int = 200
    ) -> pd.DataFrame:
        binance_interval = BINANCE_INTERVALS.get(interval)
        if not binance_interval:
            raise ValueError(f"Unsupported interval for Binance: {interval}")

        klines = self.client.get_klines(
            symbol=symbol, interval=binance_interval, limit=limit
        )

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


class YFinanceFetcher(BaseFetcher):
    """Fetches stock candle data from Yahoo Finance."""

    async def fetch_candles(
        self, symbol: str, interval: str, limit: int = 200
    ) -> pd.DataFrame:
        yf_interval = YFINANCE_INTERVALS.get(interval)
        if not yf_interval:
            raise ValueError(f"Unsupported interval for yFinance: {interval}")

        # Determine period based on interval
        period_map = {
            "1m": "1d",
            "5m": "5d",
            "15m": "5d",
            "1h": "1mo",
            "4h": "3mo",
        }
        period = period_map.get(interval, "1mo")

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=yf_interval)

        if df.empty:
            raise ValueError(f"No data returned for symbol: {symbol}")

        # Normalize column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        # Resample to 4h if needed
        if interval == "4h":
            df = df.resample("4h").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }).dropna()

        # Keep only last `limit` candles
        df = df.tail(limit)

        return df[["open", "high", "low", "close", "volume"]]


def get_fetcher(market: MarketType) -> BaseFetcher:
    """Factory: return the appropriate fetcher for the market type."""
    if market == MarketType.CRYPTO:
        return BinanceFetcher()
    elif market == MarketType.STOCK:
        return YFinanceFetcher()
    else:
        raise ValueError(f"Unsupported market type: {market}")


async def fetch_all_timeframes(
    symbol: str, market: MarketType, mode: AnalysisMode
) -> dict[str, pd.DataFrame]:
    """Fetch candle data for all timeframes in the given mode.

    Returns:
        dict mapping timeframe string (e.g. "1m") to its DataFrame.
    """
    fetcher = get_fetcher(market)
    timeframes = TIMEFRAME_PRESETS[mode]

    results: dict[str, pd.DataFrame] = {}
    for tf in timeframes:
        limit = CANDLE_LIMITS.get(tf, 200)
        results[tf] = await fetcher.fetch_candles(symbol, tf, limit)

    return results
