# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
