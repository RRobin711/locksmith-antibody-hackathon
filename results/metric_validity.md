# Do the scored metrics measure the design, or the sampler?

`scripts/52_metric_validity.py` — zero new folds. Written 2026-09-20 after an
independent audit pointed out that six days had been spent on ranking precision and
none on whether the ranked quantities carry design information.

## 1. Intraclass correlation — how much of each metric is the design?

Within-design variance from **20 designs x 7 seeds**; total variance from the
**239-design single-seed pool**. `ICC = 1 - within/total`.

| metric | within-seed sd | pool sd | **ICC** | reading |
|---|---|---|---|---|
| `dg` | 0.491 | 0.794 | **0.618** | usable |
| `ipsae` | 0.021 | 0.035 | **0.647** | usable |
| `dockq` | 0.014 | 0.039 | **0.870** | usable |
| `iface_plddt` | 0.886 | 2.224 | **0.841** | usable |
| `contacts` | 6.003 | 6.013 | **0.003** | **pure seed noise — carries no design information** |
| `cdr_sasa` | 50.552 | 46.063 | **0.000** | **pure seed noise — carries no design information** |

**`contacts`, `cdr_sasa` are pure sampler noise.** Their entire
design-to-design variation is which random seed Boltz drew. Any analysis that
compared them between designs — including the 2026-09-20 hotspot ablation, whose
verdict branch was decided on `contacts` — was comparing two noise draws.

## 2. Which metrics can move `final` at all?

A metric whose whole observed range sits inside one band contributes a constant.

| metric | observed range | Good edge | % of pool already Good | can it rank? |
|---|---|---|---|---|
| `ipsae` | 0.623 – 0.873 | 0.8 | 51% | yes |
| `dockq` | 0.596 – 0.777 | 0.8 | 0% | no — constant |
| `dg` | -15.500 – -10.600 | -12.0 | 62% | yes |
| `contacts` | 88.000 – 120.000 | 25 | 100% | no — constant |
| `iface_plddt` | 83.200 – 94.110 | 80 | 100% | no — constant |
| `cdr_sasa` | 1383.400 – 1648.300 | 600 | 100% | no — constant |
| `cdrh3_identity` | 15.4 – 46.2 | <70 | 100% | no — constant |
| `netsolp` | 0.562 – 0.619 | 0.70 | 0% | no — constant |

**5 of the 8 rubric metrics are constants across this pool.** `contacts`, `iface_plddt`, `cdr_sasa` and `cdrh3_identity` are pinned at Good; `netsolp` is pinned
at Medium. The eight-metric harness ranks on three: `dg`, `ipsae`, `dockq`.

## 3. How far does the predicted CDR-H3 move from pembrolizumab's crystal loop?

Cα RMSD over CDR-H3 (heavy 96–108) after superposing on the **framework**.

| | CDR-H3 Cα RMSD vs the 5GGS crystal loop |
|---|---|
| 5GGS crystal copy 2 vs copy 1 (experimental floor) | **0.183 Å** |
| Boltz refolding pembrolizumab's OWN sequence | **0.400 Å** |
| **239 designs, CDR-H3 identity 15.4–46.2%** | **mean 1.119 Å**, median 1.030, sd 0.384, max 2.744 |
| designs within 1.5 Å of the crystal loop | **205 / 239 (86%)** |

**Replacing 7–11 of 13 CDR-H3 residues moves the predicted loop only 2.80× as far from the crystal as Boltz's own refold of the unmodified pembrolizumab sequence already is.** A sequence change of that size should not land a loop essentially on top of the parent's.

Read with the post-cutoff control: median Fab DockQ **0.291** on five complexes
released after Boltz-2's verified 2023-06-01 cutoff, against 0.818 on 5GGS. A model
that scores 0.29 on novel antibody–antigen pairs and 0.60–0.78 on 239 CDR-variants of
a training-set complex is reproducing the template it memorised, and the pool's DockQ
spread is variation *around* that template, not evidence about the designs.

