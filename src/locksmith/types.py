"""Core types.

The central distinction encoded here is **provenance**: whether a structure came
from a predictor or from an experiment.  It is load-bearing.

A crystal structure's B-factor column holds thermal displacement parameters in
A^2, typically 10-80.  AlphaFold writes pLDDT, 0-100, into the same column.
Reading the column without knowing which produced it yields a number that looks
entirely plausible and means something completely different.  A B-factor of 30
is not a pLDDT of 30.  So metrics declare what they require, and the harness
refuses to compute rather than guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Provenance(Enum):
    EXPERIMENT = "experiment"   # crystal/cryo-EM: no PAE, B-factor is NOT pLDDT
    PREDICTION = "prediction"   # has PAE and pLDDT

    @property
    def has_pae(self) -> bool:
        return self is Provenance.PREDICTION

    @property
    def has_plddt(self) -> bool:
        return self is Provenance.PREDICTION


@dataclass(frozen=True)
class Structure:
    """A 3-chain complex on disk, already relabelled A=heavy B=light C=antigen."""
    pdb: Path
    provenance: Provenance
    pae: Path | None = None
    label: str = ""
    predictor: str | None = None
    chain_map: dict[str, str] = field(default_factory=dict)  # original -> A/B/C

    def __post_init__(self) -> None:
        if self.provenance.has_pae and self.pae is None:
            raise ValueError(f"{self.label}: prediction declared but no PAE file given")
        if self.provenance is Provenance.EXPERIMENT and self.pae is not None:
            raise ValueError(f"{self.label}: experimental structure cannot have a PAE")


@dataclass(frozen=True)
class Sequences:
    heavy: str
    light: str
    antigen: str


@dataclass
class MetricResult:
    value: float | None
    detail: str = ""
    skipped_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.value is not None
