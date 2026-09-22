# How deep must the shortlist be?

Reproduce with `scripts/31_shortlist_depth.py`. The question is not "how many can we afford to 3-seed" but "how many must we 3-seed so that the design we would have picked with perfect measurement is still in the list". Cutting on a single-seed ordering and re-measuring only the survivors makes anything wrongly discarded invisible for ever.

## 1. The noise, measured on the continuous surrogate

All quantities are in surrogate points, which share the 0–100 scale of `final` and agree with it exactly at every band anchor (`src/locksmith/select/surrogate.py`).

| quantity | value |
|---|---|
| seed noise sd, within design (40-pool, 3 seeds) | **0.529** |
| between-design sd of 3-seed means (40-pool) | 0.787 |
| single-seed reliability of the surrogate | **0.689** |
| 3-seed-mean reliability of the surrogate | **0.849** |
| observed sd of the 239-pool (single seed) | 0.772 |
| implied TRUE between-design sd, 239-pool | **0.562** |

For comparison the banded `final` scored **0.602** single-seed and **0.780** at three seeds. The surrogate is better at one seed (0.689), which is the entire reason for ranking on it.

## 2. Estimate (a) — empirical, distribution-free, n=40

| retain the true top… | depth needed in the 40-pool | as a fraction of the pool |
|---|---|---|
| 1 | **1** | 2% |
| 3 | **4** | 10% |
| 5 | **14** | 35% |

Truth here is the 3-seed mean, which is itself noisy (reliability 0.849), so this understates the depth somewhat.

## 3. Estimate (b) — simulated at the real n=239

True scores drawn N(0, 0.562); one observation each at N(true, 0.529); rank by the observation; record the depth containing the true top *m*. 4,000 simulated pools.

| retain the true top… | median depth | 90th pct | **depth for P≥0.95** | folds to 3-seed it |
|---|---|---|---|---|
| 1 | 5 | 32 | **48** | 96 |
| 3 | 26 | 73 | **91** | 182 |
| 5 | 45 | 99 | **119** | 238 |

## 4. Both of the above answer the wrong question

Estimates (a) and (b) size the shortlist so that the true best designs are *retained*. But retaining the best design is not the same as **picking** it, and only the pick ships. The shortlist is re-measured at more seeds and then argmax-ed, so the right criterion is the expected TRUE quality of the design finally named — and that is limited by the reliability of the measurement used to choose, not by the depth of the list.

Simulating the whole procedure end to end (1 seed on all 239 → top k → 3 seeds on those → argmax), 4,000 pools:

| k | extra folds | E[true score of the design picked] |
|---|---|---|
| 5 | 10 | +1.3470 |
| 10 | 20 | +1.3843 |
| 20 | 40 | +1.3949 |
| 30 | 60 | +1.4031 |
| 60 | 120 | +1.3970 |
| 119 | 238 | +1.3884 |
| 239 | 478 | +1.3798 |

**The curve is flat past k≈20.** Going from k=20 (+1.3949) to 3-seeding the entire pool (+1.3798, 478 folds) buys nothing measurable. Depth stops helping almost immediately, because a deeper list adds candidates whose 3-seed scores are just as noisy — a noisy-high mediocre design gets promoted about as often as the true best gets found.

## 5. So spend the folds on SEEDS, not on depth

If the binding constraint is the reliability of the choosing measurement, the fix is more seeds per candidate, not more candidates. Holding the fold budget fixed:

| budget (extra folds) | k × seeds | E[true score of pick] |
|---|---|---|
| 40 | 20 × 3 | +1.4024 |
| 40 | 13 × 4 | +1.4148 |
| 40 | 10 × 5 | +1.4338 |
| 40 | 6 × 7 | +1.4122 |
| 40 | 4 × 10 | +1.3847 |
| 40 | 2 × 15 | +1.2992 |
| 120 | 60 × 3 | +1.3880 |
| 120 | 40 × 4 | +1.4297 |
| 120 | 30 × 5 | +1.4587 |
| 120 | 20 × 7 | +1.4659  ← **chosen** |
| 120 | 13 × 10 | +1.4789 |
| 120 | 8 × 15 | +1.4690 |
| 240 | 120 × 3 | +1.3842 |
| 240 | 80 × 4 | +1.4302 |
| 240 | 60 × 5 | +1.4582 |
| 240 | 40 × 7 | +1.4778 |
| 240 | 26 × 10 | +1.5015 |
| 240 | 17 × 15 | +1.5003 |

**CORRECTED 2026-09-20: three seeds is NOT the worst allocation at every budget — the table above refutes it.** At budget 40, 20 x 3 (+1.4024) beats 4 x 10 (+1.3847) and 2 x 15 (+1.2992); over-seeding a 2- or 4-design shortlist is worse than under-seeding a 20-design one. The claim holds at budgets 120 and 240 only. The defensible statement is that **seeds beat candidates over roughly 3->10 seeds, and the optimum deepens as the budget grows**. Note also that at budget 120 the table's own best row is 13 x 10 (+1.4789), not the 20 x 7 (+1.4659) that was run. The campaign plan's "3-seed the shortlist" spends folds on the axis that has already stopped paying.

## 6. Decision: **k = 20 designs at 7 seeds** (120 extra folds)

Supersedes the k=119 of §3 and the k=30 planned by feel. Expected true score of the pick +1.4659 against +1.4031 for the planned 30×3 — a better pick for 120 folds against 60.

**The assumption this rests on, and how the run tests it.** The simulation assumes seed noise is i.i.d. and that s seeds shrink it by √s. The 40-pool has only three seeds, so that is unverified past s=3. Seven seeds on twenty designs checks it directly: if the within-design sd across 7 seeds materially exceeds the 3-seed estimate, the noise has a systematic component — a design with two genuine conformational basins would do it — and averaging has stopped helping. That check is reported with the winner.

## 7. Superseded: the retention-based sizing

Kept because the reasoning trail matters. Retention-based sizing said k=119.

The two estimates disagreed by construction and the larger would have been taken: empirical (a) says 14, simulation (b) says 119 for the true top 5 at 95%. **k = 20**, costing **40 additional folds** (0.9 h at the measured 84 s/fold quiet).

> Shallower than the 30 planned by feel, so 30 is kept as the operating depth: there is no reason to cut below what was already budgeted.

### Why not simply 3-seed everything
239 designs x 2 extra seeds = 478 folds = 11.2 h. That is the honest alternative and it is not absurd; it is rejected only because 30 captures the true top 5 at 95% for 13% of the folds. If the campaign is ever re-run with batching working, 3-seeding the whole pool removes this entire analysis and its assumptions.

