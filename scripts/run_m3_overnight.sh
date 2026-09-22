#!/usr/bin/env bash
# M3 primary arm, unattended. Fold first (GPU, the irreplaceable work), then score.
#
# Ordering is deliberate: if the night is cut short, folds are what cannot be
# recreated cheaply, and scoring is 19 s/fold that can run any time afterwards.
# Both stages are resumable and idempotent, so a kill at any point costs at most
# the unit in flight. `set -e` is deliberately NOT used: a non-zero scorer must
# not discard the folding that already succeeded.
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."

echo "=== M3 primary arm — started $(date -Is) ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
free -g | head -2
echo

echo "=== STAGE 1/2: folding (239 designs, 1 seed, unfiltered) $(date -Is) ==="
"$PY" scripts/29_fold_temp_arm.py
echo "stage 1 exit=$? at $(date -Is)"
echo

echo "=== STAGE 2/2: scoring $(date -Is) ==="
"$PY" scripts/30_score_temp_arm.py
echo "stage 2 exit=$? at $(date -Is)"
echo

echo "=== finished $(date -Is) ==="
echo "folds recorded:  $(wc -l < runs/designs_temp/index.jsonl 2>/dev/null || echo 0)"
echo "folds scored:    $(wc -l < runs/designs_temp/fold_scores.jsonl 2>/dev/null || echo 0)"
echo "designs scored:  $(wc -l < runs/designs_temp/seq_scores.jsonl 2>/dev/null || echo 0)"
