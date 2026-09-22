"""Boltz `.npz` -> the AlphaFold-style `design_X_pae.json` the handbook requires.

WHY THIS EXISTS, AND WHY ITS ABSENCE WAS FATAL
-----------------------------------------------
The handbook's deliverable list requires, per design:

    structures/design_X_complex.pdb
    structures/design_X_pae.json      "AlphaFold-style PAE (Predicted Aligned Error) file"

Boltz writes `pae_<label>_model_0.npz`, and until 2026-09-20 nothing in this project
converted it. That is not a cosmetic gap. ipSAE is the only metric scored in BOTH
challenges, the organisers recompute it from the files we hand over, and it reads the
PAE from `design_X_pae.json`. Without the converter the submission fails format
validation AND loses the metric.

FORMAT. `vendor/ipsae/ipsae.py` (the pinned scoring script) reads a `.json` PAE as a
JSON **object**, looking for `pae` or `predicted_aligned_error`, and optionally
`plddt`, `ptm`, `iptm` (lines 427-455). That is the ColabFold/AF2 `*_scores_*.json`
shape, so this writer emits exactly that: a dict, not the AlphaFold-DB list-wrapped
form, which `json.load` would return as a list and which would make `'pae' in data`
test list membership and silently find nothing.

TOKENS VERSUS RESIDUES, ASSERTED NOT ASSUMED. Boltz indexes the PAE by *token*. For a
protein-only complex one token is one residue, so the matrix is already residue-indexed
and `ipsae.py`'s own token mask is a no-op. That is true here and false the moment a
ligand, ion or modified residue appears. So the writer asserts
`pae.shape[0] == number of CA atoms in the PDB` and refuses otherwise rather than
emitting a silently misaligned matrix -- the same rule as everywhere else in this
project: assert on the artefact, never assume the happy path.

pLDDT is written on the 0-100 scale. Boltz stores it normalised in some versions and
not in others, so the scale is detected from the data exactly as ipsae.py does it.
"""
from __future__ import annotations

import json
from pathlib import Path

import gemmi
import numpy as np


def _ca_count(pdb: Path) -> int:
    st = gemmi.read_structure(str(pdb))
    st.remove_hydrogens()
    return sum(1 for ch in st[0] for r in ch if r.find_atom("CA", "*"))


def write_pae_json(pdb: Path, pae_npz: Path, out: Path, *,
                   plddt_npz: Path | None = None,
                   confidence_json: Path | None = None) -> Path:
    """Emit the handbook's `design_X_pae.json`. Returns the path written."""
    pae = np.asarray(np.load(pae_npz)["pae"], dtype=float)
    if pae.ndim != 2 or pae.shape[0] != pae.shape[1]:
        raise ValueError(f"{pae_npz}: expected a square PAE matrix, got {pae.shape}")

    n_ca = _ca_count(pdb)
    if pae.shape[0] != n_ca:
        raise ValueError(
            f"{pae_npz}: PAE is {pae.shape[0]}x{pae.shape[0]} but {pdb.name} has {n_ca} "
            f"CA atoms. Boltz indexes the PAE by token; this complex is not one token "
            f"per residue, so the matrix would be written misaligned. Refusing.")

    doc: dict[str, object] = {
        "predicted_aligned_error": np.round(pae, 2).tolist(),
        "max_predicted_aligned_error": float(np.round(pae.max(), 2)),
    }
    if plddt_npz is not None and Path(plddt_npz).exists():
        raw = np.asarray(np.load(plddt_npz)["plddt"], dtype=float)
        if raw.size != n_ca:
            raise ValueError(f"{plddt_npz}: {raw.size} values for {n_ca} residues")
        # Boltz normalises pLDDT in some versions; ipsae.py applies the same test.
        doc["plddt"] = np.round(raw * 100.0 if raw.max() <= 1.0 else raw, 2).tolist()
    if confidence_json is not None and Path(confidence_json).exists():
        c = json.loads(Path(confidence_json).read_text())
        for k_out, k_in in (("ptm", "ptm"), ("iptm", "iptm")):
            if k_in in c:
                doc[k_out] = float(c[k_in])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc))
    return out
