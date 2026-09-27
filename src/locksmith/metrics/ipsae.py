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

import shutil
import subprocess
import sys
import tempfile
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
    # RUN IN A TEMP DIRECTORY. ipsae.py derives its output paths from the INPUT path, so
    # it writes `<pdb-stem>_<pae>_<dist>.txt`, `_byres.txt` and a `.pml` next to whatever
    # it was pointed at. Pointed at the packaged submission -- which is what
    # scripts/58_validate_submission.py does -- it drops three stray files into
    # `structures/`, and `submit/package.py` then refuses to rebuild because SS4.2.1
    # specifies exactly design_X_complex.pdb and design_X_pae.json. Running the validator
    # therefore broke the packager. Found 2026-09-26.
    #
    # Basenames are preserved exactly on the way in, because ipsae.py locates the pLDDT
    # array by string-substituting 'pae'->'plddt' in the PAE path. Rename or relocate
    # either file and it writes an EMPTY table and exits 0.
    with tempfile.TemporaryDirectory(prefix="ipsae_") as td:
        work = Path(td)
        staged_pae = work / pae.name
        shutil.copy2(pae, staged_pae)
        staged_pdb = work / Path(struct.pdb).name
        shutil.copy2(struct.pdb, staged_pdb)
        if pae.suffix == ".npz":
            sib = pae.with_name(pae.name.replace("pae", "plddt"))
            shutil.copy2(sib, work / sib.name)

        proc = subprocess.run(
            [sys.executable, str(IPSAE.resolve()), str(staged_pae), str(staged_pdb),
             str(pae_cutoff), str(dist_cutoff)],
            capture_output=True, text=True, timeout=600,
        )
        stem = str(staged_pdb).rsplit(".", 1)[0]
        table = Path(f"{stem}_{pae_cutoff}_{dist_cutoff}.txt")
        if not table.exists():
            candidates = sorted(work.glob(f"{Path(stem).name}*.txt"))
            if not candidates:
                raise RuntimeError(f"ipsae produced no table:\n{proc.stdout}\n{proc.stderr}")
            table = candidates[0]
        text = table.read_text()

    lines = [ln.split() for ln in text.splitlines() if ln.strip()]
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
