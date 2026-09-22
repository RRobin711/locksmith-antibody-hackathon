# Pre-registration — widening the CDR-H3 ensemble measurement

**Written 2026-09-20 ~01:55, before `runs/designs_ens/` exists.** Fold script
`scripts/39_ensemble_wide_fold.py`; power analysis `scripts/36_ensemble_power.py`
(already run, zero new folds).

## 1. What we already know, stated exactly, so tonight cannot quietly rediscover it

This is the third pass over this question and the claim has narrowed each time.
Pre-registering the *superseded* version would be self-flattery, so:

| date | n | claim | status |
|---|---|---|---|
| 2026-09-18 | 8 | mean **loop** pLDDT is uncorrelated with CDR-H3 seed-to-seed spread (ρ −0.168, p=0.69); one design carries loop pLDDT 90.5 while its loop moves 4.31 Å | stands, but n=8 |
| 2026-09-18 | 40 | **interface** pLDDT *does* partly see it (ρ −0.496, p=0.001) | narrows the above |
| 2026-09-18 | 40 | CDR-H3 **aromatic fraction** predicts spread (+0.621) and explains away the spread→DockQ link entirely (partial −0.081, p=0.62) | stands |

So the headline "a confidence metric is blind to the disorder it reports on" is
**already known to be false as stated for `iface_plddt`** and true only for the loop's
own mean pLDDT. Tonight tests the narrowed version. All 40 of those designs were
T=0.1, one generation (`s37`), and used a reference-dependent spread estimator.

## 2. Hypotheses, registered

- **H1 (primary).** Mean **loop** pLDDT does not predict CDR-H3 conformational spread
  across seeds, over the full 239-design pool spanning four MPNN temperatures.
  *Null:* ρ = 0. *Direction if real:* negative (higher confidence, tighter loop).
- **H2 (primary).** **Interface** pLDDT does predict it, replicating ρ ≈ −0.50 at T=0.1
  and extending to T=0.2/0.3/0.5.
- **H3.** The H2 relationship is **modified by MPNN temperature**, decaying as sampling
  temperature rises — the pattern the aromatic-fraction effect showed
  (ρ −0.535 → −0.326 across the same four arms). Tested as an interaction, arms fitted
  separately and compared by Fisher-z.
- **H4.** CDR-H3 **aromatic fraction** predicts spread (+0.621 at T=0.1) across all arms,
  and partialling it out removes most of H2's effect — i.e. `iface_plddt` sees spread
  *because* it sees aromatics, not independently.
- **H5 (the estimate the run exists to produce).** The pool's between-design variance in
  spread is **not** carried by a single outlier. On the 20-design shortlist it is:
  dropping one design at 1.77 Å moves k=2 reliability from 0.591 to **0.265**.

## 3. Statistics, fixed in advance

- **Spread estimator:** RMS Cα deviation over CDR-H3 (heavy 96–108) across **all C(k,2)
  seed pairs**, each pair superposed on the **framework** (never the loop). This is a
  deliberate change from the 2026-09-18 estimator, which measured every seed against
  `seed[0]` and therefore depended on which seed came first. **Numbers are not
  comparable to the 0.33–1.45 Å previously quoted** and the writeup must say so.
- **Test:** Spearman ρ with a bootstrap 95% CI (10,000 resamples over designs).
- **Attenuation:** every ρ against spread is reported **twice** — observed, and
  disattenuated by `ρ / √reliability` — never only the corrected value.
  `reliability(k=2) = var_between / (var_between + V1)` with `V1 = 0.0628 Å²` measured
  from the 20×7 shortlist and `var_between = var(observed 2-seed spreads) − V1`
  estimated on the pool itself.
- **A null is a bound, not an absence.** Any null is reported as "no effect larger than
  ρ_true = x", where x is the disattenuated effect detectable at 80% power, α=0.05.
  At n=239, k=2 that is ρ_obs 0.180, i.e. ρ_true ≈ **0.23–0.35** depending on which
  reliability estimate survives H5.

## 4. Design and stopping rule

- **Nested:** seed 2 for all 239 designs first, then seed 3 in the same order.
  Any stopping point leaves a complete balanced k=2 pool plus a k=3 prefix.
- **Order shuffled** with fixed seed 0 before the run, so any prefix is a balanced
  sample across all four temperature arms and the order is independent of every design
  property. Restarts follow the same sequence.
- **Stopping rule:** no new batch starts after **07:30 local**. This is data-independent
  by construction.
- **Analysis set:** every design with ≥2 successful seeds at analysis time. Designs whose
  folds failed are reported as a count, not silently dropped.

## 5. What each outcome means

| outcome | reading |
|---|---|
| H1 null holds, H2 replicates across arms | The claim is precise and defensible: *the loop's own confidence is blind to its own heterogeneity; only confidence computed over the interface sees it.* This is the pitch's spine. |
| H1 and H2 both null | Boltz pLDDT carries no information about conformational spread at all. Stronger, simpler claim — but then the n=40 ρ −0.496 was a T=0.1 artefact and must be withdrawn in writing. |
| H2 holds but H3 shows strong decay | The relationship is real only where sampling is conservative. Report the interaction; do not quote a pooled ρ. |
| H4 holds | `iface_plddt` is a proxy for aromatic content. Then the interesting object is the **sequence feature**, and the ensemble story becomes a story about what a free feature already encoded. |
| H5 fails (one outlier carries everything) | The pool has no usable between-design variation in spread. Then the honest result is *"CDR-H3 heterogeneity does not vary meaningfully across fixed-backbone redesigns of one scaffold"* — a null that kills the axis, and must be reported as loudly as a positive would have been. |

## 6. The claim boundary — binding, not optional

Spread across diffusion seeds measures **how well determined the prediction is**, which
is a property of **Boltz**, not of the molecule. We have no experimental structure of
any design and no binding data. Any sentence of the form "this loop is flexible" is
unsupported; the supported form is "the predictor does not place this loop
consistently". Every figure and every slide inherits this sentence.
