# Reviewing M3's assumptions against folds already paid for

No new folds. 40 designs x 3 Boltz seeds from [the ensemble validation pool](ensemble_validation.md), re-interrogated to test what the M3 campaign plan assumes. Reproduce with `scripts/27_review_m3_assumptions.py`.

Every number below was computed on the same pool that *discovered* the aromatic effect, so none of it is out-of-sample evidence FOR that effect. It is evidence about the effect's **shape**, its **competitors**, and whether the planned **decision rule** can act on it — which is exactly what a campaign design needs and what a single correlation coefficient cannot supply.

## 1. The filter improves the mean; it does not improve the maximum

A pre-fold filter's job is to let a fixed fold budget reach a better design. The comparison that tests this is **not** filtered-vs-unfiltered — throwing away half a pool keeps the best design half the time by luck alone. The comparison is filtered-vs-**a random subset of the same size**, which costs nothing to run.

Random subsets drawn 20,000 times without replacement.

| keep | statistic | filtered | random mean | P(random >= filtered) |
|---|---|---|---|---|
| 40% (n=16) | **max** DockQ | 0.7467 | 0.7426 | **0.399** |
| 40% (n=16) | mean DockQ | 0.7163 | 0.7027 | **0.0223** |
| 50% (n=20) | **max** DockQ | 0.7467 | 0.7435 | **0.499** |
| 50% (n=20) | mean DockQ | 0.7142 | 0.7026 | **0.0172** |
| 60% (n=24) | **max** DockQ | 0.7467 | 0.7443 | **0.600** |
| 60% (n=24) | mean DockQ | 0.7110 | 0.7026 | **0.0335** |

**Read the max row first.** At every retention level the filtered subset's best design is no better than a random subset's — p = 0.40, 0.50, 0.60, i.e. indistinguishable from chance. The filter never discards the pool maximum, but neither does random pruning, often enough that keeping it proves nothing.

The mean row is where the filter earns its place: p = 0.022, 0.017, 0.033. Filtering raises the *typical* quality of what gets folded by +0.0137 DockQ at 40% retention — about **one seed standard deviation** (0.018).

> **Consequence for G3.** A criterion worded around *top-end* quality is aimed at the
> one thing this filter demonstrably does not do, and would pass or fail for reasons
> unrelated to the filter. A criterion worded around *mean* quality — equivalently,
> shortlist yield per fold — tests something the data can actually support.

One more thing the table exposes: at 40% retention the filter **cannot be applied cleanly at all**. Seventeen designs share aromatic count 2, so a rule that keeps 16 of 40 has to split that tier arbitrarily, and the reported figure depends on the sort's tie-breaking. A percentile filter over a 4-valued feature is not a well-defined rule.

## 2. The aromatic effect is a step at <=1, not a gradient

CDR-H3 is 13 residues throughout this pool, so `aromatic_frac` is a **4-level count** and `aromatic_frac` and aromatic *count* are the same variable (both rho = -0.536 against DockQ).

| aromatics in CDR-H3 | n | mean 3-seed DockQ | sd | max |
|---|---|---|---|---|
| 1 | 9 | **0.7326** | 0.0069 | 0.7417 |
| 2 | 17 | **0.7016** | 0.0356 | 0.7467 |
| 3 | 13 | **0.6889** | 0.0316 | 0.7307 |
| 4 | 1 | **0.6277** | — | 0.6277 |

Kruskal–Wallis over the three populated levels: H = 10.66, p = 0.0048.

**Leverage check.** The top level holds a single design. Dropping it: rho -0.536 -> **-0.497** (p = 0.0013, n = 39). The effect is not an artefact of that one point — which is worth stating, because this project has already been bitten once by an R^2 carried entirely by two anchor designs.

But the structure is a **step, not a slope**: designs with <=1 aromatic average 0.7326 with sd 0.0069, against 0.6939 (sd 0.0356) for the rest. The low-aromatic group is not just better, it is **5.1x tighter** — it contains no failures rather than better successes.

Only **9/40 (22%)** of the pool clears count <=1. A *percentile* filter ("keep the least-aromatic 40%") therefore admits a large majority of count-2 designs and dilutes the very effect it is selecting on. It is also **not portable across generation regimes**: the same percentile maps to a different absolute aromatic content at every MPNN temperature, which would confound the planned temperature arms with the filter itself. Specify the threshold as an **absolute count**.

## 3. The selection key is `final`, and nobody had measured its reliability

`config/metrics.yaml` sets `selection_key: final`. The measured 0.727 reliability that M3's multi-seeding is justified by is **DockQ's**, not `final`'s. They are not the same number, because banding is a step function and a metric sitting near a band edge flips band on seed noise.

| quantity | value |
|---|---|
| designs whose single-seed `final` changes across 3 seeds | **22/40 (55%)** |
| within-design sd of single-seed `final` | 0.873 points |
| between-design sd of 3-seed mean `final` | 1.486 points |
| single-seed reliability of `final` | **0.602** |
| 3-seed-mean reliability of `final` | **0.780** |
| distinct values of `final` across the pool | [82.5, 83.33, 84.17, 85.0, 85.83, 86.67, 87.5] |

More than half the pool changes its rubric score depending on which Boltz seed you folded it with, and the sub-scores doing the flipping are **ipSAE** and **dG** — both sitting near a band edge. Single-seed reliability of the key we actually rank on is **0.602**, materially worse than DockQ's 0.727; even the 3-seed mean reaches only **0.780**.

Worse for a wide campaign: `final` takes **three distinct values** across 40 designs. Scaling to 200 will not add resolution, because banding is what removes it. The top tier will be a large tie broken by DockQ at reliability 0.727 over a range of 0.119 — which is how you select noise.

> **Consequence for M3.** Ranking on the banded composite discards precisely the
> within-band information that distinguishes candidates. Rank internally on a
> continuous surrogate and keep `final` as the reported score; and prefer, among
> ties, the design furthest from a band edge — the project already has this idea as
> `margin_fraction` for gates, and band edges deserve it too.

## 4. A second free feature was missed, and it is nearly as strong

The pre-registration tested six pre-fold features and found one. It did not test the rubric metric that is *already* computed before folding: **CDR-H3 identity to the parent**.

| relationship | Spearman | p |
|---|---|---|
| aromatic count -> DockQ | -0.536 | 0.0004 |
| CDR-H3 identity -> DockQ | +0.505 | 0.0009 |
| aromatic count -> CDR-H3 identity | +0.085 | 0.6013 |
| partial: aromatic -> DockQ, controlling identity | **-0.674** | 0.0000 |
| partial: identity -> DockQ, controlling aromatic | **+0.655** | 0.0000 |

The two features are **uncorrelated with each other** (rho = +0.085) and each *strengthens* when the other is controlled — mutual suppression. A combined rank score reaches rho = **+0.781** (p = 0.00000) against 3-seed mean DockQ, far above either alone.

| keep 40% by | mean DockQ | max | top-5 retained | mean identity |
|---|---|---|---|---|
| aromatic only | 0.7163 | 0.7467 | 4/5 | 30.8% |
| identity only | 0.7184 | 0.7467 | 4/5 | 34.2% |
| combined | 0.7261 | 0.7467 | 5/5 | 34.2% |
| (unfiltered pool) | 0.7026 | 0.7467 | 5/5 | 31.4% |

**And here is the catch that makes this a trade, not a free win.** CDR-H3 identity is the *novelty* axis, which `config/metrics.yaml` prices at **2x** a binding metric, and it runs the wrong way: higher identity predicts better DockQ but scores **worse** on novelty. Selecting on it buys binding with novelty points.

In *this* pool the trade happens to be invisible — identity -> `final` is rho = +0.032 (p = 0.846), because all 3 distinct identity values ([23.1, 30.8, 38.5]%) fall in a single novelty band. Aromatic count, by contrast, predicts `final` at rho = **-0.524** (p = 0.0005) — *better* than it predicts DockQ. **Aromatic content is the feature to filter on; identity is a feature to hold constant**, not to optimise, or the campaign will quietly trade away the highest-priced axis on the rubric.

## 5. What this pool cannot tell anyone, and why M3's arms are right to exist

| dimension | distinct values in 40 designs |
|---|---|
| CDR-H3 length | [13] |
| MPNN temperature | [0.1] |
| CDR-H3 identity | [23.1, 30.8, 38.5] |
| aromatic count | [1, 2, 3, 4] |
| `final` | [82.5, 83.33, 84.17, 85.0, 85.83, 86.67, 87.5] |

Forty designs, and the pool is four aromatic levels x three identity levels x one length x one temperature. This is a **densely sampled single operating point**, not a design space. Every conclusion above — including the aromatic effect — is conditional on that point. Varying temperature is the correct primary axis for M3 precisely because it is the only cheap way to find out whether any of this survives elsewhere.

