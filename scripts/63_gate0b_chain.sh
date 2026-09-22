#!/usr/bin/env bash
# Gate 0b: wait for weights, then MEASURE. No production run in this script --
# Gate 0b's whole job is to produce the numbers that decide the production run.
#
# Waits on the weights PID, never `pgrep -f` (self-matched a 4th time on 2026-09-21).
set -uo pipefail
RFAB="$HOME/.cache/rfantibody"
V="$HOME/.venvs/rfab-cpu"
OUT="runs/challenge2_cpu"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/heartbeat.log"; }

WPID="${1:-}"
if [ -n "$WPID" ]; then
  log "waiting on weights download pid $WPID"
  while kill -0 "$WPID" 2>/dev/null; do sleep 20; done
fi
log "weights stage ended; $(du -sh "$RFAB/weights" 2>/dev/null | cut -f1) on disk"

# B1-style artefact assertion on the weights themselves: exit code is not evidence.
$V/bin/python - <<'PY' 2>&1 | tee -a "$OUT/heartbeat.log"
import os, glob, torch
ok = True
for p in sorted(glob.glob(os.path.expanduser("~/.cache/rfantibody/weights/*.pt"))):
    mb = os.path.getsize(p) / 1e6
    try:
        sd = torch.load(p, map_location="cpu")
        n = len(sd.get("model_state_dict", sd)) if isinstance(sd, dict) else -1
        print(f"[ ok ] {os.path.basename(p):55s} {mb:8.1f} MB  {n} tensors")
    except Exception as e:
        ok = False
        print(f"[FAIL] {os.path.basename(p):55s} {mb:8.1f} MB  {type(e).__name__}: {e}")
print("WEIGHTS_OK" if ok else "WEIGHTS_BAD")
PY
log "gate0b weight check done"
