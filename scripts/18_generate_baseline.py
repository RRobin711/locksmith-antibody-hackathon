#!/usr/bin/env python3
"""Baseline 1: plain ProteinMPNN at defaults over pembrolizumab's heavy CDRs.

The control the funnel must beat. No filtering, no reranking, no cherry-picking:
every design generated is carried through fold -> score -> gate.
"""
from __future__ import annotations
import json, sys
from dataclasses import asdict
from pathlib import Path

from locksmith.design import mpnn
from locksmith.metrics import novelty
from locksmith.validate import check_reference_foldable, check_sequence

SRC = Path("data/refs/prepared/5ggs_ABZ.pdb")
OUT = Path("designs/baseline_mpnn")
N, TEMP, SEED = 20, 0.1, 37


def main() -> int:
    ref = check_reference_foldable(SRC)
    if not ref.ok:
        print("reference is not foldable:", ref.errors, file=sys.stderr); return 1

    designs = mpnn.generate(SRC, n=N, temperature=TEMP, seed=SEED, out_root=OUT)
    parent_heavy = mpnn.seq_for_folding(SRC, "A") if hasattr(mpnn, "seq_for_folding") else None
    from locksmith.io.pdb import seq_for_folding
    parent_heavy = seq_for_folding(SRC, "A")

    rows, rejected = [], 0
    for d in designs:
        v = check_sequence(d.design_id, d.heavy, d.light, d.antigen,
                           reference_heavy=parent_heavy)
        if not v.ok:
            print(f"  REJECTED {d.design_id}: {v.errors}", file=sys.stderr)
            rejected += 1
            continue
        r = asdict(d)
        r["cdrh3_identity"] = novelty.compute(d.heavy).value
        r["parent"] = "pembrolizumab_5GGS"
        r["generator"] = "proteinmpnn_v_48_020"
        rows.append(r)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "designs.json").write_text(json.dumps(rows, indent=2))
    print(f"{len(rows)} designs pass pre-flight validation ({rejected} rejected)")
    ids = [r["cdrh3_identity"] for r in rows]
    print(f"CDR-H3 identity: min {min(ids):.1f}%  median {sorted(ids)[len(ids)//2]:.1f}%  max {max(ids):.1f}%")
    print(f"MPNN seq_recovery: {min(r['seq_recovery'] for r in rows):.3f}-{max(r['seq_recovery'] for r in rows):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
