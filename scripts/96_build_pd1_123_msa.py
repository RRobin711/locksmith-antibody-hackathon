#!/usr/bin/env python3
"""Cache a correct antigen alignment for the 123-residue PD-1, from a3m Boltz already built.

WHY CACHE RATHER THAN QUERY PER FOLD. Re-querying MMseqs2 for each of 30 designs would let
the alignment drift between them and put uncontrolled variance straight into the quantity
being ranked. Every design in a screen must see the *identical* antigen alignment. That is
the original reason `pd1_5ggs.csv` exists -- the mistake was never the cache, it was
pairing a cache built for a 113-residue query with a 123-residue antigen.

SOURCE. `runs/msa_register/matched_123` folded the exact 123-mer with `--use_msa_server`,
so Boltz has already downloaded a matched alignment. Reusing it costs nothing and avoids a
fresh query returning something slightly different.

FORMAT. Boltz's `parse_csv` wants columns `key,sequence`: the first row is the query, gaps
are `-`, and lowercase characters are insertions relative to the query (it counts them as
deletions and strips them from the alignment width). So a3m lines carry over verbatim; only
the header parsing changes.

THE INVARIANT THAT MATTERS. The query row, with gaps removed, must equal the antigen
sequence character for character. If it does not, Boltz silently discards the whole
alignment -- which is the defect this file exists to repair. Asserted here, and enforced
again at call time by `write_input`.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

A3M = Path("runs/msa_register/matched_123/boltz_results_matched_123/msa/"
           "matched_123_unpaired_tmp_env/uniref.a3m")
OUT = Path("data/msa_cache/pd1_123_handbook.csv")
MAX_SEQS = 4096


def read_a3m(p: Path) -> list[str]:
    seqs, cur = [], None
    for line in p.read_text(errors="ignore").splitlines():
        if line.startswith(">"):
            if cur is not None:
                seqs.append(cur)
            cur = ""
        elif cur is not None:
            cur += line.strip()
    if cur:
        seqs.append(cur)
    return seqs


def main() -> int:
    import json

    antigen = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    if not A3M.exists():
        print(f"missing {A3M}", file=sys.stderr)
        return 1
    seqs = read_a3m(A3M)
    if not seqs:
        print("no sequences parsed", file=sys.stderr)
        return 1

    query = seqs[0]
    bare = query.replace("-", "").upper()
    if bare != antigen.upper():
        print(f"query row does not match the antigen.\n  query   ({len(bare)}): {bare[:60]}"
              f"\n  antigen ({len(antigen)}): {antigen[:60]}", file=sys.stderr)
        return 1

    seen, rows = set(), []
    for s in seqs[:MAX_SEQS]:
        k = s.replace("-", "").upper()
        if k in seen:
            continue
        seen.add(k)
        rows.append(s)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "sequence"])
        for s in rows:
            w.writerow([-1, s])

    print(f"query matches the {len(antigen)}-residue handbook antigen exactly")
    print(f"wrote {OUT}: {len(rows)} unique sequences (from {len(seqs)} parsed)")

    # the guard that would have caught the original defect, run here as a self-check
    from locksmith.fold.boltz import _msa_query_length
    q = _msa_query_length(OUT)
    print(f"write_input would read query length {q} against antigen {len(antigen)}: "
          f"{'OK' if q == len(antigen) else 'MISMATCH'}")
    return 0 if q == len(antigen) else 1


if __name__ == "__main__":
    sys.exit(main())
