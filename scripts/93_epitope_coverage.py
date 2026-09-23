#!/usr/bin/env python3
"""Does the PD-1 construct we fold actually contain each control antibody's epitope?

WHY THIS EXISTS. The negative control's positive arm split: pembrolizumab scored ipSAE
0.874, nivolumab 0.017. Both are licensed anti-PD-1 antibodies, so "the pipeline is
broken" and "nivolumab is a bad control" are both available stories and neither is
evidence. The question is answerable from crystallography alone, with no folding: take
each antibody's OWN structure, list the PD-1 residues it contacts, and ask how many of
them exist in the construct we fold.

METHOD. Heavy-atom contacts at 4.5 A (the convention used everywhere else in this
project). The antibody's own crystal defines its epitope; the folded construct is located
inside that crystal's PD-1 chain by exact substring match, so residue identity is never
inferred from numbering -- PD-1 is numbered differently between entries and matching on
residue number is the same error this project has a standing rule about for RFdiffusion
hotspots.

Writes `results/epitope_coverage.json` so the number appears in the write-up computed
rather than transcribed.
"""
from __future__ import annotations

import json
from pathlib import Path

import gemmi

CONTACT = 4.5
CORE = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRDF"
        "HMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")                       # 113 aa, folded
EXTENDED = "LDSPDR" + CORE                                             # 119 aa, follow-up
SUBMITTED = "DSPDRP" + CORE[1:] + "VTERR"       # what the submission FASTA ships

REFS = {"pembrolizumab": ("data/refs/5ggs.pdb", "5GGS"),
        "nivolumab": ("data/refs/5wt9.pdb", "5WT9")}
OUT = Path("results/epitope_coverage.json")


def pd1_chain(st) -> str | None:
    for ch in st[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        s = gemmi.one_letter_code([r.name for r in res]).upper()
        if CORE[20:50] in s:
            return ch.name
    return None


def main() -> int:
    out = {}
    for name, (path, pdbid) in REFS.items():
        st = gemmi.read_structure(path)
        st.setup_entities()
        chains = {c.name: [r for r in c if r.find_atom("CA", "*")] for c in st[0]}
        pd1 = pd1_chain(st)
        if pd1 is None:
            continue
        ab = [n for n in chains if n != pd1 and len(chains[n]) > 80]
        seq = gemmi.one_letter_code([r.name for r in chains[pd1]]).upper()

        epitope = []
        for i, r in enumerate(chains[pd1]):
            hit = False
            for n in ab:
                for r2 in chains[n]:
                    for a in r:
                        if a.element.name == "H":
                            continue
                        for b in r2:
                            if b.element.name != "H" and a.pos.dist(b.pos) <= CONTACT:
                                hit = True
                                break
                        if hit:
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                epitope.append((i, r.seqid.num, r.name))

        row = {"pdb": pdbid, "pd1_chain": pd1, "n_epitope": len(epitope),
               "epitope": [f"{n}{num}" for _, num, n in epitope]}
        for cname, cseq in (("folded_113", CORE), ("followup_119", EXTENDED),
                            ("submitted", SUBMITTED)):
            # locate the construct inside this crystal's PD-1 by sequence, not numbering
            probe = cseq[:10]
            start = seq.find(probe)
            if start < 0:                    # construct extends N-terminally past the crystal
                inner = seq.find(CORE[:10])
                start = inner - (cseq.find(CORE[:10]) if CORE[:10] in cseq else 0)
            end = start + len(cseq)
            covered = [f"{n}{num}" for i, num, n in epitope if start <= i < end]
            missing = [f"{n}{num}" for i, num, n in epitope if not (start <= i < end)]
            row[cname] = {"covered": len(covered), "missing": len(missing),
                          "missing_residues": missing,
                          "pct": round(100.0 * len(covered) / max(len(epitope), 1), 1)}
        out[name] = row
        print(f"{name:<15} {pdbid}  epitope {len(epitope)} residues", flush=True)
        for cname in ("folded_113", "followup_119", "submitted"):
            d = row[cname]
            print(f"    {cname:<14} covers {d['covered']}/{len(epitope)} "
                  f"({d['pct']}%)" +
                  (f"  MISSING: {' '.join(d['missing_residues'])}"
                   if d["missing_residues"] else ""), flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
