# The CDR-H3 ensemble, widened from 40 designs to the pool

`scripts/39_ensemble_wide_fold.py` + `42_analyse_tonight.py`. Pre-registered in [[prereg_2026-09-20_ensemble_wide|the ensemble pre-registration]]; sizing argued in [[ensemble_power|the seeds-versus-designs power analysis]], which is why this is a wide shallow design rather than the deep narrow one originally proposed.

**n = 239 designs**, 155 at k=2 and 84 at k≥3, spanning 4 temperature arms ({0.1: 60, 0.2: 59, 0.3: 60, 0.5: 60}).

Estimator: RMS Cα deviation over CDR-H3 (heavy 96–108) across all C(k,2) seed pairs, each superposed on the **framework**. Reference-free — **not comparable** to the 0.33–1.45 Å quoted on 2026-09-18, which measured every seed against `seed[0]`.

## 1. How much does CDR-H3 actually move, and is the variation real?

| quantity | value |
|---|---|
| spread, range | 0.15 – 2.58 Å (17.5×) |
| spread, median | 0.45 Å |
| largest single pairwise deviation | 2.58 Å |
| observed variance of the spread estimate | 0.20000 Å² |
| sampling variance of one pair (V1, from the 20×7 shortlist) | 0.06280 Å² |
| **between-design variance, identified** | **0.13720 Å²** |
| **reliability of a k=2 spread** | **0.686** |
| attenuation √r applied to every ρ below | **0.828** |

**H5 — is the between-design variation carried by one outlier?** On the 20-design shortlist, dropping one design at 1.77 Å moved k=2 reliability from 0.591 to 0.265. Here, over the full pool:

- `mpnn_T0.5_s104_026` — 2.58 Å (T=0.5, aromatics 2, loop pLDDT 91.1)
- `mpnn_T0.5_s104_060` — 2.24 Å (T=0.5, aromatics 2, loop pLDDT 85.1)
- `mpnn_T0.2_s102_022` — 2.09 Å (T=0.2, aromatics 2, loop pLDDT 93.1)

Dropping the top 3, between-design variance goes 0.13720 → **0.10264 Å²** and reliability 0.686 → **0.620**. The variation survives, so it is a distribution, not an artefact of a few designs.

## 2. Does confidence see the heterogeneity?

Both pLDDT columns are read from the **seed-1** fold — the single structure a user would actually have — so this asks the practical question: does the confidence you get from one fold predict how much the loop moves between folds?

| predictor of spread | ρ observed | 95% CI (bootstrap) | p | ρ disattenuated |
|---|---|---|---|---|
| **H1** mean loop pLDDT (seed 1) | -0.432 | [-0.529, -0.321] | 2.9e-12 | -0.521 |
| **H2** interface pLDDT (seed 1) | -0.344 | [-0.455, -0.221] | 4.7e-08 | -0.416 |
| **H4** CDR-H3 aromatic count | +0.197 | [+0.080, +0.308] | 0.0022 | +0.238 |
| loop pLDDT sd across seeds | +0.454 | [+0.336, +0.562] | 1.4e-13 | +0.549 |
| ipSAE (seed 1) | -0.190 | [-0.310, -0.067] | 0.0032 | -0.230 |
| DockQ (seed 1) | -0.340 | [-0.449, -0.223] | 7e-08 | -0.411 |

**A null here is a bound, not an absence.** At n=239 and attenuation 0.828, the smallest true effect detectable at 80% power (α=0.05) is ρ_true ≈ **0.218**. Any ρ reported as null means *no effect larger than that*, and nothing stronger.

## 3. Does it hold across sampling temperature? (H3)

| arm | n | ρ(iface pLDDT, spread) | ρ(loop pLDDT, spread) | ρ(aromatics, spread) | median spread |
|---|---|---|---|---|---|
| T=0.1 | 60 | -0.411 | -0.407 | +0.455 | 0.41 Å |
| T=0.2 | 59 | -0.147 | -0.253 | +0.079 | 0.39 Å |
| T=0.3 | 60 | -0.455 | -0.440 | +0.239 | 0.45 Å |
| T=0.5 | 60 | -0.379 | -0.567 | +0.155 | 0.57 Å |

## 4. Is interface pLDDT just reading aromatics? (H4)

- interface pLDDT → spread, controlling for aromatic count: **-0.293** (p=4.4e-06)
- aromatic count → spread, controlling for interface pLDDT: **+0.056** (p=0.39)

The 2026-09-18 pattern was that a *free sequence feature* explained away a *three-fold measurement*. Whichever survives here is the one worth carrying.

## 5. The claim boundary

Spread across diffusion seeds measures **how well determined the prediction is** — a property of Boltz, not of the molecule. There is no experimental structure of any design and no binding data. The supported sentence is *the predictor does not place this loop consistently*; *this loop is flexible* is not supported by anything here.

