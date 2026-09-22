# Does batched folding reproduce the single-fold path?

`scripts/34_verify_batching.py`, seed 11 (used nowhere else so these folds cannot be mistaken for campaign data).

## Tier 0 — is the single-fold path itself reproducible?

Same design, same seed, two separate invocations of the EXISTING path.

| run | PDB sha256 (16) | seconds |
|---|---|---|
| a | `11b06b4b58b2b0e0` | 85 |
| b | `11b06b4b58b2b0e0` | 84 |

**Bitwise reproducible: True.** So byte-identity is a meaningful acceptance test for the batching code, and a tier-1 failure would implicate that code rather than the GPU.

## Tier 1 — batch of 1 against the single path

| path | PDB sha256 (16) |
|---|---|
| single | `11b06b4b58b2b0e0` |
| batch-of-1 | `11b06b4b58b2b0e0` |

**Identical: True.**

## Tier 2 — batch of 6, DockQ equivalence

Tolerance is **±0.054 DockQ**, three times the measured 0.018 seed sd. Kernel selection depends on tensor shape, so a batched forward pass can differ in the low-order bits even at a fixed seed; the question is whether it differs by more than the noise we already tolerate between seeds.

| design | DockQ single | DockQ batched | Δ | within ±0.054 |
|---|---|---|---|---|
| mpnn_T0.1_s101_001 | 0.728 | 0.743 | +0.015 | ✓ |
| mpnn_T0.1_s101_002 | 0.703 | 0.710 | +0.007 | ✓ |
| mpnn_T0.1_s101_003 | 0.709 | 0.698 | -0.011 | ✓ |
| mpnn_T0.1_s101_004 | 0.736 | 0.752 | +0.016 | ✓ |
| mpnn_T0.1_s101_005 | 0.708 | 0.733 | +0.025 | ✓ |
| mpnn_T0.1_s101_006 | 0.752 | 0.752 | +0.000 | ✓ |

**Equivalent: True.**  Batch failures: 0

## Tier 3 — the speed-up, measured

| quantity | value |
|---|---|
| single-fold wall clock (mean of 2) | 84 s |
| batch of 6: total | 434 s |
| batch of 6: per fold | **72 s** |
| **speed-up** | **1.16x** |

Projected against the ~1.8x that justified building this: BELOW the projection. At 72 s/fold the 239-design primary arm would take 4.8 h instead of 5.6 h.

## Verdict: ACCEPTED

