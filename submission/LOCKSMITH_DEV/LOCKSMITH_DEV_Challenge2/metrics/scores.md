# Our own recomputation of the seven scored metrics

Design `bb_8_0`, folded with Boltz-2 on the handbook's §4.2.2 antigen with a matched antigen alignment (`pd1_123_handbook.csv`, 3407 sequences, **verified used**: processed MSA width 123 = antigen length 123). Every Challenge 2 fold before 2026-09-23 used an alignment Boltz silently discarded; see `methods_and_limitations.md`.

Conventions: `band_value=top`, `netsolp_construct=fv`, `netsolp_chain_agg=min`.

**Seven, not eight — DockQ is excluded.** §5.2 applies DockQ to Challenge 1 only, because a de novo design has no reference structure. Every metric below is computed from the two files in `structures/`, which we generated. **A confidently wrong pose scores exactly like a right one.**

## The submitted structure (`model_0`)

| metric | value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1110.500 | good | 10.0 |
| `cdrh3_identity` | 18.200 | good | 10.0 |
| `contacts` | 99.000 | good | 10.0 |
| `dg` | -10.900 | medium | 8.0 |
| `iface_plddt` | 88.620 | good | 10.0 |
| `ipsae` | 0.904 | good | 10.0 |
| `netsolp` | 0.555 | medium | 8.0 |

**Final: 93.6 / 100. Viable: True.**

## The central estimate — median of five diffusion samples

`model_0` is Boltz's own top-ranked output and therefore an **argmax by construction**, not a draw. The median over five samples is what any claim here rests on.

| metric | model_0 | median of 5 | spread across 5 |
|---|---|---|---|
| `cdr_sasa` | 1110.500 | **1159.600** | 1110.500 – 1241.700 |
| `cdrh3_identity` | 18.200 | **18.200** | 18.200 – 18.200 |
| `contacts` | 99.000 | **98.000** | 88.000 – 115.000 |
| `dg` | -10.900 | **-10.900** | -11.600 – -10.000 |
| `iface_plddt` | 88.620 | **88.620** | 86.970 – 89.680 |
| `ipsae` | 0.904 | **0.859** | 0.819 – 0.904 |
| `netsolp` | 0.555 | **0.555** | 0.555 – 0.555 |

Composite on the median metrics: **93.6**. Per-sample composites: 93.6, 93.6, 93.6, 93.6, 93.6.

### Viable on **5 of 5** diffusion samples.

Every sample clears the §7.2 ipSAE cutoff. The median clears it by **0.259** and the *worst* sample reads **0.819** — still above the 0.80 Good edge. The composite is **93.6 on all five samples**, so the shipped `model_0` and the median agree exactly and nothing here depends on which draw was kept.