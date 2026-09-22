#!/usr/bin/env bash
# ===== LOCKSMITH CHALLENGE 2 PILOT — SINGLE PASTE BOOTSTRAP =====
# Paste this whole file into the pod terminal. It writes the three scripts and runs setup.
set -uo pipefail
mkdir -p /workspace/lock && cd /workspace/lock

cat > check_backbone.py <<'EOF_CHECK'
#!/usr/bin/env python3
"""B1 artefact + conditioning assertion for one RFdiffusion backbone.

Two jobs, and the second is the important one:

  1. Is this a STRUCTURE?  chains present, residue counts sane, no NaN, no duplicated
     coordinates, no chain collapsed to a point.  A file that exists and parses is not
     evidence -- `boltz predict` exits 0 after fatal errors, and the CPU equivalents are
     silent truncation and NaN output.

  2. Did the CONDITIONING do anything?  RFdiffusion is told to build against 26 hotspot
     residues on chain T.  `ab_pose.parse_hotspots` matches (chain, pdb_resnum) and
     SILENTLY SKIPS any hotspot it cannot find, so a numbering mistake yields zero
     hotspots and unconditioned generation wearing the target's name, with no error.
     This asks the only question that detects that: do the designed CDR loops actually
     make heavy-atom contact with those residues?

     This is deterministic and usable at n=1, which is why it is the PRIMARY instrument
     for conditioning rather than the conditioned-vs-unconditioned arm comparison.  That
     comparison is a two-sample test whose power at small n is poor, and this project
     published four underpowered nulls as findings on 2026-09-20.

Exit 0 = usable, 1 = reject (and it must NOT enter the pool).
Prints one JSON line so the heartbeat can aggregate without re-parsing PDBs.
"""
from __future__ import annotations

import json
import math
import sys

CUTOFF = 5.0          # angstrom, heavy-atom, same convention as metrics/interface.py


def main(path: str, hotspot_ordinals_csv: str) -> int:
    """hotspot_ordinals_csv: 0-based POSITIONS within the target chain, not residue
    numbers.  RFdiffusion RENUMBERS its output continuously across chains -- measured
    on gate0b_0.pdb: H=1-115, L=116-219, **T=220-332**, where the input PD-1 was
    numbered 31-143.  Matching on residue number therefore finds NOTHING and the check
    reports "zero hotspot contacts" for a perfectly good dock.  That false negative
    would have rejected every backbone in the run.  Ordinal positions survive any
    renumbering.
    """
    want = {int(x) for x in hotspot_ordinals_csv.split(",") if x.strip()}
    chains: dict[str, dict[int, list[tuple[float, float, float]]]] = {}
    order: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    loop_abs: list[int] = []
    for line in open(path):
        if line.startswith("REMARK PDBinfo-LABEL:"):
            parts = line.split()
            # The index is 1-indexed ABSOLUTE across the whole file (README), not
            # per-chain.  Reading it as per-chain silently mislocates every loop.
            if len(parts) >= 4 and parts[-1] in ("H1", "H2", "H3", "L1", "L2", "L3"):
                loop_abs.append(int(parts[-2]))
        elif line.startswith("ATOM") and line[76:78].strip() != "H":
            ch, num = line[21], int(line[22:26])
            key = (ch, num)
            if key not in seen:
                seen.add(key)
                order.append(key)
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            chains.setdefault(ch, {}).setdefault(num, []).append(xyz)

    out: dict[str, object] = {"file": path.rsplit("/", 1)[-1]}
    fail: list[str] = []
    for need in ("H", "L", "T"):
        if need not in chains:
            fail.append(f"chain {need} missing")
    if fail:
        out["ok"] = False; out["fail"] = fail; print(json.dumps(out)); return 1
    out["res"] = {c: len(r) for c, r in sorted(chains.items())}

    allxyz = [p for c in chains.values() for r in c.values() for p in r]
    if any(math.isnan(v) for p in allxyz for v in p):
        fail.append("NaN coordinates")
    if len(allxyz) != len({tuple(p) for p in allxyz}):
        fail.append("duplicate coordinates")
    for c, r in chains.items():
        pts = [p for v in r.values() for p in v]
        ext = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))
        if ext < 5.0:
            fail.append(f"chain {c} collapsed (extent {ext:.1f} A)")

    tnums = sorted(chains["T"])
    hot_nums = {tnums[i] for i in want if 0 <= i < len(tnums)}
    if len(hot_nums) != len(want):
        fail.append(f"only {len(hot_nums)}/{len(want)} hotspot positions exist in chain T")

    loop_pts = []
    for i in loop_abs:
        if 1 <= i <= len(order):
            c, n = order[i - 1]
            loop_pts.extend(chains[c][n])

    c2 = CUTOFF * CUTOFF
    def near(pts):
        return any((q[0]-p[0])**2 + (q[1]-p[1])**2 + (q[2]-p[2])**2 <= c2
                   for q in pts for p in loop_pts)

    touched = {n for n in hot_nums if near(chains["T"][n])}
    contacted = {n for n in tnums if near(chains["T"][n])}

    out["loop_residues"] = len(loop_abs)
    out["iface_residues"] = len(contacted)
    out["hotspots_contacted"] = len(touched)
    out["hotspots_total"] = len(want)
    out["frac_iface_on_epitope"] = round(len(touched) / len(contacted), 3) if contacted else 0.0

    if not loop_abs:
        fail.append("no CDR loop REMARKs -- cannot assess conditioning")
    elif not contacted:
        fail.append("loops contact NOTHING on the target: not a dock")
    elif not touched:
        fail.append("ZERO hotspot contacts: docked, but off the epitope")

    out["ok"] = not fail
    out["fail"] = fail
    print(json.dumps(out))
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
EOF_CHECK

cat > 00_setup.sh <<'EOF_SETUP'
#!/usr/bin/env bash
# RFantibody on a rented GPU pod. Run on a CUDA pod (T4 / L4 / A10 / A100 -- anything
# PRE-BLACKWELL). Tested logic, untested on a pod: no pod was available to the author.
#
# WHY THE NATIVE INSTALL WORKS HERE AND FAILED LOCALLY
# RFantibody's pyproject pins torch==2.3.* (cu118) and dgl-2.4.0+cu118. That wheel EXISTS
# and is what upstream ships. It cannot run on this project's local RTX 5070 Ti because
# that is sm_120 and needs CUDA >= 12.8, and the cu118 fatbinaries carry no PTX to JIT
# from. On any pre-Blackwell pod GPU, cu118 is native. So: no container needed, no
# dependency archaeology, no NVTX shim (a CUDA build has real NVTX).
set -euo pipefail
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

log "=== 0. PREFLIGHT: assert on arithmetic, never on is_available() ==="
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv || { log "FATAL: no GPU"; exit 1; }
CC=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d '.')
if [ "$CC" -ge 120 ]; then
  log "FATAL: compute capability sm_$CC. RFantibody's cu118 stack has no kernels for this"
  log "       and ships no PTX. This is the exact wall the local machine hit. Pick an"
  log "       older GPU (T4=75, A10=86, L4=89, A100=80)."
  exit 1
fi
log "compute capability sm_$CC -- within the cu118 range"

log "=== 1. INSTALL (upstream pins, unmodified) ==="
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
[ -d /workspace/lock/RFantibody ] || git clone https://github.com/RosettaCommons/RFantibody.git
cd RFantibody
uv sync
log "--- arithmetic check, not a flag check ---"
uv run python - <<'PY'
import numpy as np, torch, dgl, dgl.function as fn
assert torch.cuda.is_available(), "no CUDA visible to torch"
a, b = torch.randn(512, 512, device="cuda"), torch.randn(512, 512, device="cuda")
got = (a @ b).cpu().numpy(); exp = a.cpu().numpy() @ b.cpu().numpy()
assert np.allclose(got, exp, atol=1e-3), "GPU matmul disagrees with CPU"
assert torch.relu(torch.tensor([-1.0, 2.0], device="cuda")).cpu().tolist() == [0.0, 2.0]
g = dgl.graph(([0,1,2,3],[1,2,3,0]), num_nodes=4).to("cuda")
g.ndata["h"] = torch.tensor([[1.],[2.],[3.],[4.]], device="cuda")
g.update_all(fn.copy_u("h","m"), fn.sum("m","out"))
assert g.ndata["out"].squeeze().cpu().tolist() == [4.,1.,2.,3.], "DGL message-pass wrong"
print(f"[ ok ] torch {torch.__version__} | dgl {dgl.__version__} | arch {torch.cuda.get_device_name(0)}")
print("[ ok ] matmul, relu and DGL message-pass all correct ON GPU")
PY

log "=== 2. WEIGHTS ==="
bash include/download_weights.sh
uv run python - <<'PY'
import glob, os, torch
for p in sorted(glob.glob("weights/*.pt")):
    sd = torch.load(p, map_location="cpu")
    n = len(sd.get("model_state_dict", sd)) if isinstance(sd, dict) else -1
    print(f"[ ok ] {os.path.basename(p):55s} {os.path.getsize(p)/1e6:8.1f} MB  {n} tensors")
PY

log "=== 3. TARGET: rebuilt from the crystal, NOT copied ==="
# The correction this encodes: 5GGS holds TWO Fab copies (A/B and C/D) and TWO PD-1
# copies (Y/Z). Every planning document in this project said "5GGS chain C" for the
# target. Chain C is a SECOND PEMBROLIZUMAB HEAVY CHAIN. Aligning the 5IUS PD-L1
# footprint gives 90.2% to chain Y, 90.1% to Z and 15.4% to C -- while reporting
# "26/26 residues mapped" in ALL THREE cases. Coverage is not the check; identity is.
mkdir -p inputs
[ -f inputs/5ggs.pdb ] || curl -sSL -o inputs/5ggs.pdb https://files.rcsb.org/download/5GGS.pdb
uv run python - <<'PY'
import sys
FOOT = [64,66,68,70,73,74,75,76,77,78,79,80,81,85,89,90,91,
        123,124,126,128,132,134,135,136,139]
PD1_START = "PWNPPTFSPALLVVTEGDNATFTCSFSNTSESF"   # PD-1, not an antibody
AA3 = {"ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E","GLY":"G",
       "HIS":"H","ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F","PRO":"P","SER":"S",
       "THR":"T","TRP":"W","TYR":"Y","VAL":"V"}
keep, seen = [], {}
for line in open("inputs/5ggs.pdb"):
    if line.startswith("ATOM") and line[21] == "Z":          # <-- Z, the PD-1 copy
        keep.append(line[:21] + "T" + line[22:])             # relabel to target chain T
        seen.setdefault(int(line[22:26]), AA3.get(line[17:20].strip(), "X"))
if not keep:
    sys.exit("FATAL: chain Z absent from 5GGS")
seq = "".join(seen[k] for k in sorted(seen))
nums = set(seen)
# Three assertions, each of which alone would have caught the wrong-chain error:
assert 105 <= len(nums) <= 125, f"target is {len(nums)} residues -- PD-1 is ~113, a heavy chain is ~219"
assert seq.startswith(PD1_START[:20]), f"target does not look like PD-1: {seq[:25]}"
missing = [r for r in FOOT if r not in nums]
assert not missing, f"footprint residues unresolved: {missing}"
open("inputs/pd1_T.pdb", "w").writelines(keep + ["TER\n", "END\n"])
open("inputs/hotspots.txt", "w").write(",".join(f"T{r}" for r in FOOT))
print(f"[ ok ] target: {len(nums)} residues, numbering {min(nums)}-{max(nums)}")
print(f"[ ok ] sequence starts {seq[:30]} (PD-1)")
print(f"[ ok ] all {len(FOOT)} PD-L1-footprint hotspots resolve")
PY
cp scripts/examples/example_inputs/hu-4D5-8_Fv.pdb inputs/framework.pdb
log "=== SETUP COMPLETE -- run pod/01_run.sh next ==="
EOF_SETUP

cat > 01_run.sh <<'EOF_RUN'
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

RFAB="${RFAB:-/workspace/lock/RFantibody}"
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
  echo "$(python3 /workspace/lock/check_backbone.py "${OUT}_0.pdb" "$ORD" 2>/dev/null || echo '{}')" \
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
EOF_RUN

chmod +x 00_setup.sh 01_run.sh
echo
echo "=== scripts written to /workspace/lock ==="
ls -la /workspace/lock
echo
echo "Now run:  cd /workspace/lock && bash 00_setup.sh 2>&1 | tee setup.log"
