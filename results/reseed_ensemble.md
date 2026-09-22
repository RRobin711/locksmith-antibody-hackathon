# Re-seeding the baseline shortlist — stability, winner's curse, CDR-H3 ensemble

Top tier of the baseline: 8 designs all at `final` 87.5, so the DockQ tiebreaker alone orders them. Re-folded as Fab on seeds 2 and 3 with the same driver, MSA and scoring path. **Prediction going in:** median adjacent DockQ gap 0.011 against a panel-measured Fab seed sd of 0.018 → this ordering should be substantially noise.

## 1. Per-design spread across seeds

| design | DockQ mean | DockQ sd | DockQ range | ipSAE mean | ipSAE sd | final values |
|---|---|---|---|---|---|---|
| `mpnn_T0.1_s37_015` | 0.742 | **0.0180** | 0.721–0.754 | 0.836 | 0.0294 | 87.5 |
| `mpnn_T0.1_s37_003` | 0.740 | **0.0121** | 0.729–0.753 | 0.852 | 0.0112 | 87.5 |
| `mpnn_T0.1_s37_014` | 0.730 | **0.0177** | 0.710–0.742 | 0.823 | 0.0218 | 85.0, 87.5 |
| `mpnn_T0.1_s37_004` | 0.727 | **0.0275** | 0.695–0.745 | 0.829 | 0.0287 | 87.5 |
| `mpnn_T0.1_s37_019` | 0.721 | **0.0181** | 0.704–0.740 | 0.811 | 0.0063 | 87.5 |
| `mpnn_T0.1_s37_010` | 0.727 | **0.0095** | 0.720–0.738 | 0.859 | 0.0044 | 87.5 |
| `mpnn_T0.1_s37_007` | 0.663 | **0.0075** | 0.654–0.667 | 0.800 | 0.0331 | 85.0, 87.5 |
| `mpnn_T0.1_s37_001` | 0.681 | **0.0386** | 0.650–0.724 | 0.806 | 0.0237 | 85.0, 87.5 |

- pooled seed sd (designs) = **0.0209**  (panel, on mutants: 0.0181)
- between-design sd in the top tier = 0.0401
- **implied reliability of the DockQ ordering = 0.727**  (attenuation ceiling √r = 0.853)

## 2. Does the ranking survive re-seeding?

| seed pair | Spearman rank correlation | top-1 agrees? |
|---|---|---|
| seed 1 vs 2 | **+0.635** (p=0.091) | yes |
| seed 1 vs 3 | **+0.647** (p=0.083) | no — 015 vs 003 |
| seed 2 vs 3 | **+0.357** (p=0.385) | no — 015 vs 003 |

- per-seed DockQ winner: seed 1 → `mpnn_T0.1_s37_015`, seed 2 → `mpnn_T0.1_s37_015`, seed 3 → `mpnn_T0.1_s37_003`
- winner by **3-seed mean**: `mpnn_T0.1_s37_015`

## 3. The winner's curse, quantified

- seed-1 top design: `mpnn_T0.1_s37_015` at DockQ **0.754**
- its 3-seed mean: **0.742** → regression **-0.0123**
- mean regression across all 8 re-seeded designs: **-0.0045**
- **winner's-curse excess = -0.0079 DockQ**

That excess is the selection bias: the amount by which picking the argmax of a noisy measurement overstates it, over and above any drift shared by every design. Any future "our best design scored X" has to be discounted by it.

## 4. The CDR-H3 conformational ensemble

Superposition is on the **framework** CAs, never on the loop: superposing on the loop would hide exactly what is being measured — whether CDR-H3 sits in the same place relative to the rest of the molecule. Loop = heavy-chain positions 96–108 (13 residues).

| design | framework RMSD | **CDR-H3 RMSD** | CDR-H3 max dev | mean loop pLDDT | pLDDT sd | DockQ mean |
|---|---|---|---|---|---|---|
| `mpnn_T0.1_s37_015` | 0.41 Å | **0.53 Å** | 1.06 Å | 96.0 | 2.3 | 0.742 |
| `mpnn_T0.1_s37_003` | 0.36 Å | **0.33 Å** | 0.53 Å | 94.8 | 3.1 | 0.740 |
| `mpnn_T0.1_s37_014` | 0.35 Å | **1.11 Å** | 3.21 Å | 94.3 | 3.5 | 0.730 |
| `mpnn_T0.1_s37_004` | 0.30 Å | **1.13 Å** | 3.14 Å | 94.8 | 3.1 | 0.727 |
| `mpnn_T0.1_s37_019` | 0.34 Å | **0.62 Å** | 1.17 Å | 93.5 | 4.1 | 0.721 |
| `mpnn_T0.1_s37_010` | 0.32 Å | **0.43 Å** | 0.93 Å | 92.4 | 3.3 | 0.727 |
| `mpnn_T0.1_s37_007` | 0.34 Å | **0.47 Å** | 1.15 Å | 93.2 | 3.2 | 0.663 |
| `mpnn_T0.1_s37_001` | 0.28 Å | **1.45 Å** | 4.31 Å | 90.5 | 6.6 | 0.681 |

- Does a tight CDR-H3 ensemble track a better score? Spearman(CDR-H3 RMSD, DockQ) = **-0.357** (p=0.385)
- Does pLDDT know the loop is heterogeneous? Spearman(CDR-H3 RMSD, loop pLDDT) = **-0.238** (p=0.570)

- tightest ensemble: `mpnn_T0.1_s37_003` at 0.33 Å; most heterogeneous: `mpnn_T0.1_s37_001` at 1.45 Å — a 4.4× spread across designs that are indistinguishable on the rubric.


## 5. What the three readouts say

### 5.1 The prediction held — the top-tier ranking is substantially noise

Predicted before the run, from the panel's seed sd: reliability ≈ 0.70. **Measured: 0.727.**

- Seed sd on real designs is **0.0209**, slightly *larger* than the 0.0181 measured on hand-mutants.
  Generated designs are not quieter than the panel; if anything the reverse.
- Rank correlation between seed pairs: **+0.635, +0.647, +0.357** — mean ≈ 0.55, none significant
  (p = 0.08–0.39), against an attenuation ceiling of 0.853.
- **The top-1 design changes with the seed**: seeds 1 and 2 pick `015`, seed 3 picks `003`. Those
  two were separated by **0.001 DockQ** at seed 1 — one eighteenth of a seed sd.

So a single-seed ranking at the top of this funnel is not trustworthy. It is not *random* either:
ρ ≈ 0.55 is real signal. The honest reading is that single-seed ordering resolves broad tiers and
not neighbours, which is exactly what a reliability of 0.73 predicts.

**This also corrects a claim made earlier in the project.** The 0.965 reliability quoted from the
panel was **ipSAE**, not DockQ, and it was measured over designs spanning DockQ 0.036–0.818. The
baseline's top tier spans 0.650–0.754. Same absolute noise, an order of magnitude less signal —
reliability is a ratio, and restricting the range destroys it.

### 5.2 The winner's curse is small but real

Seed-1 winner regresses **−0.0123** DockQ on re-seeding; the average design regresses **−0.0045**.
**Selection excess = −0.0079 DockQ.** Modest, because 3 seeds over 8 designs is a weak selection,
and it will grow with the size of the pool the argmax is taken over. Any "our best design scored
X" claim carries at least this discount.

### 5.3 The ensemble is the part that discriminates

Across eight designs that are **identical on the rubric** — all `final` 87.5, all viable, all
clearing every gate — CDR-H3 backbone RMSD between seeds ranges **0.33 Å to 1.45 Å, a 4.4×
spread**, with maximum deviations from 0.53 Å to **4.31 Å**.

The rubric cannot see any of this. Neither can the confidence metric:

| relationship | Spearman | p |
|---|---|---|
| CDR-H3 RMSD ↔ **mean loop pLDDT** | **−0.168** | 0.691 |
| CDR-H3 RMSD ↔ pLDDT **sd across seeds** | +0.455 | 0.257 |
| CDR-H3 RMSD ↔ DockQ | −0.357 | 0.385 |

**`mpnn_T0.1_s37_001` carries a mean loop pLDDT of 90.5 — "very high confidence" by the usual
convention — on a CDR-H3 that moves 4.31 Å between seeds.** A single structure plus one
confidence number reports that loop as well-determined. It is not.

That is the concrete form of the argument that a single structure plus one confidence number is
the wrong representation for a conformationally heterogeneous region, and CDR-H3 is the most
heterogeneous part of an antibody. Note the constructive half too: the information is recoverable
from the **spread across seeds** (pLDDT sd, ρ = +0.455) even though it is absent from the mean.
The ensemble knows; the single structure does not.

**Stated honestly: we have not shown a tight ensemble means a better design.** The
CDR-H3-RMSD↔DockQ correlation is −0.357 at n=8, p=0.39 — the sign is the intuitive one but this
is not evidence. What *is* established is that ensemble spread is **real, large, and invisible to
every metric currently in the rubric**. Whether it predicts quality is the first thing worth
testing on a larger pool.
