# PRE-REGISTERED: does `diffusion_samples` move the submitted numbers?

**Written 2026-09-22 BEFORE the folds ran.** Predictions and the decision rule are fixed
here first.

## The question

Boltz's `--diffusion_samples` defaults to **1**. Every pose-derived metric in both
submissions — ipSAE, DockQ, PRODIGY ΔG, contacts, interface pLDDT, CDR SASA — is computed
from **one diffusion draw**. Recycling depth (a different axis) moved the Challenge 2
ipSAE by 0.601, so the sampling axis we never varied is the obvious remaining place for
the numbers to move.

This is the last unexamined inherited setting in the Challenge 2 path.

## Design

One run per challenge at `--diffusion_samples 5`, holding **everything else at exactly
the submitted settings**, then scoring all five emitted models.

| | construct | recycling | seed | MSA |
|---|---|---|---|---|
| Challenge 1 | Fab 232/218/123 | 3 | 71 | `--use_msa_server` |
| Challenge 2 | Fv 117/108/123 | 10 | 1 | cached PD-1 |

**Why one run of five rather than five runs of one.** Within a single invocation the MSA
is fetched once and shared across all five samples, so the spread is **pure diffusion
variability**. Five separate runs would confound the diffusion draw with MSA variation —
which matters for Challenge 1, whose submitted fold used a live MMseqs2 query.

`fold()` returns only `model_0`, so the extra models are scored directly.

## Predictions, before running

- **Challenge 1 (near-native, memorised complex).** Stable. ipSAE spread across the five
  samples **< 0.05**; no band changes; DockQ spread < 0.05. Rationale: this complex is
  invariant to recycling depth (range 0.036 over 3→20), and the same physics should make
  it invariant to the diffusion draw.
- **Challenge 2 (de novo, demonstrably unconverged).** Larger. ipSAE spread **> 0.10**,
  and I expect at least one sample to cross the 0.80 Good/Medium band edge. Rationale: it
  swung 0.601 across recycling depth; there is no reason to think the diffusion axis is
  quieter.

## Decision rule, fixed in advance

| outcome | verdict and action |
|---|---|
| **Any Challenge 2 sample below ipSAE 0.60** | **The design's VIABILITY is diffusion-sample dependent.** Far more serious than the depth finding, because it is the difference between a submission and a non-viable one. Must be disclosed at the top of the Challenge 2 docs and on the deck, and the "1 of 30 clears" framing must be re-examined. |
| **Challenge 2 spread crosses only the 0.80 band edge** | Same category as the recycling finding. Fold into the existing 93.6–96.0 envelope and widen it; no new severity. |
| **Challenge 1 spread crosses any band edge** | Challenge 1's 96.0 becomes an envelope too, and the claim "Challenge 1 survives the setting that overturned Challenge 2" must be qualified. |
| **Both stable within band** | The single diffusion draw is adequate for these two molecules. Close the item, state the measured spreads, and stop. |

No other reading is permitted after the fact. If the numbers land awkwardly, that is what
gets written down.
