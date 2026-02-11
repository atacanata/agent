#!/usr/bin/env bash
set -euo pipefail

echo "[ci] start"

if [ -f package.json ]; then
  echo "[ci] node project detected"
  npm -v
  npm install
  if npm run | grep -q " test"; then
    npm test
  else
    echo "[ci] no npm test script"
  fi
fi

if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  echo "[ci] python project detected"
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install -U pip
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt
  fi
  if command -v pytest >/dev/null 2>&1; then
    pytest -q
  else
    echo "[ci] pytest not installed; skipping"
  fi
fi

echo "[ci] done"
