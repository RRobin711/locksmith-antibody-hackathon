# PRE-REGISTERED: positive control for the Challenge 2 fold configuration

**Written 2026-09-22 BEFORE the folds were run.** Predictions and the decision rule are
fixed here first, because the whole point is to stop me interpreting whatever comes back.

## The question

`0 of 30` Challenge 2 designs cleared the §7.2 cutoffs, all failing `ipsae` (best 0.372
against ≥0.60). Is that a property of **the designs**, or of **my fold configuration**?

## Why this is a live worry and not a formality

The Challenge 2 designs are **Fv only** (119 aa heavy, 107 light — RFantibody produces
variable domains, no constant regions), so `scripts/72_challenge2_fold.py` folded Fv.

**This project already failed a gate on exactly that.** `PLAN.md` G1c, 2026-09-17:
*"Fv ipSAE reliability 0.61 vs Fab 0.96 (under-constrained elbow) … Fab-only adopted."*
Every Challenge 1 number since has been folded as Fab (`construct="fab"`). I folded
Challenge 2 as Fv without re-examining that decision.

`construct=` is only a provenance label — verified, it does not trim — so what actually
differs is the real sequence length. That is not a bug; it is a genuine confound.

## The two arms

Both use the **identical** call in `72_challenge2_fold.py`: Boltz-2, seed 1, 3 recycling
steps, `antigen_msa=PD1_MSA` (antigen gets an MSA, antibody chains do not), handbook
§4.2.2 antigen (123 aa).

| arm | construct | lengths | what it isolates |
|---|---|---|---|
| **A — Fab** | wild-type pembrolizumab Fab + PD-1 | 219 + 217 + 123 | the pipeline itself (MSA, antigen, settings) |
| **B — Fv** | wild-type pembrolizumab Fv + PD-1 | 119 + 111 + 123 | the Fv construct, matching the designs' 119/107 |

Both are a **cognate, crystallographically-solved, pre-training-cutoff pair**. Boltz-2 has
certainly memorised 5GGS. If it cannot place this, it can place nothing.

## Predictions, stated before running

- **Arm A (Fab): ipSAE ≥ 0.75**, most likely **0.80–0.85**. The Challenge 1 design on
  handbook Fab constructs measured **0.824**; wild type should be at least as good.
- **Arm B (Fv): ipSAE ≥ 0.60**, most likely **0.65–0.80**. G1c measured Fv *reliability*
  (seed-to-seed variance), not absolute level, so a real cognate pair should still dock
  confidently even if noisily.

## Decision rule, fixed in advance

| outcome | verdict |
|---|---|
| **B ≥ 0.60** | The Fv construct is sound. **`0/30` is a real property of the designs** and Challenge 2's end state stands. |
| **B < 0.60 and A ≥ 0.75** | **The construct is the confound.** `0/30` is NOT interpretable as a statement about the designs. The Challenge 2 result must be withdrawn pending a re-fold, and `STATE.md` rewritten. |
| **A < 0.75 and B < 0.60** | Something in the shared configuration is broken (antigen, MSA, recycling). Both the control and `0/30` are uninterpretable; debug the pipeline before any claim. |
| **B ≥ 0.60 but well below A** | The construct costs real confidence. `0/30` stands but must be reported **with** the Fv penalty quantified, not as a clean design failure. |

**No other reading is permitted after the fact.** If the numbers land somewhere awkward,
that is what gets written down.
