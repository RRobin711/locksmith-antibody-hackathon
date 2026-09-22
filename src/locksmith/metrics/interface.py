"""Interface residue detection and CDR residue mapping.

Both are shared by several metrics and both are places where an off-by-one
silently changes the answer, so they live in one place and are tested once.
"""
from __future__ import annotations

import gemmi

from locksmith.io.pdb import read
from locksmith.numbering import IMGT_CDR, number

ANTIBODY_CHAINS = ("A", "B")
ANTIGEN_CHAIN = "C"


def interface_residues(
    pdb: str, *, cutoff: float = 5.0
) -> dict[str, set[int]]:
    """Residues with any heavy atom within `cutoff` A of the other side.

    Returns {chain_id: {residue seqid, ...}} for all three chains.
    """
    st = read(pdb)
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, cutoff).populate()
    out: dict[str, set[int]] = {c.name: set() for c in model}

    for chain in model:
        side = "ag" if chain.name == ANTIGEN_CHAIN else "ab"
        for res in chain:
            for atom in res:
                if atom.element == gemmi.Element("H"):
                    continue
                for mark in ns.find_atoms(atom.pos, "\0", radius=cutoff):
                    cra = mark.to_cra(model)
                    other = "ag" if cra.chain.name == ANTIGEN_CHAIN else "ab"
                    if other == side:
                        continue
                    if cra.atom.pos.dist(atom.pos) <= cutoff:
                        out[chain.name].add(res.seqid.num)
                        out[cra.chain.name].add(cra.residue.seqid.num)
    return out


def cdr_residues(pdb: str, chain_id: str) -> dict[str, list[int]]:
    """IMGT CDR residues of one chain, as PDB seqid numbers.

    ANARCII numbers the *observed* sequence, so sequence index i corresponds to
    the i-th residue actually present in the coordinates -- which is why the
    sequence must be read from the same residue list used for the mapping, not
    from SEQRES.  A structure with unmodelled residues would otherwise shift
    every CDR assignment downstream of the gap.
    """
    st = read(pdb)
    residues = [r for r in st[0][chain_id]]
    seq = gemmi.one_letter_code([r.name for r in residues])
    seq = "".join(c.upper() for c in seq if c.isalpha())

    n = number(seq)
    if n is None:
        raise ValueError(f"chain {chain_id} is not an antibody V domain")

    # Non-gap numbering entries map 1:1 onto seq[query_start : query_end+1].
    non_gap = [(pos, aa) for pos, aa in n.numbering if aa != "-"]
    out: dict[str, list[int]] = {k: [] for k in IMGT_CDR}
    for offset, ((imgt_pos, _icode), aa) in enumerate(non_gap):
        seq_idx = n.query_start + offset
        if seq_idx >= len(residues):
            break
        if residues[seq_idx].name and aa != seq[seq_idx]:
            raise AssertionError(
                f"numbering/coordinate mismatch at {chain_id}:{seq_idx} "
                f"({aa} vs {seq[seq_idx]}) -- CDR mapping would be wrong"
            )
        for cdr, (lo, hi) in IMGT_CDR.items():
            if lo <= imgt_pos <= hi:
                out[cdr].append(residues[seq_idx].seqid.num)
    return out
