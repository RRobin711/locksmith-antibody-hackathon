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


def compute(heavy_seq: str, *, reference: str | None = None,
            challenge: int = 1) -> MetricResult:
    """CDR-H3 percent identity against the reference THIS CHALLENGE specifies.

    §6.3.1 is explicit that the metric is the same and only the reference changes:
    "Challenge 1: Compared to Keytruda's CDR-H3 / Challenge 2: Compared to human
    germline CDR sequences". The band triple and the <95% cutoff are shared (§5.2,
    §7.2), so this is ONE metric with two references, not two metrics -- encoding it
    as two would duplicate the bands and give them somewhere to diverge.

    Challenge 2 has no single germline string to compare against: CDR-H3 spans the
    V(D)J junction and the N-region insertions have no germline counterpart at all, so
    the germline side is a best-match search over IGHV/IGHD/IGHJ. See
    `metrics/germline.py`, which is validated in `results/germline_metric_validation.md`.

    An explicit `reference` overrides the challenge dispatch and is used only by the
    Challenge 1 path and by tests.
    """
    n = number(heavy_seq)
    if n is None:
        return MetricResult(None, skipped_reason="heavy chain is not a V domain")
    if reference is None and challenge == 2:
        from locksmith.metrics import germline
        return germline.compute_from_cdr3(n.cdr3)
    ref = reference if reference is not None else PEMBROLIZUMAB_CDRH3
    pct = identity(n.cdr3, ref)
    return MetricResult(round(pct, 1), detail=f"CDR-H3 {n.cdr3} ({len(n.cdr3)}aa) vs {ref}")
