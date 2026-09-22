"""Interface pLDDT.

AlphaFold writes per-residue pLDDT (0-100) into the B-factor column.  A crystal
structure's B-factor column holds thermal displacement in A^2, commonly 10-80 --
numerically indistinguishable from a plausible pLDDT.  This metric therefore
refuses to run on anything not declared a prediction.  See types.Provenance.
"""
from __future__ import annotations

from statistics import mean

from locksmith.io.pdb import read
from locksmith.metrics.interface import interface_residues
from locksmith.types import MetricResult, Structure


def compute(struct: Structure, *, cutoff: float = 5.0) -> MetricResult:
    if not struct.provenance.has_plddt:
        return MetricResult(
            None,
            skipped_reason="experimental structure: B-factor is thermal displacement, not pLDDT",
        )

    iface = interface_residues(str(struct.pdb), cutoff=cutoff)
    st = read(str(struct.pdb))
    vals: list[float] = []
    for chain in st[0]:
        wanted = iface.get(chain.name, set())
        for res in chain:
            if res.seqid.num in wanted and len(res):
                vals.append(mean(a.b_iso for a in res))

    if not vals:
        return MetricResult(None, skipped_reason="no interface residues found")
    return MetricResult(round(mean(vals), 2), detail=f"{len(vals)} interface residues")
