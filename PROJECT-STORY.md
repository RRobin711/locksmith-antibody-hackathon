---
date: 2026-09-15
tags: [project, protein-design, antibody, locksmith-bio, learning, index]
status: living
---

Tags: [[Protein Design|protein design]] · [[Antibody|antibodies]] · [[Locksmith Bio|Locksmith Bio]] · [[Learning|things I'm learning]] · [[index|indexes]]

# Designing a cancer drug on a laptop

*Computational antibody design against PD-1 — and everything that went wrong on the way.*

**Status:** scoring system built and validated. One structure predicted and scored. No
antibodies designed yet.

---

## The goal

Design an antibody that binds **PD-1**, and show it would plausibly work — with no laboratory.

Your T cells can already kill cancer. Tumours survive by switching them off, pressing an
"off switch" called PD-1 on the T cell's surface. A drug that blocks that contact leaves the
brake unapplied. That is **checkpoint blockade**, and the drug that does it best — Keytruda —
earns over $25bn a year. So: a real problem, a validated target, and a known-good answer to
measure against.

The task comes from a hackathon run by **Locksmith Bio**. **We are not submitting.** The point
is to learn the field properly and build something a computational biology lab would respect —
so the quality of the reasoning matters more than a score.

→ [[knowledge/README|Start here for the science]], or read on for the arc.

## The two problems

**Challenge 1** — take Keytruda's structure, rewrite the loops that do the binding, keep it
working but make it new. Editing a known good answer.

**Challenge 2** — no template. Design one from scratch. *Proposing* an answer, and it may
simply not work.

→ [[knowledge/De Novo Design and the Two Challenges|Why the second is so much harder]]

## The strategy, in two ideas

**Build the judge before the contestant.** We generate thousands of candidates and pick the
best, so the scoring decides everything — and if the scoring is subtly wrong, *nothing visible
happens*. So we rebuilt the scoring system first and tested it on molecules whose answers we
already knew, including a deliberate fake that had to fail.

→ [[knowledge/Build the Judge Before the Contestant|Including the test that failed for the
right reason]]

**Confidence is not truth.** Most of the score comes from files we generate ourselves — our
predicted structure, our own confidence in it. Nobody checks them against reality, because for
a molecule that has never been made there *is* no reality to check. So a confidently wrong
answer scores well, and anyone willing to hill-climb can hit the numbers. Hitting them isn't
the achievement; showing they mean something is.

→ [[knowledge/Confidence Is Not Truth|Goodhart, the winner's curse, and what counts as
evidence]]

## Where we are

The harness reproduces ground truth: pembrolizumab passes every binding gate and correctly
*fails* the novelty gate, because it is the molecule you're not allowed to copy.

We then gave a folding model nothing but two sequences — no template — and asked how
pembrolizumab binds PD-1. It recovered the real structure at **DockQ 0.820**, where two copies
of the same crystal score 0.867 against each other.

**⚠ What that proves and doesn't.** The reference structure is from 2017 and is almost
certainly in the model's training data, so this is partly retrieval. It establishes that the
pipeline works end to end. It does **not** establish that the model can place a
never-before-seen antibody — which is exactly what Challenge 2 needs. The honest test is a
post-training-cutoff complex, and we haven't run it.

→ [[knowledge/How Structure Prediction Works|What the model does and what its numbers mean]]

## What broke

The most valuable part. **Eight silent failures** — not one raised an exception, each would
have produced a confident wrong number. A structure format where experimental and predicted
files store different quantities in the same field. A tool numbering the *target* as an
antibody because they share an evolutionary fold. A reference structure whose chains are paired
crosswise. A comparison tool whose defaults would have refused to score every design we plan to
make. A folding model exiting successfully after failing, twice.

→ [[knowledge/Eight Silent Failures|All eight: cause, catch, fix, principle]]

Plus half a day lost to infrastructure: a dependency conflict forcing four separate
environments, a prediction that took four attempts for four different reasons, and two mistakes
of my own.

→ [[knowledge/The Environment Saga|Symptom, real cause, fix, generalisation]]

**The one lesson I'd keep:**

> A tool that refuses to produce output is the good failure. The dangerous ones hand you a
> number anyway — right range, right units, computed on the wrong thing.

## Where we got to

**Challenge 1 has a named candidate.** `mpnn_T0.5_s104_036` — CDR-H3 `ALRPRDVDRGFYK`, 38.5%
identity to pembrolizumab, rubric score **87.5**, viable on all eight gates, fresh-seed DockQ
**0.749**. Chosen from 239 designs generated across four sampling temperatures, every one of
them folded rather than filtered, then re-measured at seven random seeds.

Three things the campaign taught that outlast it:

- **A cheap filter has to beat the same filter applied at random.** The CDR-H3 aromatic screen
  does — by +0.0241 mean DockQ against an equal-size random subset, p<0.0001. But it does not
  move the *maximum*, and the design we named would have been thrown away by it. A filter that
  raises a pool's average is not a filter that finds you a winner.
- **Three seeds is the worst way to spend a fold budget.** Given noisy measurements, extra
  *candidates* stop helping almost immediately while extra *precision per candidate* keeps
  paying. Twenty designs at seven seeds beats sixty at three, for the same compute.
- **The winner's curse is real, correctable, and we proved the correction.** The best-looking
  design is best-looking partly by luck. Shrinking its score by the measurement's reliability
  landed within **0.001 points** of an independent re-measurement — a coincidence, not a validation: that measurement is one fold with sd 0.467, so it cannot separate the discount from no discount (corrected 2026-09-20) — against a raw number
  that was 0.155 too high, which is seven times the gap separating first place from second.

## What's next

Resolve the top of the ranking — first and second differ by a tenth of a standard error, so we
have *a* best design rather than *the* best (~20 more folds settles it) · then the validation
dossier the whole project was aimed at: specificity controls, hotspot ablation, epitope overlap
· and, if the length axis is ever to be explored, a second generator, because ProteinMPNN
cannot change a loop's length.

## Working documents

[[PLAN|Delivery plan, including a review of its own weaknesses]] ·
[[BUILD|Code skeleton]] · [[docs/sessions/README|Session logs]] ·
[[knowledge/README|Knowledge notes index]]
