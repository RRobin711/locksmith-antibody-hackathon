---
date: 2026-09-23
tags: [project, lecture, learning, index]
status: review
---

# Chapter 11 — Study plan: how to actually learn this

## What this chapter teaches

The other chapters explain the campaign. This one is about getting the material
into your head, which is a different problem. It gives a reading order, a
prerequisite curriculum for the gaps, a set of exercises whose answers are
checkable against the repository, and a longer track for rebuilding the system
yourself.

The organising principle: **you do not understand a measurement until you can
say what it would look like if it were lying to you.** Every exercise below is
built to produce that reflex, because it is the one skill this project actually
demonstrates.

---

## 1. Reading orders

Pick the one that matches why you are here.

### 1.0 The straight-through pass — "I am reading 00 to 12 in order"

*Added 2026-10-05, because this is what people actually do and the three passes below all
assume you have already decided to skip something.*

**It works.** No chapter declares a prerequisite on a later one, and
[Chapter 12](12-the-audit.md) is deliberately last: it is the only chapter written after
corrections [C1–C8](CORRECTIONS.md) and incorporates them, so reading it last turns the
corrections into a resolution rather than an interruption. **87,815 words, 13 chapters,
roughly 12–15 hours** at a careful technical pace.

Four things are not linear prose, and knowing which is which before you start saves the
frustration of reading them as though they were:

| chapter | words | what it actually is | how to take it |
|---|---|---|---|
| **03** The toolchain | 10,124 | a **reference** — versions, flags, install gotchas | **Skim or skip on the first pass.** Return when you install something. It is the one chapter that is a manual, and hitting it third is a wall. |
| **10** Glossary | 2,467 | a **lookup table** | Open it in a second tab at chapter 01 and consult it, rather than reading it at position 10. |
| **11** Study plan | 2,782 | **this file** — it tells you how to read the course | Its §1 is useless to you by the time you arrive. Its **§3 self-tests and §4 exercises are not** — that is the right moment for them. |
| **`CORRECTIONS.md`** | 6,096 | what the course got **wrong**, and the fixes | Unnumbered, so it has no place in the sequence. Read it **after chapter 02**, once you know what a composite and a gate are. Every chapter's banner points at it. |

So the practical order is:

```
00 → 01 → 02 → CORRECTIONS.md → (03, skim) → 04 → 05 → 06
   → 07 → 08 → 09 → 11 §3–§4 → 12
```

with **10** open alongside throughout.

**The load is not evenly distributed.** 00, 09, 10 and 11 are short (2.5–5k). The six long
chapters — **01, 02, 03, 07, 08, 12**, all 8–10k — are where the hours go. If you have one
evening rather than a week, read **00, 04, 05, 06, 12** and stop: that is the
field-independent spine and it needs none of the biology.

### 1.1 The nine-hour pass — "I want to understand what happened"

Read in this order, roughly one hour each:

1. [Orientation](00-orientation.md) — the four questions
2. [The campaign](07-the-campaign.md) — the nine days as narrative
3. [The biological problem](01-the-biological-problem.md)
4. [The engineering problem](02-the-engineering-problem.md)
5. [Measurement theory](04-measurement-theory.md)
6. [Experiment design](05-experiment-design.md)
7. [Allocation and selection](06-allocation-and-selection.md)
8. [What broke](08-what-broke.md)
9. [The critique](09-critique.md)
10. [The audit](12-the-audit.md) — the eleven days after the campaign

Skip [the toolchain](03-the-toolchain.md) on a first pass and return when you need
to actually install something. **Chapter 12 is the one not to skip**: the campaign
chapter stops on 2026-09-22, and most of what this course treats as established was
established after that date.

### 1.2 The transferable pass — "I do not care about antibodies"

This is the honest recommendation for most readers. The measurement theory here
is field-independent: it applies to A/B testing, model evaluation, benchmark
design, hiring, or any setting where you rank noisy candidates and pick the best.

1. [Orientation](00-orientation.md) §1.3 and §2 only
2. [Measurement theory](04-measurement-theory.md) — all of it
3. [Experiment design](05-experiment-design.md) — all of it
4. [Allocation and selection](06-allocation-and-selection.md) — all of it
5. **[The audit](12-the-audit.md) — all of it.** Chapters 04–06 are the mathematics of
   measuring well; 12 is the epistemics of *checking* well, and it stands alone. Its
   thesis — every check answers a narrower question than the one you asked, and answers
   it truthfully — is demonstrated on `grep`, on `git`, on a preflight, on a null and on
   a budget, none of which are about antibodies.
6. [The critique](09-critique.md) §2 and §6

That is five to six hours and it is where the compounding knowledge lives.

### 1.3 The practitioner pass — "I am going to build something like this"

Add [the toolchain](03-the-toolchain.md), [what broke](08-what-broke.md) and
[the audit](12-the-audit.md) §2 (documents are owned by their generators) and §4 (guards
that cannot fail) to the transferable pass, then work the Track B exercises in §4. Read
[the engineering problem](02-the-engineering-problem.md) with `config/metrics.yaml`
open beside it.

---

## 2. Prerequisite curriculum

Eight tiers, ordered by leverage. You do not need all of them, and the ordering
is deliberately not the conventional one — the statistics comes early because it
is what most people are missing and what pays back fastest.

**Tier 1 — Measurement theory (highest leverage; start here).** Classical test
theory: `observed = true + error`. Reliability as a variance ratio. The
[intraclass correlation](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants). [Spearman–Brown](04-measurement-theory.md#3-spearmanbrown-what-averaging-buys). Attenuation. Range restriction. If you
learn only one tier, learn this one; it is what
[Chapter 04](04-measurement-theory.md) teaches and it is what the project spent
five sessions discovering the hard way.

**Tier 2 — Inference and power.** Confidence intervals, the Fisher-z
transformation, statistical power, and above all the **detectable-effect
standard**: a null result is meaningless unless you state the effect you could
have detected. Partial correlation. Resampling and permutation tests.

**Tier 3 — Scientific software practice.** Version control from the first line.
Invariant testing. Mutation testing. Configuration as data. Determinism and
resumability. This tier is cheap and the project's own record shows what skipping
it costs.

**Tier 4 — Protein structure basics.** Amino acids, the peptide backbone, the PDB
format, chains, residue numbering, RMSD, solvent-accessible surface area,
interfaces. Enough to read a structure file and know what you are looking at.

**Tier 5 — Antibody architecture.** Heavy and light chains, Fv/Fab/IgG, the six
CDRs, framework regions, V(D)J recombination and why CDR-H3 is special, IMGT
numbering.

**Tier 6 — Structure prediction.** What a folding model does. MSAs and
co-evolution. pLDDT, PAE, ipTM, [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae) and what each is a statement *about*.
Recycling and diffusion sampling. Training cutoffs and memorisation.

**Tier 7 — Design tools.** [ProteinMPNN](03-the-toolchain.md#21-proteinmpnn), [RFdiffusion](03-the-toolchain.md#22-rfdiffusion-via-rfantibody), and their limits — notably
that ProteinMPNN optimises sequence recovery given a backbone, which is not the
same objective as anything you care about.

**Tier 8 — Developability.** Glycosylation sequons, [deamidation](01-the-biological-problem.md#62-the-ng-deamidation-motif-in-challenge-1s-cdr-h2) motifs,
isoelectric point, aggregation propensity, immunogenicity. Deferrable until you
have a design worth criticising.

---

## 3. Self-test questions

Answer these from memory before checking. If you cannot, reread the named
chapter. Answers are all recoverable from the repository.

**On measurement** ([Ch 04](04-measurement-theory.md))

1. A metric has an intraclass correlation of 0.003 across random seeds. What does
   that tell you about using it to rank designs, and what does it tell you about
   the *designs*?
2. Two noisy measurements each with [reliability](04-measurement-theory.md#13-reliability) 0.75 have a true correlation of
   0.80. What correlation will you observe? Why must you never report the
   corrected value as if it were observed?
3. You measure reliability 0.965 on a panel spanning a wide quality range, then
   apply it to a shortlist spanning one tenth the range, with identical noise.
   What happens, and why is this not a noise problem?
4. Why is "shortlisting destroys reliability" a statement about the *selection
   step* rather than about the measurement?

**On inference** ([Ch 05](05-experiment-design.md))

5. You measure a correlation of −0.168 with p = 0.69 at n = 8 and conclude the
   effect is absent. State precisely what is wrong with that conclusion, and what
   you should have written instead.
6. A filter improves a pool's mean quality with p < 0.0001 but does not move the
   maximum, and the p-value for the maximum *rises monotonically* with retention
   fraction. What is that pattern the signature of?
7. Your filter beats an [equal-budget](05-experiment-design.md#6-equal-budget-resampling-and-varying-the-outcome) random null on the outcome you chose. What
   should you do before believing it, and what did doing so reveal here?
8. Why is a null built from uniformly-drawn residues a strawman when testing
   whether a designed interface lands on a target epitope? What is the right null
   and what is still wrong with it?

**On allocation** ([Ch 06](06-allocation-and-selection.md))

9. The error of a mean falls as `1/√k`. What law governs the error of a *spread*,
   and why does that invert the depth-versus-breadth answer?
10. You pick the highest-scoring candidate from a noisy pool. In what direction is
    its score biased, by how much, and what is the correction?
11. Why can a single fresh measurement never validate a shrinkage correction,
    however closely it lands?
12. A monotone relabelling of a banded sub-score cannot change which of two
    designs scores higher — true or false? Justify carefully.

**On engineering** ([Ch 02](02-the-engineering-problem.md), [Ch 08](08-what-broke.md))

13. Name four distinct ways a structure-prediction run can exit with status 0
    having produced nothing usable.
14. A resume mechanism checks whether an output row exists before re-running.
    What is the failure mode, and what should it key on instead?
15. Why does merging a CUDA-using stage and a multiprocessing stage into one
    script kill every worker on Linux, and what is the one-line fix?
16. A config file and a module constant encode the same convention. The config is
    the declared source of truth. What actually happened here, and what did it
    cost?

**On the science** ([Ch 01](01-the-biological-problem.md))

17. A handbook lists `N→Q` and `S→A` as interchangeable fixes for a glycosylation
    sequon. What single free calculation tells you which one is safe, and what was
    the measured difference?
18. Why is whole-chain sequence identity useless as a novelty screen for
    antibodies, and what do you use instead?
19. An anti-lysozyme antibody passes every gate in a PD-1 binding pipeline. What
    does this establish, and what does it not?

---

## 4. Exercises

### Track A — analysis only, no GPU

Everything here runs on a laptop against files already in the repository.

**A1 — Reproduce the ICC table.** Take the multi-seed scores in `runs/` and
compute the intraclass correlation for each of the eight metrics. Confirm that
`contacts` and `cdr_sasa` are indistinguishable from zero and that five of eight
metrics are effectively constant across the pool. *This is the single highest-value
hour in the whole course, because it is the calculation that would have
redesigned the campaign had it been run on day 5 instead of day 7.*

**A2 — Build the equal-budget null.** Implement the resampling test: draw random
subsets of the same size the filter retains, and compare the filter's mean and
maximum against those distributions. Reproduce the result that the filter wins on
the mean and not the maximum. Then re-run it with each of the six scored metrics
as the outcome and reproduce the six-row table that refutes the filter.

**A3 — Verify the band-relabelling counterexample.** The composite depends only
on the multiset of the six binding bands plus two more, so there are 252 distinct
designs on the grid. Enumerate them with exact rational arithmetic and find the
ordering reversals between the midpoint and top band mappings. Confirm there are
39, and explain in one sentence why "monotone" was not sufficient.

**A4 — Settle the Spearman–Brown inconsistency.** Reconcile the 7-seed-mean
reliability of 0.629 against the single-seed figures of 0.276 and 0.296. Show
that 0.629 reproduces as `1 − 0.176²/0.290²`, then show that the two remain
mutually inconsistent, and quantify by how much. This was a real open item in the project, not a made-up exercise — **closed on 2026-09-28**, so do the work before reading [register §D2](../../results/retractions.md), which gives the answer: r₇ reproduces, the recorded single-seed 0.296 is the outlier at ≈0.20, and no script produces any of the competing figures.

**A5 — Audit a claim you choose.** Pick any numeric claim in any `results/*.md`
file. Find its provenance, its n, and its estimand. Decide whether it is stated
at the right resolution. The project's own auditors found errors at roughly one
per twenty claims; see whether you can match that rate.

**A6 — Price a null that already closed a decision.** *Added 2026-10-03; this one
actually happened, eleven days late, and it is the exercise most likely to change how
you work.* `results/depth_sweep.md` concluded "these 18 backbones are exchangeable"
from 18 backbones × 8 sequences with 12 clears, and on that basis declined a 144-fold
follow-up. The per-backbone counts are **10 zeros, 5 ones, 2 twos, one three**.

Do it in this order, and do not skip the first step:

1. **Reproduce the recorded statistics before computing anything new** — Pearson
   X² = **22.91**, p = **0.152**, beta-binomial LRT **0.696**, fitted ρ = **0.0446**,
   p = **0.202**. If your implementation does not reproduce all five to 3 dp, your power
   curve measures *your* test, not theirs. (`scripts/110_heterogeneity_power.py` exits
   non-zero if any drifts — copy that discipline.)
2. **Simulate the critical value under ρ = 0** rather than trusting χ²₁₇, since the
   expected successes per cell are `8 × 0.083 = 0.67`. You should find the asymptotic
   cutoff is *conservative* — real type-I **0.042** — and the calibrated p is **0.132**.
   Note that this does **not** change the conclusion, and work out why that matters.
3. **Compute power at the fitted ρ.** You should get **0.231**, with 80% power arriving
   only at ρ ≈ **0.24**.
4. **Restate it in decision units**: g of 18 backbones clearing at `p_good`, the rest at
   `p_bad`, pool mean held at 8.3%. Three backbones at 25% against 5% → power **0.399**.
   Write the one sentence you would have put in front of the person about to decline the
   follow-up.

*The point of step 4 is that steps 1–3 are the easy part and persuade nobody.*
See [§1.4](05-experiment-design.md#14-when-the-formula-will-not-do-simulate-the-critical-value-and-report-power-in-decision-units)
and [C7](CORRECTIONS.md#c7--the-course-undercounts-its-own-most-repeated-error-and-the-newest-instance-bought-something).
**No GPU, no folds, no money** — which is exactly why there was never an excuse for
running it after the decision instead of before.

### Track B — with compute

**B1 — The eight-fold negative control.** Fold a known-wrong antibody against
your target and score it through your gates. Eight folds. If it passes, you have
learned more than a hundred folds of ranking would have taught you.

**B2 — Vary one inherited parameter.** Pick any setting you copied from somewhere
else and run a two-level arm. Six folds. Compare against the effort you were
about to spend assuming it was fine.

**B3 — The diffusion-sample envelope.** Fold the same input with one sample and
with five. Fifty-four extra seconds. Report the range rather than the point
estimate, forever afterwards.

**B4 — The decoy-patch control.** ~~This is the experiment the project never ran
and still needs~~ — **run 2026-09-28, and it passed** ([C8](CORRECTIONS.md#c8--the-decoy-patch-control-has-been-run-and-no-arm-of-this-project-needs-a-rented-card)).
Condition backbone generation on hotspots on the *opposite face*
of the target and compare epitope coverage. It is the only design that separates
"conditioning steers the interface" from "the geometry would have gone there
anyway." ~~A few GPU-hours and a few dollars.~~ **It cost \$0 and no GPU: ~26 min/backbone
on CPU.** Do it anyway — then compare your numbers to **0.803** on the decoy face and
**0.000** on the real epitope, against an unconditioned baseline of **0/18**.

*Design the decoy before you need it.* The patch here was matched to the real epitope on
size (26 residues), RMS spread (**10.15 Å** vs **9.85 Å**), surface exposure (≥15 Å² SASA)
and zero overlap, and chosen maximally opposite (**165.9°**). An unmatched decoy tests
nothing: if it is more compact or more buried than the epitope, a difference in coverage is
a difference in geometry, not in steering.

### Track C — rebuild it

Work through [Chapter 02](02-the-engineering-problem.md) and implement the pipeline
yourself, in this order — which is deliberately *not* the order the project used:

1. Encode the rubric as data, with every unspecified convention as an explicit switch.
2. Write the five invariant tests. `git init` first.
3. Calibrate against a known-good complex and a deliberate decoy that must fail.
4. Run a twenty-design baseline.
5. **Compute the ICC and dynamic range of every metric on that baseline.**
6. Run the negative control.
7. *Only now* size a campaign.

Steps 5 and 6 are the ones the project did in the wrong place, and doing them in
the right place is the entire lesson.

---

## 5. A checklist to keep

Pin this somewhere. Every line is paid for by an incident in the record.

**Before you measure anything**
- [ ] Does this metric vary across my candidates at all? (ICC, dynamic range)
- [ ] Does it respond to the thing I care about? (knockout or ablation control)
- [ ] What does a known-wrong input score?

**Before you believe a number**
- [ ] What is its n?
- [ ] What is its estimand — single observation, k-replicate mean, pool mean?
- [ ] What effect could I have detected at this n?
- [ ] Which script and which run directory produced it?

**Before you believe a null**
- [ ] State it as "no effect larger than x." If you cannot name x, do not report it.

**Before you believe a filter or a rule**
- [ ] Does it beat the *same rule applied at random* at equal budget?
- [ ] Does it survive when I change the outcome variable?
- [ ] Does my null match the *geometry* of the thing it is a null for?

**Before you trust a parameter**
- [ ] Did it cross a task boundary? If so it is an untested hypothesis — vary it once.

**Before you trust a passing control**
- [ ] Which confound does it eliminate? What is it silent about?

**Before you ship**
- [ ] Does the validator re-derive every number from the delivered files alone?
- [ ] Does the headline lead with what I actually believe?

---

## What to take away

The project's own closing lesson is an ordering rule, and it is the thing to
practise:

> **Establish that your measurement carries signal before spending anything on
> its precision. Run the cheap falsifying experiment first, because it is the one
> that can make all the expensive work unnecessary.**

Almost everything this campaign took nine days to learn was learnable in two. The
negative control cost eight folds. The metric reliability table cost nothing at
all. The chapter that explains why they came last is [the critique](09-critique.md);
the chapters that explain why they matter are
[measurement theory](04-measurement-theory.md),
[experiment design](05-experiment-design.md) and
[allocation and selection](06-allocation-and-selection.md).
