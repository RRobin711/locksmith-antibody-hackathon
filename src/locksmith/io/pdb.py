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


def contacting_residues(a_res, b_res, cutoff: float = 4.5) -> int:
    """How many residues of `a_res` have a heavy atom within `cutoff` Å of `b_res`.

    Hydrogens are excluded because crystal structures mostly do not resolve them, so
    including them would make the count depend on whether a given entry was refined with
    riding hydrogens rather than on the geometry.
    """
    n = 0
    for r in a_res:
        touched = False
        for r2 in b_res:
            for x in r:
                if x.element.name == "H":
                    continue
                for y in r2:
                    if y.element.name != "H" and x.pos.dist(y.pos) <= cutoff:
                        touched = True
                        break
                if touched:
                    break
            if touched:
                break
        n += int(touched)
    return n


def pick_contacting_chain(candidates: dict, target_res, *, min_contacts: int = 1):
    """Of `candidates` (name -> residues), the one actually touching `target_res`.

    WHY THIS EXISTS. Selecting "the first heavy chain, the first light chain and the first
    non-antibody chain" in a PDB entry is the obvious thing to do and is wrong whenever the
    asymmetric unit holds more than one copy of the complex: nothing in that rule requires
    the three chains to belong to the SAME copy. The result is a complex whose chains never
    touch, which is not a complex.

    Measured 2026-09-22 on a 40-entry panel: **8 of 40 (20%)** paired an antibody Fv with
    the antigen of a different copy. The resulting DockQ "native" contained only the
    heavy-light framework interface, so DockQ scored `Total DockQ over 1 native interfaces`
    and the antibody-antigen number -- the entire point of the measurement -- was absent.

    The failure is silent in the worst way: every chain is present, every sequence is
    correct, the file parses, and the number that comes out is merely about the wrong pair
    of molecules. It was caught only by a contradiction -- ipSAE 0.819 (chains demonstrably
    in contact) alongside a missing DockQ (no interface found) cannot both be true.

    Returns (name, n_contacts), or (None, 0) if nothing clears `min_contacts`.

    Pinned by `tests/test_invariants.py::test_pick_contacting_chain_rejects_the_wrong_copy`.
    """
    best, best_n = None, 0
    for name, res in candidates.items():
        n = contacting_residues(res, target_res)
        if n > best_n:
            best, best_n = name, n
    return (best, best_n) if best_n >= min_contacts else (None, 0)
