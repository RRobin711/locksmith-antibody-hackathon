#!/usr/bin/env bash
# The decoy-patch control, run LOCALLY ON CPU. No pod, no rental, $0.
#
# WHY LOCAL IS POSSIBLE. RFantibody cannot use this machine's RTX 5070 Ti (sm_120): it
# pins torch==2.3.*, PyPI's DGL ships no matching ABI, and those wheels carry no PTX, so
# nothing JITs forward. That is a GPU-path problem only. The CPU path was built and
# measured on 2026-09-21 (results/gate0_cpu.md, Gate 0b PASS): torch 2.2.1+cpu, dgl 2.1.0,
# e3nn 0.6.0 in ~/.venvs/rfab-cpu, 19.5 min of diffusion per backbone (23.37 s/step x 50)
# plus a ~4 min one-off model load.
#
# Renting was never required for THIS block. The decoy control measures targeting on
# BACKBONES (scripts/70, 94, 95 all parse the pdb), so no ProteinMPNN and no RF2.
#
# TWO CORRECTIONS after the first attempt failed 18/18 in 34 seconds (2026-09-28):
#
#   1. `inference.seed` DOES NOT EXIST in this RFantibody version. The pod script passes
#      it; Hydra here rejects it with "Key 'seed' is not in struct" before doing any work.
#      Confirmed: no `seed` key in scripts/config/inference/{base,antibody}.yaml and no
#      reference in src/rfantibody/rfdiffusion/inference/. So designs are varied the way
#      this version supports -- ONE invocation with `inference.num_designs=K`, which also
#      loads the 4-minute model once instead of K times (~68 min saved at K=18).
#      `inference.deterministic` defaults to False, so the K draws are independent.
#   2. The first version LOGGED each failure and still EXITED 0, so a run in which nothing
#      whatsoever succeeded reported success. That is this project's own "a program that
#      runs without error is not evidence it did what you intended", written by the person
#      who keeps citing it. It now exits non-zero unless K artefacts exist.
#
# Resume: `inference.design_startnum` continues from however many .pdb files are already
# on disk. Keyed on ARTEFACTS, never on a process pattern -- `pgrep -f` self-matched five
# times in this project, costing 2h39m and 1h22m of idle hardware.
set -uo pipefail

RFAB="$HOME/.cache/rfantibody"
V="$HOME/.venvs/rfab-cpu"
OUT="${OUT:-runs/challenge2_decoy}"
K="${K:-18}"
# PARALLEL MODE (added 2026-09-28 after measuring the serial run): one worker reached
# only 1140% CPU on a 24-core box -- load average 11.35, so ~12 cores sat idle for the
# whole run. RFdiffusion's own intra-op parallelism plateaus well short of the machine.
# Three workers on DISJOINT design ranges, 8 threads each, use all 24 and cost 3 x 2.2 GB
# of RSS against 8 GB available.
#   START  first design index this worker owns (maps to inference.design_startnum)
#   NUM    how many it makes  (maps to inference.num_designs)
#   THREADS torch intra-op threads; unset = torch grabs everything and workers contend
# Ranges must not overlap: two workers writing the same dec_N.pdb is a silent corruption,
# not an error.
START="${START:-}"
NUM="${NUM:-}"
THREADS="${THREADS:-}"
if [ -n "$THREADS" ]; then
  export OMP_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS" TORCH_NUM_THREADS="$THREADS"
fi
# Decoy hotspots from scripts/95_decoy_patch_control.py: 26 residues on the far face of
# PD-1, RMS spread 10.15 A against the epitope's 9.85, ZERO overlap, 165.9 deg apart, and
# the 18 existing conditioned backbones score 0.000 on this patch.
HOT="T34,T36,T37,T38,T39,T40,T41,T43,T49,T51,T53,T55,T95,T96,T97,T98,T99,T100,T101,T102,T103,T104,T105,T107,T109,T141"
LOOPS="H1:7,H2:6,H3:5-13,L1:8-13,L2:7,L3:9-11"

mkdir -p "$OUT"/{bb,logs}
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/heartbeat.log"; }

if [ -n "$START" ] && [ -n "$NUM" ]; then
  HAVE="$START"; TODO="$NUM"; TAG="w${START}"
else
  HAVE=$(ls "$OUT"/bb/dec_*.pdb 2>/dev/null | wc -l)
  if [ "$HAVE" -ge "$K" ]; then log "already have $HAVE/$K backbones, nothing to do"; exit 0; fi
  TODO=$(( K - HAVE )); TAG="serial"
fi

log "=== DECOY CONTROL (CPU): $TODO backbone(s), $HAVE already on disk ==="
log "target=$RFAB/inputs/pd1_T.pdb  decoy hotspots=26  out=$OUT/bb"
log "expect ~4 min model load + ~19.5 min/backbone => ~$(( 4 + 20 * TODO )) min"

S=$(date +%s)
"$V/bin/python" scripts/65_rfdiff_cpu.py --config-name antibody \
    antibody.target_pdb="$RFAB/inputs/pd1_T.pdb" \
    antibody.framework_pdb="$RFAB/scripts/examples/example_inputs/hu-4D5-8_Fv.pdb" \
    inference.ckpt_override_path="$RFAB/weights/RFdiffusion_Ab.pt" \
    "ppi.hotspot_res=[$HOT]" "antibody.design_loops=[$LOOPS]" \
    inference.num_designs="$TODO" inference.design_startnum="$HAVE" \
    inference.output_prefix="$PWD/$OUT/bb/dec" > "$OUT/logs/run_${TAG}_$(date +%H%M%S).log" 2>&1
RC=$?
D=$(( $(date +%s) - S ))

GOT=$(ls "$OUT"/bb/dec_*.pdb 2>/dev/null | wc -l)
LAST=$(ls -t "$OUT"/logs/run_${TAG}_*.log | head -1)
# `26/26 resolved` proves the tool RECEIVED the conditioning, not that it changed the
# output -- but unmatched hotspots are SILENTLY ignored, so assert the count.
HS=$(grep -c "as a hotspot" "$LAST" 2>/dev/null || true)
log "rfdiffusion exit=$RC, ${D}s ($((D/60)) min), artefacts now $GOT/$K, hotspot lines=${HS:-0}"

# Exit code is NOT evidence: RFdiffusion's CPU failure modes are silent truncation and NaN
# output, and the first version of this script exited 0 having produced nothing.
NEED="$K"; [ "$TAG" != "serial" ] && NEED=$(( START + NUM ))
if [ "$GOT" -lt "$NEED" ]; then
  log "[$TAG] INCOMPLETE: $GOT on disk, needed $NEED. Last error lines:"
  grep -iE "error|not in struct|Traceback|Killed|OOM" "$LAST" | tail -5 | tee -a "$OUT/heartbeat.log"
  exit 1
fi
log "=== DONE: $GOT/$K backbones ==="
log "Next: uv run python scripts/95_decoy_patch_control.py --analyse $OUT/bb"
