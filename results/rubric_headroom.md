> ## ⚠ CORRECTED 2026-09-22 — the light-chain recommendation below is REFUTED
>
> This file recommends light-chain CDR redesign as the route to a Good developability
> band. **It was never tested and it does not work**, for two independent reasons:
>
> 1. **The ceiling is the heavy chain.** NetSolP is `min(VH, VL)` and VH is **0.699**
>    against a Good edge of **0.70**, so a perfect light chain still leaves the band at
>    Medium — **by 0.001**.
> 2. **ProteinMPNN cannot lift VL anyway.** 24 light chains at T=0.1 moved VL from 0.5690
>    to at best **0.5920** (+0.023) against a required **+0.131**; **0 of 24** reached the
>    edge and **24 of 24** introduced new CDR liabilities.
>
> Measured in `results/ch1_ng_and_light_chain_2026-09-22.md` at a cost of zero folds
> (NetSolP is sequence-only). The real requirement is a **solubility-aware objective**;
> ProteinMPNN optimises sequence recovery given a backbone and solubility is not in its
> loss. Everything else below stands.

# What is left on the rubric, and is it reachable?

`scripts/40_rubric_headroom.py` — CPU only, run concurrently with the overnight folds.
No selection decision is taken here; M3's named winner is unchanged.

## 1. The board

Under this project's `band_scores` (good 9.5, medium 7.0) the reachable maximum is
**95.0**, not 100. The winner is at **87.5**, and the entire 7.5-point gap is two
metrics sitting in Medium:

| metric | winner | Good needs | worth if moved |
|---|---|---|---|
| `dockq` | 0.747 | ≥ 0.80 | **+2.50** |
| `netsolp` | 0.585 | ≥ 0.70 | **+5.00** |
| both | | | **95.0 total** |

Note the +5.00 for NetSolP is *not* the +8 that a 6/10-vs-10/10 band reading gives;
this project scores bands at their midpoints (9.5 / 7.0 / 2.5), a convention recorded
in `config/metrics.yaml`. Quoting +8 would overstate the prize by 60%.

## 2. NetSolP — measured over the whole pool

All 239 designs, ESM1b 5-fold ensemble, `chain_agg = min`.

| quantity | value |
|---|---|
| VH (Fv) over 239 designs | 0.6677 – 0.7424 (mean 0.7061) |
| VL (Fv; pembrolizumab's, **byte-identical in all 239 designs**) | 0.5686 |
| `min(VH, VL)` achievable maximum | **0.5686** |
| Good band edge | 0.70 |
| shortfall | **+0.1314** |
| designs reaching Good | **0 / 239** |
| pool spread of VH | 0.0747 |
| shortfall as multiples of the pool spread | **1.8×** |

**The heavy chain already clears Good — 168 of 239 designs have VH >= 0.70 (mean 0.706, best 0.742) — and the composite is pinned at Medium anyway, entirely by the light chain.**

That is the actionable form of this finding and it was invisible until 2026-09-20, because the score was being computed on the **Fab** chains, where the heavy chain looked limiting (0.623 vs 0.626). On the Fv the handbook specifies, the ordering reverses: VH 0.668-0.742 against a fixed VL of 0.5686. Under `chain_agg: min` the light chain therefore sets the score for every design that will ever be made on this scaffold by heavy-CDR redesign.

**So the Good band is not reachable by heavy-CDR redesign — but not for the reason previously reported.**
ProteinMPNN varies only the 29 heavy CDR positions, which moves VH across a
range of 0.075; the gap to 0.70 is 1.8 times that range. The light chain is
pembrolizumab's in all 239 designs and scores 0.569, so it caps `min()` at 0.569
regardless of the heavy chain. The concrete lever is therefore **redesign the light-chain CDRs**, which nothing in this
project has touched: lifting VL above 0.70 would move developability Good and `final`
from 87.5 to 92.5. The only other route is to change the
`netsolp_chain_agg` convention — and the second is a convention change, not a
design improvement, so it would have to be declared as such.

**This is a finding, not a failure.** 20% of the rubric is pinned at Medium for
any pembrolizumab-framework Fab, including pembrolizumab itself. A pitch that
says so, with the measurement, is stronger than one that quietly leaves the
points on the table.

## 3. DockQ — the lever nobody pulled

Novelty is **banded**: `cdrh3_identity < 70%` scores Good and nothing below 70 scores
better. The pool spans **15.4–46.2%** identity. Every design is therefore buying
novelty that the rubric does not pay for, and identity is the strongest free predictor
of DockQ we have.

| quantity | value |
|---|---|
| Spearman identity↔DockQ, n=239 | **+0.389** (p=4.7e-10) |
| OLS slope | +0.00273 DockQ per % identity (SE 0.00042) |
| observed DockQ max | 0.777 |
| designs at DockQ ≥ 0.80 | 0 |
| identity implied for DockQ 0.80 | **66%** |
| still inside the Good novelty band? | **yes** |

**Read the extrapolation honestly.** The implied identity is outside the observed
range (15.4–46.2%), so it is a linear extrapolation, and the
relationship need not stay linear — DockQ is bounded above by what the predictor can do
on this complex at all, which the pembrolizumab refold puts near 0.82. What the number
licenses is a *hypothesis worth one cheap arm*: generate designs at 50–69% CDR-H3
identity, which is untouched design space that is free on novelty, and see whether
DockQ crosses 0.80. It does not license claiming the 2.5 points.

It is also worth saying what this lever is: it is **Goodhart in our favour**. The
rubric's banding means a design at 69% identity and one at 15% are scored identically
on novelty while differing substantially on pose retention. Reporting that we found it,
and what it implies about banded rubrics, is more interesting than the 2.5 points.

