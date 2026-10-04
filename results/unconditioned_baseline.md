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
| sequences | ProteinMPNN | **local CPU, free** | missing |
| fold + score | Boltz-2 | **local, free** | missing |

**Nothing here needs renting.** This table said `rented sm_86` for the sequencing row from 2026-09-22 to 2026-10-03, on reasoning that is true in every clause and false in its conclusion: RFantibody pins `torch==2.3.*`, DGL ships no matching ABI, and those wheels carry no PTX, so nothing reaches `sm_120` -- all correct, and the CPU was never in the comparison. RFantibody's bundled ProteinMPNN branches on `torch.cuda.is_available()` (`proteinmpnn_interface_design.py:85-90`) and generated 2 sequences in 1 second on `~/.venvs/rfab-cpu` (torch 2.2.1+cpu):

```
$ PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 8 -t 0.2
No GPU found, running ProteinMPNN on CPU
```

The one real obstacle is not a device problem and reads exactly like one: the CLI subprocesses a bare `python` (`cli/inference.py:294`), so without the venv's `bin` on PATH it dies `FileNotFoundError: 'python'`. See [register B12](retractions.md).

**The tool-matching objection goes with it.** The reason to rent rather than use standalone ProteinMPNN was that the conditioned arm used RFantibody's bundled copy. This *is* that copy -- same entry point as `pod/01_run.sh:69`, same weights (`ProteinMPNN_v48_noise_0.2.pt`), same `-t 0.2`. The arms would differ in **device**, not in code, weights or flags; state that on the result.

