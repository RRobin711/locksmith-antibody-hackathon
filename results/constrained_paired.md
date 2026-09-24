# The §9.2 constraint is free — and sequence depth, not backbones, was the bottleneck

**2026-09-23.** Pre-registered in [[prereg_2026-09-23_constrained_paired]]. 18 local folds,
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
predictor. Against the 40-crystal panel, ipSAE tracks pose accuracy at ρ = +0.702 with a 0%
false-positive rate — which is why the number is worth something — but nothing here is an
affinity measurement, and this project's SKEMPI work found no metric in the stack tracks
measured ΔΔG.

The exploratory arm (8 backbones with no unconstrained partner) is reported for
completeness and excluded from the test: medians 0.000–0.414, none clearing.
