# The §9.2 constraint is free — and sequence depth, not backbones, was the bottleneck

**2026-09-23.** Pre-registered in [prereg_2026-09-23_constrained_paired](prereg_2026-09-23_constrained_paired.md). 18 local folds,
~50 minutes, no rental.

## Primary result: the constraint costs nothing measurable

Paired on the backbone, n=10 backbones with both a constrained and an unconstrained score
under the same correct alignment:

| | |
|---|---|
| median paired difference (constrained − unconstrained median) | **+0.042** |
| mean | +0.136 |
| Wilcoxon signed-rank | W = 15.0, **p = 0.426** |
| secondary, vs *best* unconstrained (conservative) | **+0.017** |

**Pre-registered rule: "≥ −0.05 and p > 0.05 → the constraint is free."** Both conditions
met. The campaign proceeds as designed: constrain at generation, discard nothing.

Stated as pre-registered: at n=10 this detects roughly d > 1.0. **A null here means "no
effect larger than large", not "no effect".** A modest cost to the constraint is not
excluded by this test and no claim of that kind is made from it.

## The confound that applies, because the sign came out positive

Recorded *before* the folds: *"if constrained folds better, the likely explanation is not
that the constraint helps but that the yield loop draws 8 sequences and keeps the first
clean one — a mild selection the unconstrained pool did not get."*

That is what happened, and it is the more interesting result. The constrained sequences
came from **8+ draws per backbone**; the pilot's pool had roughly **3**. The positive
difference is more plausibly **sampling depth** than the constraint.

## Secondary result, and it is larger than the primary

| | clearing ipSAE ≥ 0.60 on the median |
|---|---|
| constrained | **2 / 18 backbones** |
| unconstrained (re-screen) | **1 / 30 sequences** across 10 backbones |

Two backbones went from near-floor to clearing, on the same geometry:

| backbone | unconstrained median | unconstrained best | constrained |
|---|---|---|---|
| `bb_8_0` | 0.011 | 0.203 | **0.859** |
| `bb_3_0` | 0.039 | 0.197 | **0.660** |

**The backbone did not change. Only how many sequences were drawn on it.** `bb_8_0` found
its clean sequence on **attempt 1** — the first unconstrained batch of 8 — so no constraint
was even applied to the winner. That is sampling depth alone.

## `bb_8_0` is a better design than anything this project has produced

| | current submission `bb_1_0_dldesign_0` | **`bb_8_0` constrained** |
|---|---|---|
| ipSAE median of 5 | 0.637 | **0.859** |
| per-sample | 0.855 0.697 0.509 0.637 0.423 | **0.904 0.865 0.859 0.828 0.819** |
| worst sample | 0.423 | **0.819** |
| margin over the 0.60 cutoff | 0.037 | **0.259** |
| viable | 3 / 5 | **5 / 5** |
| §9.2 | **FAIL** — 2 HIGH CDR liabilities | **PASS** |
| composite (model_0 / median) | 90.0 / 91.2 | **93.6 / 93.6** |

Every one of its five diffusion samples sits above **0.80**. Its *worst* sample beats the
current candidate's *median* by 0.18. It is §9.2-clean by construction rather than shipping
two disclosed liabilities, and it needs no repair — which matters, because all three repair
routes were measured killing the current design.

Where it is slightly worse: `netsolp` 0.555 vs 0.617 and `dg` −10.9 vs −12.1, both Medium
band either way, and neither near an edge that changes the score.

## What this changes about spending

**The evidence now says sequence depth was the bottleneck, not backbone diversity.**

Eighteen existing backbones produced a 0.859 design by drawing more sequences on them.
Nothing was regenerated and nothing was rented. ProteinMPNN sequence design runs on CPU at
~8 sequences per 8 seconds per backbone; the folds are local at ~2.9 min each.

So the cheapest next move is **not** renting a GPU for fresh RFdiffusion backbones. It is
generating many more sequences per *existing* backbone — 16 or 32 rather than 3 — screening
them free on liabilities, and folding the survivors locally. If that keeps producing
designs at 0.859, backbone diversity was never the limit.

The rental case is not dead, but it is now second in line behind an experiment that costs
nothing.

## What this does not establish

**That any of these bind.** ipSAE 0.859 means Boltz places this antibody on PD-1 with high
confidence given evolutionary information about the antigen. It is a statement about a
predictor. Against the 40-crystal panel, ipSAE tracks pose accuracy at **ρ = +0.702** —
which is why the number is worth something — but nothing here is an affinity measurement,
and this project's SKEMPI work found no metric in the stack tracks measured ΔΔG.

*(Corrected 2026-09-26: this sentence also carried the unqualified "0% false-positive rate".
An error rate is a property of a threshold; see the correction at the end of this file and
[the retraction register, §C1](retractions.md).)*

The exploratory arm (8 backbones with no unconstrained partner) is reported for
completeness and excluded from the test: medians 0.000–0.414, none clearing.

---

# Is 0.859 credible? Three checks, because it has the shape of the last artefact

**2026-09-23.** A de novo design outscoring real crystallised complexes is exactly the
pattern that turned out to be the discarded-MSA artefact, when the old design read 0.864
against pembrolizumab's 0.842. Same shape. Checked rather than assumed.

## Check 1 — the alignment was demonstrably USED

Not "the guard did not fire", which is absence of evidence. Read from the processed
alignment each fold actually featurised:

| fold | MSA depth | MSA width | antigen length | |
|---|---|---|---|---|
| `cf_bb_8_0` | 1024 | **123** | 123 | **used** |
| `cf_bb_3_0` | 1024 | **123** | 123 | **used** |
| `rs_bb_1_0_dldesign_0` | 1024 | **123** | 123 | **used** |

The specific artefact is excluded.

## Check 2 — the percentile, and the confound in it

| arm | n | median | max | real complexes above 0.859 |
|---|---|---|---|---|
| post-cutoff (novel antigens) | 20 | 0.165 | 0.839 | **0 / 20 — 100th percentile** |
| pre-cutoff (memorised antigens) | 20 | 0.646 | 0.874 | 1 / 20 — 95th percentile |

Taken alone this looks alarming. **It is the wrong comparison, and I made it.** Our design
has a **memorised antigen and a novel antibody**; the post-cutoff panel has **novel
antigens and novel antibodies**, a strictly harder task. PD-1 is pre-cutoff, deeply
represented, and carries a 3407-sequence alignment. This project has a standing rule to
screen antibody and antigen novelty separately, for precisely this reason.

## Check 3 — the matched control, which is what settles it

Real antibodies folded under **identical** conditions: same 123-residue handbook antigen,
same `pd1_123_handbook.csv`, recycling 10, 5 diffusion samples, seed 1.

| | per-sample ipSAE | median | ≥0.60 |
|---|---|---|---|
| **pembrolizumab** — licensed anti-PD-1 | 0.886 0.877 0.870 0.897 0.852 | **0.877** | **5/5** |
| **`bb_8_0`** — our de novo design | 0.904 0.865 0.859 0.828 0.819 | **0.859** | **5/5** |
| `bb_1_0_dldesign_0` — current submission | 0.855 0.697 0.509 0.637 0.423 | 0.637 | 3/5 |
| nivolumab — licensed anti-PD-1 | 0.643 0.477 0.463 0.474 0.255 | 0.474 | 1/5 |
| **trastuzumab** — anti-HER2, **negative** | 0.740 0.210 0.057 0.000 0.000 | **0.057** | 1/5 |

**0.859 is not anomalous. It sits just *below* what a licensed anti-PD-1 antibody scores on
this exact target under these exact conditions (0.877), and roughly 15× above what an
irrelevant antibody scores (0.057).** The apparent inversion was an artefact of comparing
across constructs: pembrolizumab's 0.874 came from the 113-mer with the old cached
alignment and its 0.843 from the 119-mer with a server alignment. Neither is comparable to
a 123-mer fold.

The trastuzumab arm matters as much as the pembrolizumab one: the condition is not
inflating everything. A wrong antibody still collapses to the floor under the same
alignment, construct and sampling depth.

**Nivolumab at 0.474 is expected and independently consistent.** Its epitope needs PD-1's
N-terminal loop, and the handbook's 123-mer begins at `DSPDRP` — covering 13 of its 14
contact residues but missing **L25**. It is the one licensed antibody this construct cannot
serve, which the epitope analysis predicted before this fold existed.

## What the three checks establish, and what they do not

**Establish:** the alignment was applied; the alarming percentile was the wrong comparison;
and against the right comparison — a true binder on the same antigen, same construct, same
alignment, same sampling — 0.859 is credible and slightly conservative.

**Do not establish:** that `bb_8_0` binds. Every number here is Boltz's confidence. What
the 40-crystal panel buys is knowing that this confidence tracks pose accuracy at
ρ = +0.702, which is why a high value is worth more than it was before the panel existed.
It is still not an affinity measurement.

> **Correction, 2026-09-26.** This paragraph originally read "with a **0% false-positive
> rate** — it never accepted a wrong pose in 40 tries". **An error rate is a property of a
> threshold, and that one is quoted at none.** Against DockQ ≥ 0.23 (Acceptable+) the
> ipSAE ≥ 0.60 gate gives 0% FP / **58.3%** FN; against DockQ ≥ 0.49 (Medium+) it gives
> **12.5%** FP / 25.0% FN. The 0% additionally rests on **4 negatives** — Clopper–Pearson
> 95% upper bound **0.602**, i.e. uninformative. See
> [the retraction register, §C1](retractions.md).
> The conclusion of this section is unchanged: ρ = +0.702 is what makes the confidence
> worth reading, and it was never the error rate doing that work.
