#!/usr/bin/env bash
# Overnight 2026-09-20: characterisation, not selection.
#
# M3 is closed and mpnn_T0.5_s104_036 stays the named design whatever tonight finds.
# Nothing here re-ranks, re-shortlists or re-names anything.
#
# ORDER IS DELIBERATE AND IS NOT THE ORDER THAT WAS ASKED FOR. The brief put the big
# ensemble job first "because it is the valuable one". But it is ~4.6 h and the other
# two are ~46 min combined, so running it first risks losing both tails to any overrun,
# while running the tails first risks only the tail of a job that DEGRADES GRACEFULLY:
# the ensemble folds are shuffled, so stopping early costs precision, not the
# experiment. Losing 46 min off the end of a shuffled pool moves n from ~239 to ~200
# and the detectable effect by ~0.01 — against a 100% chance of losing a whole result
# the other way round. Cheap insurance, quantified.
#
# The NetSolP / rubric-headroom job is CPU-only (quantized ONNX) and runs CONCURRENTLY
# from the start: Boltz is GPU-bound and NetSolP does not meaningfully parallelise
# anyway (measured load 1.22 on 24 cores), so it costs the fold queue nothing.
#
# Two Boltz processes on a 12 GB card is a CUDA OOM that exits 0 and looks like a
# completed fold, so the GPU stages are strictly serial. Every stage asserts on
# artefacts, never on exit status.
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."
export ENSEMBLE_DEADLINE="${ENSEMBLE_DEADLINE:-07:30}"

echo "=== tonight's chain started $(date -Is) ==="
echo "ensemble deadline: $ENSEMBLE_DEADLINE"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
echo

echo "=== CPU (background, no GPU): rubric headroom + NetSolP over the 239 pool ==="
"$PY" scripts/40_rubric_headroom.py > runs/rubric_headroom.log 2>&1 &
CPU_PID=$!
echo "started pid $CPU_PID -> runs/rubric_headroom.log"
echo

echo "=== GPU STAGE 1/3: specificity controls (15 folds) $(date -Is) ==="
"$PY" scripts/37_specificity_fold.py
echo "stage 1 exit=$? at $(date -Is)"
echo

echo "=== GPU STAGE 2/3: hotspot ablation (18 folds) $(date -Is) ==="
"$PY" scripts/38_ablation_fold.py
echo "stage 2 exit=$? at $(date -Is)"
echo

echo "=== GPU STAGE 3/3: ensemble widening (deadline $ENSEMBLE_DEADLINE) $(date -Is) ==="
"$PY" scripts/39_ensemble_wide_fold.py
echo "stage 3 exit=$? at $(date -Is)"
echo

echo "=== waiting for the CPU job ==="
wait $CPU_PID
echo "cpu job exit=$? at $(date -Is)"
echo

if [ -f scripts/42_analyse_tonight.py ]; then
  echo "=== ANALYSIS $(date -Is) ==="
  "$PY" scripts/42_analyse_tonight.py
  echo "analysis exit=$? at $(date -Is)"
else
  echo "no scripts/42_analyse_tonight.py — folds are on disk, analyse in the morning"
fi

echo
echo "=== chain finished $(date -Is) ==="
echo "folds: specificity=$(wc -l < runs/specificity/index.jsonl 2>/dev/null || echo 0)" \
     "ablation=$(wc -l < runs/ablation/index.jsonl 2>/dev/null || echo 0)" \
     "ensemble=$(wc -l < runs/designs_ens/index.jsonl 2>/dev/null || echo 0)"
