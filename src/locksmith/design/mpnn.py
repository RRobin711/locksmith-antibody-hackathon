"""ProteinMPNN sequence design over the heavy-chain CDRs.

Baseline 1: plain ProteinMPNN at defaults, no filtering. This is the CONTROL the
funnel has to beat. Without it "our pipeline scored 84" is a number with no
referent; with it the claim becomes "the funnel beats naive MPNN on hit-rate and
composite score", which is defensible.

WHAT IS DESIGNED, AND WHAT IS HELD FIXED
----------------------------------------
Designed: the 29 IMGT CDR positions of the heavy chain (H1 8, H2 8, H3 13),
located by ANARCII rather than by a fixed residue range -- the V/C junction and
loop lengths differ between antibodies, which is the entire reason the handbook
specifies IMGT.

Fixed: everything else in the heavy chain, the whole light chain, and the whole
antigen. The antigen is context, not substrate: ProteinMPNN will happily redesign
any chain it is given, and redesigning PD-1 would produce a molecule that binds a
protein nobody has.

A NOTE ON TEMPERATURE, WHICH IS THE NOVELTY DIAL
------------------------------------------------
ProteinMPNN's sampling temperature controls how far sequences stray from the
native. At the default 0.1 it recovers native-like residues at high rate, so a
"default" baseline may produce designs whose CDR-H3 identity is too high to clear
the novelty gate (cutoff: >95% identity fails). That is a legitimate and
informative baseline result -- naive MPNN is not a novelty generator -- and it is
reported rather than tuned away. `seq_recovery` is captured per design so the
effect is measurable instead of inferred.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from locksmith.io.pdb import seq_for_folding
from locksmith.numbering import IMGT_CDR, number

MPNN_DIR = Path.home() / ".local/share/locksmith/ProteinMPNN"
MPNN_RUN = MPNN_DIR / "protein_mpnn_run.py"


@dataclass(frozen=True)
class MpnnDesign:
    design_id: str
    heavy: str
    light: str
    antigen: str
    score: float             # MPNN negative log-likelihood (lower is better)
    global_score: float
    seq_recovery: float      # fraction of designed positions matching native
    temperature: float
    seed: int
    sample: int


def cdr_positions(heavy_seq: str) -> dict[str, list[int]]:
    """0-based indices into `heavy_seq` of the IMGT heavy CDRs."""
    n = number(heavy_seq)
    if n is None:
        raise ValueError("heavy chain is not a recognisable V domain")
    out: dict[str, list[int]] = {}
    i = 0
    for (pos, _), aa in n.numbering:
        if aa == "-":
            continue
        for name, (lo, hi) in IMGT_CDR.items():
            if lo <= pos <= hi:
                out.setdefault(name, []).append(i + n.query_start)
        i += 1
    return out


def _parse_fasta(path: Path) -> list[tuple[str, dict[str, float]]]:
    """ProteinMPNN writes the native first, then one record per sample."""
    out: list[tuple[str, dict[str, float]]] = []
    header, seq = None, []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if header is not None:
                out.append(("".join(seq), header))
            header = {k: float(v) for k, v in
                      re.findall(r"(\w+)=([-\d.]+)", line)}
            seq = []
        else:
            seq.append(line.strip())
    if header is not None:
        out.append(("".join(seq), header))
    return out


def generate(pdb: Path, *, n: int, temperature: float = 0.1, seed: int = 37,
             design_chain: str = "A", context_chains: tuple[str, ...] = ("B", "C"),
             out_root: Path, timeout: int = 3600) -> list[MpnnDesign]:
    heavy = seq_for_folding(pdb, design_chain)
    light = seq_for_folding(pdb, context_chains[0])
    antigen = seq_for_folding(pdb, context_chains[1])

    cdr = cdr_positions(heavy)
    designable = sorted(i for v in cdr.values() for i in v)
    # ProteinMPNN's fixed-position lists are 1-BASED over the chain's residues.
    fixed = [i + 1 for i in range(len(heavy)) if i not in set(designable)]

    out_root.mkdir(parents=True, exist_ok=True)
    name = Path(pdb).stem
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chains.jsonl").write_text(json.dumps(
            {name: [[design_chain], list(context_chains)]}) + "\n")
        (td / "fixed.jsonl").write_text(json.dumps(
            {name: {design_chain: fixed}}) + "\n")
        cmd = [sys.executable, str(MPNN_RUN),
               "--pdb_path", str(Path(pdb).resolve()),
               "--pdb_path_chains", design_chain,
               "--chain_id_jsonl", str(td / "chains.jsonl"),
               "--fixed_positions_jsonl", str(td / "fixed.jsonl"),
               "--out_folder", str(out_root.resolve()),
               "--num_seq_per_target", str(n),
               "--sampling_temp", str(temperature),
               "--seed", str(seed),
               "--batch_size", "1"]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=MPNN_DIR, timeout=timeout)

    fa = out_root / "seqs" / f"{name}.fa"
    if not fa.exists():                      # assert on the artefact, not the exit code
        raise RuntimeError(
            f"ProteinMPNN wrote no sequences (rc={proc.returncode}):\n"
            f"{(proc.stdout + proc.stderr)[-1500:]}")

    records = _parse_fasta(fa)
    designs: list[MpnnDesign] = []
    for k, (seq, meta) in enumerate(records[1:], start=1):   # [0] is the native
        h = seq.split("/")[0]
        if len(h) != len(heavy):
            raise RuntimeError(
                f"MPNN returned a heavy chain of {len(h)} aa, expected {len(heavy)}")
        designs.append(MpnnDesign(
            design_id=f"mpnn_T{temperature}_s{seed}_{k:03d}",
            heavy=h, light=light, antigen=antigen,
            score=meta.get("score", float("nan")),
            global_score=meta.get("global_score", float("nan")),
            seq_recovery=meta.get("seq_recovery", float("nan")),
            temperature=temperature, seed=seed, sample=k))
    return designs
