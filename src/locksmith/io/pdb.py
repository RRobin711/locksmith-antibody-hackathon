"""Structure IO: sequence extraction, chain selection and relabelling.

The submission convention is Chain A = heavy, B = light, C = antigen.  That
collides with 5GGS, whose native chain C is a *second heavy chain* -- so
relabelling must be explicit and verified, never assumed.  Getting this wrong
does not raise an error; it silently pairs the wrong chains and yields
plausible-looking interface metrics computed across the wrong interface.
"""
from __future__ import annotations

from dataclasses import dataclass
import warnings
from pathlib import Path

import gemmi

SUBMISSION_CHAINS = {"heavy": "A", "light": "B", "antigen": "C"}


@dataclass(frozen=True)
class ChainInfo:
    chain_id: str
    seq: str
    n_res: int
    internal_gaps: tuple[tuple[int, int, int], ...] = ()   # (before, after, n_missing)

    @property
    def spliced(self) -> bool:
        """True if residues are missing from the MIDDLE of this chain.

        `seq` is built from the residues present in the COORDINATES. An
        unresolved loop is therefore silently absent and the flanking residues
        are concatenated, so `seq` describes a CHIMERA -- a protein with a loop
        excised and the ends fused -- not the molecule in the file.

        Terminal truncation (a disordered N- or C-terminus) leaves no gap in the
        author numbering and is harmless: the sequence is still a contiguous
        piece of the real protein.
        """
        return bool(self.internal_gaps)

    @property
    def n_missing_internally(self) -> int:
        return sum(g[2] for g in self.internal_gaps)


class SplicedSequenceError(ValueError):
    """A coordinate-derived sequence has an internal deletion and must not be folded."""


def read(path: str | Path) -> gemmi.Structure:
    st = gemmi.read_structure(str(path))
    st.setup_entities()          # must precede remove_ligands_and_waters(), which
    st.remove_alternative_conformations()   # reads entity_type and throws without it
    st.remove_hydrogens()
    st.remove_ligands_and_waters()
    st.setup_entities()
    return st


def chains(path: str | Path, model: int = 0) -> dict[str, ChainInfo]:
    """One-letter sequences per chain, from coordinates (NOT SEQRES).

    WARNS on internal gaps. On 2026-09-17 four of five post-cutoff targets were
    folded from sequences with unresolved loops spliced out -- 9W43's antigen at
    83 aa against a true 115 -- which invalidated two of three conclusions of a
    completed study. The spliced sequence is a valid protein sequence: it folds
    without error and yields a confident structure, so nothing downstream raises.
    Use `seq_for_folding()` when the sequence will be handed to a predictor.
    """
    st = read(path)
    out: dict[str, ChainInfo] = {}
    for ch in st[model]:
        seq = gemmi.one_letter_code([r.name for r in ch])
        seq = "".join(c.upper() for c in seq if c.isalpha())
        if not seq:
            continue
        nums = [r.seqid.num for r in ch]
        gaps = tuple((a, b, b - a - 1) for a, b in zip(nums, nums[1:]) if b - a > 1)
        info = ChainInfo(ch.name, seq, len(seq), gaps)
        if info.spliced:
            warnings.warn(
                f"{Path(path).name} chain {ch.name}: coordinate-derived sequence has "
                f"{info.n_missing_internally} residue(s) missing INTERNALLY at "
                f"{[(a, b) for a, b, _ in gaps]}. This string is a chimera, not the real "
                f"protein. Safe for coordinate-based metrics; NEVER fold it -- use SEQRES.",
                SplicedSequenceWarning, stacklevel=2)
        out[ch.name] = info
    return out


class SplicedSequenceWarning(UserWarning):
    """A coordinate-derived sequence has an internal deletion."""


def seq_for_folding(path: str | Path, chain_id: str, model: int = 0) -> str:
    """The sequence of one chain, REFUSING to return a chimera.

    This is the call to use anywhere the result will be handed to a structure
    predictor. Terminal truncation passes; internal deletion raises.
    """
    info = chains(path, model)[chain_id]
    if info.spliced:
        raise SplicedSequenceError(
            f"{Path(path).name} chain {chain_id}: {info.n_missing_internally} residue(s) "
            f"missing internally at {[(a, b) for a, b, _ in info.internal_gaps]}. Folding "
            f"this would predict a protein with a loop excised and the ends fused. "
            f"Fetch the SEQRES entity sequence instead (see scripts/13_reprepare_postcutoff.py)."
        )
    return info.seq


def extract_complex(
    src: str | Path,
    dest: str | Path,
    *,
    heavy: str,
    light: str,
    antigen: str,
    model: int = 0,
) -> dict[str, str]:
    """Write a 3-chain complex relabelled to the submission convention.

    Returns the applied mapping {original_chain: new_chain} so it can be
    recorded alongside the artefact -- the mapping is not recoverable from the
    output file once applied.
    """
    st = read(src)
    want = {heavy: "A", light: "B", antigen: "C"}
    missing = [c for c in want if c not in {ch.name for ch in st[model]}]
    if missing:
        raise KeyError(f"{Path(src).name}: chains not found: {missing}")

    out = gemmi.Structure()
    out.spacegroup_hm = st.spacegroup_hm
    out.cell = st.cell
    out.add_model(gemmi.Model("1"))
    # Insert in A, B, C order so downstream tools that assume file order agree
    # with tools that key on the chain label.
    for original in (heavy, light, antigen):
        ch = st[model][original].clone()
        ch.name = want[original]
        out[0].add_chain(ch)
    out.setup_entities()
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    out.write_pdb(str(dest))
    return want
