"""Boltz-2 driver.

THE CONFIGURATION IS NOT DEFAULTS -- every flag below was bought with a failure.

`--no_kernels`      the optimised CUDA kernels need `cuequivariance_torch`, whose
                    absence produced an import error and exit 0. Pure PyTorch is
                    slower and works.
`--num_workers 0`   dataloader workers multiply host RAM; a fold was OOM-killed
                    by the kernel with workers > 0.
antibody MSA `empty`  an antibody and its antigen have not co-evolved, so an
                    antibody alignment carries no interface signal -- this is why
                    IgFold and ABodyBuilder2 work from single sequences. It is
                    also where the memory goes: alignments dominate the pair
                    representation, and dropping two of three chains' MSAs cut
                    VRAM by ~2/3 and fixed a CUDA OOM. Correct protocol and cheap
                    protocol coinciding.
`--max_msa_seqs 1024`  caps the antigen alignment.

THE ANTIGEN MSA IS CACHED ON PURPOSE (data/msa_cache/pd1_5ggs.csv, 3787 seqs).
Two reasons, one scientific and one about disclosure:
  - Every variant in a ranking panel must see the *identical* antigen alignment.
    Re-querying the MMseqs2 server per fold would let the alignment drift between
    designs and put uncontrolled variance straight into the quantity being ranked.
  - `--use_msa_server` uploads any chain whose MSA field is blank to the PUBLIC
    ColabFold server. Antibody chains are `empty` so they are never sent, but the
    cache removes the server from the loop entirely, which is the only way to be
    sure a designed sequence never leaves the machine.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from locksmith.fold import FoldFailed, FoldResult, assert_artefacts

BOLTZ = shutil.which("boltz") or "boltz"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")

# The vault path contains a space ("Obsidian Personal") and Boltz's FASTA parser
# splits the MSA field on whitespace: it reported
#     FileNotFoundError: MSA file /home/rrobin711/Obsidian not found.
# then printed a 100% progress bar, initialised the GPU and carried on. Another
# fatal-error-with-exit-0. So MSA files are staged to a space-free cache and the
# FASTA only ever carries that path.
MSA_STAGE = Path.home() / ".cache/locksmith/msa"


def _stage(msa: Path) -> Path:
    """Return a path to `msa` guaranteed free of whitespace."""
    resolved = msa.resolve()
    if " " not in str(resolved):
        return resolved
    MSA_STAGE.mkdir(parents=True, exist_ok=True)
    staged = MSA_STAGE / resolved.name
    if not staged.exists() or staged.stat().st_mtime < resolved.stat().st_mtime:
        shutil.copy2(resolved, staged)
    if " " in str(staged):
        raise FoldFailed(f"staged MSA path still contains a space: {staged}")
    return staged


def _msa_query_length(msa: Path) -> int | None:
    """Length of the cached alignment's query row (its first sequence), gaps removed."""
    import csv

    try:
        rows = list(csv.reader(msa.read_text().splitlines()))
    except Exception:                                        # noqa: BLE001
        return None
    if len(rows) < 2:
        return None
    header = [c.strip().lower() for c in rows[0]]
    if "sequence" not in header:
        return None
    return len(rows[1][header.index("sequence")].replace("-", ""))


def write_input(path: Path, heavy: str, light: str, antigen: str,
                *, antigen_msa: Path | None = PD1_MSA,
                allow_msa_mismatch: bool = False) -> Path:
    """Boltz FASTA: >CHAIN|entity|msa. The literal `empty` means no alignment.

    REFUSES a cached alignment whose query length differs from the antigen, because Boltz
    SILENTLY DISCARDS such an alignment. `featurizerv2.py` compares
    `len(residues) == len(first_residues)` and, on mismatch, prints
    `Warning: MSA does not match input sequence, creating dummy.` to stdout and replaces
    the MSA with a dummy. No exception, no non-zero exit, no marker in any output file.

    The check is on LENGTH ALONE -- a query that is an exact substring of the input at
    offset 5 is treated exactly like an unrelated sequence.

    Measured 2026-09-23: the shipped Challenge 2 structure was folded this way. The cached
    PD-1 alignment has a 113-residue query; the fold passed it alongside the handbook's
    123-residue antigen, and `runs/sequon_fix.log` carries that warning twice. The antigen
    was folded in single-sequence mode and nothing in the pipeline said so. Worse, the
    processed `msa/*.npz` still records 1024 sequences at width 113, so inspecting the
    artefact SUGGESTS THE ALIGNMENT WAS USED.

    `allow_msa_mismatch=True` is for deliberately reproducing that pairing -- see
    `scripts/94_msa_register.py`, which measures what the discard cost.
    """
    if antigen_msa is not None and not allow_msa_mismatch:
        qlen = _msa_query_length(Path(antigen_msa))
        if qlen is not None and qlen != len(antigen):
            raise FoldFailed(
                f"cached MSA {Path(antigen_msa).name} has a {qlen}-residue query but the "
                f"antigen is {len(antigen)} residues. Boltz would DISCARD this alignment "
                f"silently and fold the antigen single-sequence "
                f"(featurizerv2.py compares lengths only, then calls dummy_msa). "
                f"Pass an alignment built for this exact sequence, use "
                f"antigen_msa=None to query the server, or set allow_msa_mismatch=True "
                f"if you are deliberately reproducing the mismatch.")
    msa_field = str(_stage(antigen_msa)) if antigen_msa else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f">A|protein|empty\n{heavy}\n"
        f">B|protein|empty\n{light}\n"
        f">C|protein|{msa_field}\n{antigen}\n"
    )
    return path


def fold(label: str, heavy: str, light: str, antigen: str, *,
         out_root: Path, construct: str = "fv", seed: int = 1,
         antigen_msa: Path | None = PD1_MSA,
         diffusion_samples: int = 1, recycling_steps: int = 3,
         timeout: int = 3600, allow_msa_mismatch: bool = False) -> FoldResult:
    # ipsae.py finds the pLDDT array by doing pae_path.replace("pae", "plddt").
    # A label containing "pae" corrupts that substitution and ipsae then writes an
    # empty table and exits 0. Cheap assertion against an expensive silent failure.
    if "pae" in label or "plddt" in label:
        raise FoldFailed(
            f"label {label!r} contains 'pae'/'plddt'; ipsae.py locates the pLDDT "
            f"file by string-substituting the PAE path and would silently produce "
            f"an empty table")

    out_dir = Path(out_root) / label
    fasta = write_input(out_dir / f"{label}.fasta", heavy, light, antigen,
                        antigen_msa=antigen_msa,
                        allow_msa_mismatch=allow_msa_mismatch)

    cmd = [BOLTZ, "predict", str(fasta),
           "--out_dir", str(out_dir),
           "--output_format", "pdb", "--write_full_pae",
           "--diffusion_samples", str(diffusion_samples),
           "--recycling_steps", str(recycling_steps),
           "--seed", str(seed),
           "--accelerator", "gpu", "--num_workers", "0",
           "--no_kernels", "--max_msa_seqs", "1024"]
    if antigen_msa is None:
        cmd.append("--use_msa_server")       # only when no cache is available

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0

    pred = out_dir / f"boltz_results_{label}" / "predictions" / label
    pdb = pred / f"{label}_model_0.pdb"
    pae = pred / f"pae_{label}_model_0.npz"
    plddt = pred / f"plddt_{label}_model_0.npz"

    # Exit code is deliberately not consulted -- see fold/__init__.py.
    assert_artefacts(pdb, pae, plddt, label=label,
                     stdout=proc.stdout + proc.stderr)

    return FoldResult(
        label=label, predictor="boltz2", construct=construct, seed=seed,
        pdb=pdb, pae=pae, plddt=plddt, seconds=elapsed,
        n_residues=len(heavy) + len(light) + len(antigen),
        chain_lengths=(len(heavy), len(light), len(antigen)),
    )
