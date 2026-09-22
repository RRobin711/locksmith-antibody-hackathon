"""Batched Boltz-2 folding: many complexes, one `boltz predict` invocation.

THE ARITHMETIC THAT JUSTIFIES IT. A single Fab fold on this machine costs ~84 s
quiet. The *fold itself* is roughly 34 s; the rest is fixed per-invocation cost --
loading the checkpoint, building the featuriser, parsing the antigen MSA. Boltz
accepts a DIRECTORY of FASTA files and pays that cost once for the whole directory,
so batching N complexes converts N x (fixed + fold) into fixed + N x fold. At the
measured split that is ~1.8x for large N.

This was deferred twice, correctly, with an explicit condition for un-deferring it:
"once the funnel pattern is known and stable". The pattern is now N independent
549-residue Fab folds with no interdependence, so the condition is met.

WHAT BATCHING CANNOT DO, AND WHY THE API MAKES IT EXPLICIT
----------------------------------------------------------
`--seed` is an invocation-level flag, not a per-record one. Every complex in a batch
therefore shares a seed, and `fold_batch` takes a single `seed` argument rather than
per-item seeds so that this is impossible to get wrong silently. Multi-seed work
batches by seed: one invocation per seed, N designs inside it.

WHY BYTE-IDENTITY IS THE WRONG ACCEPTANCE TEST ABOVE BATCH SIZE 1
-----------------------------------------------------------------
It is exactly right AT batch size 1: same seed, same input, same code path, so any
difference means the refactor changed something. Above that it is the wrong bar.
cuDNN and cuBLAS select kernels by tensor shape, and a batched forward pass presents
different shapes, so results can differ in the low-order bits even with an identical
seed. Demanding byte-identity there would report a correct implementation as broken.
The acceptance test is therefore two-tier, and `scripts/34_verify_batching.py`
implements it: byte-identity at batch 1, statistical equivalence (DockQ within 3 seed
sd, +/-0.054) above it.

EVERY ARTEFACT IS STILL ASSERTED INDIVIDUALLY. A batch that half-fails is the most
dangerous shape of all: `boltz predict` exits 0 after fatal errors, and in a batch it
can complete most records and drop one, leaving a directory that looks right. Each
label is checked for its own PDB, PAE and pLDDT, and missing ones are reported per
label rather than failing the whole batch -- so one bad complex costs one fold, not N.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from locksmith.fold import FoldFailed, FoldResult, assert_artefacts
from locksmith.fold.boltz import BOLTZ, PD1_MSA, write_input


@dataclass(frozen=True)
class BatchItem:
    label: str
    heavy: str
    light: str
    antigen: str


@dataclass
class BatchOutcome:
    results: dict[str, FoldResult]
    failures: dict[str, str]
    seconds: float
    invocations: int = 1

    @property
    def per_fold_seconds(self) -> float:
        n = len(self.results)
        return self.seconds / n if n else float("nan")


def _chain_lengths(pdb: Path) -> tuple[int, int, int]:
    import gemmi
    st = gemmi.read_structure(str(pdb))
    lens = [len(c) for c in st[0]]
    while len(lens) < 3:
        lens.append(0)
    return tuple(lens[:3])                                    # type: ignore[return-value]


def fold_batch(items: list[BatchItem], *, out_root: Path, seed: int = 1,
               construct: str = "fab", antigen_msa: Path | None = PD1_MSA,
               diffusion_samples: int = 1, recycling_steps: int = 3,
               timeout: int = 14400) -> BatchOutcome:
    """Fold every item in ONE boltz invocation. Artefacts are asserted per label."""
    if not items:
        return BatchOutcome(results={}, failures={}, seconds=0.0)

    for it in items:
        # Same guard as the single-fold path: ipsae.py locates the pLDDT array by
        # string-substituting the PAE path, so a label containing 'pae'/'plddt'
        # makes it write an empty table and exit 0.
        if "pae" in it.label or "plddt" in it.label:
            raise FoldFailed(f"label {it.label!r} contains 'pae'/'plddt'")
    labels = [it.label for it in items]
    if len(set(labels)) != len(labels):
        raise FoldFailed("duplicate labels in one batch would collide in the output dir")

    out_root = Path(out_root)
    batch_dir = out_root / f"_batch_s{seed}_{len(items)}"
    fasta_dir = batch_dir / "inputs"
    fasta_dir.mkdir(parents=True, exist_ok=True)
    for it in items:
        write_input(fasta_dir / f"{it.label}.fasta", it.heavy, it.light, it.antigen,
                    antigen_msa=antigen_msa)

    cmd = [BOLTZ, "predict", str(fasta_dir),
           "--out_dir", str(batch_dir),
           "--output_format", "pdb", "--write_full_pae",
           "--diffusion_samples", str(diffusion_samples),
           "--recycling_steps", str(recycling_steps),
           "--seed", str(seed),
           "--accelerator", "gpu", "--num_workers", "0",
           "--no_kernels", "--max_msa_seqs", "1024"]
    if antigen_msa is None:
        cmd.append("--use_msa_server")

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0

    results, failures = {}, {}
    pred_root = batch_dir / f"boltz_results_{fasta_dir.name}" / "predictions"
    for it in items:
        pred = pred_root / it.label
        pdb = pred / f"{it.label}_model_0.pdb"
        pae = pred / f"pae_{it.label}_model_0.npz"
        plddt = pred / f"plddt_{it.label}_model_0.npz"
        try:
            # Exit code deliberately not consulted; the artefact is the evidence.
            assert_artefacts(pdb, pae, plddt, label=it.label,
                             stdout=proc.stdout + proc.stderr)
        except FoldFailed as e:
            failures[it.label] = str(e)[:400]
            continue
        cl = _chain_lengths(pdb)
        results[it.label] = FoldResult(
            label=it.label, predictor="boltz2", construct=construct, seed=seed,
            pdb=pdb, pae=pae, plddt=plddt, seconds=elapsed / len(items),
            n_residues=sum(cl), chain_lengths=cl)
    return BatchOutcome(results=results, failures=failures, seconds=elapsed)
