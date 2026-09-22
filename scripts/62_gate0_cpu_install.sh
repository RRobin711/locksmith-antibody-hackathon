#!/usr/bin/env bash
# Gate 0-CPU: build an ISOLATED CPU-only environment for RFantibody.
#
# HARD REQUIREMENT, from reading the code rather than assuming:
#   RFdiffusion (model_runners.py:48-52), ProteinMPNN (proteinmpnn_interface_design.py:85-90)
#   and RF2 (rf2_predict.py:32) all branch on `torch.cuda.is_available()`.
#   On 2026-09-20 that call returned True in two environments where every kernel
#   failed.  So this venv must carry a CPU-ONLY torch build, where is_available()
#   is False by construction.  A CUDA-enabled torch here takes the GPU branch and dies.
#
# Nothing here touches ~/.venvs/locksmith.  00_doctor.py is run at the end as the gate.
set -uo pipefail
RFAB="$HOME/.cache/rfantibody"
VENV="$HOME/.venvs/rfab-cpu"
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "=== Gate 0-CPU install ==="
rm -rf "$VENV"
uv venv "$VENV" --python 3.10 2>&1 | tail -2 || { log "FATAL: venv creation failed"; exit 1; }
export VIRTUAL_ENV="$VENV"

log "--- torch 2.3.x CPU-only ---"
uv pip install --python "$VENV/bin/python" \
  --index-url https://download.pytorch.org/whl/cpu \
  "torch==2.3.1" "torchvision==0.18.1" 2>&1 | tail -3

log "--- runtime deps (cuda-python==11.8 pin deliberately NOT installed) ---"
uv pip install --python "$VENV/bin/python" \
  "numpy<2" hydra-core icecream opt-einsum "biotite>=0.38.0" e3nn \
  pyrsistent "click>=8.0.0" pandas 2>&1 | tail -3

log "--- DGL (CPU); PyPI first, DGL's own index as fallback ---"
uv pip install --python "$VENV/bin/python" dgl 2>&1 | tail -3
if ! "$VENV/bin/python" -c "import dgl" 2>/dev/null; then
  log "PyPI dgl unusable; trying DGL wheel index"
  uv pip install --python "$VENV/bin/python" dgl \
    -f https://data.dgl.ai/wheels/torch-2.3/repo.html 2>&1 | tail -3
fi

log "--- rfantibody itself, --no-deps (its pins are the thing we are routing around) ---"
uv pip install --python "$VENV/bin/python" --no-deps -e "$RFAB" 2>&1 | tail -3

log "--- installed versions ---"
"$VENV/bin/python" - <<'PY'
import importlib
for m in ("torch", "dgl", "e3nn", "numpy", "hydra", "biotite"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m:10s} {getattr(mod,'__version__','?')}")
    except Exception as e:
        print(f"  {m:10s} IMPORT FAILED: {type(e).__name__}: {e}")
import torch
print(f"  torch.version.cuda = {torch.version.cuda}  (None = CPU-only build, which is what we need)")
print(f"  torch.cuda.is_available() = {torch.cuda.is_available()}  (must be False)")
PY

log "--- THE GATE: did the working environment survive? ---"
cd "/home/rrobin711/Obsidian Personal/7- Projects/locksmith-antibody-hackathon"
~/.venvs/locksmith/bin/python scripts/00_doctor.py 2>&1 | tail -25
log "doctor exit=$?"
log "=== install stage complete ==="
