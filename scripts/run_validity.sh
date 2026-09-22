#!/usr/bin/env bash
# Validity experiments, 2026-09-20. These test whether the scored metrics measure
# anything, as opposed to how precisely they measure it. Strictly serial: two Boltz
# processes on a 12 GB card is a CUDA OOM that exits 0 and looks like a completed fold.
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."
echo "=== validity run started $(date -Is) ==="

echo "=== V1: epitope knockout (12 folds) $(date -Is) ==="
"$PY" scripts/48_epitope_knockout.py
echo "V1 exit=$? at $(date -Is)"
echo

echo "=== V2: composition-matched scramble null (30 folds) $(date -Is) ==="
"$PY" scripts/49_scramble_null.py
echo "V2 exit=$? at $(date -Is)"
echo

if [ -f scripts/51_analyse_validity.py ]; then
  "$PY" scripts/51_analyse_validity.py
  echo "analysis exit=$? at $(date -Is)"
fi
echo "=== validity run finished $(date -Is) ==="
