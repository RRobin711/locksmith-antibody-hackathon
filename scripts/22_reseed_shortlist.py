#!/usr/bin/env python3
"""Re-fold the top-tier baseline designs on additional seeds.

WHY THE TOP TIER SPECIFICALLY. All 8 share final=87.5, so `final` cannot order
them and the DockQ tiebreaker does the whole job. Their median adjacent DockQ gap
is 0.011 against a measured Fab seed sd of 0.018 -- 0.61 sd -- so the prediction
going in is that this ordering is substantially noise. This run tests that.

Boltz-2 is a diffusion model: a different seed gives a genuinely different
structure, not merely a different confidence. So re-seeding is also sampling the
conformational ensemble, which is what scripts/23 reads out for CDR-H3.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

DESIGNS = Path("designs/baseline_mpnn/designs.json")
SHORT = Path("designs/baseline_mpnn/reseed_shortlist.json")
OUT = Path("runs/designs_reseed")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEEDS = (2, 3)


def main() -> int:
    meta = {r["design_id"]: r for r in json.loads(DESIGNS.read_text())}
    shortlist = json.loads(SHORT.read_text())
    done = set()
    if INDEX.exists():
        done = {json.loads(l)["label"] for l in INDEX.read_text().splitlines() if l.strip()}
    for did in shortlist:
        r = meta[did]
        for seed in SEEDS:
            label = f"{did.replace('.', 'p')}__s{seed}"
            if label in done:
                print(f"skip {label}"); continue
            try:
                res = drv.fold(label, r["heavy"], r["light"], r["antigen"],
                               out_root=OUT, construct="fab", seed=seed,
                               antigen_msa=PD1_MSA)
            except FoldFailed as e:
                print(f"FAILED {label}: {e}", file=sys.stderr)
                rec = {"design_id": did, "label": label, "seed": seed,
                       "ok": False, "error": str(e)[:400]}
            else:
                print(f"  {label}: {res.seconds:.0f}s")
                rec = {"design_id": did, "label": label, "seed": seed, "ok": True,
                       "pdb": str(res.pdb), "pae": str(res.pae),
                       "plddt": str(res.plddt), "seconds": res.seconds}
            INDEX.parent.mkdir(parents=True, exist_ok=True)
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
