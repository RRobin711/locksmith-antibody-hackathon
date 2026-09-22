"""Typed access to config/metrics.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path("config/metrics.yaml")


@dataclass(frozen=True)
class Band:
    name: str
    direction: str          # 'high' | 'low'
    good: float
    medium: float
    cutoff: float
    challenges: tuple[int, ...]
    requires: tuple[str, ...]
    strict_good: bool = False       # handbook uses "> x" rather than ">= x" for this edge
    strict_cutoff: bool = False     # ditto for the viability cutoff

    def better(self, a: float, b: float, *, strict: bool = False) -> bool:
        if self.direction == "high":
            return a > b if strict else a >= b
        return a < b if strict else a <= b

    def passes_cutoff(self, v: float) -> bool:
        return self.better(v, self.cutoff, strict=self.strict_cutoff)

    def band_of(self, v: float) -> str:
        # BOUNDARY INCLUSIVITY IS NOT COSMETIC. The handbook writes four of these edges
        # with STRICT inequalities -- contacts "> 25", interface pLDDT "> 80", CDR SASA
        # "> 600", CDR-H3 identity "< 70%" -- and two viability cutoffs likewise
        # (CDR SASA "> 250", identity "< 95%"). Treating them as inclusive scores a
        # boundary value one band too high. On cdrh3_identity that is worth 5.0 final
        # points, because novelty carries the full 0.20 weight on a single metric, and
        # a 10-residue CDR-H3 with 7 matches lands on exactly 70.0%. Flagged 2026-09-20
        # by an independent audit against the handbook; previously every edge was
        # inclusive.
        if self.better(v, self.good, strict=self.strict_good):
            return "good"
        if self.better(v, self.medium):
            return "medium"
        return "poor"

    def required_with_margin(self, fraction: float) -> float:
        span = self.good - self.cutoff          # signed; negative when direction=='low'
        return self.cutoff + fraction * span

    def margin_fraction_achieved(self, v: float) -> float:
        """How far past the cutoff, as a fraction of the cutoff->good span."""
        span = self.good - self.cutoff
        return 0.0 if span == 0 else (v - self.cutoff) / span


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any]

    @property
    def conventions(self) -> dict[str, Any]:
        return self.raw["conventions"]

    @property
    def weights(self) -> dict[str, float]:
        return self.raw["weights"]

    @property
    def margin_fraction(self) -> float:
        return float(self.raw["margin_fraction"])

    @property
    def band_scores(self) -> dict[str, float]:
        """Band -> 0-10 sub-score, selected by `conventions.band_value`.

        `band_scores:` in the YAML is retained only as an explicit override for
        reproducing pre-2026-09-20 numbers; when `band_value` is set it wins, because
        the handbook specifies ranges and not the point values that block ever held.
        """
        bv = self.band_value
        if bv not in self.BAND_VALUES:
            raise ValueError(f"band_value must be one of {sorted(self.BAND_VALUES)}, "
                             f"got {bv!r}")
        return dict(self.BAND_VALUES[bv])

    # HOW A BAND BECOMES A NUMBER IS NOT IN THE HANDBOOK.
    # S5.2 gives RANGES -- "Good (9-10)", "Medium (6-8)", "Poor (0-5)" -- and S5.1 gives
    # the weighting formula, but nothing states how to pick a value inside a band.
    # Three readings are implementable from the handbook alone:
    #   bottom   9 / 6 / 0     most conservative; caps the maximum at 90
    #   midpoint 9.5 / 7 / 2.5 what this project used until 2026-09-20; caps it at 95
    #   top      10 / 8 / 5    the only one that attains the 0-100 range S7.3 states
    # A fourth -- interpolating within each band on the raw value -- is equally permitted
    # by the text and is NOT implemented, because it needs an upper anchor (what raw
    # value maps to 10?) that the handbook never gives.
    # NOTE the choice is a monotone relabelling applied uniformly, so it moves the
    # headline number and CANNOT change the ordering of two designs.
    BAND_VALUES = {
        "bottom":   {"good": 9.0, "medium": 6.0, "poor": 0.0},
        "midpoint": {"good": 9.5, "medium": 7.0, "poor": 2.5},
        "top":      {"good": 10.0, "medium": 8.0, "poor": 5.0},
    }

    @property
    def band_value(self) -> str:
        return self.conventions.get("band_value", "top")

    @property
    def categories(self) -> dict[str, list[str]]:
        return self.raw["categories"]

    def bands(self) -> dict[str, Band]:
        return {
            name: Band(
                name=name, direction=m["direction"], good=float(m["good"]),
                medium=float(m["medium"]), cutoff=float(m["cutoff"]),
                challenges=tuple(m["challenges"]), requires=tuple(m.get("requires", ())),
                strict_good=bool(m.get("strict_good", False)),
                strict_cutoff=bool(m.get("strict_cutoff", False)),
            )
            for name, m in self.raw["metrics"].items()
        }


@lru_cache(maxsize=1)
def load(path: str | Path = CONFIG_PATH) -> Config:
    return Config(yaml.safe_load(Path(path).read_text()))
