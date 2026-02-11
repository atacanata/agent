#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${1:-}"
if [ -z "$RUN_ID" ]; then
  echo "Usage: gate_stage_c.sh <RUN_ID>"
  exit 2
fi

REQ=(
  "docs/RUNBOOK/ci_${RUN_ID}.log"
  "docs/RUNBOOK/test_${RUN_ID}.md"
  "docs/RUNBOOK/diff_${RUN_ID}.patch"
  "docs/RUNBOOK/review_${RUN_ID}.md"
)

for f in "${REQ[@]}"; do
  [ -f "$f" ] || { echo "[gate] missing: $f"; exit 3; }
done

grep -q "RESULT: PASS" "docs/RUNBOOK/test_${RUN_ID}.md" || { echo "[gate] RESULT: PASS not found"; exit 4; }
grep -q "VERDICT: APPROVE" "docs/RUNBOOK/review_${RUN_ID}.md" || { echo "[gate] VERDICT: APPROVE not found"; exit 5; }

echo "[gate] PASS"
