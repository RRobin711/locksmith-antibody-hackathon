# What the exchangeability null could have detected — and why the rental was never needed

**2026-10-03.** `scripts/110_heterogeneity_power.py`. No folds, no GPU, no money.

Two findings, independent of each other:

1. The depth sweep's heterogeneity null had **23% power against the effect it itself
   fitted**. The claim "these 18 backbones are exchangeable" is not supported at the
   available power, and the decision it carried — *no stratum C, no rental* — rests on it.
2. **ProteinMPNN runs on this laptop's CPU**, so the one step the project has called
   rental-blocked since 2026-09-22 is not blocked. The project's own depth sweep proved
   this on 2026-09-23 and the finding was never propagated back.

---

## 1. The control, first

Power curves measure whatever test you implemented, so the implementation reproduces the
recorded statistics from the recorded per-backbone counts (10 zeros, 5 ones, 2 twos, one
three) before anything else runs. All five match:

| quantity | recorded | computed |
|---|---|---|
| Pearson X² | 22.91 | **22.9091** |
| its p | 0.152 | **0.1522** |
| beta-binomial LR | 0.696 | **0.6957** |
| fitted ρ | 0.0446 | **0.0446** |
| its p | 0.202 | **0.2021** |

The script exits non-zero if any of them drifts.

**Asymptotics are not assumed.** At p = 0.083 and k = 8 the χ² approximation is suspect, so
critical values are simulated under ρ = 0. The asymptotic χ²₁₇ cutoff is mildly
**conservative** — real type-I **0.042**, not 0.050 — and the calibrated p for the observed
22.909 is **0.132** rather than 0.152. The conclusion is unchanged, which is itself worth
recording: the original test was not wrong, it was underpowered.

## 2. Power against ρ

n = 18 backbones, k = 8 sequences, μ = 8.3%, α = 0.05 calibrated.

| ρ | sd of per-backbone rate | 10th–90th pct of rates | power |
|---|---|---|---|
| 0.000 | 0.0000 | 8.3% – 8.3% | 0.053 |
| **0.0446** *(fitted)* | 0.0584 | 2.1% – 16.3% | **0.231** |
| 0.100 | 0.0874 | 0.5% – 20.4% | 0.474 |
| 0.150 | 0.1070 | 0.1% – 23.0% | 0.639 |
| 0.200 | 0.1236 | 0.0% – 25.1% | 0.745 |
| **0.240** | 0.1354 | 0.0% – 26.5% | **0.801** |

**80% power arrives at ρ ≈ 0.24, five times the fitted value.** At the ρ the data actually
estimated, the test would have rejected **23% of the time**. A non-rejection at 23% power is
close to no evidence at all.

## 3. Power against worlds anyone can act on

ρ is not a quantity a campaign decision can be taken in. The decision is *is there a
backbone worth generating more of?* — so: g of 18 backbones clear at `p_good`, the rest at
`p_bad`, pool mean held near the observed 8.3%.

| good backbones | p_good | p_bad | pool mean | power |
|---|---|---|---|---|
| 3 | 20% | 6.0% | 8.3% | **0.198** |
| 2 | 25% | 6.3% | 8.4% | 0.252 |
| **3** | **25%** | **5.0%** | 8.3% | **0.399** |
| 1 | 40% | 6.3% | 8.2% | 0.426 |
| 4 | 25% | 3.6% | 8.4% | 0.557 |
| 2 | 40% | 4.2% | 8.2% | 0.758 |
| 3 | 35% | 3.0% | 8.3% | 0.835 |
| 1 | 60% | 5.0% | 8.1% | 0.836 |

**A world in which three of the eighteen backbones are five times better than the rest
(25% vs 5%) would have been missed three times in five.** Three at 20% vs 6% — still a
threefold difference, and exactly the finding that would justify generating more backbones
— would have been missed **four times in five**.

The sentence in `depth_sweep.md` reading *"These 18 backbones are exchangeable: there are no
good or bad ones in this pool, only draws"* is therefore too strong. What the data support
is: **no backbone in this pool is detectably more than about four times the pool rate.**
That is a real result and a much weaker one.

## 4. What design would settle it

| backbones | sequences each | total folds | **new** folds | power at ρ=0.10 | at ρ=0.15 |
|---|---|---|---|---|---|
| 18 | 8 *(what was run)* | 144 | 0 | 0.470 | 0.636 |
| **18** | **16** | 288 | **144** | **0.802** | **0.908** |
| 36 | 8 | 288 | 144 | 0.699 | 0.872 |
| 54 | 8 | 432 | 288 | 0.824 | 0.947 |
| 18 | 32 | 576 | 432 | 0.977 | 0.992 |

**At equal cost, depth beats breadth for this question** — 18×16 reaches 0.802 where 36×8
reaches 0.699 on the same 288 folds. That inverts the project's standing allocation result,
and the inversion is principled rather than surprising: *"an optimal-allocation result is a
property of the estimator, not the pipeline."* Breadth won when the estimator was a **mean**
over designs; here the estimator is a **within-backbone dispersion**, which needs replicates
on the same backbone to exist at all. Same budget, different quantity, opposite answer. This
is the third time that lesson has been re-derived in this project.

**The design that settles it is `prereg_2026-09-23_depth_sweep.md`'s stratum C** — +8
sequences per backbone, 144 new folds, costed there at 7.0 h on the local 5070 Ti. It was
declined on the strength of the underpowered null it would have corrected.

## 5. The rental was never needed

`docs/gpu-run-brief-2026-09-28.md` §2, `scripts/96_sequence_unconditioned.py`'s docstring,
and `STATE.md` §6–§7 all state that sequencing the unconditioned arm needs a rented `sm_86`
card, because RFantibody pins `torch==2.3.*` with no PTX.

The pin is real. The conclusion does not follow. **Verified 2026-10-03** by running the
bundled tool rather than reasoning about it:

```
$ PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 2 -t 0.2
No GPU found, running ProteinMPNN on CPU
MPNN generated 2 sequences in 1 seconds
```

`proteinmpnn_interface_design.py:85-90` branches on `torch.cuda.is_available()` and falls
back to CPU; in `~/.venvs/rfab-cpu` (torch **2.2.1+cpu**) that is `False`, so the CPU path
is taken. One real obstacle, and it is not the card: the CLI subprocesses a bare `python`
(`cli/inference.py:294`), so the venv's `bin` must be on `PATH` or it dies with
`FileNotFoundError: 'python'` — which looks nothing like a device problem.

**The tool-matching objection also dissolves.** The brief's stated reason for renting rather
than using standalone ProteinMPNN was that the conditioned arm used RFantibody's bundled
copy. This *is* that copy — same entry point as `pod/01_run.sh:69`, same weights
(`ProteinMPNN_v48_noise_0.2.pt`), same `-t 0.2`. The arms differ in **device**, not in code,
weights or flags. Worth stating on the result; not an uncontrolled difference between arms.

**And the project already knew.** `prereg_2026-09-23_depth_sweep.md:22` costs sequence
generation at *"~8 s per 8 draws per backbone — ~10 minutes total for all 576"* and
`scripts/101_constrained_redesign_yield.py` closes its docstring with *"Sequence-only, CPU,
no folds, no GPU, no money."* Both predate the GPU brief by five days. The brief was written
without checking them, and `STATE.md` has carried the rental as a blocker ever since.

*This is the second instance of the same failure in six days.* On 2026-09-28 the decoy
control was also believed to need a rented card and ran locally on CPU for $0 — discovered
only by checking whether it *could* run before reporting that it could not. That discovery
was never carried across to the sibling blocker one row below it in the same table.
**A blocker inherited from a sibling task is not evidence; re-run the check per task.**

## 6. What this does and does not say

- It does **not** show the backbones are heterogeneous. No new data were generated here.
- It does **not** refute the ceiling. ~0.86 may well be the ceiling; the point is that the
  evidence offered for it cannot distinguish that from a pool containing good backbones.
- It does **not** address range restriction — whether the 18 were a representative sample
  at all, given they were selected on an `interaction_pae` measured at ICC −0.113. That is
  the separate question in `results/unconditioned_baseline.md`, and §5 means it is now also
  free.
