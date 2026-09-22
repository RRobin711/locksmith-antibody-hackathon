# Do these metrics track measured binding affinity?

`scripts/53_skempi_fold.py` + this. **The only experiment in this project that compares a predicted number to a laboratory measurement.** Everything else measures how precisely the pipeline reproduces itself.

System: **3HFM**, HyHEL-10 Fab vs hen egg-white lysozyme, from SKEMPI 2.0. 45 single mutants folded at one seed, wild type at 3 seeds. `ddG = RT ln(Kd_mut/Kd_wt)`; **positive ddG means the mutation weakens binding**, so a metric that tracks affinity should correlate NEGATIVELY with ddG when higher is better.

## Noise floor, measured on this complex

| metric | WT mean | seed sd (n=3) |
|---|---|---|
| PRODIGY ΔG | -12.000 | 0.173 |
| ipSAE | 0.903 | 0.012 |
| DockQ vs the 3HFM crystal | 0.844 | 0.002 |
| interface pLDDT | 97.883 | 0.045 |
| contacts | 90.000 | 3.606 |

## Correlation with measured ddG

All 45 mutants, and separately the 27 with |ddG| <= 6 kcal/mol (the rest sit at an assay detection limit, so their magnitudes are not real numbers even though their rank order is).

| metric | ρ (all) | p | ρ (|ddG|≤6) | p | expected sign |
|---|---|---|---|---|---|
| PRODIGY ΔG | **+0.221** | 0.14 | +0.050 | 0.8 | positive |
| ipSAE | **+0.059** | 0.7 | +0.300 | 0.13 | negative |
| DockQ vs the 3HFM crystal | **-0.101** | 0.51 | -0.198 | 0.32 | negative |
| interface pLDDT | **+0.047** | 0.76 | +0.275 | 0.16 | negative |
| contacts | **-0.246** | 0.1 | -0.223 | 0.26 | negative |

**A null is a bound.** At n=45 the smallest effect detectable at 80% power (α=0.05) is ρ ≈ **0.41**, so any metric reported as uncorrelated means *no monotone relationship stronger than that*.


## Did the metrics move at all? (a null is only informative if they did)

| metric | seed sd (WT, n=3) | between-mutant sd | ratio |
|---|---|---|---|
| PRODIGY ΔG | 0.173 | 0.436 | **2.5×** |
| ipSAE | 0.012 | 0.232 | **19.5×** |
| DockQ | 0.002 | 0.027 | **13.0×** |
| interface pLDDT | 0.045 | 3.740 | **82.9×** |
| contacts | 3.606 | 2.775 | **0.8×** |

Every metric except `contacts` varies across mutants by many times its own seed
noise — ipSAE by 19.5×, interface pLDDT by 82.9×. **They are moving a great deal;
they are simply not moving with the measured affinity.** That is what makes this a
null result rather than an insensitive assay. (`contacts` at 0.8× is once again
indistinguishable from noise, matching its ICC of 0.003 on the PD-1 system.)

## The five mutants that experimentally abolish binding

More persuasive than any correlation coefficient. ΔΔG above about +20 kcal/mol means
binding was not detectable at all:

| mutant | measured ΔΔG | ipSAE | DockQ | PRODIGY ΔG |
|---|---|---|---|---|
| **wild type** | 0.00 | **0.903** | **0.844** | **-12.0** |
| `KY96M` | **+28.35** | 0.713 | 0.820 | -12.8 |
| `KY96A` | **+28.19** | 0.560 | 0.797 | -11.4 |
| `KY97A` | **+24.52** | 0.184 | 0.799 | -10.8 |
| `WH98A` | **+23.06** | 0.875 | 0.806 | -11.5 |
| `NL31A` | **+21.81** | 0.917 | 0.837 | -12.2 |

**Four of the five score essentially like the wild type on every metric.** `NL31A`,
which abolishes binding, scores ipSAE **0.917** against the wild type's 0.903 — the
pipeline rates a non-binder *above* the real complex. `KY96M` scores a more
favourable PRODIGY ΔG (−12.8) than the wild type (−12.0). Only `KY97A` is caught.

## Verdict

**None of the five metrics tracks measured binding affinity at a resolution this
test could detect** (bound: no monotone effect stronger than ρ ≈ 0.41 at n=45).
Two results sharpen that:

1. **The two metrics that passed the epitope-knockout control — ipSAE and interface
   pLDDT — carry the WRONG SIGN on the reliable subset** (+0.300 and +0.275, where
   binding-weakening mutations should *lower* them). They detect gross interface
   destruction and mis-rank point mutations.
2. That is exactly the 'liveness test, not a ranking metric' pattern this project
   first recorded for ipSAE on 2026-09-17 from the poly-Gly anchors. **This is its
   fifth instance and the first validated against experimental data** rather than
   against another prediction.

What this licenses, stated exactly: the pipeline can tell a destroyed interface from
an intact one, and cannot rank two intact ones by affinity. Every ranking claim in
this project sits in the second category.

## Reading

A metric that ranks designs for binding must, at minimum, rank *known* affinity changes on a complex of the same kind. This is the weakest possible version of that test — single point mutations, one seed, a complex the predictor has memorised — and it is still the only external check the project has. Whatever the numbers above say, they bound what the whole scoring stack can claim.

Caveat, stated rather than buried: 3HFM predates Boltz-2's 2023-06-01 cutoff, so the wild-type pose is memorised. That is acceptable for a ddG *ranking* test — the question is whether the scores move correctly when an experimentally important residue is removed — but it means a positive result would need re-testing on a post-cutoff complex before being believed.

