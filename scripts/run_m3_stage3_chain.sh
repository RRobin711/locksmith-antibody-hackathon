#!/usr/bin/env bash
# Runs after the 7-seed reseed finishes. Waits for it rather than racing it:
# both stages want the GPU, and two Boltz processes on a 12 GB card is a CUDA OOM
# that exits 0 and looks like a completed fold.
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."

echo "=== chain started $(date -Is); waiting for the reseed to finish ==="
while pgrep -f "32_shortlist_and_reseed" > /dev/null; do sleep 60; done
echo "reseed finished at $(date -Is); folds on disk: $(wc -l < runs/designs_reseed7/index.jsonl)"
echo

echo "=== STAGE A: score shortlist, name + discount winner, characterise ensemble ==="
"$PY" scripts/35_winner.py
echo "stage A exit=$? at $(date -Is)"
echo

echo "=== STAGE B: batching acceptance test (GPU now free) ==="
"$PY" scripts/34_verify_batching.py
echo "stage B exit=$? at $(date -Is)"
echo
echo "=== chain finished $(date -Is) ==="
