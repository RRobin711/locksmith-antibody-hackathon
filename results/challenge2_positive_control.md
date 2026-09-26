# Positive control: the Challenge 2 fold configuration is sound

**2026-09-22.** Run against the decision rule pre-registered in
[the pre-registration](prereg_2026-09-22_positive_control.md), written before the folds.

## Result

| arm | construct | lengths | predicted | **measured ipSAE** |
|---|---|---|---|---|
| **A** | WT pembrolizumab **Fab** + PD-1 | 219 + 217 + 123 | ≥ 0.75 | **0.776** |
| **B** | WT pembrolizumab **Fv** + PD-1 | 119 + 111 + 123 | ≥ 0.60 | **0.842** |

Both through the identical `72_challenge2_fold.py` call: Boltz-2, seed 1, 3 recycling
steps, antigen MSA only, handbook §4.2.2 antigen.

**Verdict by the pre-registered rule: B ≥ 0.60, so the Fv construct is sound and `0/30`
is a real property of the designs. Challenge 2's end state STANDS.**

## The hypothesis this was built to test, and why it failed

The worry was specific and well-grounded. The Challenge 2 designs are **Fv only** (119 aa
heavy, 107 light — RFantibody produces variable domains), so they were folded as Fv. But
`PLAN.md` G1c records a gate this project **failed** on 2026-09-17:

> *"Fv ipSAE reliability 0.61 vs Fab 0.96 (under-constrained elbow) … Fab-only adopted."*

Every Challenge 1 number since has been folded as Fab. Challenge 2 was folded as Fv
without re-examining that. `0/30` failing on the single metric most sensitive to chain
placement is exactly the symptom an under-constrained elbow would produce.

**The control refutes it, and by a wider margin than predicted.** The Fv arm does not
merely clear 0.60 — at **0.842 it beats the Fab arm's 0.776**.

That is consistent with what G1c actually measured, which the pre-registration said
explicitly before the numbers existed: G1c measured **reliability** (seed-to-seed
variance), not **absolute level**. A construct can be noisy across seeds and still place a
real cognate pair confidently on any given seed. The Fab/Fv ordering here is unremarkable —
ipSAE's `d0` normalisation depends on chain size, so a smaller complex is not penalised —
and the point is not that Fv is better, only that it is **not the explanation**.

## The comparison that matters

Same pipeline, same construct type, near-identical chain lengths, same antigen, same
seed, same recycling:

| | ipSAE |
|---|---|
| wild-type pembrolizumab **Fv** (119/111) | **0.842** |
| best of 30 designs (119/107) | **0.372** |
| median of 30 designs | **0.006** |
| §7.2 gate | 0.600 |

The gap is not subtle and it is not attributable to the configuration. A real cognate pair
goes through this exact path and lands well above the gate; the designs do not.

## What this does and does not license

**Does:** `0 of 30` is a statement about the designs, not about my fold settings. The
pipeline can demonstrably produce a high-confidence interface when handed one.

**Does not:** say the designs fail to bind. ipSAE is Boltz-2's uncertainty about chain
placement. `results/skempi_validity.md` shows this stack does not track measured affinity
in either direction. A predictor that will not place a novel complex is telling you about
the predictor's training distribution as much as about the molecule.

**Does not** close the sampling objection — that is `scripts/78_challenge2_reseed.py`,
which re-folds the top 5 at recycling 10 across 3 seeds.

## Why the control was worth running even though it "passed"

It was built to break the result, and stated in advance what breaking would look like. Had
arm B come back below 0.60 with arm A above 0.75, the rule required withdrawing the
Challenge 2 finding and rewriting `STATE.md`. That it passed is worth something only
because failing was a live, specified outcome — and because the hypothesis it tested came
from this project's own recorded evidence rather than from a general worry.
