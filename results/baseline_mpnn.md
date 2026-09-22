# Baseline 1 — plain ProteinMPNN at defaults

20 designs, ProteinMPNN `v_48_020`, temperature 0.1, seed 37, over the 29 IMGT heavy CDR positions of pembrolizumab (H1 8, H2 8, H3 13). Light chain and PD-1 held fixed as context. **No filtering, no reranking** — every design generated was folded as a Fab, scored on all eight metrics and gated. This is the control the funnel must beat.

## 1. Headline

- **20 of 20 designs clear all eight gates** (100%). 0 undetermined.
- Fold success: **20/20**, zero failures.
- Best composite score among viable: **87.5**

## 2. Which gates do the rejecting

| gate | designs failed | cutoff | direction |
|---|---|---|---|
| *(none — every design cleared every gate)* | | | |

## 3. Distributions

| metric | min | median | max | cutoff | good |
|---|---|---|---|---|---|
| `dockq` | 0.650 | 0.728 | 0.754 | 0.23 | 0.8 |
| `ipsae` | 0.765 | 0.809 | 0.862 | 0.6 | 0.8 |
| `dg` | -13.400 | -12.150 | -10.400 | -6.0 | -12.0 |
| `contacts` | 96.000 | 103.000 | 116.000 | 10.0 | 25.0 |
| `iface_plddt` | 84.000 | 91.350 | 93.850 | 65.0 | 80.0 |
| `cdr_sasa` | 1413.300 | 1528.550 | 1574.200 | 250.0 | 600.0 |
| `netsolp` | 0.567 | 0.585 | 0.597 | 0.5 | 0.7 |
| `cdrh3_identity` | 23.100 | 30.800 | 38.500 | 95.0 | 70.0 |

## 4. Where these designs sit on the panel's ipSAE↔DockQ curve

Panel Fab curve: `ipSAE = 0.364 + 0.566 × DockQ`, residual sd 0.088, n=14. These designs are perturbations of a **memorised** complex, so this tests the level-shift question from the post-cutoff work for free.

- mean residual **+0.039** (SE 0.031) → **+1.3 SE**
- residual sd **0.033** vs panel **0.088** (0.4×)
- Spearman ipSAE↔DockQ across the baseline: **+0.013** (p=0.957)

## 5. Ranked (via `select.rank`, gates structurally enforced)

20 viable, 0 gated out, 0 undetermined.

| rank | design | final | DockQ | ipSAE | CDR-H3 id % | ΔG |
|---|---|---|---|---|---|---|
| 1 | `mpnn_T0.1_s37_015` | **87.5** | 0.754 | 0.819 | 30.8 | -13.3 |
| 2 | `mpnn_T0.1_s37_003` | **87.5** | 0.753 | 0.839 | 30.8 | -13.3 |
| 3 | `mpnn_T0.1_s37_014` | **87.5** | 0.742 | 0.830 | 30.8 | -12.3 |
| 4 | `mpnn_T0.1_s37_004` | **87.5** | 0.740 | 0.801 | 30.8 | -13.4 |
| 5 | `mpnn_T0.1_s37_019` | **87.5** | 0.740 | 0.815 | 30.8 | -13.0 |
| 6 | `mpnn_T0.1_s37_010` | **87.5** | 0.720 | 0.862 | 30.8 | -12.5 |
| 7 | `mpnn_T0.1_s37_007` | **87.5** | 0.667 | 0.823 | 23.1 | -12.4 |
| 8 | `mpnn_T0.1_s37_001` | **87.5** | 0.650 | 0.833 | 30.8 | -13.4 |
| 9 | `mpnn_T0.1_s37_009` | **85.0** | 0.742 | 0.803 | 38.5 | -11.7 |
| 10 | `mpnn_T0.1_s37_020` | **85.0** | 0.740 | 0.813 | 38.5 | -11.1 |

## 6. What this baseline actually says

**Pembrolizumab itself scores 76.0 and is NON-VIABLE** — it fails the novelty gate at 100% CDR-H3 identity, by construction. Every one of these 20 designs outscores the licensed drug on the competition's own rubric (82.5–87.5). That is the rubric working as specified, not an anomaly: it is scoring novelty at 20% weight and a marketed antibody has none.

**The eight gates do not discriminate among backbone-constrained CDR redesigns.** A 100% hit rate is not a sign the designs are good; it is a sign the gates are not the binding constraint in this regime. ProteinMPNN redesigns sequence onto the *native backbone in complex*, so it selects residues that fit pembrolizumab's exact binding geometry, and Boltz then recovers approximately that pose. High DockQ is close to guaranteed by construction — which is precisely the caveat that DockQ-vs-5GGS measures **retention of the native binding mode**, not correctness.

**Consequence for M3: the funnel cannot demonstrate value through hit-rate against this baseline.** There is no headroom — naive MPNN already clears every gate. The funnel has to compete on composite score, on robustness under re-seeding, or in a regime where the gates actually bite (larger backbone perturbation, or Challenge 2's de novo placement, where the post-cutoff test already shows they do).

**The composite has coarse resolution: 3 distinct values across 20 designs.** Sub-scores are band midpoints, so `final` only moves when a metric crosses a band edge. Ranking on `final` therefore sorts designs into a few tiers and the **DockQ tiebreaker does the fine ordering within them** — which is the intended division of labour under `selection_key: final`, and worth stating because it means the tiebreaker is not decorative.

**The ipSAE level shift does NOT apply here.** On the five post-cutoff targets ipSAE sat ~0.19–0.28 *below* the panel curve. These designs sit **on** it (mean residual +0.039, +1.3 SE, and a *tighter* spread than the panel itself at 0.4×). The shift is a property of novel complexes, not of designs — so Challenge 1 gate thresholds calibrated on the panel transfer, and Challenge 2's would not.

**But ipSAE carries no ranking information here either**: Spearman ipSAE↔DockQ across the 20 designs is **+0.013** (p=0.957). This is the panel's §8 finding reproduced on real designs rather than on hand-mutants — within a narrow band of live designs, ipSAE and structural correctness are uncorrelated. It confirms the selection re-spec: report ipSAE, gate on it, do not rank on it.

## 7. Precision

At n=20 a viability rate of 100% carries a 95% CI of roughly [83%, 100%] (rule of three). The claim supported is 'naive MPNN clears these gates at a high rate', not 'always'. Twenty is enough to establish the referent and to show the gates do not bite; it is not enough to estimate a small failure rate.

