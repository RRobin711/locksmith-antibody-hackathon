"""Ranking and selection.

THE GATES ARE STRUCTURAL, NOT ADVISORY
--------------------------------------
`rank()` cannot return a non-viable design in its ranked list. Viability is not a
column the caller is trusted to filter on; non-viable designs are partitioned out
before any ordering happens, and a design whose viability is UNKNOWN (a metric
failed to compute) is treated as non-viable rather than optimistically included.
`score.evaluate()` already computes `viable` as "no metric below its cutoff, and
no metric missing"; this module's job is to make it impossible to ignore.

WHAT WE RANK ON, AND WHY IT IS THE RUBRIC COMPOSITE
---------------------------------------------------
The obvious alternative is to rank on DockQ, on the grounds that among live
designs ipSAE barely discriminates (panel: Fab R^2 0.755 -> 0.263 once the dead
anchors are removed). That would be a mistake, for two measured reasons.

1. **The rubric already states the trade, and it favours novelty 2:1 over DockQ.**
   Measured against config/metrics.yaml: one band step on CDR-H3 identity moves
   the final score by **14.0 points**; one band step on DockQ moves it by **7.0**.
   A faithful design (96% CDR-H3 identity, DockQ 0.88) scores 81.0 and is
   NON-VIABLE -- it fails the novelty gate. A divergent one (55% identity, DockQ
   0.55) scores 92.5 and is viable. Ranking on DockQ would invert the customer's
   stated preference and systematically promote near-copies of pembrolizumab.

2. **Banding neutralises ipSAE's flatness rather than amplifying it.** Sub-scores
   are band midpoints (9.5 / 7.0 / 2.5), so a metric that sits in the same band
   for every live design contributes a CONSTANT. It supplies no ranking signal,
   but it injects no noise either. ipSAE's non-discrimination therefore costs far
   less inside a banded composite than it would in a continuous sort.

So: rank on `final`, the rubric composite. DockQ is the **tiebreaker**, which is
where its extra resolution is genuinely useful and where it cannot override the
novelty weighting. The convention is recorded in config/metrics.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from locksmith.score import Scored


@dataclass(frozen=True)
class Candidate:
    design_id: str
    scored: Scored
    meta: dict


@dataclass
class Selection:
    ranked: list[Candidate]          # viable only, best first
    rejected: list[Candidate]        # failed >=1 hard gate
    unknown: list[Candidate]         # viability could not be established
    gate_failures: dict[str, int]    # metric -> how many designs it rejected

    @property
    def n_viable(self) -> int:
        return len(self.ranked)


def rank(candidates: Iterable[Candidate], *,
         tiebreakers: Sequence[str] = ("dockq", "cdrh3_identity")) -> Selection:
    ranked, rejected, unknown = [], [], []
    failures: dict[str, int] = {}
    for c in candidates:
        if c.scored.viable is None:
            unknown.append(c)
        elif c.scored.viable:
            ranked.append(c)
        else:
            rejected.append(c)
            for m in c.scored.failing:
                failures[m] = failures.get(m, 0) + 1

    def key(c: Candidate):
        k = [-(c.scored.final if c.scored.final is not None else -1e9)]
        for t in tiebreakers:
            v = c.scored.raw.get(t)
            # dockq: higher better. cdrh3_identity: LOWER is better (novelty).
            if v is None:
                k.append(0.0)
            elif t == "cdrh3_identity":
                k.append(v)
            else:
                k.append(-v)
        return tuple(k)

    ranked.sort(key=key)
    return Selection(ranked=ranked, rejected=rejected, unknown=unknown,
                     gate_failures=failures)
