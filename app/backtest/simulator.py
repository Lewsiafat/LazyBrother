"""Trade simulator — walks forward through candles to determine trade outcomes.

Assumptions:
- Within a candle the order is: open → (low or high, worst-case first for SL) → close
- SL is checked before TP to be conservative (pessimistic fill)
- TP levels are hit progressively; reaching TP1 moves SL to breakeven,
  reaching TP2 moves SL to TP1.
- Partial exit sizes: TP1=33%, TP2=33%, TP3=34% of position
"""

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from app.backtest.signal_generator import TradeSignal


@dataclass
class TradeResult:
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    outcome: str          # "tp3" | "tp2" | "tp1" | "sl" | "expired"
    pnl_pct: float        # weighted average P&L %
    signal_time: datetime
    entry_time: datetime | None
    exit_time: datetime | None
    candles_held: int
    score: float

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "entry_price": round(self.entry_price, 6),
            "exit_price": round(self.exit_price, 6),
            "stop_loss": round(self.stop_loss, 6),
            "tp1": round(self.tp1, 6),
            "tp2": round(self.tp2, 6),
            "tp3": round(self.tp3, 6),
            "outcome": self.outcome,
            "pnl_pct": round(self.pnl_pct, 4),
            "signal_time": self.signal_time.isoformat() if self.signal_time else None,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "candles_held": self.candles_held,
            "score": self.score,
        }


def _pnl_pct(entry: float, exit_price: float, direction: str) -> float:
    if direction == "long":
        return (exit_price - entry) / entry * 100
    else:
        return (entry - exit_price) / entry * 100


def simulate_trade(
    signal: TradeSignal,
    exec_candles: pd.DataFrame,
    max_hold: int = 48,
) -> TradeResult | None:
    """Simulate a trade given a signal and forward-looking execution candles.

    Args:
        signal: The generated trade signal with entry/SL/TP levels.
        exec_candles: OHLCV candles starting after the signal timestamp.
        max_hold: Maximum candles to hold before forced expiry.

    Returns:
        TradeResult or None if price never entered the entry zone.
    """
    if exec_candles.empty:
        return None

    # ── Phase 1: find entry ──────────────────────────────────────────────────
    entry_price: float | None = None
    entry_time: datetime | None = None
    entry_candle_idx: int = -1

    for i, (ts, row) in enumerate(exec_candles.iterrows()):
        if i >= max_hold:
            break
        # Entry when price overlaps with entry zone
        if row["low"] <= signal.entry_high and row["high"] >= signal.entry_low:
            entry_price = (signal.entry_low + signal.entry_high) / 2
            entry_time = ts
            entry_candle_idx = i
            break

    if entry_price is None:
        return None

    # ── Phase 2: walk forward for exit ──────────────────────────────────────
    direction = signal.direction
    sl = signal.stop_loss
    tp1, tp2, tp3 = signal.tp1, signal.tp2, signal.tp3

    # SL ladders: after TP1 hit → SL moves to breakeven, after TP2 → SL to TP1
    current_sl = sl
    touched_tp1 = False
    touched_tp2 = False

    remaining_candles = exec_candles.iloc[entry_candle_idx:]
    for i, (ts, row) in enumerate(remaining_candles.iterrows()):
        if i >= max_hold:
            # Force close at close price
            outcome = "tp1" if touched_tp1 else ("tp2" if touched_tp2 else "expired")
            exit_price = float(row["close"])
            pnl = _weighted_pnl(
                entry_price, exit_price, direction,
                touched_tp1, touched_tp2, tp1, tp2,
            )
            return TradeResult(
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                stop_loss=sl,
                tp1=tp1, tp2=tp2, tp3=tp3,
                outcome=outcome,
                pnl_pct=pnl,
                signal_time=signal.signal_time,
                entry_time=entry_time,
                exit_time=ts,
                candles_held=i,
                score=signal.score,
            )

        if direction == "long":
            # Check SL first (conservative)
            if row["low"] <= current_sl:
                exit_price = current_sl
                pnl = _weighted_pnl(
                    entry_price, exit_price, direction,
                    touched_tp1, touched_tp2, tp1, tp2,
                )
                outcome = "sl" if not touched_tp1 else ("tp1_sl" if not touched_tp2 else "tp2_sl")
                return TradeResult(
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    stop_loss=sl,
                    tp1=tp1, tp2=tp2, tp3=tp3,
                    outcome=outcome,
                    pnl_pct=pnl,
                    signal_time=signal.signal_time,
                    entry_time=entry_time,
                    exit_time=ts,
                    candles_held=i,
                    score=signal.score,
                )
            # TP3
            if row["high"] >= tp3:
                pnl = _weighted_pnl(entry_price, tp3, direction, True, True, tp1, tp2)
                return TradeResult(
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=tp3,
                    stop_loss=sl,
                    tp1=tp1, tp2=tp2, tp3=tp3,
                    outcome="tp3",
                    pnl_pct=pnl,
                    signal_time=signal.signal_time,
                    entry_time=entry_time,
                    exit_time=ts,
                    candles_held=i,
                    score=signal.score,
                )
            # TP2
            if not touched_tp2 and row["high"] >= tp2:
                touched_tp2 = True
                current_sl = tp1   # trail SL to TP1
            # TP1
            if not touched_tp1 and row["high"] >= tp1:
                touched_tp1 = True
                current_sl = entry_price  # trail SL to breakeven

        else:  # short
            # Check SL first
            if row["high"] >= current_sl:
                exit_price = current_sl
                pnl = _weighted_pnl(
                    entry_price, exit_price, direction,
                    touched_tp1, touched_tp2, tp1, tp2,
                )
                outcome = "sl" if not touched_tp1 else ("tp1_sl" if not touched_tp2 else "tp2_sl")
                return TradeResult(
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    stop_loss=sl,
                    tp1=tp1, tp2=tp2, tp3=tp3,
                    outcome=outcome,
                    pnl_pct=pnl,
                    signal_time=signal.signal_time,
                    entry_time=entry_time,
                    exit_time=ts,
                    candles_held=i,
                    score=signal.score,
                )
            # TP3
            if row["low"] <= tp3:
                pnl = _weighted_pnl(entry_price, tp3, direction, True, True, tp1, tp2)
                return TradeResult(
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=tp3,
                    stop_loss=sl,
                    tp1=tp1, tp2=tp2, tp3=tp3,
                    outcome="tp3",
                    pnl_pct=pnl,
                    signal_time=signal.signal_time,
                    entry_time=entry_time,
                    exit_time=ts,
                    candles_held=i,
                    score=signal.score,
                )
            # TP2
            if not touched_tp2 and row["low"] <= tp2:
                touched_tp2 = True
                current_sl = tp1
            # TP1
            if not touched_tp1 and row["low"] <= tp1:
                touched_tp1 = True
                current_sl = entry_price

    # Ran out of candles — close at last available price
    last_ts = remaining_candles.index[-1]
    last_close = float(remaining_candles.iloc[-1]["close"])
    outcome = "tp2" if touched_tp2 else ("tp1" if touched_tp1 else "expired")
    pnl = _weighted_pnl(
        entry_price, last_close, direction,
        touched_tp1, touched_tp2, tp1, tp2,
    )
    return TradeResult(
        direction=direction,
        entry_price=entry_price,
        exit_price=last_close,
        stop_loss=sl,
        tp1=tp1, tp2=tp2, tp3=tp3,
        outcome=outcome,
        pnl_pct=pnl,
        signal_time=signal.signal_time,
        entry_time=entry_time,
        exit_time=last_ts,
        candles_held=len(remaining_candles),
        score=signal.score,
    )


def _weighted_pnl(
    entry: float,
    final_exit: float,
    direction: str,
    touched_tp1: bool,
    touched_tp2: bool,
    tp1: float,
    tp2: float,
) -> float:
    """Calculate weighted average P&L across partial exit tiers.

    Tiers: TP1=33%, TP2=33%, TP3/remainder=34%.
    Exits already triggered are locked in at their TP price;
    the remainder uses final_exit.
    """
    if direction == "long":
        exits: list[tuple[float, float]] = []
        remaining = 1.0
        if touched_tp1:
            exits.append((tp1, 0.33))
            remaining -= 0.33
        if touched_tp2:
            exits.append((tp2, 0.33))
            remaining -= 0.33
        exits.append((final_exit, remaining))

        total_pnl = sum((price - entry) / entry * 100 * weight for price, weight in exits)
    else:
        exits = []
        remaining = 1.0
        if touched_tp1:
            exits.append((tp1, 0.33))
            remaining -= 0.33
        if touched_tp2:
            exits.append((tp2, 0.33))
            remaining -= 0.33
        exits.append((final_exit, remaining))

        total_pnl = sum((entry - price) / entry * 100 * weight for price, weight in exits)

    return round(total_pnl, 4)
