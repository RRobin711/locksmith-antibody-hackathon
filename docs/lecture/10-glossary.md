---
date: 2026-09-23
tags: [project, lecture, learning, index, resource]
status: review
---

# Chapter 10 — Glossary

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1 and C2, and what they do and do not invalidate](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding. Challenge 1 is unaffected.

## What this chapter teaches

Nothing — it is a reference. Every term, acronym, metric, tool and piece of
jargon used in the course, defined in one place, with the project's own measured
values attached where they exist. Entries are alphabetical within four sections:
**biology**, **structure prediction**, **metrics and tools**, and **statistics
and method**.

Where a definition carries a warning, the warning is the important part.

---

## 1. Biology

**Affinity** — how tightly two molecules bind, usually as a dissociation constant
K_D. Nothing in this project measures affinity. Every "binding" number here is a
predictor's self-assessed confidence.

**Antibody** — a Y-shaped immune protein made of two identical heavy chains and
two identical light chains, which binds a target with high specificity.

**Antigen** — the molecule an antibody binds. Here, PD-1.

**CDR (complementarity-determining region)** — the six hypervariable loops, three
on the heavy chain (H1, H2, H3) and three on the light (L1, L2, L3), that form
the binding surface. Everything else in the variable domain is *framework*.

**CDR-H3** — the third heavy-chain CDR, and the dominant contributor to binding.
It is the only loop built by V(D)J recombination with junctional diversity, so it
varies in length and composition far more than the other five. In this project it
is 13 residues long; pembrolizumab's is `ARRDYRFDMGFDY` and the winning design's
is `ALRPRDVDRGFYK`.

**Checkpoint blockade** — a cancer therapy that blocks an inhibitory receptor on
a T cell, preventing a tumour from switching that T cell off.

**Deamidation** — spontaneous chemical degradation of an asparagine (N) residue,
proceeding through a cyclic succinimide intermediate. Strongly accelerated when
the next residue is glycine, because glycine's lack of a side chain permits the
ring to form. An `NG` motif is therefore a liability. Note the chemistry happens
*at the asparagine*: mutating the Asn eliminates it, while mutating the Gly only
slows it.

**Developability** — whether a molecule that binds can actually become a drug:
solubility, stability, expression yield, freedom from chemical liabilities. A
design can bind perfectly and be undevelopable.

**Epitope** — the patch of the antigen an antibody actually touches. Here, the
region of PD-1 that overlaps the PD-L1 binding footprint. The pembrolizumab
epitope on 5GGS is 27 residues; the PD-L1 footprint is 26; they share 15, which
is the **58%** figure.

**Fab** — "fragment, antigen-binding": the variable domains plus the first
constant domain of each chain. Larger and more realistic than an Fv.

**Framework** — the conserved structural scaffold of a variable domain that holds
the CDRs in place. Framework conservation is why whole-chain identity is a
useless novelty screen: every antibody sits at **86–94%** identity to something.

**Fv** — "fragment, variable": just the two variable domains, VH and VL. The
minimal binding unit. Cheaper to fold, but which of Fv and Fab you use changes
answers — see `netsolp_construct` in [Chapter 02](02-the-engineering-problem.md).

**Glycosylation sequon** — the sequence motif **N-X-S/T** (asparagine, any residue
except proline, then serine or threonine), which is a substrate for enzymatic
attachment of a sugar chain. In a binding site this is a liability. Both of this
project's Challenge 2 sequons were in the paratope.

**Heavy chain / light chain** — the two chain types in an antibody. The heavy
chain contributes CDR-H3 and usually dominates binding.

**[IgV fold](01-the-biological-problem.md#25-the-igv-fold-and-the-trap-it-set)** — the immunoglobulin variable domain fold. PD-1 has one, which is
why the antibody-numbering tool [ANARCII](03-the-toolchain.md#45-anarcii-208-imgt-numbering-and-the-antigen-it-numbered-as-an-antibody) cheerfully numbers PD-1 *as an antibody*.

**IMGT** — a standardised antibody residue-numbering scheme. Numbering schemes
matter more than they look: IMGT and [Kabat](01-the-biological-problem.md#24-numbering-schemes-and-why-the-novelty-gate-depends-on-one) disagree on CDR-H3 boundaries, which
changes the identity **denominator from 11 to 13**, which changes a novelty gate's
value.

**Nivolumab / pembrolizumab (Keytruda)** — licensed anti-PD-1 antibodies.
Pembrolizumab is the parent molecule for Challenge 1 and the positive control
throughout. It scores **76.0 and is non-viable** under the rubric, failing the
novelty gate at 100% CDR-H3 identity — which is the correct answer.

**Paratope** — the antibody's side of the interface; the residues that touch the
antigen.

**PD-1** — programmed cell death protein 1, an inhibitory receptor on T cells.
The target.

**PD-L1** — PD-1's natural ligand, displayed by tumour cells to switch T cells
off. A therapeutic antibody works by occluding the PD-L1 footprint.

**Polyreactivity** — an antibody's tendency to stick to things it should not.
High positive charge in CDR-H3 is a leading predictor; the winning design carries
net charge **+2** where pembrolizumab carries **0**.

**Sequon** — see *[glycosylation sequon](01-the-biological-problem.md#61-two-n-glycosylation-sequons-in-the-challenge-2-paratope)*.

**SKEMPI** — a database of experimentally measured binding-affinity changes on
mutation (ΔΔG). The only external ground truth this project touched, and the
source of its most damaging result.

**Specificity** — binding the intended target and not others. The named Challenge
1 design failed its own pre-declared specificity condition against **[TIM-3](01-the-biological-problem.md#64-tim-3-cross-reactivity-a-specificity-failure)**.

**TIM-3** — another immune checkpoint receptor, used here as a decoy antigen.

---

## 2. Structure prediction

**AlphaFold2 / [ColabFold](03-the-toolchain.md#32-colabfold-alphafold2-multimer)** — the original high-accuracy folding model and a
convenient wrapper. Qualified and dropped here: it **cannot fold designed
antibodies without an MSA**, giving pLDDT 37 and interpenetrating chains.

**[B-factor](03-the-toolchain.md#47-gemmi-freesasa-and-the-interface-definition) column** — a PDB field that holds crystallographic disorder in an
experimental structure and **per-residue confidence in a predicted one**. Same
column, two incompatible meanings. A classic [silent failure](08-what-broke.md#class-1-silent-failures).

**[Boltz-2](03-the-toolchain.md#31-boltz-2-the-primary-predictor)** — the folding model used for essentially everything here, version
2.2.1. Training cutoff **2023-06-01 on PDB release date** — release, not
deposition.

**Diffusion samples** — how many candidate structures the diffusion head
generates. Boltz's default is **1**, and outputs are returned ranked, so
`model_0` at the default is an **[argmax by construction](06-allocation-and-selection.md#5-order-statistics-when-your-prediction-is-silently-a-maximum)**, not a sample. Five
samples cost 2m54s against ~2m for one.

**Folding / structure prediction** — predicting a protein's three-dimensional
coordinates from its sequence.

**MSA (multiple sequence alignment)** — a stack of evolutionarily related
sequences. Folding models read co-evolution from it. **Antibody chains want no
MSA**, because their diversity is somatic rather than evolutionary, so an
alignment is misleading.

**PAE (predicted aligned error)** — a matrix estimating, for each residue pair,
how wrong their relative position is likely to be, in ångströms. The only source
of inter-chain positional confidence, and the input to [ipSAE](03-the-toolchain.md#43-ipsae-interface-confidence-from-the-pae).

**pLDDT** — predicted local distance difference test: per-residue confidence,
0–100. A statement about the model's certainty, not about correctness. One design
here carried pLDDT **90.5** on a loop moving **4.31 Å** between seeds.

**PTX vs [SASS](03-the-toolchain.md#62-sass-versus-ptx-the-mechanism-you-need)** — SASS is machine code compiled for one specific GPU
architecture; PTX is an intermediate representation the driver can just-in-time
compile for a *newer* one. A wheel shipping SASS but no PTX cannot run on a newer
chip at all. `get_arch_list()` showing `PTX entries: NONE` is why the Blackwell
GPU failed.

**Recycling steps** — how many times a folding model feeds its own output back as
input to refine it. Inherited here as **3** from another task and never
re-examined until it had produced a published, wrong, unanimous result. At
recycling 10 one design moved ipSAE **0.263 → 0.864**.

**[RFdiffusion](03-the-toolchain.md#22-rfdiffusion-via-rfantibody) / RFantibody** — generative models that produce protein backbones,
optionally conditioned on target hotspots.

**[ProteinMPNN](03-the-toolchain.md#21-proteinmpnn)** — designs a sequence given a fixed backbone. Critically, it
optimises **sequence recovery given a backbone** — solubility and developability
are not in its loss. It also **cannot vary loop length**.

**SEQRES vs coordinates** — a PDB file states the full construct sequence in
`SEQRES` records and the *observed* atoms in coordinate records. Unresolved loops
appear in the former and not the latter. Building a sequence from coordinates
therefore **splices out** missing segments, producing a chimera. This error
changed a verdict here from FAIL to MARGINAL.

---

## 3. Metrics and tools

**ANARCII** — antibody numbering tool, 2.0.8. Will number PD-1 as an antibody
given the chance.

**Contacts** — count of heavy-atom pairs across the interface within a distance
cutoff. Measured [ICC](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants) here: **0.003**. Pure sampler noise.

**CDR SASA** — solvent-accessible surface area of the CDR loops, in Å². Measured
ICC: **0.000**.

**[DockQ](03-the-toolchain.md#41-dockq-213-two-flags-that-both-default-wrong)** — a 0–1 measure of how close a predicted complex is to a reference
structure, with CAPRI quality bands. Version 2.1.3. **At its defaults it refuses
to score a redesigned antibody**, exiting 1 with no output; it needs
`--allowed_mismatches` and a pinned chain mapping. Note also that DockQ requires
a reference, so it does not exist for a de novo target.

**ipSAE** — an interface score computed from the PAE matrix with a 10 Å cutoff.
The only gate in this rubric that actually rejects anything. Locates its pLDDT
input by **string-substituting the PAE filename**, so renaming a file makes it
write an empty table and exit 0.

**Interface pLDDT** — mean pLDDT over interface residues. One of only two metrics
shown to respond to the epitope (64.0× its seed standard deviation under
knockout).

**[NetSolP](03-the-toolchain.md#44-netsolp-10-sequence-only-solubility-and-a-positive-control-that-chose-the-model)** — a sequence-only solubility predictor. Ships **three** model
variants scoring a licensed antibody at 0.379 / 0.463 / 0.733 against a 0.50
cutoff. Aggregated here as `min(VH, VL)`.

**[PRODIGY](03-the-toolchain.md#42-prodigy-240-δg-and-contacts)** — predicts binding free energy ΔG in kcal/mol from a structure. It is
a **contact-count regression over an unminimised predicted pose**, with no
solvation term. Shown here to be **blind to the epitope** (0.9× its own seed sd
against a 527-contact deletion) while carrying the largest share of the ranking
variance.

**RF2** — RoseTTAFold2, used as a cheap filter. Its poses sit **24.9 Å** from the
designed pose.

**uv** — the Python package manager used throughout. `uv tool install` gives each
tool its own environment plus a CLI shim, which is how the [numpy 2.0](03-the-toolchain.md#5-the-numpy-20-fault-line-and-isolation-as-architecture) conflict was
resolved.

---

## 4. Statistics and method

**Ablation** — deliberately removing part of a design to see whether a metric
notices. Here, removing 158 antigen contacts cost 0.030 DockQ and *gained* four
contacts, because the predictor simply re-docked and rebuilt an interface.

**Argmax by construction** — see *diffusion samples*. When a generator returns
ranked output and you take the first, you have an order statistic, not a sample.

**Attenuation** — the shrinking of an observed correlation by measurement noise:
`ρ_obs ≈ ρ_true · √(r₁r₂)`. With [reliability](04-measurement-theory.md#13-reliability) 0.75 on each side, a true 0.80
presents as 0.60. Never report a corrected value as observed.

**Detectable effect** — the smallest effect an experiment could have found at its
sample size. **A null is only meaningful as "no effect larger than x."** Four
claims here were published as findings of absence and reversed.

**Effect size (Cohen's d)** — a standardised mean difference.

**Equal-budget null** — the correct null for a filter: the same filter applied at
random, retaining the same number of items. A random subset retaining fraction f
keeps the maximum with probability exactly f, and one of the top five with ~97%
at f = 0.5 — so "our filter kept the best design" proves nothing.

**Fisher-z** — a transformation making correlation standard errors tractable:
`SE = 1/√(n−3)`. At n = 14 that is 0.30, so a measured ρ of 0.47 carries a 95% CI
of **[−0.14, +0.82]**.

**Goodhart's law** — when a measure becomes a target it stops being a good
measure. The organising anxiety of this project.

**ICC (intraclass correlation)** — reliability estimated from k replicate
measurements of the same item. ICC ≈ 0 means the metric is **pure sampler
noise**; it carries no information about the item at all.

**Mutation testing** — deliberately reintroducing bugs to check your test suite
detects them. *A green suite is a claim about the code; a suite shown to go red
on reintroduced defects is evidence about the suite.*

**Optional stopping** — looking at data, then collecting more, then testing at
nominal α. Inflates the type-I error rate; the reported p is not the real one.
The conditioning result here (d = 1.47, p = 0.0016) was affected and was replaced
with a deterministic per-item null.

**Partial correlation** — the correlation between X and Y with Z held constant.
Used here to adjudicate whether a 3-fold ensemble measurement carried information
a free sequence feature did not. The answer half-reversed at larger n.

**Pre-registration** — writing down the hypothesis, analysis and failure
condition *before* seeing the data. Eleven documents here; at least three fired
against the author's interest.

**Range restriction** — reliability is a *ratio* of true variance to total
variance, so narrowing the range of items destroys it even with unchanged noise.
The crucial corollary: **shortlisting is itself the range-restricting
operation**, so reliability measured on a wide pool never applies to the
selection stage.

**Reliability** — `r = var_true / var_observed`. How much of what you measured is
signal. Distinct from **validity**, which asks whether the signal is the thing you
care about. The central confusion this project ran on for six days.

**[Spearman–Brown](04-measurement-theory.md#3-spearmanbrown-what-averaging-buys)** — how reliability improves with k replicates:
`r_k = k·r₁ / (1 + (k−1)·r₁)`.

**Validity** — whether a metric measures what it claims to. A metric can be
perfectly reliable and completely invalid. See *reliability*.

**Winner's curse** — the top-scoring candidate from a noisy pool is
disproportionately one whose noise landed high, so its score is biased upward.
Correction: `corrected = pool_mean + reliability × (observed − pool_mean)`. Note
that a **larger pool makes the correction larger, not smaller**, and that a single
fresh measurement can never validate the correction however closely it lands.

---

## Cross-references

Definitions here are expanded where they are used:
[biology](01-the-biological-problem.md),
[the rubric and the pipeline](02-the-engineering-problem.md),
[tool versions and gotchas](03-the-toolchain.md),
[reliability](04-measurement-theory.md),
[nulls and controls](05-experiment-design.md),
[allocation, banding and the winner's curse](06-allocation-and-selection.md).
