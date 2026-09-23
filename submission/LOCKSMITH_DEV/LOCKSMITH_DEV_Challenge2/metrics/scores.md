# Our own recomputation of the seven scored metrics

Design `bb_1_0_dldesign_0`, folded with Boltz-2 on the handbook's §4.2.2 antigen **with a matched antigen alignment** (`pd1_123_handbook.csv`, 3407 sequences). Every previous Challenge 2 fold in this project used an alignment Boltz silently discarded; see `methods_and_limitations.md`.

Conventions: `band_value=top`, `netsolp_construct=fv`, `netsolp_chain_agg=min`.

**Seven, not eight — DockQ is excluded.** §5.2 applies DockQ to Challenge 1 only, because a de novo design has no reference structure. Every metric below is computed from the two files in `structures/`, which we generated. **A confidently wrong pose scores exactly like a right one.**

## The submitted structure (`model_0`)

| metric | value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1265.400 | good | 10.0 |
| `cdrh3_identity` | 33.300 | good | 10.0 |
| `contacts` | 71.000 | good | 10.0 |
| `dg` | -9.500 | poor | 5.0 |
| `iface_plddt` | 81.400 | good | 10.0 |
| `ipsae` | 0.855 | good | 10.0 |
| `netsolp` | 0.617 | medium | 8.0 |

**Final: 90.0 / 100. Viable: True.**

## The central estimate — median of five diffusion samples

`model_0` is Boltz's own top-ranked output and therefore an **argmax by construction**, not a draw. The median over five samples is what any claim here rests on.

| metric | model_0 | median of 5 | spread across 5 |
|---|---|---|---|
| `cdr_sasa` | 1265.400 | **1226.700** | 1084.500 – 1265.400 |
| `cdrh3_identity` | 33.300 | **33.300** | 33.300 – 33.300 |
| `contacts` | 71.000 | **99.000** | 71.000 – 115.000 |
| `dg` | -9.500 | **-12.100** | -12.600 – -9.500 |
| `iface_plddt` | 81.400 | **79.550** | 76.990 – 81.400 |
| `ipsae` | 0.855 | **0.637** | 0.423 – 0.855 |
| `netsolp` | 0.617 | **0.617** | 0.617 – 0.617 |

Composite on the median metrics: **91.2**. Per-sample composites: 90.0, 91.2, 87.6, 91.2, 87.6.

### **Viable on 3 of 5 diffusion samples, not 5 of 5.**

Two of the five fall below the §7.2 ipSAE cutoff. The median clears it by **0.037**, and the worst sample reads 0.423. This is a thin pass and is reported as one.