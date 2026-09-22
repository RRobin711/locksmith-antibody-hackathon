#!/usr/bin/env python3
"""Fetch and prepare the 5 post-cutoff targets. See results/postcutoff_targets.md.

Chain roles are assigned by ANARCII, NOT by the PDB's chain labels or entity names:
the heavy chain is the V domain scoring as chain_type 'H', the light chain as 'K'/'L',
and the antigen is whatever does not number as a V domain. This matters because PD-1
itself numbers as antibody-like (IgV fold, ANARCII score ~16 vs ~31 for a true V
domain) -- MIN_V_DOMAIN_SCORE=25 is what keeps the antigen out of the antibody slot,
and the same trap applies to TIM-3, ULBP6 and CD38, which are all Ig-superfamily.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from locksmith.io.pdb import chains, extract_complex
from locksmith.numbering import number

TARGETS = ["9JBQ", "9BQW", "8TBB", "9W43", "8RWB"]
RAW = Path("data/refs/postcutoff")
PREP = Path("data/refs/postcutoff/prepared")


def fetch(pdb_id: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / f"{pdb_id.lower()}.pdb"
    if dest.exists():
        return dest
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    urllib.request.urlretrieve(url, dest)
    return dest


def main() -> int:
    PREP.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for pid in TARGETS:
        src = fetch(pid)
        ch = chains(str(src))
        roles = {}
        for name, info in ch.items():
            if info.n_res < 50:
                continue
            n = number(info.seq)
            roles[name] = (n.chain_type if n else None, n.score if n else 0.0, info.n_res)

        heavy = [c for c, (t, _, _) in roles.items() if t == "H"]
        light = [c for c, (t, _, _) in roles.items() if t in ("K", "L")]
        antigen = [c for c, (t, _, _) in roles.items() if t is None]
        print(f"{pid}: " + "  ".join(
            f"{c}={roles[c][0] or 'Ag'}({roles[c][1]:.1f},{roles[c][2]}aa)" for c in roles))
        if not (len(heavy) == 1 and len(light) == 1 and len(antigen) == 1):
            print(f"  SKIP {pid}: expected exactly one H, one L, one antigen; "
                  f"got H={heavy} L={light} Ag={antigen}", file=sys.stderr)
            continue

        dest = PREP / f"{pid.lower()}_ABC.pdb"
        mapping = extract_complex(src, dest, heavy=heavy[0], light=light[0],
                                  antigen=antigen[0])
        out = chains(str(dest))
        nh, nl = number(out["A"].seq), number(out["B"].seq)
        manifest[pid] = {
            "source": str(src), "prepared": str(dest), "chain_map": mapping,
            "heavy_len": out["A"].n_res, "light_len": out["B"].n_res,
            "antigen_len": out["C"].n_res,
            "total": out["A"].n_res + out["B"].n_res + out["C"].n_res,
            "heavy_fv": out["A"].seq[nh.query_start: nh.query_end + 1],
            "light_fv": out["B"].seq[nl.query_start: nl.query_end + 1],
            "heavy_full": out["A"].seq, "light_full": out["B"].seq,
            "antigen": out["C"].seq,
            "cdrh3": nh.cdr3,
        }
        m = manifest[pid]
        print(f"  -> {dest.name}  Fab {m['total']} res | "
              f"Fv {len(m['heavy_fv'])+len(m['light_fv'])+m['antigen_len']} res | "
              f"CDR-H3 {m['cdrh3']}")

    (PREP / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nprepared {len(manifest)}/{len(TARGETS)} targets")
    return 0 if len(manifest) == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
