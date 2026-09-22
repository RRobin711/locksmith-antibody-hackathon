---
date: 2026-09-18
tags: [project, protein-design, structure-prediction, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Learning|things I'm learning]]

# M2: the design path, and a baseline that passes everything

**Session:** 2026-09-17 → 2026-09-18. **Built:** `design/mpnn.py`, `select/`, `validate/`, four
scripts, and `designs.parquet`. **Result:** ProteinMPNN at defaults clears **20/20** of the
eight gates — which says more about the gates than about the designs.
**Prerequisites:** [[2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test|the panel doc]] for the ipSAE↔DockQ curve, and [[2026-09-17-validating-the-inputs-and-withdrawing-a-result|the validation doc]] for the splice guard this path relies on.

---

## 1. The selection re-spec — I argued against it, with numbers

The brief proposed: rank on DockQ-vs-5GGS with ipSAE as a 0.60 liveness gate, because among
live designs ipSAE barely discriminates. The diagnosis is right. The prescription is wrong, and
the reason is measurable against `config/metrics.yaml` itself.

**The rubric already states the trade, and it prices novelty at 2× DockQ.** Measured by
perturbing one metric at a time through `score.evaluate()`:

| change | effect on `final` |
|---|---|
| CDR-H3 identity, good → poor (60% → 93%) | **−14.0** |
| DockQ, good → poor (0.85 → 0.30) | **−7.0** |
| ipSAE, good → medium (0.85 → 0.70) | −2.5 |

And at the extremes the ordering inverts entirely:

| design | final | viable |
|---|---|---|
| faithful: 96% CDR-H3 identity, DockQ 0.88 | 81.0 | **False** (novelty gate) |
| divergent: 55% identity, DockQ 0.55 | **92.5** | True |

So ranking on DockQ would **invert the customer's stated preference** and systematically promote
near-copies of pembrolizumab — exactly the failure the brief was worried about, arrived at by
the proposed fix rather than avoided by it.

**Second reason: banding neutralises ipSAE's flatness rather than amplifying it.** Sub-scores
are band midpoints (9.5 / 7.0 / 2.5), so a metric sitting in the same band for every live design
contributes a *constant*. It supplies no ranking signal, but it injects no noise. ipSAE's
non-discrimination costs far less inside a banded composite than it would in a continuous sort —
which is the premise the re-spec rested on.

**Adopted instead:** rank on `final` (the rubric composite), with **DockQ as tiebreaker** and
CDR-H3 identity second. Recorded as `selection_key: final` in `config/metrics.yaml` with the
measured justification, so it is a convention with evidence attached rather than a sort key that
emerged by accident. §5 below shows the tiebreaker is doing real work.

---

## 2. What was built

- **`design/mpnn.py`** — ProteinMPNN over the 29 IMGT heavy CDR positions (H1 8, H2 8, H3 13),
  located by ANARCII rather than a fixed residue range. Light chain and PD-1 held fixed as
  *context*: MPNN will redesign any chain it is given, and redesigning PD-1 would produce a
  molecule that binds a protein nobody has. Asserts on the artefact, not the exit code.
- **`validate/`** — pre-flight on every design before GPU time: non-standard residues, `X`,
  empty chains, and a length check against the parent (an indel means the design was built
  against the wrong frame — a bug, not a design). Plus `check_reference_foldable()`, which
  delegates to the splice guard so there is one definition of "spliced".
- **`select/`** — ranking with **gates enforced structurally**. `rank()` cannot return a
  non-viable design: viability partitions before any ordering, and `viable is None` (a metric
  failed to compute) is treated as non-viable rather than optimistically included.
- **`designs.parquet`** — 20 rows × 33 columns: raw values, per-metric band, category scores,
  composite, viability, failing gates, plus generator provenance (model, temperature, seed,
  MPNN score, sequence recovery). Queryable, not a log. Because `score.evaluate()` is a pure
  function of (raw values, config), re-scoring after a convention change costs seconds and no
  GPU time — which is why raw values are persisted and not just verdicts.

---

## 3. The baseline

20 designs, `v_48_020`, temperature 0.1, seed 37. No filtering, no reranking — every design
generated was folded as a Fab, scored on all eight metrics and gated. **20/20 folds succeeded.**

| | |
|---|---|
| distinct heavy chains | 20/20 |
| distinct CDR-H3 | 17/20 |
| substitutions vs pembrolizumab | 14–16 of 29 designable |
| CDR-H3 identity | 23.1–38.5% (median 30.8) — all in the **good** novelty band |
| MPNN sequence recovery | 0.448–0.517 |

**A prediction of mine that was wrong, recorded because it was load-bearing.** I expected
temperature 0.1 to recover near-native sequences and produce designs failing the novelty gate.
It did not: recovery is ~48%, because the 29 designed positions are the *most variable* in the
molecule. Naive MPNN at defaults is a perfectly good novelty generator over CDRs. Had I "fixed"
this by raising the temperature pre-emptively, I would have tuned away the baseline's actual
behaviour before measuring it.

---

## 4. The result: 20/20 viable — and what that actually means

Every design cleared every gate. Per the standing rule, I stopped and interrogated rather than
writing it up.

It survives interrogation. The designs are genuinely distinct (20 unique heavy chains, 14–16
substitutions), their CDR-H3s bear no resemblance to the native (`ARRDYRFDMGFDY` →
`AARPRNYDGGLFL`), and the metric distributions are sensible: DockQ 0.650–0.754, ipSAE
0.765–0.862, ΔG −13.4 to −10.4, contacts 96–116.

**The mechanism is the explanation.** ProteinMPNN redesigns sequence onto the *native backbone
in complex*. It is choosing residues that fit pembrolizumab's exact binding geometry, and Boltz
then recovers approximately that pose. High DockQ is near-guaranteed **by construction** — which
is precisely the caveat the brief raised, that DockQ-vs-5GGS measures retention of the native
binding mode rather than correctness. Here that caveat is not a limitation of the metric; it is
the whole reason the hit rate is 100%.

**So a 100% hit rate is not evidence the designs are good. It is evidence the gates are not the
binding constraint in this regime.**

### 4.1 Pembrolizumab is non-viable

Scored through the same path: **final 76.0, viable False**, failing `cdrh3_identity` at 100%.
Every one of the 20 designs outscores the licensed drug (82.5–87.5).

That is the rubric working exactly as written — novelty carries 20% weight and a marketed
antibody has none — but it is worth stating plainly because it fixes what the baseline means.
The control the funnel must beat is not "pembrolizumab"; pembrolizumab cannot even enter.

---

## 5. Two things this answered for free

**The ipSAE level shift does not apply to Challenge 1.** On the five post-cutoff targets ipSAE
sat ~0.19–0.28 *below* the panel curve. These designs sit **on** it: mean residual **+0.039**
(+1.3 SE), with a *tighter* spread than the panel itself (0.4×). The shift is a property of
**novel complexes**, not of designs. So panel-calibrated gate thresholds transfer to Challenge 1
and would not have transferred to Challenge 2 — which is a concrete reason the two challenges
needed separate calibration and now have it.

**ipSAE carries no ranking information among real designs either.** Spearman ipSAE↔DockQ across
the 20 is **+0.013 (p=0.957)** — indistinguishable from zero. The panel's §8 finding, derived
from hand-mutants of a memorised complex, reproduces on actual MPNN designs. It confirms the
adopted rule: **report ipSAE, gate on it, never rank on it.**

**And the composite is coarse.** Three distinct `final` values across 20 designs, because
sub-scores are band midpoints and `final` only moves when a metric crosses a band edge. Ranking
on `final` sorts into tiers; the **DockQ tiebreaker does the fine ordering within them.** That is
the intended division of labour, but it means the tiebreaker is load-bearing rather than
decorative — worth knowing before anyone changes it.

---

## 6. What this means for M3, which I did not start

**The funnel cannot demonstrate value through hit-rate against this baseline.** There is no
headroom: naive MPNN already clears every gate at defaults, in 42 minutes of GPU time, with no
filtering. A funnel that reports "our designs are viable" says nothing the control does not.

Three regimes where the gates would actually bite, in rough order of how much they'd prove:

1. **Robustness under re-seeding.** Boltz is a diffusion model; these are single-seed scores.
   The winner's-curse re-score (§5.4a) is the cheapest way to separate designs that are
   *reliably* good from ones that got a lucky draw — and it is a discriminator the baseline
   does not have.
2. **Larger backbone perturbation.** Fixed-backbone redesign is the easy case. Varying CDR-H3
   *length*, or grafting, breaks the geometric guarantee that makes DockQ near-free here.
3. **Challenge 2's de novo placement**, where the post-cutoff test already shows the gates bite
   hard (median Fab DockQ 0.291 on unseen complexes).

**Precision caveat:** at n=20 a 100% viability rate has a 95% CI of about [83%, 100%] (rule of
three). The supported claim is "naive MPNN clears these gates at a high rate", not "always".

---

## 7. State

**Built and exercised end to end:** design → validate → fold → score → gate → rank, with
`designs.parquet` as the queryable output. 20/20 folds, 20/20 scored, zero failures.

**Open.** M3 not started. `submit/` still empty (packaging; nothing needs it yet). Fold batching
still outstanding (~1.8×). The second-predictor question still deferred, and this session gives
no reason to revisit it.
