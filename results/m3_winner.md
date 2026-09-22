# M3 — the winner

`scripts/35_winner.py`. 20 shortlisted designs, [7] Boltz seeds each.

## 1. Does the noise actually average down?

The shortlist was sized (20 designs x 7 seeds, over 60 x 3) by assuming seed noise is i.i.d. and shrinks as 1/sqrt(s). That was measured on three seeds and extrapolated. Seven seeds test it.

| quantity | value |
|---|---|
| within-design sd over 3 seeds (40-pool, surrogate pts) | 0.529 |
| within-design sd over 7 seeds (this shortlist) | **0.467** |
| ratio | **0.88x** |

The two agree, so the i.i.d. assumption holds well enough at s=7 and the shortlist sizing rested on a sound premise.

Between-design sd of the 7-seed means: **0.290**; noise sd of a 7-seed mean: 0.176; **reliability = 0.629**.

## 2. The ranking

| rank | design | arm T | arom | surrogate (mean ± sd) | DockQ (mean ± sd) |
|---|---|---|---|---|---|
| 1 | `mpnn_T0.5_s104_036` | 0.5 | 2 | 95.117 ± 0.210 | 0.747 ± 0.011 |
| 2 | `mpnn_T0.5_s104_053` | 0.5 | 2 | 95.095 ± 0.125 | 0.750 ± 0.010 |
| 3 | `mpnn_T0.5_s104_057` | 0.5 | 3 | 95.057 ± 0.161 | 0.681 ± 0.013 |
| 4 | `mpnn_T0.5_s104_047` | 0.5 | 1 | 94.974 ± 0.272 | 0.737 ± 0.013 |
| 5 | `mpnn_T0.5_s104_011` | 0.5 | 2 | 94.937 ± 0.565 | 0.723 ± 0.016 |
| 6 | `mpnn_T0.1_s101_022` | 0.1 | 2 | 94.892 ± 0.186 | 0.721 ± 0.013 |
| 7 | `mpnn_T0.3_s103_046` | 0.3 | 1 | 94.865 ± 0.446 | 0.720 ± 0.009 |
| 8 | `mpnn_T0.2_s102_035` | 0.2 | 1 | 94.834 ± 0.348 | 0.737 ± 0.017 |
| 9 | `mpnn_T0.2_s102_032` | 0.2 | 1 | 94.828 ± 0.492 | 0.742 ± 0.011 |
| 10 | `mpnn_T0.2_s102_053` | 0.2 | 3 | 94.708 ± 0.473 | 0.741 ± 0.013 |

## 3. The winner, discounted

**`mpnn_T0.5_s104_036`** — arm T=0.5, aromatic count 2, CDR-H3 `ALRPRDVDRGFYK`, identity 38.5%.

| quantity | value |
|---|---|
| raw 7-seed mean surrogate | 95.117 |
| shortlist mean | 94.703 |
| reliability used for shrinkage | 0.629 |
| **winner's-curse discount** | **−0.153** |
| **HEADLINE: discounted surrogate** | **94.963** |
| margin over 2nd place | 0.022 (0.1 noise sd) |

> The gap to second place is **smaller than one standard error of the 7-seed mean**. The ordering at the top is not resolved: this is *a* best design, not *the* best, and a different seed set could reorder the top two.

## 4. Fresh-seed re-score

Seed 23, used nowhere in selection — the only estimate not contaminated by having been selected on.

| quantity | value |
|---|---|
| surrogate, selection seeds (mean of 7) | 95.117 |
| surrogate, fresh seed 23 | **94.962** |
| shrinkage-predicted value | 94.963 |
| fresh-seed DockQ | 0.749 |

The fresh seed came in -0.155 against the selection mean and -0.001 against the shrinkage prediction.

> **This is not a validation, and calling it one was wrong (corrected 2026-09-20).** The fresh estimate is ONE fold, sd **0.467**. The shrunk prediction misses by 0.03 sd and the *unshrunk* one by 0.33 sd — both inside one standard error, so this measurement cannot distinguish a 0.153-point discount from no discount. Landing within +/-0.0005 of any prediction is a 1-in-1200 event. Discriminating the discount at 80% power needs about **73 fresh seeds**. The estimator is sound on theory; this number is a coincidence.

## 5. The winner's CDR-H3 ensemble

Pairwise CA deviation over CDR-H3 (positions 96–108) after superposing on the **framework**, across 7 seeds:

| quantity | value |
|---|---|
| ensemble RMSD | **0.52 Å** |
| max pairwise deviation | 1.33 Å |

For context the 40-design discovery pool spanned 0.28–2.23 Å, median 0.71 Å, so this winner is tighter than the median design there. Ensemble spread is reported as characterisation only — it was dropped from selection on 2026-09-18 because CDR-H3 aromatic content explains it away entirely.

## 6. The reported rubric score

Ranking used the continuous surrogate; the rubric composite is what the organisers would recompute, so it is what gets reported.

```
metric                 raw  band     score  margin
ipsae                0.856  good       9.5  +128%
dockq                0.747  medium     7.0  +91%
dg                 -12.700  good       9.5  +112%
contacts            97.000  good       9.5  +580%
iface_plddt         89.984  good       9.5  +167%
cdr_sasa          1586.657  good       9.5  +382%
netsolp              0.585  medium     7.0  +42%
cdrh3_identity      38.500  good       9.5  +226%
```

`final` = **87.5**, viable = **True**.

