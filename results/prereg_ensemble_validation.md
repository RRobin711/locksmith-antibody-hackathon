# Pre-registration — does ensemble tightness earn a place in selection?

**Written 2026-09-18, before generating the additional designs and before any new fold.**
`runs/designs_wide/` did not exist when this was written.

## 1. The question, and what it is not

The re-seed found CDR-H3 backbone spread ranging **4.4×** (0.33–1.45 Å) across eight designs the
rubric calls identical, invisible to mean loop pLDDT (ρ = −0.168). Dynamic range is not meaning.
This tests whether the axis predicts anything.

**One link is already settled and is NOT the question.** Ensemble RMSD vs DockQ sd across seeds:
**ρ = +0.833, p = 0.010, n = 8.** That is partly mechanical — both are computed from the same
three structures — and, more importantly, **it is a co-measurement, not a leading indicator**.
Knowing the ensemble spread requires folding 3 seeds, by which point the score variance is
directly available. It cannot save a fold, so it cannot drive selection. Recorded as
characterisation; not retested.

## 2. Design

**40 designs, ProteinMPNN `v_48_020`, temperature 0.1** (the baseline's setting, so the pool is
comparable), MPNN seeds 37 and 38. **All 40 folded as Fab on 3 Boltz seeds** — no gating and no
shortlisting before the correlation is measured, because selecting on DockQ and then correlating
against DockQ restricts the range of the variable under test. Gating would also reduce nothing:
20/20 of the baseline cleared every gate.

Existing folds are reused: 20 designs have Boltz seed 1, of which 8 have all three. **84 new folds.**

**Declared limitation.** All designs come from one temperature, so DockQ range will be narrow
(the baseline spanned 0.650–0.754). That is deliberate — it is the regime in which selection
actually operates, and the G1c lesson is that a screen must be tested where it will be used. But
it means a null result reads as "does not discriminate **among plausible designs**", not "carries
no information anywhere". Widening the range by varying temperature would confound: temperature
drives both divergence and quality.

## 3. Thresholds, fixed in advance

Primary: **Spearman(CDR-H3 ensemble RMSD, 3-seed mean DockQ)**, n = 40.

| observed | verdict |
|---|---|
| \|ρ\| ≥ 0.50 and p < 0.05 | **worth selecting on** — explains ≥25% of quality variance; goes into `select/` as a second axis |
| \|ρ\| 0.30–0.50, or p ≥ 0.05 | **worth reporting only** — real spread, no established link to quality; characterisation in the dossier |
| \|ρ\| < 0.30 and p ≥ 0.05 | **drop from selection** — no relationship in the operating regime |

Power at n = 40: detects an observed ρ of 0.45 at ~80% (α = 0.05, two-sided). Attenuation is
expected — DockQ reliability is 0.727 and ensemble RMSD is itself estimated from 3 seeds — so a
true ρ of ~0.6 would present near the 0.45 boundary. **A null is therefore "no effect larger than
roughly ρ = 0.45", not "no effect".**

Secondary, same data, reported regardless:
- ensemble RMSD vs each of the eight rubric metrics, and vs `final`.
- **ensemble RMSD vs cheap PRE-FOLD features** — MPNN score, CDR-H3 length, net charge,
  hydrophobic fraction, aromatic fraction, glycine content. A feature reaching \|ρ\| ≥ 0.50 with
  p < 0.05 would be a **screen for conformational stability costing zero folds**, which is worth
  more than the primary result. Six features tested, so significance is judged at
  Bonferroni α = 0.0083.

## 4. What cannot be tested, and must be said in the writeup

There is **no binding data, no experimental structure for any design, and no ground truth about
which CDR-H3 conformation is correct.** So "tight ensemble" cannot be shown to mean "better
antibody" by any route available here.

What ensemble spread measures is **how well-determined the prediction is** — a statement about
the predictor's agreement with itself, not about the molecule. Even the primary correlation, if
it comes back positive, would only establish that predictions which are self-consistent about the
loop also reproduce the crystal's binding mode more closely. That is worth knowing and it is not
the same claim.

## 5. What the run produces regardless of the outcome

40 designs with 3-seed mean scores: the shortlist M3's campaign needs anyway, since reliability
0.727 means single-seed ordering resolves tiers but not neighbours. **The folds are not
contingent on the correlation landing.**

**No design will be added, dropped or re-generated after any correlation is seen.**
