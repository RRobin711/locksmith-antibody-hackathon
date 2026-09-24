#!/usr/bin/env python3
"""Serial baseline sampling the FOLD's own GPU memory, not the card total.

The first baseline reported a 6529 MiB peak, but that is `memory.used` for the whole card
and includes ~1042 MiB of desktop graphics (Xorg 450, gnome-shell 115, brave 303, zoom 75).
Subtracting that by hand is guesswork, because the desktop's footprint moves while a fold
runs. `--query-compute-apps=used_memory` gives each CUDA process's own allocation, which is
the quantity the concurrency arithmetic needs.

Sampled at 1 Hz: NVML refreshes internally at ~2 Hz on this card, so faster polling returns
duplicates and buys nothing but file size.
"""
from __future__ import annotations

import json, subprocess, sys, time
from pathlib import Path

OUT = Path("runs/determinism")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
LABEL = "clean_bb_8_0"
RECYCLING, SAMPLES, SEED = 10, 5, 1

SAMPLER = r"""
while true; do
  T=$(date +%s.%N)
  C=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null | tr '\n' ';')
  G=$(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits 2>/dev/null)
  R=$(ps -eo rss= --sort=-rss | head -40 | awk '{s+=$1} END{print s}')
  echo "$T|$C|$G|$R"
  sleep 1
done
"""


def main() -> int:
    from locksmith.fold import fold_is_complete
    from locksmith.fold.boltz import fold

    d = {r["backbone"]: r for r in json.loads(
        Path("runs/redesign_yield/yield.json").read_text()) if r["clean"]}["bb_8_0"]
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    OUT.mkdir(parents=True, exist_ok=True)
    pred = OUT / LABEL / f"boltz_results_{LABEL}" / "predictions" / LABEL
    if fold_is_complete(pred, LABEL, n_models=SAMPLES):
        print("clean baseline fold already present")
        return 0

    log = OUT / "clean_samples.txt"
    sampler = subprocess.Popen(["bash", "-c", SAMPLER], stdout=log.open("w"),
                               stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        fold(LABEL, d["heavy"], d["light"], ag, out_root=OUT, antigen_msa=MSA, seed=SEED,
             diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
    finally:
        elapsed = time.time() - t0
        sampler.terminate(); sampler.wait(timeout=10)

    proc_mem, card_mem, util, rss = [], [], [], []
    for line in log.read_text().splitlines():
        parts = line.split("|")
        if len(parts) < 4:
            continue
        procs = [p for p in parts[1].split(";") if p.strip()]
        tot = sum(int(p.split(",")[1]) for p in procs if "," in p)
        if procs:
            proc_mem.append(tot)
        g = parts[2].split(",")
        if len(g) == 2:
            card_mem.append(int(g[0])); util.append(int(g[1]))
        if parts[3].strip().isdigit():
            rss.append(int(parts[3]) // 1024)

    base = {"seconds": round(elapsed, 1), "samples": len(card_mem),
            "fold_gpu_mem_peak_MiB": max(proc_mem) if proc_mem else None,
            "fold_gpu_mem_mean_MiB": round(sum(proc_mem)/len(proc_mem)) if proc_mem else None,
            "card_total_peak_MiB": max(card_mem) if card_mem else None,
            "desktop_baseline_MiB": (min(card_mem) if card_mem else None),
            "gpu_util_mean": round(sum(util)/max(len(util),1), 1),
            "gpu_util_max": max(util) if util else None,
            "top40_rss_peak_MB": max(rss) if rss else None}
    (OUT / "clean_baseline.json").write_text(json.dumps(base, indent=1))
    print(f"wall-clock            {base['seconds']} s")
    print(f"FOLD's own GPU peak   {base['fold_gpu_mem_peak_MiB']} MiB   (mean {base['fold_gpu_mem_mean_MiB']})")
    print(f"card total peak       {base['card_total_peak_MiB']} MiB")
    print(f"desktop baseline      {base['desktop_baseline_MiB']} MiB  (card minimum during the run)")
    print(f"GPU utilisation       mean {base['gpu_util_mean']}%  max {base['gpu_util_max']}%")
    print(f"top-40 RSS peak       {base['top40_rss_peak_MB']} MB")
    cap = 12227
    p = base["fold_gpu_mem_peak_MiB"] or 0
    dk = base["desktop_baseline_MiB"] or 0
    for n in (2, 3):
        need = n * p + dk
        print(f"  {n} concurrent -> {need} MiB of {cap}  "
              f"({'FITS, headroom ' + str(cap-need) + ' MiB' if need < cap*0.9 else 'TOO TIGHT'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
