#!/usr/bin/env bash
# Start backend (FastAPI) and frontend (Vite) together.
# Ctrl+C kills both.

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Colours
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[start]${NC} $*"; }
warn() { echo -e "${YELLOW}[start]${NC} $*"; }

# Kill child processes on exit
cleanup() {
  warn "Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

# ── Backend ──────────────────────────────────────────────────────────────────
log "Starting backend…"
cd "$ROOT"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────────────────────
log "Starting frontend…"
cd "$ROOT/frontend"

if [ ! -d node_modules ]; then
  warn "node_modules not found — running npm install…"
  npm install
fi

npm run dev &
FRONTEND_PID=$!

# ── Summary ──────────────────────────────────────────────────────────────────
cd "$ROOT"
echo ""
log "Backend  → http://localhost:8000"
log "Frontend → http://localhost:5173"
log "API docs → http://localhost:8000/docs"
echo ""
log "Press Ctrl+C to stop both."

wait
