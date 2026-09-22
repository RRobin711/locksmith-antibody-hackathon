"""IMGT numbering and CDR extraction via ANARCII.

IMGT CDR position ranges (the scheme the handbook specifies):
    CDR1  27-38      CDR2  56-65      CDR3  105-117

These are positions in the IMGT scheme, not indices into the sequence.  IMGT
inserts gaps and insertion codes so that equivalent positions align across
antibodies with different loop lengths -- which is the whole reason to use it.
"CDR-H3" then names the same structural element in every antibody, and a
novelty comparison between two different antibodies is meaningful.

ANARCII returns numbering as [((position:int, insertion:str), residue:str), ...]
with '-' for gaps, and always numbers in IMGT internally (`to_scheme` converts).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

IMGT_CDR = {"cdr1": (27, 38), "cdr2": (56, 65), "cdr3": (105, 117)}
Position = tuple[int, str]


@dataclass(frozen=True)
class Numbered:
    chain_type: str                      # 'H' heavy | 'K' kappa | 'L' lambda
    score: float                         # ANARCII confidence; low => not an antibody domain
    query_start: int                     # residue span of the variable domain within the
    query_end: int                       #   input sequence -- everything after is constant
    numbering: list[tuple[Position, str]]
    cdr1: str
    cdr2: str
    cdr3: str

    @property
    def fv(self) -> str:
        """The variable domain only, gaps removed."""
        return "".join(aa for _, aa in self.numbering if aa != "-")

    def span(self, lo: int, hi: int) -> str:
        return "".join(aa for (pos, _), aa in self.numbering if lo <= pos <= hi and aa != "-")


@lru_cache(maxsize=1)
def _model():
    from anarcii import Anarcii

    return Anarcii(seq_type="antibody", verbose=False)


# PD-1 is an immunoglobulin-superfamily member with an IgV fold, so ANARCII
# recognises it as antibody-like and happily assigns it CDRs (measured: score
# ~16 for 5GGS chains Y/Z).  Genuine antibody V domains score ~31.  A permissive
# threshold therefore silently classifies the *antigen* as an antibody chain and
# every downstream CDR metric is then computed on the wrong molecule.
# Measured on 5GGS/5WT9: true V domains 30.8-30.9, PD-1 15.8-16.2.
MIN_V_DOMAIN_SCORE = 25.0


def number(seq: str, *, min_score: float = MIN_V_DOMAIN_SCORE) -> Numbered | None:
    """Number one sequence. Returns None if it is not a recognisable V domain.

    See MIN_V_DOMAIN_SCORE: the threshold is load-bearing, not cosmetic.
    """
    rec = next(iter(_model().number([("q", seq)]).values()))
    if rec is None or rec.get("error") or rec.get("chain_type") in (None, "", "F"):
        return None
    if rec.get("score", 0.0) < min_score:
        return None

    pairs = [(p, aa) for p, aa in rec["numbering"]]
    n = Numbered(
        chain_type=rec["chain_type"],
        score=float(rec["score"]),
        query_start=int(rec["query_start"]),
        query_end=int(rec["query_end"]),
        numbering=pairs,
        cdr1="", cdr2="", cdr3="",
    )
    return Numbered(
        chain_type=n.chain_type, score=n.score,
        query_start=n.query_start, query_end=n.query_end, numbering=pairs,
        cdr1=n.span(*IMGT_CDR["cdr1"]),
        cdr2=n.span(*IMGT_CDR["cdr2"]),
        cdr3=n.span(*IMGT_CDR["cdr3"]),
    )
