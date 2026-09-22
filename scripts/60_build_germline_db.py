#!/usr/bin/env python3
"""Build data/germline/human_igh.json -- the reference set for Challenge 2 novelty.

Handbook 6.3.1: Challenge 2 novelty is CDR-H3 identity to *human germline*. CDR-H3
spans the V(D)J junction, so there is no single germline template: the loop is
V 3'-end + D (any reading frame, trimmed) + J 5'-end, plus non-templated N residues.
This script assembles the three segment families ONCE into a static asset so the
metric itself has no new runtime dependency.

Sources, both harvested without installing into any working environment:
  V, J : ANARCI's `germlines.py` (IMGT-gapped amino acid, 128-position alignment).
         Position 104 is the conserved Cys; IMGT CDR3 is 105-117. V alleles carry
         105-106(+) before their gap run; J alleles carry 115-117 before FR4 at 118.
  D    : riot-na's `databases/gene_db/d_genes/human/igh.fasta` (NUCLEOTIDE).
         Translated in all 3 forward frames. D is genuinely read in any frame in vivo.

Run once:  uv run scripts/60_build_germline_db.py --anarci <dir> --riot <dir>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OUT = Path("data/germline/human_igh.json")

# IMGT junction numbering. CDR3 = 105..117 inclusive (13 positions when ungapped
# and untrimmed); 104 is the conserved Cys, 118 the conserved Trp/Phe of FR4.
CDR3_START, CDR3_END = 105, 117

CODONS = {
    "TTT":"F","TTC":"F","TTA":"L","TTG":"L","CTT":"L","CTC":"L","CTA":"L","CTG":"L",
    "ATT":"I","ATC":"I","ATA":"I","ATG":"M","GTT":"V","GTC":"V","GTA":"V","GTG":"V",
    "TCT":"S","TCC":"S","TCA":"S","TCG":"S","CCT":"P","CCC":"P","CCA":"P","CCG":"P",
    "ACT":"T","ACC":"T","ACA":"T","ACG":"T","GCT":"A","GCC":"A","GCA":"A","GCG":"A",
    "TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","CAT":"H","CAC":"H","CAA":"Q","CAG":"Q",
    "AAT":"N","AAC":"N","AAA":"K","AAG":"K","GAT":"D","GAC":"D","GAA":"E","GAG":"E",
    "TGT":"C","TGC":"C","TGA":"*","TGG":"W","CGT":"R","CGC":"R","CGA":"R","CGG":"R",
    "AGT":"S","AGC":"S","AGA":"R","AGG":"R","GGT":"G","GGC":"G","GGA":"G","GGG":"G",
}


def translate(nt: str, frame: int) -> str:
    nt = nt.upper().replace("U", "T")[frame:]
    return "".join(CODONS.get(nt[i:i + 3], "X") for i in range(0, len(nt) - 2, 3))


def imgt_slice(aligned: str, lo: int, hi: int) -> str:
    """Ungapped residues occupying IMGT positions lo..hi of a 128-col alignment."""
    if len(aligned) != 128:
        raise ValueError(f"expected a 128-column IMGT alignment, got {len(aligned)}")
    return "".join(c for i, c in enumerate(aligned, start=1) if lo <= i <= hi and c != "-")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anarci", required=True, help="dir containing anarci/germlines.py")
    ap.add_argument("--riot", required=True, help="dir containing riot_na/databases/...")
    a = ap.parse_args()

    sys.path.insert(0, a.anarci)
    from anarci.germlines import all_germlines as G  # noqa: E402

    hv = G["V"]["H"]["human"]
    hj = G["J"]["H"]["human"]

    v_parts: dict[str, str] = {}
    for allele, aln in hv.items():
        seg = imgt_slice(aln, CDR3_START, CDR3_END)
        if seg:
            v_parts[allele] = seg
    j_parts: dict[str, str] = {}
    for allele, aln in hj.items():
        seg = imgt_slice(aln, CDR3_START, CDR3_END)
        if seg:
            j_parts[allele] = seg

    # D: nucleotide -> 3 forward frames. Stop codons truncate that frame's usable
    # peptide, which is biologically right: a D read through a stop cannot be in a
    # productive rearrangement.
    dpath = Path(a.riot) / "riot_na/databases/gene_db/d_genes/human/igh.fasta"
    d_parts: dict[str, str] = {}
    name, buf = None, []
    def flush() -> None:
        if name is None:
            return
        nt = "".join(buf)
        for f in (0, 1, 2):
            pep = translate(nt, f).split("*")[0]
            if len(pep) >= 3:
                d_parts[f"{name}_f{f + 1}"] = pep
    for line in dpath.read_text().splitlines():
        if line.startswith(">"):
            flush()
            name, buf = line[1:].split("\t")[0].strip(), []
        elif line.strip():
            buf.append(line.strip())
    flush()

    db = {
        "provenance": {
            "v_j": "ANARCI germlines.py (IMGT-gapped AA, 128-col)",
            "d": "riot-na databases/gene_db/d_genes/human/igh.fasta (nt), "
                 "translated in 3 forward frames, truncated at first stop",
            "cdr3_definition": f"IMGT positions {CDR3_START}-{CDR3_END} inclusive",
        },
        "v": v_parts, "d": d_parts, "j": j_parts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(db, indent=1, sort_keys=True))
    # Full V alignments, kept separately: used only for V-gene ASSIGNMENT, which
    # is not the scored metric but is the only germline quantity with published
    # ground truth to validate against.
    (OUT.parent / "human_ighv_alignments.json").write_text(
        json.dumps(hv, indent=1, sort_keys=True))

    print(f"wrote {OUT}")
    print(f"  IGHV CDR3-contributing alleles : {len(v_parts)}")
    print(f"  IGHD peptides (alleles x frames): {len(d_parts)}")
    print(f"  IGHJ CDR3-contributing alleles : {len(j_parts)}")
    import collections
    print(f"  distinct V contributions: {dict(collections.Counter(v_parts.values()).most_common(6))}")
    print(f"  distinct J contributions: {dict(collections.Counter(j_parts.values()).most_common(6))}")
    dl = [len(x) for x in d_parts.values()]
    print(f"  D peptide length: min {min(dl)} median {sorted(dl)[len(dl)//2]} max {max(dl)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
