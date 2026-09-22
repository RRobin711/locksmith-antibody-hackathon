#!/usr/bin/env python3
"""M3 primary arm: ProteinMPNN across four sampling temperatures, CDR-H3 length fixed.

WHY TEMPERATURE IS THE AXIS. The existing 40-design pool is one generator at one
temperature (0.1) with one CDR-H3 length (13) -- a densely sampled single operating
point, not a design space. See results/m3_plan_review.md §5. Temperature is the only
dial ProteinMPNN has that widens sequence space without changing the backbone, so it
is the only cheap way to find out whether the aromatic-content effect (measured at
T=0.1 alone) holds anywhere else.

WHY NOT VARIED LOOP LENGTH. ProteinMPNN is fixed-backbone: it samples one residue per
given backbone position and cannot emit a loop of a different length -- design/mpnn.py
asserts this at line 139. Varying CDR-H3 length needs RFdiffusion/RFantibody, neither
installed nor qualified here. That is a milestone, not an arm.

DEDUPLICATION IS NOT COSMETIC. At T=0.1 ProteinMPNN recovers near-native residues at
high rate, so requesting N designs does not yield N distinct sequences. The existing
40-design pool collapsed onto three distinct CDR-H3 identity values. Duplicates folded
twice waste GPU hours and, worse, inflate any n in the analysis with rows that are not
independent. Dedupe on the heavy chain and report the unique yield per arm -- that
yield is itself a result about how much diversity each temperature actually buys.

Writes designs/wide_temp/designs.json. Does NOT touch designs/wide_mpnn/.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from locksmith.design import mpnn
from locksmith.io.pdb import seq_for_folding
from locksmith.metrics import novelty
from locksmith.validate import check_reference_foldable, check_sequence

SRC = Path("data/refs/prepared/5ggs_ABZ.pdb")
OUT = Path("designs/wide_temp")
AROMATIC = set("FWY")
CDRH3 = slice(95, 108)

# (temperature, n_requested, mpnn_seed). Seeds are distinct per arm so arms cannot
# collide; none is 37 or 38, which the existing T=0.1 pool used, so these are fresh
# designs rather than a re-derivation of that pool.
ARMS = [(0.1, 60, 101), (0.2, 60, 102), (0.3, 60, 103), (0.5, 60, 104)]


def main() -> int:
    ref = check_reference_foldable(SRC)
    if not ref.ok:
        print("reference is not foldable:", ref.errors, file=sys.stderr)
        return 1
    parent_heavy = seq_for_folding(SRC, "A")
    OUT.mkdir(parents=True, exist_ok=True)

    rows, seen, stats = [], {}, []
    for temp, n, seed in ARMS:
        designs = mpnn.generate(SRC, n=n, temperature=temp, seed=seed,
                                out_root=OUT / f"T{str(temp).replace('.', 'p')}")
        kept = rejected = dup = 0
        for d in designs:
            v = check_sequence(d.design_id, d.heavy, d.light, d.antigen,
                               reference_heavy=parent_heavy)
            if not v.ok:
                print(f"  REJECTED {d.design_id}: {v.errors}", file=sys.stderr)
                rejected += 1
                continue
            if d.heavy in seen:
                dup += 1
                continue
            seen[d.heavy] = d.design_id
            h3 = d.heavy[CDRH3]
            r = asdict(d)
            r["cdrh3_identity"] = novelty.compute(d.heavy).value
            r["arom_count"] = sum(c in AROMATIC for c in h3)
            r["cdrh3"] = h3
            r["arm_temperature"] = temp
            r["parent"] = "pembrolizumab_5GGS"
            r["generator"] = "proteinmpnn_v_48_020"
            rows.append(r)
            kept += 1
        ids = [r["cdrh3_identity"] for r in rows if r["arm_temperature"] == temp]
        ar = [r["arom_count"] for r in rows if r["arm_temperature"] == temp]
        stats.append((temp, n, kept, dup, rejected, ids, ar))
        print(f"T={temp}: requested {n}, unique kept {kept}, duplicates {dup}, rejected {rejected}")

    (OUT / "designs.json").write_text(json.dumps(rows, indent=2))

    print(f"\n{len(rows)} unique designs written to {OUT/'designs.json'}\n")
    print(f"{'T':>5} {'req':>4} {'uniq':>5} {'dup':>4} {'rej':>4} "
          f"{'CDR-H3 identity %':>22} {'aromatic count':>26}")
    for temp, n, kept, dup, rejected, ids, ar in stats:
        idr = f"{min(ids):.1f}-{max(ids):.1f} ({len(set(ids))} distinct)" if ids else "—"
        arr = f"{dict(sorted(Counter(ar).items()))}" if ar else "—"
        print(f"{temp:>5} {n:>4} {kept:>5} {dup:>4} {rejected:>4} {idr:>22} {arr:>26}")
    lo = sum(1 for r in rows if r["arom_count"] <= 1)
    print(f"\nclearing the pre-registered filter (aromatic count <= 1): "
          f"{lo}/{len(rows)} ({lo/len(rows):.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
