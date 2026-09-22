# Post-cutoff test — target selection (LOCKED 2026-09-17, before any fold)

Boltz-2 training cutoff **2023-06-01 on PDB release date**, verified in the paper
(see [[prereg_post_cutoff_test|the pre-registration]]). Margin adopted: release ≥ 2024-01-01.

## How the pool was built

RCSB search: release ≥ 2024-01-01, ≥3 protein entities, resolution ≤ 3.2 Å, ≤4 chains,
full-text "Fab antigen complex" → 63 entries. Filtered to exactly 3 polymer entities, total
≤700 residues, antigen ≥60 aa, and no promiscuous antigen (lysozyme / spike / HA / gp120 /
SARS / HIV / influenza) → **28 candidates**. Twelve were carried into the novelty screen.

## The novelty screen, and why full-chain identity is the wrong measure

Every antibody shares framework, so full-chain identity to *some* pre-cutoff antibody is high
for all of them — measured range **0.86–0.94**, and none exceeded the 0.95 rejection bar. That
number is nearly uninformative.

**CDR-H3 identity to the closest pre-cutoff relative** is the discriminator, and it separates
the pool properly. For each candidate the heavy chain was searched against the PDB (≥70%
identity), hits filtered to release < 2023-06-01, the 12 closest fetched, and every one
numbered with ANARCII to extract CDR-H3.

| PDB | released | CDR-H3 | closest pre-cutoff CDR-H3 | %id | via | verdict |
|---|---|---|---|---|---|---|
| **9JBQ** | 2024-09-11 | `VLYGNYVVYYTMDY` | `ARDDPGGGEYYFDY` | **21.4** | 5AZE (2015) | **SELECTED** |
| **9BQW** | 2025-08-06 | `ARDRRIVVVSAPGY` | `AKDGGKLWVYYFDY` | **28.6** | 6ZCZ (2020) | **SELECTED** |
| **8TBB** | 2024-08-28 | `ATSWETARILPGAFDI` | `ARGRDLAAFTKTAFDV` | **31.2** | 7S0C (2021) | **SELECTED** |
| **9W43** | 2026-07-01 | `ARLGNYGWTMDY` | `ARRGRYGLYAMDY` | **38.5** | 6IAP (2019) | **SELECTED** |
| **8RWB** | 2025-02-12 | `ARQGYGFDN` | `ARSWGYFDV` | **44.4** | 6PE7 (2019) | **SELECTED** |
| 9VXL | 2026-05-27 | `AGEPGERDPDAVDI` | `ARAPNYGDYVAFDI` | 42.9 | 6WH9 (2020) | rejected: 670 res, VRAM |
| 9YIO | 2026-02-04 | `ARSYYYGSSDAMDN` | `ARSDYYDSTHYFDY` | 50.0 | 5FB8 (2016) | rejected: weaker novelty |
| 13BS | 2026-07-15 | `ARDTLSGAFDY` | `ARDRGYYAFDI` | 54.5 | 3WSQ (2014) | rejected: weaker novelty |
| 9M5B | 2025-12-17 | `VREFYDAFDI` | `ARENFDAFDV` | 60.0 | 6YAX (2021) | rejected: weaker novelty |
| 8VUI | 2024-07-10 | `ARHGYGAMDY` | `ARYVYHALDY` | 60.0 | 4K94 (2018) | rejected: weaker novelty |
| 9O7G | 2026-05-13 | `ATWDSSLTAGRV` | `GTWDSSLSAHWV` | 66.7 | 7M8J (2022) | rejected: weaker novelty |
| 13BF | 2026-07-15 | `ARDYDLAFDY` | `AREGDGAFDY` | 70.0 | 3WLW (2015) | rejected: weaker novelty |

## The five

| PDB | released | antigen | class | total res | CDR-H3 novelty |
|---|---|---|---|---|---|
| 9JBQ | 2024-09-11 | PcrV | bacterial (*P. aeruginosa*) | 573 | 21.4% |
| 9BQW | 2025-08-06 | Decorin-binding protein A | bacterial (*Borrelia*) | 604 | 28.6% |
| 8TBB | 2024-08-28 | TIM-3 | human checkpoint receptor | 550 | 31.2% |
| 9W43 | 2026-07-01 | PD-1 | human checkpoint receptor | 539 | 38.5% |
| 8RWB | 2025-02-12 | ULBP6 | human MHC-I-like ligand | 601 | 44.4% |

Two bacterial and three human antigens; the closest pre-cutoff CDR-H3 relative is ≤44.4%
identical for all five. All released 7–37 months clear of the cutoff.

**9W43 is reported separately as well as pooled.** Its antigen is PD-1, which is
heavily represented in the PDB (5GGS, 5IUS and others, all pre-cutoff), so the antigen is
certainly memorised even though the antibody is novel. That makes it simultaneously the most
**deployment-relevant** point — a novel antibody against a known target is exactly Challenge 1
and 2 — and the most **flattered**. It satisfies the pre-registered criteria (PD-1 is not on
the excluded promiscuous list) so it is included, but the tension is stated rather than hidden.

**9VXL was rejected on the VRAM criterion, before folding.** 670 residues against the measured
549 res → 7,603 MiB; pair memory goes as ~N², predicting ~10.8 GB of 12.2 GB. 8RWB (601 res)
was taken instead at essentially the same novelty (44.4% vs 42.9%).
