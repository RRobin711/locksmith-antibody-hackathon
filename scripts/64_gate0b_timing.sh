#!/usr/bin/env bash
# Gate 0b: MEASURE, do not produce.  Outputs the numbers that decide CPU-vs-pod.
#   - seconds per DIFFUSION STEP (not per backbone: a backbone may take hours)
#   - peak RSS (RAM is the suspected binding constraint, not CPU)
#   - hotspot resolution count (an unmatched hotspot is SILENTLY ignored:
#     ab_pose.py:105-110 matches (chain,pdb_resnum) and just skips misses)
set -uo pipefail
V="$HOME/.venvs/rfab-cpu"; RFAB="$HOME/.cache/rfantibody"
IN="$RFAB/inputs"; OUT="$RFAB/gate0b"; mkdir -p "$OUT"
HOT="T64,T66,T68,T70,T73,T74,T75,T76,T77,T78,T79,T80,T81,T85,T89,T90,T91,T123,T124,T126,T128,T132,T134,T135,T136,T139"
LOOPS="H1:7,H2:6,H3:5-13,L1:8-13,L2:7,L3:9-11"

export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24   # quiet-machine baseline; contention cost is separate
echo "=== Gate 0b start $(date +%H:%M:%S) | OMP=$OMP_NUM_THREADS | $(nproc) cores ==="
echo "target : $IN/pd1_T.pdb"
echo "frame  : $RFAB/scripts/examples/example_inputs/hu-4D5-8_Fv.pdb"
echo "hotspots: 26"

PROJ="/home/rrobin711/Obsidian Personal/7- Projects/locksmith-antibody-hackathon"
export PYTHONPATH="$RFAB/src:${PYTHONPATH:-}"
cd "$RFAB"
/usr/bin/time -v "$V/bin/python" "$PROJ/scripts/65_rfdiff_cpu.py" \
    --config-name antibody \
    antibody.target_pdb="$IN/pd1_T.pdb" \
    antibody.framework_pdb="$RFAB/scripts/examples/example_inputs/hu-4D5-8_Fv.pdb" \
    inference.ckpt_override_path="$RFAB/weights/RFdiffusion_Ab.pt" \
    "ppi.hotspot_res=[$(echo $HOT | sed 's/,/,/g')]" \
    "antibody.design_loops=[$LOOPS]" \
    inference.num_designs=1 \
    inference.output_prefix="$OUT/gate0b" 2>&1
RC=$?; echo "=== Gate 0b end $(date +%H:%M:%S) rc=$RC ==="
