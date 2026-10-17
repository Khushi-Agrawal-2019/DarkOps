#!/usr/bin/env bash
# ==============================================================================
# Return Detective — Local Full-Stack Launch Script
# Starts rd-api (:8000), rd-runner (:8001), and rd-web (:3000)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

source .venv/bin/activate

echo "=========================================================="
echo "🕵️  Starting Return Detective Local Demo Environment"
echo "=========================================================="

# 1. Start rd-api
echo "Starting rd-api on http://localhost:8000 ..."
python -m uvicorn api.main:app --port 8000 --log-level warning &
PID_API=$!

# 2. Start rd-runner
echo "Starting rd-runner on http://localhost:8001 ..."
python -m uvicorn api.runner:app --port 8001 --log-level warning &
PID_RUNNER=$!

# 3. Start rd-web
echo "Starting Next.js dashboard on http://localhost:3000 ..."
(cd web && npm run dev) &
PID_WEB=$!

trap "kill ${PID_API} ${PID_RUNNER} ${PID_WEB} 2>/dev/null || true" EXIT

sleep 3

echo ""
echo "=========================================================="
echo "🎉 Return Detective is LIVE locally!"
echo "=========================================================="
echo "Web Dashboard : http://localhost:3000/inbox?demo=1"
echo "Owner Portal  : http://localhost:3000/owner"
echo "Mock Store API: http://localhost:8000"
echo "Runner Engine : http://localhost:8001"
echo "=========================================================="
echo "Press Ctrl+C to stop all services."

wait
