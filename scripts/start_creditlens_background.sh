#!/bin/bash
# CreditLens Persistent Background Launcher for macOS
# Starts the Streamlit application in the background so it stays running without needing a terminal open.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# Ensure reports directory exists for logs
mkdir -p "$BASE_DIR/reports"

# Check if already running on port 8501
RUNNING_PID=$(lsof -ti :8501 2>/dev/null)
if [ -n "$RUNNING_PID" ]; then
    echo "CreditLens is already running (PID: $RUNNING_PID)."
    echo "Opening in browser: http://localhost:8501"
    open "http://localhost:8501" 2>/dev/null || true
    exit 0
fi

echo "Starting CreditLens Risk OS in background..."
nohup "$BASE_DIR/.venv/bin/streamlit" run "$BASE_DIR/app/streamlit_app.py" --server.port=8501 --server.headless=true > "$BASE_DIR/reports/creditlens_app.log" 2>&1 &
NEW_PID=$!
echo "CreditLens started with PID $NEW_PID."
sleep 2
open "http://localhost:8501" 2>/dev/null || true
echo "✅ App is live at http://localhost:8501 (Logs: reports/creditlens_app.log)"
