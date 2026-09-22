"""A continuous stand-in for the banded rubric score, for INTERNAL ranking only.

WHY THIS EXISTS. `score.evaluate` maps each raw metric onto one of three band
sub-scores (9.5 / 7.0 / 2.5) and combines them with the rubric's category weights.
That is exactly right for REPORTING -- the organisers recompute it deterministically
from the files we hand over, so it is the number that counts. It is a poor basis for
CHOOSING between candidates, for two measured reasons:

  * Resolution. 40 designs collapsed onto three distinct values of `final`
    {82.5, 85.0, 87.5}. A wider pool adds candidates without adding ordering.
  * Noise. A step function does not attenuate measurement noise, it concentrates it
    at the band edges and delivers it as a full 2.5-point jump. 22/40 designs changed
    their single-seed `final` across Boltz seeds; single-seed reliability of `final`
    is 0.602 against DockQ's 0.727.

Both are recorded in results/m3_plan_review.md §3.

WHAT THIS DOES. Same metrics, same category weights, same rubric pricing -- the band
STEP is replaced by a piecewise-linear interpolation through the same three anchors:

    raw == cutoff  ->  the 'poor' band score
    raw == medium  ->  the 'medium' band score
    raw == good    ->  the 'good' band score

all three read from `conventions.band_value` in config/metrics.yaml, never hardcoded
here -- see `_anchors` for what happened the one time they were.

so the surrogate agrees with `final` at every anchor whose edge is INCLUSIVE, and
varies smoothly in between.

THE ONE PLACE IT CANNOT AGREE, stated because it was found by test and would
otherwise be rediscovered as a surprise. The handbook writes four good-edges with
STRICT inequalities (`contacts > 25`, `iface_plddt > 80`, `cdr_sasa > 600`,
`cdrh3_identity < 70`). A value sitting EXACTLY on such an edge is Medium in the
reported score (8.0 under `band_value: top`) but the interpolation has already
reached the Good anchor (10.0). This is intrinsic: no continuous function agrees
with a step function AT the step. It is not measure-zero either -- `contacts` is an
integer count, so "exactly 25" is an ordinary outcome, not a coincidence.
The surrogate therefore ranks such a design Good-side while we report it Medium.
That is the intended direction (the surrogate exists to break ties the bands cannot
resolve) but it must never be quoted as though the two scales agreed.
Pinned by `test_surrogate_diverges_only_at_strict_edges`. It is absolute, not pool-relative: a rank-normalised surrogate would make two
runs incomparable and would let the pool's composition change a design's score.

Beyond `good` the same slope continues, clamped at 10; below `cutoff` it continues
downward, clamped at 0. Gating is NOT done here -- viability still comes from
`score.evaluate`, because a gate is a property of the rubric, not of our ranking.

MARGIN, AND WHY IT IS A SEPARATE NUMBER. `band_margin` reports how far the worst
metric sits from the nearest band edge, in units of that metric's cutoff->good span.
A design scoring well because every metric sits mid-band is worth more than one
scoring the same with a metric 0.002 from an edge, because the edge one is a coin
flip on the seed. This is the same idea the config already applies to gates as
`margin_fraction`; it is applied to band edges here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from locksmith.config import Config, load


def _anchors(cfg: Config) -> tuple[float, float, float]:
    """The three band sub-scores, FROM CONFIG.

    These were hardcoded as 2.5/7.0/9.5 (the `midpoint` reading) until 2026-09-22,
    while `config/metrics.yaml` had been switched to `band_value: top` on 2026-09-20.
    The surrogate never read the config, so the thing we RANKED on and the thing we
    REPORTED silently drifted two conventions apart -- an all-medium design scored
    final=80.0 and surrogate=70.0, and the segment slopes changed non-uniformly
    (1.8 -> 1.5), which can invert a ranking rather than just relabel it. The
    submitted Challenge 1 winner was selected on the diverged surrogate.

    Pinned by `tests/test_invariants.py::test_surrogate_anchors_match_config_band_values`
    and, behaviourally, by `test_surrogate_equals_final_at_the_anchors`.
    """
    bs = cfg.band_scores
    return bs["poor"], bs["medium"], bs["good"]


ANCHOR_POOR, ANCHOR_MEDIUM, ANCHOR_GOOD = _anchors(load())


@dataclass
class Surrogate:
    value: float                                    # 0-100, same scale as `final`
    sub: dict[str, float] = field(default_factory=dict)
    categories: dict[str, float] = field(default_factory=dict)
    band_margin: float | None = None                # worst metric's distance to an edge
    limiting: str | None = None                     # which metric that was
    missing: tuple[str, ...] = ()                   # scored metrics that did not compute


def _interp(v: float, cutoff: float, medium: float, good: float,
            anchors: tuple[float, float, float] | None = None) -> float:
    """Piecewise-linear through (cutoff, poor), (medium, medium), (good, good),
    where the three sub-scores come from `conventions.band_value` -- NOT from
    constants in this file. See `_anchors`.

    Works for both directions because the three anchors are monotone in the raw value
    either way: for a 'low' metric cutoff > medium > good and every span below is
    negative, which flips the comparisons consistently.
    """
    a_poor, a_med, a_good = anchors or (ANCHOR_POOR, ANCHOR_MEDIUM, ANCHOR_GOOD)
    hi_span = good - medium
    lo_span = medium - cutoff

    # Upper segment first. It is well defined even when cutoff == medium, which is the
    # case for `ipsae` (0.60/0.60) and `netsolp` (0.50/0.50) -- a degenerate LOWER span
    # must not be allowed to swallow values sitting at or above `medium`. Getting this
    # wrong scored a design sitting exactly on `good` as 7.0 instead of 9.5, caught by
    # the anchor-agreement test rather than by reading the code.
    if hi_span != 0 and (v - medium) / hi_span >= 0:
        t = (v - medium) / hi_span
        return min(10.0, a_med + t * (a_good - a_med))

    # Lower segment. When cutoff == medium there is no interval to interpolate over:
    # anything below `medium` is also below `cutoff`, i.e. failing, and `band_of` calls
    # it 'poor'. Return the poor anchor. Such designs are gated out by score.evaluate
    # anyway, so the surrogate never has to rank them against each other.
    if lo_span == 0:
        return a_poor
    t = (v - cutoff) / lo_span
    return max(0.0, a_poor + t * (a_med - a_poor))


def _edge_distance(v: float, cutoff: float, medium: float, good: float) -> float:
    """Distance from the nearest band edge, as a fraction of the cutoff->good span.

    Larger is safer. A design sitting exactly on an edge scores 0 and is one seed's
    noise away from a 2.5-point swing in the reported score.
    """
    span = abs(good - cutoff)
    if span == 0:
        return 0.0
    return min(abs(v - medium), abs(v - good)) / span


def compute(raw: dict[str, float | None], challenge: int,
            cfg: Config | None = None) -> Surrogate:
    cfg = cfg or load()
    bands = cfg.bands()
    anchors = _anchors(cfg)
    sub, margins, missing = {}, {}, []
    for name, b in bands.items():
        if challenge not in b.challenges:
            continue
        v = raw.get(name)
        if v is None:
            # NOT `continue`. A category mean over the SURVIVING members silently
            # rewards a design whose worst metric failed to compute: drop the worst
            # of binding's six and the mean of the other five rises. `score.evaluate`
            # already refuses a `final` under these conditions (`s.unknown`); the
            # surrogate is what we rank on, so it must refuse at least as loudly.
            missing.append(name)
            continue
        sub[name] = _interp(v, b.cutoff, b.medium, b.good, anchors)
        margins[name] = _edge_distance(v, b.cutoff, b.medium, b.good)

    categories = {}
    for cat, members in cfg.categories.items():
        present = [sub[m] for m in members if m in sub]
        if present:
            categories[cat] = sum(present) / len(present)

    if missing or len(categories) != len(cfg.categories):
        return Surrogate(value=float("nan"), sub=sub, categories=categories,
                         missing=tuple(missing))

    value = sum(cfg.weights[c] * v for c, v in categories.items()) * 10
    limiting = min(margins, key=margins.get) if margins else None
    return Surrogate(value=value, sub=sub, categories=categories,
                     band_margin=(margins[limiting] if limiting else None),
                     limiting=limiting)
