"""Backtest runner — orchestrates full walk-forward backtesting."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.models.request import AnalysisMode, TIMEFRAME_PRESETS
from app.models.snapshot import AnalysisSnapshot
from app.pipeline.pattern_analyzer import analyze_patterns
from app.pipeline.indicator_calc import calculate_all_timeframes
from app.pipeline.smc_analyzer import analyze_smc_all_timeframes
from app.pipeline.llm_synthesizer import _build_prompt
from app.backtest.data_loader import load_historical_candles
from app.backtest.signal_generator import generate_signal, TradeSignal
from app.backtest.simulator import simulate_trade, TradeResult
from app.backtest.evaluator import evaluate_trades, BacktestResult

# Minutes per timeframe — used to compute a forward window end date
_TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240}


@dataclass
class PromptRecord:
    """A prompt generated at a specific backtest signal point."""
    signal_time: datetime
    direction: str
    score: float
    current_price: float
    prompt: str

    def to_dict(self) -> dict:
        return {
            "signal_time": self.signal_time.isoformat(),
            "direction": self.direction,
            "score": self.score,
            "current_price": round(self.current_price, 6),
            "prompt": self.prompt,
        }

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Walk-forward backtest engine.

    For each step along the primary (highest) timeframe:
      1. Slice the last `window_size` candles per TF up to the current point
      2. Run pattern + indicator + SMC analysis (no LLM)
      3. Generate a directional signal via rule-based scoring
      4. Simulate trade execution on the lowest TF going forward
      5. Record trade outcomes
    """

    def __init__(
        self,
        window_size: int = 200,
        step_candles: int = 1,
        min_score: float = 3.0,
        max_hold_candles: int = 48,
    ) -> None:
        self.window_size = window_size
        self.step_candles = step_candles
        self.min_score = min_score
        self.max_hold_candles = max_hold_candles

    def run(
        self,
        symbol: str,
        mode: AnalysisMode,
        start_date: str,
        end_date: str,
    ) -> BacktestResult:
        """Execute the full backtest.

        Args:
            symbol: e.g. "BTCUSDT"
            mode: AnalysisMode.SCALPING or AnalysisMode.SWING
            start_date: "YYYY-MM-DD"
            end_date: "YYYY-MM-DD"

        Returns:
            BacktestResult with all trades and performance metrics.
        """
        timeframes = TIMEFRAME_PRESETS[mode]
        primary_tf = timeframes[-1]   # highest TF drives signal cadence
        exec_tf = timeframes[0]       # lowest TF for trade execution

        logger.info(
            "Backtest: %s | %s | %s → %s", symbol, mode.value, start_date, end_date
        )
        logger.info(
            "Settings: window=%d, step=%d, min_score=%.1f, max_hold=%d",
            self.window_size, self.step_candles, self.min_score, self.max_hold_candles,
        )

        # ── Load full historical data ────────────────────────────────────────
        all_data = load_historical_candles(symbol, timeframes, start_date, end_date)

        primary_df = all_data.get(primary_tf, pd.DataFrame())
        exec_df = all_data.get(exec_tf, pd.DataFrame())

        if primary_df.empty or len(primary_df) < self.window_size + 10:
            logger.error(
                "Insufficient data for %s %s: only %d candles", symbol, primary_tf, len(primary_df)
            )
            return evaluate_trades(
                [], symbol, mode.value, start_date, end_date, 0,
                self.window_size, self.step_candles, self.min_score,
            )

        logger.info(
            "Loaded: %s=%d, %s=%d candles",
            primary_tf, len(primary_df),
            exec_tf, len(exec_df),
        )

        # ── Walk-forward loop ────────────────────────────────────────────────
        trades: list[TradeResult] = []
        total_signals = 0

        # Step through primary TF candles (skip first window_size for warm-up)
        step_indices = range(self.window_size, len(primary_df), self.step_candles)
        logger.info("Analysis steps: %d", len(step_indices))

        for step_num, i in enumerate(step_indices, start=1):
            current_time = primary_df.index[i]

            # Build windows: last window_size candles up to (and including) current_time
            windows: dict[str, pd.DataFrame] = {}
            for tf, df in all_data.items():
                mask = df.index <= current_time
                windows[tf] = df[mask].tail(self.window_size)

            if windows.get(exec_tf, pd.DataFrame()).empty:
                continue

            # Run pipeline stages
            try:
                patterns = analyze_patterns(windows)
                indicators = calculate_all_timeframes(windows)
                smc = analyze_smc_all_timeframes(windows)
            except Exception as e:
                logger.debug("Pipeline error at step %d: %s", step_num, e)
                continue

            # Generate signal
            signal = generate_signal(
                patterns_by_tf=patterns,
                indicators_by_tf=indicators,
                smc_by_tf=smc,
                timeframes=timeframes,
                candles_by_tf=windows,
                signal_time=current_time,
                min_score=self.min_score,
            )

            if signal is None:
                continue

            total_signals += 1

            # Get execution candles going forward from signal time
            forward_mask = exec_df.index > current_time
            exec_window = exec_df[forward_mask].head(self.max_hold_candles * 3)

            # Simulate trade
            trade = simulate_trade(
                signal=signal,
                exec_candles=exec_window,
                max_hold=self.max_hold_candles,
            )

            if trade is not None:
                trades.append(trade)
                if step_num % 50 == 0 or len(trades) % 10 == 0:
                    logger.info(
                        "  [step %d] Signal %s @ %.4f | score=%.1f → %s (%.2f%%)",
                        step_num, signal.direction, signal.entry_high,
                        signal.score, trade.outcome, trade.pnl_pct,
                    )

        logger.info(
            "Complete: %d signals, %d trades executed", total_signals, len(trades)
        )

        return evaluate_trades(
            trades=trades,
            symbol=symbol,
            mode=mode.value,
            start_date=start_date,
            end_date=end_date,
            total_signals=total_signals,
            window_size=self.window_size,
            step_candles=self.step_candles,
            min_score=self.min_score,
        )

    def dump_prompts(
        self,
        symbol: str,
        mode: AnalysisMode,
        start_date: str,
        end_date: str,
        limit: int | None = None,
    ) -> list[PromptRecord]:
        """Walk-forward through history and collect the LLM prompts at each signal point.

        Does NOT call the LLM — only builds the prompt string that would be sent.
        Useful for reviewing data quality, prompt structure, and improving instructions.

        Args:
            symbol: e.g. "BTCUSDT"
            mode: AnalysisMode.SCALPING or AnalysisMode.SWING
            start_date: "YYYY-MM-DD"
            end_date: "YYYY-MM-DD"
            limit: stop after collecting this many prompts (None = collect all)

        Returns:
            List of PromptRecord (signal_time, direction, score, current_price, prompt)
        """
        timeframes = TIMEFRAME_PRESETS[mode]
        primary_tf = timeframes[-1]
        exec_tf = timeframes[0]

        logger.info(
            "Prompt dump: %s | %s | %s → %s", symbol, mode.value, start_date, end_date
        )

        all_data = load_historical_candles(symbol, timeframes, start_date, end_date)
        primary_df = all_data.get(primary_tf, pd.DataFrame())

        if primary_df.empty or len(primary_df) < self.window_size + 10:
            logger.error("Insufficient data for prompt dump")
            return []

        records: list[PromptRecord] = []
        step_indices = range(self.window_size, len(primary_df), self.step_candles)

        for step_num, i in enumerate(step_indices, start=1):
            if limit is not None and len(records) >= limit:
                break

            current_time = primary_df.index[i]

            windows: dict[str, pd.DataFrame] = {}
            for tf, df in all_data.items():
                mask = df.index <= current_time
                windows[tf] = df[mask].tail(self.window_size)

            if windows.get(exec_tf, pd.DataFrame()).empty:
                continue

            try:
                patterns = analyze_patterns(windows)
                indicators = calculate_all_timeframes(windows)
                smc = analyze_smc_all_timeframes(windows)
            except Exception as e:
                logger.debug("Pipeline error at step %d: %s", step_num, e)
                continue

            signal = generate_signal(
                patterns_by_tf=patterns,
                indicators_by_tf=indicators,
                smc_by_tf=smc,
                timeframes=timeframes,
                candles_by_tf=windows,
                signal_time=current_time,
                min_score=self.min_score,
            )

            if signal is None:
                continue

            exec_df_window = windows.get(exec_tf, pd.DataFrame())
            current_price = float(exec_df_window.iloc[-1]["close"]) if not exec_df_window.empty else 0.0

            prompt = _build_prompt(
                symbol=symbol,
                market="crypto",
                mode=mode.value,
                timeframes=timeframes,
                patterns=patterns,
                indicators=indicators,
                smc_data=smc,
            )

            records.append(PromptRecord(
                signal_time=current_time,
                direction=signal.direction,
                score=signal.score,
                current_price=current_price,
                prompt=prompt,
            ))

            logger.info(
                "[%d] %s signal @ %s | price=%.4f score=%.1f",
                len(records), signal.direction,
                current_time.strftime("%Y-%m-%d %H:%M"),
                current_price, signal.score,
            )

        logger.info("Collected %d prompts", len(records))
        return records

    def run_from_snapshots(
        self,
        snapshots: list[AnalysisSnapshot],
    ) -> BacktestResult:
        """Backtest saved LLM snapshots — validate each LLM signal against real price action.

        For every snapshot that has an LLM analysis:
          1. Extract the LLM's signal (direction, entry_zone, SL, TP)
          2. Fetch execution candles from Binance starting at the snapshot timestamp
          3. Simulate the trade using the existing simulator
          4. Report performance

        This tests the actual LLM-generated advice, not a rule-based proxy.

        Args:
            snapshots: List of AnalysisSnapshot loaded from storage.

        Returns:
            BacktestResult with performance metrics across all snapshots.
        """
        tradeable = [s for s in snapshots if s.data.analysis is not None]
        logger.info(
            "Snapshot backtest: %d snapshots total, %d with LLM analysis",
            len(snapshots), len(tradeable),
        )

        if not tradeable:
            logger.warning("No snapshots with LLM analysis found — nothing to backtest")
            return evaluate_trades(
                [], "mixed", "mixed", "—", "—", 0,
                self.window_size, self.step_candles, self.min_score,
            )

        trades: list[TradeResult] = []

        for snap in tradeable:
            analysis = snap.data.analysis
            mode_str = snap.data.mode
            symbol = snap.data.symbol
            signal_time = snap.data.timestamp

            # Resolve execution timeframe (lowest TF for the mode)
            try:
                mode = AnalysisMode(mode_str)
            except ValueError:
                logger.warning("Unknown mode %r in snapshot %s — skipping", mode_str, snap.id)
                continue
            exec_tf = TIMEFRAME_PRESETS[mode][0]
            tf_minutes = _TF_MINUTES.get(exec_tf, 15)

            # Build a TradeSignal from the LLM's TradingAnalysis
            tp_prices = [tp.price for tp in analysis.take_profit_targets]
            if len(tp_prices) < 2:
                logger.warning("Snapshot %s has < 2 TP targets — skipping", snap.id)
                continue
            tp1 = tp_prices[0]
            tp2 = tp_prices[1]
            tp3 = tp_prices[2] if len(tp_prices) >= 3 else tp2 + (tp2 - tp1)

            signal = TradeSignal(
                direction=analysis.direction,
                entry_low=analysis.entry_zone.low,
                entry_high=analysis.entry_zone.high,
                stop_loss=analysis.stop_loss.price,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                score=0.0,   # LLM-generated; score not applicable
                signal_time=signal_time,
            )

            # Fetch forward execution candles
            # Window: signal_time → signal_time + max_hold_candles * tf_minutes
            start_str = signal_time.strftime("%Y-%m-%d %H:%M:%S")
            end_dt = signal_time + timedelta(minutes=tf_minutes * self.max_hold_candles * 2)
            end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

            logger.info(
                "Fetching %s %s from %s for snapshot %s",
                symbol, exec_tf, start_str, snap.id,
            )
            try:
                candles = load_historical_candles(symbol, [exec_tf], start_str, end_str)
                exec_df = candles.get(exec_tf, pd.DataFrame())
            except Exception as e:
                logger.error("Failed to fetch candles for snapshot %s: %s", snap.id, e)
                continue

            if exec_df.empty:
                logger.warning("No execution candles for snapshot %s — skipping", snap.id)
                continue

            # Only use candles strictly after the signal time
            exec_df = exec_df[exec_df.index > signal_time]

            trade = simulate_trade(
                signal=signal,
                exec_candles=exec_df,
                max_hold=self.max_hold_candles,
            )

            if trade is not None:
                trades.append(trade)
                logger.info(
                    "  %s %s @ %.4f → %s (%.2f%%)",
                    symbol, analysis.direction, snap.data.current_price,
                    trade.outcome, trade.pnl_pct,
                )
            else:
                logger.info("  %s %s — price never entered entry zone", symbol, analysis.direction)

        logger.info("Snapshot backtest complete: %d/%d trades executed", len(trades), len(tradeable))

        # Use the date range of the snapshots as metadata
        dates = sorted(s.data.timestamp for s in tradeable)
        start_date = dates[0].strftime("%Y-%m-%d") if dates else "—"
        end_date = dates[-1].strftime("%Y-%m-%d") if dates else "—"

        return evaluate_trades(
            trades=trades,
            symbol=", ".join(sorted({s.data.symbol for s in tradeable})),
            mode=", ".join(sorted({s.data.mode for s in tradeable})),
            start_date=start_date,
            end_date=end_date,
            total_signals=len(tradeable),
            window_size=self.window_size,
            step_candles=self.step_candles,
            min_score=self.min_score,
        )
