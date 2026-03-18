"""Performance evaluator — computes backtesting metrics from trade results."""

from dataclasses import dataclass, field

from app.backtest.simulator import TradeResult


@dataclass
class BacktestResult:
    symbol: str
    mode: str
    start_date: str
    end_date: str
    window_size: int
    step_candles: int
    min_score: float

    total_signals: int = 0       # signals generated
    total_trades: int = 0        # signals that actually entered
    winning_trades: int = 0
    losing_trades: int = 0
    expired_trades: int = 0

    win_rate: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    profit_factor: float = 0.0
    total_pnl_pct: float = 0.0
    avg_pnl_pct: float = 0.0
    max_consecutive_losses: int = 0
    max_drawdown_pct: float = 0.0

    outcome_distribution: dict[str, int] = field(default_factory=dict)
    trades: list[TradeResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "mode": self.mode,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "window_size": self.window_size,
            "step_candles": self.step_candles,
            "min_score": self.min_score,
            "total_signals": self.total_signals,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "expired_trades": self.expired_trades,
            "win_rate": round(self.win_rate, 4),
            "avg_win_pct": round(self.avg_win_pct, 4),
            "avg_loss_pct": round(self.avg_loss_pct, 4),
            "profit_factor": round(self.profit_factor, 4),
            "total_pnl_pct": round(self.total_pnl_pct, 4),
            "avg_pnl_pct": round(self.avg_pnl_pct, 4),
            "max_consecutive_losses": self.max_consecutive_losses,
            "max_drawdown_pct": round(self.max_drawdown_pct, 4),
            "outcome_distribution": self.outcome_distribution,
            "trades": [t.to_dict() for t in self.trades],
        }


def _is_win(trade: TradeResult) -> bool:
    return trade.pnl_pct > 0


def _is_loss(trade: TradeResult) -> bool:
    return trade.pnl_pct < 0


def evaluate_trades(
    trades: list[TradeResult],
    symbol: str,
    mode: str,
    start_date: str,
    end_date: str,
    total_signals: int,
    window_size: int,
    step_candles: int,
    min_score: float,
) -> BacktestResult:
    """Compute performance metrics from a list of completed trades."""
    result = BacktestResult(
        symbol=symbol,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
        window_size=window_size,
        step_candles=step_candles,
        min_score=min_score,
        total_signals=total_signals,
        total_trades=len(trades),
        trades=trades,
    )

    if not trades:
        return result

    wins = [t for t in trades if _is_win(t)]
    losses = [t for t in trades if _is_loss(t)]
    expired = [t for t in trades if t.outcome in ("expired",) and t.pnl_pct == 0]

    result.winning_trades = len(wins)
    result.losing_trades = len(losses)
    result.expired_trades = len([t for t in trades if "expired" in t.outcome])
    result.win_rate = len(wins) / len(trades) if trades else 0.0

    result.avg_win_pct = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0.0
    result.avg_loss_pct = sum(t.pnl_pct for t in losses) / len(losses) if losses else 0.0

    gross_profit = sum(t.pnl_pct for t in wins)
    gross_loss = abs(sum(t.pnl_pct for t in losses))
    result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    result.total_pnl_pct = sum(t.pnl_pct for t in trades)
    result.avg_pnl_pct = result.total_pnl_pct / len(trades)

    # Max consecutive losses
    max_consec = 0
    current_consec = 0
    for t in trades:
        if _is_loss(t):
            current_consec += 1
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = 0
    result.max_consecutive_losses = max_consec

    # Max drawdown (equity curve assuming equal position size)
    equity = 100.0
    peak = 100.0
    max_dd = 0.0
    for t in trades:
        equity += t.pnl_pct
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd
    result.max_drawdown_pct = max_dd

    # Outcome distribution
    from collections import Counter
    result.outcome_distribution = dict(Counter(t.outcome for t in trades))

    return result
