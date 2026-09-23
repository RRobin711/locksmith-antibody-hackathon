# 06 — Allocation and Selection

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [[CORRECTIONS|correction C1, and what it does and does not invalidate]]. Challenge 1 is unaffected.

**What this chapter teaches.** You have a noisy instrument, a pool of candidates, and a budget. Where
does the next measurement go — a new candidate, or another replicate of an old one? The answer is not
a matter of taste; it is derivable, and it **inverts** depending on what you are trying to estimate.
We derive the two laws that govern it (the error of a *mean* falls as `1/√k`; the error of a *spread*
falls as `1/√(2(k−1))`), simulate the whole selection procedure including the final `argmax`, and
then confront the three ways a selection stage lies to you even when the arithmetic is right:
**winner's curse** (the argmax is biased upward), **banding** (a step function destroys the resolution
you paid for and reorders under a change of convention), and **order statistics from a ranked
generator** (your "prediction" is silently a maximum).

This is the chapter where the measurement theory of
[[04-measurement-theory|the reliability chapter]] turns into decisions, and where several of the
campaign's own decisions turn out to have been wrong. The banding section contains the course's
sharpest single result: a claim written in a config file, repeated in an audit, and **false as a
theorem** — with an exhaustively verified counterexample.

Formulas are derived; arithmetic is shown. [[10-glossary|The glossary]] carries the terms.

---

## 1. Two laws, and why the same budget inverts

### 1.1 The error of a mean

For a mean of *k* independent, identically distributed replicates with per-replicate sd σ,

```
SE(x̄)  =  σ / √k                                                            (6.1)
```

Units: whatever σ is in. The consequence everyone knows: halving your error costs **four times** the
measurements. The consequence fewer people internalise: the *marginal* return is brutal, because
`d/dk (σ/√k) = −σ/(2k^{3/2})`. Going 1 → 2 seeds removes 29% of the error; going 6 → 7 removes 3.7%.

### 1.2 The error of a spread

Now suppose the quantity you care about is not a design's mean score but its **variability** — here,
how much a flexible loop moves between independent folds, a direct read on conformational
heterogeneity. You are estimating an sd, and an sd obeys a different law. For roughly normal data,

```
SE(s²)  ≈  s² · √(2/(k − 1)),        so       SE(s)/s  ≈  1 / √(2(k − 1))    (6.2)
```

The second expression follows from the delta method applied to `s = √(s²)`: if `g(x) = √x` then
`SE(g) ≈ |g'(x)|·SE(x) = SE(s²)/(2s)`, and substituting the first expression gives
`s√(2/(k−1))/2 = s/√(2(k−1))`.

Note what (6.2) is: a **relative** error. Evaluate it:

```
k = 3 :  1/√4   =  0.500   →  50%
k = 5 :  1/√8   =  0.354   →  35%
k = 7 :  1/√12  =  0.289   →  29%
```

(`scripts/36_ensemble_power.py:9` and the session doc record exactly 50% / 35% / 29%.) For comparison,
the *mean* at the same k has relative error 0.58σ, 0.45σ, 0.38σ.

**A three-fold estimate of a spread carries a 50% relative error.** If a design's measured loop
spread is 0.60 Å at k = 3, the honest statement is roughly 0.30–0.90 Å. This is a far worse position
than the same three folds put you in for a mean, and it is why the allocation answer flips.

> **Transferable principle**, stated verbatim in the project:
> *"An optimal-allocation result is a property of the estimator, not of the pipeline. Change what you
> are estimating and you must re-derive it."*

This is the best worked example the campaign produced, because the *same team*, on the *same data*,
with the *same budget*, reached opposite conclusions a week apart — and both were right, for
different estimands.

### 1.3 The reliability of a k-seed spread

Estimated **for free**, from 20 shortlisted designs already folded at 7 seeds each, using all `C(k,2)`
seed pairs with each pair superposed on the **framework** — never on the loop itself, which would
superpose away the very motion being measured (`results/ensemble_power.md`):

| seeds k | sampling var of a k-seed spread | reliability | attenuation √r |
|---|---|---|---|
| 2 | 0.06280 Å² | **0.599** | 0.774 |
| 3 | 0.02465 Å² | **0.792** | 0.890 |
| 4 | 0.01222 Å² | **0.885** | 0.941 |
| 5 | 0.00618 Å² | **0.938** | 0.969 |
| 6 | 0.00270 Å² | **0.972** | 0.986 |
| 7 | 0.00000 Å² | **1.000** | 1.000 |

with between-design variance of the 7-seed spread **0.09372 Å²** (sd 0.306 Å over 20 designs). Each
row is `r = B/(B + s_k)`; verify the k = 2 row: `0.09372/(0.09372 + 0.06280) = 0.5988`.

**Two traps, both named by the project.** First, **the k = 7 row is a tautology**: truth was *defined*
as the 7-seed spread, so a 7-seed estimate has zero error against it by construction. Modelling the
sampling variance as `V₁/C(k,2)` and subtracting gives a corrected value of **0.968**, and *"a table
with a 1.000 in it invites a reader to believe something no data can support."*

Second, and more alarming: **the table is carried by one design.** The 20 seven-seed spreads are
0.31, 0.37, 0.39, 0.40, 0.45, 0.46, 0.46, 0.49, 0.50, 0.50, 0.51, 0.52, 0.52, 0.54, 0.55, 0.65, 0.68,
0.74, 0.82 … and **1.77 Å**. Dropping that single design collapses between-design variance **5.7×**,
from 0.0907 Å² to **0.0145 Å²**, and with it:

| quantity | with the outlier | without |
|---|---|---|
| reliability at k = 2 | **0.591** | **0.265** |
| reliability at k = 3 | **0.813** | **0.520** |
| attenuation at k = 2 | 0.769 | **0.515** |

(Those 0.591/0.813 figures are the ones that disagree with the table above at the third significant
figure; the reconstruction of why is in
[[04-measurement-theory|the measurement-theory chapter's section on figures that disagree]].)

A leverage check like this costs one line of code and it is the difference between "the ensemble axis
carries signal" and "one design does". The question was then settled properly on the full 239-design
pool: between-design variance **0.13720 Å²**, k = 2 [[04-measurement-theory#1.3 Reliability|reliability]] **0.686**; dropping the top three
spreads (2.58, 2.24, 2.09 Å) moves it to 0.10264 Å² and **0.620**. *"The variation survives, so it is
a distribution, not an artefact of a few designs."*

### 1.4 Breadth beat depth — the opposite of the previous week's answer

Now spend the budget. Going from 2 to 5 seeds per design costs **4×** the folds and recovers, at best,
`0.967/0.769 = 1.26×` of the attenuated effect. The *same* folds spent on new designs take n from 60
to 239 and shrink the Fisher-z standard error (see
[[05-experiment-design|the power machinery]]) by `√(236/57) = 2.0×`. The allocation table makes it
concrete: at a 120-fold budget the detectable `ρ_true` at 80% power is **0.327** for k = 2 / n = 120
against **0.591** for k = 7 / n = 20.

**Breadth wins, decisively** — for estimating a correlation. One week earlier, for *ranking*, depth had
won. Both conclusions stand. The estimand changed.

---

## 2. Simulating the whole procedure, including the argmax

### 2.1 The setup

`results/m3_shortlist_depth.md` §3–§5. Inputs, all measured rather than assumed: 239 designs,
single-seed surrogate reliability **0.689**, seed noise sd **0.529** surrogate points, implied true
between-design sd **0.562**. Four thousand simulated pools; true scores drawn `N(0, 0.562)`, one
observation each at `N(true, 0.529)`.

### 2.2 The wrong question, kept for the trail

First the project asked: *how deep must the shortlist be to retain the true best designs?*

| retain the true top… | median depth | 90th pct | depth for P ≥ 0.95 | folds to 3-seed it |
|---|---|---|---|---|
| 1 | 5 | 32 | **48** | 96 |
| 3 | 26 | 73 | **91** | 182 |
| 5 | 45 | 99 | **119** | 238 |

Retaining the true top 5 with 95% confidence demands a shortlist of **119 of 239** — half the pool.
That looks like a devastating argument for enormous shortlists, and it is wrong, because **retention
is a proxy**. Retaining the best design is not the same as *picking* it.

### 2.3 The right question

Simulate what actually ships: one seed on all 239 → take the top *k* → 3 seeds each → `argmax` → and
record the **true** score of the design you named.

| k | extra folds | E[true score of the pick] |
|---|---|---|
| 5 | 10 | +1.3470 |
| 10 | 20 | +1.3843 |
| 20 | 40 | **+1.3949** |
| 30 | 60 | +1.4031 |
| 60 | 120 | +1.3970 |
| 119 | 238 | +1.3884 |
| 239 | 478 | +1.3798 |

**The curve plateaus past k ≈ 20 and then turns down.** Three-seeding the entire pool — 478 folds —
is *worse* than forty. The mechanism: *"a deeper list adds candidates whose 3-seed scores are just as
noisy — a noisy-high mediocre design gets promoted about as often as the true best gets found."*
Breadth adds candidates measured just as badly as the ones you had; the quality of the pick is bounded
by the reliability of the **choosing** measurement, not by the size of the pool.

### 2.4 The budget table, and the claim that was false

Now hold total folds fixed and trade shortlist size against seeds:

| budget | allocation | E[true score of pick] |
|---|---|---|
| 40 | 20 × 3 | **+1.4024** |
| 40 | 13 × 4 | +1.4148 |
| 40 | 10 × 5 | **+1.4338** |
| 40 | 6 × 7 | +1.4122 |
| 40 | 4 × 10 | **+1.3847** |
| 40 | 2 × 15 | **+1.2992** |
| 120 | 60 × 3 | **+1.3880** |
| 120 | 40 × 4 | +1.4297 |
| 120 | 30 × 5 | +1.4587 |
| 120 | 20 × 7 | **+1.4659** ← chosen |
| 120 | 13 × 10 | **+1.4789** |
| 120 | 8 × 15 | +1.4690 |
| 240 | 120 × 3 | +1.3842 |
| 240 | 80 × 4 | +1.4302 |
| 240 | 60 × 5 | +1.4582 |
| 240 | 40 × 7 | +1.4778 |
| 240 | 26 × 10 | **+1.5015** |
| 240 | 17 × 15 | +1.5003 |

The headline extracted from this table, promoted into a rules file and repeated for a day, was
**"three seeds is the worst allocation at every budget tested"**. It is **false**, and the correction
is recorded in place: *"At budget 40, 20×3 (+1.4024) beats 4×10 (+1.3847) and 2×15 (+1.2992);
over-seeding a 2- or 4-design shortlist is worse than under-seeding a 20-design one. The claim holds
at budgets 120 and 240 only."*

The defensible statement: **seeds beat candidates over roughly the range 3 → 10 seeds, and the optimum
deepens as the budget grows.** At 40 folds the best row is 10 × 5; at 120 it is 13 × 10; at 240 it is
26 × 10. Note in passing that the allocation actually **run** at budget 120 was 20 × 7 (+1.4659) while
the table's own best row is 13 × 10 (+1.4789).

**Why this error is worth a section of a lecture course.** The refuting row was printed *directly
above* the false sentence, in the same file, by the same script. The claim was not inferred from bad
data or a broken model; it was a summary of a table the author had not read across. It then propagated
into a curated rules file, where it acquired the authority of a distilled principle and lost the table
that refutes it. An independent audit found it a day later.

> **Transferable principle.** *Read the table you are summarising — all of it, including the rows that
> are inconvenient. A summary sentence is a lossy compression of data that is right there, and the
> compression is performed by the person with the strongest incentive to like the conclusion.*

One genuinely good habit from the same work: **the i.i.d. assumption was tested, not assumed.** The
7-seed within-design sd was predicted at 0.529 from the 3-seed estimate and **measured at 0.467**
(0.88×) — close enough that no systematic component appeared, so averaging kept paying up to k = 7.
(Compare the mild evidence *against* i.i.d. seeds in
[[04-measurement-theory|the Spearman–Brown section]]; these two checks disagree slightly and neither
is decisive.)

---

## 3. Winner's curse

### 3.1 Why the argmax is biased

Every design's observed score is `x_i = τ_i + ε_i`. Take the argmax over *n* of them. The winner is
disproportionately a design whose `ε_i` happened to land high — not because noise is unfair, but
because you *searched* for the largest sum, and the largest sum tends to combine a large `τ` with a
large `ε`. Formally, `E[τ_{argmax}] < E[x_{argmax}]`, and the gap **grows with n**, because the
maximum of more draws is more extreme.

The empirical-Bayes (Kelley regression) correction is:

```
corrected  =  pool_mean  +  reliability × (observed − pool_mean)             (6.3)
```

Read it as: *trust a design's deviation from the pool mean only as far as the measurement is reliable.*
At r = 1 it does nothing; at r = 0 it shrinks everything to the mean. Units are the score's units.

The only **unbiased** estimate of a winner's quality is a measurement on a **fresh replicate that took
no part in selection**. Every seed used in selection is contaminated by having been selected on.

### 3.2 Worked

From `results/m3_winner.md` §3–§4:

| quantity | value |
|---|---|
| raw 7-seed mean surrogate (winner `mpnn_T0.5_s104_036`) | **95.117** |
| shortlist mean | **94.703** |
| reliability used for shrinkage | **0.629** |
| **winner's-curse discount** | **−0.153** |
| **discounted surrogate** | **94.963** |
| margin over 2nd place | **0.022** |
| fresh seed 23, used nowhere in selection | **94.962** |

Apply (6.3):

```
94.703 + 0.629 × (95.117 − 94.703)  =  94.703 + 0.629 × 0.414
                                    =  94.703 + 0.26041  =  94.963
```

Predicted 94.963; measured 94.962. One thousandth of a point apart.

An earlier, cleaner instance is worth copying as a technique: on re-seeding, the seed-1 top design
regressed **−0.0123** [[03-the-toolchain#4.1 DockQ 2.1.3 — two flags that both default wrong|DockQ]] while the average of all 8 re-seeded designs regressed **−0.0045**, so the
**selection excess is −0.0079 DockQ**. Subtracting the shared drift from the winner's drift isolates
the selection bias from whatever the re-run did to everything — that decomposition is the right way to
measure a winner's curse empirically.

### 3.3 The correction, which is the sharpest lesson in the campaign

The 0.001 agreement was published as a **validation** of the shrinkage estimator, in the README, the
results file and the rules file. It was then withdrawn:

> *"**This is not a validation, and calling it one was wrong.** The fresh estimate is ONE fold, sd
> **0.467**. The shrunk prediction misses by 0.03 sd and the *unshrunk* one by 0.33 sd — both inside
> one standard error, so this measurement cannot distinguish a 0.153-point discount from no discount.
> Landing within ±0.0005 of any prediction is a 1-in-1200 event. Discriminating the discount at 80%
> power needs about **73 fresh seeds**."*

Derive both arresting numbers, because they are the substance of the correction.

**The 1-in-1200.** A single fresh fold is one draw from `N(μ, 0.467²)`. The density at the centre is

```
1 / (0.467 × √(2π))  =  1 / 1.17060  =  0.85427   per surrogate point
```

so the probability of landing in a window of width 0.001 (that is, ±0.0005) is
`0.85427 × 0.001 = 8.543e−4 ≈ 1/1171`. Agreement that close was **luck**, and luck of a kind that
happens once in roughly twelve hundred tries.

**The k ≈ 73.** To distinguish a mean shift of δ = 0.153 from zero at 80% power and α = 0.05
two-sided, with per-observation sd σ = 0.467:

```
k  =  ((z_{0.975} + z_{0.80}) · σ / δ)²  =  ((1.96 + 0.84) × 0.467 / 0.153)²
   =  (1.3076 / 0.153)²  =  8.5464²  =  73.0
```

Seventy-three fresh folds to tell the discount from nothing. One fold tells you nothing at all,
*however close it lands*.

**And yet the discount matters.** 0.153 points is negligible against a 0–100 scale and **7× the 0.022
gap between 1st and 2nd place**. *"A bias far below the scale of the metric can sit far above the
scale of the decision, and a larger pool makes the correction LARGER, not smaller."*

> **Transferable principle.** *Apply the shrinkage estimator on theory; never quote a single confirming
> measurement as validation of it. State the measurement's own standard error first, and ask whether
> the competing hypothesis — no effect at all — is excluded. Here it was not.*

---

## 4. Banding: what a step function costs, and what changes when you relabel it

### 4.1 Resolution and edge noise

A banded metric maps a continuous measurement onto a step function: below a cutoff it is Poor, above
a threshold it is Good, in between Medium. Each band then contributes a fixed sub-score.

**Steps do not attenuate noise; they concentrate it at the edges and deliver it as a whole band step.**
A design far from an edge is perfectly reproducible. A design sitting on an edge flips on arbitrarily
small noise, and the flip is worth a full 2.5 points of the composite under the midpoint convention.
This is exactly the item-dependent, non-i.i.d. error component that made measured three-seed
reliabilities fall below their [[04-measurement-theory#3. Spearman–Brown: what averaging buys|Spearman–Brown]] predictions in
[[04-measurement-theory|the measurement-theory chapter]].

Measured (`results/m3_plan_review.md` §3.2): **22 of 40 designs (55%)** change their single-seed
composite across 3 seeds; the flipping sub-scores are **[[03-the-toolchain#4.3 ipSAE — interface confidence from the PAE|ipSAE]] (16 designs)** and **ΔG (17 designs)**;
single-seed reliability **0.602**; and — the cost that no amount of extra compute repairs — the
**40 designs collapse onto three distinct values, {82.5, 85.0, 87.5}**. *"Scaling generation to 200
does not add resolution, because banding is what removed it."*

The fix was a **continuous surrogate**: piecewise-linear interpolation through the same three anchors,
so that the surrogate agrees with the banded score exactly at each anchor and interpolates between
them. With `hi = good − medium` and `lo = medium − cutoff`:

```
if hi ≠ 0 and (v − medium)/hi ≥ 0:   sub = min(10, A_med  + (A_good − A_med)·(v − medium)/hi)
elif lo == 0:                        sub = A_poor
else:                                sub = max(0,  A_poor + (A_med − A_poor)·(v − cutoff)/lo)
```

Two details in that snippet are hard-won. The test `(v − medium)/hi ≥ 0` rather than `v ≥ medium` is
deliberate, so the same code works for **low-is-better** metrics where all three anchors and both
spans are negative. And the **degenerate-span** case — some metrics have `medium == cutoff`, so
`lo == 0` — was originally guarded by a single check that returned the medium anchor whenever *either*
span was zero, so a design sitting exactly on the Good edge scored 7.0 instead of 9.5 and a composite
of 95.00 came back as a surrogate of 87.50. *"Reading the code would not have found it — the guard
looks obviously correct."* The anchor-agreement test found it. Healthy output is 38.50 / 70.00 / 95.00
at cutoff / medium / good.

There is one place a continuous surrogate can **never** agree with a banded score, and it is not
measure-zero. Four Good edges are **strict** (`contacts > 25`, `iface_plddt > 80`, `cdr_sasa > 600`,
`cdrh3_identity < 70`). A value exactly on such an edge is Medium in the step function and Good in the
interpolation — and `contacts` is an integer count, so "exactly 25" is an ordinary outcome, not a
pathological one.

### 4.2 The anchors are worth twelve points

The rubric specifies bands as *ranges* — "Good (9–10)", "Medium (6–8)", "Poor (0–5)" — and never says
how to pick a number inside one. Three readings are implemented as a config switch:

| reading | anchors (poor / medium / good) | the winner's composite |
|---|---|---|
| bottom | 0 / 6 / 9 | **84.0** |
| midpoint | 2.5 / 7.0 / 9.5 | **90.0** |
| **top** (default) | 5 / 8 / 10 | **96.0** |

**An undocumented convention is worth 12 points out of 100 on the same molecule.** The defence of the
default is honest and deliberately weak: the rubric states its range as "0 – 100" and only `top`
attains it — *"Against that: '0 - 100' is a scale label, not a claim that 100 is attainable; `top` is
also the most flattering reading."*

### 4.3 The surrogate reorders under a change of anchors

The anchors do not merely relabel the surrogate; they set the **slopes of its two interpolation
segments**. Lower-segment rise over upper-segment rise is

```
midpoint:  (7.0 − 2.5) / (9.5 − 7.0)  =  4.5 / 2.5  =  1.8
top:       (8   − 5  ) / (10  − 8  )  =  3.0 / 2.0  =  1.5
```

A **non-uniform** slope change reorders. Measured on the 20-design shortlist
(`results/audit_response_2026-09-22.md` §B0, re-derived independently by
`scripts/76_audit_tonight.py` as one of 46 passing checks):

- the shipped winner falls from **1st to 4th**;
- **18 of 20 designs change rank**; Spearman between the two rankings is **0.755**, not 1.0;
- the 1st–4th gap is **0.191** surrogate points, against a pooled within-design seed sd of **0.226**
  and a 7-seed standard error of **0.086**; the entire top six spans 0.205;
- single-seed reliability on this shortlist is **0.296**.

The decision — **do not swap the submitted design** — is the right one and the reasoning is the point:
*"Swapping now would mean acting on a ranking this project has already measured as unable to rank. The
correct reading is that **the winner changing is itself further evidence for the claim we already
make**."* When your ranking's 1st-to-4th gap is smaller than one seed's standard deviation, the
identity of the winner is not information.

### 4.4 Monotone is not affine — and the config file's claim is false as stated

`config/metrics.yaml:17` states: *"The choice is a uniform monotone relabelling, so it moves the
headline number and never the ranking."* An audit repeated and sharpened it: *"That is true of the
banded `final` and false of the surrogate."*

**The surrogate half is right** — that is §4.3. **The `final` half is false as a theorem**, and the
distinction between *monotone* and *affine* is the payoff of this chapter.

Write the composite in closed form. The rubric's weights sum to 1: six binding metrics at 0.10 each
(0.60 total), developability 0.20, novelty 0.20. Let `w_g, w_m, w_p` be the **total weight a design
places in each band**, with `w_g + w_m + w_p = 1`, and let the anchors be `(a, b, c)` for
Good/Medium/Poor. Because the composite is a **weighted mean of sub-scores**,

```
final  =  10·[ a·w_g + b·w_m + c·w_p ]
       =  10·[ c + (a − c)·w_g + (b − c)·w_m ]        using w_p = 1 − w_g − w_m    (6.4)
```

Two designs are ordered by the sign of `(a − c)·Δw_g + (b − c)·Δw_m`. The additive constant `10c`
cancels; what survives is the **direction of the vector `(a − c, b − c)`**:

```
midpoint (9.5, 7.0, 2.5):   (a − c, b − c)  =  (7.0, 4.5),   ratio 1.5556
top      (10,  8,   5  ):   (a − c, b − c)  =  (5.0, 3.0),   ratio 1.6667
```

**These two vectors are not parallel.** The decision boundary in `(w_g, w_m)` space rotates when you
change convention, so pairs of designs lying between the two boundaries swap order.

The general statement: a componentwise monotone relabelling `g` of sub-scores is order-preserving for
*every* pair of designs under a weighted **mean** if and only if `g` is **affine**. Monotonicity alone
buys you only the much weaker guarantee that a design which dominates another *metric by metric* keeps
its position. And this `g` is not affine: fit a line through the two lower anchors
(`5 = 2.5α + β`, `8 = 7α + β`) to get `α = 2/3`, `β = 10/3`, and predict the Good anchor:

```
9.5 × (2/3) + 10/3  =  6.3333 + 3.3333  =  9.667      but the top reading uses 10
```

The relabelling bends upward at the top by exactly one third of a point, and that bend is the whole
phenomenon.

**The counterexample, verified exhaustively with exact rational arithmetic.** On this weight grid the
composite depends only on the band profile, and there are exactly **252 distinct profiles**
(`C(8,2) = 28` ways to distribute six binding metrics across three bands, times 3 for developability,
times 3 for novelty). Enumerating all `C(252,2) = 31,626` pairs and comparing the midpoint ordering to
the top ordering gives **39 strict ordering reversals**, with margins up to **1.000 composite point**.

A concrete instance, one of the maximum-margin pairs:

| | binding bands | dev | nov | `w_g` | `w_m` | `w_p` | midpoint | top |
|---|---|---|---|---|---|---|---|---|
| **A** | P P P P P G | G | G | 0.50 | 0.00 | 0.50 | **60.000** | **75.000** |
| **B** | M M M M M M | P | M | 0.00 | 0.80 | 0.20 | **61.000** | **74.000** |

```
A, midpoint:  10 × (9.5 × 0.50 + 2.5 × 0.50)              =  10 × 6.00  =  60.000
B, midpoint:  10 × (7.0 × 0.80 + 2.5 × 0.20)              =  10 × 6.10  =  61.000   → B wins
A, top:       10 × (10  × 0.50 + 5   × 0.50)              =  10 × 7.50  =  75.000   → A wins
B, top:       10 × (8   × 0.80 + 5   × 0.20)              =  10 × 7.40  =  74.000
```

The order flips, by a full composite point, from nothing but a change of convention. (The source
report constructs a second, independent counterexample on the same grid — A at 65.5 versus B at 64.5
under midpoint, 77.0 versus 78.0 under top — reaching the same conclusion by a different pair.)

So the correct statement is: **the band→score choice is a per-metric monotone relabelling, which
guarantees only that a design dominating another metric-by-metric keeps its position. It does not
guarantee a total order, because the relabelling is not affine.** That no reordering was observed here
is an **empirical fact about this pool** — where every design sits Good on at least six of eight
metrics and no design carries a Poor band, so the 39 reversing configurations are never realised — not
the theorem the config file asserts.

This matters practically, not just pedantically: the same sentence is the reason nobody re-ranked
under the `top` convention until the surrogate bug forced the question. A claim believed to be a
theorem is never re-tested.

> **Transferable principle.** *"Monotone" and "order-preserving under aggregation" are different
> properties, and the gap between them is exactly affineness. Any time you relabel the levels of an
> ordinal variable that is then **averaged**, you can change the ranking — and the only way to know
> you have not is to enumerate the grid, which here took one second.*

**Three things to keep apart**, because they are constantly confused: (i) *banding* destroys
resolution and concentrates noise at edges — 3 distinct values over 40 designs, 55% flip rate;
(ii) *the anchor values within bands* move the headline by 12 points and, in the continuous surrogate,
**reorder** designs because they change segment slopes non-uniformly — 18/20 ranks, Spearman 0.755;
(iii) *in the banded score itself* they reorder only in configurations this pool never produced — a
latent hazard, 39 of 31,626 pairs, not an observed one.

---

## 5. Order statistics: when your prediction is silently a maximum

### 5.1 The mechanism

The structure predictor emits `diffusion_samples` candidate structures and **orders them by its own
confidence**. Under the default `diffusion_samples=1`, `model_0` is *not a sample*. It is an **argmax
by construction** over a distribution that was never drawn — and with one sample there is nothing to
average, so the ranking is invisible.

If the per-draw score has CDF `F`, the maximum of *m* draws has CDF `F^m`, and `E[max of m]` rises with
*m*. Two consequences:

1. The value you report is biased upward by an amount depending on *m* **and on the spread of F** — so
   the bias is largest exactly where the prediction is least converged, which is exactly where you most
   need it to be honest.
2. A **threshold test read off the max of m draws** has effective false-positive rate
   `1 − (1 − p₁)^m`, where `p₁` is the single-draw rate. At `p₁ = 0.05` and `m = 5`, that is
   `1 − 0.95⁵ = 0.226`.

### 5.2 The measured envelopes

Five samples, everything else at the submitted settings (`results/diffusion_samples_2026-09-22.md`):

| | Challenge 1 | Challenge 2 |
|---|---|---|
| ipSAE spread | **0.039** | **0.128** |
| DockQ spread | **0.109** (0.711–0.820; crosses the 0.80 band edge on 2 of 5) | n/a |
| ΔG spread | 0.80 | 1.10 |
| contacts spread | 7 | 8 |
| interface pLDDT spread | 1.25 | 2.62 |
| **composite envelope** | **94.0–96.0** | **91.2–96.0** |

In both challenges, `model_0` — the submitted one — is the **best or joint-best of five**. Challenge
2's `model_0` has the highest ipSAE of the five, 0.864 against a median of 0.773.

**The second lesson the same data forced: confidence stability does not imply coordinate stability.**
Challenge 1's ipSAE barely moved (0.039) while DockQ — the only scored metric reading **coordinates
against an external reference** — moved 0.109 and crossed a band edge. The mechanism is architectural:
recycling refines a representation the trunk has already committed to, while the diffusion head
*generates the coordinates*. A rock-steady confidence number over a moving structure is not a
contradiction; it is the expected behaviour of a model that is confident about a fold it keeps drawing
slightly differently.

**The cost of knowing this: five diffusion samples took 2m54s against roughly 2m for one**, because
the alignment, the trunk and the recycling are shared within an invocation and only the diffusion head
reruns. About 50% more wall clock, available for the life of the project, and the argmax problem was
found on day 9 of 9.

**The independent confirmation is devastating**, and it links straight back to
[[05-experiment-design|the negative-control panel]]: HyHEL-10, an anti-lysozyme antibody, cleared all
five hard viability cutoffs on `model_0` — while its **median over five samples is ipSAE 0.219**.
*"The maximum of five draws from a broad low distribution routinely lands above a threshold the
distribution's centre is nowhere near. The gate is not broken. Reading the gate off a single diffusion
sample is."*

> **Transferable principle.** *A generative predictor that returns its outputs ranked hands you an
> order statistic, not a sample. Taking the first and calling it "the prediction" silently reports a
> maximum. Sample enough to know the spread you are sitting at the top of, and report that spread
> beside the number.*

---

## 6. Compression versus noise in an under-converged sampler

The last allocation question is the sampler's own depth, and it produces a distinction worth naming.

**The situation.** Thirty de novo designs were folded at `recycling_steps=3` — a setting inherited
from a different arm and never re-examined — and returned **0/30 viable**, all failing the ipSAE gate,
best **0.372** against a 0.60 threshold, median 0.006, and **15 of 30 at exactly 0.000**.

**The tell.** A pile-up at the floor is a **convergence diagnosis**, not a result.

**The re-fold at recycling 10:**

| design | recycling 3, seed 1 | recycling 10, seeds 1/2/3 |
|---|---|---|
| `bb_2_0_dldesign_1` | 0.263 | **0.864 / 0.842 / 0.856** |
| `bb_4_0_dldesign_2` | 0.372 | 0.331 / 0.416 / 0.361 |
| `bb_6_0_dldesign_2` | 0.242 | 0.011 / 0.267 / 0.105 |
| `bb_4_0_dldesign_0` | 0.235 | 0.000 / 0.000 / 0.000 |
| `bb_7_0_dldesign_1` | 0.234 | 0.161 / 0.169 / 0.000 |

Extra recycling did **not lift the pool**. It **resolved** it, and the evidence is three numbers:

- the **rank correlation between depths is only 0.432** — the ordering is not preserved;
- the **zero count is identical, 15/30, at both depths** — the distribution's shape did not move;
- the design that clears was ranked **2nd** at depth 3, and the one ranked **1st still fails**.

**The distinction that matters.** *Noise* inflates `σ_noise` and degrades a ranking symmetrically:
reliability falls, but the expected rank correlation between two independent noisy measurements stays
positive and the marginal distribution of scores **widens**. *Compression* is different: the map from
true quality to observed score is flattened — here, saturated at a floor — so the ranking is destroyed
**without the distribution widening**. That is precisely the signature observed: rank correlation
0.432, zero count unchanged, one design moving.

At depth 3 the ranking was not merely weak, it was **actively misleading**. Final answer: 1/30.

**Convergence is not even monotone.** Across recycling 3 / 10 / 20 the winner reads
**0.263 → 0.864 → 0.795**, and at depth 20 across seeds **0.795 / 0.883 / 0.731**, giving composites
**93.6 / 96.0 / 93.6** — so the headline 96.0 reproduces in **one of three** seeds at the deepest
setting tested. The honest report is **93.6–96.0 depending on sampling depth and seed**.

**And the variance finding is larger than the score.** Across depths 3/10/20, the ipSAE range for a
real crystallised complex is **0.050**, for the near-native Challenge 1 design **0.036**, and for the
de novo Challenge 2 design **0.601** — **12–17× more variable, and not converged at any depth tested.**

**The control that was blind.** A positive control had been built precisely to catch a pool-wide
failure. It passed, and it was blind, *"because it ran at recycling 3 too"*. It correctly exonerated
the construct choice (Fab 0.776, Fv 0.842) and *"printed a verdict about the pool that was wrong
within the hour."*

> **Transferable principle.** *Before interpreting a unanimous null from a sampler, vary its **sampling
> depth**, not just its seed. And remember: a control eliminates the confound you thought of and is
> silent on the one you did not — a passing control reads as general reassurance and is nothing of the
> kind.*

---

## What to take away

1. **Derive the allocation, do not intuit it, and re-derive it when the estimand changes.** The error
   of a mean falls as `1/√k`; the error of a spread falls as `1/√(2(k−1))` — 50% / 35% / 29% relative
   at k = 3/5/7. Same data, same budget, opposite answers a week apart, and both correct.
2. **Simulate the whole procedure including the final argmax.** Retention is a proxy: retaining the
   true top 5 with 95% confidence needed a shortlist of 119 of 239, while expected pick quality
   plateaus at **k ≈ 20** and 3-seeding all 239 (478 folds) is worse than 40 folds.
3. **Check every row of the table you summarise.** "Three seeds is the worst allocation at every
   budget" is refuted at budget 40 (20 × 3 at +1.4024 beats 4 × 10 at +1.3847 and 2 × 15 at +1.2992) by
   the table printed directly above the sentence.
4. **Check leverage.** Dropping one design with a 1.77 Å spread moved k = 2 spread reliability from
   0.591 to **0.265**. One line of code; the difference between a distribution and an anecdote.
5. **The argmax is biased upward, and the correction is `pool_mean + r × (observed − pool_mean)`.**
   Here: 94.703 + 0.629 × 0.414 = 94.963, against a fresh measurement of 94.962 — **which validates
   nothing.** One fold has sd 0.467, both shrunk and unshrunk predictions sit inside one standard
   error, ±0.0005 agreement is a 1-in-1200 event, and discriminating the 0.153 discount at 80% power
   needs ~73 fresh seeds. Apply the estimator on theory; never quote a single confirming measurement
   as validation.
6. **Banding destroys resolution and concentrates noise at the edges** — 40 designs onto three values,
   55% changing score across seeds via full 2.5-point band-edge steps. Rank on a continuous surrogate,
   report the banded score, break ties by distance from a band edge.
7. **Monotone ≠ affine.** A monotone relabelling of ordinal levels that are subsequently **averaged**
   can reorder. Verified exhaustively on this rubric's own 252-profile grid: **39 strict reversals**,
   margins to 1.000 composite point. The config file's "never the ranking" is an empirical fact about
   one pool, not a theorem — and believing it was a theorem is why nobody re-ranked.
8. **A ranked generative output is an order statistic.** `diffusion_samples=1` reports a maximum; five
   samples cost 2m54s against 2m. And **confidence stability is not coordinate stability** — ipSAE
   moved 0.039 while DockQ moved 0.109 on the same five structures.
9. **An under-converged sampler gives you a compressed ranking, not a noisy one.** Rank correlation
   0.432 between depths, identical 15/30 zero count, the clearing design ranked 2nd at the shallow
   depth. Vary sampling depth before believing a unanimous null.

This closes the mathematical core. [[07-the-campaign|The campaign chapter]] walks the nine days in
order and shows where each of these ideas arrived — usually later than it should have.
[[08-what-broke|The failure catalogue]] and [[09-critique|the critique]] take up what that lateness
cost.
