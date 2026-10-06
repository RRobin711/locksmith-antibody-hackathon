---
date: 2026-09-23
tags: [project, lecture, learning, index, resource]
status: review
---

# Chapter 10 — Glossary

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1–C8](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding, and **C3 applies to Challenge 1**: its composite is **94.0**, not the 96.0 this course derives in several places. Challenge 1 is unaffected *by the alignment defect*, which is narrower than "unaffected". **C4** (the preflight), **C5** (the NetSolP triple) and **C6** were added 2026-09-28 — and **C6 applies to this course's most-quoted finding**: "an anti-lysozyme antibody cleared all five cutoffs" holds on the **truncated 113-mer only**; on the repaired 119-mer it clears nothing. **C7** and **C8** were added 2026-10-05 from work done after this course was written: **C7** corrects this course's count of its own most repeated error (a small-*n* null read as evidence of absence) from **≥6 to ≥7**, the seventh being the first to carry a **spending decision**; **C8** records that the decoy-patch control **has been run and passed**, on CPU for **\$0**, and that no arm of this project needs a rented card.

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

**K_D (dissociation constant), and the concentration units it is quoted in** — *how much
free drug must be floating about before half the target molecules are occupied.* Because a
tight binder needs very little to achieve that, **lower means tighter**. Quoted as a
concentration: **M** (molar) → **mM** (10⁻³) → **µM** (10⁻⁶) → **nM** (10⁻⁹) → **pM**
(10⁻¹²), each step a thousandfold more dilute. Pembrolizumab binds PD-1 at **≈29 pM**,
about 4 µg in a litre — under a tenth of a grain of salt. A *weak* protein–protein
interaction is micromolar, roughly **34,000×** looser than that (µM is a millionfold looser
than 1 pM, not than 29 pM).

K_D and **[ΔG](03-the-toolchain.md#42-prodigy-240--δg-and-contacts)** are the same fact in
different units, `ΔG = RT·ln K_D` (RT ≈ 0.592 kcal/mol at 25 °C), and PRODIGY reports both.
Converting the handbook's own thresholds is clarifying: **Good ≤ −12 kcal/mol ≈ 1.6 nM**,
but the **hard cutoff of ≤ −6 kcal/mol ≈ 40 µM** — a weak interaction, about **1.4 million
times** looser than the licensed drug. That is one reason the ΔG gate
[rejects 0 of 6 known-wrong antibodies](05-experiment-design.md#43-the-negative-control-panel-what-a-known-wrong-input-does-to-your-gates).
Note what is a measurement and what is not: pembrolizumab's 29 pM was measured in a
laboratory; every ΔG here is **predicted**.

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
why the antibody-numbering tool [ANARCII](03-the-toolchain.md#45-anarcii-208--imgt-numbering-and-the-antigen-it-numbered-as-an-antibody) cheerfully numbers PD-1 *as an antibody*.

**IMGT** — a standardised antibody residue-numbering scheme. Numbering schemes
matter more than they look: IMGT and [Kabat](01-the-biological-problem.md#24-numbering-schemes-and-why-the-novelty-gate-depends-on-one) disagree on CDR-H3 boundaries, which
changes the identity **denominator from 11 to 13**, which changes a novelty gate's
value.

**Ligand** — a molecule that binds another molecule, usually a
[receptor](10-glossary.md#1-biology), in order to deliver a signal. From Latin *ligare*,
"to bind" — the same root as *ligament*. Ligand and receptor are a **key and lock** pair:
the receptor sits on the cell surface and *receives*, the ligand fits into it and
*delivers*. Here the pair is **[PD-1](01-the-biological-problem.md#1-the-brake-on-the-immune-system)**
(receptor, on the T cell) and **[PD-L1](01-the-biological-problem.md#31-the-pd-l1-footprint-on-pd-1)**
(ligand, on the cell being inspected) — the name says so: *Programmed Death-**Ligand** 1*.
Both designs here aim at PD-1's **PD-L1-competitive footprint**: the 26 residues PD-L1
itself touches, so that binding there *blocks* it. An antibody gripping any other face of
PD-1 would score the same and do nothing.

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

**Receptor** — a protein, usually spanning a cell's surface, whose job is to
*receive* a signal from outside and change the cell's behaviour. Its partner is a
**ligand**. [PD-1](01-the-biological-problem.md#1-the-brake-on-the-immune-system) is the
receptor in this project: an **inhibitory** one, so the signal it receives is a brake —
*stand down, this cell is friendly* — rather than an accelerator. Blocking a receptor
therefore *releases* the behaviour it was suppressing, which is why an anti-PD-1 antibody
makes T cells **more** aggressive, not less.

**Sequon** — see *[glycosylation sequon](01-the-biological-problem.md#61-two-n-glycosylation-sequons-in-the-challenge-2-paratope)*.

**SKEMPI** — a database of experimentally measured binding-affinity changes on
mutation (ΔΔG). The only external ground truth this project touched, and the
source of its most damaging result.

**Specificity** — binding the intended target and not others. The named Challenge
1 design failed its own pre-declared specificity condition against **[TIM-3](01-the-biological-problem.md#64-tim-3-cross-reactivity--a-specificity-failure)**.

**TIM-3** — another immune checkpoint receptor, used here as a decoy antigen.

---

## 2. Structure prediction

**AlphaFold2 / [ColabFold](03-the-toolchain.md#32-colabfold--alphafold2-multimer)** — the original high-accuracy folding model and a
convenient wrapper. Qualified and dropped here: it **cannot fold designed
antibodies without an MSA**, giving pLDDT 37 and interpenetrating chains.

**[B-factor](03-the-toolchain.md#47-gemmi-freesasa-and-the-interface-definition) column** — a PDB field that holds crystallographic disorder in an
experimental structure and **per-residue confidence in a predicted one**. Same
column, two incompatible meanings. A classic [silent failure](08-what-broke.md#class-1--silent-failures).

**[Boltz-2](03-the-toolchain.md#31-boltz-2--the-primary-predictor)** — the folding model used for essentially everything here, version
2.2.1. Training cutoff **2023-06-01 on PDB release date** — release, not
deposition.

**Diffusion samples** — how many candidate structures the diffusion head
generates. Boltz's default is **1**, and outputs are returned ranked, so
`model_0` at the default is an **[argmax by construction](06-allocation-and-selection.md#5-order-statistics-when-your-prediction-is-silently-a-maximum)**, not a sample. Five
samples cost 2m54s against ~2m for one.

**Backbone** — the repeating N–Cα–C chain of a protein, without side chains. A
[generative backbone model](03-the-toolchain.md#22-rfdiffusion-via-rfantibody) proposes *shape*; a sequence
model then decides which amino acids will fold into it. Challenge 2 generates
backbones; Challenge 1 keeps one fixed and redesigns only the sequence on it — which
is why its gates do not bite.

**Folding / structure prediction** — predicting a protein's three-dimensional
coordinates from its sequence.

**Hotspot** — a target residue named to
[RFdiffusion](03-the-toolchain.md#22-rfdiffusion-via-rfantibody) to tell it *where on the antigen to build*.
Conditioning on 26 hotspots moved interface placement from 0.500 to 0.712; a decoy
patch on the opposite face scored 0.803 there and 0.000 on the real
[epitope](01-the-biological-problem.md#3-the-epitope-which-26-residues). **Receipt is not effect** — the tool
silently skips hotspots it cannot match, so `26/26 resolved` proves only that it read
them.

**ipTM** — AlphaFold-family *interface* predicted TM-score, a single 0–1 number for
how confidently the model placed two chains together. Distinct from
[ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae), which is computed from the
[PAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae) matrix restricted to interface pairs.
These are **not interchangeable**, which is the entire point of the sentence that
first names them together.

**MSA (multiple sequence alignment)** — a stack of evolutionarily related
sequences. Folding models read co-evolution from it. **Antibody chains want no
MSA**, because their diversity is somatic rather than evolutionary, so an
alignment is misleading.

**PAE (predicted aligned error)** — a matrix estimating, for each residue pair,
how wrong their relative position is likely to be, in ångströms. The only source
of inter-chain positional confidence, and the input to [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae).

**pLDDT** — predicted local distance difference test: per-residue confidence,
0–100. A statement about the model's certainty, not about correctness. One design
here carried pLDDT **90.5** on a loop moving **4.31 Å** between seeds.

**PTX vs [SASS](03-the-toolchain.md#62-sass-versus-ptx--the-mechanism-you-need)** — SASS is machine code compiled for one specific GPU
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

**[ANARCII](03-the-toolchain.md#45-anarcii-208--imgt-numbering-and-the-antigen-it-numbered-as-an-antibody)** — antibody numbering tool, 2.0.8. Will number PD-1 as an antibody
given the chance.

**[Band / banding](06-allocation-and-selection.md#4-banding-what-a-step-function-costs-and-what-changes-when-you-relabel-it)** — the rubric maps each raw metric onto a 0–10 sub-score through three
ranges (Poor / Medium / Good) rather than continuously. Banding is a **step function**,
so it does not average noise away — it **concentrates it at the band edges**, where a
movement of 0.0005 can cost 2 composite points. Relabelling the bands is *monotone but
not affine*, and therefore **does** change rankings: 39 strict reversals on the
252-design grid.

**CAPRI quality bands** — the community standard for calling a predicted complex
Incorrect / Acceptable / Medium / High, by [DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong) thresholds
**0.23** (Acceptable), **0.49** (Medium), **0.80** (High). Every DockQ verdict in this
course is a CAPRI band, and *which* threshold you quote changes the error rate you
report.

**[Composite](02-the-engineering-problem.md#32-the-composite-formula)** — the headline 0–100 score, a weighted mean of the eight metrics'
banded sub-scores: `[0.60 × binding + 0.20 × developability + 0.20 × novelty] × 10`.
Challenge 1 ships **94.0**, Challenge 2 **93.6**. Contrast the
**[surrogate](06-allocation-and-selection.md#43-the-surrogate-reorders-under-a-change-of-anchors)**, which is the same thing with the steps
replaced by interpolation.

**Contacts** — count of heavy-atom pairs across the interface within a distance
cutoff. Measured [ICC](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants) here: **0.003**. Pure sampler noise.

**ΔG (binding free energy)** — the predicted free energy of complex formation in
kcal/mol, here from [PRODIGY](03-the-toolchain.md#42-prodigy-240--δg-and-contacts). More negative is tighter.
One of the eight scored metrics, and one of the four that
[reject 0 of 6 known-wrong antibodies](05-experiment-design.md#43-the-negative-control-panel-what-a-known-wrong-input-does-to-your-gates)
— it is satisfied by any two proteins the predictor places in contact.

**[Gate / viability cutoff](02-the-engineering-problem.md#31-the-eight-metrics)** — a hard threshold a design must clear to count as viable
at all, as opposed to the [band](06-allocation-and-selection.md#4-banding-what-a-step-function-costs-and-what-changes-when-you-relabel-it) that decides how many points it earns. Failing
any one gate ranks a design below every viable design. There are five; after the
construct correction, **four of them reject 0 of 6** known-wrong antibodies, so in
practice the gate set rests on [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae) alone.

**Contacts** — count of heavy-atom pairs across the interface within a distance
cutoff. Measured [ICC](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants) here: **0.003**. Pure sampler noise.

**[CDR SASA](03-the-toolchain.md#47-gemmi-freesasa-and-the-interface-definition)** — solvent-accessible surface area of the CDR loops, in Å². Measured
ICC: **0.000**.

**[DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong)** — a 0–1 measure of how close a predicted complex is to a reference
structure, with CAPRI quality bands. Version 2.1.3. **At its defaults it refuses
to score a redesigned antibody**, exiting 1 with no output; it needs
`--allowed_mismatches` and a pinned chain mapping. Note also that DockQ requires
a reference, so it does not exist for a de novo target.

**[ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae)** — an interface score computed from the PAE matrix with a 10 Å cutoff.
The only gate in this rubric that actually rejects anything. Locates its pLDDT
input by **string-substituting the PAE filename**, so renaming a file makes it
write an empty table and exit 0.

**[Interface pLDDT](03-the-toolchain.md#47-gemmi-freesasa-and-the-interface-definition)** — mean pLDDT over interface residues. One of only two metrics
shown to respond to the epitope (64.0× its seed standard deviation under
knockout).

**[NetSolP](03-the-toolchain.md#44-netsolp-10--sequence-only-solubility-and-a-positive-control-that-chose-the-model)** — a sequence-only solubility predictor. Ships **three** model
variants scoring a licensed antibody at 0.379 / 0.463 / 0.733 against a 0.50
cutoff. Aggregated here as `min(VH, VL)`.
*(⚠️ That triple is corrected by [C5](CORRECTIONS.md) — it mixes VH and VL across three
variants and two constructs. Per chain, on Fv: VH 0.733 / 0.569, 0.637 / 0.463, 0.379 /
0.346.)*

**[PRODIGY](03-the-toolchain.md#42-prodigy-240--δg-and-contacts)** — predicts binding free energy ΔG in kcal/mol from a structure. It is
a **contact-count regression over an unminimised predicted pose**, with no
solvation term. Shown here to be **blind to the epitope** (0.9× its own seed sd
against a 527-contact deletion) while carrying the largest share of the ranking
variance.

**[RF2](03-the-toolchain.md#23-rosettafold2--a-filter-not-a-scorer)** — RoseTTAFold2, used as a cheap filter. Its poses sit **24.9 Å** from the
designed pose.

**[Surrogate](06-allocation-and-selection.md#43-the-surrogate-reorders-under-a-change-of-anchors)** — a continuous stand-in for the banded
[composite](02-the-engineering-problem.md#32-the-composite-formula), used for *ranking* because the banded score
collapses 40 designs onto three distinct values. It interpolates between band anchors —
and because it does, **changing the anchors reorders the shortlist**: the winner fell
from 1st to 4th, with 18 of 20 ranks changing.

**uv** — the Python package manager used throughout. `uv tool install` gives each
tool its own environment plus a CLI shim, which is how the [numpy 2.0](03-the-toolchain.md#5-the-numpy-20-fault-line-and-isolation-as-architecture) conflict was
resolved.

---

## 4. Statistics and method

**[Ablation](05-experiment-design.md#41-the-epitope-knockout-a-matched-control-plus-a-doseresponse)** — deliberately removing part of a design to see whether a metric
notices. Here, removing 158 antigen contacts cost 0.030 DockQ and *gained* four
contacts, because the predictor simply re-docked and rebuilt an interface.

**Argmax by construction** — see *diffusion samples*. When a generator returns
ranked output and you take the first, you have an order statistic, not a sample.

**[Attenuation](04-measurement-theory.md#4-attenuation-why-correlations-between-noisy-things-look-weak)** — the shrinking of an observed correlation by measurement noise:
`ρ_obs ≈ ρ_true · √(r₁r₂)`, equation (4.8). With [reliability](04-measurement-theory.md#13-reliability) 0.75 on each side, a true 0.80
presents as 0.60. Never report a corrected value as observed. The inverse operation is
**disattenuation**, `ρ_true = ρ_obs / √(r₁r₂)` — applied in
[the critique](09-critique.md) and never to be reported as if it were measured.

**Detectable effect** — the smallest effect an experiment could have found at its
sample size. **A null is only meaningful as "no effect larger than x."** **At least
seven** claims here were published as findings of absence and reversed; this entry read
"Four" until 2026-10-05, see
[C7](CORRECTIONS.md#c7--the-course-undercounts-its-own-most-repeated-error-and-the-newest-instance-bought-something).
State the bound in the units the decision is taken in — ρ persuades nobody.

**Effect size (Cohen's d)** — a standardised mean difference.

**[Equal-budget null](05-experiment-design.md#6-equal-budget-resampling-and-varying-the-outcome)** — the correct null for a filter: the same filter applied at
random, retaining the same number of items. A random subset retaining fraction f
keeps the maximum with probability exactly f, and one of the top five with ~97%
at f = 0.5 — so "our filter kept the best design" proves nothing.

**Estimand** — *what a number is a number of.* Not its value and not its precision:
the quantity it estimates — "single seed", "7-seed mean", "pool mean", "median of five
diffusion samples". Most of this course's withdrawn claims are estimand errors rather
than arithmetic errors, including the
[0.629 that "did not reproduce"](04-measurement-theory.md#6-the-0629-that-does-not-reproduce-an-estimand-mismatch-and-a-residual-inconsistency)
— it reproduced perfectly, as a different estimand. One of the four fields every number
is supposed to carry.

**[Fisher-z](05-experiment-design.md#11-the-fisher-z-machinery)** — a transformation making correlation standard errors tractable:
`SE = 1/√(n−3)`. At n = 14 that is 0.30, so a measured ρ of 0.47 carries a 95% CI
of **[−0.14, +0.82]**.

**[Goodhart's law](09-critique.md#goodhart)** — when a measure becomes a target it stops being a good
measure. The organising anxiety of this project.

**[ICC (intraclass correlation)](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants)** — reliability estimated from k replicate
measurements of the same item. ICC ≈ 0 means the metric is **pure sampler
noise**; it carries no information about the item at all.

**[Mutation testing](02-the-engineering-problem.md#113-mutation-testing)** — deliberately reintroducing bugs to check your test suite
detects them. *A green suite is a claim about the code; a suite shown to go red
on reintroduced defects is evidence about the suite.*

**[Optional stopping](05-experiment-design.md#7-optional-stopping)** — looking at data, then collecting more, then testing at
nominal α. Inflates the type-I error rate; the reported p is not the real one.
The conditioning result here (d = 1.47, p = 0.0016) was affected and was replaced
with a deterministic per-item null.

**[Order statistic](06-allocation-and-selection.md#5-order-statistics-when-your-prediction-is-silently-a-maximum)** — a value selected by *rank* rather than drawn at random: the
maximum, the median, the 3rd largest. A predictor that returns its outputs ranked hands
you one of these, not a sample — so `model_0` at `diffusion_samples=1` is an **argmax by
construction**, and reporting it as "the prediction" reports the top of a distribution
never sampled.

**[Partial correlation](05-experiment-design.md#3-partial-correlation-and-a-result-that-half-reversed)** — the correlation between X and Y with Z held constant.
Used here to adjudicate whether a 3-fold ensemble measurement carried information
a free sequence feature did not. The answer half-reversed at larger n.

**[Power](05-experiment-design.md#1-sampling-error-and-the-detectable-effect-standard)** — the probability that an experiment detects an effect *that is really
there*. The companion of the **detectable effect**: quoting a null without its power is
quoting an instrument's silence as the world's. This project's most repeated error,
**at least seven times**; the sharpest instance ran at **23% power** and closed a
144-fold experiment. State power in the units the decision is taken in, never in ρ.

**[Pre-registration](05-experiment-design.md#8-pre-registration-and-the-rarer-virtue)** — writing down the hypothesis, analysis and failure
condition *before* seeing the data. Eleven documents here; at least three fired
against the author's interest.

**[Range restriction](04-measurement-theory.md#5-range-restriction--and-the-insight-that-selection-is-the-restricting-operation)** — reliability is a *ratio* of true variance to total
variance, so narrowing the range of items destroys it even with unchanged noise.
The crucial corollary: **shortlisting is itself the range-restricting
operation**, so reliability measured on a wide pool never applies to the
selection stage.

**[Reliability](04-measurement-theory.md#13-reliability)** — `r = var_true / var_observed`. How much of what you measured is
signal. Distinct from **validity**, which asks whether the signal is the thing you
care about. The central confusion this project ran on for six days.

**[Spearman–Brown](04-measurement-theory.md#3-spearmanbrown-what-averaging-buys)** — how reliability improves with k replicates:
`r_k = k·r₁ / (1 + (k−1)·r₁)`.

**[Validity](09-critique.md#21-precision-before-validity)** — whether a metric measures what it claims to. A metric can be
perfectly reliable and completely invalid. See *reliability*.

**[Winner's curse](06-allocation-and-selection.md#3-winners-curse)** — the top-scoring candidate from a noisy pool is
disproportionately one whose noise landed high, so its score is biased upward.
Correction: `corrected = pool_mean + reliability × (observed − pool_mean)`. Note
that a **larger pool makes the correction larger, not smaller**, and that a single
fresh measurement can never validate the correction however closely it lands.

---

## 5. Engineering and process

*Added 2026-10-05, with [chapter 12](12-the-audit.md). These are the project's own
working vocabulary — a newcomer could not previously look any of them up.*

**[Generator](03-the-toolchain.md#2-generators)** — **three unrelated senses, and the course uses all three.**
(1) A *model* that produces structures — [RFdiffusion](03-the-toolchain.md#22-rfdiffusion-via-rfantibody),
[ProteinMPNN](03-the-toolchain.md#21-proteinmpnn). (2) A *script that writes a document*, which is the
sense in which [a packaged file is owned by its generator](12-the-audit.md#2-a-document-is-owned-by-whatever-writes-it)
and hand-editing it is undone by the next build. (3) A *generating mechanism* for a class
of error, as in [chapter 08's frequency analysis](08-what-broke.md#frequency-analysis-where-the-systematic-weakness-was).
Context disambiguates; nothing else does.

**[Guard](12-the-audit.md#4-guards-that-could-not-see-their-own-corpus)** — any automated check whose job is to **fail**. The project's organising
belief is that a lesson written in prose cannot fail a build, so lessons get promoted
into guards. The corollary is the trap: **a guard that cannot fail is not evidence**, and
the usual reason it cannot fail is that its required set was assembled from convenient
checks rather than from what the job needs. Five were found blind in a single session.

**[Orphaned artefact](12-the-audit.md#23-the-orphaned-artefact--worse-because-nothing-ever-looks-wrong)** — a file left behind when generator `A` writes `{w,x,y,z}` and
generator `B` writes only `{w,x,y}`. Nothing updates `z` again, and **no per-file check
can see it**: it exists, parses, is internally consistent, and its numbers were all true
once. Detected by a modification-time spread inside one directory, or by recomputing from
declared inputs. *A partial writer is more dangerous than a broken one.*

**[Silent failure / exit 0](02-the-engineering-problem.md#9-the-recurring-failure-mode-programs-that-exit-0-having-done-the-wrong-thing)** — a program that completes successfully having done the wrong
thing. The dangerous failure is never the crash; it is the number in the right range,
with the right units, computed on the wrong thing. This project catalogued **26**
([the full catalogue](08-what-broke.md#class-1--silent-failures)). *A build that dies is
cheaper than a build that lies.*

---

## Cross-references

Definitions here are expanded where they are used:
[biology](01-the-biological-problem.md),
[the rubric and the pipeline](02-the-engineering-problem.md),
[tool versions and gotchas](03-the-toolchain.md),
[reliability](04-measurement-theory.md),
[nulls and controls](05-experiment-design.md),
[allocation, banding and the winner's curse](06-allocation-and-selection.md).
