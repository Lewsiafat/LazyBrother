"""Data fetcher module — pulls OHLCV candles from Binance."""

from abc import ABC, abstractmethod
import logging
import pandas as pd
from binance.client import Client as BinanceClient

from app.config import settings
from app.models.request import AnalysisMode, TIMEFRAME_PRESETS

logger = logging.getLogger(__name__)

# Binance interval mapping
BINANCE_INTERVALS = {
    "1m": BinanceClient.KLINE_INTERVAL_1MINUTE,
    "5m": BinanceClient.KLINE_INTERVAL_5MINUTE,
    "15m": BinanceClient.KLINE_INTERVAL_15MINUTE,
    "1h": BinanceClient.KLINE_INTERVAL_1HOUR,
    "4h": BinanceClient.KLINE_INTERVAL_4HOUR,
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
        self._cached_symbols: list[str] = []

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

    async def get_all_symbols(self) -> list[str]:
        """Fetch all available USDT symbols from Binance."""
        if self._cached_symbols:
            return self._cached_symbols

        try:
            info = self.client.get_exchange_info()
            symbols = [
                s["symbol"] for s in info["symbols"]
                if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"
            ]
            self._cached_symbols = sorted(symbols)
            return self._cached_symbols
        except Exception as e:
            logger.error("Failed to fetch symbols from Binance: %s", e)
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]


def get_fetcher() -> BinanceFetcher:
    """Factory: return the Binance fetcher."""
    return BinanceFetcher()


async def fetch_all_timeframes(
    symbol: str, mode: AnalysisMode
) -> dict[str, pd.DataFrame]:
    """Fetch candle data for all timeframes in the given mode.

    Returns:
        dict mapping timeframe string (e.g. "1m") to its DataFrame.
    """
    fetcher = get_fetcher()
    timeframes = TIMEFRAME_PRESETS[mode]

    results: dict[str, pd.DataFrame] = {}
    for tf in timeframes:
        limit = CANDLE_LIMITS.get(tf, 200)
        results[tf] = await fetcher.fetch_candles(symbol, tf, limit)

    return results
