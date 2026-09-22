#!/usr/bin/env bash
# Measure the UNMEASURED term: MPNN and RF2 cost per sequence on CPU.
# The 20-backbone budget is ~12 h or ~24 h depending on this number alone.
set -uo pipefail
V="$HOME/.venvs/rfab-cpu"; RFAB="$HOME/.cache/rfantibody"
PROJ="/home/rrobin711/Obsidian Personal/7- Projects/locksmith-antibody-hackathon"
GB="$RFAB/gate0b"; MP="$RFAB/gate0b_mpnn"; R2="$RFAB/gate0b_rf2"
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
export PYTHONPATH="$RFAB/src:${PYTHONPATH:-}"
# RFantibody's CLI shells out to a BARE `python`; invoking the venv interpreter by
# full path does not put it on PATH, so that subprocess dies with FileNotFoundError.
export PATH="$V/bin:$PATH"
mkdir -p "$MP" "$R2"

# NO WAIT LOOP.  The first version of this script used
#     while pgrep -f "65_rfdiff_cpu"; do sleep 20; done
# which matched a STALE HARNESS SHELL whose argv still contained that string
# (it was created by a heredoc inside `bash -c`), and idled 1h22m on 2026-09-21
# waiting for a process that had exited at 09:58:38.  Fifth instance of this bug.
# The artefact on disk is the completion signal -- not a process pattern.
if [ ! -f "$GB/gate0b_0.pdb" ]; then
  echo "FATAL: $GB/gate0b_0.pdb missing -- backbone not complete"; exit 1
fi
echo "backbone artefact present: $(ls -la "$GB/gate0b_0.pdb" | awk '{print $5" bytes"}')"

echo; echo "=== B1 artefact check on the backbone (exit code is not evidence) ==="
ls -la "$GB" || true
"$V/bin/python" - <<'PY'
import glob, os, sys
import numpy as np
pdbs = sorted(glob.glob(os.path.expanduser("~/.cache/rfantibody/gate0b/*.pdb")))
if not pdbs:
    print("NO BACKBONE PRODUCED"); sys.exit(1)
for p in pdbs:
    xyz, chains = [], {}
    for line in open(p):
        if line.startswith("ATOM"):
            chains.setdefault(line[21], set()).add(int(line[22:26]))
            xyz.append([float(line[30+8*i:38+8*i]) for i in range(3)])
    a = np.array(xyz)
    print(f"{os.path.basename(p)}: {len(a)} atoms | chains " +
          ", ".join(f"{c}:{len(r)}res" for c, r in sorted(chains.items())))
    print(f"   NaN: {np.isnan(a).any()} | dup coords: {len(a) - len(np.unique(a, axis=0))}"
          f" | extent {a.max(0) - a.min(0)}")
PY

echo; echo "=== ProteinMPNN: 4 sequences, timed ==="
cd "$RFAB"
S=$(date +%s)
/usr/bin/time -v "$V/bin/python" "$PROJ/scripts/66_cpu_run.py" proteinmpnn \
    -i "$GB" -o "$MP" -n 4 -t 0.2 2>&1 | grep -viE "^ic\||Timestep" | tail -25
echo "MPNN_WALL_SEC=$(( $(date +%s) - S ))"
ls -la "$MP" | head

echo; echo "=== RF2: one design, 10 recycles (the default), timed ==="
S=$(date +%s)
/usr/bin/time -v "$V/bin/python" "$PROJ/scripts/66_cpu_run.py" rf2 \
    -i "$MP" -o "$R2" -r 10 2>&1 | grep -viE "^ic\|" | tail -30
echo "RF2_WALL_SEC=$(( $(date +%s) - S ))"
ls -la "$R2" | head
echo "=== done $(date +%H:%M:%S) ==="
