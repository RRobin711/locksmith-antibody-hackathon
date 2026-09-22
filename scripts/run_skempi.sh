#!/usr/bin/env bash
# Queued behind run_validity.sh. Two Boltz processes on a 12 GB card is a CUDA OOM
# that exits 0 and looks like a completed fold, so this waits rather than races.
# The pattern cannot self-match: "scripts/run_validity.sh" is not a substring of
# "scripts/run_skempi.sh".
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."
echo "=== skempi chain armed $(date -Is); waiting for the validity run ==="
while pgrep -f "scripts/run_validity\.sh" > /dev/null; do sleep 60; done
echo "validity run finished at $(date -Is)"
"$PY" scripts/53_skempi_fold.py
echo "fold exit=$? at $(date -Is)"
"$PY" scripts/54_analyse_skempi.py
echo "analysis exit=$? at $(date -Is)"
echo "=== skempi chain finished $(date -Is) ==="
