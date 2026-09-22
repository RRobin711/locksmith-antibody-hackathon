#!/usr/bin/env python3
"""Score every fold in runs/panel/index.jsonl: ipSAE + DockQ vs the 5GGS crystal.

Writes runs/panel/scores.jsonl (resumable -- already-scored labels are skipped).

ON WHAT DockQ MEANS HERE, WHICH IS NOT "CORRECTNESS"
----------------------------------------------------
For v00_wt (unmutated pembrolizumab) DockQ against 5GGS is a clean accuracy
measure: same molecule, known answer.

For a mutated variant it is NOT. The variant's true structure is unknown -- the
crystal is the structure of a *different molecule*. DockQ-vs-crystal therefore
measures **retention of the native binding mode**, and conflates two things:
  (a) prediction error, and
  (b) genuine structural change caused by the mutation, which is a real effect
      and not an error at all.
That is still the right quantity for Challenge 1, where the question is "does
this design still bind the way pembrolizumab binds" -- but it must not be
described as ground-truth accuracy for the mutants, and the regression of ipSAE
on it is "does confidence track retention of the native pose", not "does
confidence track correctness".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.metrics import dockq as dockq_m
from locksmith.metrics import ipsae as ipsae_m
from locksmith.types import Provenance, Structure

INDEX = Path("runs/panel/index.jsonl")
SCORES = Path("runs/panel/scores.jsonl")
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS crystal")


def scored() -> set[str]:
    if not SCORES.exists():
        return set()
    return {json.loads(l)["label"] for l in SCORES.read_text().splitlines() if l.strip()}


def main() -> int:
    if not INDEX.exists():
        print("no folds to score", file=sys.stderr)
        return 1
    have = scored()
    rows = [json.loads(l) for l in INDEX.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r.get("ok")]
    print(f"{len(rows)} successful folds, {len(have)} already scored")

    for r in rows:
        if r["label"] in have:
            continue
        st = Structure(pdb=Path(r["pdb"]), provenance=Provenance.PREDICTION,
                       pae=Path(r["pae"]), label=r["label"],
                       predictor=r["predictor"])
        out = {k: r[k] for k in ("label", "variant", "construct", "seed",
                                 "predictor", "seconds", "n_residues")}
        try:
            ip = ipsae_m.compute(st)["ipsae"]
            out["ipsae"] = ip.value
            out["ipsae_detail"] = ip.detail
        except Exception as e:                                   # noqa: BLE001
            out["ipsae"] = None
            out["ipsae_error"] = str(e)[:300]
        try:
            dq = dockq_m.compute(st, NATIVE)["dockq"]
            out["dockq"] = dq.value
            out["dockq_detail"] = dq.detail
            out["dockq_skipped"] = dq.skipped_reason
        except Exception as e:                                   # noqa: BLE001
            out["dockq"] = None
            out["dockq_error"] = str(e)[:300]
        with SCORES.open("a") as f:
            f.write(json.dumps(out) + "\n")
        print(f"  {r['label']:<28} ipSAE={out.get('ipsae')}  DockQ={out.get('dockq')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
