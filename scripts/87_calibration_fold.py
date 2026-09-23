#!/usr/bin/env python3
"""Fold the calibration panel through the identical pipeline used for our own designs.

Same driver, same flags, same construct (Fv + antigen), same sampling depth. The ONLY
differences from a design fold are forced by the panel itself:

  * `antigen_msa=None` -> `--use_msa_server`, because every complex has a different
    antigen and there is no cached alignment for any of them. The antibody chains still
    carry `empty`, exactly as for our designs, so the *protocol* is unchanged: antigen
    aligned, antibody not. Disclosure is a non-issue here -- every sequence in the panel
    is already public in the PDB. (For a novel design it would not be, which is why the
    PD-1 alignment is cached.)

SAMPLING DEPTH. `recycling_steps=10` and `diffusion_samples=5`, both bought with
measurements on this project:

  * recycling 3 (the inherited default) does not give a noisy ranking, it gives a
    COMPRESSED one. At recycling 3, 15 of 30 designs scored ipSAE exactly 0.000 and the
    pool read as 0/30 viable; at recycling 10 one design moved 0.263 -> 0.864 while
    others moved sideways or down. A calibration panel folded under-converged would
    measure the sampler's floor, not the metric's distribution.
  * `diffusion_samples=1` reports an **argmax**, not a sample: Boltz orders its outputs by
    its own confidence, so `model_0` of one sample is the maximum of a distribution never
    drawn. Five samples cost almost nothing (2m54s vs ~2m measured) because the MSA, trunk
    and recycling are shared and only the diffusion head reruns. We keep all five so the
    panel reports a *spread* per complex, not a point.

RESUME KEYS ON THE ARTEFACT, NEVER ON A ROW EXISTING. This project once treated 239 error
rows as completed work because the resume check asked whether a row was present rather
than whether the fold produced a usable structure. `assert_artefacts` is the check.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from locksmith.fold import FoldFailed, fold_is_complete
from locksmith.fold.boltz import fold

PANEL = Path("runs/calibration/panel.json")
FOLDS = Path("runs/calibration/folds")
LOG = Path("runs/calibration/fold_log.json")
RECYCLING = 10
SAMPLES = 5


def label_for(x: dict) -> str:
    return f"cal_{x['arm']}_{x['pdb_id'].lower()}"


def already_done(label: str) -> bool:
    """True only if this fold left behind SAMPLES scorable models."""
    return fold_is_complete(
        FOLDS / label / f"boltz_results_{label}" / "predictions" / label,
        label, n_models=SAMPLES)


def main() -> int:
    panel = json.loads(PANEL.read_text())
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    if only:
        panel = [x for x in panel if x["pdb_id"].lower() in {o.lower() for o in only}]
    FOLDS.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG.read_text()) if LOG.exists() else {}

    todo = [x for x in panel if not already_done(label_for(x))]
    print(f"{len(panel)} in panel, {len(panel)-len(todo)} already folded, "
          f"{len(todo)} to do\n", flush=True)

    for i, x in enumerate(todo, 1):
        label = label_for(x)
        t0 = time.time()
        print(f"[{i}/{len(todo)}] {label}  {x['n_res']} res ...", end=" ", flush=True)
        try:
            r = fold(label, x["heavy"], x["light"], x["antigen"],
                     out_root=FOLDS, antigen_msa=None, seed=1,
                     diffusion_samples=SAMPLES, recycling_steps=RECYCLING,
                     timeout=5400)
            dt = time.time() - t0
            log[label] = {"ok": True, "seconds": round(dt, 1), "n_res": x["n_res"],
                          "arm": x["arm"], "pdb_id": x["pdb_id"]}
            print(f"ok in {dt/60:.1f} min", flush=True)
        except (FoldFailed, Exception) as e:                 # noqa: BLE001
            dt = time.time() - t0
            log[label] = {"ok": False, "seconds": round(dt, 1), "arm": x["arm"],
                          "pdb_id": x["pdb_id"], "error": str(e)[:300]}
            print(f"FAILED after {dt/60:.1f} min: {str(e)[:160]}", flush=True)
        LOG.write_text(json.dumps(log, indent=1))

    ok = sum(1 for v in log.values() if v.get("ok"))
    secs = [v["seconds"] for v in log.values() if v.get("ok")]
    print(f"\n{ok}/{len(log)} folds succeeded"
          + (f", median {sorted(secs)[len(secs)//2]/60:.1f} min each" if secs else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
