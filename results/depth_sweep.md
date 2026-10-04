# Depth sweep: more sequences buy more viable designs at a constant rate, not better ones

**2026-09-24.** 144 folds, 18 backbones × 8 constrained sequences, zero failures, ~10.6 h
local. Pre-registered in [prereg_2026-09-23_depth_sweep](prereg_2026-09-23_depth_sweep.md).

## The curve, with per-stratum rates

Rates are **per stratum**, not cumulative. A cumulative rate at depth 8 includes stratum
A's own sequences, so comparing it to A is comparing a superset to its subset and is
guaranteed to look flatter than the data.

| | depth 1 | stratum A (seq 0–3) | stratum B (seq 4–7) |
|---|---|---|---|
| sequences | 18 | **72** | **72** |
| clearing ipSAE ≥ 0.60 | 2 | **4** | **8** |
| **per-stratum rate** | 11.1% | **5.6%** | **11.1%** |
| backbones with ≥1 clear (cumulative) | 2 / 18 | 4 / 18 | **8 / 18** |
| best overall | **0.859** | 0.854 | 0.854 |

Fisher exact, A vs B: **p = 0.367**. The two strata are not distinguishable; everything is
consistent with a single rate near **8.3%** (12/144).

## Are some backbones genuinely better? No.

Per-backbone clear counts over 8 draws each:

```
  0 clears : 10 backbones
  1 clear  :  5
  2 clears :  2
  3 clears :  1   (bb_17_0)
```

Two tests of whether that spread exceeds one shared rate:

| test | statistic | p | reading |
|---|---|---|---|
| Pearson chi-square dispersion | X² = 22.91 on 17 df, ratio **1.35** | **0.152** | no overdispersion |
| Beta-binomial LRT vs binomial | LR = 0.696, fitted ρ = **0.0446** | **0.202** | no overdispersion |

**Neither rejects a homogeneous binomial.** The fitted intra-backbone correlation is 0.045,
i.e. indistinguishable from zero.

> **CORRECTION, 2026-10-03 — the sentence that stood here is withdrawn.** It read: *"These
> 18 backbones are exchangeable: there are no good or bad ones in this pool, only draws."*
> That is evidence of absence drawn from an underpowered null. At n=18, k=8 and an 8.3%
> rate, this test has **23% power at the ρ it fitted** and reaches 80% only at **ρ ≈ 0.24**.
> Three of eighteen backbones being five times better than the rest would have been missed
> **three times in five**. What the data support is: *no backbone in this pool is detectably
> more than about four times the pool rate.* The statistics were right; the sentence was
> too strong, and it carried the spending decision below.
> See [the power analysis](heterogeneity_power.md) and [register §B11](retractions.md).
> Note the irony recorded there: **two claims are withdrawn further down this very file for
> exactly this error**, and the section immediately below names it as such.

## Two claims from the interim readout, both withdrawn

**"Depth rescues backbones."** Coverage went 2 → 4 → 8 of 18, which looked like depth
recovering backbones that had been written off. Under one shared rate of 8.3% the expected
coverage is **5.3 backbones at depth 4** and **9.0 at depth 8**, against observed **4** and
**8**. The growth is the order statistic behaving exactly as a flat rate predicts. Nothing
is being rescued; more draws simply find more of a constant population.

**"`bb_17_0` is a genuinely good backbone."** It produced 3 clears in 8 draws.
P(≥3 in 8 | p = 0.083) = **0.0235**, so across 18 backbones the expected number doing this
is **0.42** and we observed **1**. Entirely unremarkable. The claim does not survive and is
withdrawn.

Both errors have the same shape: reading structure off small counts without asking what a
structureless model predicts. That is the third time this project has done it — the aromatic
CDR-H3 filter and the n=8 conformational-heterogeneity null were the others.

## The ceiling did not move

| | best ipSAE | found at |
|---|---|---|
| depth 1 (18 sequences) | **0.859** (`bb_8_0`) | 1 sequence per backbone |
| depth 8 (144 sequences) | **0.854** (`bb_2_0`) | 8× the sampling |

**Eight times the sequences produced nothing better than the first pass found.** The
submitted design remains the best in the pool.

That is the number that decides the campaign. Depth buys **more viable designs at a
constant rate**; it does not buy **better** ones. A ninth sequence per backbone has the
same ~8% chance of clearing as the first, and no greater chance of exceeding 0.859.

## Decision

**No stratum C. No rental.**

Renting is justified only if the backbones themselves are the ceiling — and the
heterogeneity test says the backbones are not distinguishable from each other at all, so
"generate more backbones" and "draw more sequences" are the same experiment with different
price tags. One of them is free.

> **AMENDED 2026-10-03.** The decision stands; its stated justification does not. "Not
> distinguishable" was a 23%-power null (see the correction above), so this paragraph
> claimed support it never had. **The decision survives on the other leg of the argument** —
> eight times the sequences produced nothing better than the first pass found — which is a
> direct observation rather than a null. Two further corrections to the economics: stratum C
> costs **144 folds** and would take the heterogeneity test to **0.802** power, and the
> sequencing step was never rental-blocked at all ([register §B12](retractions.md)). At
> equal cost depth beats breadth here — 18×16 reaches 0.802 where 36×8 reaches 0.699 —
> because the estimator is a within-backbone dispersion, which needs replicates on the same
> backbone to exist. **So "more backbones" and "more sequences" are *not* the same
> experiment for this question**, which is the opposite of what this section asserts.

If a *panel* of viable designs is wanted rather than a single best one, depth delivers that
at a predictable ~8% per sequence, locally and for nothing. If a *better* design is wanted,
144 sequences say this pipeline's ceiling on these backbones is around 0.86, and reaching
past it needs a different generator, not more samples from this one.

## Cost

144 folds × ~166 s folding + ~95 s scoring ≈ **10.6 h**, one laptop GPU, $0. Sequence
generation was 314 s of CPU for all 18 backbones at depth 4.
