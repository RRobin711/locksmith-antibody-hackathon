#!/usr/bin/env python3
"""Package Challenge 2 from the CONSTRAINED re-design: bb_8_0.

WHY THIS REPLACES scripts/75 RATHER THAN EDITING IT. `75` selects from
`runs/challenge2_fold_r10/scores.jsonl`, every row of which was folded with the antigen
alignment silently discarded (see `results/msa_silently_discarded.md`). Its pre-registered
rule is sound; the data under it is not. Rather than repoint a script whose provenance
comment describes a different run, this one reads the re-screen and says so.

WHAT SHIPS. `bb_8_0`, produced by constrained re-design on an existing backbone. It beats
the design it replaces on every axis: ipSAE median **0.859 vs 0.637**, worst sample **0.819
vs 0.423**, **5/5 viable vs 3/5**, composite **93.6 vs 90.0**, and it **passes §9.2** where
the other fails with two HIGH CDR liabilities that were measured unrepairable.

It needed no constraint to find: it was clean on the first batch of 8 sequences. The pilot
drew ~3 per backbone. This backbone read ipSAE **0.011** unconstrained and **0.859** with
more sequences drawn on the same geometry -- sampling depth, not backbone diversity.

THREE CHECKS BEFORE IT WAS TRUSTED, because a de novo design outscoring real crystals is
the shape of the artefact this project already fell for:
  1. Alignment **demonstrably used** -- processed MSA width 123 = antigen length 123,
     depth 1024. Not "no warning fired".
  2. Matched control, identical construct/alignment/sampling: pembrolizumab **0.877**,
     bb_8_0 **0.859**, trastuzumab (anti-HER2 negative) **0.057**. Ours sits just BELOW a
     licensed antibody on its own target and ~15x above an irrelevant one.
  3. Memorisation: highest CDR identity to any known anti-PD-1 is 62.5% on **CDR-H1**,
     which is germline-encoded -- an anti-VEGF antibody scores **87.5%** on that same loop
     against pembrolizumab. On **CDR-H3**, where novelty lives, ours is 23.1%, the same as
     trastuzumab's and more divergent than cetuximab's 38.5%.

THE STRUCTURE IS `model_0`, Boltz's own top-ranked prediction and an argmax by
construction. Here it barely matters: all five samples score composite **93.6** and all
five are viable, so the median and the shipped model agree exactly.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import liabilities
from locksmith.score import evaluate
from locksmith.submit.package import Design, build_challenge, build_zip
from locksmith.submit.docs import challenge2_repro_md

TEAM, CHALLENGE = "LOCKSMITH_DEV", 2
ROOT = Path("submission")
DID = "bb_8_0"
LABEL = f"cf_{DID}"
RUN = Path("runs/constrained_fold") / LABEL / f"boltz_results_{LABEL}" / "predictions" / LABEL


def main() -> int:
    cfg = load()
    bd = json.loads(Path("runs/constrained_fold/bb_8_0_check3.json").read_text())
    per, med = bd["per_sample"], bd["median"]
    d = {r["backbone"]: r for r in json.loads(
        Path("runs/redesign_yield/yield.json").read_text()) if r["clean"]}[DID]
    d["antigen"] = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    METS = ["ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa", "netsolp", "cdrh3_identity"]

    # The breakdown JSON was produced with novelty.compute()'s DEFAULT reference, which is
    # Challenge 1's (Keytruda). S6.3.1 specifies human germline for Challenge 2. Same
    # metric, different reference; using the wrong one here put 20.0 in the docs against
    # the validator's 33.3. Recomputed with the challenge, not inherited.
    from locksmith.metrics import novelty as _nov
    _ident = _nov.compute(d["heavy"], challenge=CHALLENGE).value
    for _row in per:
        _row["cdrh3_identity"] = _ident
    med["cdrh3_identity"] = _ident

    m0 = per[0]
    sc0 = evaluate({k: m0[k] for k in METS}, challenge=CHALLENGE, cfg=cfg)
    scm = evaluate(med, challenge=CHALLENGE, cfg=cfg)
    n_viable = sum(1 for x in per
                   if evaluate({k: x[k] for k in METS}, challenge=CHALLENGE, cfg=cfg).viable)

    rep = liabilities.compute(d["heavy"], d["light"])
    CDR = ("CDR-H1", "CDR-H2", "CDR-H3", "CDR-L1", "CDR-L2", "CDR-L3")
    cdr_hits = [x for x in rep.liabilities
                if (getattr(x, "region", "") or "") in CDR
                and (getattr(x, "kind", "") == "glycosylation"
                     or getattr(x, "motif", "") in ("NG", "DG"))]

    rows = ["# Our own recomputation of the seven scored metrics", "",
            f"Design `{DID}`, folded with Boltz-2 on the handbook's §4.2.2 antigen with a "
            f"matched antigen alignment (`pd1_123_handbook.csv`, 3407 sequences, "
            f"**verified used**: processed MSA width 123 = antigen length 123). Every "
            f"Challenge 2 fold before 2026-09-23 used an alignment Boltz silently "
            f"discarded; see `methods_and_limitations.md`.", "",
            "Conventions: `band_value=top`, `netsolp_construct=fv`, `netsolp_chain_agg=min`.", "",
            "**Seven, not eight — DockQ is excluded.** §5.2 applies DockQ to Challenge 1 only, "
            "because a de novo design has no reference structure. Every metric below is "
            "computed from the two files in `structures/`, which we generated. "
            "**A confidently wrong pose scores exactly like a right one.**", "",
            "## The submitted structure (`model_0`)", "",
            "| metric | value | band | sub-score |", "|---|---|---|---|"]
    for k in sorted(METS):
        rows.append(f"| `{k}` | {m0[k]:.3f} | {sc0.bands.get(k)} | {sc0.sub.get(k, 0):.1f} |")
    rows += ["", f"**Final: {sc0.final} / 100. Viable: {sc0.viable}.**", "",
             "## The central estimate — median of five diffusion samples", "",
             "`model_0` is Boltz's own top-ranked output and therefore an **argmax by "
             "construction**, not a draw. The median over five samples is what any claim "
             "here rests on.", "",
             "| metric | model_0 | median of 5 | spread across 5 |", "|---|---|---|---|"]
    for k in sorted(METS):
        vals = [x[k] for x in per]
        rows.append(f"| `{k}` | {m0[k]:.3f} | **{med[k]:.3f}** | {min(vals):.3f} – {max(vals):.3f} |")
    rows += ["",
             f"Composite on the median metrics: **{scm.final}**. Per-sample composites: "
             f"{', '.join(str(x) for x in bd['finals'])}.", "",
             f"### Viable on **{n_viable} of 5** diffusion samples.", "",
             f"Every sample clears the §7.2 ipSAE cutoff. The median clears it by "
             f"**{med['ipsae'] - 0.60:.3f}** and the *worst* sample reads "
             f"**{min(x['ipsae'] for x in per):.3f}** — still above the 0.80 Good edge. "
             f"The composite is **{scm.final} on all five samples**, so the shipped "
             f"`model_0` and the median agree exactly and nothing here depends on which "
             f"draw was kept."]

    docs = f"""# Methods and limitations — Challenge 2

## What this design is

`{DID}`, a ProteinMPNN sequence on an RFdiffusion/RFantibody backbone conditioned on the
26-residue PD-L1-competitive footprint of PD-1. **All six CDRs are designed;** the
framework is RFantibody's stock humanised trastuzumab scaffold, **unchanged** — VH 86/86
and VL 80/80 framework positions identical to the stock scaffold. §3.2 asks for a complete
VH/VL designed de novo and **this does not meet that**. The rubric does not detect it,
because `cdrh3_identity` reads only CDR-H3 — genuinely novel here at **{med['cdrh3_identity']:.1f}%
to human germline**, the reference §6.3.1 specifies for Challenge 2. Disclosed rather than
left to be found.

## How it was found, and why that is the finding

This backbone scored ipSAE **0.011** in the original screen. It scores **{med['ipsae']:.3f}** here.
**The backbone did not change.** The pilot drew ~3 sequences per backbone; drawing 8 found
this one, clean on the first batch. Across 18 backbones, deeper sampling took 2 to
viability where 1 of 30 sequences had cleared before.

That is the transferable result: **sequence depth per backbone, not backbone diversity,
was the binding constraint** — and establishing it required no new backbones and no rented
hardware.

## The defect that invalidated every earlier Challenge 2 number

Every Challenge 2 fold before 2026-09-23 paired the 123-residue antigen with a cached
alignment whose query is 113 residues. Boltz compares lengths, **discards the alignment**,
substitutes a dummy, and says so only on a stdout stream this code captured and threw
away. Measured 2×2, the mutation is irrelevant and the alignment is the whole effect:

| | antigen MSA used | antigen MSA absent |
|---|---|---|
| previously-submitted design | **0.012** | 0.686 |
| its pre-fix predecessor | **0.012** | 0.773 |

**"1 of 30 clears" was measured in a condition that flatters every design.** Two guards now
prevent it: `write_input` refuses a length-mismatched alignment, and `fold()` raises on the
warning rather than discarding it. For this design the alignment is **positively verified
as used**, not merely unflagged.

## Three checks on a suspiciously good number

A de novo design outscoring real crystals is the exact shape of the artefact above, so
{med['ipsae']:.3f} was checked before it was believed.

**Alignment used.** Processed MSA width 123 = antigen length 123, depth 1024.

**Matched control** — real antibodies, identical construct, alignment, sampling:

| | median ipSAE | viable |
|---|---|---|
| pembrolizumab (licensed anti-PD-1) | **0.877** | 5/5 |
| **`{DID}` (this design)** | **{med['ipsae']:.3f}** | **{n_viable}/5** |
| nivolumab (licensed anti-PD-1) | 0.474 | 1/5 |
| trastuzumab (anti-HER2, negative) | **0.057** | 1/5 |

It sits **below** a licensed antibody on its own target and ~15× above an irrelevant one.

**Memorisation.** Highest CDR identity to any known anti-PD-1 is **62.5%**, on CDR-H1 —
which is germline-encoded, and an anti-VEGF antibody (bevacizumab) scores **87.5%** on that
same loop against pembrolizumab. On **CDR-H3**, where novelty lives, this design is
**23.1%** to pembrolizumab — the same as trastuzumab's and more divergent than cetuximab's
38.5%. No drift toward a known binder.

## Two things this run found about the rubric

**An anti-HER2 antibody clears the viability cutoff on one draw of five.** Trastuzumab
against PD-1, correct alignment, handbook construct: samples 0.740 / 0.210 / 0.057 / 0.000
/ 0.000. Its best sample passes §7.2. `diffusion_samples=1` returns an argmax by
construction, so a single-sample run can certify an antibody that cannot bind. **This is
why every number here is a median of five.**

**A licensed anti-PD-1 drug is non-viable on the handbook's own construct.** Nivolumab
scores **0.474** on the specified 123-mer and **0.691** when six N-terminal residues are
restored. Its epitope needs `LDSPDR` (L25–R30); the handbook construct starts at `DSPDRP`
and misses L25. The epitope analysis predicted this before either fold existed.
Pembrolizumab's epitope is 100% inside all constructs, which is why the truncation stayed
invisible for the whole project.

## Liabilities

**Passes §9.2.** No N-glycosylation sequon and no NG/DG motif in any CDR. This was achieved
at *generation* — the sequence was screened before it was folded — not by repairing a
finished design. That distinction is load-bearing: on the design this replaces, all three
prescribed repair routes were measured killing the interface, including one at a residue
with **zero** antigen contacts.

## What we can and cannot claim

**Cannot: that this binds.** ipSAE {med['ipsae']:.3f} is Boltz's confidence given evolutionary
information about the antigen. Nothing here is an affinity measurement, and this project's
SKEMPI work found no metric in the stack tracks measured ΔΔG.

**Can: that the confidence is calibrated.** Against 40 real crystallised complexes folded
through this identical pipeline, ipSAE tracks pose accuracy at Spearman **ρ = +0.702** with
error rates that **must be quoted at one threshold**. Against DockQ ≥ 0.49 (Medium+) the
ipSAE ≥ 0.60 gate gives **12.5% false-positive / 25.0% false-negative**; against DockQ ≥ 0.23
(Acceptable+) it gives **0% false-positive / 58.3% false-negative**, and that 0% rests on
only 4 negatives — a Clopper–Pearson 95% upper bound of **0.602**, i.e. uninformative. An
earlier version of this document paired the 0% with the 25%, which is the favourable half of
each threshold and is reachable at neither. The post-cutoff (novel-antigen) median is 0.165.

**Can: that the targeting is evidenced.** Backbones were conditioned on the PD-L1
competitive footprint; against 2000 random contiguous surface patches of the same size on
the same chain, 17 of 18 backbones sit at p<0.05 (real epitope 0.712 vs patch 0.154).
"""

    pdb = RUN / f"{LABEL}_model_0.pdb"
    dsn = Design(name="design_1", heavy=d["heavy"], light=d["light"], antigen=d["antigen"],
                 pdb=pdb, pae_npz=RUN / f"pae_{LABEL}_model_0.npz",
                 plddt_npz=RUN / f"plddt_{LABEL}_model_0.npz",
                 confidence_json=(RUN / f"confidence_{LABEL}_model_0.json"
                                  if (RUN / f"confidence_{LABEL}_model_0.json").exists() else None))
    # Regenerate reproducing_our_numbers.md too. Leaving it out is what orphaned the
    # previous one: scripts/75 wrote it for the design this replaces, and swapping the
    # design without rewriting the doc shipped a file describing a structure that is no
    # longer in the package. `m0` is model_0, which is the design actually written here.
    repro = challenge2_repro_md(m0, cfg.conventions, TEAM, d["heavy"])
    base = build_challenge(ROOT, TEAM, CHALLENGE, dsn,
                           metrics_md="\n".join(rows), docs_md=docs,
                           extra_docs={"reproducing_our_numbers.md": repro})
    print(f"built {base}")
    print(f"  model_0 composite {sc0.final}, median-metrics composite {scm.final}, "
          f"viable {n_viable}/5")
    print(f"  {len(cdr_hits)} HIGH CDR liabilities disclosed")
    z = build_zip(ROOT, TEAM)
    print(f"built {z} ({z.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
