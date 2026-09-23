# Challenge 2 re-screened with an alignment Boltz actually uses

**2026-09-23.** All 30 designs re-folded with `data/msa_cache/pd1_123_handbook.csv`
(3407 sequences, query matching the 123-residue antigen exactly). Everything else held
fixed: same sequences, same antigen, `recycling_steps=10`, `diffusion_samples=5`, same
seed, same driver. Point estimate is the **median of five**, fixed in advance.

This is the first Challenge 2 screen ever run under a condition where the antigen
alignment was used. See [[msa_silently_discarded|why every previous one was not]].

## Result

**1 of 30 clears ipSAE ≥ 0.60 on the median — and it is not the design we packaged.**

| | design | new median | min–max of 5 | old ipSAE | old rank |
|---|---|---|---|---|---|
| ✅ | `bb_1_0_dldesign_0` | **0.637** | 0.423–0.855 | 0.014 | 29th of 30 |
| | `bb_1_0_dldesign_1` | 0.440 | — | 0.116 | 18th |
| | `bb_4_0_dldesign_1` | 0.372 | — | 0.013 | 26th |
| ❌ | `bb_2_0_dldesign_1` *(packaged)* | **0.013** | 0.000–0.817 | 0.864 | **1st** |

**The ranking barely survives.** Spearman between old and new is **+0.366 (p = 0.047)** —
statistically distinguishable from zero and practically useless. The design that clears
was ranked **29th of 30** in the screen that chose the submission; the one that was chosen
is now 15th.

## The argmax hazard, measured on a real screen

| reading | designs "viable" |
|---|---|
| median of five samples | **1 / 30** |
| at least one of five ≥ 0.60 — *what `diffusion_samples=1` can report* | **5 / 30** |

Four of those five fail on the median. The packaged design is the sharpest case: median
**0.013**, best sample **0.817**. A single-sample run on it today would still report a
number in the Good band for a design whose central estimate is at the floor.

## The candidate is not submission-ready

`bb_1_0_dldesign_0` clears the binding gate but **fails handbook §9.2**, carrying two HIGH
liabilities inside CDRs:

| severity | motif | chain | position | region |
|---|---|---|---|---|
| HIGH | glycosylation `NKS` | light | 91 | CDR-L3 |
| HIGH | deamidation `NG` | light | 31 | CDR-L1 |
| MODERATE | oxidation `W` | heavy | 101 | CDR-H3 |

Novelty is fine: CDR-H3 `SRLSWTASGGIYLDV` is **20.0%** identical to pembrolizumab's,
far inside the <95% gate.

**Fixing those liabilities is precisely the operation that destroyed the previous
design.** `N→Q` on an acceptor carrying antigen contacts collapsed ipSAE 0.864 → 0.014;
the same substitution on an acceptor carrying 3 contacts was free. So the contact table
for N91 and N31 has to be computed before any substitution is chosen, and both arms have
to be re-folded and re-scored under the corrected alignment. That work is not done here.

Note also the margin: median **0.637** against a **0.60** cutoff, with the worst of five
samples at **0.423**. This clears, but not comfortably, and a liability fix that costs
anything at all could put it under.

## Honest status of Challenge 2

- There **is** a design in the existing pool that clears the binding gate under a correct
  fold. The backbones are not all worthless, which was the plausible worst case.
- It is **not** the packaged design, and the packaged design is not defensible.
- The clearing design needs liability work that is known to be capable of destroying it.
- Nothing here is evidence of binding. ipSAE 0.637 means Boltz places this antibody on
  PD-1 with moderate confidence given evolutionary information about the antigen — a
  statement about a predictor, not an experiment.

## What the re-screen cost

30 folds × ~2.9 min = **87 minutes** on one laptop GPU, plus a 3-minute scoring pass. The
alignment was built once from a server query Boltz had already performed, so no MSA
queries were spent.
