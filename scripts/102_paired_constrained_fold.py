#!/usr/bin/env python3
"""Fold the constrained sequences on the SAME backbones, for a paired comparison.

Pre-registered in `results/prereg_2026-09-23_constrained_paired.md`. Identical pipeline to
the re-screen in every respect -- `pd1_123_handbook.csv`, recycling 10, 5 diffusion
samples, seed 1, same driver -- so the only thing that differs between a constrained
sequence and its unconstrained partner is the §9.2 constraint applied at design time.
"""
from __future__ import annotations

import json, time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold

OUT = Path("runs/constrained_fold")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
RECYCLING, SAMPLES, SEED = 10, 5, 1


def main() -> int:
    y = [r for r in json.loads(Path("runs/redesign_yield/yield.json").read_text())
         if r["clean"]]
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    scored = json.loads(Path("runs/challenge2_rescreen/scores.json").read_text())
    paired_bb = {x["design_id"].split("_dldesign_")[0] for x in scored}

    OUT.mkdir(parents=True, exist_ok=True)
    log = json.loads((OUT / "fold_log.json").read_text()) if (OUT / "fold_log.json").exists() else {}
    # paired backbones first: if the run is cut short, the paired test still completes
    y.sort(key=lambda r: (r["backbone"] not in paired_bb, r["backbone"]))
    print(f"{len(y)} constrained sequences; "
          f"{sum(1 for r in y if r['backbone'] in paired_bb)} have an unconstrained "
          f"partner (paired arm), {sum(1 for r in y if r['backbone'] not in paired_bb)} "
          f"do not (exploratory)\n", flush=True)

    for i, r in enumerate(y, 1):
        label = f"cf_{r['backbone']}"
        pred = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(pred, label, n_models=SAMPLES):
            print(f"[{i}/{len(y)}] {label:<14} already folded", flush=True)
            continue
        arm = "paired" if r["backbone"] in paired_bb else "exploratory"
        print(f"[{i}/{len(y)}] {label:<14} {arm:<12} (clean at attempt {r['attempt']}) ...",
              end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, r["heavy"], r["light"], ag, out_root=OUT, antigen_msa=MSA,
                 seed=SEED, diffusion_samples=SAMPLES, recycling_steps=RECYCLING,
                 timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1),
                          "backbone": r["backbone"], "arm": arm, "attempt": r["attempt"]}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                                   # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300], "backbone": r["backbone"]}
            print(f"FAILED: {str(e)[:170]}", flush=True)
        (OUT / "fold_log.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
