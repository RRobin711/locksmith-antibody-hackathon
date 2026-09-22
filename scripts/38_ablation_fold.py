#!/usr/bin/env python3
"""Hotspot ablation: is the winner's score actually reporting its interface?

THE QUESTION. PRODIGY's dG, the contact count and ipSAE are all computed from a
predicted structure. If the score survives destroying the residues that make the
interface, then the score is not measuring the interface -- it is measuring
"two chains are near each other", which any sticky surface produces. This is the
cheapest available test of whether the number means what its name says.

THE MUTANTS, chosen from MEASURED contacts, not intuition. Heavy-atom pairs within
5.0 A of the antigen (chain C) in the winner's seed-1 structure, counted per heavy
chain residue (0-based index into the 219-aa heavy chain):

    idx  31  TYR  54 contacts  CDR-H1     <- joint largest
    idx 100  ASP  54 contacts  CDR-H3     <- joint largest
    idx  99  ARG  50 contacts  CDR-H3
    idx  57  ASN  39 contacts  CDR-H2
    idx 102  ASP  31 contacts  CDR-H3
    idx  97  ARG  30 contacts  CDR-H3

Six singles, each -> Ala. Plus ONE triple (Y31A/R99A/D100A) removing the three
largest contributors at once, because a single alanine often costs little and the
interesting question is whether the score can be made to fall at all.

THE CONTROLS ARE THE POINT, and they are what the brief did not ask for. Without
them an ablation is uninterpretable: if every mutant degrades, you cannot tell
whether the score tracks the interface or merely punishes any mutation. So two
NEGATIVE controls, both Ala substitutions at CDR-H3 positions with ZERO measured
antigen contact:

    idx  96  LEU   0 contacts  CDR-H3, solvent-facing
    idx 106  TYR   0 contacts  CDR-H3, solvent-facing aromatic

An informative result is hotspots falling while controls hold. Controls falling as
far as hotspots means the readout is mutation-sensitive rather than
interface-sensitive, and the whole ablation says nothing -- which is itself worth
knowing before it appears on a slide.

Y106A doubles as a probe of the aromatic story: CDR-H3 aromatic fraction predicted
ensemble spread at +0.621 and DockQ at -0.536 on 2026-09-18, so removing a
non-contacting aromatic separates "aromatics matter through the interface" from
"aromatics matter through loop conformation". n=1, so this is a hypothesis-generator
only.

2 seeds per mutant: enough to see whether a change exceeds seed noise (DockQ seed
sd 0.018, surrogate 0.467), not enough to rank mutants against each other. The
comparison that matters is mutant-vs-parent, where the parent has 7 seeds.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

WINNER = "mpnn_T0.5_s104_036"
POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/ablation")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEEDS = (41, 42)

HOTSPOTS = [(31, "Y", 54, "CDR-H1"), (100, "D", 54, "CDR-H3"), (99, "R", 50, "CDR-H3"),
            (57, "N", 39, "CDR-H2"), (102, "D", 31, "CDR-H3"), (97, "R", 30, "CDR-H3")]
CONTROLS = [(96, "L", 0, "CDR-H3 non-contacting"), (106, "Y", 0, "CDR-H3 non-contacting")]
TRIPLE = [(31, "Y"), (99, "R"), (100, "D")]


def mutate(seq: str, subs: list[tuple[int, str]]) -> str:
    s = list(seq)
    for i, expect in subs:
        if s[i] != expect:
            raise SystemExit(f"position {i} is {s[i]}, expected {expect} -- "
                             f"the heavy chain is not the one the contacts were measured on")
        s[i] = "A"
    return "".join(s)


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    w = pool[WINNER]
    heavy = w["heavy"]

    plan = []
    for idx, aa, n, where in HOTSPOTS:
        plan.append((f"{aa}{idx}A", "hotspot", where, n, mutate(heavy, [(idx, aa)])))
    for idx, aa, n, where in CONTROLS:
        plan.append((f"{aa}{idx}A", "control", where, n, mutate(heavy, [(idx, aa)])))
    plan.append(("Y31A_R99A_D100A", "triple", "CDR-H1+H3", 158, mutate(heavy, TRIPLE)))

    OUT.mkdir(parents=True, exist_ok=True)
    have = done()
    print(f"winner {WINNER}, heavy {len(heavy)} aa, {len(plan)} mutants x {len(SEEDS)} seeds",
          flush=True)
    for name, kind, where, n, _ in plan:
        print(f"  {name:16s} {kind:8s} {where:22s} contacts_removed={n}", flush=True)

    t0, ok, bad = time.time(), 0, 0
    for name, kind, where, ncon, mut in plan:
        for seed in SEEDS:
            label = f"abl_{name}__s{seed}"
            if label in have:
                print(f"skip {label}", flush=True)
                continue
            try:
                r = drv.fold(label, mut, w["light"], w["antigen"], out_root=OUT,
                             construct="fab", seed=seed, antigen_msa=PD1_MSA)
            except FoldFailed as e:
                bad += 1
                print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
                rec = {"label": label, "mutant": name, "kind": kind, "seed": seed,
                       "ok": False, "error": str(e)[:400]}
            else:
                ok += 1
                print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
                rec = {"label": label, "mutant": name, "kind": kind, "where": where,
                       "contacts_removed": ncon, "seed": seed, "ok": True,
                       "pdb": str(r.pdb), "pae": str(r.pae), "plddt": str(r.plddt),
                       "seconds": r.seconds}
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"\nablation: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
