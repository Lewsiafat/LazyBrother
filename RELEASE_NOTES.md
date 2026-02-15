# Release Notes

## [v0.2.0] - 2026-02-15

### Added
- **Vue 3 Debug Frontend** — visual client at `frontend/` for testing the analysis API
  - Input form with symbol, market, and mode selectors
  - Quick-pick buttons for common symbols (BTC, ETH, SOL, AAPL, TSLA, NVDA)
  - Structured result cards: trading thesis, entry/exit levels, indicators, SMC, patterns
  - Collapsible raw JSON viewer with copy-to-clipboard
  - Backend health indicator (auto-polls every 15s)
  - Request elapsed time tracking
  - Dark glassmorphism theme with responsive layout
- Archived walkthrough documentation to `docs/archive/`

### Changed
- Updated `README.md` with frontend instructions and `uv`-based install
- Updated `CLAUDE.md` with frontend directory structure

## [v0.1.0] - 2026-02-15

### Added
- Initial backend scaffolding with FastAPI + Uvicorn
- Analysis pipeline: DataFetcher, PatternAnalyzer, IndicatorCalc, SMCAnalyzer, LLMSynthesizer
- Multi-provider LLM support (OpenAI, Gemini, Claude)
- Multi-market data fetching (Binance for crypto, yFinance for stocks)
- Scalping and swing analysis modes
- API endpoints: POST /api/v1/analyze, GET /api/v1/health
