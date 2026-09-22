#!/usr/bin/env python3
"""Fetch the reference structures from RCSB.

  5GGS  Pembrolizumab Fab + PD-1      PRIMARY reference (Challenge 1 template, DockQ target)
  5DK3  Pembrolizumab Fab alone       unbound-state comparison
  5IUS  PD-1 / PD-L1 complex          defines the epitope we must block
  5WT9  Nivolumab + PD-1              an independent real anti-PD-1 solution

Both .pdb and .cif are kept: DockQ and PRODIGY want PDB, while mmCIF carries the
full assembly metadata and does not truncate long chain identifiers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

REFS = {
    "5GGS": "Pembrolizumab Fab + PD-1 (primary reference)",
    "5DK3": "Pembrolizumab Fab alone",
    "5IUS": "PD-1/PD-L1 complex (epitope context)",
    "5WT9": "Nivolumab + PD-1",
}
OUT = Path("data/refs")


def fetch(pdb_id: str, fmt: str) -> Path | None:
    dest = OUT / f"{pdb_id.lower()}.{fmt}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.{fmt}"
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        print(f"  !! {pdb_id}.{fmt}: HTTP {r.status_code}")
        return None
    dest.write_bytes(r.content)
    return dest


def summarise(path: Path) -> str:
    """Chain composition and residue counts, straight from the coordinate records."""
    chains: dict[str, set[int]] = {}
    for line in path.read_text().splitlines():
        if line.startswith("ATOM"):
            ch = line[21]
            try:
                chains.setdefault(ch, set()).add(int(line[22:26]))
            except ValueError:
                continue
    return "  ".join(f"{c}:{len(r)}aa" for c, r in sorted(chains.items()))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok = True
    for pdb_id, desc in REFS.items():
        print(f"\n{pdb_id}  {desc}")
        for fmt in ("pdb", "cif"):
            p = fetch(pdb_id, fmt)
            if p is None:
                ok = False
                continue
            print(f"  {p.name:<12} {p.stat().st_size // 1024:>5} KiB")
        pdb = OUT / f"{pdb_id.lower()}.pdb"
        if pdb.exists():
            print(f"  chains: {summarise(pdb)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
