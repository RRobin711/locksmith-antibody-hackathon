# Specificity controls on the named design

`scripts/37_specificity_fold.py` + `42_analyse_tonight.py`. Design **`mpnn_T0.5_s104_036`**, unchanged, folded against five antigens at three fresh seeds (31–33) each.
Pre-registered in [the specificity pre-registration](prereg_2026-09-20_specificity.md) before any fold ran.

| antigen | role | len | ipSAE | ΔG (kcal/mol) | contacts | iface pLDDT |
|---|---|---|---|---|---|---|
| `pd1` | PD-1 (positive control) | 113 | **0.847** ± 0.013 | -12.5 ± 0.1 | 94 ± 4 | 90.1 ± 0.4 |
| `pdl1` | PD-L1 IgV (functional decoy) | 113 | **0.000** ± 0.000 | -11.6 ± 1.5 | 74 ± 7 | 81.4 ± 2.1 |
| `tim3` | TIM-3 (Ig V-set decoy) | 110 | **0.568** ± 0.086 | -14.1 ± 0.3 | 97 ± 8 | 85.6 ± 0.3 |
| `ulbp6` | ULBP6 (MHC-I-like decoy) | 172 | **0.007** ± 0.007 | -11.8 ± 1.2 | 72 ± 12 | 81.6 ± 2.0 |
| `pcrv` | PcrV (bacterial decoy) | 134 | **0.421** ± 0.305 | -9.2 ± 0.1 | 47 ± 4 | 80.2 ± 0.5 |

## Verdict against the pre-registered thresholds

**H2 — positive control reproduces (ipSAE ≥ 0.80):** PD-1 at fresh seeds scores **0.847** → PASS.

| decoy | ipSAE per seed | mean | seeds ≥0.60 **and** ΔG ≤−10 | gap to PD-1 | >0.20? |
|---|---|---|---|---|---|
| `pdl1` | 0.000, 0.000, 0.000 | 0.000 | **0 / 3** | +0.847 | yes |
| `tim3` | 0.624, 0.612, 0.469 | 0.568 | **2 / 3** ⚠ | +0.278 | yes |
| `ulbp6` | 0.000, 0.010, 0.012 | 0.007 | **0 / 3** | +0.839 | yes |
| `pcrv` | 0.711, 0.103, 0.449 | 0.421 | **0 / 3** | +0.426 | yes |

**PRE-DECLARED FAILURE CONDITION TRIGGERED** on `tim3` (2/3 seeds) — ipSAE ≥ 0.60 with ΔG ≤ −10 on at least 2 of 3 seeds.

Per the pre-registration, **this design does not go into a pitch as a PD-1 binder without that sentence attached.** Note the arm *mean* would have passed; the rule was written per-seed before the data existed and is applied as written.

### Reference controls on TIM-3 — antigen fixed, antibody varied

**Exploratory, not pre-registered** — added after seeing the panel. The panel varies the antigen with the antibody fixed; this varies the antibody with the antigen fixed, which is the only way to tell a property of the design from a property of the predictor.

| antibody | role | n | ipSAE per seed | mean | ΔG mean |
|---|---|---|---|---|---|
| **our design** | `mpnn_T0.5_s104_036` | **8** | 0.335, 0.449, 0.469, 0.500, 0.504, 0.612, 0.613, 0.624 | **0.513** | — |
| `pembro` | pembrolizumab (negative reference) | 8 | 0.015, 0.189, 0.256, 0.322, 0.371, 0.395, 0.458, 0.641 | **0.331** | -14.0 |
| `8tbbfab` | 8TBB Fab (positive reference: a real TIM-3 binder) | 3 | 0.614, 0.684, 0.747 | **0.682** | -11.5 |

Difference (ours − pembrolizumab): **+0.182**, bootstrap 95% CI **[+0.045, +0.320]**, Mann–Whitney p = **0.038** (n=8 vs 8). Report the interval, not a branch: the point estimate sits about one standard error from the threshold that would reverse the reading.

**Reading: the design is TIM-3-reactive relative to a specific antibody.** Pembrolizumab 0.331 against our 0.513, real binder 0.682. The pre-declared failure condition stands and travels with the design.

## What this does and does not license

A decoy scoring high is strong evidence of a problem; a decoy scoring low is **weak** evidence of its absence, because a predictor that is unreliable at novel placement scores novel pairings low whether or not they would bind. This predictor's measured post-cutoff median DockQ is 0.291. So the supported sentence is *no evidence of gross promiscuity, from a test that could only have detected gross promiscuity* — not *the design is specific*.

The positive-decoy control named as missing in the pre-registration **was run** (see the reference table above), so that gap is closed.

