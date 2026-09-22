#!/usr/bin/env python3
"""Fold every baseline design as a Fab. Resumable; no design is skipped or filtered."""
from __future__ import annotations
import json, sys
from pathlib import Path
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

DESIGNS = Path("designs/baseline_mpnn/designs.json")
OUT = Path("runs/designs_baseline")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")   # identical antigen alignment for every design


def main() -> int:
    rows = json.loads(DESIGNS.read_text())
    done = set()
    if INDEX.exists():
        done = {json.loads(l)["design_id"] for l in INDEX.read_text().splitlines() if l.strip()}
    for r in rows:
        did = r["design_id"]
        if did in done:
            continue
        label = did.replace(".", "p")          # keep 'pae'/'plddt' out of the label
        try:
            res = drv.fold(label, r["heavy"], r["light"], r["antigen"],
                           out_root=OUT, construct="fab", seed=1, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            print(f"FAILED {did}: {e}", file=sys.stderr)
            rec = {"design_id": did, "label": label, "ok": False, "error": str(e)[:400]}
        else:
            print(f"  {did}: {res.n_residues} res, {res.seconds:.0f}s")
            rec = {"design_id": did, "label": label, "ok": True, "pdb": str(res.pdb),
                   "pae": str(res.pae), "plddt": str(res.plddt),
                   "seconds": res.seconds, "n_residues": res.n_residues}
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
