#!/usr/bin/env python3
"""Re-screen all 30 Challenge 2 designs with an antigen alignment that Boltz actually uses.

WHY. Every previous Challenge 2 fold paired the 123-residue antigen with a cached
alignment whose query is 113 residues. Boltz compares lengths, discards the alignment and
folds the antigen single-sequence -- announcing it only on a stdout stream this project
captured and threw away. The 2x2 in `results/msa_silently_discarded.md` measures what that
was worth: the design that "cleared" scores ipSAE **0.773 without an alignment and 0.012
with one**, and the same holds for the pre-fix baseline, so the effect is the alignment
rather than any mutation.

The screen that produced "1 of 30 clears" therefore ranked 30 designs under a condition
that flatters all of them. This re-runs it under the corrected one.

WHAT IS HELD FIXED. Everything except the alignment: same 30 sequences, same 123-residue
handbook antigen, same `recycling_steps=10`, same `diffusion_samples=5`, same seed, same
driver. The alignment is `data/msa_cache/pd1_123_handbook.csv`, built once from a matched
server query so all 30 designs see an IDENTICAL alignment -- re-querying per design would
put alignment drift straight into the ranking.

ORDER. Designs are folded best-first **by the old ranking**, purely so that the earliest
folds are the most informative if the run is stopped. The old ranking carries little
information about the new one -- it was produced in the flattering condition -- and no
conclusion is drawn from position in it.

EXPECTATION, RECORDED BEFORE RUNNING: probably **0 of 30**. The best design collapses to
0.012 with an alignment and the other 29 sat at <=0.331 without one. A null here is the
expected result, not a surprise, and would say the backbones do not dock under a correct
fold -- which no amount of re-scoring can repair, only re-generation.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold

OUT = Path("runs/challenge2_rescreen")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
DESIGNS = Path("runs/challenge2_fold_r10/designs.json")
OLD_SCORES = Path("runs/challenge2_fold_r10/scores.jsonl")
RECYCLING = 10
SAMPLES = 5


def main() -> int:
    limit = None
    for a in sys.argv[1:]:
        if a.startswith("--limit"):
            limit = int(a.split("=", 1)[1])

    designs = {d["design_id"]: d for d in json.loads(DESIGNS.read_text())}
    old = {}
    if OLD_SCORES.exists():
        for line in OLD_SCORES.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("design_id"):
                    old[r["design_id"]] = r.get("ipsae") or 0.0
    order = sorted(designs, key=lambda k: -old.get(k, 0.0))
    if limit:
        order = order[:limit]

    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / "fold_log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}

    print(f"{len(order)} designs, antigen alignment {MSA.name}, "
          f"recycling {RECYCLING}, {SAMPLES} diffusion samples\n", flush=True)

    for i, did in enumerate(order, 1):
        d = designs[did]
        label = f"rs_{did}"
        pred = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(pred, label, n_models=SAMPLES):
            print(f"[{i}/{len(order)}] {did:<22} already folded", flush=True)
            continue
        print(f"[{i}/{len(order)}] {did:<22} (old ipSAE {old.get(did, 0):.3f}) ...",
              end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, d["heavy"], d["light"], d["antigen"], out_root=OUT,
                 antigen_msa=MSA, seed=1, diffusion_samples=SAMPLES,
                 recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1),
                          "design_id": did, "old_ipsae": old.get(did)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300], "design_id": did}
            print(f"FAILED: {str(e)[:170]}", flush=True)
        log_path.write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
