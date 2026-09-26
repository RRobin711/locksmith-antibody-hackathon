# Challenge 2 re-screened with an alignment Boltz actually uses

**2026-09-23.** All 30 designs re-folded with `data/msa_cache/pd1_123_handbook.csv`
(3407 sequences, query matching the 123-residue antigen exactly). Everything else held
fixed: same sequences, same antigen, `recycling_steps=10`, `diffusion_samples=5`, same
seed, same driver. Point estimate is the **median of five**, fixed in advance.

This is the first Challenge 2 screen ever run under a condition where the antigen
alignment was used. See [why every previous one was not](msa_silently_discarded.md).

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

---

# Candidate readout — `bb_1_0_dldesign_0`

**2026-09-23, no new folds.** Everything below is computed from the re-screen artefacts.

## NetSolP (the §7.2 stop condition)

**0.617** = `min(VH 0.617, VL 0.657)` under the declared conventions (ESM1b, Fv,
`chain_agg=min`). Clears the 0.50 cutoff; **Medium** band, 8/10. Sequence-only, no fold.

## §5.2 breakdown, per diffusion sample

Challenge 2 scores **7 metrics** — DockQ is excluded because a de novo design has no
reference structure.

| metric | model_0 | model_1 | model_2 | model_3 | model_4 | **median** |
|---|---|---|---|---|---|---|
| `ipsae` | 0.855 | 0.697 | 0.509 | 0.637 | 0.423 | **0.637** |
| `dg` | −9.50 | −12.60 | −11.90 | −12.10 | −12.30 | **−12.10** |
| `contacts` | 71 | 99 | 98 | 104 | 115 | **99** |
| `iface_plddt` | 81.40 | 79.55 | 80.34 | 77.74 | 76.99 | **79.55** |
| `cdr_sasa` | 1265.4 | 1235.8 | 1226.7 | 1188.6 | 1084.5 | **1226.7** |
| `netsolp` | 0.617 | — constant — | | | | **0.617** |
| `cdrh3_identity` | 20.0 | — constant — | | | | **20.0** |
| **composite** | **90.0** | **91.2** | **87.6** | **91.2** | **87.6** | |
| **viable** | ✅ | ✅ | ❌ | ✅ | ❌ | **3 of 5** |

**Two different medians, both reported rather than choosing the flattering one.**
Evaluating the median of each metric gives **91.2**; the median of the five per-sample
composites is **90.0**. They differ because banding is not linear in the underlying value.

**Viable on 3 of 5 samples**, not 5 of 5. Models 2 and 4 fail on ipSAE.

## Which metrics sit near a band edge

| metric | median | band | nearest edge | distance |
|---|---|---|---|---|
| `ipsae` | 0.637 | medium | **cutoff 0.60** | **0.037** |
| `dg` | −12.100 | good | **good −12.0** | **0.100** |
| `iface_plddt` | 79.550 | medium | **good 80.0** | **0.450** |
| `netsolp` | 0.617 | medium | good 0.70 | 0.083 |
| `cdr_sasa` | 1226.7 | good | good 600 | 626.7 |
| `contacts` | 99 | good | good 25 | 74 |
| `cdrh3_identity` | 20.0 | good | good 70 | 50 |

**Three metrics sit within half a band edge**, and one of them is the viability cutoff
itself. This design is fragile to any change that costs anything at all.

## The structure the package would ship

`model_0`, because Boltz ranks by its own confidence and the package ships one structure.

| metric | model_0 value | band | sub-score |
|---|---|---|---|
| `ipsae` | **0.855** | good | 10.0 |
| `dg` | **−9.50** | **poor** | 5.0 |
| `contacts` | 71 | good | 10.0 |
| `iface_plddt` | 81.40 | good | 10.0 |
| `cdr_sasa` | 1265.4 | good | 10.0 |
| `netsolp` | 0.617 | medium | 8.0 |
| `cdrh3_identity` | 20.0 | good | 10.0 |
| **final** | **90.0** | | viable ✅ |

Note the trade: **the sample with the best confidence has the worst interface energy.**
`model_0` carries ipSAE 0.855 (the argmax) alongside ΔG −9.5, the only Poor band in the
set. The central estimate is the median, **ipSAE 0.637 / composite 91.2 (or 90.0 by
per-sample median)**; 0.855 is the top of a five-sample distribution and is reported as
such wherever it appears.

## Challenge 1, read from the package rather than inferred

| metric | value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1596.5 | good | 10.0 |
| `cdrh3_identity` | 38.5 | good | 10.0 |
| `contacts` | 97.0 | good | 10.0 |
| `dg` | −13.3 | good | 10.0 |
| `dockq` | 0.800 | good | 10.0 |
| `iface_plddt` | 88.63 | good | 10.0 |
| `ipsae` | 0.821 | good | 10.0 |
| `netsolp` | 0.569 | medium | 8.0 |

Categories: binding 10.000, developability 8.000, novelty 10.000. **Final 96.0.**

**Its margin is thinner than 96.0 suggests.** `dockq` **0.800 sits exactly on the Good
edge** (distance 0.000) and `ipsae` 0.821 is **0.021** above it. Two of the seven tens are
won by a hair, and both are on metrics that move with the diffusion draw — which is why
the Challenge 1 envelope is 94.0–96.0 rather than a point.

## Contacts, before any mutation

Heavy-atom contacts to PD-1 (chain C) within 4.5 Å, **all five samples**:

| residue | liability | model_0 | model_1 | model_2 | model_3 | model_4 | median | verdict |
|---|---|---|---|---|---|---|---|---|
| light **91** ASN | glycosylation `NKS`, CDR-L3 | 0 | 0 | 0 | 0 | 0 | **0** | **free** |
| light **31** ASN | deamidation `NG`, CDR-L1 | 0 | 13 | 15 | 13 | 5 | **13** | **load-bearing** |

**Measuring only the shipped sample would have given the wrong answer.** `model_0` shows
**zero** contacts for light 31; the median across five is **13**. A single-structure
contact analysis would have called a load-bearing residue free and licensed a mutation
that this project has already watched destroy an interface.

Against the precedent: `N→Q` on acceptors carrying **10 and 19** contacts collapsed ipSAE
0.864 → 0.014, while the same substitution on a **3**-contact acceptor was free. Light 31
at a median of **13** sits inside the fatal range, not the free one.

**Stopped here. One residue is load-bearing, so the §9.2 fix is not proposed.**
