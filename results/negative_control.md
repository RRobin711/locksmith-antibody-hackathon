# Negative control — does the viability gate mean anything?

**2026-09-22.** Pre-registered in [the pre-registration written before these folds finished](prereg_2026-09-22_calibration_and_negative_control.md).

## The argument

Every gate in handbook §7.2 is a threshold on a number Boltz produces for an antibody–antigen pair, and this project has only ever shown that its own designs *clear* those thresholds. It never showed that a **wrong** antibody fails them. If a real antibody with an unrelated target is docked onto PD-1 and still scores ipSAE ≥ 0.60, the gate does not measure binding — it registers that two proteins were placed next to each other, and every ipSAE-derived claim in the submission is worthless.

This is the cheapest experiment available with the largest possible consequence. It costs eight folds and nobody ran it for a week.

## Design

Every row below is folded against **the identical 113-residue PD-1 construct** with **the identical cached alignment** (`data/msa_cache/pd1_5ggs.csv`, 3787 sequences), identical flags, `recycling_steps=10`, `diffusion_samples=5`. Antibodies are trimmed to their variable domains by ANARCII. The only thing that varies across rows is which antibody is present, so any difference is attributable to the antibody and to nothing else.

The point estimate is the **median over the five diffusion samples**, fixed in advance. The maximum is reported beside it because `diffusion_samples=1` returns Boltz's own top-ranked model — an argmax, not a sample — and the gap between the two columns is exactly the error a single-sample run would make.

### What a single diffusion sample would have reported

`diffusion_samples=1` is Boltz's default and was this project's setting for most of its life. Boltz ranks its diffusion outputs by its own confidence, so the model it returns is the **argmax of a distribution that was never drawn**. This table is that column: `model_0` of five, scored against every §7.2 hard cutoff.

> ⚠️ **Every row in this table is on the truncated 113-residue construct** (§Design above). That qualifier sat above this subsection's heading, which is not where a reader of the table looks — so it is repeated here. On the repaired 119-mer, HyHEL-10's `5/5 ✅ ALL` below becomes **4/5**, best of five **0.409**. Register [§C9](retractions.md), course [C6](../docs/lecture/CORRECTIONS.md).

| antibody | its real target | arm | ipSAE | ΔG | contacts | iface pLDDT | CDR SASA | §7.2 cutoffs cleared |
|---|---|---|---|---|---|---|---|---|
| pembrolizumab | PD-1 | positive | 0.876 | -12.6 | 106 | 94.8 | 1507 | **5/5** ✅ ALL |
| nivolumab | PD-1 | positive | 0.263 | -11.8 | 78 | 82.3 | 1317 | **4/5** (fails ipsae) |
| Challenge 1 design | PD-1 (ours) | **test** | 0.881 | -12.4 | 99 | 92.0 | 1608 | **5/5** ✅ ALL |
| Challenge 2 design | PD-1 (ours) | **test** | 0.074 | -13.0 | 82 | 77.7 | 1279 | **4/5** (fails ipsae) |
| HyHEL-10 | hen egg lysozyme | negative | 0.609 | -12.4 | 77 | 85.0 | 1084 | **5/5** ✅ ALL |
| cetuximab | EGFR domain III | negative | 0.594 | -10.0 | 54 | 84.0 | 1470 | **4/5** (fails ipsae) |
| CR9114 | influenza haemagglutinin | negative | 0.567 | -8.4 | 56 | 75.6 | 1707 | **4/5** (fails ipsae) |
| bevacizumab | VEGF-A | negative | 0.525 | -11.8 | 75 | 81.0 | 1493 | **4/5** (fails ipsae) |
| BO2C11 | coagulation factor VIII C2 | negative | 0.343 | -11.3 | 119 | 85.6 | 1374 | **4/5** (fails ipsae) |
| trastuzumab | HER2 extracellular domain | negative | 0.011 | -10.1 | 69 | 81.7 | 1415 | **4/5** (fails ipsae) |

### What five samples report

The same folds, collapsed to the **median over the five diffusion samples** — the point estimate fixed in the pre-registration before any of this was seen.

| antibody | its real target | arm | median ipSAE | best of 5 | median ΔG | median contacts | §7.2 cutoffs cleared |
|---|---|---|---|---|---|---|---|
| pembrolizumab | PD-1 | positive | **0.874** | 0.895 | -12.3 | 103 | **5/5** ✅ ALL |
| nivolumab | PD-1 | positive | **0.017** | 0.263 | -12.3 | 78 | **4/5** (fails ipsae) |
| Challenge 1 design | PD-1 (ours) | **test** | **0.863** | 0.881 | -12.4 | 97 | **5/5** ✅ ALL |
| Challenge 2 design | PD-1 (ours) | **test** | **0.012** | 0.074 | -9.9 | 68 | **4/5** (fails ipsae) |
| cetuximab | EGFR domain III | negative | **0.594** | 0.676 | -10.0 | 51 | **4/5** (fails ipsae) |
| BO2C11 | coagulation factor VIII C2 | negative | **0.343** | 0.392 | -11.5 | 113 | **4/5** (fails ipsae) |
| CR9114 | influenza haemagglutinin | negative | **0.307** | 0.567 | -10.6 | 73 | **4/5** (fails ipsae) |
| HyHEL-10 | hen egg lysozyme | negative | **0.219** | 0.609 | -12.6 | 87 | **4/5** (fails ipsae) |
| bevacizumab | VEGF-A | negative | **0.153** | 0.525 | -11.4 | 69 | **4/5** (fails ipsae) |
| trastuzumab | HER2 extracellular domain | negative | **0.000** | 0.011 | -10.1 | 66 | **4/5** (fails ipsae) |

## Verdict, by the pre-registered rules

**Rule 3 fires: the control is INCONCLUSIVE.** 1 of 2 positive controls (nivolumab) failed the 0.60 ipSAE gate on the median. A panel whose positives do not work cannot license any conclusion from its negatives: a uniform failure is then a statement about the pipeline, not about the antibodies. This project has already published a '0/30 viable' that was the sampler's floor rather than a finding, and this has the same shape. The negative arm is reported but **must not be read as evidence that the gate discriminates.**

## The finding that matters more than the verdict

1 of 6 irrelevant antibodies — **HyHEL-10** (anti-hen egg lysozyme) — clear **every one of the §7.2 hard cutoffs** on `model_0`, the model a default `diffusion_samples=1` run returns.

> **On the 113-mer only.** Every row in this section uses the truncated construct named in §Design. The follow-up below repairs it to 119 residues, and there HyHEL-10's best of five is **0.409** — it clears nothing. Register [§C9](retractions.md). Quoting this paragraph without the construct is how the claim travelled to nine other files.


- **HyHEL-10**, whose real target is hen egg lysozyme, docked onto PD-1: ipSAE **0.609**, ΔG **-12.4 kcal/mol**, **77** heavy-atom contacts, interface pLDDT **85.0**, CDR SASA **1084 Å²**. Its median across five samples is ipSAE 0.219 — it fails comfortably when you actually sample.

**Read the mechanism, not just the number.** Boltz orders its diffusion outputs by its own confidence, so `model_0` is the maximum of five draws, and the maximum of five draws from a broad low distribution routinely lands above a threshold the distribution's centre is nowhere near. The gate is not broken. **Reading the gate off a single diffusion sample is.**

The consequence is concrete and not hypothetical: under the sampling settings this project shipped with for most of its life, an antibody raised against hen egg lysozyme would have been certified a viable PD-1 binder on every metric in the rubric. That is not a near miss — it is a clean sweep of the gate set by a molecule that cannot possibly bind.

This is an independent confirmation, from a completely different direction, of [the diffusion-sampling result](diffusion_samples_2026-09-22.md) — which was measured on our own designs and could have been dismissed as a quirk of them. It cannot be dismissed here.

## Which of the five gates actually does any work

A gate that every irrelevant antibody clears is not a filter; it is a formality. Below, each §7.2 cutoff is scored on how many of the 6 known-wrong antibodies it rejects, using the pre-registered median-of-five point estimate.

| §7.2 cutoff | threshold | negatives rejected | positives passed | verdict |
|---|---|---|---|---|
| ipSAE | ≥ 0.6 | 6/6 | 1/2 | partial |
| ΔG (kcal/mol) | ≤ -6.0 | 0/6 | 2/2 | **inert** — rejects nothing |
| contacts | ≥ 10.0 | 0/6 | 2/2 | **inert** — rejects nothing |
| interface pLDDT | ≥ 65.0 | 0/6 | 2/2 | **inert** — rejects nothing |
| CDR SASA (Å²) | > 250.0 | 0/6 | 2/2 | **inert** — rejects nothing |

**4 of the 5 hard cutoffs (ΔG (kcal/mol), contacts, interface pLDDT, CDR SASA (Å²)) are cleared by every antibody in the negative arm.** They are satisfied by any pair of proteins the predictor places in contact at all, so they measure *that a complex was built*, not that it is the right one. Practically, the §7.2 viability decision rests on ipSAE alone, and the other four cutoffs contribute the appearance of a five-way check without the substance of one.

That is worth stating carefully, because it is a criticism of the rubric and not of the tools. ΔG, contact count, interface pLDDT and buried CDR surface are all perfectly good *descriptive* quantities — they just cannot function as pass/fail gates at these thresholds, because the thresholds sit below what a docked-but-wrong complex achieves. A gate has to be calibrated against something that should fail it, and until this experiment nothing in this project ever was.

## Why the positive control split — diagnosed from crystallography, not from a story

Both positives are licensed anti-PD-1 antibodies, so "the pipeline is broken" and "nivolumab is simply a hard case" are both available explanations and **neither is evidence**. The question is answerable with no folding at all: take each antibody's own crystal, list the PD-1 residues it contacts at 4.5 Å, and ask how many of them exist in the construct we fold.

| binding partner | epitope on PD-1 | covered by our folded 113-mer | missing |
|---|---|---|---|
| pembrolizumab (5GGS) | 26 residues | **26/26 (100.0%)** | — |
| nivolumab (5WT9) | 14 residues | **8/14 (57.1%)** | LEU25 ASP26 SER27 PRO28 ASP29 ARG30 |
| PD-L1 (therapeutic target face) (5IUS) | 23 residues | **23/23 (100.0%)** | — |

**The construct is missing 6 of nivolumab's 14 contact residues** — the `LDSPDR` N-terminal segment, PD-1 residues 25–30. Nivolumab did not fail because the pipeline is broken. It failed because **the molecule it was docked against does not contain the surface it binds.**

Every fold in this project used a 113-residue PD-1 beginning at `PWNPP`, inherited from the 5GGS (pembrolizumab) construct and never re-examined. Pembrolizumab's 26-residue epitope is 100.0% inside it, which is why the truncation was invisible for the entire project — **the only reference antibody ever folded was the one incapable of detecting it.**

**How far does the damage reach? Bounded, and in our favour.** The same calculation against the PD-1/PD-L1 complex (5IUS) — the face a checkpoint inhibitor must occlude, and the face our Challenge 2 design was conditioned on — gives a 23-residue footprint of which the folded construct contains **23/23 (100.0%)**. The truncation damages nivolumab, which binds the N-terminal loop, and touches neither pembrolizumab's epitope nor the therapeutic target face. **Our own numbers are not affected by it.** Worth computing rather than assuming: the alternative — having folded against a construct missing part of our own target epitope — would have invalidated the project, and it takes one script to rule out.

**Which construct is used where — corrected 2026-09-23, because an earlier version of this document got it wrong.** This paragraph previously claimed *every* fold in the project used the 113-mer. It does not. The **screening and selection** folds did (`runs/batch_verify`, `runs/challenge2_fold_r10`), and so does the negative control above. The **shipped structures** were folded on the handbook's 123-residue construct, which covers 92.9% of nivolumab's epitope against the 113-mer's 57.1%.

So the defect is not that the submission was measured on a short antigen. It is that **selection and final scoring were done on different constructs** — candidates were ranked against a 113-residue PD-1 and the winner was then re-folded and scored against a 123-residue one. Nothing in the pipeline compared them, and the difference is invisible to pembrolizumab, the only reference ever folded.

**And there is a worse consequence, under investigation rather than concluded.** `data/msa_cache/pd1_5ggs.csv` is aligned to the **113-residue** query. The shipped Challenge 2 fold passed that cache alongside the **123-residue** antigen, and Boltz did not complain: the processed alignment in `runs/sequon_fix/sq_sa/.../processed/msa/sq_sa_0.npz` is **113 columns wide for a 123-residue chain**, with the cached query sitting at offset 5 within the folded sequence. Whether Boltz re-aligns by sequence or maps positionally — in which case the antigen alignment is out of register by five residues for the whole chain — is not something to settle by reading the number. It is being settled by re-folding the shipped design with a matched alignment and comparing; the result is reported wherever it lands.

**The transferable point.** A positive control can fail for a reason that has nothing to do with the thing being controlled for. "The positive failed, so the panel is broken" and "the positive failed, so ignore it" are equally unjustified until you ask *why*, from data. Here the answer took no GPU time and turned a failed control into the most useful finding in the experiment.

## Follow-up: the same experiment on a construct containing both epitopes

**This is a follow-up, not the pre-registered experiment.** Rule 3 fired above and is not retracted. The construct here is the 113-mer extended N-terminally by `LDSPDR` to 119 residues (PD-1 25–143), the minimal change that restores nivolumab's epitope while leaving every previously-used residue in place. The cached alignment cannot be reused against a longer query, so all rows take a fresh MMseqs2 query; because the antigen is byte-identical across rows, the alignment depth of each row is recorded and compared rather than assumed.

| antibody | arm | median ipSAE | best of 5 | §7.2 cutoffs cleared | was (113-mer) |
|---|---|---|---|---|---|
| pembrolizumab | positive | **0.843** | 0.889 | **5/5** ✅ ALL | 0.874 |
| nivolumab | positive | **0.691** | 0.840 | **5/5** ✅ ALL | 0.017 |
| Challenge 1 design | **test** | **0.841** | 0.862 | **5/5** ✅ ALL | 0.863 |
| Challenge 2 design | **test** | **0.013** | 0.194 | **4/5** (fails ipsae) | 0.012 |
| BO2C11 | negative | **0.507** | 0.769 | **4/5** (fails ipsae) | 0.343 |
| trastuzumab | negative | **0.371** | 0.622 | **4/5** (fails ipsae) | 0.000 |
| bevacizumab | negative | **0.308** | 0.555 | **4/5** (fails ipsae) | 0.153 |
| HyHEL-10 | negative | **0.228** | 0.409 | **4/5** (fails ipsae) | 0.219 |
| CR9114 | negative | **0.217** | 0.584 | **4/5** (fails ipsae) | 0.307 |
| cetuximab | negative | **0.052** | 0.399 | **4/5** (fails ipsae) | 0.594 |

**On the repaired construct the control resolves.** All 2 positives clear the gate and all 6 irrelevant antibodies fail it, separated by **0.184 ipSAE**. The diagnosis is therefore confirmed by the intervention it predicted: restoring the six missing residues is sufficient to recover the positive control.

## What this does not establish

Passing this control shows the metric separates cognate from non-cognate pairs. It says **nothing** about whether it ranks correctly among plausible designs, which is the job it is actually asked to do in selection. This project measured that second property failing directly: across a panel of real variants ipSAE wandered within ±0.04 while DockQ fell 0.820 → 0.601, and the highest ipSAE in that panel belonged to a variant with a *worse* pose than the wild type. Discrimination and ranking are different properties and only the first is tested here.
