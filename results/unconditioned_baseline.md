# The unconditioned arm — what is already on disk, and what is missing

`scripts/96_sequence_unconditioned.py`. CPU only. 18 unconditioned backbones, 18 conditioned, both from the 2026-09-21 pod run.

## Targeting baseline, computed here

| arm | n | mean `frac_iface_on_epitope` | sd | min | max |
|---|---|---|---|---|---|
| conditioned | 18 | **0.712** | 0.113 | 0.600 | 1.000 |
| **unconditioned** | 18 | **0.500** | 0.168 | 0.250 | 0.714 |

The unconditioned mean is not zero and should not be: the epitope is 26 of 113 residues on a small IgV domain, so a patch drawn at random already captures about a quarter of any interface. That denominator is why the 2026-09-21 two-arm comparison was replaced by the per-backbone patch null in `scripts/70` — and why the *decoy* control in `scripts/95` is the one that can actually fail.

| backbone | iface residues | frac on epitope |
|---|---|---|
| `un_10_0.pdb` | 7 | 0.286 |
| `un_11_0.pdb` | 5 | 0.400 |
| `un_12_0.pdb` | 9 | 0.444 |
| `un_13_0.pdb` | 10 | 0.300 |
| `un_14_0.pdb` | 3 | 0.667 |
| `un_15_0.pdb` | 7 | 0.714 |
| `un_16_0.pdb` | 9 | 0.556 |
| `un_17_0.pdb` | 8 | 0.500 |
| `un_18_0.pdb` | 3 | 0.667 |
| `un_1_0.pdb` | 10 | 0.700 |
| `un_2_0.pdb` | 11 | 0.636 |
| `un_3_0.pdb` | 4 | 0.250 |
| `un_4_0.pdb` | 10 | 0.300 |
| `un_5_0.pdb` | 7 | 0.714 |
| `un_6_0.pdb` | 6 | 0.667 |
| `un_7_0.pdb` | 8 | 0.375 |
| `un_8_0.pdb` | 3 | 0.333 |
| `un_9_0.pdb` | 8 | 0.500 |

## What is missing, and where it has to run

| step | tool | where | status |
|---|---|---|---|
| backbones | RFdiffusion | pod, 2026-09-21 | **done**, 18 on disk |
| targeting baseline | this script | local CPU | **done**, above |
| sequences | ProteinMPNN | **rented sm_86** | missing |
| fold + score | Boltz-2 | **local, free** | missing |

ProteinMPNN is the only step that needs renting, and not for capability reasons: RFantibody pins `torch==2.3.*`, DGL ships no matching ABI, and those wheels carry no PTX, so there is no forward-JIT to `sm_120`. The local RTX 5070 Ti is too **new**, not too small.

*Option worth pricing before spending anything:* the **standalone** ProteinMPNN builds on modern torch and would make this step free. The cost is that the conditioned arm used RFantibody's bundled copy, so a standalone run is no longer tool-matched — and a two-arm comparison where the arms were sequenced by different code is exactly the kind of uncontrolled difference this project keeps finding in other people's work. Matched and rented is the defensible choice; free and unmatched is defensible only if stated on the result.

