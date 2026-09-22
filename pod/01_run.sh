#!/usr/bin/env bash
# PILOT BLOCK ONLY. This script deliberately does NOT run production.
#
# It produces exactly two numbers, and N is set from them afterwards (prereg 10.2):
#   1. per-backbone wall-clock on this GPU  -> sizes N against the budget
#   2. ICC of interaction_pae across backbones -> decides the SELECTION RULE (prereg 10.1)
#
# Why a pilot at all: the 5-8 min/backbone figure is a BRACKET, and the last bracketed
# figure in this project (RF2 at "4 min/sequence") measured 7.1 -- 1.75x off. Committing
# N before measuring would repeat that error knowingly.
#
# k=10 backbones x m=3 sequences. At df=(9,20) the between-backbone F_crit(0.05)=2.39,
# i.e. this block DETECTS ICC >= ~0.32. Anything below is not "no signal" -- it is "no
# signal larger than 0.32 detectable at k=10". Stated before the run, per standing rule.
set -uo pipefail

RFAB="${RFAB:-$HOME/RFantibody}"
WORK="${WORK:-/workspace/c2}"          # /workspace = VOLUME disk, survives a pod stop.
                                       # Container disk is erased on stop -- never write here.
K=10; M=3; RECYCLES=10
HOT=$(cat "$RFAB/inputs/hotspots.txt")
LOOPS="H1:7,H2:6,H3:5-13,L1:8-13,L2:7,L3:9-11"
ORD="33,35,37,39,42,43,44,45,46,47,48,49,50,54,58,59,60,92,93,95,97,101,103,104,105,108"

mkdir -p "$WORK"/{bb,seq,rf2,logs}
HB="$WORK/heartbeat.log"
log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$HB"; }

log "=== PILOT BLOCK: k=$K backbones x m=$M sequences, $RECYCLES recycles ==="
log "target=$RFAB/inputs/pd1_T.pdb  hotspots=26  work=$WORK"

# ---------------------------------------------------------------------------
# 1. BACKBONES, one invocation per backbone so each is separately timed and
#    separately resumable.  Resume keys on the ARTEFACT, never on a process
#    pattern: `pgrep -f` matched a stale shell's argv five times in this project,
#    costing 2h39m and 1h22m of idle hardware.  A file on disk is the signal.
# ---------------------------------------------------------------------------
for i in $(seq 1 $K); do
  OUT="$WORK/bb/bb_${i}"
  if [ -f "${OUT}_0.pdb" ]; then log "bb_$i: already on disk, skipping"; continue; fi
  S=$(date +%s)
  cd "$RFAB"
  uv run python scripts/rfdiffusion_inference.py --config-name antibody \
      antibody.target_pdb="$RFAB/inputs/pd1_T.pdb" \
      antibody.framework_pdb="$RFAB/inputs/framework.pdb" \
      inference.ckpt_override_path="$RFAB/weights/RFdiffusion_Ab.pt" \
      "ppi.hotspot_res=[$HOT]" "antibody.design_loops=[$LOOPS]" \
      inference.num_designs=1 inference.output_prefix="$OUT" \
      inference.seed=$((1000 + i)) > "$WORK/logs/bb_$i.log" 2>&1
  D=$(( $(date +%s) - S ))
  # assert_artefacts: exit code is NOT evidence -- boltz exits 0 after fatal errors and
  # RFdiffusion's CPU failure modes are silent truncation and NaN output.
  if [ ! -f "${OUT}_0.pdb" ]; then log "bb_$i: FAILED after ${D}s, no artefact"; continue; fi
  HS=$(grep -c "as a hotspot" "$WORK/logs/bb_$i.log" || echo 0)
  [ "$HS" -eq 26 ] || log "bb_$i: WARNING only $HS/26 hotspots resolved (unmatched ones are SILENTLY ignored)"
  echo "$(python3 "${CHECK:-/workspace/lock/check_backbone.py}" "${OUT}_0.pdb" "$ORD" 2>/dev/null || echo '{}')" \
      | sed "s/^{/{\"backbone\":\"bb_$i\",\"sec\":$D,/" >> "$WORK/backbones.jsonl"
  log "bb_$i: ${D}s, hotspots_resolved=$HS"
done

# ---------------------------------------------------------------------------
# 2. SEQUENCES.  Backbone ID is stamped into every row HERE, at generation --
#    it cannot be reconstructed after aggregation, and every variance and rate
#    figure in the prereg depends on it.
# ---------------------------------------------------------------------------
log "=== ProteinMPNN: $M sequences per backbone ==="
S=$(date +%s)
cd "$RFAB"
uv run proteinmpnn -i "$WORK/bb" -o "$WORK/seq" -n $M -t 0.2 > "$WORK/logs/mpnn.log" 2>&1
log "mpnn: $(( $(date +%s) - S ))s, $(ls "$WORK/seq"/*.pdb 2>/dev/null | wc -l) designs"

# ---------------------------------------------------------------------------
# 3. RF2.  Scores are written as `SCORE` lines INSIDE each output pdb by the
#    directory path (model_runner.py:215); only --output-quiver strips them out.
# ---------------------------------------------------------------------------
log "=== RF2: $RECYCLES recycles ==="
S=$(date +%s)
uv run rf2 -i "$WORK/seq" -o "$WORK/rf2" -r $RECYCLES > "$WORK/logs/rf2.log" 2>&1
RF2SEC=$(( $(date +%s) - S ))
log "rf2: ${RF2SEC}s for $(ls "$WORK/rf2"/*_best.pdb 2>/dev/null | wc -l) designs"

# ---------------------------------------------------------------------------
# 4. THE TWO NUMBERS.
# ---------------------------------------------------------------------------
log "=== analysis ==="
python3 - "$WORK" "$ORD" <<'PY' | tee -a "$HB"
import glob, json, os, statistics as st, sys
work, ord_csv = sys.argv[1], sys.argv[2]

bb = [json.loads(l) for l in open(f"{work}/backbones.jsonl")] if os.path.exists(f"{work}/backbones.jsonl") else []
if bb:
    secs = [b["sec"] for b in bb]
    print(f"\nBACKBONE WALL-CLOCK  n={len(secs)}  mean {st.mean(secs)/60:.2f} min  "
          f"median {st.median(secs)/60:.2f}  sd {st.pstdev(secs)/60:.2f}")
    hs = [b.get("hotspots_contacted") for b in bb if b.get("hotspots_contacted") is not None]
    fr = [b.get("frac_iface_on_epitope") for b in bb if b.get("frac_iface_on_epitope") is not None]
    if hs:
        print(f"CONDITIONING         hotspots contacted mean {st.mean(hs):.1f}/26 "
              f"(min {min(hs)}, max {max(hs)}); frac_iface_on_epitope mean {st.mean(fr):.3f}")
        if max(hs) == 0:
            print("  ** ZERO hotspot contacts on EVERY backbone -- this run is unconditioned. STOP. **")

# interaction_pae per design, grouped by backbone -> one-way ICC
groups: dict[str, list[float]] = {}
for f in sorted(glob.glob(f"{work}/rf2/*_best.pdb")):
    val = None
    for line in open(f):
        if line.startswith("SCORE interaction_pae:"):
            val = float(line.split(":")[1]); break
        if line.startswith("ATOM"): break
    if val is None: continue
    key = os.path.basename(f).split("_dldesign")[0]
    groups.setdefault(key, []).append(val)

groups = {k: v for k, v in groups.items() if len(v) >= 2}
k = len(groups); print(f"\nINTERACTION_PAE      {k} backbones with >=2 designs")
if k >= 2:
    allv = [v for vs in groups.values() for v in vs]
    m = st.mean(len(v) for v in groups.values())
    grand = st.mean(allv)
    ms_b = sum(len(v) * (st.mean(v) - grand) ** 2 for v in groups.values()) / (k - 1)
    within = [(x - st.mean(v)) ** 2 for v in groups.values() for x in v]
    dfw = len(allv) - k
    ms_w = sum(within) / dfw if dfw else 0.0
    icc = (ms_b - ms_w) / (ms_b + (m - 1) * ms_w) if (ms_b + (m - 1) * ms_w) else 0.0
    icc = max(0.0, icc)
    print(f"  range {min(allv):.2f}-{max(allv):.2f} | MS_between {ms_b:.3f} MS_within {ms_w:.3f}"
          f" | F={ms_b/ms_w if ms_w else float('inf'):.2f} (df={k-1},{dfw})")
    print(f"  ICC = {icc:.3f}")
    print(f"\n  SELECTION RULE (pre-registered, prereg 10.1):")
    if icc >= 0.32:
        print(f"  -> ICC {icc:.3f} >= 0.32: PRIMARY KEY = interaction_pae, per-backbone MEAN, lower better.")
    else:
        print(f"  -> ICC {icc:.3f} < 0.32: NOT 'no signal' -- 'no signal larger than 0.32 at k={k}'.")
        print(f"     FALL BACK to hotspot contact count; tie-break frac_iface_on_epitope.")
print("\nN IS NOT SET BY THIS SCRIPT. Set it from the two numbers above (prereg 10.2):")
print("  default N=30; revise up only if ICC>=0.32 or the gate pass rate is very low.")
PY
log "=== PILOT COMPLETE -- stopping deliberately. Do not start production from this script. ==="
