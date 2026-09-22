# Reproducing every number we report

Written because an independent reviewer ran the obvious command and got a crash rather
than a score. **If a number cannot be reproduced from the artefact we hand over, we have
not really handed over the number.** Everything below was executed against the files in
this package, not recalled.

## The one that fails at defaults: DockQ

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb
ERROR:root:For chains ['A'] no identical corresponding chain was found between in the native.
$ echo $?
1
```

Exit status **1**, no score printed. The two flags are mandatory:

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb \
      --allowed_mismatches 40 --mapping ABC:ABC
Total DockQ over 3 native interfaces: 0.816 with ABC:ABC model:native mapping
  A,B  DockQ 0.931      (heavy-light framework -- near-perfect by construction)
  A,C  DockQ 0.723      <-- the interface the design actually creates
  B,C  DockQ 0.794
```

- `--allowed_mismatches` defaults to **0**. A redesigned CDR is not identical to the
  native by definition, so the default refuses *every* mutated design instead of scoring
  it badly. 40 is comfortably above our 15 substitutions.
- `--mapping ABC:ABC` pins the correspondence §4.2.2 already fixes (A=heavy, B=light,
  C=antigen). Left free, DockQ searches, and a wrong mapping scores a good design badly.

**Which number is "the" DockQ.** We report `global`, DockQ v2's own
Total over the three interfaces, because that is what an organiser reads off the tool's
summary line. The handbook says only that DockQ "returns a docking quality score between
0 and 1" and does not say how to combine three interfaces. Worth knowing when comparing:
the Total averages in the **heavy-light framework interface (0.931)**, which no design
touches and which is near-perfect by construction. The interface our design is actually
responsible for is **A-C = 0.723**.

## The native reference, and a trap in it

Use PDB **5GGS** with chains **A, B, Z** renamed to A, B, C. **Chain C of the deposited
crystal is a second copy of the antibody heavy chain, not the antigen.** Scoring against
raw chain C compares our antibody to an antibody and yields a confidently wrong number.
Our prepared reference is `data/refs/prepared/5ggs_ABZ.pdb` in the repository.

## The other seven

All seven are computed from the two files in `structures/` plus `sequences/design_1.fasta`,
with the conventions named in `metrics/scores.md`. The conventions that are NOT fixed by
the handbook, and therefore change the number:

| metric | convention | our setting | why it matters |
|---|---|---|---|
| all | `band_value` | `top` | the same design scores 84.0 / 90.0 / 96.0 under the three readings |
| `dockq` | `dockq_interface_agg` | `global` | one band |
| `netsolp` | `netsolp_construct` | `fv` | Fv, per §6.2.1; we used Fab until 2026-09-20 |
| `netsolp` | `netsolp_chain_agg` | `min` | VH 0.699 vs VL 0.569 -- `min` picks the light chain |
| `cdr_sasa` | `cdr_sasa_chains` | `AB` | none here; Good either way |

**NetSolP model choice is not cosmetic.** NetSolP ships three predictors and on
pembrolizumab -- a licensed antibody that must pass developability -- they score
0.733 / 0.637 / 0.379 on VH against a 0.50 cutoff. Only the full ESM1b 5-fold ensemble
clears it. The CLI default would fail a marketed drug and look like a design problem.
We use **ESM1b**.

## Validating the package itself

`scripts/58_validate_submission.py` re-derives all eight metrics from **this folder
alone** -- no run directory, no cached score -- and exits non-zero on any structural
problem or failed cutoff.
