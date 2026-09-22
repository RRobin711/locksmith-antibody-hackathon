---

> ## ⚠ PARTLY REVERSED 2026-09-20 at n=239
>
> **What replicated, almost exactly:** CDR-H3 aromatic fraction → DockQ, raw **−0.535**
> here against −0.536 then, and **−0.408** controlling for ensemble spread against −0.410.
> An independent out-of-sample confirmation on 239 designs; the aromatic result is sound.
>
> **What did not:** the conclusion drawn from the *other* half. "Ensemble spread carries no
> information the sequence didn't already have" rested on a partial of **−0.081 (p=0.62) at
> n=40**; over the pool it is **−0.289 (p=5.7e-06)**, and **−0.303** on this very T=0.1 arm.
> **The ensemble axis was dropped from selection on an underpowered partial that does not
> replicate.**
>
> Also: "mean loop pLDDT is uncorrelated with spread" was n=8 (ρ −0.168, p=0.69, CI ≈ ±0.7);
> at n=239 it is **−0.432**, and it *beats* interface pLDDT (−0.344). See
> [[2026-09-20-auditing-the-judge-reliability-is-not-validity|the audit]].

date: 2026-09-18
tags: [project, protein-design, structure-prediction, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Learning|things I'm learning]]

# The ensemble axis loses to a free sequence feature

**Session:** 2026-09-18. **Ran:** 84 new Fab folds (40 designs × 3 seeds), 120 scored.
**Result:** ensemble tightness **does not earn** a place in selection — its correlation with
design quality is fully explained by CDR-H3 **aromatic fraction**, which predicts quality better
and costs **zero folds**.
**Prerequisite:** [[2026-09-18-reseeding-and-the-cdr-h3-ensemble|the re-seed doc]], which found the 4.4× ensemble spread this tests.

---

## 1. The question, and why it was asked this way

The re-seed found CDR-H3 backbone spread varying 4.4× across eight designs the rubric calls
identical, invisible to mean loop pLDDT. That is dynamic range where nothing else has any — and
the funnel badly needs a discriminator, since plain ProteinMPNN clears every gate and the
composite takes three distinct values across twenty designs.

But **dynamic range is not meaning.** So this session tested whether the axis predicts anything
before building selection around it.

Three choices shaped the design, all fixed in
[[../../results/prereg_ensemble_validation|a pre-registration]] written before the designs existed:

**No gating or shortlisting before the correlation.** Selecting the top by DockQ and then
correlating ensemble spread *against* DockQ restricts the range of the variable under test —
the error behind G1c and behind the reliability figure quoted from a wide-range panel. All 40
designs got 3 seeds. Gating would also have filtered nothing: 40/40 were viable.

**n = 40, sized rather than asserted.** Detects an observed rho of 0.45 at ~80% power. With DockQ
reliability 0.727 and ensemble RMSD itself estimated from three seeds, a true 0.6 attenuates to
near that boundary — so a null means "no effect larger than ~0.45", not "no effect".

**A secondary question that turned out to be the real one.** Whether any *cheap pre-fold* feature
(MPNN score, CDR-H3 length, charge, hydrophobicity, aromatics, glycine) predicts ensemble spread.
A hit there is a screen costing no GPU time at all — declared in advance as "worth more than the
primary result", which is exactly how it played out.

**One link deliberately not retested.** Ensemble RMSD vs DockQ sd across seeds was already
+0.833 at n=8. It is partly mechanical — both come from the same three structures — and it cannot
drive selection, because knowing the ensemble spread requires the folds that would give the score
variance directly. Confirmed at n=40 (**+0.718**) and set aside.

---

## 2. The primary result, and the verdict it looked like

**Spearman(CDR-H3 ensemble RMSD, 3-seed mean DockQ) = −0.387**, 95% CI [−0.62, −0.09],
p = 0.014, n = 40.

Sign as expected: tighter ensemble, better recovery of the native binding mode. Significant, but
inside the pre-registered 0.30–0.50 band — **"worth reporting only"**.

That would have been the answer. The secondary analysis overturned it.

---

## 3. The confound: aromatic content explains all of it

| relationship | Spearman | p |
|---|---|---|
| aromatic fraction → CDR-H3 ensemble RMSD | **+0.621** | 0.00002 |
| aromatic fraction → 3-seed mean DockQ | **−0.536** | 0.00036 |
| ensemble RMSD → 3-seed mean DockQ | −0.387 | 0.014 |
| **partial: ensemble → DockQ, controlling aromatics** | **−0.081** | **0.621** |
| **partial: aromatics → DockQ, controlling ensemble** | **−0.410** | 0.0086 |

**Control for aromatic content and the ensemble↔quality link vanishes** (−0.387 → −0.081,
p = 0.62). Control for ensemble spread and the aromatic↔quality link **survives** (−0.410,
p = 0.009). The direction of explanation is not ambiguous.

And the cost comparison finishes it:

| predictor of 3-seed mean DockQ | Spearman | folds |
|---|---|---|
| CDR-H3 ensemble RMSD | −0.387 | **3 per design** |
| **CDR-H3 aromatic fraction** | **−0.536** | **0** |

**A sequence feature you can compute before folding anything predicts design quality better than
a measurement costing three GPU folds, and explains away the expensive one.**

**Verdict: ensemble tightness is dropped from selection.** Not for lack of signal — for lack of
*additional* signal. Everything it knows about quality is already in the sequence.

---

## 4. What this does not say

- **Not that ensembles are uninteresting.** Spread varies **7.9×** across the pool (0.28–2.23 Å)
  and remains the right characterisation of how well-determined a prediction is. Report it in a
  dossier; do not select on it.
- **Not causation.** Aromatic content may be a marker for something else. It is chemically
  plausible — F/W/Y are bulky with many packing arrangements, and aromatic-rich CDR-H3 is a known
  correlate of polyreactivity — but 40 designs from one generator do not establish mechanism.
- **Not general across loop lengths.** Every design has a **13-residue CDR-H3**, fixed by the
  backbone MPNN redesigns onto. That is why the `cdrh3_len` test returned `nan`: the variable is
  constant. Length is the main determinant of loop flexibility, so this result is measured with
  that dimension held still — and length variation is the obvious way to break it.
- Aromatic fraction spans only **0.08–0.31**. Nothing outside that is supported.

---

## 5. A smaller finding worth keeping

`iface_plddt` is the rubric metric most correlated with ensemble spread (**−0.496, p = 0.001**),
better than `ipsae` (−0.387). The n=8 re-seed found *mean loop pLDDT* blind to heterogeneity
(−0.168); at n=40 the *interface* pLDDT partly sees it.

So the earlier "confidence is blind to conformational heterogeneity" claim needs narrowing: it
depends which pLDDT you read. The loop's own mean is blind; the interface value is not. The
general lesson survives — a single number over the wrong atoms misses it — but the specific claim
was broader than the data.

---

## 6. What M3 should be now

**Rank on 3-seed mean composite, with aromatic fraction as a pre-fold filter.** The ensemble
branch is closed.

This is a better outcome than the branch I was hoping for. A selection axis costing three folds
per design would have tripled the campaign's budget; a sequence filter costs nothing and can be
applied to thousands of candidates before a single GPU second is spent. Concretely, MPNN can
over-generate and the aromatic filter prunes before folding — the first genuinely *cheap* stage
this funnel has had.

**Multi-seeding is still required**, independently of all this: reliability 0.727 means
single-seed ordering resolves tiers but not neighbours. Three seeds on the shortlist stays.

**And length variation now has a sharper purpose.** It was the natural next experiment anyway;
it is now specifically the way to test whether the aromatic effect survives when loop length is
free to vary, since everything here was measured at a fixed 13 residues.

---

## 7. G3 is vacuously satisfied, and that is a problem with G3

Checked while scoping M3. The gate reads:

> **G3** — Ch1: ≥3 designs clearing all gates; best re-scored on fresh seeds

We have **40/40 designs clearing all gates**, all re-scored on 3 seeds. **G3 is literally met.**
It certifies nothing: plain ProteinMPNN at defaults clears every gate at a 100% rate, so a
criterion of "≥3 designs clearing all gates" is a bar the *control* clears forty times over. The
gate was written before the baseline was measured, and the baseline invalidated it.

Recorded rather than ticked. Three honest replacements:

1. **Beat the baseline on ranked quality** — the funnel's top-5 by 3-seed mean composite beats a
   random 5 from the unfiltered pool by a stated margin. Risk: with the whole pool viable and
   tightly banded (DockQ 0.628–0.747), "better-ranked" may not be distinguishable at achievable n.
2. **Beat it on cost** — the aromatic filter reaches equal-quality designs using materially fewer
   folds. This is the claim §3's data actually supports.
3. **Drop gate-clearing entirely** — make G3 about the shortlist's defensibility: best design
   named, re-scored on fresh seeds, winner's-curse discount applied, ensemble characterised.

Recommended: **2 + 3**. The cost claim is the one the measurements support, and the gate-clearing
language should go because it now certifies nothing. Decision pending with the user, and it
determines how wide the generation pass needs to be — which is why M3 was not started.

## 8. M3, costed from measured rates

| quantity | measured this session |
|---|---|
| Fab fold (549 residues), quiet machine | **85 s** |
| Fab fold, machine contended | 133–137 s |
| Scoring | **19 s per fold** (serial, incl. amortised NetSolP) |
| NetSolP | ~40 s per design (CPU, overlaps with folding) |

M3 shape: generate wide → aromatic-filter pre-fold → fold survivors at 1 seed → shortlist →
3-seed the shortlist → fresh-seed the winner.

| sizing | designs generated → folded | folds | at 85 s | at 133 s |
|---|---|---|---|---|
| minimal | reuse 40 + small demo pass | ~70 | 1.7 h | 2.6 h |
| **modest** | 200 → 100 → shortlist 30 | **~162** | **3.8 h** | 6.0 h |
| wide | 500 → 200 → shortlist 40 | ~282 | 6.7 h | 10.4 h |

**Decision taken: wide, run overnight.**

### 8.1 Fold batching now pays for itself on M3 alone

Batching several targets into one `boltz predict` invocation is worth ~1.8×, because a large
fixed cost per invocation (checkpoint load plus MSA parse) currently dominates: the *fold* is
~34 s for an Fv and the *invocation* is 85–133 s.

It has been deferred twice, correctly, on the grounds that the right batch shape depends on the
funnel pattern. **That pattern is now known and stable**: N independent 549-residue Fab folds
with no interdependence. On a wide M3 batching converts ~6.7 h into ~3.7 h — it saves more than
it costs to build, and every later milestone inherits it. M5's dossier needs another round of
folds (6 validations × 2 designs × 2 challenges).

**Transferable principle.** A deferred optimisation should carry the *condition* that would
un-defer it, not just a "later". The condition here was "once the funnel pattern is known"; it
was met the moment M2 closed, and writing it down is what made that checkable instead of a
judgement call re-litigated each session.

---

## 9. State

**Ran.** 84 new folds (124 cumulative for this pool), 120 scored, zero failures.
`results/ensemble_validation.md`, `scripts/24`–`26`, `runs/designs_wide/`.

**Carried.** 40 designs with 3-seed means on all eight metrics — a usable Challenge 1 candidate
set, though not a "wide" generation pass.

**Open.** M3 not started. `submit/` empty. Fold batching outstanding. Second predictor deferred.
