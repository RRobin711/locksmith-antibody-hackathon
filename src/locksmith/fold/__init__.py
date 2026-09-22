"""Structure-prediction drivers.

One interface over Boltz-2 and ColabFold/AlphaFold2, because Gate 1d needs the
same complex folded by both and scored by the same code.

THE INVARIANT THIS MODULE EXISTS TO ENFORCE
-------------------------------------------
**A fold counts only when its artefacts exist and parse. The exit code is never
consulted.** On 2026-09-15, three of four failed Boltz runs exited 0 -- a missing
CUDA kernel, a host-RAM kill, and a CUDA OOM that printed
`Number of failed examples: 1` underneath a `100%` progress bar. A batch keyed on
return status marks all three complete and skips them forever, and the resulting
gap is invisible because the output directory exists and looks plausible.

So `fold()` raises `FoldFailed` unless it can point at a PDB that parses, a PAE
matrix, and a pLDDT array.

FILE NAMING IS LOAD-BEARING -- DO NOT "TIDY" THE OUTPUT
------------------------------------------------------
`vendor/ipsae/ipsae.py` locates the pLDDT array by string-substituting the PAE
path (`pae_file.replace("pae", "plddt")`). A Boltz PAE must therefore keep its
`pae_<name>_model_<n>.npz` name AND keep `plddt_<name>_model_<n>.npz` as a
sibling in the same directory. Rename or relocate either and ipsae writes an
EMPTY table and exits 0. This module returns paths *in place* and never copies
or renames them; callers get paths, not files.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class FoldFailed(RuntimeError):
    """A fold produced no usable artefact, whatever its exit code said."""


@dataclass(frozen=True)
class FoldResult:
    label: str
    predictor: str            # 'boltz2' | 'alphafold2_multimer_v3'
    construct: str            # 'fv' | 'fab'
    seed: int
    pdb: Path
    pae: Path
    plddt: Path | None        # Boltz only; AF2 carries pLDDT in the PDB B-factor
    seconds: float
    n_residues: int
    chain_lengths: tuple[int, int, int]

    @property
    def ok(self) -> bool:
        return self.pdb.exists() and self.pae.exists()


def assert_artefacts(pdb: Path, pae: Path, plddt: Path | None, *,
                     label: str, stdout: str = "") -> None:
    """Raise unless every promised artefact exists and parses.

    Existence is not enough: a truncated .npz exists and fails at read time, and
    a 0-byte PDB satisfies `.exists()`.
    """
    import numpy as np

    missing = [p for p in (pdb, pae) if p is None or not p.exists()]
    if plddt is not None and not plddt.exists():
        missing.append(plddt)
    if missing:
        raise FoldFailed(
            f"{label}: fold produced no {', '.join(str(m.name) for m in missing)}"
            f"\n--- tail of tool output ---\n{stdout[-1200:]}")

    if pdb.stat().st_size == 0:
        raise FoldFailed(f"{label}: PDB is empty")
    atoms = sum(1 for ln in pdb.read_text().splitlines() if ln.startswith("ATOM"))
    if atoms == 0:
        raise FoldFailed(f"{label}: PDB contains no ATOM records")

    if pae.suffix == ".npz":
        try:
            with np.load(pae) as z:
                arr = z[list(z.keys())[0]]
        except Exception as e:                                  # noqa: BLE001
            raise FoldFailed(f"{label}: PAE .npz will not load: {e}") from e
        if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
            raise FoldFailed(f"{label}: PAE is not a square matrix, got {arr.shape}")
