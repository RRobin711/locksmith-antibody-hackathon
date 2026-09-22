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
[ -d RFantibody ] || git clone https://github.com/RosettaCommons/RFantibody.git
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
