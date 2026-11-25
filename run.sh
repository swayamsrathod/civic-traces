#!/usr/bin/env bash
# One-command start for Mac/Linux: installs, loads demo data, starts the dashboard.
set -e
cd "$(dirname "$0")"
echo "Installing dependencies (first run takes a few minutes)..."
python3 -m pip install -r requirements.txt --quiet
if [ ! -f civictrace.db ]; then
  echo "Loading demo complaints..."
  python3 -m scripts.seed_demo
fi
echo
echo "Dashboard starting at http://localhost:8000  (press Ctrl+C to stop)"
( sleep 2; (open http://localhost:8000 || xdg-open http://localhost:8000) >/dev/null 2>&1 ) &
python3 -m uvicorn backend.main:app
