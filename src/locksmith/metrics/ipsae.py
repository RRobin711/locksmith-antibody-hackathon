"""ipSAE -- interface confidence from the PAE matrix.

Requires a PREDICTED structure: an experimental structure has no PAE and the
metric is undefined, not zero.

FILE NAMING IS LOAD-BEARING FOR BOLTZ INPUTS.  ipsae.py locates the pLDDT array
by string-substituting the PAE path: `pae_file_path.replace("pae", "plddt")`.
So a Boltz PAE must keep its `pae_<name>_model_<n>.npz` name AND keep
`plddt_<name>_model_<n>.npz` as a sibling in the same directory.  Rename or
relocate either and ipsae writes an EMPTY results table and exits without error
-- another silent failure to guard against rather than discover downstream.

The handbook says the pipeline "reads rows with Type = max for antibody vs
antigen chains, and takes the best ipSAE among them", so that is reproduced
exactly.  The script also takes pae_cutoff and dist_cutoff, which the handbook
never specifies -- they are configuration, defaulting to the repo's documented
10 / 15.  See config/metrics.yaml.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from locksmith.types import MetricResult, Structure

IPSAE = Path("vendor/ipsae/ipsae.py")
AB, AG = {"A", "B"}, "C"


def compute(
    struct: Structure, *, pae_cutoff: int = 10, dist_cutoff: int = 15
) -> dict[str, MetricResult]:
    if not struct.provenance.has_pae:
        return {"ipsae": MetricResult(
            None, skipped_reason="experimental structure has no PAE matrix")}

    pae = Path(struct.pae)
    if pae.suffix == ".npz":                       # Boltz: needs a plddt sibling
        sib = pae.with_name(pae.name.replace("pae", "plddt"))
        if not sib.exists():
            return {"ipsae": MetricResult(
                None,
                skipped_reason=f"Boltz PAE needs sibling {sib.name}; ipsae.py derives it "
                               f"by replacing 'pae'->'plddt' in the path",
            )}
    proc = subprocess.run(
        [sys.executable, str(IPSAE), str(pae), str(struct.pdb),
         str(pae_cutoff), str(dist_cutoff)],
        capture_output=True, text=True, timeout=600,
    )
    stem = str(struct.pdb).rsplit(".", 1)[0]
    table = Path(f"{stem}_{pae_cutoff}_{dist_cutoff}.txt")
    if not table.exists():
        candidates = sorted(Path(struct.pdb).parent.glob(f"{Path(stem).name}*.txt"))
        if not candidates:
            raise RuntimeError(f"ipsae produced no table:\n{proc.stdout}\n{proc.stderr}")
        table = candidates[0]

    lines = [ln.split() for ln in table.read_text().splitlines() if ln.strip()]
    if not lines:
        return {"ipsae": MetricResult(
            None, skipped_reason=f"ipsae produced an empty table; stderr: {proc.stderr[-300:]}")}
    header, *rows = lines
    idx = {name: i for i, name in enumerate(header)}
    best, detail = None, []
    for r in rows:
        if len(r) <= idx.get("ipSAE", 99):
            continue
        c1, c2, typ = r[idx["Chn1"]], r[idx["Chn2"]], r[idx["Type"]]
        if typ != "max":
            continue
        pair = {c1, c2}
        if not (pair & AB and AG in pair):        # antibody-vs-antigen only
            continue
        val = float(r[idx["ipSAE"]])
        detail.append(f"{c1}-{c2}={val:.3f}")
        best = val if best is None else max(best, val)

    if best is None:
        return {"ipsae": MetricResult(None, skipped_reason="no Ab-vs-Ag 'max' rows found")}
    return {"ipsae": MetricResult(round(best, 4), detail=" ".join(detail))}
