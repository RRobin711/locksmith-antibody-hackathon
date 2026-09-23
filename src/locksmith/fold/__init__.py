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


def fold_is_complete(pred_dir: Path, label: str, *, n_models: int = 1) -> bool:
    """Has this fold already produced `n_models` scorable models? Resume keys on THIS.

    WHY THIS EXISTS AS A FUNCTION. Four driver scripts each grew their own resume check,
    and every one of them called `assert_artefacts(dir, label)` -- which is not its
    signature. The call raised `TypeError`, each script caught it with a bare
    `except Exception`, and the error was silently read as "not folded yet". A completed
    40-complex panel would have been refolded from scratch on any restart, and nothing
    would have said so. The bug survived because the failure mode of a resume check is
    invisible in the direction it failed: re-doing finished work looks exactly like
    doing work.

    Note the asymmetry that makes this dangerous. Had the boolean been inverted -- had the
    swallowed exception meant "done" -- the same bug would have SKIPPED every fold and
    produced an empty panel that looked complete. A resume predicate must therefore
    distinguish "the artefacts say no" from "the check itself is broken", which is why
    only `FoldFailed` is caught here and every other exception propagates.

    Pinned by `tests/test_invariants.py::test_fold_is_complete_distinguishes_absent_from_broken`.
    """
    if not pred_dir.is_dir():
        return False
    for i in range(n_models):
        tag = f"{label}_model_{i}"
        try:
            assert_artefacts(pred_dir / f"{tag}.pdb",
                             pred_dir / f"pae_{tag}.npz",
                             pred_dir / f"plddt_{tag}.npz",
                             label=tag)
        except FoldFailed:
            return False
    return True
