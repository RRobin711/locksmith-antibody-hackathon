"""Raw metric values -> band sub-scores -> categories -> final score + viability.

Everything here is a pure function of (raw values, config).  Nothing is cached
and nothing is stored, so changing a convention in config/metrics.yaml and
re-running costs seconds rather than a re-fold.  That is the single most
important architectural property of this file.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from locksmith.config import Config, load
from locksmith.types import MetricResult


@dataclass
class Scored:
    challenge: int
    raw: dict[str, float | None]
    bands: dict[str, str] = field(default_factory=dict)
    rounding_risk: list[str] = field(default_factory=list)
    sub: dict[str, float] = field(default_factory=dict)
    categories: dict[str, float] = field(default_factory=dict)
    final: float | None = None
    viable: bool | None = None
    failing: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    thin_margin: list[str] = field(default_factory=list)

    def table(self) -> str:
        lines = [f"{'metric':<16}{'raw':>10}  {'band':<8}{'score':>6}  margin"]
        for name, v in self.raw.items():
            if v is None:
                lines.append(f"{name:<16}{'--':>10}  {'UNKNOWN':<8}{'':>6}")
                continue
            m = self._margins.get(name)
            flag = "" if m is None else f"{m:+.0%}"
            lines.append(
                f"{name:<16}{v:>10.3f}  {self.bands[name]:<8}{self.sub[name]:>6.1f}  {flag}"
            )
        return "\n".join(lines)

    _margins: dict[str, float] = field(default_factory=dict)


# How many decimals each metric carries by the time it reaches banding. Where a value is
# parsed from a tool's printed output the precision is the TOOL's, not ours.
_DISPLAY_PRECISION = {
    "dockq": 3,          # DockQ prints its summary to 3 dp (we now read --json instead)
    "ipsae": 4,          # metrics/ipsae.py rounds to 4
    "iface_plddt": 2,    # metrics/plddt.py rounds to 2
    "cdr_sasa": 1,       # metrics/sasa.py rounds to 1
    "dg": 1,             # PRODIGY prints kcal/mol to 1 dp
    "cdrh3_identity": 1,
    "netsolp": 4,
}


def evaluate(
    raw: dict[str, MetricResult | float | None], challenge: int, cfg: Config | None = None
) -> Scored:
    cfg = cfg or load()
    bands = cfg.bands()
    bs = cfg.band_scores
    values = {
        k: (v.value if isinstance(v, MetricResult) else v) for k, v in raw.items()
    }

    s = Scored(challenge=challenge, raw=values)
    for name, band in bands.items():
        if challenge not in band.challenges:
            continue
        v = values.get(name)
        if v is None:
            s.unknown.append(name)
            continue
        s.bands[name] = band.band_of(v)
        s.sub[name] = bs[s.bands[name]]
        # BAND EDGE WITHIN ROUNDING DISTANCE. Several metrics reach this function already
        # rounded for display -- ipsae 4 dp, iface_plddt 2 dp, cdr_sasa 1 dp -- and DockQ
        # and PRODIGY are parsed from tool output printed to 3 and 1 dp. Rounding is
        # harmless everywhere EXCEPT within half a unit of a band edge, where it can move
        # a value across and change the score.
        #
        # Measured 2026-09-24: DockQ's true GlobalDockQ was 0.7995794972281312, printed
        # by the tool as `0.800`, re-rounded here, and banded **good** against a 0.80
        # edge. The true value is Medium. Two composite points came from a printf.
        #
        # This does not prevent the error -- only reading the unrounded value does, which
        # dockq.compute now does -- but it makes the condition VISIBLE wherever it recurs,
        # rather than silent until an auditor recomputes it.
        _prec = _DISPLAY_PRECISION.get(name)
        if _prec is not None:
            _eps = 0.5 * 10 ** (-_prec)
            for _edge in (band.good, band.medium, band.cutoff):
                if abs(v - _edge) <= _eps:
                    s.rounding_risk.append(
                        f"{name}={v} is within its display precision "
                        f"(+/-{_eps:g}) of the {_edge:g} edge; the band may be an "
                        f"artefact of rounding")
                    break
        s._margins[name] = band.margin_fraction_achieved(v)
        if not band.passes_cutoff(v):
            s.failing.append(name)
        elif s._margins[name] < cfg.margin_fraction:
            s.thin_margin.append(name)

    if s.unknown:
        s.viable = None          # cannot assert viability with missing metrics
    else:
        s.viable = not s.failing

    for cat, members in cfg.categories.items():
        present = [s.sub[m] for m in members if m in s.sub]
        if present:
            s.categories[cat] = sum(present) / len(present)

    if len(s.categories) == len(cfg.categories) and not s.unknown:
        s.final = round(
            sum(cfg.weights[c] * v for c, v in s.categories.items()) * 10, 2
        )
    return s
