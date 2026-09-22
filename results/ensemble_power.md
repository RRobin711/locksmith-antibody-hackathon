# How many seeds does a CDR-H3 spread estimate need?

`scripts/36_ensemble_power.py` — **zero new folds**; computed from the 20 M3-shortlist
designs already folded at 7 seeds each. Run before committing GPU time to the ensemble
widening, because the answer decides the (designs x seeds) split.

Estimator: RMS CA deviation over CDR-H3 (heavy 96–108) across **all C(k,2) seed pairs**,
each pair superposed on the framework. Reference-free, unlike the 2026-09-18 estimator
which measured everything against seed[0]; numbers here are not comparable to that one.

Between-design variance of the 7-seed spread: **0.09372 Å²** (sd 0.306 Å over 20 designs).

| seeds k | sampling var of a k-seed spread | reliability | attenuation √r | folds per design |
|---|---|---|---|---|
| 2 | 0.06280 Å² | **0.599** | 0.774 | 1 new |
| 3 | 0.02465 Å² | **0.792** | 0.890 | 2 new |
| 4 | 0.01222 Å² | **0.885** | 0.941 | 3 new |
| 5 | 0.00618 Å² | **0.938** | 0.969 | 4 new |
| 6 | 0.00270 Å² | **0.972** | 0.986 | 5 new |
| 7 | 0.00000 Å² | **1.000** | 1.000 | 6 new |

`reliability = var_between / (var_between + sampling var)`. A correlation measured
against a k-seed spread is attenuated by √reliability, so a true ρ of 0.50 presents as
`0.50 × √r`.

## Allocation at a fixed fold budget

Seed 1 exists for all 239 pool designs, so `n` designs at `k` seeds costs `n(k-1)` new
folds. Power for a correlation is driven by the attenuated ρ and by n. Using Fisher-z,
`SE = 1/√(n-3)`, the detectable effect at 80% power / α=0.05 two-sided is
`z = 2.80/√(n-3)`, and we compare it against the attenuated true effect.

| budget (folds) | k | n | attenuation | ρ_true detectable at 80% power |
|---|---|---|---|---|
| 120 | 2 | 120 | 0.774 | 0.327 **←** |
| 120 | 3 | 60 | 0.890 | 0.399 |
| 120 | 4 | 40 | 0.941 | 0.458 |
| 120 | 5 | 30 | 0.969 | 0.508 |
| 120 | 6 | 24 | 0.986 | 0.553 |
| 120 | 7 | 20 | 1.000 | 0.591 |
| 200 | 2 | 200 | 0.774 | 0.254 **←** |
| 200 | 3 | 100 | 0.890 | 0.311 |
| 200 | 4 | 66 | 0.941 | 0.360 |
| 200 | 5 | 50 | 0.969 | 0.400 |
| 200 | 6 | 40 | 0.986 | 0.436 |
| 200 | 7 | 33 | 1.000 | 0.471 |
| 280 | 2 | 239 | 0.774 | 0.233 **←** |
| 280 | 3 | 140 | 0.890 | 0.264 |
| 280 | 4 | 93 | 0.941 | 0.305 |
| 280 | 5 | 70 | 0.969 | 0.340 |
| 280 | 6 | 56 | 0.986 | 0.372 |
| 280 | 7 | 46 | 1.000 | 0.403 |
| 360 | 2 | 239 | 0.774 | 0.233 **←** |
| 360 | 3 | 180 | 0.890 | 0.233 |
| 360 | 4 | 120 | 0.941 | 0.269 |
| 360 | 5 | 90 | 0.969 | 0.301 |
| 360 | 6 | 72 | 0.986 | 0.330 |
| 360 | 7 | 60 | 1.000 | 0.355 |

