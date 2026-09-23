#!/usr/bin/env python3
"""Does either design actually BLOCK PD-L1? The question we never asked.

WHY THIS MATTERS MORE THAN ANYTHING ELSE WE MEASURED. Every metric in the rubric asks
whether the antibody binds PD-1. **None asks whether it does the job.** An anti-PD-1
antibody is a checkpoint inhibitor: its therapeutic mechanism is occluding the PD-L1
binding site so the ligand cannot engage. An antibody that binds PD-1 confidently on the
wrong face is worth nothing clinically and scores identically on all eight metrics.

We have claimed a "PD-L1 competitive epitope" throughout this project, and we verified
that the designed loops contact the conditioned footprint. **We never verified that the
resulting antibody would actually compete with PD-L1.**

METHOD. Superpose our complex's PD-1 onto the PD-1 of PDB **5IUS** (the PD-1/PD-L1
complex), carry our Fv along with that transform, then measure how much of PD-L1 the Fv
now occupies:

  * **steric clashes** -- Fv heavy atoms within 3.0 A of a PD-L1 heavy atom. Two atoms
    closer than roughly the sum of their van der Waals radii cannot coexist, so a clash
    is a hard statement: these two molecules cannot both be bound.
  * **occluded PD-L1 interface** -- of the PD-L1 residues that contact PD-1 in 5IUS,
    how many are now within 4.5 A of our Fv. This is the softer, more informative
    measure: it says how much of the ligand's own footprint we have taken.
  * **epitope overlap** -- of the PD-1 residues PD-L1 binds, how many our antibody binds.

A design can block by direct overlap (taking the same PD-1 surface) or by steric
occlusion (sitting adjacent but in the way). Both count therapeutically; they are
reported separately because they are different mechanisms.

5IUS chains: A/B = PD-1, C/D = PD-L1. We use A and C.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import gemmi

REF = Path("data/refs/5ius.pdb")
OUT = Path("results/pdl1_competition.md")
CLASH = 3.0          # A, heavy-atom; below this two atoms cannot coexist
CONTACT = 4.5        # A, heavy-atom; the convention used everywhere else in this project

TARGETS = {
    1: "submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge1/structures/design_1_complex.pdb",
    2: "submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge2/structures/design_1_complex.pdb",
}


def chains_of(st) -> dict:
    return {ch.name: [r for r in ch if r.find_atom("CA", "*")] for ch in st[0]}


def seq(residues) -> str:
    return gemmi.one_letter_code([r.name for r in residues]).upper()


def superpose_on_pd1(design_pdb: Path, ref_st):
    """Return the design structure moved into 5IUS's frame, by its PD-1 chain.

    Matched by GAPPED global alignment of the two PD-1 sequences, CA atoms only.

    A longest-common-substring match was tried first and its own guard refused it: only
    **35** contiguous residues agree, because 5IUS's PD-1 has unresolved loops that split
    the sequence into blocks. Contiguity is the wrong requirement -- superposition needs
    corresponding residues, not consecutive ones. This is the same class of error as
    folding a coordinate-derived sequence across an internal gap, which this project
    already has a guard for.
    """
    from Bio import Align

    st = gemmi.read_structure(str(design_pdb))
    st.setup_entities()
    dc, rc = chains_of(st), chains_of(ref_st)
    ds, rs = seq(dc["C"]), seq(rc["A"])

    aligner = Align.PairwiseAligner(mode="global", match_score=1, mismatch_score=-1,
                                    open_gap_score=-5, extend_gap_score=-0.5)
    aln = aligner.align(ds, rs)[0]
    dpos, rpos, n, numap = [], [], 0, {}
    for (d0, d1), (r0, r1) in zip(aln.aligned[0], aln.aligned[1]):
        for t in range(d1 - d0):
            di, ri = d0 + t, r0 + t
            if ds[di] != rs[ri]:
                continue                      # identical residues only
            a = dc["C"][di].find_atom("CA", "*")
            b = rc["A"][ri].find_atom("CA", "*")
            if a and b:
                dpos.append(a.pos); rpos.append(b.pos); n += 1
                numap[dc['C'][di].seqid.num] = rc['A'][ri].seqid.num
    if n < 40:
        raise RuntimeError(f"{design_pdb.name}: only {n} PD-1 residues align to 5IUS; "
                           f"refusing to superpose on that")

    sup = gemmi.superpose_positions(rpos, dpos)      # moves design -> reference frame
    st[0].transform_pos_and_adp(sup.transform)
    return st, n, sup.rmsd, numap


def main() -> int:
    ref = gemmi.read_structure(str(REF))
    ref.setup_entities()
    rc = chains_of(ref)
    pd1_ref, pdl1 = rc["A"], rc["C"]
    pdl1_atoms = [(r, a) for r in pdl1 for a in r if a.element.name != "H"]

    # PD-L1 residues that contact PD-1 in the crystal -- the footprint we must occlude
    pdl1_iface = set()
    pd1_iface = set()
    for r, a in pdl1_atoms:
        for r2 in pd1_ref:
            for a2 in r2:
                if a2.element.name == "H":
                    continue
                if a.pos.dist(a2.pos) <= CONTACT:
                    pdl1_iface.add(r.seqid.num)
                    pd1_iface.add(r2.seqid.num)
    print(f"5IUS: PD-L1 contributes {len(pdl1_iface)} interface residues, "
          f"PD-1 contributes {len(pd1_iface)}\n", flush=True)

    L, w = [], None
    L = []; w = L.append
    w("# Does either design block PD-L1?")
    w("")
    w("**2026-09-22.** Every metric in the rubric asks whether the antibody binds PD-1. "
      "None asks whether it does the job. An anti-PD-1 antibody is a checkpoint inhibitor: "
      "its mechanism is occluding the PD-L1 site. **An antibody that binds PD-1 "
      "confidently on the wrong face scores identically on all eight metrics and is "
      "worthless.** We had never checked.")
    w("")
    w(f"Method: superpose each design's PD-1 onto PDB **5IUS** (PD-1/PD-L1), carry the Fv "
      f"with it, then measure the overlap with PD-L1. Clash = {CLASH} Å heavy-atom "
      f"(below the van der Waals sum, so the two cannot coexist); contact = {CONTACT} Å. "
      f"In 5IUS, PD-L1 contributes **{len(pdl1_iface)}** interface residues and PD-1 "
      f"**{len(pd1_iface)}**.")
    w("")
    w("| challenge | superposed on | CA RMSD | Fv↔PD-L1 clashes (<3 Å) | PD-L1 footprint occluded | PD-1 epitope shared with PD-L1 |")
    w("|---|---|---|---|---|---|")

    summary = {}
    for ch, path in TARGETS.items():
        p = Path(path)
        if not p.exists():
            print(f"challenge {ch}: {p} missing", file=sys.stderr)
            continue
        st, nmatch, rmsd, numap = superpose_on_pd1(p, ref)
        dc = chains_of(st)
        fv = [(r, a) for cn in ("A", "B") for r in dc[cn] for a in r
              if a.element.name != "H"]

        clashes = 0
        occluded = set()
        for r, a in pdl1_atoms:
            for _, b in fv:
                d = a.pos.dist(b.pos)
                if d <= CLASH:
                    clashes += 1
                if d <= CONTACT and r.seqid.num in pdl1_iface:
                    occluded.add(r.seqid.num)

        # which PD-1 residues does OUR antibody contact, and how many are PD-L1's?
        ab_epitope = set()
        for r in dc["C"]:
            for a in r:
                if a.element.name == "H":
                    continue
                for _, b in fv:
                    if a.pos.dist(b.pos) <= CONTACT:
                        ab_epitope.add(r.seqid.num)
                        break
        # PD-1 NUMBERING DIFFERS BETWEEN THE TWO CONSTRUCTS, so intersecting residue
        # numbers directly is meaningless -- it is the same error as matching RFdiffusion
        # hotspots on residue number, which this project has a standing rule about. Map
        # our numbering into 5IUS's through the alignment before comparing.
        shared = len({numap[r] for r in ab_epitope if r in numap} & pd1_iface)

        pct = 100.0 * len(occluded) / max(len(pdl1_iface), 1)
        w(f"| **Challenge {ch}** | {nmatch} PD-1 residues | {rmsd:.2f} Å | "
          f"**{clashes}** | **{len(occluded)}/{len(pdl1_iface)} ({pct:.0f}%)** | "
          f"{shared} residues |")
        summary[ch] = {"clashes": clashes, "occluded": len(occluded),
                       "pdl1_iface": len(pdl1_iface), "pct": round(pct, 1),
                       "rmsd": round(rmsd, 2), "matched": nmatch,
                       "ab_epitope": len(ab_epitope), "shared_with_pdl1": shared}
        print(f"challenge {ch}: {clashes} clashes, {len(occluded)}/{len(pdl1_iface)} "
              f"of the PD-L1 footprint occluded ({pct:.0f}%), superposition RMSD "
              f"{rmsd:.2f} Å over {nmatch} residues", flush=True)

    w("")
    for ch, s in summary.items():
        verdict = ("**blocks PD-L1**" if s["clashes"] > 0 and s["pct"] > 30 else
                   "**partially occludes**" if s["pct"] > 10 else
                   "**does NOT block**")
        w(f"- **Challenge {ch}: {verdict}.** {s['clashes']} atomic clashes with PD-L1 and "
          f"{s['occluded']} of {s['pdl1_iface']} PD-L1 interface residues occluded "
          f"({s['pct']}%). Its own PD-1 epitope is {s['ab_epitope']} residues, "
          f"{s['shared_with_pdl1']} of them shared with PD-L1's.")
    w("")
    w("## What this does and does not establish")
    w("")
    w("**Does:** whether the *predicted* pose is geometrically incompatible with PD-L1 "
      "binding. That is the therapeutic mechanism of a checkpoint inhibitor, and it is "
      "not measured anywhere in the rubric.")
    w("")
    w("**Does not:** that the design binds at all. This analysis takes the predicted pose "
      "as given; if the pose is wrong the competition result is wrong with it. It is a "
      "conditional statement — *if* it binds as predicted, *then* it blocks — and the "
      "antecedent is exactly what this project has spent a week failing to establish.")
    w("")
    w("**Also does not** account for PD-1's own glycosylation (N49/N58/N74/N116 in vivo, "
      "modelled bare here) or for conformational change on binding. Both are rigid-body "
      "approximations and both could change the answer at the margin.")
    OUT.write_text("\n".join(L) + "\n")
    (OUT.with_suffix(".json")).write_text(json.dumps(summary, indent=1))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
