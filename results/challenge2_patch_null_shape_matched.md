# Shape-matching the epitope-patch null

`scripts/94_shape_matched_patch_null.py`, seed 20260928, 2000 draws/backbone, 18 backbones. Tolerance ±0.5 Å on RMS spread. No new folds, no GPU.

Register **§D4** flagged that the contiguous-patch null in `scripts/70_epitope_patch_null.py` draws patches **more compact** than the real epitope, because it takes the *k nearest* residues to a seed. A compact patch is the worst shape for capturing a spread-out designed interface, so the null scores too low and the test is anti-conservative. D4 could not say by how much. This can.

| backbone | iface | real | compact null | **shape-matched null** | uniform | p (compact) | **p (matched)** |
|---|---|---|---|---|---|---|---|
| `bb_10_0.pdb` | 10 | **0.600** | 0.159 | **0.165** | 0.231 | 0.0005 | **0.0135** |
| `bb_11_0.pdb` | 4 | **0.750** | 0.139 | **0.147** | 0.237 | 0.0050 | **0.0130** |
| `bb_12_0.pdb` | 7 | **0.714** | 0.144 | **0.185** | 0.231 | 0.0005 | **0.0095** |
| `bb_13_0.pdb` | 6 | **0.667** | 0.141 | **0.157** | 0.230 | 0.0260 | **0.0230** |
| `bb_14_0.pdb` | 15 | **0.600** | 0.153 | **0.171** | 0.232 | 0.0005 | **0.0030** |
| `bb_15_0.pdb` | 14 | **0.714** | 0.161 | **0.177** | 0.230 | 0.0005 | **0.0010** |
| `bb_16_0.pdb` | 7 | **0.857** | 0.198 | **0.250** | 0.231 | 0.0080 | **0.0080** |
| `bb_17_0.pdb` | 12 | **0.833** | 0.158 | **0.189** | 0.232 | 0.0005 | **0.0005** |
| `bb_18_0.pdb` | 5 | **1.000** | 0.129 | **0.133** | 0.229 | 0.0005 | **0.0015** |
| `bb_1_0.pdb` | 8 | **0.625** | 0.147 | **0.145** | 0.234 | 0.0090 | **0.0120** |
| `bb_2_0.pdb` | 8 | **0.625** | 0.134 | **0.140** | 0.232 | 0.0305 | **0.0125** |
| `bb_3_0.pdb` | 8 | **0.625** | 0.164 | **0.165** | 0.236 | 0.0730 | **0.0115** |
| `bb_4_0.pdb` | 8 | **0.875** | 0.155 | **0.186** | 0.231 | 0.0005 | **0.0010** |
| `bb_5_0.pdb` | 11 | **0.727** | 0.171 | **0.194** | 0.225 | 0.0005 | **0.0010** |
| `bb_6_0.pdb` | 10 | **0.600** | 0.119 | **0.137** | 0.227 | 0.0005 | **0.0040** |
| `bb_7_0.pdb` | 11 | **0.636** | 0.148 | **0.161** | 0.232 | 0.0085 | **0.0040** |
| `bb_8_0.pdb` | 9 | **0.667** | 0.161 | **0.188** | 0.224 | 0.0095 | **0.0110** |
| `bb_9_0.pdb` | 10 | **0.700** | 0.173 | **0.204** | 0.233 | 0.0005 | **0.0065** |

## Summary

| quantity | value |
|---|---|
| mean real `frac_iface_on_epitope` | **0.712** |
| mean compact-patch null | 0.153 |
| mean **shape-matched** null | **0.172** |
| mean uniform null (= k/n_target, the denominator) | 0.231 |
| backbones at p < 0.05, compact null | **17/18** |
| backbones at p < 0.05, shape-matched null | **18/18** |
| mean epitope RMS spread | 10.09 Å |
| mean compact-patch RMS spread | 7.76 Å |
| mean shape-matched RMS spread | 10.10 Å |
| rejection acceptance rate | 0.163 |
| draws that never found a matched patch | 0 |

**The mismatch was worth +0.019 on the null's mean** (0.153 → 0.172), against a real value of 0.712 — so on the MEAN, §D4 is right and the old null was anti-conservative.

**But the mean is not what the test uses, and on the tail the sign reverses.**

| null | mean | sd | p99 | max |
|---|---|---|---|---|
| compact (old) | 0.153 | 0.185 | 0.554 | 0.602 |
| shape-matched | 0.172 | 0.155 | 0.605 | 0.788 |

The matched null is **less variable** (sd 0.185 → 0.155) but its extreme quantiles are **higher**, not lower (p99 0.554 → 0.605, max 0.602 → 0.788). So this is not a story about a thinner tail, and per-backbone the p-values mostly move the way the higher mean predicts: **12 rose, 4 fell, 2 unchanged**.

**One backbone decides the headline.** `bb_3_0.pdb` was the single failure under the old null at α = 0.05, and it moves **p 0.0730 → 0.0115**. Its real value (0.625) sat just inside the compact null's fat upper shoulder; under a shape-matched null the mass sitting above 0.625 specifically is smaller, even though the null's mean and its 99th percentile both rise. The count goes **17/18 → 18/18**.

*Read this as a robustness check that passed, and nothing more.* §D4's diagnosis was correct — the old patches really were too compact (7.76 Å against the epitope's 10.09 Å) and the null's mean really was too low. The correction is worth **+0.019** against a real value of 0.712, i.e. the flagged defect was never carrying the result. What it does change is the one marginal backbone, and it changes it in our favour, which is the direction that deserves the most suspicion — hence the full distribution table above rather than a single summary number.

