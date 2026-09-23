#!/usr/bin/env python3
"""Package Challenge 2 from the RE-SCREEN, as a checkpoint so a failed campaign costs nothing.

WHY THIS REPLACES scripts/75 RATHER THAN EDITING IT. `75` selects from
`runs/challenge2_fold_r10/scores.jsonl`, every row of which was folded with the antigen
alignment silently discarded (see `results/msa_silently_discarded.md`). Its pre-registered
rule is sound; the data under it is not. Rather than repoint a script whose provenance
comment describes a different run, this one reads the re-screen and says so.

WHAT SHIPS. `bb_1_0_dldesign_0`, the one design of 30 that clears ipSAE >= 0.60 on the
median of five diffusion samples under a correct alignment -- **unfixed**. All three §9.2
repair routes were measured killing it (`results/liability_fix_arms.md`), including one at
a residue with zero antigen contacts, so it ships carrying two HIGH CDR liabilities, both
disclosed here.

THE STRUCTURE IS `model_0` -- Boltz's own top-ranked prediction, which is an argmax by
construction. Its ipSAE is 0.855; the design's central estimate is the **median of five,
0.637**. Both appear, in their own places, and the median is what any claim rests on.

VIABILITY IS 3 OF 5, not 5 of 5. No "viable throughout" language survives from the design
this replaces.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import liabilities
from locksmith.score import evaluate
from locksmith.submit.package import Design, build_challenge, build_zip

TEAM, CHALLENGE = "LOCKSMITH_DEV", 2
ROOT = Path("submission")
DID = "bb_1_0_dldesign_0"
LABEL = f"rs_{DID}"
RUN = Path("runs/challenge2_rescreen") / LABEL / f"boltz_results_{LABEL}" / "predictions" / LABEL


def main() -> int:
    cfg = load()
    bd = json.loads(Path("runs/challenge2_rescreen/breakdown_bb_1_0_dldesign_0.json").read_text())
    per, med = bd["per_sample"], bd["median"]
    d = {x["design_id"]: x for x in json.loads(
        Path("runs/challenge2_fold_r10/designs.json").read_text())}[DID]
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
            f"Design `{DID}`, folded with Boltz-2 on the handbook's §4.2.2 antigen **with a "
            f"matched antigen alignment** (`pd1_123_handbook.csv`, 3407 sequences). Every "
            f"previous Challenge 2 fold in this project used an alignment Boltz silently "
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
             f"### **Viable on {n_viable} of 5 diffusion samples, not 5 of 5.**", "",
             "Two of the five fall below the §7.2 ipSAE cutoff. The median clears it by "
             f"**{med['ipsae'] - 0.60:.3f}**, and the worst sample reads "
             f"{min(x['ipsae'] for x in per):.3f}. This is a thin pass and is reported as one."]

    docs = f"""# Methods and limitations — Challenge 2

## What this design is

`{DID}`, one of 30 ProteinMPNN sequences on RFdiffusion/RFantibody backbones conditioned on
the 26-residue PD-L1-competitive footprint of PD-1. **All six CDRs are designed;** the
framework is RFantibody's stock humanised trastuzumab scaffold, **unchanged** — VH 86/86
and VL 80/80 framework positions identical to the stock scaffold. §3.2 asks for a complete
VH/VL designed de novo and **this does not meet that**. The rubric does not detect it,
because `cdrh3_identity` reads only CDR-H3 — genuinely novel here at **33.3% to human
germline**, which is the reference §6.3.1 specifies for Challenge 2 (Challenge 1 compares
to Keytruda instead). Against pembrolizumab's CDR-H3 it is 20.0%, but that is the other
challenge's metric and is noted only to prevent the two numbers being confused.
Disclosed rather than left to be found.

## The defect that invalidated our previous submission

Every Challenge 2 fold this project ran before 2026-09-23 paired the 123-residue antigen
with a cached alignment whose query is 113 residues. Boltz compares lengths, **discards the
alignment**, substitutes a dummy, and announces it only on a stdout stream this code
captured and threw away. Measured 2×2:

| | antigen MSA used | antigen MSA absent |
|---|---|---|
| previously-submitted design | **0.012** | 0.686 |
| its pre-fix predecessor | **0.012** | 0.773 |

The mutation is irrelevant; the alignment is the whole effect. **"1 of 30 clears" was
measured in a condition that flatters every design.** Re-screened under a correct
alignment, the previously-submitted design scores **0.013** and this one — ranked 29th of
30 before — scores **{med['ipsae']:.3f}**. Old-vs-new ranking correlation across all 30 is
ρ = +0.366.

Two guards now make the failure impossible to repeat: `write_input` refuses a
length-mismatched alignment, and `fold()` raises on the warning rather than discarding it.

## Known liabilities, unfixed and deliberate

This design **fails handbook §9.2**, carrying two HIGH liabilities in CDRs:

| severity | motif | chain | position | region | contacts to PD-1 (median of 5) |
|---|---|---|---|---|---|
| HIGH | N-glycosylation `NKS` | light | 91 | CDR-L3 | **0** |
| HIGH | deamidation `NG` | light | 31 | CDR-L1 | **13** |

**All three repair routes were measured and all three killed the interface:**

| arm | change | median ipSAE | viable/5 |
|---|---|---|---|
| unfixed (shipped) | — | **{med['ipsae']:.3f}** | **{n_viable}/5** |
| `fix91` | N91Q | 0.128 | 0/5 |
| `fix31` | G32A | 0.140 | 0/5 |
| `fix_both` | N91Q + G32A | 0.034 | 0/5 |

`fix91` mutates a residue with **zero antigen contacts in all five samples** and the design
still collapses. Whether that is residue-specific or simply reflects this design sitting
{med['ipsae'] - 0.60:.3f} above the cutoff — a margin that may absorb no change at all — is
under test with a framework control and is **not** claimed either way here.

So the liabilities ship. A glycosylation site in CDR-L3 is a real developability problem
and we are not pretending otherwise; the alternative was a design that does not bind.

## What we can and cannot claim

**Cannot: that this binds.** ipSAE {med['ipsae']:.3f} means Boltz places this antibody on
PD-1 with moderate confidence given evolutionary information about the antigen. That is a
statement about a predictor. Nothing here is an affinity measurement, and this project's
SKEMPI work found no metric in the stack tracks measured ΔΔG.

**Can: that the targeting is evidenced.** Backbones were conditioned on the PD-L1
competitive footprint, and against 2000 random contiguous surface patches of the same size
on the same chain, 17 of 18 backbones sit at p<0.05 (real epitope 0.712 vs patch 0.154).

**Calibration.** Against 40 real crystallised antibody–antigen complexes folded through
this identical pipeline, ipSAE tracks pose accuracy at Spearman ρ = +0.702 with a **0%
false-positive rate** — it never accepted a wrong pose — and a **25% false-negative rate**.
The post-cutoff (genuinely novel) median ipSAE in that panel is 0.165.
"""

    pdb = RUN / f"{LABEL}_model_0.pdb"
    dsn = Design(name="design_1", heavy=d["heavy"], light=d["light"], antigen=d["antigen"],
                 pdb=pdb, pae_npz=RUN / f"pae_{LABEL}_model_0.npz",
                 plddt_npz=RUN / f"plddt_{LABEL}_model_0.npz",
                 confidence_json=(RUN / f"confidence_{LABEL}_model_0.json"
                                  if (RUN / f"confidence_{LABEL}_model_0.json").exists() else None))
    base = build_challenge(ROOT, TEAM, CHALLENGE, dsn,
                           metrics_md="\n".join(rows), docs_md=docs)
    print(f"built {base}")
    print(f"  model_0 composite {sc0.final}, median-metrics composite {scm.final}, "
          f"viable {n_viable}/5")
    print(f"  {len(cdr_hits)} HIGH CDR liabilities disclosed")
    z = build_zip(ROOT, TEAM)
    print(f"built {z} ({z.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
