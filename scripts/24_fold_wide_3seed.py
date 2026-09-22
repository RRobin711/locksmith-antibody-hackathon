#!/usr/bin/env python3
"""Fold the 40-design pool on 3 Boltz seeds each. No gating, no shortlisting.

Shortlisting before the ensemble↔quality correlation is measured would restrict
the range of the very variable under test -- the error that has bitten this
project twice (G1c's Fv screen, and the reliability estimate quoted from a
wide-range panel). Gating would also reduce nothing: 20/20 of the baseline
cleared every gate.

Reuses folds already on disk: the 20 baseline designs have Boltz seed 1, and 8 of
those have seeds 2 and 3 from the re-seed run. Resumable.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

POOL = Path("designs/wide_mpnn/designs.json")
OUT = Path("runs/designs_wide")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEEDS = (1, 2, 3)

# folds already on disk from earlier runs
PRIOR = [Path("runs/designs_baseline/index.jsonl"), Path("runs/designs_reseed/index.jsonl")]


def existing() -> dict[tuple[str, int], dict]:
    have = {}
    for p in PRIOR:
        if not p.exists():
            continue
        for l in p.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if not r.get("ok"):
                continue
            seed = r.get("seed", 1)
            have[(r["design_id"], seed)] = r
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ok"):
                have[(r["design_id"], r["seed"])] = r
    return have


def main() -> int:
    pool = json.loads(POOL.read_text())
    have = existing()
    todo = [(d, s) for d in pool for s in SEEDS if (d["design_id"], s) not in have]
    print(f"{len(pool)} designs x {len(SEEDS)} seeds = {len(pool)*len(SEEDS)} folds; "
          f"{len(have)} already on disk; {len(todo)} to run")
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    for d, seed in todo:
        did = d["design_id"]
        label = f"{did.replace('.', 'p')}__w{seed}"
        try:
            res = drv.fold(label, d["heavy"], d["light"], d["antigen"],
                           out_root=OUT, construct="fab", seed=seed, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            print(f"FAILED {label}: {e}", file=sys.stderr)
            rec = {"design_id": did, "label": label, "seed": seed, "ok": False,
                   "error": str(e)[:400]}
        else:
            print(f"  {label}: {res.seconds:.0f}s")
            rec = {"design_id": did, "label": label, "seed": seed, "ok": True,
                   "pdb": str(res.pdb), "pae": str(res.pae), "plddt": str(res.plddt),
                   "seconds": res.seconds}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
