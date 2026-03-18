# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-03-18

### Added
- **Backtesting System**: Walk-forward backtesting with rule-based signal generation (RSI, MACD, SMC, patterns), trade simulation with partial take-profit exits, and performance evaluation metrics (win rate, profit factor, drawdown).
- **Snapshot API**: REST endpoints (`GET/POST/DELETE /api/v1/snapshots`) to save and retrieve analysis results for backtesting validation.
- **Snapshot UI**: "Save Snapshot" button in `ResultPanel.vue` to persist LLM analysis results from the frontend.
- **Backtest CLI**: `backtest_run.py` entry point supporting walk-forward, snapshot-based, and prompt-dump modes.
- **Prompt Passthrough**: `llm_synthesizer.synthesize_analysis()` now returns the prompt string alongside analysis, stored in `AnalysisResponse.prompt` for snapshot use.
- **Start Script**: `start.sh` to launch backend and frontend together with a single command.

## [0.5.0] - 2026-03-13

### Added
- **Real-time Price Sync**: Added Binance WebSocket integration in debug client to show live ticker prices.
- **Analysis Price Context**: API now returns `current_price` (the price at the moment of analysis) for comparison.
- **Improved UI**: Enhanced `ResultPanel.vue` to display analysis price and live price side-by-side with price movement indicators (green/red).

## [0.4.0] - 2026-02-15

### Added
- Initial structure for Smart Money Concepts (SMC) analyzer.
- Support for Order Blocks and Fair Value Gaps (FVG) detection.
- Multi-timeframe analysis orchestrator.
