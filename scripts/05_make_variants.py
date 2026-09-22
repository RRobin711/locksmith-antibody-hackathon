#!/usr/bin/env python3
"""Build the 14-variant pembrolizumab panel for Gates 1c and 1d.

Emits designs/variants.json. Fv and Fab constructs are derived at fold time:
the mutated *variable* domains are the same in both, which is what makes the
Fv-vs-Fab comparison paired rather than two unrelated measurements.
"""
from __future__ import annotations

import sys
from pathlib import Path

from locksmith.design.variants import build_panel, save
from locksmith.io.pdb import seq_for_folding
from locksmith.numbering import number

SRC = Path("data/refs/prepared/5GGS_ABZ.pdb")
OUT = Path("designs/variants.json")


def main() -> int:
    heavy, light = seq_for_folding(SRC, "A"), seq_for_folding(SRC, "B")
    nh, nl = number(heavy), number(light)
    if nh is None or nl is None:
        print("ERROR: cannot number 5GGS heavy/light", file=sys.stderr)
        return 1
    fv_h = heavy[nh.query_start : nh.query_end + 1]
    fv_l = light[nl.query_start : nl.query_end + 1]

    panel = build_panel(fv_h, fv_l)
    save(panel, OUT)

    print(f"{'variant':<18} {'subs':>4} {'region':<10} {'CDR-H3':<16} {'%id':>6}  kind")
    for v in panel:
        print(f"{v.name:<18} {v.n_subs:>4} {v.regions:<10} {v.cdrh3:<16} "
              f"{v.cdrh3_identity:>6.1f}  {v.kind}")
    print(f"\nwrote {len(panel)} variants -> {OUT}")
    print(f"WT CDR-H3 = {panel[0].cdrh3} ({len(panel[0].cdrh3)} aa)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
