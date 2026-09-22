"""CDR solvent-accessible surface area, in A^2.

The handbook does not say whether SASA is measured on the complex (bound, with
the antigen burying part of the paratope) or on the antibody alone (unbound).
The two differ by hundreds of A^2 and they conflict in SIGN with the contacts
metric: a better-buried interface means more contacts but LESS bound CDR SASA.

So both are always computed and the convention is chosen in config/metrics.yaml.
"""
from __future__ import annotations

import freesasa

from locksmith.metrics.interface import cdr_residues
from locksmith.types import MetricResult, Structure

freesasa.setVerbosity(freesasa.silent)


def _cdr_area(pdb: str, chains: tuple[str, ...]) -> float:
    st = freesasa.Structure(pdb)
    res = freesasa.calc(st)
    areas = res.residueAreas()
    total = 0.0
    for ch in chains:
        for num in sum(cdr_residues(pdb, ch).values(), []):
            ra = areas.get(ch, {}).get(str(num))
            if ra is not None:
                total += ra.total
    return total


def compute(struct: Structure, *, state: str = "bound") -> dict[str, MetricResult]:
    """Returns both states; caller picks per config."""
    from locksmith.io.pdb import extract_complex
    import tempfile
    from pathlib import Path

    bound = _cdr_area(str(struct.pdb), ("A", "B"))

    # Unbound: the same antibody chains with the antigen deleted.
    with tempfile.TemporaryDirectory() as td:
        ab_only = Path(td) / "ab.pdb"
        import gemmi
        from locksmith.io.pdb import read
        st = read(str(struct.pdb))
        out = gemmi.Structure()
        out.add_model(gemmi.Model("1"))
        for name in ("A", "B"):
            out[0].add_chain(st[0][name].clone())
        out.setup_entities()
        out.write_pdb(str(ab_only))
        unbound = _cdr_area(str(ab_only), ("A", "B"))

    return {
        "cdr_sasa_bound": MetricResult(round(bound, 1), detail="complex"),
        "cdr_sasa_unbound": MetricResult(round(unbound, 1), detail="antibody alone"),
        "cdr_sasa_buried": MetricResult(round(unbound - bound, 1), detail="unbound - bound"),
    }
