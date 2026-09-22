#!/usr/bin/env python3
"""Re-prepare the post-cutoff targets from SEQRES, not from coordinates.

THE BUG THIS FIXES (found 2026-09-17 by Control 1b).
`io.pdb.chains()` builds a sequence from the residues present in the COORDINATES.
Any residue unresolved in the crystal is silently absent, and the flanking
residues are concatenated. Folding that string predicts a **chimera** -- a protein
with a real loop deleted and its ends fused -- not the molecule the crystal
contains.

Measured damage on the original run: 9W43's antigen was folded 83 aa against a
true 115 (32 residues gone, in three internal gaps across the epitope face), and
9BQW's 132 against 163 (a 19-residue internal gap). Those two produced the two
lowest DockQ scores in the panel, which is exactly what a corrupted antigen
surface would produce, and is not evidence about the model.

The fix: fold the **full entity (SEQRES) sequence** from the PDB. The DockQ
reference stays the coordinate file -- that is correct, it is the real
experimental answer, and DockQ aligns over the resolved residues.

The failure is invisible without this check: the spliced sequence is a valid
protein sequence, folds without error, and yields a confident structure.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from locksmith.numbering import number

PREP = Path("data/refs/postcutoff/prepared")
MANIFEST = PREP / "manifest.json"
OUT = PREP / "manifest_seqres.json"
TARGETS = ["9JBQ", "9BQW", "8TBB", "9W43", "8RWB"]


def entities(pdb_ids):
    q = ('{ entries(entry_ids: %s) { rcsb_id polymer_entities { '
         'entity_poly { pdbx_seq_one_letter_code_can } '
         'rcsb_polymer_entity { pdbx_description } } } }' % json.dumps(pdb_ids))
    url = "https://data.rcsb.org/graphql?query=" + urllib.parse.quote(q)
    return json.load(urllib.request.urlopen(url, timeout=180))["data"]["entries"]


def main() -> int:
    old = json.loads(MANIFEST.read_text())
    ents = {e["rcsb_id"]: e["polymer_entities"] for e in entities(TARGETS)}
    out = {}
    for t in TARGETS:
        o = old[t]
        # Match each entity to a role by sequence containment against the
        # coordinate-derived sequence -- names differ per deposition and the
        # coordinate string is a subsequence of its own SEQRES.
        roles = {}
        for role, coordseq in (("heavy", o["heavy_full"]), ("light", o["light_full"]),
                               ("antigen", o["antigen"])):
            best, bestscore = None, -1
            for e in ents[t]:
                s = e["entity_poly"]["pdbx_seq_one_letter_code_can"] or ""
                # score = longest common prefix of the coordinate seq within SEQRES
                score = sum(1 for a, b in zip(s, coordseq) if a == b)
                if coordseq[:20] in s:
                    score += 1000
                if score > bestscore:
                    best, bestscore = s, score
            roles[role] = best
        nh = number(roles["heavy"])
        nl = number(roles["light"])
        if nh is None or nl is None:
            print(f"{t}: SEQRES chains not numberable", file=sys.stderr)
            return 1
        out[t] = {
            "prepared": o["prepared"],
            "heavy_full": roles["heavy"], "light_full": roles["light"],
            "antigen": roles["antigen"],
            "heavy_fv": roles["heavy"][nh.query_start: nh.query_end + 1],
            "light_fv": roles["light"][nl.query_start: nl.query_end + 1],
            "cdrh3": nh.cdr3,
        }
        m = out[t]
        print(f"{t}: H {len(o['heavy_full'])}->{len(m['heavy_full'])}  "
              f"L {len(o['light_full'])}->{len(m['light_full'])}  "
              f"Ag {len(o['antigen'])}->{len(m['antigen'])}   "
              f"Fab {len(m['heavy_full'])+len(m['light_full'])+len(m['antigen'])} res")
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
