# Pre-registration — does the §9.2 constraint cost binding?

**2026-09-23, written before any constrained sequence was folded.**

## The question

Constrained re-design produces a §9.2-clean sequence on 18 of 18 backbones, median one
attempt ([[constrained_redesign_yield]]). That establishes clean sequences *exist* and are
cheap to reach. It does **not** establish they fold to viable interfaces.

The concern is specific and chemical: the constraint forbids asparagine at particular CDR
positions, and Asn is a workhorse paratope residue. ProteinMPNN compensating at
neighbouring positions is exactly what should happen — the question is whether the
compensated interface is as good.

## Why this design and not a new campaign

The comparison is **paired on the backbone**. Each constrained sequence is folded on a
backbone whose *unconstrained* behaviour is already measured under the same correct
alignment. New backbones would confound the constraint with backbone identity; these
cannot, because the backbone is held fixed and only the sequence constraint varies.

Cost: 18 local folds, ~52 minutes, no rental. Nothing here touches RFdiffusion, which is
the only step that needed a rented GPU (RFantibody pins torch 2.3, which will not run on
this Blackwell card at all).

## Sample size, stated before the fact

The re-screen scored **30 sequences across 10 backbones** (3 each). The yield run produced
clean sequences on **18**. So:

- **Paired arm: n = 10 backbones** that have both constrained and unconstrained scores.
- **Exploratory arm: 8 backbones** with no unconstrained comparator — they produced no
  sequences that reached scoring in the pilot. Reported separately and **excluded from the
  paired test**; they are new information, not evidence about the constraint.

**Power.** At n=10 pairs a Wilcoxon signed-rank test detects roughly a large effect
(d ≳ 1.0) at 80%. **A null here means "no effect larger than large", not "no effect".**
This design can distinguish "the constraint is roughly free" from "the constraint is
severely costly". It cannot resolve a modest cost, and no claim of that kind will be made
from it.

## Primary comparison, fixed now

For each of the 10 paired backbones:

- **constrained** = ipSAE, median of 5 diffusion samples, of the single clean sequence.
- **unconstrained** = ipSAE, median of 5, of the **median-scoring** of that backbone's 3
  sequences. Using the *best* unconstrained sequence would stack the comparison against the
  constraint, so the best-case is reported as a **secondary, conservative** bound rather
  than as the headline.

Statistic: **Wilcoxon signed-rank** on the 10 paired differences (constrained −
unconstrained), two-sided.

## Decision rule

- **Median paired difference ≥ −0.05 and p > 0.05** → the constraint is free at the
  resolution this test has. The campaign proceeds as designed: constrain at generation,
  discard nothing.
- **Median paired difference materially negative (≤ −0.15) or p < 0.05 against** → the
  constraint costs binding. The campaign design changes — liabilities move back to a
  post-fold ranking criterion and the §9.2-clean requirement is relaxed to a preference.
- **Between those** → inconclusive at n=10, reported as such, and the campaign proceeds
  with the constraint flagged as an unquantified risk rather than a settled one.

## Secondary readouts, also fixed now

- **How many constrained sequences clear ipSAE ≥ 0.60 on the median**, against the
  unconstrained pool's **1 of 30**. If several clear, sequence depth rather than backbone
  diversity was the bottleneck, and the cheapest next move is more sequences per existing
  backbone — local and free — rather than renting for new backbones.
- The 8 exploratory backbones, reported as a separate count.

## What would make me wrong

If constrained sequences fold *better* on average, the most likely explanation is not that
the constraint helps binding but that it is a second sampling pass — the yield loop draws
8 sequences per attempt and keeps the first clean one, which is a mild selection the
unconstrained pool did not get. That confound is **not** controlled here and would have to
be stated if the difference comes out positive.
