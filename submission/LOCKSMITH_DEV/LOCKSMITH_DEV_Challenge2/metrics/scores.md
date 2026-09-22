# Our own recomputation of the seven scored metrics

Design `bb_2_0_dldesign_1`, folded with Boltz-2 on the handbook's §4.2.2 antigen.
Conventions: `band_value=top`, `netsolp_construct=fv`, `netsolp_chain_agg=min`.

**Seven, not eight — DockQ is excluded.** §5.2 applies DockQ to Challenge 1 only, because a de novo design has no reference structure. Note what that removes: DockQ was the only metric that compares the prediction to anything external. Every metric below is computed from the two files in `structures/`, which we generated. **A confidently wrong pose scores exactly like a right one.**

| metric | value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1066.900 | good | 10.0 |
| `cdrh3_identity` | 30.000 | good | 10.0 |
| `contacts` | 98.000 | good | 10.0 |
| `dg` | -12.400 | good | 10.0 |
| `iface_plddt` | 83.580 | good | 10.0 |
| `ipsae` | 0.864 | good | 10.0 |
| `netsolp` | 0.562 | medium | 8.0 |

**Final: 96.0 / 100. Viable: True.**