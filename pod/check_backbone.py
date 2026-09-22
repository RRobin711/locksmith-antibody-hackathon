#!/usr/bin/env python3
"""B1 artefact + conditioning assertion for one RFdiffusion backbone.

Two jobs, and the second is the important one:

  1. Is this a STRUCTURE?  chains present, residue counts sane, no NaN, no duplicated
     coordinates, no chain collapsed to a point.  A file that exists and parses is not
     evidence -- `boltz predict` exits 0 after fatal errors, and the CPU equivalents are
     silent truncation and NaN output.

  2. Did the CONDITIONING do anything?  RFdiffusion is told to build against 26 hotspot
     residues on chain T.  `ab_pose.parse_hotspots` matches (chain, pdb_resnum) and
     SILENTLY SKIPS any hotspot it cannot find, so a numbering mistake yields zero
     hotspots and unconditioned generation wearing the target's name, with no error.
     This asks the only question that detects that: do the designed CDR loops actually
     make heavy-atom contact with those residues?

     This is deterministic and usable at n=1, which is why it is the PRIMARY instrument
     for conditioning rather than the conditioned-vs-unconditioned arm comparison.  That
     comparison is a two-sample test whose power at small n is poor, and this project
     published four underpowered nulls as findings on 2026-09-20.

Exit 0 = usable, 1 = reject (and it must NOT enter the pool).
Prints one JSON line so the heartbeat can aggregate without re-parsing PDBs.
"""
from __future__ import annotations

import json
import math
import sys

CUTOFF = 5.0          # angstrom, heavy-atom, same convention as metrics/interface.py


def main(path: str, hotspot_ordinals_csv: str) -> int:
    """hotspot_ordinals_csv: 0-based POSITIONS within the target chain, not residue
    numbers.  RFdiffusion RENUMBERS its output continuously across chains -- measured
    on gate0b_0.pdb: H=1-115, L=116-219, **T=220-332**, where the input PD-1 was
    numbered 31-143.  Matching on residue number therefore finds NOTHING and the check
    reports "zero hotspot contacts" for a perfectly good dock.  That false negative
    would have rejected every backbone in the run.  Ordinal positions survive any
    renumbering.
    """
    want = {int(x) for x in hotspot_ordinals_csv.split(",") if x.strip()}
    chains: dict[str, dict[int, list[tuple[float, float, float]]]] = {}
    order: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    loop_abs: list[int] = []
    for line in open(path):
        if line.startswith("REMARK PDBinfo-LABEL:"):
            parts = line.split()
            # The index is 1-indexed ABSOLUTE across the whole file (README), not
            # per-chain.  Reading it as per-chain silently mislocates every loop.
            if len(parts) >= 4 and parts[-1] in ("H1", "H2", "H3", "L1", "L2", "L3"):
                loop_abs.append(int(parts[-2]))
        elif line.startswith("ATOM") and line[76:78].strip() != "H":
            ch, num = line[21], int(line[22:26])
            key = (ch, num)
            if key not in seen:
                seen.add(key)
                order.append(key)
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            chains.setdefault(ch, {}).setdefault(num, []).append(xyz)

    out: dict[str, object] = {"file": path.rsplit("/", 1)[-1]}
    fail: list[str] = []
    for need in ("H", "L", "T"):
        if need not in chains:
            fail.append(f"chain {need} missing")
    if fail:
        out["ok"] = False; out["fail"] = fail; print(json.dumps(out)); return 1
    out["res"] = {c: len(r) for c, r in sorted(chains.items())}

    allxyz = [p for c in chains.values() for r in c.values() for p in r]
    if any(math.isnan(v) for p in allxyz for v in p):
        fail.append("NaN coordinates")
    if len(allxyz) != len({tuple(p) for p in allxyz}):
        fail.append("duplicate coordinates")
    for c, r in chains.items():
        pts = [p for v in r.values() for p in v]
        ext = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))
        if ext < 5.0:
            fail.append(f"chain {c} collapsed (extent {ext:.1f} A)")

    tnums = sorted(chains["T"])
    hot_nums = {tnums[i] for i in want if 0 <= i < len(tnums)}
    if len(hot_nums) != len(want):
        fail.append(f"only {len(hot_nums)}/{len(want)} hotspot positions exist in chain T")

    loop_pts = []
    for i in loop_abs:
        if 1 <= i <= len(order):
            c, n = order[i - 1]
            loop_pts.extend(chains[c][n])

    c2 = CUTOFF * CUTOFF
    def near(pts):
        return any((q[0]-p[0])**2 + (q[1]-p[1])**2 + (q[2]-p[2])**2 <= c2
                   for q in pts for p in loop_pts)

    touched = {n for n in hot_nums if near(chains["T"][n])}
    contacted = {n for n in tnums if near(chains["T"][n])}

    out["loop_residues"] = len(loop_abs)
    out["iface_residues"] = len(contacted)
    out["hotspots_contacted"] = len(touched)
    out["hotspots_total"] = len(want)
    out["frac_iface_on_epitope"] = round(len(touched) / len(contacted), 3) if contacted else 0.0

    if not loop_abs:
        fail.append("no CDR loop REMARKs -- cannot assess conditioning")
    elif not contacted:
        fail.append("loops contact NOTHING on the target: not a dock")
    elif not touched:
        fail.append("ZERO hotspot contacts: docked, but off the epitope")

    out["ok"] = not fail
    out["fail"] = fail
    print(json.dumps(out))
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
