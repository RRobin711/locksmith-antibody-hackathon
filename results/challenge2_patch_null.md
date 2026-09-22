# Is the interface on the PD-L1 epitope, or just on *a* patch of PD-1?

`scripts/70_epitope_patch_null.py`, seed 20260922, 2000 draws per backbone, 18 conditioned backbones retrieved from the pod volume.

The pilot's published test compared conditioned against unconditioned backbones (d=1.47). That asks whether conditioning does anything at all. **This asks the question that can fail: does the interface sit on the epitope we AIMED at, rather than on an equally-sized patch somewhere else on the same antigen?** It costs nothing -- same files, no new folds.

| backbone | iface res | real epitope | contiguous-patch null (mean, p95) | empirical p | uniform-26 null |
|---|---|---|---|---|---|
| `bb_10_0.pdb` | 10 | **0.600** | 0.155, 0.500 | 0.0005 | 0.228 |
| `bb_11_0.pdb` | 4 | **0.750** | 0.138, 0.500 | 0.0090 | 0.227 |
| `bb_12_0.pdb` | 7 | **0.714** | 0.147, 0.429 | 0.0005 | 0.229 |
| `bb_13_0.pdb` | 6 | **0.667** | 0.147, 0.500 | 0.0275 | 0.231 |
| `bb_14_0.pdb` | 15 | **0.600** | 0.156, 0.467 | 0.0005 | 0.229 |
| `bb_15_0.pdb` | 14 | **0.714** | 0.162, 0.429 | 0.0005 | 0.231 |
| `bb_16_0.pdb` | 7 | **0.857** | 0.193, 0.571 | 0.0100 | 0.229 |
| `bb_17_0.pdb` | 12 | **0.833** | 0.166, 0.417 | 0.0005 | 0.231 |
| `bb_18_0.pdb` | 5 | **1.000** | 0.137, 0.400 | 0.0005 | 0.233 |
| `bb_1_0.pdb` | 8 | **0.625** | 0.147, 0.500 | 0.0125 | 0.226 |
| `bb_2_0.pdb` | 8 | **0.625** | 0.127, 0.500 | 0.0285 | 0.231 |
| `bb_3_0.pdb` | 8 | **0.625** | 0.169, 0.625 | 0.0785 | 0.235 |
| `bb_4_0.pdb` | 8 | **0.875** | 0.152, 0.625 | 0.0005 | 0.233 |
| `bb_5_0.pdb` | 11 | **0.727** | 0.166, 0.455 | 0.0005 | 0.234 |
| `bb_6_0.pdb` | 10 | **0.600** | 0.121, 0.400 | 0.0005 | 0.232 |
| `bb_7_0.pdb` | 11 | **0.636** | 0.150, 0.545 | 0.0095 | 0.232 |
| `bb_8_0.pdb` | 9 | **0.667** | 0.171, 0.556 | 0.0115 | 0.232 |
| `bb_9_0.pdb` | 10 | **0.700** | 0.169, 0.500 | 0.0005 | 0.229 |

**Pooled.** Real epitope mean **0.712** against a contiguous surface patch of the same size at **0.154**, and 26 residues drawn uniformly at **0.231**. 17/18 backbones beat their own contiguous-patch null at p<0.05.

The target chain has 113 residues and the epitope is 26 of them, so a uniformly-drawn set captures about 0.230 of any interface by construction. **That is why the uniform column is the strawman and the contiguous column is the test** -- a real dock lands on contiguous surface, so the null must too.

## What this does and does not establish

**Does:** the conditioning put the designed loops on the intended face of PD-1 rather than on an arbitrary patch of equal size, and the comparison is deterministic per backbone rather than a two-sample test with an undeclared stopping rule.

**Does not:** that any of these backbones binds. Targeting is not affinity. The epitope is also the largest contiguous patch the loops could plausibly reach given where RFdiffusion was told to build, so a portion of this effect is mechanical rather than evidential.
