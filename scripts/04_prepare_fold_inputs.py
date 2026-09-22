#!/usr/bin/env python3
"""Emit sequence inputs for the 5GGS refold, in both Fv and Fab form.

The standing protocol (PLAN 15.2) is: screen wide on Fv, confirm the shortlist as
Fab.  Fv is ~350 residues against ~554, roughly 2.5x cheaper, but a bare Fv leaves
the VH/VL elbow orientation under-constrained -- the constant domains clamp it.
So both forms are produced here, and Gate 1c tests whether Fv RANKING actually
predicts Fab ranking before we trust the cheap screen.

Fv boundaries come from ANARCII's variable-domain span, not from a fixed residue
count: the V/C junction is not at the same position in every antibody.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.io.pdb import chains, seq_for_folding
from locksmith.numbering import number

SRC = Path("data/refs/prepared/5GGS_ABZ.pdb")
OUT = Path("data/fold_inputs")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # seq_for_folding refuses a chain with an INTERNAL deletion: folding a
    # coordinate-derived sequence with an unresolved loop spliced out predicts a
    # chimera. 5GGS is clean (terminal truncation only); the guard is here so a
    # future reference swap cannot reintroduce the 2026-09-17 failure silently.
    heavy = seq_for_folding(SRC, "A")
    light = seq_for_folding(SRC, "B")
    antigen = seq_for_folding(SRC, "C")

    nh, nl = number(heavy), number(light)
    if nh is None or nl is None:
        print("ERROR: could not number heavy/light chain", file=sys.stderr)
        return 1

    fv_h = heavy[nh.query_start : nh.query_end + 1]
    fv_l = light[nl.query_start : nl.query_end + 1]

    forms = {
        "fab": (heavy, light, antigen),
        "fv": (fv_h, fv_l, antigen),
    }

    manifest = {}
    for form, (h, l, a) in forms.items():
        # Boltz FASTA: >CHAIN|protein|  (empty MSA field -> use --use_msa_server)
        fa = OUT / f"5ggs_{form}.fasta"
        fa.write_text(
            f">A|protein|\n{h}\n>B|protein|\n{l}\n>C|protein|\n{a}\n"
        )
        # Plain 3-header FASTA in the handbook's submission format, for our own tools.
        sub = OUT / f"5ggs_{form}_submission.fasta"
        sub.write_text(
            f">Heavy_Chain\n{h}\n>Light_Chain\n{l}\n>Antigen\n{a}\n"
        )
        total = len(h) + len(l) + len(a)
        manifest[form] = {"heavy": len(h), "light": len(l), "antigen": len(a),
                          "total_residues": total}
        print(f"{form:>4}: H={len(h):>3}  L={len(l):>3}  Ag={len(a):>3}  total={total:>3} residues")

    ratio = manifest["fab"]["total_residues"] / manifest["fv"]["total_residues"]
    print(f"\nFab/Fv size ratio: {ratio:.2f}x  "
          f"(Evoformer cost grows worse than linearly, so the wall-clock saving is larger)")
    print(f"V-domain spans: heavy {nh.query_start}-{nh.query_end}, light {nl.query_start}-{nl.query_end}")

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nwrote {len(list(OUT.glob('*.fasta')))} FASTA files to {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
