---
date: 2026-09-23
tags: [project, lecture, learning, statistics, pattern]
status: review
---

# 04 — Measurement Theory

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1, C2 and C3](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding, and **C3 applies to Challenge 1**: its composite is **94.0**, not the 96.0 this course derives in several places. Challenge 1 is unaffected *by the alignment defect*, which is narrower than "unaffected".

**What this chapter teaches.** How good is my measurement? Not "is it accurate" — that question
needs a truth to compare against, and this project never had one — but the prior question: *does
this number carry any information about the thing I am ranking, or is it the instrument talking to
itself?* We build classical test theory from zero: the decomposition `observed = true + error`, the
variance identity it implies, and reliability as a **ratio** of variances. From that one ratio
everything else in the chapter falls out — the intraclass correlation and its estimation from
replicates, the Spearman–Brown prophecy formula for what averaging buys you, the attenuation of
correlations by measurement error, and the collapse of reliability under range restriction. Each is
derived, then worked against numbers this campaign actually measured.

The chapter is the load-bearing one for the two that follow, because
[the chapter on designing an experiment that could fail](05-experiment-design.md) and
[the chapter on where to spend the next measurement](06-allocation-and-selection.md) both consume
reliability as an input. It is also the chapter where the campaign's single most expensive
conceptual error lives: **reliability is a property of a measurement *and a population*, and
selecting a shortlist destroys it on purpose.**

No statistics beyond an introductory course is assumed. No biology is assumed at all — every
quantity below is just "a number a program printed for a design", and if you want to know what
`ipSAE` or `DockQ` mean physically, see [the chapter on what each tool computes](03-the-toolchain.md).
Terms are collected in [the glossary](10-glossary.md).

---

## 1. The model: observed = true + error

### 1.1 Setting it up

We have a population of **items** — here, antibody designs, indexed by *i*. Each item has a fixed
but unobservable **true score** `τ_i`. We cannot read `τ_i`. What we can do is run a **measurement**,
which in this project means folding the design with a structure predictor at a particular random
seed *j* and reading a number off the result. Write that observation

```
x_ij = τ_i + ε_ij ,        ε_ij ~ (0, σ²_noise),   ε ⫫ τ,   ε_ij ⫫ ε_ij'      (4.1)
```

Three assumptions are packed in there and all three are testable, so name them:

1. **Additivity.** Error adds to truth; it does not multiply it or depend on it.
2. **Zero mean.** `E[ε] = 0`, so the measurement is *unbiased for the item*. Note this is much
   weaker than "the metric measures what you want" — a metric can be perfectly unbiased for a
   quantity nobody cares about. That distinction is validity, not reliability, and it is
   [the subject of the next chapter's control section](05-experiment-design.md).
3. **Homoscedastic independence.** The same `σ²_noise` for every item, and independent across
   replicates. This is the one that fails quietly. Section 4 shows the campaign's own evidence that
   it fails here.

Units: `x`, `τ` and `ε` all carry the metric's units — surrogate points on a 0–100 scale, ångströms
of RMSD, kcal/mol of predicted free energy, or dimensionless in the case of [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae) and [DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong).
`σ²_noise` carries the square of those units.

### 1.2 The variance identity

Take the variance of (4.1) over the population of items *and* over the measurement error. Because
`ε ⫫ τ`, the cross term vanishes:

```
σ²_obs = σ²_true + σ²_noise                                                  (4.2)
```

This is the whole of classical test theory in one line. The spread you see across designs is the
spread that is really there, plus the spread the instrument invents. You never observe either term
separately — but you can estimate `σ²_noise` by measuring *one* item repeatedly, and `σ²_obs`
directly from the pool, and then get `σ²_true` by subtraction.

### 1.3 Reliability

```
r  =  σ²_true / σ²_obs  =  σ²_true / (σ²_true + σ²_noise)                    (4.3)
```

Dimensionless, in [0, 1]. It is the **share of observed variance that is signal**. At `r = 1` the
observed ordering *is* the true ordering. At `r = 0` your ranking is a lottery whose tickets happen
to have numbers printed on them.

Two readings of `r` are worth holding simultaneously, because the campaign used both:

- **As a variance share.** `r = 0.6` means 60% of what you see is real.
- **As a correlation.** `r` is the expected correlation between two independent measurements of the
  same items. This is what makes it estimable, and it is why the same quantity is called the
  *intraclass correlation*.

The project states (4.1)–(4.3) in its own words as equations 2.1–2.3 of
`docs/sessions/2026-09-19-three-seeds-is-the-worst-allocation.md:100-120`.

### 1.4 First worked example: two ways to fold the same molecule

An antibody can be folded as a small construct (**Fv**, the two variable domains only) or a larger
one (**Fab**, variable plus one constant domain each). The Fv is cheaper. Is it as good?

From 3 variants × 3 seeds each (`results/panel_g1c_g1d.md` §1), pooling the within-variant variance
across variants and comparing it to the variance across the panel:

| construct | pooled within-variant variance | across-panel variance | reliability |
|---|---|---|---|
| Fv  | 0.00813 | 0.02071 | **0.607** |
| Fab | 0.00103 | 0.02918 | **0.965** |

Do the arithmetic yourself, using `r = 1 − σ²_within/σ²_obs`, which is (4.3) with `σ²_true`
eliminated by (4.2):

```
Fv :  1 − 0.00813 / 0.02071  =  1 − 0.39256  =  0.60744
Fab:  1 − 0.00103 / 0.02918  =  1 − 0.03530  =  0.96470
```

Both reproduce the file. The Fv is not merely worse; 39% of everything you see in an Fv screen is
the sampler. The decision this drove was to **abolish the Fv screen entirely** — and the argument
was a cost calculation, not a purity argument: three Fv seeds reach r = 0.823 (we derive that number
in §3) at 277 s, against one Fab fold at r = 0.965 for 126 s.

> **Transferable principle.** *A cheap measurement is only cheap per unit of reliability. Price it
> in replicates-to-parity, not in wall clock.*

---

## 2. The intraclass correlation, and metrics that turn out to be constants

### 2.1 Three estimators, and why the distinction bites

**Replicate form.** When the same item is measured *k* times, estimate `σ²_within` by pooling the
within-item variances and `σ²_obs` from the item means, then `r = 1 − σ²_within/σ²_obs`. This is what
§1.4 did.

**Cross-pool plug-in form.** Sometimes the replicates and the population come from different runs:
the campaign estimated within-design variance from **20 designs × 7 seeds** and total variance from
a **239-design single-seed pool**, then formed `ICC = 1 − within/total` (`results/metric_validity.md`
§1). This is legitimate, but note it is a ratio of two independently estimated quantities and is
**not constrained to be non-negative**. Keep that in mind; it is about to matter.

**ANOVA form.** For a balanced one-way design with *k* groups and *m* replicates per group, the
mean squares between and within give

```
ICC = (MS_between − MS_within) / (MS_between + (m − 1)·MS_within)            (4.4)
```

This is the classical ICC(1,1). It too can go negative, whenever `MS_between < MS_within` — that is,
whenever items differ from each other by *less* than replicates of the same item differ.

### 2.2 The measured table

From `results/metric_validity.md` §1 (20 designs × 7 seeds for the within term, 239 single-seed
designs for the total):

| metric | within-seed sd | pool sd | ICC | reading |
|---|---|---|---|---|
| `dg` (predicted ΔG, kcal/mol) | 0.491 | 0.794 | **0.618** | usable |
| `ipsae` (dimensionless) | 0.021 | 0.035 | **0.647** | usable |
| `dockq` (dimensionless) | 0.014 | 0.039 | **0.870** | usable |
| `iface_plddt` (0–100) | 0.886 | 2.224 | **0.841** | usable |
| `contacts` (integer count) | 6.003 | 6.013 | **0.003** | pure seed noise |
| `cdr_sasa` (Å²) | 50.552 | 46.063 | **0.000** | pure seed noise |

Check the two interesting rows:

```
contacts :  1 − (6.003/6.013)²   = 1 − 0.99668  =  0.00332
cdr_sasa :  1 − (50.552/46.063)² = 1 − 1.20442  = −0.20442
```

The `contacts` figure reproduces. The `cdr_sasa` figure does **not** reproduce as 0.000: the raw
plug-in is **−0.204**, and it was clamped at the boundary of the parameter space before being
reported. Clamping is the right reporting choice — a variance share below zero is not meaningful —
but it hides information, and the hidden information is the stronger claim. A negative estimate says
the within-design spread *exceeds* the between-design spread: `cdr_sasa` has **no detectable
between-design variance at all**. Report the clamp, but know the sign of what you clamped.

### 2.3 What ICC ≈ 0 actually means

It means the entire spread you observe across the pool is the same spread you would see by folding
**one** design over and over. Ranking on such a metric is drawing lots with the item names written
on them. The campaign records the consequence without softening it: any analysis that compared
designs on `contacts` — "including the 2026-09-20 hotspot ablation, whose verdict branch was decided
on `contacts`" — "was comparing two noise draws" (`results/metric_validity.md` §1).

There is a second, wholly independent way for a metric to be useless, and confusing the two is a
classic error. A metric can have **excellent** ICC and still contribute nothing, if its entire
observed range sits inside a single band of the scoring rubric — then it adds the same constant to
every design's score. From `results/metric_validity.md` §2: `dockq` spans 0.596–0.777 (0% of designs
reach the Good band), `contacts` 88–120 (100% Good), `iface_plddt` 83.2–94.11 (100%), `cdr_sasa`
1383.4–1648.3 (100%), `cdrh3_identity` 15.4–46.2 (100%), `netsolp` 0.562–0.619 (0% Good, pinned at
Medium).

**Five of the eight rubric metrics are constants across this pool. The eight-metric harness ranks on
three: `dg`, `ipsae`, `dockq`.** Two of those three are among the least reliable of the usable set,
and one of them — `dg` — is [blind to the epitope under the knockout control](05-experiment-design.md).

> **Transferable principle.** *ICC and dynamic range are different objections and they are not
> interchangeable. A metric can be perfectly reproducible and useless (pinned in one band), or wildly
> variable and useless (ICC ≈ 0). Check both before you rank on anything.*

### 2.4 The negative ICC, and the floor below which you cannot see

The second challenge scored candidates with a different predictor, and its pilot ran a one-way ANOVA
on k = 10 backbones × m = 3 sequences (`results/challenge2_pilot.md` Result 2):
`MS_between = 3.539`, `MS_within = 5.087`, `F = 0.70`. The pilot reported ICC **0.000**. Apply (4.4):

```
ICC = (3.539 − 5.087) / (3.539 + 2 × 5.087)  =  −1.548 / 13.713  =  −0.1129
```

which reproduces the audit's later figure of **−0.113** (`results/audit_response_2026-09-22.md` §B2)
and shows the "0.000" was, once again, a clamp.

Now the important construction. **What is the smallest ICC this design could have detected?** Put the
critical *F* at the design's degrees of freedom into (4.4) in place of the observed *F*. Since
(4.4) can be rewritten `ICC = (F − 1)/(F + m − 1)` where `F = MS_between/MS_within`, and
`F_crit(0.05, 9, 20) = 2.393`:

```
ICC_detectable = (2.393 − 1) / (2.393 + 2)  =  1.393 / 4.393  =  0.3171
```

reproducing the audit's stated **0.317**. So the honest statement is not "this metric cannot rank"
but "**no between-dock signal larger than ICC ≈ 0.32 is detectable at n = 10, k = 3**". The audit
puts it in one word: *"The word to use is **undetected**, not **absent**."*

The same pass overturned a grouping error. `pred_lddt` had been filed alongside `contacts` as
"constant and useless" because its sd is only 0.012. Measured properly it is ICC **+0.836** — the
highest of the four RF2 metrics and the only one clearing the 0.317 floor. Its sd is small because
roughly 85% of the complex is fixed framework, not because it fails to discriminate.
**Low variance is not uninformativeness** (`results/audit_response_2026-09-22.md` §B4).

---

## 3. Spearman–Brown: what averaging buys

### 3.1 Derivation

Average *k* independent replicates of the same item. Truth is unchanged; the noise variance divides
by *k*:

```
r_k  =  σ²_true / (σ²_true + σ²_noise / k)                                   (4.5)
```

Divide numerator and denominator by `σ²_obs = σ²_true + σ²_noise`, substitute `r₁ = σ²_true/σ²_obs`
and hence `σ²_noise/σ²_obs = 1 − r₁`:

```
r_k  =  r₁ / (r₁ + (1 − r₁)/k)  =  k·r₁ / (1 + (k − 1)·r₁)                   (4.6)
```

That is the **Spearman–Brown prophecy formula**. Invert it for the replicates needed to reach a
target `r_k`:

```
k  =  r_k (1 − r₁) / (r₁ (1 − r_k))                                          (4.7)
```

Both are dimensionless. Note the shape: (4.6) is concave in *k*, so every additional replicate buys
less than the one before, and `r_k → 1` only in the limit.

### 3.2 Worked: the Fv screen's seeds-to-parity

From `r₁ = 0.607` (Fv):

```
r₃  =  3 × 0.607 / (1 + 2 × 0.607)  =  1.821 / 2.214  =  0.8225
```

which is the 0.823 quoted in `results/panel_g1c_g1d.md` §1. To reach the Fab's 0.965 with Fv folds,
use (4.7):

```
k  =  0.965 × (1 − 0.607) / (0.607 × (1 − 0.965))  =  0.37925 / 0.021245  =  17.85
```

so eighteen Fv folds to match one Fab fold. The project's own statement — "0.96 needs k > 8 and 5.9×
the Fab cost already" — is the cheaper target `r_k = 0.96`, giving `k = 0.96 × 0.393 / (0.607 ×
0.04) = 15.5`; either way the conclusion is identical and the Fv screen dies.

### 3.3 Worked: the composite score, and a crack in the model

The campaign's headline score is a banded composite called `final`, on a 0–100 scale. From
`results/m3_plan_review.md` §3.2:

| quantity | value |
|---|---|
| within-design sd of single-seed `final` | 0.873 points |
| between-design sd of 3-seed-mean `final` | 1.486 points |
| designs whose single-seed `final` changes across 3 seeds | **22/40 (55%)** |
| single-seed reliability of `final` | **0.602** |
| 3-seed-mean reliability of `final` | **0.780** |
| distinct values of `final` across the 40 designs | **{82.5, 85.0, 87.5}** |

Now predict the 3-seed figure from the 1-seed figure:

```
r₃ (predicted)  =  3 × 0.602 / (1 + 2 × 0.602)  =  1.806 / 2.204  =  0.8194
r₃ (measured)   =  0.780
```

And do the same for the continuous **surrogate** score built to replace `final` for ranking
(`results/m3_shortlist_depth.md` §1), whose single-seed reliability is **0.689**:

```
r₃ (predicted)  =  3 × 0.689 / (1 + 2 × 0.689)  =  2.067 / 2.378  =  0.8692
r₃ (measured)   =  0.849
```

**Both measured three-seed reliabilities fall below their Spearman–Brown predictions**, by 0.039 and
0.020 respectively. This is not a rounding artefact and it is not noise in the same direction twice
by accident; it is the signature of seed noise with a **small non-independent component**. Averaging
correlated replicates removes less noise than (4.5) promises, because the `/k` in the denominator
assumes independence.

The mechanism is identifiable here: `final` is **banded**, so a design sitting near a band edge flips
band on arbitrarily small noise, and a design far from an edge cannot flip at all. That is a
structured, item-dependent error component, not an i.i.d. one, and it violates assumption 3 of §1.1
directly. We take [banding](06-allocation-and-selection.md#4-banding-what-a-step-function-costs-and-what-changes-when-you-relabel-it) apart properly in
[the chapter on allocation and selection](06-allocation-and-selection.md).

**The project never comments on this gap.** It matters because the allocation simulations of
[that same chapter](06-allocation-and-selection.md) assume i.i.d. seed noise throughout, and here is
its own data mildly contradicting the assumption. The correct disposition is not alarm — the
discrepancy is small — but it belongs in the record, and its absence is a real omission.

---

## 4. Attenuation: why correlations between noisy things look weak

### 4.1 Derivation

Let X and Y each be measured with independent error: `x = ξ + e`, `y = υ + f`, with
`e ⫫ f ⫫ ξ ⫫ υ`. Then

```
Cov(x, y) = Cov(ξ, υ)          because every cross term with e or f vanishes
sd(x) = sd(ξ)/√r₁ ,  sd(y) = sd(υ)/√r₂     from (4.3), since σ_obs = σ_true/√r
```

so the observed correlation is the true correlation shrunk by the geometric mean of the two
reliabilities:

```
ρ_obs  ≈  ρ_true · √(r₁ · r₂)                                                (4.8)
```

and the **disattenuated** estimate is `ρ_true = ρ_obs / √(r₁ r₂)`. The quantity `√r` is called the
**attenuation ceiling**: it is the largest correlation a perfectly-predicting instrument could show
against a perfectly-measured truth. If your metric has r = 0.6, no correlation you ever measure with
it against an errorless criterion will exceed 0.775, however good the science is.

### 4.2 Worked, with the campaign's numbers

From §1.4, `r_Fv = 0.607` and `r_Fab = 0.965`, so

```
√(0.607 × 0.965)  =  √0.58576  =  0.7654
```

and from `results/panel_g1c_g1d.md` §2:

```
restricted-range observed  ρ = +0.469  →  0.469 / 0.7654  =  +0.6128   (reported +0.612)
full-panel       observed  ρ = +0.662  →  0.662 / 0.7654  =  +0.8649   (reported +0.864)
```

The gate this fed — *does an Fv ranking predict a Fab ranking?* — **failed**, and the failure is
worth studying because the corrected number, 0.612, sits just above the 0.60 threshold that would
have passed it. The file refuses the pass in exactly the right words: *"Attenuation-**corrected**
restricted rho = +0.612… **This is a *corrected* figure, not an observation**"*, and the session
doc adds that *"0.612 straddling the threshold is not a pass"*
(`docs/sessions/2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test.md:215-216`).

### 4.3 The rule: never report a corrected value as an observation

Two reasons, and only the second is usually given.

1. **The correction is a ratio of estimates, and it inflates uncertainty by the same factor it
   inflates the point estimate.** Dividing by 0.7654 multiplies the point estimate by 1.31 — and
   multiplies its standard error by 1.31 too, *before* accounting for the fact that `r₁` and `r₂` are
   themselves estimated. A corrected ρ is strictly less certain than the observation it came from.
   Quoting it bare conceals that.
2. **It answers a counterfactual.** "What would I see with a perfect instrument?" is an interesting
   question and never the operative one, because no decision is ever taken with a perfect instrument.
   The gate is crossed or not with the instrument you have.

The campaign wrote the rule into a pre-registration before collecting the data:
*"every ρ against spread is reported **twice** — observed, and disattenuated by `ρ/√reliability` —
never only the corrected value"* (`results/prereg_2026-09-20_ensemble_wide.md` §3). The resulting
table (`results/ensemble_wide.md` §2, attenuation `√r = 0.828`) does exactly that: loop pLDDT
**−0.432** observed / **−0.521** disattenuated; interface pLDDT **−0.344** / **−0.416**; aromatic
count **+0.197** / **+0.238**; DockQ **−0.340** / **−0.411**.

> **Transferable principle.** *Report the pair. The observation is what happened; the correction is
> what the observation implies about a machine you do not own.*

---

## 5. Range restriction — and the insight that selection is the restricting operation

### 5.1 Why a ratio collapses when you narrow the pool

Return to (4.3) and read the two terms carefully. **`σ²_noise` is a property of the instrument and
of a single item. `σ²_true` is a property of the set of items you chose to measure.** Nothing about
the instrument knows which items you put in front of it.

So take a subpool whose true sd is `s` instead of the full pool's `S`, with `s < S`. The noise term
is unchanged, and

```
r_sub  =  s² / (s² + σ²_noise)   <   S² / (S² + σ²_noise)  =  r_full        (4.9)
```

strictly, for any `s < S`. This is the standard truncation result and it has a brutal practical
reading: **reliability is not a property of a measurement. It is a property of a measurement applied
to a population.** Quote one without the other and you have said nothing.

### 5.2 Instance 1 — the wide panel versus the top tier

The 0.965 of §1.4 was measured over designs spanning DockQ 0.036–0.818 — a panel deliberately built
to include obviously-dead controls. The real shortlist's top tier spans DockQ 0.650–0.754: roughly
ten times narrower. With the **same** seed noise, `results/reseed_ensemble.md` §1 reports pooled seed
sd 0.0209 and top-tier between-design sd 0.0401, giving

```
r  =  1 − (0.0209 / 0.0401)²  =  1 − 0.27165  =  0.7284      (reported 0.727)
```

Two distinct errors were compounded in reasoning from 0.965 to the shortlist, and the file names
both: the 0.965 was (a) a different **metric** (ipSAE, not DockQ) and (b) a different **range**.

> **Transferable principle.** *A reliability figure is meaningless without both the metric and the
> range it was measured on. Two numbers, always, or do not quote it.*

### 5.3 Instance 2 — the prediction that worked

Before re-running, the project predicted the top-tier reliability from the ratio of seed sd to
between-design sd: `seed_sd / between_design_sd ≈ 55%`, hence

```
r  =  1 − 0.55²  =  1 − 0.3025  =  0.6975      predicted ≈ 0.70
```

Measured: **0.727** (realised ratio 0.0209/0.0401 = 0.521, so `1 − 0.271 = 0.728`). The forecast was
good to three points of reliability, which is the strongest evidence in the campaign that the
classical model is doing real work rather than being decoration.

The consequence is stated exactly: single-seed ranking *"resolves broad tiers and not neighbours"*.
Concretely, the top two designs were separated by **0.001 DockQ** — one eighteenth of a seed sd —
and the identity of the top-1 changed with the seed (seeds 1 and 2 pick `mpnn_T0.1_s37_015`, seed 3
picks `..._003`), `results/reseed_ensemble.md` §2 and §5.1.

### 5.4 Instance 3 — shortlisting *is* the range-restricting operation

This is the sharpest version and the one to take away. A shortlist is, by construction, the
narrow-range subpool of (4.9). You created it deliberately. It therefore degrades every downstream
measurement's discriminating power, as a matter of arithmetic, before any of the measuring happens.

| quantity | value | source |
|---|---|---|
| surrogate 3-seed-mean reliability, used to size the shortlist from the 239-pool | **0.849** | `results/m3_shortlist_depth.md` §1 |
| top-20 shortlist, between-design sd of 7-seed means | **0.290** | `results/m3_winner.md` §1 |
| within-design sd over 7 seeds | **0.467** (forecast 0.529; ratio 0.88×) | `results/m3_winner.md` §1 |
| noise sd of a 7-seed mean | **0.176** | `results/m3_winner.md` §1 |
| **measured shortlist reliability** | **0.629** | `results/m3_winner.md` §1 |

Check the chain. The noise sd of a 7-seed mean follows from (4.5):

```
0.467 / √7  =  0.467 / 2.6458  =  0.17651       (reported 0.176)
```

and treating 0.290 as the observed sd of the 7-seed means, subtract noise variance from observed
variance to get the signal variance:

```
σ²_true  =  0.290² − 0.176²  =  0.08410 − 0.030976  =  0.053124
r        =  0.053124 / 0.08410  =  0.6317        (reported 0.629)
```

Now read the two lines that matter. **The noise behaved exactly as forecast** — 0.467 measured
against 0.529 predicted, a ratio of 0.88, well within estimation error of an sd from seven draws
(see [the spread-estimation law](06-allocation-and-selection.md), which gives that sd a 29% relative
error at k = 7). Nothing went wrong with the instrument. **The reliability fell from 0.849 to 0.629
because the signal was destroyed by the act of selecting.** The 239-pool's true between-design sd is
0.562; the top-20's is 0.290, roughly half. Halve the signal sd at constant noise and you quarter
the signal variance's share.

> **Transferable principle.** *Any reliability quoted for a selection stage must be computed on the
> range that stage actually sees, not on the discovery pool that fed it. Shortlisting is a
> range-restricting operation you perform on purpose, and it costs you the very resolution you built
> the shortlist to exploit.*

---

## 6. The 0.629 that "does not reproduce": an estimand mismatch, and a residual inconsistency

The campaign left this open, and it is worth resolving in full because the resolution is a general
lesson about how numerical disagreements should be diagnosed.

**What was flagged.** `STATE.md` §8 and `results/audit_response_2026-09-22.md` "Still open" §5 both
record: the reliability figure **0.629** *"does not reproduce from the recorded inputs under any
standard estimator we tried (the plug-in variance ratio on these data gives **0.276** under
`midpoint` and **0.296** under `top`)"*. Flagged, not corrected — on the sound grounds that
*"guessing would add a fifth number to a project already carrying four"*.

**The resolution, first half: they are estimating different things.** 0.629 is the reliability of a
**7-seed mean**, and §5.4 reproduces it exactly: `1 − 0.176²/0.290² = 0.6317`. That is the correct
quantity for the purpose it was used for, which was shrinking a 7-seed mean
([the winner's-curse estimator](06-allocation-and-selection.md) takes it as input). The audit's
0.276/0.296 are **single-seed** reliabilities on the same shortlist. Two different estimands. So
"does not reproduce" is itself an instance of a rule the project catalogues elsewhere: *never diff a
single observation against an aggregate without first checking what each number is.*

**The resolution, second half: they remain mutually inconsistent, and that was never established
either.** Different estimands are only innocent if they are *compatible*. Put them through
Spearman–Brown (4.6) and (4.7):

```
r₁ = 0.296  ⇒  r₇  =  7 × 0.296 / (1 + 6 × 0.296)  =  2.072 / 2.776  =  0.7464
r₇ = 0.629  ⇒  r₁  =  0.629 / (7 − 6 × 0.629)      =  0.629 / 3.226  =  0.1950
```

Predicted 0.746 against a recorded 0.629; back-implied 0.195 against a recorded 0.296. **These two
numbers cannot both be right under the i.i.d. model.** The discrepancy is real — it is simply not
the discrepancy that was flagged. Two candidate explanations, neither tested: the non-independent
seed component of §3.3 (which pushes measured `r_k` *below* its Spearman–Brown prediction, the right
direction and roughly the right neighbourhood at k = 3 but rather too small at k = 7), or a genuine
difference in the design sets or conventions behind the two estimates. Both figures sit inside the
shipped headline, so this is the weakest live item in the record.

> **Transferable principle.** *When two numbers disagree, first ask what each one is an estimate
> **of**, and only then ask whether the estimator is broken. But do not stop at "different
> estimands" — check that the two estimands are consistent with each other under the model you claim
> to be using. An estimand mismatch that is also an inconsistency is two errors, and finding the
> first one hides the second.*

---

## 7. Two figures in the record that disagree with each other

Recorded so that a course built on this material does not propagate them.

**The k = 2 spread reliability is 0.599 in one place and 0.591 in six others.** The canonical results
file `results/ensemble_power.md:15` says **0.599**; the value **0.591** appears in
`docs/sessions/2026-09-20-spread-is-not-a-mean-and-the-rubric-has-a-ceiling.md:96`,
`scripts/39_ensemble_wide_fold.py:11`, `results/prereg_2026-09-20_ensemble_wide.md:39`,
`results/ensemble_wide.md:22`, `scripts/42_analyse_tonight.py:497`, and `LEARNINGS.md`. The k = 3
value is **0.792** in the results file and the session doc's main table, but **0.813** in
`scripts/39_ensemble_wide_fold.py:12` and the session doc's outlier table at line 121.

I can partly reconstruct the cause, and it is instructive. `results/ensemble_power.md`'s table is
internally consistent under `r = B/(B + s_k)` with between-design variance **B = 0.09372 Å²** and its
own fitted sampling variances `s_k`:

```
k=2:  0.09372 / (0.09372 + 0.06280)  =  0.5988      → 0.599 ✓
k=3:  0.09372 / (0.09372 + 0.02465)  =  0.7918      → 0.792 ✓
k=5:  0.09372 / (0.09372 + 0.00618)  =  0.9381      → 0.938 ✓
```

The competing 0.591 falls out of the **same** k = 2 sampling variance with a **different**
between-design variance, `B = 0.0907 Å²` — the value the session doc uses in its outlier analysis:

```
0.0907 / (0.0907 + 0.06280)  =  0.5909      → 0.591 ✓
```

So the disagreement is in the *signal* term, not the noise term: two slightly different estimates of
between-design variance for the same 20 designs. The 0.813 needs a third combination — `B = 0.0907`
with the sampling variance modelled as `V₁/C(k,2) = 0.0628/3 = 0.020933` rather than fitted:

```
0.0907 / (0.0907 + 0.020933)  =  0.8125     → 0.813 ✓
```

Note the consequence, which no one in the project seems to have spotted: the triple most often quoted
downstream, **0.591 / 0.813 / 0.938 at k = 2/3/5**, is a *mixture* of the two estimates — the first
two from `B = 0.0907`, the third from `B = 0.09372`. No decision turns on it (the attenuation
ceilings are `√0.591 = 0.769` and `√0.599 = 0.774`, indistinguishable in practice), but it is exactly
the convention drift the project's own rule about divergent constants exists to prevent, and it is
catalogued in [the failure catalogue](08-what-broke.md) alongside the other bookkeeping defects.

One further trap in that table, which the project does name: **the k = 7 row reads 1.000, and it is a
tautology.** Truth was *defined* as the 7-seed spread, so a 7-seed estimate has zero error against it
by construction. Modelling the sampling variance as `V₁/C(k,2)` and subtracting gives a corrected
k = 7 reliability of **0.968**. As the file puts it, *"a table with a 1.000 in it invites a reader to
believe something no data can support."*

---

## What to take away

1. **`observed = true + error` implies `σ²_obs = σ²_true + σ²_noise`, and reliability is the ratio
   `r = σ²_true/σ²_obs`.** Everything else in this chapter is that identity rearranged. Learn to
   estimate it two ways — `1 − within/observed` from replicates, and `(F−1)/(F+m−1)` from an ANOVA —
   and to notice when the estimate comes out negative, because a clamped 0.000 is hiding the stronger
   statement.
2. **ICC ≈ 0 means your ranking is a lottery.** Measured: `contacts` 0.003, `cdr_sasa` −0.204 clamped
   to 0.000. And ICC is only half the check — **five of eight** rubric metrics here were constants by
   *range* rather than by noise, so an eight-metric harness ranked on three.
3. **Spearman–Brown, `r_k = k·r₁/(1 + (k−1)·r₁)`, prices replicates in reliability.** Eighteen Fv
   folds to equal one Fab fold. Use its inverse to answer "how many seeds do I need", and check the
   prediction against measurement: here the measured 3-seed values came in **below** prediction
   (0.780 vs 0.819; 0.849 vs 0.869), which is evidence of correlated seed noise and mildly undercuts
   the i.i.d. assumption downstream.
4. **Attenuation, `ρ_obs ≈ ρ_true·√(r₁r₂)`, sets a ceiling you cannot design your way past.** Report
   observed and corrected as a pair; **never** quote the corrected value alone. A corrected 0.612
   straddling a 0.60 gate is not a pass.
5. **Reliability belongs to a measurement *and a population*, and shortlisting is the operation that
   destroys it.** Measured: 0.849 predicted from the 239-pool, **0.629** on the top-20 whose signal sd
   is 0.290 against the pool's 0.562. The noise behaved exactly as forecast; the signal was removed by
   the selection step itself. There is no way around this: it is arithmetic, not a defect.
6. **Diagnose numerical disagreements by estimand first.** 0.629 is a 7-seed-mean reliability;
   0.276/0.296 are single-seed. They are different quantities — and they are still mutually
   inconsistent under Spearman–Brown (r₁ = 0.296 ⇒ r₇ = 0.746; r₇ = 0.629 ⇒ r₁ = 0.195). Finding the
   first error is not permission to stop looking for the second.

Next: [what would have to be true for me to be wrong](05-experiment-design.md), which takes the
reliability numbers established here and asks what experiment could actually overturn a claim —
including the four nulls this campaign published and then reversed.
