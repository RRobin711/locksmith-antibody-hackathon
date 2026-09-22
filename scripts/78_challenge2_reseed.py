#!/usr/bin/env python3
"""Can more sampling lift the best Challenge 2 designs from 0.372 toward the 0.60 gate?

THE OBJECTION THIS CLOSES. The 30 designs were folded at **one seed, 3 recycling steps**.
`0/30` is only a statement about the designs if it survives a more generous sample --
otherwise the honest verdict is "we did not look hard enough", and leaving that open
invites exactly the objection this project would raise against someone else.

DESIGN. The top 5 designs by single-seed ipSAE, each re-folded under three conditions:

    (seed 1, recycling 10)   isolates RECYCLING from seed -- same seed as the original
    (seed 2, recycling 10)   adds sampling
    (seed 3, recycling 10)

15 folds. This is a **bounded** test, not a campaign: it asks whether the gap is within
reach of sampling, not what the designs' true ipSAE is. The best design needs to move
**+0.228** to clear. For scale, the positive control (wild-type pembrolizumab Fv through
the identical pipeline) scores **0.842**.

Interpretation fixed in advance: if the best of 15 richer folds still sits below ~0.50,
the gap is not a sampling artefact and `0/30` stands as a property of the designs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.metrics import ipsae
from locksmith.types import Provenance, Structure

FOLD = Path("runs/challenge2_fold")
OUT = Path("runs/challenge2_reseed")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
RECYCLING = 10
SEEDS = (1, 2, 3)
TOP_N = 5


def main() -> int:
    cfg = load()
    c = cfg.conventions
    designs = {d["design_id"]: d for d in json.loads((FOLD / "designs.json").read_text())}
    rows = [json.loads(l) for l in (FOLD / "scores.jsonl").read_text().splitlines()
            if l.strip() and "ipsae" in json.loads(l)]
    rows.sort(key=lambda r: -r["ipsae"])
    top = rows[:TOP_N]
    base = {r["design_id"]: r["ipsae"] for r in top}
    print(f"re-folding the top {TOP_N} at recycling={RECYCLING}, seeds={SEEDS}", flush=True)
    for r in top:
        print(f"  {r['design_id']:<28} baseline ipSAE {r['ipsae']:.3f}", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if l.strip():
                j = json.loads(l)
                if "ipsae" in j:
                    done.add((j["design_id"], j["seed"]))

    for r in top:
        did = r["design_id"]
        d = designs[did]
        for seed in SEEDS:
            if (did, seed) in done:
                continue
            label = f"rs_{did}_s{seed}"
            try:
                res = drv.fold(label, d["heavy"], d["light"], d["antigen"],
                               out_root=OUT, construct="fv", seed=seed,
                               antigen_msa=PD1_MSA, recycling_steps=RECYCLING)
            except FoldFailed as e:
                print(f"  FAILED {label}: {str(e)[:160]}", file=sys.stderr, flush=True)
                rec = {"design_id": did, "seed": seed, "ok": False, "error": str(e)[:300]}
            else:
                st = Structure(pdb=res.pdb, provenance=Provenance.PREDICTION,
                               pae=res.pae, label=label)
                v = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                  dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
                rec = {"design_id": did, "seed": seed, "ok": True, "ipsae": v,
                       "recycling": RECYCLING, "seconds": res.seconds}
                print(f"  {did} seed {seed}: ipSAE {v:.3f} "
                      f"(baseline {base[did]:.3f}, {res.seconds:.0f}s)", flush=True)
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")

    got = [json.loads(l) for l in INDEX.read_text().splitlines()
           if l.strip() and json.loads(l).get("ok")]
    print("\n" + "=" * 64)
    if not got:
        print("no successful re-folds")
        return 1
    best = max(g["ipsae"] for g in got)
    print(f"{len(got)} richer folds (recycling {RECYCLING}, {len(SEEDS)} seeds)")
    print(f"best ipSAE anywhere : {best:.3f}   (single-seed baseline best 0.372)")
    print(f"gate                : 0.600")
    print(f"positive control    : 0.842  (wild-type pembrolizumab Fv, same pipeline)")
    print("=" * 64)
    if best >= 0.60:
        print("A DESIGN CLEARS under richer sampling. 0/30 was a sampling artefact -- "
              "re-score the full pool at these settings before any verdict.")
    elif best >= 0.50:
        print("Moved materially but still short. Ambiguous: report the range, do not "
              "call 0/30 settled.")
    else:
        print("The gap is NOT a sampling artefact. 0/30 stands as a property of the "
              "designs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
