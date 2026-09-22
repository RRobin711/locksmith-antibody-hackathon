"""CDR-H3 sequence identity against a reference.

Challenge 1 compares to Keytruda's CDR-H3; Challenge 2 to human germline.

Identity here is over an alignment, not a raw position-by-position comparison,
because a designed loop may differ in LENGTH from the reference.  Pembrolizumab's
IMGT CDR-H3 is 13 residues (ARRDYRFDMGFDY, measured from 5GGS); nivolumab's is 6.
Length changes are legitimate and common, so the denominator must come from the
alignment.
"""
from __future__ import annotations

from locksmith.numbering import number
from locksmith.types import MetricResult

# Measured from 5GGS chain C via ANARCII, IMGT positions 105-117.
PEMBROLIZUMAB_CDRH3 = "ARRDYRFDMGFDY"


def identity(query: str, reference: str) -> float:
    """Percent identity over a global alignment. 0-100."""
    from Bio import Align

    aligner = Align.PairwiseAligner(
        mode="global", match_score=1, mismatch_score=0,
        open_gap_score=-1, extend_gap_score=-0.5,
    )
    aln = aligner.align(query, reference)[0]
    matches = sum(q == r for q, r in zip(aln[0], aln[1]) if q != "-" and r != "-")
    return 100.0 * matches / max(len(query), len(reference))


def compute(heavy_seq: str, *, reference: str = PEMBROLIZUMAB_CDRH3) -> MetricResult:
    n = number(heavy_seq)
    if n is None:
        return MetricResult(None, skipped_reason="heavy chain is not a V domain")
    pct = identity(n.cdr3, reference)
    return MetricResult(round(pct, 1), detail=f"CDR-H3 {n.cdr3} ({len(n.cdr3)}aa) vs {reference}")
