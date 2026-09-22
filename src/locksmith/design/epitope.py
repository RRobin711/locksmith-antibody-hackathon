"""The PD-L1 competitive footprint on PD-1, and epitope overlap.

Serves two purposes, which is why it moves early:

1. **Design conditioning (Challenge 2).**  RFdiffusion takes `ppi.hotspot_res`
   and RFantibody takes target hotspots, so we can design TOWARD the right face
   of PD-1 rather than discovering at the end that a confident binder hit the
   wrong side.
2. **Validation (both challenges).**  Fraction of the PD-L1 footprint our
   antibody buries.  This is the only check in the whole project that asks
   whether the molecule would work as a *checkpoint inhibitor* -- the rubric
   never asks, because ipSAE and dG do not know what a checkpoint is.

Residue numbers cannot be assumed transferable between PDB entries: 5IUS and
5GGS do not carry identical PD-1 sequences, so the footprint is mapped across by
explicit alignment.
"""
from __future__ import annotations

from dataclasses import dataclass

import gemmi

from locksmith.io.pdb import chains, read


@dataclass(frozen=True)
class Footprint:
    source: str
    chain: str
    residues: dict[int, str]      # seqid -> one-letter residue

    def __len__(self) -> int:
        return len(self.residues)

    def numbers(self) -> list[int]:
        return sorted(self.residues)


def contacts_between(
    pdb: str, group_a: tuple[str, ...], group_b: tuple[str, ...], *, cutoff: float = 5.0
) -> dict[str, dict[int, str]]:
    """Residues of each group within `cutoff` A (heavy atom) of the other group."""
    st = read(pdb)
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, cutoff).populate()
    out: dict[str, dict[int, str]] = {c.name: {} for c in model}
    for chain in model:
        if chain.name not in group_a + group_b:
            continue
        side = group_a if chain.name in group_a else group_b
        other = group_b if side is group_a else group_a
        for res in chain:
            for atom in res:
                hit = False
                for mark in ns.find_atoms(atom.pos, "\0", radius=cutoff):
                    cra = mark.to_cra(model)
                    if cra.chain.name in other and cra.atom.pos.dist(atom.pos) <= cutoff:
                        hit = True
                        break
                if hit:
                    out[chain.name][res.seqid.num] = gemmi.find_tabulated_residue(
                        res.name).one_letter_code.upper()
                    break
    return out


def map_numbering(src_pdb: str, src_chain: str, dst_pdb: str, dst_chain: str
                  ) -> tuple[dict[int, int], float]:
    """Map residue numbers from one structure's chain onto another's by alignment.

    Returns (src_seqid -> dst_seqid, percent identity over aligned columns).
    """
    from Bio import Align

    def residues(pdb: str, cid: str):
        st = read(pdb)
        rs = [r for r in st[0][cid]]
        seq = "".join(
            gemmi.find_tabulated_residue(r.name).one_letter_code.upper() for r in rs
        )
        return rs, seq

    src_res, src_seq = residues(src_pdb, src_chain)
    dst_res, dst_seq = residues(dst_pdb, dst_chain)

    aligner = Align.PairwiseAligner(
        mode="global", match_score=2, mismatch_score=-1,
        open_gap_score=-10, extend_gap_score=-0.5,
    )
    aln = aligner.align(src_seq, dst_seq)[0]
    mapping: dict[int, int] = {}
    matches = aligned = 0
    for (s0, s1), (d0, d1) in zip(aln.aligned[0], aln.aligned[1]):
        for k in range(s1 - s0):
            si, di = s0 + k, d0 + k
            mapping[src_res[si].seqid.num] = dst_res[di].seqid.num
            aligned += 1
            matches += src_seq[si] == dst_seq[di]
    return mapping, (100.0 * matches / aligned if aligned else 0.0)


def pdl1_footprint_on_pd1(
    ius: str = "data/refs/5ius.pdb", *, pd1: str = "A", pdl1: tuple[str, ...] = ("C", "D")
) -> Footprint:
    c = contacts_between(ius, (pd1,), pdl1)
    return Footprint(source="5IUS", chain=pd1, residues=c[pd1])


def antibody_epitope_on_pd1(complex_pdb: str) -> Footprint:
    """Antigen (chain C) residues contacted by the antibody (chains A, B)."""
    c = contacts_between(complex_pdb, ("C",), ("A", "B"))
    return Footprint(source=complex_pdb, chain="C", residues=c["C"])


def overlap(ab_epitope: Footprint, pdl1_site_in_ab_numbering: set[int]) -> dict[str, float]:
    ab = set(ab_epitope.numbers())
    site = pdl1_site_in_ab_numbering
    shared = ab & site
    return {
        "shared_residues": len(shared),
        "fraction_of_pdl1_site_covered": round(len(shared) / len(site), 3) if site else 0.0,
        "fraction_of_epitope_on_pdl1_site": round(len(shared) / len(ab), 3) if ab else 0.0,
    }
