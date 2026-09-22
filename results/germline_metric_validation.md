# Validating the Challenge 2 germline novelty metric — 2026-09-21

Produced by `scripts/61_validate_germline.py`. Reference built by
`scripts/60_build_germline_db.py` into `data/germline/`.

Reference size: **249 IGHV** alleles contributing CDR3 residues, 
**76 IGHD** peptides (alleles × 3 forward frames), 
**14 IGHJ** alleles.

## 1. Positive control — a verbatim germline junction

Assembled as V(`AR`) + a full D peptide + J(`FDY`). Every residue is germline
by construction, so an honest metric must return ~100%.

| Constructed CDR-H3 | len | vdj_coverage | best_segment |
|---|---|---|---|
| `ARYYYGSGSYYNFDY` | 15 | **100.0%** | 66.7% |
| `ARGYCSGGSCYSFDY` | 15 | **100.0%** | 66.7% |
| `ARGYSSSWYFDY` | 12 | **100.0%** | 58.3% |

## 2. Noise floor — what a NON-germline loop scores

- **Scrambled pembrolizumab CDR-H3** (n=2000, composition held exactly): 
  `vdj_coverage` mean **21.5%**, sd 6.1%, max 53.8%, p95 30.8%
  `best_segment` mean **30.5%**, sd 4.4%, max 38.5%, p95 38.5%
- **Uniform-random 13-mers** (n=2000): `vdj_coverage` mean **21.3%**, sd 6.3%, max 46.2%, p95 30.8%

## 3. V-gene assignment — every allele must return itself

- **242 of 249 alleles returned themselves** (or a byte-identical allele); 7 wrong; 0 not numberable by ANARCII.
- The 7 disagreements are **ties, not errors**: each returned allele scores **100.0%**
  identity over IMGT 1-104, i.e. the two alleles are indistinguishable in the region
  compared and differ only outside it. Assignment resolves a gene to its 1-104 sequence,
  which is all the scored metric needs; allele-level calls would need the full V region.
- First ties: IGHV2-26*04 -> IGHV2-26*01 (100.0%), IGHV2-70*23 -> IGHV2-70*15 (100.0%), IGHV3-21*08 -> IGHV3-21*01 (100.0%), IGHV3-30*18 -> IGHV3-30*03 (100.0%), IGHV3-30-3*02 -> IGHV3-30*01 (100.0%)

## 4. Pembrolizumab — recorded, not predicted

- V assignment: **IGHV1-2*02** at **78.9%** over 95 compared positions.
  Humanised mouse-derived, so CDR1/CDR2 inside IMGT 1-104 are murine and drag this down.
- CDR-H3 `ARRDYRFDMGFDY`: CDR-H3 ARRDYRFDMGFDY (13aa) | vdj_coverage 53.8% [V IGHV1-18*01 2aa + D IGHD3-16*02_f2 2aa + J IGHJ4*01 3aa] | best_segment 38.5% [D:IGHD4-17*01_f2] | convention=vdj_coverage

## What this establishes, and what it does not

- The metric **separates germline from non-germline**: 100.0% on verbatim
  germline junctions against a 21.5% scramble floor.
- **The <95% hard cutoff is free.** Pembrolizumab itself — a licensed antibody
  with a mouse-derived CDR-H3 — scores 53.8%, and the
  scramble floor is 21.5%. Nothing a design campaign can produce
  approaches 95%, so this gate cannot discriminate between designs. It is
  scored as the handbook specifies and claimed as nothing more.
- **The V allele printed by `vdj_coverage` is NOT a germline call.** 173 of 249
  human alleles contribute the identical `AR`, so that field is arbitrary among
  ties. Use `assign_v()` for a call; it is validated in §3 and is a different
  computation over IMGT 1-104.
- **Convention risk.** `vdj_coverage` and `best_segment` disagree by
  15.4% on pembrolizumab.
  The handbook does not say which it means. Both are reported; neither crosses
  the 95% cutoff, so the ambiguity costs 0 points here — unlike band→score.

