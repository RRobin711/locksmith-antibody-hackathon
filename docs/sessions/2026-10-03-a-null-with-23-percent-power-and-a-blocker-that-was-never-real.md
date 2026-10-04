# A null with 23% power, and a blocker that was never real

**2026-10-03.** No folds, no GPU, no money. Two findings, both produced by interrogating
things the project had already written down rather than by generating data.

1. A **spending decision rested on a statistical test that had a 23% chance of detecting
   the effect it was testing for.** The test was correctly implemented and correctly
   reported; it was simply underpowered, and its detectable effect was never stated.
2. A **blocker carried on the roadmap for eleven days did not exist.** The reasoning
   behind it was true in every clause and false in its conclusion, and the project had
   already disproved it five days *before* writing it down.

Neither required new measurement. Both are recorded in the retraction register as
[§B11](../../results/retractions.md) and [§B12](../../results/retractions.md).

---

## 1. The setup, from first principles

**Jargon, defined once.** A **backbone** is the 3-D shape of a candidate antibody with no
amino acids assigned — the wireframe, produced by RFdiffusion. **ProteinMPNN** then fills in
a *sequence* of amino acids that would fold into that shape; you can draw many different
sequences from one backbone. **Boltz-2** predicts the resulting complex and scores it; a
design **clears** if its ipSAE (an interface-confidence score) reaches 0.60.

In this project's Challenge 2 pool, sequences clear at about **8%**.

The campaign faced one economic question:

> **Are some backbones genuinely better than others?**
>
> - **Yes** → backbones differ, so *generating more backbones* is worth paying for; a good
>   one might clear at 25% instead of 8%.
> - **No** → backbones are interchangeable, so draw more sequences from the ones you have.
>   That is free.

`results/depth_sweep.md` answered it on 2026-09-24 with **18 backbones × 8 sequences = 144
folds**. Per-backbone clear counts came out as:

```
0 clears : 10 backbones
1 clear  :  5
2 clears :  2
3 clears :  1   (bb_17_0)
```

Two tests of whether that spread exceeds a single shared rate:

| test | statistic | p |
|---|---|---|
| Pearson dispersion | X² = 22.91 on 17 df | 0.152 |
| beta-binomial LRT vs binomial | LR = 0.696, fitted ρ = 0.0446 | 0.202 |

Neither rejects. The file concluded: *"These 18 backbones are exchangeable: there are no
good or bad ones in this pool, only draws"*, and decided **"No stratum C. No rental."**

## 2. Why that conclusion does not follow

### The concept: a null result is a claim about your instrument, not about the world

A significance test asks: *if there were no effect, how often would I see data this
extreme?* A large p-value means **the data are consistent with no effect**. It does **not**
mean there is no effect. The data may also be entirely consistent with a large effect, if
the test is too blunt to tell the two apart.

The missing quantity is **statistical power**: the probability that the test rejects the
null *given that a specified effect is real*. Power is not a property of the data alone —
it is a function of (sample size, effect size, α). A null result without a power statement
is uninterpretable, because *"we found nothing"* and *"we could not have found anything"*
produce identical output.

The disciplined form of a null result is therefore:

> **No effect larger than x**, where x is the effect detectable at the n you actually have.

### Why this design is blunt

The clear rate is μ = 12/144 = **0.0833**, over k = 8 draws per backbone. Expected clears
per backbone:

```
k · μ = 8 × 0.0833 = 0.67
```

Nearly every backbone therefore shows **0 or 1**, which is exactly what the counts above
show. You are trying to detect a *pattern of variation* in a column of mostly zeros. A truly
good backbone (say 25%) expects 2 clears; an average one expects 0.67. Over 8 draws those
distributions overlap heavily, and across 18 backbones the aggregate signal is weak.

### Measuring it

`scripts/110_heterogeneity_power.py`. Method: **Monte Carlo power simulation**, which needs
no closed form and is the right tool whenever the test statistic's distribution under the
alternative is awkward.

1. **Pick a generative model for "backbones differ".** The natural one is the
   **beta-binomial**: each backbone i draws its own true rate `p_i ~ Beta(α, β)`, then
   clears `x_i ~ Binomial(k, p_i)`. Parameterise by the mean μ and the **intra-class
   correlation** ρ = 1/(s+1) where s = α+β is the concentration. ρ = 0 is the homogeneous
   binomial; larger ρ means more spread between backbones. Usefully,

   ```
   Var(p_i) = ρ · μ(1 − μ)        so   sd(p_i) = sqrt(ρ · μ(1−μ))
   ```

2. **Calibrate the critical value by simulation rather than from a table.** At μ = 0.083 and
   k = 8 the χ² approximation to the Pearson dispersion statistic is suspect — the counts
   are small and discrete. Simulating 20,000 datasets under ρ = 0 gives a 95th percentile of
   **26.80**, against the asymptotic χ²₁₇ value of **27.59**. So the asymptotic cutoff is
   mildly **conservative**: its real type-I rate is **0.042**, not 0.050. The
   simulation-calibrated p for the observed 22.909 is **0.132** rather than 0.152.

   *This mattered less than it could have, and checking was still right.* Had the
   approximation erred the other way, the original p would have been anti-conservative and
   the finding would be worse, not better.

3. **Sweep ρ, counting rejections.** 6,000 simulations per grid point.

### The result

| ρ | sd of per-backbone rate | 10th–90th pct of rates | power |
|---|---|---|---|
| 0.000 | 0.0000 | 8.3% – 8.3% | 0.053 ← α, a control |
| **0.0446** *(the fitted value)* | 0.0584 | 2.1% – 16.3% | **0.231** |
| 0.100 | 0.0874 | 0.5% – 20.4% | 0.474 |
| 0.150 | 0.1070 | 0.1% – 23.0% | 0.639 |
| 0.200 | 0.1236 | 0.0% – 25.1% | 0.745 |
| **0.240** | 0.1354 | 0.0% – 26.5% | **0.801** |

The ρ = 0 row returning **0.053** is a control: a correctly calibrated test must reject at
the nominal α when the null is true. Without it, a flat power curve could mean a broken
statistic rather than a blunt design.

**80% power arrives at ρ ≈ 0.24 — five times the value the data fitted.** At the fitted ρ,
the test would have rejected **23% of the time**. A non-rejection at 23% power is close to
no information.

### Expressed in units a decision can be taken in

ρ is not actionable. Re-run the same simulation over **mixture worlds**: g of 18 backbones
clear at `p_good`, the rest at `p_bad`, pool mean held at the observed 8.3%.

| good backbones | p_good | p_bad | power |
|---|---|---|---|
| 3 | 20% | 6.0% | **0.198** |
| 2 | 25% | 6.3% | 0.252 |
| **3** | **25%** | **5.0%** | **0.399** |
| 1 | 40% | 6.3% | 0.426 |
| 4 | 25% | 3.6% | 0.557 |
| 2 | 40% | 4.2% | 0.758 |
| 3 | 35% | 3.0% | 0.835 |

**A pool in which three of eighteen backbones clear five times more often than the rest
would have been missed three times in five.** At three times better it is missed four times
in five. Both are worlds in which *generating more backbones is clearly worth paying for*.

So the supportable claim is the much weaker: **no backbone in this pool is detectably more
than about four times the pool rate.**

### The control that makes any of this trustworthy

Before computing a single power number, the script recomputes the published statistics from
the published per-backbone counts and **exits non-zero if any drifts**:

| quantity | recorded | computed |
|---|---|---|
| Pearson X² | 22.91 | 22.9091 |
| its p | 0.152 | 0.1522 |
| beta-binomial LR | 0.696 | 0.6957 |
| fitted ρ | 0.0446 | 0.0446 |
| its p | 0.202 | 0.2021 |

This is not ceremony. A power curve measures *whatever test you implemented*. Without this
control, a mis-specified statistic would produce a confident, wrong, entirely plausible
power curve — and there would be no way to tell.

## 3. The allocation inversion, which is the most transferable part

Given 288 folds, is it better to spend them on **more sequences per backbone** or **more
backbones**?

| spend 288 folds as | power at ρ = 0.10 | at ρ = 0.15 |
|---|---|---|
| 18 backbones × 16 sequences | **0.802** | 0.908 |
| 36 backbones × 8 sequences | 0.699 | 0.872 |
| 54 backbones × 8 sequences *(432 folds)* | 0.824 | 0.947 |

**Depth wins at equal cost — and this inverts what this project concluded a fortnight
earlier**, where breadth won decisively (`LEARNINGS.md`: *"Breadth won, the opposite of the
previous week's answer"*).

Both are correct, because the **estimator changed**:

- Choosing **the single best design** estimates a *maximum over designs*. Each candidate
  needs only rough measurement; more candidates means more chances at a good one.
- Asking **do backbones differ** estimates a *within-backbone dispersion*. That quantity
  does not exist without replicates on the same backbone. Adding backbones adds more
  poorly-characterised units; adding depth characterises each one.

> **The transferable principle: an optimal-allocation result is a property of the
> estimator, not of the pipeline.** Same hardware, same tools, same budget, opposite answer.
> Re-derive the allocation whenever the target quantity changes.

This is the **third** time this project has re-derived that lesson — previously for a mean
versus a spread, where `SE(s)/s ≈ 1/sqrt(2(k−1))` obeys a different law from a mean's
`1/sqrt(k)`.

The design that settles the question is `results/prereg_2026-09-23_depth_sweep.md`'s own
**stratum C** — +8 sequences per backbone, 144 new folds, costed there at 7.0 h locally.
**It was declined on the strength of the null it would have corrected.**

## 4. The blocker that was never real

`STATE.md` §6–§7, `docs/gpu-run-brief-2026-09-28.md` §2 and
`scripts/96_sequence_unconditioned.py` all stated that sequencing the unconditioned arm
required a rented `sm_86` card. The argument:

> RFantibody pins `torch==2.3.*`. PyPI's DGL ships `libgraphbolt_pytorch_<v>.so` for
> 2.0.0–2.2.1 only. Those wheels carry **no PTX**, so there is no forward-JIT to `sm_120`
> (Blackwell). Therefore it cannot run on this machine.

**Every clause is true. The conclusion is false.** The argument establishes that it cannot
run on *this GPU*; it says nothing about the *CPU*, which was never in the comparison.

```
$ PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 2 -t 0.2
No GPU found, running ProteinMPNN on CPU
MPNN generated 2 sequences in 1 seconds
```

`proteinmpnn_interface_design.py:85-90` branches on `torch.cuda.is_available()` and falls
back to CPU. In `~/.venvs/rfab-cpu` (torch **2.2.1+cpu**) that is `False`.

**The one real obstacle is not a device problem and looks nothing like one.** The CLI
subprocesses a bare `python` (`cli/inference.py:294`), so without the venv's `bin` on `PATH`
it dies with `FileNotFoundError: [Errno 2] No such file or directory: 'python'`. A plausible
reading of that traceback is "the environment is broken, as predicted" — which is probably
why the CPU route was never pursued.

**The tool-matching objection dissolves too.** The brief's reason for renting rather than
using standalone ProteinMPNN was that the conditioned arm used RFantibody's bundled copy.
This *is* that copy — same entry point as `pod/01_run.sh:69`, same weights
(`ProteinMPNN_v48_noise_0.2.pt`), same `-t 0.2`. The arms differ in **device**, not in code,
weights or flags. Worth stating on any result; not an uncontrolled difference.

### The part worth keeping

`results/prereg_2026-09-23_depth_sweep.md:22` costs sequence generation at *"~8 s per 8
draws per backbone — ~10 minutes total for all 576"*, and
`scripts/101_constrained_redesign_yield.py` closes its docstring *"Sequence-only, CPU, no
folds, no GPU, no money."* **Both predate the GPU brief by five days.**

And this is the **second instance in six days**. On 2026-09-28 the decoy-patch control was
also believed to need a rented card and ran locally on CPU for $0 — discovered only because
someone checked whether it *could* run before reporting that it could not. That discovery
was never carried across to the sibling blocker **one row below it in the same table**.

> **A blocker inherited from a neighbouring task is not evidence. Re-run the check per
> task.** Cost of checking: one minute. Cost of assuming: eleven days of a false blocker on
> the roadmap, and two offers to spend money that did not need spending.

## 5. How to verify this, and what "healthy" looks like

```bash
uv run python scripts/110_heterogeneity_power.py
```

Healthy output: all five control rows print `OK`; the ρ = 0 power row sits near **0.05**;
power rises monotonically in ρ; the calibrated critical value lands near **26.8**. If any
control row prints `MISMATCH` the script exits 1 and the power curve below it is void.

Numbers are stable to roughly ±0.01 at the simulation counts used (6,000 per grid point;
binomial standard error at p = 0.8 is `sqrt(0.8·0.2/6000) ≈ 0.005`). Reported to 3 dp, which
slightly overstates precision — the third digit is noise.

## 6. What is not claimed

- **Nothing here shows the backbones are heterogeneous.** No new data were generated. ~0.86
  may well be the generator's ceiling.
- **The campaign decision is not refuted, only its stated justification.** It survives on
  its other leg: eight times the sequences produced nothing better than the first pass
  found (best 0.859 at depth 1, 0.854 at depth 8). That is a direct observation, not a null.
- **Range restriction is untouched.** The 18 backbones were *selected* on an
  `interaction_pae` later measured at ICC −0.113, so they may be a compressed slice rather
  than a representative sample — a separate question, and one the project has been bitten by
  before (predicted reliability 0.849, measured 0.629, because shortlisting destroyed the
  spread). The experiment that addresses it is in `results/unconditioned_baseline.md`, and
  §4 above means it is now free rather than rental-blocked. It also carries a known
  confound: unconditioned backbones dock to a random face, so their scores mix targeting
  failure with design quality.

## 7. Glossary

| term | meaning |
|---|---|
| **backbone** | 3-D antibody shape with no amino acids assigned; RFdiffusion's output |
| **clear** | a design reaching ipSAE ≥ 0.60 |
| **statistical power** | P(reject the null \| a specified effect is real) |
| **ρ (intra-class correlation)** | how much true clear-rates vary between backbones; 0 = identical |
| **beta-binomial** | each unit draws its own rate from a Beta, then a Binomial given that rate |
| **Monte Carlo power simulation** | simulate the experiment many times under an assumed effect, count rejections |
| **type-I rate** | how often a test rejects when the null is true; should equal α |
| **stratum** | a batch of sequences at a given depth per backbone |
| **range restriction** | selecting on a variable shrinks its observed variance in the selected group |
| **PTX** | portable GPU intermediate representation a driver can JIT to newer architectures |

## 8. What this session cost, and what it changed

Zero compute. One script (`scripts/110_heterogeneity_power.py`), one results file
(`results/heterogeneity_power.md`), two register entries, and corrections to five documents
that were asserting things no longer true. 44/44 tests still pass.

The hackathon deliverable is unaffected — both designs remain packaged and validated at
94.0 and 93.6, and nothing in the rubric scores methodology. **This work moves the
submission score by exactly zero points, which is the correct reason to be clear about why
it was worth doing: the project's stated deliverable is the record of measuring honestly,
not the score.**
