---
date: 2026-09-23
tags: [project, lecture, learning, index, protein-design, antibody]
status: review
---

# Chapter 00 — Orientation: the four questions, answered

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1, C2 and C3](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding, and **C3 applies to Challenge 1**: its composite is **94.0**, not the 96.0 this course derives in several places. Challenge 1 is unaffected *by the alignment defect*, which is narrower than "unaffected".

## What this chapter teaches

This chapter answers four questions about the Locksmith antibody-design campaign
directly and without teaching apparatus, so you know what you are about to study
before you study it:

1. **What did we have to do?** — the medical question and the programming question
2. **What did we need to know?** — technical knowledge, and the industry knowledge no tutorial states
3. **What did we use?** — tools, methods, lines of reasoning, mathematics
4. **What did we make?** — code, tests, artefacts, documents, results

Everything here is expanded elsewhere in the course. Treat this as the map. Every
number is exact and traceable; where a figure was later corrected, both values
appear, because the corrections are the most instructive part of the record.

One framing note before starting. This was a nine-day solo campaign, 2026-09-14
to 2026-09-22, for a hackathon run by Locksmith Bio that **was never submitted
to** — it was done to learn the field properly. That changes how you should read
every score in this course. The goal was never to win; it was to find out what
the numbers mean. As it turned out, the most valuable results are the ones
showing that the numbers mean less than they appear to.

---

## 1. What did we have to do?

### 1.1 The medical question

Your T cells can already kill cancer. Tumours survive by switching them off,
pressing an inhibitory receptor on the T-cell surface called **PD-1**
(programmed cell death protein 1). A tumour cell displaying **PD-L1**, PD-1's
natural ligand, engages that receptor and applies the brake. Block the contact
and the brake is never applied — this is **checkpoint blockade**, and the
antibody that does it best, pembrolizumab (Keytruda), earns over $25bn a year.

So the target is real, clinically validated, and comes with a known-good answer
to measure against. That last property is what makes it a good teaching problem:
you can check your machinery against a molecule whose behaviour is already known.

The brief had two parts.

**Challenge 1 — redesign.** Take pembrolizumab's structure, rewrite the loops
that do the binding, keep it binding, but make it genuinely new. This is editing
a known good answer. The backbone geometry that makes binding work is given to
you; you are changing the sequence that decorates it.

**Challenge 2 — de novo.** No template. Design an anti-PD-1 antibody from
nothing. This is *proposing* an answer rather than editing one, and it may simply
not work.

The gap between these is not one of degree. In Challenge 1 the binding geometry
is guaranteed by the native backbone, which is why — as the project discovered —
**20 of 20** baseline designs at default settings cleared all eight quality
gates. The gates do not bite when the answer is handed to you. In Challenge 2
nothing is guaranteed, and **1 of 30** designs cleared.

### 1.2 What a design has to achieve to be a drug

Binding is necessary and nowhere near sufficient. A real therapeutic antibody
must also be **specific** (it must not bind other human proteins), **developable**
(soluble, stable, expressible, free of chemical liabilities that degrade in a
vial), **manufacturable**, and **non-immunogenic**. The project measured the
first two and found problems in both: its named Challenge 1 design turned out to
be cross-reactive against [TIM-3](01-the-biological-problem.md#64-tim-3-cross-reactivity--a-specificity-failure), and both designs carried chemical liabilities in
the binding site itself.

### 1.3 The programming question

Stated as an engineering brief: *given a scoring rubric and two design
challenges, build a system that generates candidate molecules, predicts their
three-dimensional structures, scores those structures against eight metrics,
selects the best, and packages it so an external evaluator can reproduce every
number from the delivered files alone.*

That is a five-stage pipeline — **generate → fold → score → select → package** —
and each stage has a contract the next one depends on.

The structural difficulty is subtler than the pipeline suggests, and it is the
reason this project is worth studying. You are generating thousands of candidates
and picking the best, so **the scoring decides everything**. And if the scoring
is subtly wrong, *nothing visible happens*. No exception is raised. A number in
the right range with the right units comes back, computed on the wrong thing.

Worse, for a molecule that has never been synthesised there is **no ground truth
at all**. Most of the score is computed from files the pipeline generates itself:
a predicted structure, and the predictor's own confidence in that prediction.
Nobody checks them against reality, because there is no reality to check them
against. A confidently wrong answer therefore scores well.

This is why the project's governing strategy was **build the judge before the
contestant** — construct and validate the scoring system first, against molecules
whose answers are already known, including a deliberate fake that must fail.

---

## 2. What did we need to know?

### 2.1 Formal technical knowledge

**Structural biology.** Protein structure; the PDB file format and the fact that
`SEQRES` records and coordinate records disagree whenever a loop is unresolved in
the crystal; that predicted structures reuse the [B-factor](03-the-toolchain.md#47-gemmi-freesasa-and-the-interface-definition) column to store a
confidence score, so the same field means different things in two files with the
same extension; residue numbering schemes, and that [IMGT versus Kabat](01-the-biological-problem.md#24-numbering-schemes-and-why-the-novelty-gate-depends-on-one) changes the
CDR-H3 identity **denominator from 11 to 13** — so a novelty gate's value depends
on a scheme choice nobody thinks to record.

**Antibody architecture.** Heavy and light chains; variable versus constant
domains; Fv versus Fab versus full IgG; the six complementarity-determining
regions (CDRs) that form the binding surface; why [CDR-H3 dominates](01-the-biological-problem.md#23-why-cdr-h3-dominates--and-the-reason-is-genetic-not-structural), being the
only loop built by V(D)J recombination with junctional diversity.

**Machine learning for structure.** What a folding model does; multiple sequence
alignments and co-evolution, and the counter-intuitive fact that **antibody
chains want no alignment** because their diversity is somatic rather than
evolutionary; pLDDT, PAE, ipTM and [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae), and that these are not interchangeable;
`recycling_steps` and `diffusion_samples` as first-class scientific parameters
rather than defaults; training cutoffs, and that [Boltz-2](03-the-toolchain.md#31-boltz-2--the-primary-predictor)'s is **2023-06-01 on PDB
release date** — release, not deposition, and read from the paper rather than a
summary.

**Statistics.** This is the deepest requirement and the one that separates a
working pipeline from a trustworthy one. Reliability and the intraclass
correlation; [attenuation](04-measurement-theory.md#4-attenuation-why-correlations-between-noisy-things-look-weak); [range restriction](04-measurement-theory.md#5-range-restriction--and-the-insight-that-selection-is-the-restricting-operation); [Spearman–Brown](04-measurement-theory.md#3-spearmanbrown-what-averaging-buys); [partial correlation](05-experiment-design.md#3-partial-correlation-and-a-result-that-half-reversed);
resampling nulls; statistical power and the [detectable-effect standard](05-experiment-design.md#1-sampling-error-and-the-detectable-effect-standard); order
statistics; the [winner's curse](06-allocation-and-selection.md#3-winners-curse). Three chapters of this course are devoted to it.

**Software engineering and systems.** Isolated Python environments; subprocess
orchestration; multiprocessing start methods; GPU architecture compatibility,
including the distinction between [SASS](03-the-toolchain.md#62-sass-versus-ptx--the-mechanism-you-need) (compiled for one chip) and PTX
(intermediate code the driver can just-in-time compile for a newer chip);
determinism; testing.

### 2.2 The tacit knowledge — the part no tutorial contains

This is the more valuable category, and the project's successes and failures both
turn on it.

- **Validate a scoring harness against known answers before using it, including a
  negative control that must fail.** Without this you cannot distinguish "my
  designs are good" from "my gates do not bite."
- **A confidence metric is not a truth metric.** The predictor's certainty is a
  statement about the predictor.
- **Tool defaults are frequently wrong for your case.** [NetSolP](03-the-toolchain.md#44-netsolp-10--sequence-only-solubility-and-a-positive-control-that-chose-the-model) ships three model
  variants that score a licensed antibody at 0.379, 0.463 and 0.733 against a
  0.50 cutoff — a spread wider than the distance from cutoff to "good". The CLI
  default would have failed every design and looked exactly like a design
  problem. Separately, [DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong) at its defaults **refuses to score the submission at
  all**, exiting 1 with no output.
- **Full-chain identity is a useless novelty screen for antibodies.** Framework
  conservation puts every antibody at 86–94% identity to something. You must
  screen on CDR-H3, which spread the same candidates over 21–70%.
- **Prescribed developability fixes are not interchangeable.** The single best
  finding in the project, covered in §4.4 below.
- **Know what a rubric rewards versus what a drug needs**, and keep the gap in
  view rather than closing your eyes to it.

### 2.3 What not knowing cost

Roughly half of day one went to environment problems. A construct mismatch meant
the molecule folded was not the molecule submitted. Four separate statistical
nulls were published and later reversed because nobody stated the effect
detectable at the sample size in hand. A GPU sat idle for 4 h 22 m across three
instances of a bug that had already been written down.

---

## 3. What did we use?

### 3.1 Tools

| role                 | tool                         | note                                                            |
| -------------------- | ---------------------------- | --------------------------------------------------------------- |
| sequence design      | ProteinMPNN (`8907e66`)      | cannot vary loop length — a hard constraint on the design space |
| backbone generation  | RFdiffusion / RFantibody     | hotspot conditioning; would not run on the local GPU            |
| structure prediction | Boltz-2 **2.2.1**            | the workhorse; every headline number comes from it              |
| structure prediction | ColabFold / AlphaFold2 1.6.3 | qualified and dropped — cannot fold designs without an MSA      |
| filter               | RF2                          | sits 24.9 Å from the designed pose                              |
| pose quality         | DockQ 2.1.3                  | needs non-default flags or it refuses to run                    |
| binding energy       | PRODIGY 2.4.0                | later shown blind to the epitope                                |
| interface confidence | ipSAE (`6174cf9`)            | the only gate that actually rejects anything                    |
| solubility           | NetSolP (ESM1b ensemble)     | variant chosen by positive control, not by default              |
| numbering            | ANARCII 2.0.8                | numbers PD-1 *as an antibody* — shared IgV fold                 |

Hardware: a laptop RTX 5070 Ti (Blackwell, `sm_120`) for everything Boltz, plus
one rented RTX 3090 at **$2.82 for 5.5 hours** for the backbone generation the
laptop could not run.

### 3.2 Methods and lines of reasoning

Pre-registration (11 documents). Positive and negative controls. Equal-budget
random-subset nulls. Geometry-matched nulls drawn as contiguous surface patches.
Composition-matched sequence scrambles. Epitope knockout with a matched
off-interface control and a dose–response. Ablation. Post-training-cutoff
generalisation testing. Adversarial multi-judge audits. Mutation testing of the
test suite itself. Re-derivation of every published number from raw data.

### 3.3 Mathematics``

The intellectual core. Reliability as a variance ratio and the intraclass
correlation; Spearman–Brown for the [reliability](04-measurement-theory.md#13-reliability) of a k-replicate mean;
attenuation of correlations by unreliability; range restriction, and the
realisation that **shortlisting is itself the range-restricting operation**;
Fisher-z standard errors and the detectable-effect standard for nulls; partial
correlation; resampling; optimal allocation of a noisy measurement budget,
including the fact that the error of a *mean* falls as `1/√k` while the error of
a *spread* falls as `1/√(2(k−1))`, so the same budget inverts when the target
quantity changes; the winner's-curse shrinkage estimator; and the difference
between a monotone and an affine relabelling, which turns out to decide whether a
scoring convention can reorder your candidates.

---

## 4. What did we make?

### 4.1 Code

**18,020 lines of Python**, plus 442 of shell:

| component | lines | what it is |
|---|---|---|
| `src/locksmith/` | 3,407 | the reusable package: config, folding, 10 metric modules, selection, packaging, validation |
| `scripts/` | 14,095 | 86 numbered Python scripts plus 5 shell, one per unit of work, `00_doctor.py` through `93_epitope_coverage.py` |
| `tests/` | 518 | 30 test cases, all written on the final day |

The most interesting structural fact about this codebase: **roughly 53% of it
exists to check the other half.** That ratio is the project's thesis expressed as
an artefact rather than an argument.

### 4.2 Tests and configuration

`tests/test_invariants.py` collects 30 cases, selected by an explicit rule —
*an invariant whose violation is invisible*. The suite was itself
mutation-tested: five bugs reintroduced, five localised failures, green restored
after each. `config/metrics.yaml` encodes the rubric as data, including five
conventions the handbook never specified, deliberately expressed as **switches
rather than constants** so that resolving one costs a re-score rather than a
re-fold.

### 4.3 Results and documents

1,274 predicted structures across 42 run directories (3.6 GB). 62 results
write-ups including 11 pre-registrations and 3 adversarial audits. 23 session
documents. 14 knowledge notes. **165,333 words** of documentation in total, a
1.04 : 1 ratio against Python.

### 4.4 Scientific findings

The designs:

| | design | shipped score | status |
|---|---|---|---|
| Challenge 1 | `mpnn_T0.5_s104_036` + N55Q | **94.0** | viable; CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to pembrolizumab |
| Challenge 2 | **`bb_8_0`** | **93.6** | viable on 5/5 diffusion samples |

> **Updated 2026-09-26** — was `96.0` and `bb_2_0_dldesign_1` at `91.2`; see
> [C1 and C3](CORRECTIONS.md).

Challenge 2 ships **4.8 points below** its unfixed score on purpose, to remove
two [glycosylation sequons](01-the-biological-problem.md#61-two-n-glycosylation-sequons-in-the-challenge-2-paratope) from the binding site.

**The best result in the project** is a chemistry finding. Handbook §9 prescribes
`N→Q` or `S→A` as interchangeable fixes for a glycosylation sequon. They are not.
The asparagine acceptors carried **10 and 19** heavy-atom contacts to the
antigen; the serines carried **zero**. Measured over five diffusion samples each,
`N→Q` collapsed ipSAE from **0.864 to 0.014** — reproducible to ±0.001 — while
`S→A` stayed viable 5 of 5. That is a sixty-fold difference between two fixes
listed on the same line, and *the contact table predicted it before any structure
was folded*. Confirmed in the opposite direction the same day: Challenge 1's
`N55Q`, on an acceptor carrying only 3 contacts, was free (0.822 → 0.821).

> "Conservative substitution" is a claim about chemistry, not about a particular
> interface.

### 4.5 The findings that matter more than the scores

The project's real output is a set of bounded negative results about its own
measurement stack:

1. Four of five hard cutoffs reject **0 of 6** known-wrong antibodies (measured on
   the **median of five** diffusion draws). Viability rests on ipSAE alone.
2. **HyHEL-10, an anti-lysozyme antibody, cleared all five cutoffs as a PD-1 binder
   on `model_0`** — the argmax of five draws, and the default a grader gets. On the
   **median** it fails (ipSAE 0.219 vs 0.609). Note points 1 and 2 use *different
   estimators*; a pass rate is a property of the estimator, so neither is quotable
   without it.
3. Five of eight rubric metrics are constants across the design pool; the harness
   ranks on three; one of those three ([PRODIGY](03-the-toolchain.md#42-prodigy-240--δg-and-contacts) ΔG) is blind to the epitope while
   carrying the largest share of the ranking variance.
4. On genuinely novel antibody–antigen pairs released after the predictor's
   training cutoff, median DockQ is **0.291**, against **0.818** on the memorised
   reference complex.
5. On SKEMPI, a mutation that experimentally abolishes binding (ΔΔG **+21.8
   kcal/mol**) scores ipSAE **0.917** against the wild type's **0.903** — the
   pipeline rates a known non-binder *above* the real complex.

Neither 96.0 nor 91.2 is evidence of binding. Both are self-consistency scores.
The project says so itself, and the five results above are why.

---

## What to take away

The campaign built a working computational drug-design pipeline, produced two
scoring designs, and then — this is the part worth learning — **spent most of its
remaining effort establishing that its own scores do not mean what they appear to
mean.**

Three ideas recur, and the rest of the course is an elaboration of them:

1. **A program that runs without error is not evidence it did what you intended.**
   The dangerous failure hands you a number in the right range, computed on the
   wrong thing.
2. **Reliability is not validity.** You can measure something very precisely and
   still be measuring the wrong thing. Establish signal before buying precision.
3. **A null is only meaningful as "no effect larger than x."** Four claims in
   this project were published as findings of absence and later reversed, all
   from the same error.

Read next: [the biology](01-the-biological-problem.md) if you want the science
first, [the engineering](02-the-engineering-problem.md) if you want the system
first, or go straight to [measurement theory](04-measurement-theory.md) for the
material that transfers furthest. The unflinching version of everything above is
in [the critique](09-critique.md), and [the study plan](11-study-plan.md) tells you
how to practise it.
