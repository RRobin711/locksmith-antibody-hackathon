# A decoy epitope on the far face of PD-1

`scripts/95_decoy_patch_control.py`, seed 20260928. CPU only — selection and verification run before any GPU is rented.

This is the control that can **falsify** the conditioning result. Every test run so far compares one conditioned arm against a resampled null on the same structures, so none of them can separate *"the hotspots steered RFdiffusion"* from *"RFdiffusion docks antibodies on that face of PD-1 anyway"*. Nothing has ever asked it for a different face.

## The patch, and why it is fair

| property | epitope (PD-L1 footprint) | decoy | constraint |
|---|---|---|---|
| residues | 26 | **26** | equal — the statistic scales with size |
| RMS spread | 9.85 Å | **10.15 Å** | matched ±0.5 Å (§D4) |
| overlap | — | **0 residues** | zero, or one dock satisfies both |
| min SASA (isolated chain) | — | **≥ 15 Å²** | a buried patch fails for geometry, not conditioning |
| angle from epitope, about the centroid | 0° | **165.9°** | maximised |
| centroid separation | — | **14.3 Å** | |

## The two numberings — do not mix them

RFdiffusion renumbers its output continuously across chains, so a check keyed on the wrong form returns a clean, believable **zero**. Both are emitted:

```
hotspots for RFdiffusion (5GGS chain Z author numbering, relabelled T):
  T34,T36,T37,T38,T39,T40,T41,T43,T49,T51,T53,T55,T95,T96,T97,T98,T99,T100,T101,T102,T103,T104,T105,T107,T109,T141
ordinals for pod/check_backbone.py (0-based within chain T):
  3,5,6,7,8,9,10,12,18,20,22,24,64,65,66,67,68,69,70,71,72,73,74,76,78,110
```

Written to `pod/inputs_decoy_hotspots.txt` and `results/decoy_patch.json`.

## Two pre-run checks, both free

**Separation.** Nearest decoy↔epitope residue pair: **4.9 Å** centroid to centroid (mean 19.4 Å). The sets are disjoint by construction, but they share an *edge*, so a dock straddling the boundary could partially satisfy both. Recorded as a limitation rather than designed away — pushing the patches further apart on a 113-residue IgV domain costs either the size match or the spread match.

**Behavioural disjointness.** The 18 EXISTING conditioned backbones, scored against this decoy: mean `frac_iface_on_decoy` = **0.000**, against `frac_iface_on_epitope` = **0.712**. So an arm aimed at the real epitope never touches the decoy, and the two patches separate cleanly in practice and not merely on paper. *This is what makes the decoy run interpretable: the measurement already distinguishes the two faces before any new backbone exists.*

## Pre-registered reading of the outcome

Measured on the decoy-conditioned backbones, against the **decoy** and against the **real epitope**:

| outcome | meaning |
|---|---|
| `frac_iface_on_decoy` high, `frac_iface_on_epitope` low | conditioning works; the published result is about our hotspots |
| both low | the decoy face is simply not dockable — **inconclusive**, not a pass |
| `frac_iface_on_epitope` still ≈ 0.712 | **the published result is refuted**: it was reading RFdiffusion's prior, not our conditioning |

The conditioned arm's own value is **0.712** on its target and **0.172** against a shape-matched null, so those are the two reference points. Note the middle row: a null result here does not rescue the claim, and saying so before the run is the point of writing it down now.

