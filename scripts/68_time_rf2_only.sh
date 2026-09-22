#!/usr/bin/env bash
set -uo pipefail
V="$HOME/.venvs/rfab-cpu"; RFAB="$HOME/.cache/rfantibody"
PROJ="/home/rrobin711/Obsidian Personal/7- Projects/locksmith-antibody-hackathon"
MP="$RFAB/gate0b_mpnn"; R2="$RFAB/gate0b_rf2"
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
export PYTHONPATH="$RFAB/src:${PYTHONPATH:-}"
export PATH="$V/bin:$PATH"
mkdir -p "$R2"
IN=$( [ -n "$(ls -A "$MP" 2>/dev/null)" ] && echo "$MP" || echo "$RFAB/gate0b" )
echo "=== RF2 on $IN, 10 recycles, started $(date +%H:%M:%S) ==="
S=$(date +%s)
/usr/bin/time -v "$V/bin/python" "$PROJ/scripts/66_cpu_run.py" rf2 -i "$IN" -o "$R2" -r 10 2>&1 \
  | grep -viE "^ic\|" | tail -35
echo "RF2_WALL_SEC=$(( $(date +%s) - S ))"
ls -la "$R2" | head
echo "=== done $(date +%H:%M:%S) ==="
