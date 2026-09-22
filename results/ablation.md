# Hotspot ablation on the named design

`scripts/38_ablation_fold.py` + `42_analyse_tonight.py`. Alanine substitutions in **`mpnn_T0.5_s104_036`**, two seeds each (41, 42), re-folded from scratch. Pre-registered in [[prereg_2026-09-20_ablation|the ablation pre-registration]], hotspots chosen from measured 5 Å heavy-atom contacts **before** folding.

Parent over 8 seeds: ipSAE **0.856**, ΔG **-12.6**, contacts **97**, DockQ **0.747**.

Δ columns are mutant − parent. Seed noise on the parent: DockQ sd 0.018, ipSAE sd ~0.02; the pre-registered bar for a real change is **3×** the relevant sd.

| mutant | kind | contacts removed | ipSAE (Δ) | ΔG (Δ) | contacts (Δ) | DockQ (Δ) |
|---|---|---|---|---|---|---|
| `D100A` | hotspot | 54 | 0.848 (-0.009) | -12.2 (+0.4) | 96 (-1) | 0.736 (-0.010) |
| `D102A` | hotspot | 31 | 0.839 (-0.017) | -12.6 (+0.1) | 96 (-1) | 0.738 (-0.009) |
| `N57A` | hotspot | 39 | 0.811 (-0.046) | -12.9 (-0.3) | 93 (-4) | 0.694 (-0.052) |
| `R97A` | hotspot | 30 | 0.826 (-0.030) | -12.2 (+0.4) | 99 (+2) | 0.621 (-0.126) |
| `R99A` | hotspot | 50 | 0.847 (-0.009) | -12.2 (+0.4) | 94 (-2) | 0.733 (-0.014) |
| `Y31A` | hotspot | 54 | 0.818 (-0.038) | -12.8 (-0.1) | 98 (+1) | 0.730 (-0.017) |
| `Y31A_R99A_D100A` | triple | 158 | 0.835 (-0.021) | -12.6 (-0.0) | 100 (+4) | 0.716 (-0.030) |
| `L96A` | control | 0 | 0.853 (-0.003) | -12.4 (+0.2) | 92 (-4) | 0.752 (+0.006) |
| `Y106A` | control | 0 | 0.851 (-0.006) | -12.4 (+0.2) | 96 (-0) | 0.739 (-0.008) |

## Verdict

Mean contact change: hotspots **-0.6**, negative controls **-2.1**.

**Controls degrade about as much as hotspots.** The readout is mutation-sensitive rather than interface-sensitive, so per the pre-registration this ablation is **uninformative** and must be reported as such rather than spun.

**H3 — ipSAE blunter than the physical metrics?** Mean relative change on hotspots: ipSAE **2.9%**, contacts **1.8%**. ipSAE moved at least as much as the physical metrics here, which cuts against the liveness-test reading; note it.

## Limit that must travel with this table

Boltz **re-predicts** every mutant from scratch, so a mutant is not the parent minus a side chain — the model may re-dock. This is the right question for a scored pipeline (*does the pipeline's verdict survive losing the hotspots*) but it is **not** an in-silico ΔΔG and must never be called one.

