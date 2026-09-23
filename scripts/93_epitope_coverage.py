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

from locksmith.io.pdb import contacting_residues

CONTACT = 4.5
CORE = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRDF"
        "HMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")                       # 113 aa, folded
EXTENDED = "LDSPDR" + CORE                                             # 119 aa, follow-up
SUBMITTED = "DSPDRP" + CORE[1:] + "VTERR"       # what the submission FASTA ships

REFS = {"pembrolizumab": ("data/refs/5ggs.pdb", "5GGS"),
        "nivolumab": ("data/refs/5wt9.pdb", "5WT9"),
        # Not an antibody: PD-1's PD-L1-binding face, from the PD-1/PD-L1 complex. This is
        # the surface a checkpoint inhibitor must occlude and the face our own designs
        # were conditioned on, so whether the construct contains it BOUNDS the damage the
        # truncation does to our own numbers rather than to nivolumab's.
        "PD-L1 (therapeutic target face)": ("data/refs/5ius.pdb", "5IUS")}
OUT = Path("results/epitope_coverage.json")


# Several short probes spread along PD-1, not one long window. A coordinate-derived
# sequence omits unresolved residues, so ANY crystal with a disordered loop inside a
# 30-residue probe fails to match it -- which is exactly what happened: 5IUS's PD-1 has a
# gap inside CORE[20:50], and a single-probe detector silently returned "no PD-1 chain
# here" and skipped the entry. Requiring only one of several probes makes detection
# robust to a gap anywhere, and the probes are short enough to survive one.
PROBES = [CORE[i:i + 12] for i in (0, 20, 40, 60, 80, 96)]


MIN_IFACE = 5          # contacting residues required to call a chain a real partner
                       # rather than a lattice neighbour


def pd1_copies(st) -> list[str]:
    """Every PD-1 chain in the file, not just the first one found.

    5GGS holds two independent copies in the asymmetric unit and their epitopes differ:
    chain Y (with Fab C/D) contacts 24 residues, chain Z (with Fab A/B) contacts 26. Both
    are real; the difference is which side chains each copy resolved. Returning "the first
    chain that matched" would make the reported number depend on chain iteration order,
    which is not a reproducible measurement. Every copy is scored and the one with the
    LARGEST epitope is used for coverage, because that is the conservative choice for a
    test asking "how much of the epitope is missing from our construct".
    """
    out = []
    for ch in st[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        sq = gemmi.one_letter_code([r.name for r in res]).upper()
        if sum(1 for p in PROBES if p in sq) >= 2:
            out.append(ch.name)
    return out


def main() -> int:
    out = {}
    for name, (path, pdbid) in REFS.items():
        st = gemmi.read_structure(path)
        st.setup_entities()
        chains = {c.name: [r for r in c if r.find_atom("CA", "*")] for c in st[0]}
        copies = pd1_copies(st)
        if not copies:
            print(f"{name}: no PD-1 chain found in {pdbid}", flush=True)
            continue

        scored = []
        for cp in copies:
            partners = []
            for n, res in chains.items():
                if n == cp or len(res) < 80:
                    continue
                sn = gemmi.one_letter_code([r.name for r in res]).upper()
                if sum(1 for pr in PROBES if pr in sn) >= 2:
                    continue                   # another PD-1 copy, not a partner
                partners.append(n)
            ab = [n for n in partners if contacting_residues(chains[cp], chains[n]) >= MIN_IFACE]
            epitope = []
            for i, r in enumerate(chains[cp]):
                if any(contacting_residues([r], chains[n]) > 0 for n in ab):
                    epitope.append((i, r.seqid.num, r.name))
            scored.append({"copy": cp, "partners": ab, "epitope": epitope})

        scored.sort(key=lambda d: -len(d["epitope"]))
        best = scored[0]
        epitope = best["epitope"]
        seq = gemmi.one_letter_code([r.name for r in chains[best["copy"]]]).upper()

        row = {"pdb": pdbid, "pd1_chain": best["copy"], "partners": best["partners"],
               "n_epitope": len(epitope),
               "epitope": [f"{n}{num}" for _, num, n in epitope],
               "all_copies": {d["copy"]: len(d["epitope"]) for d in scored}}
        for cname, cseq in (("folded_113", CORE), ("followup_119", EXTENDED),
                            ("submitted", SUBMITTED)):
            probe = cseq[:10]
            start_i = seq.find(probe)
            if start_i < 0:
                inner = seq.find(CORE[:10])
                start_i = inner - (cseq.find(CORE[:10]) if CORE[:10] in cseq else 0)
            end_i = start_i + len(cseq)
            covered = [f"{n}{num}" for i, num, n in epitope if start_i <= i < end_i]
            missing = [f"{n}{num}" for i, num, n in epitope if not (start_i <= i < end_i)]
            row[cname] = {"covered": len(covered), "missing": len(missing),
                          "missing_residues": missing,
                          "pct": round(100.0 * len(covered) / max(len(epitope), 1), 1)}
        out[name] = row
        extra = (f"  (copies: {row['all_copies']}, using {best['copy']} with "
                 f"{best['partners']})" if len(scored) > 1 else
                 f"  (chain {best['copy']} with {best['partners']})")
        print(f"{name:<32} {pdbid}  epitope {len(epitope)} residues{extra}", flush=True)
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
