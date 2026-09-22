#!/usr/bin/env python3
"""Score the post-cutoff folds: ipSAE, and DockQ against each target's OWN crystal.

Unlike the variant panel -- where every prediction was compared to the single 5GGS
crystal and DockQ therefore measured *retention of the native binding mode* -- here
each target is scored against its own released structure. So for these five, DockQ is
genuine prediction accuracy: same molecule, known answer, and an answer the model has
not seen.

That is the whole point of the test, and it is why these points can be compared with
the panel's `v00_wt` (also genuine accuracy) but not naively with the panel's mutants.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.metrics import dockq as dockq_m
from locksmith.metrics import ipsae as ipsae_m
from locksmith.types import Provenance, Structure

INDEX = Path("runs/postcutoff/index.jsonl")
SCORES = Path("runs/postcutoff/scores.jsonl")
PREP = Path("data/refs/postcutoff/prepared")


def scored() -> set[str]:
    if not SCORES.exists():
        return set()
    return {json.loads(l)["label"] for l in SCORES.read_text().splitlines() if l.strip()}


def main() -> int:
    if not INDEX.exists():
        print("nothing to score", file=sys.stderr)
        return 1
    have = scored()
    rows = [json.loads(l) for l in INDEX.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r.get("ok")]
    for r in rows:
        if r["label"] in have:
            continue
        native_pdb = PREP / f"{r['target'].lower()}_ABC.pdb"
        if not native_pdb.exists():
            print(f"  no native for {r['target']}", file=sys.stderr)
            continue
        native = Structure(pdb=native_pdb, provenance=Provenance.EXPERIMENT,
                           label=f"{r['target']} crystal")
        st = Structure(pdb=Path(r["pdb"]), provenance=Provenance.PREDICTION,
                       pae=Path(r["pae"]), label=r["label"], predictor=r["predictor"])
        out = {k: r[k] for k in ("label", "target", "construct", "seed", "predictor",
                                 "seconds", "n_residues")}
        try:
            ip = ipsae_m.compute(st)["ipsae"]
            out["ipsae"], out["ipsae_detail"] = ip.value, ip.detail
        except Exception as e:                                   # noqa: BLE001
            out["ipsae"], out["ipsae_error"] = None, str(e)[:300]
        try:
            dq = dockq_m.compute(st, native)["dockq"]
            out["dockq"], out["dockq_detail"] = dq.value, dq.detail
            out["dockq_skipped"] = dq.skipped_reason
        except Exception as e:                                   # noqa: BLE001
            out["dockq"], out["dockq_error"] = None, str(e)[:300]
        with SCORES.open("a") as f:
            f.write(json.dumps(out) + "\n")
        print(f"  {r['label']:<20} ipSAE={out.get('ipsae')}  DockQ={out.get('dockq')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
