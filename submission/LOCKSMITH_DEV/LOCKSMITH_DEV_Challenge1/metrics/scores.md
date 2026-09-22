# Our own recomputation of the eight scored metrics

**To reproduce the DockQ number below you MUST pass two flags.** At its
defaults DockQ exits 1 with no output on this submission:

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb
ERROR:root:For chains ['A'] no identical corresponding chain was found between in the native.

$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb \
      --allowed_mismatches 40 --mapping ABC:ABC
Total DockQ over 3 native interfaces: 0.816 with ABC:ABC model:native mapping
```

`--allowed_mismatches` defaults to **0**, and a redesigned CDR is by
definition not identical to the native, so the default refuses every
mutated design rather than scoring it low. `--mapping ABC:ABC` pins the
chain correspondence that §4.2.2 already fixes (A=heavy, B=light,
C=antigen); left free, DockQ searches, and a wrong mapping scores a good
design badly. Native reference: PDB **5GGS**, chains A/B/Z renamed A/B/C
(chain **C of the deposited crystal is a second copy of the antibody heavy
chain**, not the antigen -- using it silently scores the wrong interface).

Design `mpnn_T0.5_s104_036`, folded on the handbook's §4.2.2 constructs.
Conventions: `band_value=top`, `dockq_interface_agg=global`, `netsolp_construct=fv`, `netsolp_chain_agg=min`.

| metric | value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1565.000 | good | 10.0 |
| `cdrh3_identity` | 38.500 | good | 10.0 |
| `contacts` | 94.000 | good | 10.0 |
| `dg` | -12.700 | good | 10.0 |
| `dockq` | 0.816 | good | 10.0 |
| `iface_plddt` | 89.430 | good | 10.0 |
| `ipsae` | 0.824 | good | 10.0 |
| `netsolp` | 0.569 | medium | 8.0 |

Categories: binding 10.000, developability 8.000, novelty 10.000

**Final: 96.0 / 100. Viable: True.**

Band values are a handbook ambiguity; see `docs/` and
`results/handbook_conformance.md`. Under the three readings the same design
scores 84.0 / 90.0 / 96.0, which is a property of the reading, not the design.