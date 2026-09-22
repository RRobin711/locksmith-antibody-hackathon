#!/usr/bin/env bash
# Stage 2, 2026-09-20. Waits for run_tonight.sh to exit, then uses the remaining
# GPU time before 10:00. Launched separately BECAUSE run_tonight.sh is already
# running and bash reads a script incrementally from disk -- editing a running
# shell script can make it resume at a corrupted byte offset. A second waiting
# process is the safe way to extend a chain that is already in flight.
#
# ORDER, and why:
#   1. Novelty probe (42 folds, ~65 min) FIRST. It is a complete new experiment with
#      a pre-registered primary comparison; the ensemble continuation only adds
#      precision to a study that is already well powered at k=2/n=239. Guaranteeing
#      the whole experiment beats marginally improving another one.
#   2. Analysis pass. Runs BEFORE the optional extra folding so that a full set of
#      results exists on disk no matter what happens after.
#   3. Ensemble continuation to 09:05 -- seed 3 in the same shuffled order, which
#      raises attenuation on that subset from ~0.77 to ~0.90 and, more usefully,
#      lets the pool's own V1 be checked against the shortlist's rather than assumed.
#   4. Analysis again, refreshing with whatever step 3 added. Cheap: every scorer is
#      cached per label, so the second pass only touches new folds.
set -u
PY=/home/rrobin711/.venvs/locksmith/bin/python
cd "$(dirname "$0")/.."

echo "=== stage 2 armed $(date -Is); waiting for stage 1 ==="
# The pattern cannot match this script: "scripts/run_tonight.sh" is not a substring
# of "scripts/run_tonight_stage2.sh". Verified before launch.
while pgrep -f "scripts/run_tonight\.sh" > /dev/null; do sleep 60; done
echo "stage 1 finished at $(date -Is)"
nvidia-smi --query-gpu=memory.used --format=csv,noheader
echo

echo "=== STAGE 2A: TIM-3 reference controls, 6 folds $(date -Is) ==="
# Added 01:45 after the specificity panel came back with the named design at ipSAE
# 0.624/0.612/0.469 against TIM-3 -- 2 of 3 seeds over the 0.60 viability cutoff at
# dG <= -14, which triggers the pre-declared failure condition. Six folds decide
# whether that is our design or the predictor: pembrolizumab (certain non-binder) and
# the 8TBB Fab (real binder) against the same antigen. Cheapest, highest-value folds
# available tonight, so they go first.
"$PY" scripts/46_decoy_reference_fold.py
echo "2A exit=$? at $(date -Is)"
echo

echo "=== STAGE 2B: novelty probe, 42 folds $(date -Is) ==="
"$PY" scripts/44_novelty_probe_fold.py
echo "2B exit=$? at $(date -Is)"
echo

echo "=== STAGE 2C: analysis pass 1 (guarantees results exist) $(date -Is) ==="
"$PY" scripts/45_analyse_novelty_probe.py
"$PY" scripts/42_analyse_tonight.py
echo "2C exit=$? at $(date -Is)"
echo

echo "=== STAGE 2D: ensemble continuation to 09:05 $(date -Is) ==="
ENSEMBLE_DEADLINE=09:05 "$PY" scripts/39_ensemble_wide_fold.py
echo "2D exit=$? at $(date -Is)"
echo

echo "=== STAGE 2E: analysis pass 2 $(date -Is) ==="
"$PY" scripts/42_analyse_tonight.py
"$PY" scripts/45_analyse_novelty_probe.py
echo "2E exit=$? at $(date -Is)"
echo

echo "=== stage 2 finished $(date -Is) ==="
for f in results/specificity.md results/ablation.md results/ensemble_wide.md \
         results/novelty_probe.md results/rubric_headroom.md results/ensemble_power.md; do
  [ -f "$f" ] && echo "  OK   $f" || echo "  MISS $f"
done
echo "folds: spec=$(wc -l < runs/specificity/index.jsonl 2>/dev/null || echo 0)" \
     "abl=$(wc -l < runs/ablation/index.jsonl 2>/dev/null || echo 0)" \
     "ens=$(wc -l < runs/designs_ens/index.jsonl 2>/dev/null || echo 0)" \
     "probe=$(wc -l < runs/novelty_probe/index.jsonl 2>/dev/null || echo 0)" "refs=$(wc -l < runs/specificity_ref/index.jsonl 2>/dev/null || echo 0)"
