"""ColabFold / AlphaFold2-multimer driver.

DISCLOSURE GUARD -- the reason this is not just a subprocess call.

`colabfold_batch`'s default `--msa-mode mmseqs2_uniref_env` uploads the query to
the **public MMseqs2 server**. For pembrolizumab and PD-1 that is harmless: both
are published. For a *designed* sequence it is an irreversible disclosure of
unpublished work to a third party, and it is the default, so it happens unless
someone stops it.

So `msa_mode` defaults to `single_sequence`, and any server-backed mode must be
requested explicitly with `allow_public_server=True`. The guard is in code rather
than in a docstring because the failure is silent and one-way.

NOTE FOR GATE 1d: single-sequence AF2 is NOT the configuration the rubric's ipSAE
bands were calibrated on (that was AF2 with full MSAs). Comparisons across MSA
regimes need a bridge point -- fold the same unmutated complex both ways.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from locksmith.fold import FoldFailed, FoldResult, assert_artefacts

COLABFOLD = (shutil.which("colabfold_batch")
             or str(Path.home() / ".venvs/colabfold/bin/colabfold_batch"))
AF2_DATA = Path.home() / ".cache/colabfold"
SERVER_MODES = {"mmseqs2_uniref_env", "mmseqs2_uniref_env_envpair", "mmseqs2_uniref"}


def fold(label: str, heavy: str, light: str, antigen: str, *,
         out_root: Path, construct: str = "fv", seed: int = 1,
         msa_mode: str = "single_sequence", allow_public_server: bool = False,
         model_type: str = "alphafold2_multimer_v3",
         num_models: int = 1, num_recycle: int = 3,
         timeout: int = 3600) -> FoldResult:
    if msa_mode in SERVER_MODES and not allow_public_server:
        raise FoldFailed(
            f"{label}: msa_mode={msa_mode!r} uploads the query to the public "
            f"MMseqs2 server. Pass allow_public_server=True only for sequences "
            f"that are already published. Designed sequences must use "
            f"'single_sequence'.")

    out_dir = Path(out_root) / label
    out_dir.mkdir(parents=True, exist_ok=True)
    # ColabFold complex convention: chains joined by ':' on ONE line.
    fasta = out_dir / f"{label}.fasta"
    fasta.write_text(f">{label}\n{heavy}:{light}:{antigen}\n")

    cmd = [COLABFOLD, "--model-type", model_type,
           "--num-models", str(num_models), "--num-recycle", str(num_recycle),
           "--random-seed", str(seed), "--msa-mode", msa_mode,
           "--data", str(AF2_DATA), str(fasta), str(out_dir)]

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0

    pdbs = sorted(out_dir.glob(f"{label}_unrelaxed_rank_001_*.pdb"))
    jsons = sorted(out_dir.glob(f"{label}_scores_rank_001_*.json"))
    if not pdbs or not jsons:
        raise FoldFailed(
            f"{label}: ColabFold produced no rank_001 PDB/scores "
            f"(rc={proc.returncode})\n{(proc.stdout + proc.stderr)[-1200:]}")

    assert_artefacts(pdbs[0], jsons[0], None, label=label,
                     stdout=proc.stdout + proc.stderr)

    return FoldResult(
        label=label, predictor=model_type, construct=construct, seed=seed,
        pdb=pdbs[0], pae=jsons[0], plddt=None, seconds=elapsed,
        n_residues=len(heavy) + len(light) + len(antigen),
        chain_lengths=(len(heavy), len(light), len(antigen)),
    )
