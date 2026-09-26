---
date: 2026-09-18
tags: [project, protein-design, structure-prediction, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Learning|things I'm learning]]

# Re-seeding, and the CDR-H3 ensemble

> ⚠️ **One claim below was narrowed at n=40 — see [the validation doc](2026-09-18-the-ensemble-axis-loses-to-a-free-sequence-feature.md).**
> "Invisible to pLDDT" was measured on *mean loop* pLDDT (rho −0.168, n=8) and is too broad.
> At n=40, **`iface_plddt` does partly see the heterogeneity (rho −0.496, p=0.001)**. The loop's
> own mean is blind; the interface value is not. Separately, the ensemble axis was **dropped from
> selection**: CDR-H3 aromatic fraction predicts quality better (−0.536) at zero folds and fully
> explains the ensemble↔quality link (partial −0.081, p=0.62). The 4.4× spread finding stands.

**Session:** 2026-09-18. **Ran:** 16 Fab folds re-seeding the baseline's top tier.
**Found:** the single-seed ranking is substantially noise (reliability 0.727, as predicted),
the winner's curse is −0.0079 DockQ, and CDR-H3 ensemble spread varies **4.4×** across designs
the rubric calls identical — invisible to pLDDT.
**Prerequisite:** [the M2 doc](2026-09-18-m2-the-design-path-and-a-baseline-that-passes-everything.md) for the baseline this re-seeds.

---

## 1. The argument for running this, which nearly went the other way

The scoping view going in was that re-seeding would be a cheap null: the baseline's designs are
built on pembrolizumab's native backbone, so the model is recovering a pose it is anchored to,
so variance should be small and nothing learned. The supporting evidence offered was 9W43 —
a genuinely hard novel placement that came out at DockQ sd **0.003** across three seeds.

Both halves of that are true and the conclusion still does not follow.

**9W43's stability is stability at the floor.** DockQ ≈ 0.05 is a confidently-wrong pose
reproduced identically. It says nothing about variance in the 0.65–0.75 band where ranking
actually happens, and variance in structure prediction is strongly heteroscedastic — the panel
itself showed Fv seed sd ranging 0.019 to 0.122 depending on the design.

**Reliability is a ratio, and the baseline destroyed the denominator.** This is the calculation
that decided it, done before any fold:

| | |
|---|---|
| baseline between-design DockQ sd (the signal the ranking must resolve) | 0.0329 |
| panel Fab **DockQ** seed sd (the noise) | 0.0181 |
| noise as a share of signal | **55%** |
| implied reliability | **0.700** |

Small variance is not the same as resolvable differences. The panel's reliability looked
excellent because its designs spanned DockQ 0.036–0.818 — dead to alive. The baseline's top tier
spans 0.650–0.754, ten times narrower. **Same absolute noise, an order of magnitude less signal.**

**And the 0.965 figure everyone was reasoning from was ipSAE, not DockQ.** I introduced that
error in the panel write-up and it propagated into the scoping of this session. DockQ's Fab seed
sd is 0.018, and DockQ is what does the ordering.

Concretely: ranks 1 and 2 differed by **0.001 DockQ**, one eighteenth of a seed sd, and the
median adjacent gap in the top tier was 0.011 — 0.61 sd. So this was not a cheap null. It was a
test of a specific quantitative prediction.

---

## 2. What was run

The top tier: **8 designs all at `final` 87.5**, where the composite cannot order them and the
DockQ tiebreaker does the whole job. Re-folded as Fab on seeds 2 and 3 — same driver, same cached
PD-1 alignment, same scoring path. 16 folds, ~70 minutes, zero failures.

The ensemble readout was built into the same run rather than retrofitted, because re-seeding a
diffusion model *is* sampling conformations. Superposition for the loop analysis is on the
**framework** CAs only: superposing on the loop would hide the thing being measured.

---

## 3. The prediction held

**Measured reliability 0.727** against 0.700 predicted.

- Seed sd on real designs: **0.0209** — slightly *larger* than the 0.0181 measured on
  hand-mutants. Generated designs are not quieter than the panel.
- Rank correlation between seed pairs: **+0.635, +0.647, +0.357**, mean ≈ 0.55, none significant
  (p = 0.08–0.39), against an attenuation ceiling of 0.853.
- **The winner changes with the seed**: seeds 1 and 2 pick `015`, seed 3 picks `003`.

The honest reading is not "the ranking is random" — ρ ≈ 0.55 is real signal. It is that
**single-seed ordering resolves tiers, not neighbours**, which is exactly what reliability 0.73
predicts. Anything that turns on adjacent ranks needs multiple seeds.

**Winner's curse:** the seed-1 winner regresses −0.0123 on re-seeding against a −0.0045 average,
so the selection excess is **−0.0079 DockQ**. Small, because taking the argmax of 8 designs is a
weak selection; it grows with the pool.

---

## 4. The ensemble — the result worth keeping

Across eight designs that are **identical on the rubric** (all `final` 87.5, all viable, every
gate cleared), CDR-H3 backbone RMSD between seeds ranges **0.33 Å to 1.45 Å — a 4.4× spread** —
with maximum deviations up to **4.31 Å**.

Nothing in the current metric set sees this:

| relationship | Spearman | p |
|---|---|---|
| CDR-H3 RMSD ↔ **mean loop pLDDT** | **−0.168** | 0.691 |
| CDR-H3 RMSD ↔ pLDDT **sd across seeds** | +0.455 | 0.257 |
| CDR-H3 RMSD ↔ DockQ | −0.357 | 0.385 |

**`mpnn_T0.1_s37_001` has a mean loop pLDDT of 90.5 — "very high confidence" — on a CDR-H3 that
moves 4.31 Å between seeds.** The single structure reports that loop as well-determined; the
ensemble says it is not.

This is the project's own reading-list thesis in measured form: a single structure plus one
confidence number is the wrong representation for a conformationally heterogeneous region, and
CDR-H3 is the most heterogeneous part of an antibody. The constructive half matters too — the
information is recoverable from the **spread across seeds** (pLDDT sd, ρ = +0.455) even though
it is absent from the mean. The ensemble knows; the single structure does not.

**What this does not show.** That a tight ensemble means a *better* design. CDR-H3 RMSD ↔ DockQ
is −0.357 at n=8, p=0.39 — the sign is intuitive, the evidence is not there. What is established
is that ensemble spread is real, large, and **invisible to every metric in the rubric**.

---

## 5. What M3 should be

**Not CDR-H3 length variation as the primary move, and not more designs.** M3 should be built
around **ensemble-aware selection**, for three reasons.

**The funnel needs a discriminator and this is the only one that discriminates.** Plain MPNN
clears every gate, the composite takes three values across twenty designs, and single-seed DockQ
resolves tiers but not neighbours. Ensemble spread has **4.4× dynamic range on designs the rubric
calls identical**. It is the only measured quantity that separates them.

**Re-seeding is now mandatory anyway, so the ensemble is free.** Reliability 0.73 means a
shortlist must be multi-seeded before anything turns on its order. Once three seeds are being
folded, the loop RMSD and the pLDDT spread cost nothing.

**It is the piece that speaks Locksmith's vocabulary.** A funnel that reports "our design is
viable" says nothing the baseline does not. A funnel that reports "this design is viable *and*
its CDR-H3 is conformationally tight, while this equally-scoring one moves 4.3 Å" is making a
claim the rubric cannot express and the company's own thesis is about.

**Concrete shape.** Generate wide at one seed → gate → shortlist → 3-seed re-fold → rank on the
3-seed mean composite, with ensemble tightness reported as an explicit second axis. Budget: at
~126 s per Fab fold, 3 seeds costs 378 s per shortlisted design, so a shortlist of ~30 fits
comfortably inside the ~1,290-fold budget alongside a wide first pass.

**The first thing M3 must establish** is whether ensemble tightness predicts anything — n=8 and
p=0.39 is not evidence. That is a question a campaign answers as a by-product, and it is the
difference between a second axis worth reporting and a second axis worth selecting on.

**Where length variation fits: second, and for a specific reason.** CDR-H3 length is the main
determinant of loop flexibility, so varying it is the natural way to *generate* ensemble
variation and test whether tightness predicts quality. It also breaks the geometric guarantee
that made the baseline trivially pass. But doing it first means entering an untested regime with
an unvalidated selection criterion and a ranking already known to be noisy at the neighbour
level. Sequenced second, it becomes the experiment that tests the criterion rather than a leap.

---

## 6. State

**Ran:** 16 Fab folds, zero failures; `runs/designs_reseed/`, `results/reseed_ensemble.md`,
`scripts/22`–`23`.

**Open.** M3 not started. `submit/` empty. Fold batching outstanding (~1.8×, and now more
attractive since 3-seed shortlists triple the fold count). Second predictor still deferred.
