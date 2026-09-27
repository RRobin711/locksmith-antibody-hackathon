---
date: 2026-09-26
tags: [project, protein-design, antibody, locksmith-bio, learning, index]
status: living
---

# Designing a cancer drug on a laptop

*Computational antibody design against PD-1 — and everything that went wrong on the way.*

**Status:** two designs, packaged and validated, scoring 94.0 and 93.6. A scoring harness
that was built before the designs and then used to show the scoring system itself is weak.
A register of twenty claims this project withdrew. No wet lab, and no claim that needs one.

> This is the narrative version. For the numbers and how to run it, see
> [the README](README.md); for the current state, [`STATE.md`](STATE.md).

---

## The goal

Design an antibody that binds **PD-1**, and show it would plausibly work — with no
laboratory.

Your T cells can already kill cancer. Tumours survive by switching them off, pressing an
"off switch" called PD-1 on the T cell's surface. A drug that blocks that contact leaves
the brake unapplied. That is **checkpoint blockade**, and the drug that does it best —
Keytruda (pembrolizumab) — earns over $25bn a year. So: a real problem, a validated
target, and a known-good answer to measure against.

The task comes from a hackathon run by **Locksmith Bio** and **IBAB EC**. Its deadline
(14 December 2025) had already passed when this work started, so nothing here was entered
into anything. The brief was used because it is *specific* — eight named metrics, eight
hard cutoffs, an exact scoring formula — and a specific brief is a far better teacher than
an open-ended one.

## The two problems

**Challenge 1 — remix Keytruda.** Take pembrolizumab, redesign the loops that touch PD-1,
keep the binding, make the sequence novel. There is a safety net: the real answer exists,
so you can measure how far you drifted.

**Challenge 2 — invent the future.** Design a complete antibody against PD-1 from nothing.
No safety net: no reference structure exists, so nothing external can tell you if you are
right.

## The strategy, in one idea

**Build the judge before the contestant.**

Six of the eight scored metrics are computed from files *the entrant generates*. The
organisers do not re-fold anyone's design. So a high score is partly a statement about how
confident your structure predictor is in itself — and a confidently wrong pose scores
exactly like a correct one.

That makes the first deliverable not a design but an evaluator, and the first test of the
evaluator is whether it scores **pembrolizumab itself** correctly: passing every binding
gate and correctly *failing* the novelty gate, because it is the molecule you are not
allowed to copy. It does.

## What broke

The most valuable part, and the reason this repo is worth reading.

**The silent failures.** Not one of them raised an exception; each produced a confident
wrong number. A structure format where experimental and predicted files store different
quantities in the same field. A tool numbering the *target* as an antibody because they
share an evolutionary fold. A folding model exiting **successfully** after failing, twice.
A comparison tool whose defaults refuse to score any redesigned antibody — exit 1, no
output — which would have scored a viable design as zero.
→ [All of them, with cause, catch, fix and principle](knowledge/Eight%20Silent%20Failures.md)

**The worst one took nine days to find.** The folding model compares an alignment's length
against the input chain and, on mismatch, **throws the alignment away and folds the
sequence alone** — announcing it only on a text stream the harness was discarding. Every
Challenge 2 number the project produced was measured in that condition. Fixing it did not
add noise to the ranking; it very nearly **inverted** it. The design that came out on top
had previously ranked 29th of 30, and the one already packaged for submission fell from
first to last.
→ [The 2×2 that isolates it](results/msa_silently_discarded.md)

**And a self-inflicted one.** Challenge 1 scored 96.0 for nine days because the code read
the comparison tool's *printed* summary, which rounds to three decimals. The true value is
0.7995794972281312 — **0.00042** below a threshold at 0.80. Two points came from a
`printf`. A project whose whole argument is that the rubric is gameable cannot keep them,
so the score is now 94.0.

**The one lesson I'd keep:**

> A tool that refuses to produce output is the *good* failure. The dangerous ones hand you
> a number anyway — right range, right units, computed on the wrong thing.

## What the judge found when pointed at the rubric

This is the result I did not expect and the one worth an outsider's time.

**HyHEL-10 is an antibody raised against hen egg lysozyme.** It has no business binding
PD-1. Run through this pipeline against PD-1, it **clears all five of the hackathon's hard
cutoffs on `model_0`** — and `model_0` is what the rubric gets by default, because the
folding tool returns five candidate structures ranked by its own confidence and keeps one
unless told otherwise. **On the median of those five it fails**, at 0.219 against a 0.60
cutoff, versus 0.609 for the single draw. So the finding is not "this molecule passes"; it
is *a rubric evaluated at its own default setting accepts an anti-lysozyme antibody as a
PD-1 binder*, and that is the criticism, because it is what a grader following the
instructions would actually compute.

Separately, and measured on the **median** rather than the best draw: across six
deliberately wrong antibodies, four of the five gates reject **none of them**.

The reason is mechanical and general: ΔG, contact count, interface confidence and buried
surface area all measure *that a complex was built*, not that it is the right complex. Give
a structure predictor two proteins and it will place them against each other. Only one of
the five gates carries real information, and even that one puts a wrong antibody within
0.006 of passing.

Underneath it sits a second trap. The predictor returns five candidate structures **ranked
by its own confidence**, and the default is to keep one. So the number everybody reports is
an **argmax, not a sample**. HyHEL-10's *median* across five draws is 0.219 — it fails
easily. Its best draw is 0.609 — it passes. Same molecule, same run.
→ [The negative control](results/negative_control.md)

## Where we got to

**Challenge 1:** `mpnn_T0.5_s104_036` with a deamidation fix, **94.0/100**, viable. Chosen
from 239 designs across four sampling temperatures — every one of them folded rather than
filtered, deliberately, so that every filter and threshold stays evaluable offline without
the circularity of testing a filter on the run that used it.

**Challenge 2:** `bb_8_0`, **93.6/100**, viable on all five diffusion samples. From 144
folds over 18 backbones conditioned on the epitope that PD-L1 itself uses.

Three things the campaigns taught that outlast them:

- **A cheap filter has to beat the same filter applied at random**, at equal budget. The
  aromatic screen does, on mean quality, p<0.0001 — and it is still refuted as a design
  rule, because it only wins on outcomes that are properties of the *predictor* rather
  than of the interface, and on the one chemically meaningful outcome it runs backwards.
  *When a result survives a good null but contradicts a strong prior, vary the outcome,
  not the test.*
- **The winner's curse is real and correctable.** The best-looking design is best-looking
  partly by luck; shrink its score by the measurement's reliability. The correction is
  worth applying on theory — and the single fresh measurement that appeared to confirm it
  **cannot** confirm it, because one fold's standard error is three times the size of the
  effect. Discriminating it properly needs about 73 more folds.
- **More candidates or more precision?** Simulating the whole procedure — shortlist,
  re-measure, take the best — shows depth beats breadth *once the budget is large enough*,
  and not before. An earlier, stronger version of this claim appeared in my own notes and
  was **false against the very table it was drawn from**. Read the table you are
  summarising.

## Being wrong on the record

Twenty claims were withdrawn, refuted or superseded over this project, and five figures
are flagged as not reproducing. They are all
[enumerated in one place](results/retractions.md), with what replaced them.

That file exists because of a smaller failure: for three sessions the project carried a
note saying "five stale retractions are outstanding" without anyone ever writing the list.
A known-issues list that exists only as a count is not a list — there is nothing to check
off, so it survives indefinitely at no cost to whoever carries it. When finally
enumerated, the count was twenty.

## What's next

The controls that need a GPU and have not been run: a decoy-patch control that could
falsify the epitope-conditioning result, and sequencing the 18 unconditioned backbones.
Neither changes a design; both would change how much the evidence supports.
Full list in [`STATE.md`](STATE.md) §6–7.

## Working documents

[The delivery plan, including a review of its own weaknesses](PLAN.md) ·
[Code skeleton](BUILD.md) ·
[Session logs](docs/sessions/README.md) ·
[Knowledge notes](knowledge/README.md) ·
[The 12-chapter course](docs/lecture/README.md)
