#!/usr/bin/env python3
"""LazyBrother Backtest CLI — walk-forward backtesting entry point.

Usage examples:
  # Swing backtest on BTCUSDT for 2024
  uv run python backtest_run.py --symbol BTCUSDT --mode swing --start 2024-01-01 --end 2024-12-31

  # Scalping backtest on ETHUSDT, stricter signal threshold
  uv run python backtest_run.py --symbol ETHUSDT --mode scalping --start 2024-06-01 --end 2024-09-30 --min-score 4.0

  # Output as JSON (for further analysis)
  uv run python backtest_run.py --symbol SOLUSDT --mode swing --start 2024-01-01 --end 2024-06-30 --output json > results.json

  # Step every 4 primary-TF candles (less crowded signals)
  uv run python backtest_run.py --symbol BTCUSDT --mode swing --start 2024-01-01 --end 2024-12-31 --step 4
"""

import argparse
import json
import logging
import sys
from datetime import datetime

from app.models.request import AnalysisMode
from app.backtest.runner import BacktestRunner, PromptRecord
from app.backtest.evaluator import BacktestResult
from app.storage.snapshot_store import list_snapshots


# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backtest")


# ── Report rendering ──────────────────────────────────────────────────────────

def _bar(value: float, max_val: float, width: int = 20, char: str = "█") -> str:
    filled = int(round(value / max_val * width)) if max_val > 0 else 0
    return char * filled + "░" * (width - filled)


def print_report(result: BacktestResult) -> None:
    sep = "─" * 60

    print()
    print("╔" + "═" * 58 + "╗")
    print(f"║{'LazyBrother Backtest Report':^58}║")
    print("╚" + "═" * 58 + "╝")
    print()

    # ── Config ──────────────────────────────────────────────────────────────
    print(f"  Symbol   : {result.symbol}")
    print(f"  Mode     : {result.mode}")
    print(f"  Period   : {result.start_date}  →  {result.end_date}")
    print(f"  Window   : {result.window_size} candles  |  Step: {result.step_candles}  |  Min score: {result.min_score}")
    print()
    print(sep)

    # ── Trade counts ────────────────────────────────────────────────────────
    print(f"  Signals generated : {result.total_signals}")
    print(f"  Trades executed   : {result.total_trades}")
    if result.total_signals > 0:
        entry_rate = result.total_trades / result.total_signals * 100
        print(f"  Entry rate        : {entry_rate:.1f}%  (price entered zone)")
    print()

    if result.total_trades == 0:
        print("  ⚠  No trades executed — try lowering --min-score or widening the date range.")
        print()
        return

    # ── Win/Loss ─────────────────────────────────────────────────────────────
    win_bar = _bar(result.win_rate * 100, 100)
    print(f"  Win rate          : {result.win_rate * 100:.1f}%  {win_bar}")
    print(f"  Winners / Losers  : {result.winning_trades} W  /  {result.losing_trades} L  /  {result.expired_trades} expired")
    print()

    # ── P&L ─────────────────────────────────────────────────────────────────
    pnl_sign = "+" if result.total_pnl_pct >= 0 else ""
    print(f"  Total P&L         : {pnl_sign}{result.total_pnl_pct:.2f}%  (equal-size positions, compounded)")
    print(f"  Avg P&L / trade   : {pnl_sign}{result.avg_pnl_pct:.3f}%")
    print(f"  Avg win           : +{result.avg_win_pct:.3f}%")
    print(f"  Avg loss          : {result.avg_loss_pct:.3f}%")
    print(f"  Profit factor     : {result.profit_factor:.2f}x")
    print()

    # ── Risk ─────────────────────────────────────────────────────────────────
    print(f"  Max drawdown      : -{result.max_drawdown_pct:.2f}%")
    print(f"  Max consec losses : {result.max_consecutive_losses}")
    print()

    # ── Outcome breakdown ────────────────────────────────────────────────────
    print(sep)
    print("  Outcome breakdown:")
    total = result.total_trades
    for outcome, count in sorted(result.outcome_distribution.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        bar = _bar(pct, 100, width=15)
        print(f"    {outcome:<12}  {count:4d}  ({pct:5.1f}%)  {bar}")
    print()

    # ── Rating ───────────────────────────────────────────────────────────────
    print(sep)
    rating = _rate(result)
    print(f"  Signal quality    : {rating}")
    print()

    # ── Last 10 trades ───────────────────────────────────────────────────────
    if result.trades:
        print(sep)
        print("  Recent trades (last 10):")
        print(f"  {'Time':<20} {'Dir':<6} {'Entry':>10} {'Exit':>10} {'SL':>10} {'Outcome':<12} {'P&L':>8}")
        print(f"  {'─'*20} {'─'*6} {'─'*10} {'─'*10} {'─'*10} {'─'*12} {'─'*8}")
        for t in result.trades[-10:]:
            sign = "+" if t.pnl_pct >= 0 else ""
            ts = t.signal_time.strftime("%Y-%m-%d %H:%M") if t.signal_time else "—"
            print(
                f"  {ts:<20} {t.direction:<6} {t.entry_price:>10.4f} "
                f"{t.exit_price:>10.4f} {t.stop_loss:>10.4f} "
                f"{t.outcome:<12} {sign}{t.pnl_pct:>7.3f}%"
            )
        print()


def print_prompts(records: list[PromptRecord]) -> None:
    """Print collected prompts to stdout in human-readable format."""
    divider = "═" * 70

    if not records:
        print("\n  (no signals matched — try lowering --min-score)\n")
        return

    print(f"\n  {len(records)} prompt(s) collected\n")

    for idx, r in enumerate(records, start=1):
        print(divider)
        print(
            f"  [{idx}/{len(records)}]  {r.signal_time.strftime('%Y-%m-%d %H:%M')}  |  "
            f"{r.direction.upper()}  |  score={r.score:+.1f}  |  price={r.current_price:.6f}"
        )
        print(divider)
        print(r.prompt)
        print()


def _rate(result: BacktestResult) -> str:
    pf = result.profit_factor
    wr = result.win_rate
    dd = result.max_drawdown_pct

    if pf >= 2.0 and wr >= 0.55 and dd < 15:
        return "⭐⭐⭐  Excellent  (consider live testing)"
    elif pf >= 1.5 and wr >= 0.45 and dd < 25:
        return "⭐⭐    Good  (monitor closely)"
    elif pf >= 1.0 and wr >= 0.40:
        return "⭐      Marginal  (needs improvement)"
    elif pf < 1.0:
        return "✗       Unprofitable  (do not trade)"
    else:
        return "?       Inconclusive  (more data needed)"


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LazyBrother walk-forward backtesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--symbol", default=None, help="Trading pair, e.g. BTCUSDT (required unless --from-snapshots)")
    parser.add_argument(
        "--mode", choices=["scalping", "swing"], default="swing",
        help="Analysis mode (default: swing)"
    )
    parser.add_argument("--start", default=None, metavar="YYYY-MM-DD", help="Backtest start date (required unless --from-snapshots)")
    parser.add_argument(
        "--end", default=None, metavar="YYYY-MM-DD",
        help="Backtest end date (default: today)"
    )
    parser.add_argument(
        "--window-size", type=int, default=200,
        help="Candles in analysis window per TF (default: 200)"
    )
    parser.add_argument(
        "--step", type=int, default=1,
        help="Step between signal points in primary TF candles (default: 1)"
    )
    parser.add_argument(
        "--min-score", type=float, default=3.0,
        help="Minimum |score| to emit a signal (default: 3.0)"
    )
    parser.add_argument(
        "--max-hold", type=int, default=48,
        help="Max candles to hold a trade before forced exit (default: 48)"
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--trades-file", default=None, metavar="PATH",
        help="Save full trade list as JSON to this file"
    )
    parser.add_argument(
        "--from-snapshots", action="store_true",
        help="Backtest saved LLM snapshots (from data/snapshots.json) instead of walk-forward"
    )
    parser.add_argument(
        "--dump-prompts", action="store_true",
        help="Instead of simulating trades, print the LLM prompts generated at each signal point"
    )
    parser.add_argument(
        "--prompt-limit", type=int, default=None, metavar="N",
        help="Stop after collecting N prompts (use with --dump-prompts)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show DEBUG-level logs"
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    end_date = args.end or datetime.now().strftime("%Y-%m-%d")

    runner = BacktestRunner(
        window_size=args.window_size,
        step_candles=args.step,
        min_score=args.min_score,
        max_hold_candles=args.max_hold,
    )

    # ── Snapshot backtest mode ────────────────────────────────────────────────
    if args.from_snapshots:
        snapshots = list_snapshots()
        if not snapshots:
            logger.error("No snapshots found in data/snapshots.json — save some first via the UI.")
            sys.exit(1)

        logger.info("Loaded %d snapshots", len(snapshots))
        try:
            result = runner.run_from_snapshots(snapshots)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error("Snapshot backtest failed: %s", e, exc_info=True)
            sys.exit(1)

        if args.output == "json":
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            print_report(result)

        if args.trades_file:
            with open(args.trades_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            logger.info("Results saved to %s", args.trades_file)
        return

    # ── Prompt dump mode ──────────────────────────────────────────────────────
    if args.dump_prompts:
        try:
            records = runner.dump_prompts(
                symbol=args.symbol.upper(),
                mode=AnalysisMode(args.mode),
                start_date=args.start,
                end_date=end_date,
                limit=args.prompt_limit,
            )
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error("Prompt dump failed: %s", e, exc_info=True)
            sys.exit(1)

        if args.output == "json":
            print(json.dumps([r.to_dict() for r in records], indent=2, default=str))
        else:
            print_prompts(records)

        if args.trades_file:
            with open(args.trades_file, "w") as f:
                json.dump([r.to_dict() for r in records], f, indent=2, default=str)
            logger.info("Prompts saved to %s", args.trades_file)
        return

    # ── Backtest mode ─────────────────────────────────────────────────────────
    if not args.symbol or not args.start:
        logger.error("--symbol and --start are required for walk-forward backtest (or use --from-snapshots)")
        sys.exit(1)

    try:
        result = runner.run(
            symbol=args.symbol.upper(),
            mode=AnalysisMode(args.mode),
            start_date=args.start,
            end_date=end_date,
        )
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error("Backtest failed: %s", e, exc_info=True)
        sys.exit(1)

    # Output
    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print_report(result)

    # Optionally save trades to file
    if args.trades_file:
        with open(args.trades_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        logger.info("Results saved to %s", args.trades_file)


if __name__ == "__main__":
    main()
