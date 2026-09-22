#!/usr/bin/env python3
"""Fold the 5 post-cutoff targets, Fv and Fab, untemplated. No special-casing.

Antigen MSA: each target has a different antigen, so each needs its own alignment.
These are all PUBLISHED structures, so the public MMseqs2 server is a fair use here --
unlike for designed sequences, where the driver refuses. The Fv fold fetches the
alignment and it is cached for the Fab fold of the same target, so the antigen sees an
identical alignment in both constructs (the same reason the panel cached PD-1).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as boltz_drv

MANIFEST = Path("data/refs/postcutoff/prepared/manifest.json")
OUT = Path("runs/postcutoff")
INDEX = OUT / "index.jsonl"
CACHE = Path("data/msa_cache")


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines() if l.strip()}


def record(rec: dict) -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with INDEX.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def main() -> int:
    man = json.loads(MANIFEST.read_text())
    for pid, m in man.items():
        ag_cache = CACHE / f"{pid.lower()}_antigen.csv"
        for form in ("fv", "fab"):
            label = f"{pid.lower()}__{form}__s1"
            if label in done():
                print(f"skip {label}")
                continue
            h = m["heavy_fv"] if form == "fv" else m["heavy_full"]
            l = m["light_fv"] if form == "fv" else m["light_full"]
            a = m["antigen"]
            msa = ag_cache if ag_cache.exists() else None
            try:
                r = boltz_drv.fold(label, h, l, a, out_root=OUT / form,
                                   construct=form, seed=1, antigen_msa=msa)
            except FoldFailed as e:
                print(f"FAILED {label}: {e}", file=sys.stderr)
                record({"label": label, "target": pid, "construct": form, "seed": 1,
                        "predictor": "boltz2", "ok": False, "error": str(e)[:500]})
                continue
            # Cache the antigen alignment the first time we get one.
            if msa is None:
                src = (OUT / form / label / f"boltz_results_{label}" / "msa" / f"{label}_2.csv")
                if src.exists():
                    CACHE.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, ag_cache)
                    print(f"  cached antigen MSA -> {ag_cache.name} "
                          f"({sum(1 for _ in ag_cache.open())-1} seqs)")
            print(f"  {label}: {r.n_residues} res, {r.seconds:.0f}s")
            record({"label": label, "target": pid, "construct": form, "seed": 1,
                    "predictor": "boltz2", "ok": True, "pdb": str(r.pdb),
                    "pae": str(r.pae), "plddt": str(r.plddt), "seconds": r.seconds,
                    "n_residues": r.n_residues, "chain_lengths": list(r.chain_lengths)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
