"""CDR-H3 identity to human germline -- the Challenge 2 novelty metric.

Handbook 6.3.1 / 7.1 step 4: Challenge 2 novelty is "CDR-H3 identity to human
germline", hard cutoff < 95%.  Challenge 1's equivalent compares to one reference
string (Keytruda's CDR-H3); Challenge 2 has NO such string, and that is not an
oversight in our reading -- it is a property of the biology.

WHY THERE IS NO GERMLINE CDR-H3
-------------------------------
CDR-H3 is the V(D)J junction.  Its residues come from three places:

    IMGT 105-117  =  [ V 3'-end ] [ N1 ] [ D, any frame, trimmed ] [ N2 ] [ J 5'-end ]

Only the flanks are templated.  Measured from the assembled reference
(`data/germline/human_igh.json`, built by `scripts/60_build_germline_db.py`):

    IGHV contributes 2-3 residues   ("AR" in 173 of 249 human alleles)
    IGHJ contributes 3 residues     ("FDY", "MDV", "FDP", ...)
    IGHD contributes 3-12 residues  (76 peptides = alleles x 3 forward frames)

The N regions are non-templated nucleotide additions with no germline counterpart
at all.  So for a 13-residue CDR-H3, roughly 5 positions are germline-templated
before any D match is even considered.  **Every human antibody, natural or
designed, scores well under 95% on any honest reading.**  The cutoff is free.
Report the noise floor (below) beside every number or the value means nothing.

TWO CONVENTIONS, BOTH REPORTED
------------------------------
The handbook says only "aligned to reference sequences, and percent identity is
calculated".  That admits two readings which give very different numbers, and we
do not know which the organisers implemented.  This is the same class of
ambiguity as the band->score mapping (see config/metrics.yaml conventions):

  `best_segment`  Literal reading.  Global-align the query against each germline
                  segment and take the best percent identity, denominator
                  max(len(query), len(segment)).  A 13-mer against a 3-mer "FDY"
                  can never exceed 3/13, so this convention is bounded low by
                  construction and is nearly a constant.

  `vdj_coverage`  Biologically faithful reading.  Reconstruct the junction: best
                  exact V prefix + best D substring + best exact J suffix,
                  non-overlapping, and report covered/len(query).  This is what
                  "how much of this loop is germline" actually means.

`vdj_coverage` is the primary because `best_segment` cannot discriminate -- but
the choice is declared, not hidden, and both are written to the result detail.

NEITHER IS A NOVELTY TEST.  A loop can be 0% germline-covered and still be a
trivial copy of a published antibody; germline identity does not measure that.
It is the metric the handbook names, scored as specified, and no more.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from locksmith.numbering import number
from locksmith.types import MetricResult

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "germline" / "human_igh.json"


@lru_cache(maxsize=1)
def _db() -> dict:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH} missing -- run scripts/60_build_germline_db.py first"
        )
    return json.loads(DB_PATH.read_text())


def _longest_common_substring(a: str, b: str) -> tuple[int, int]:
    """(length, start-index-in-a) of the longest exact common substring."""
    best, best_i = 0, 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, best_i = cur[j], i - cur[j]
        prev = cur
    return best, best_i


def vdj_coverage(cdr3: str) -> tuple[float, dict]:
    """Fraction of the loop attributable to a best-match V/D/J reconstruction.

    V is matched as an exact PREFIX of the loop and J as an exact SUFFIX, because
    exonuclease trimming removes segment ends, never their interiors relative to
    the junction.  D is matched as an arbitrary substring in whatever window the
    flanks leave, because D is trimmed at BOTH ends and read in any frame.
    """
    db = _db()
    n = len(cdr3)
    if n == 0:
        return 0.0, {}

    v_k, v_hit = 0, None
    for allele, seg in db["v"].items():
        k = 0
        for a, b in zip(cdr3, seg):
            if a != b:
                break
            k += 1
        if k > v_k:
            v_k, v_hit = k, allele

    j_k, j_hit = 0, None
    for allele, seg in db["j"].items():
        k = 0
        for a, b in zip(reversed(cdr3), reversed(seg)):
            if a != b:
                break
            k += 1
        if k > j_k:
            j_k, j_hit = k, allele

    # Flanks may not overlap; if they would, give the longer one precedence.
    if v_k + j_k > n:
        if v_k >= j_k:
            j_k = n - v_k
        else:
            v_k = n - j_k

    window = cdr3[v_k:n - j_k] if n - j_k > v_k else ""
    d_len, d_hit = 0, None
    for allele, pep in db["d"].items():
        ln, _ = _longest_common_substring(window, pep)
        if ln > d_len:
            d_len, d_hit = ln, allele

    covered = v_k + d_len + j_k
    return 100.0 * covered / n, {
        "v": v_hit, "v_len": v_k, "d": d_hit, "d_len": d_len,
        "j": j_hit, "j_len": j_k, "covered": covered, "loop_len": n,
    }


def best_segment(cdr3: str) -> tuple[float, dict]:
    """Literal reading: best global-alignment identity against any one segment."""
    from locksmith.metrics.novelty import identity

    db = _db()
    best, hit = 0.0, None
    for fam in ("v", "d", "j"):
        for allele, seg in db[fam].items():
            pct = identity(cdr3, seg)
            if pct > best:
                best, hit = pct, f"{fam.upper()}:{allele}"
    return best, {"segment": hit}


def compute(heavy_seq: str, *, convention: str = "vdj_coverage") -> MetricResult:
    n = number(heavy_seq)
    if n is None:
        return MetricResult(None, skipped_reason="heavy chain is not a V domain")
    return compute_from_cdr3(n.cdr3, convention=convention)


def compute_from_cdr3(cdr3: str, *, convention: str = "vdj_coverage") -> MetricResult:
    cov, cd = vdj_coverage(cdr3)
    seg, sd = best_segment(cdr3)
    value = cov if convention == "vdj_coverage" else seg
    detail = (
        f"CDR-H3 {cdr3} ({len(cdr3)}aa) | vdj_coverage {cov:.1f}% "
        f"[V {cd.get('v')} {cd.get('v_len')}aa + D {cd.get('d')} {cd.get('d_len')}aa "
        f"+ J {cd.get('j')} {cd.get('j_len')}aa] | best_segment {seg:.1f}% "
        f"[{sd.get('segment')}] | convention={convention}"
    )
    return MetricResult(round(value, 1), detail=detail)


# ---------------------------------------------------------------------------
# V-gene assignment.  NOT part of the scored metric -- CDR-H3 identity is.  It
# exists because it is the only part of "germline" that CAN be validated against
# published calls, and because it exposes an honest limitation: the V allele
# reported by `vdj_coverage` is arbitrary among ties (173 of 249 human alleles
# contribute the identical "AR"), so that field must never be read as a call.
# ---------------------------------------------------------------------------

def assign_v(heavy_seq: str) -> tuple[str | None, float, dict]:
    """Best human IGHV allele for a heavy chain, by identity over IMGT 1-104.

    Both sides are in IMGT coordinates -- the query via ANARCII, the reference
    via ANARCI's 128-column alignment -- so this is a position-wise comparison
    with no alignment step and no gap penalties to tune.  Insertion codes are
    dropped: they occur inside CDRs, where the germline alignment has no column.
    """
    n = number(heavy_seq)
    if n is None:
        return None, 0.0, {}
    q: dict[int, str] = {}
    for (pos, ins), aa in n.numbering:
        if ins.strip() or aa == "-":
            continue
        q.setdefault(int(pos), aa)
    best, best_pct, best_d = None, 0.0, {}
    for allele, aln in _v_alignments().items():
        match = total = 0
        for i, c in enumerate(aln, start=1):
            if i > 104 or c == "-":
                continue
            if i in q:
                total += 1
                match += (q[i] == c)
        if total >= 60:
            pct = 100.0 * match / total
            if pct > best_pct:
                best, best_pct, best_d = allele, pct, {"matched": match, "compared": total}
    return best, round(best_pct, 1), best_d


@lru_cache(maxsize=1)
def _v_alignments() -> dict[str, str]:
    """Full 128-column IMGT alignments, re-read from the ANARCI harvest."""
    path = DB_PATH.parent / "human_ighv_alignments.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing -- re-run scripts/60_build_germline_db.py")
    return json.loads(path.read_text())
