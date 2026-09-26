---

> ## ⚠ CORRECTED 2026-09-20 — the title of this doc is wrong
>
> **"Three seeds is the worst allocation at every budget tested" is false**, and it is
> refuted by the table printed inside this document. At a 40-fold budget, **20 × 3 scores
> +1.4024**, beating 4 × 10 (+1.3847) and 2 × 15 (+1.2992). Over-seeding a two- or
> four-design shortlist is worse than under-seeding a twenty-design one; the claim holds
> only at budgets 120 and 240.
>
> The defensible version: **seeds beat candidates over roughly 3→10 seeds, and the optimum
> deepens as the budget grows.** Note also that at budget 120 this doc's own best row is
> 13 × 10 (+1.4789), not the 20 × 7 (+1.4659) that was actually run.
>
> Everything else here stands. Kept unedited below as the reasoning trail; see
> [the audit](2026-09-20-auditing-the-judge-reliability-is-not-validity.md).

tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [[Learning]], [[Protein Design]]

# Session 2026-09-19 — Three seeds is the worst allocation

## 0. Session at a glance

**Before:** 239 antibody designs had been folded overnight (one structure prediction each)
but the scoring stage had failed on all 239. There was no way to rank designs, no named
candidate, and Gate 3 — the criterion deciding whether a cheap sequence filter earns a place
in the pipeline — was unadjudicated.

**Now:** all 239 are scored; a continuous ranking function exists and is tested; Gate 3 is
adjudicated **PASS** with two attached conditions; a winner is named, its selection bias
corrected and the correction *validated* against an independent measurement; and batched
folding is built and accepted. Milestone M3 is complete.

**Still running:** nothing. The machine is idle.

**Prerequisites.** General statistics (variance, correlation, standard error). No biology is
assumed — §2 defines everything. Two earlier docs give fuller treatments of things restated
briefly here: [the aromatic
finding](2026-09-18-the-ensemble-axis-loses-to-a-free-sequence-feature.md) and [the random-pruning null](2026-09-18-what-a-pre-fold-filter-has-to-beat.md).

---

## 1. The problem this session addressed

We can generate candidate antibody sequences essentially free — a sequence-design neural
network emits one in under a second. **Evaluating** one requires predicting the 3-D structure
of the antibody bound to its target, which costs ~84 seconds of GPU time. So the campaign is
an optimisation under a fixed budget of *folds* (structure predictions), and the whole game is
deciding where to spend them.

Three sub-problems, each of which turned out to have a counterintuitive answer:

1. **How do we rank designs?** The competition's scoring rubric maps each measurement into one
   of three quality bands. Banding destroys resolution: 40 designs collapsed onto three
   distinct scores. You cannot rank 239 candidates with a function that takes three values.
2. **How many designs should be re-measured?** Ranking from a single structure prediction is
   noisy. Re-measuring a shortlist costs folds. How deep should the shortlist be?
3. **Does the cheap pre-fold filter actually work?** A previous session found that the fraction
   of aromatic amino acids in one loop predicts design quality at zero compute cost. Gate 3
   asks whether that survives contact with new data.

---

## 2. Concepts from first principles

### 2.1 The biology, in one paragraph

An **antibody** is a Y-shaped protein that binds a target (**antigen**). Binding is done almost
entirely by six short loops at the tips, the **CDRs** (complementarity-determining regions).
The third loop of the heavy chain, **CDR-H3**, is the most variable and contributes most of
the binding, so it is the loop we redesign. Here the antigen is **PD-1**, an immune checkpoint
receptor, and the reference antibody is **pembrolizumab**, a licensed drug. We redesign
pembrolizumab's CDRs and ask whether the result still binds.

**Folding** means running a neural network (here **Boltz-2**) that predicts the 3-D coordinates
of the antibody–antigen complex from sequence alone. It is a *diffusion* model, so it is
stochastic: different random **seeds** give genuinely different structures, not merely
different confidence numbers. That stochasticity is the measurement noise this whole document
is about.

**DockQ** is a 0–1 score for how close a predicted complex is to the experimentally known
one — 1.0 is perfect, and by convention ≥0.23 is "acceptable", ≥0.49 "medium", ≥0.80 "high".

### 2.2 Reliability: the ratio that governs everything here

Every measurement here is a true value plus noise:

```
observed = true + noise,    noise ~ N(0, σ_noise²)
```

Across a population of designs the observed variance decomposes as

```
σ_obs²  =  σ_true²  +  σ_noise²                                        (2.1)
```

**Reliability** is the fraction of observed variance that is real signal:

```
reliability  =  σ_true² / (σ_true² + σ_noise²)                         (2.2)
```

It is dimensionless, in [0, 1]. A reliability of 1.0 means the ordering you observe is the
true ordering; 0.0 means your ranking is pure noise. Averaging *k* independent seeds divides
the noise variance by *k*:

```
reliability(k seeds)  =  σ_true² / (σ_true² + σ_noise²/k)              (2.3)
```

**Two consequences that drive the whole session.** First, reliability is a *ratio*, so it can
be destroyed by shrinking the numerator without touching the noise — which is exactly what
shortlisting does (§7.1). Second, because the denominator falls only as 1/k, buying precision
gets expensive fast: going from 1 seed to 4 halves the noise *sd*, not the noise variance.

### 2.3 The winner's curse

If you take the argmax over *n* noisy measurements, the winner is disproportionately a design
whose noise happened to land high. So the winner's observed score is a **biased** estimate of
its true score, and the bias **grows with n** — more draws means a more extreme maximum.

The correction is empirical-Bayes shrinkage toward the population mean:

```
corrected  =  pool_mean  +  reliability × (observed − pool_mean)       (2.4)
```

Interpretation: trust the deviation from the mean only as far as the measurement is reliable.
At reliability 1.0 it does nothing; at 0.0 it shrinks every design to the mean. Units are
whatever the score is in.

The only unbiased estimate of a winner's quality is a measurement taken on a **fresh seed that
took no part in the selection**. Every seed used to choose the winner is contaminated by
having been selected on.

---

## 3. What was built — mechanism

### 3.1 The continuous surrogate (`src/locksmith/select/surrogate.py`)

**The problem.** `score.evaluate` maps each raw metric into a band and assigns that band's
score: 9.5 for *good*, 7.0 for *medium*, 2.5 for *poor*. Category means are then combined with
the rubric's weights (binding 0.60 averaged over six metrics, developability 0.20, novelty
0.20) and multiplied by 10 to give `final` on a 0–100 scale. A step function has two
pathologies: it collapses distinct designs onto identical scores, and it does not attenuate
noise — it *concentrates* noise at band edges and delivers it as a full 2.5-point jump.

**The mechanism.** Keep every metric, every weight and every anchor; replace only the step
with piecewise-linear interpolation through the same three anchor points:

```
raw == cutoff  ->  sub = 2.5
raw == medium  ->  sub = 7.0
raw == good    ->  sub = 9.5
```

Concretely, with spans `hi = good − medium` and `lo = medium − cutoff`:

```
if hi ≠ 0 and (v − medium)/hi ≥ 0:                 # at or above `medium`
    sub = min(10, 7.0 + 2.5 · (v − medium)/hi)
elif lo == 0:                                      # degenerate lower span
    sub = 2.5
else:
    sub = max(0, 2.5 + 4.5 · (v − cutoff)/lo)
```

The `(v − medium)/hi ≥ 0` form rather than `v ≥ medium` is deliberate: it works unchanged for
`low`-is-better metrics (ΔG, CDR-H3 identity) where all three anchors and both spans are
negative, so the comparisons flip consistently.

**Band configuration actually used** (`config/metrics.yaml`, direction / cutoff / medium /
good): `ipsae` high 0.60/0.60/0.80 · `dockq` high 0.23/0.49/0.80 · `dg` low −6.0/−10.0/−12.0
kcal·mol⁻¹ · `contacts` high 10/15/25 · `iface_plddt` high 65/70/80 · `cdr_sasa` high
250/300/600 Å² · `netsolp` high 0.50/0.50/0.70 · `cdrh3_identity` low 95/90/70 %.

**Invariant:** the surrogate equals `final` exactly at every anchor. Violating it means the
surrogate and the reported score disagree about what "good" means, and the ranking silently
optimises something the rubric does not reward. Tested in §7.

**Measured gain:** single-seed reliability **0.689** against `final`'s **0.602**; at three
seeds **0.849** against **0.780**.

### 3.2 Batched folding (`src/locksmith/fold/batch.py`)

`boltz predict` accepts a *directory* of input files and pays its fixed startup cost
(checkpoint load, featuriser construction, alignment parse) once for the whole directory. So
N × (fixed + fold) becomes fixed + N × fold.

**Invariant:** `--seed` is an invocation-level flag, so every complex in a batch shares a seed.
`fold_batch()` therefore takes one `seed` argument rather than per-item seeds — making the
error impossible rather than documenting it. Multi-seed work batches *by* seed.

**Invariant:** each label's artefacts are asserted individually. A half-failed batch is the
most dangerous shape available, because the tool exits 0 after fatal errors and a batch can
drop one record while leaving a directory that looks right. One bad complex costs one fold,
not N.

### 3.3 File map, in reading order

| file | owns |
|---|---|
| `src/locksmith/select/surrogate.py` | the continuous ranking function (§3.1) |
| `src/locksmith/fold/batch.py` | batched folding (§3.2) |
| `scripts/28_generate_temp_arm.py` | generate 239 designs over 4 temperatures, dedupe |
| `scripts/29_fold_temp_arm.py` | fold all 239 unfiltered, shuffled, resumable |
| `scripts/30_score_temp_arm.py` | score them (sequence metrics serial, structure parallel) |
| `scripts/31_shortlist_depth.py` | size the shortlist → `results/m3_shortlist_depth.md` |
| `scripts/32_shortlist_and_reseed.py` | rank, cut top 20, fold at 7 seeds |
| `scripts/33_g3_verdict.py` | adjudicate Gate 3 → `results/m3_g3_verdict.md` |
| `scripts/34_verify_batching.py` | 4-tier batching acceptance → `results/m3_batching.md` |
| `scripts/35_winner.py` | name + discount + fresh-seed + ensemble → `results/m3_winner.md` |

### 3.4 One design's path through the system

`mpnn_T0.5_s104_036` was sampled by ProteinMPNN at temperature 0.5 (script 28), passing
deduplication and sequence validation. Script 29 folded it once (seed 1) as a full Fab complex
of 549 residues: heavy 219, light 217, PD-1 113. Script 30 computed eight metrics from that
one structure. Script 32 ranked it 1st of 239 on the surrogate and folded it at seeds 2–7.
Script 35 averaged the surrogate over all 7 seeds (95.117), shrank it by reliability 0.629
toward the shortlist mean 94.703 giving **94.963**, then folded it once more at seed 23 —
untouched by selection — which measured **94.962**.

---

## 4. Design decisions

**Fold all 239 rather than filtering first.**
*Chosen:* fold everything unfiltered. *Alternatives:* filter to ~45 and fold only survivors;
or fold survivors plus a random sample of rejects. *Why:* using the filter and evaluating it
in the same run is circular — you never see what you discarded. A reject *sample* fixes the
circularity but leaves sampling error. Folding everything makes the comparison exact and
re-evaluable offline for ever, at ~30 extra folds ≈ 23 min. *Cost to reverse:* none; a future
run can prune freely using this run's data to set the threshold.

**Rank on the surrogate, report `final`.**
*Chosen:* continuous surrogate for internal ranking. *Alternatives:* rank on `final` (3 distinct
values over 40 designs); rank on DockQ alone (rejected 2026-09-17 — the rubric prices one
novelty band step at 14.0 points against DockQ's 7.0, so DockQ-ranking promotes near-copies of
pembrolizumab); rank-normalise within the pool (rejected: makes runs incomparable and lets the
pool's composition change a design's score). *Cost to reverse:* trivial — pure function, no
stored state.

**20 designs × 7 seeds, not 30 × 3.** See §5.3. *Cost to reverse:* the folds are on disk and
resumable; any other allocation can be computed from them or extended.

**Absolute aromatic threshold (count ≤ 1), not a percentile.** *Why:* the feature takes four
values over a 13-residue loop, so a percentile cannot be applied without arbitrary
tie-breaking, and it maps to a different absolute threshold at every sampling temperature —
confounding the temperature comparison with the filter's own definition.

---

## 5. What went wrong

### 5.1 Scoring failed on all 239, three separate defects, all mine

**What happened.** Every scoring worker died with `RuntimeError: Cannot re-initialize CUDA in
forked subprocess`. I had merged the serial NetSolP stage and the 6-worker parallel structure
stage into one script. NetSolP initialises CUDA in the parent process; `ProcessPoolExecutor`
defaults to `fork` on Linux; a forked child inherits a CUDA context it cannot re-initialise.
The original code kept the two stages in separate *processes* (`scripts/25` and `25p`), and
that boundary was load-bearing with nothing recording why.

**Why dangerous.** Two aggravating defects turned a visible failure into a potentially silent
one. The stage **returned 0** despite 239/239 failures, so the shell logged `exit=0`. And the
resume logic skipped any design that had *a row* in the output file — and an error row is a
row — so the obvious re-run would have skipped all 239 for ever, leaving a file that looks
complete.

**How caught.** Reading the log rather than the exit status.

**General lesson, three of them.** (i) A refactor that removes a process boundary must state
what was crossing it. (ii) A stage that failed every unit must not report success. (iii)
**Resume must key on the artefact, not on the row** — `'dockq' in row`, never "a row exists".
This is the same error class as keying a batch on a process exit code, which this project
already had a rule about; I reproduced it one level up.

**Fixes:** `mp_context=multiprocessing.get_context("spawn")`; `return 1 if n_err else 0`;
`done_keys(..., require="dockq")`.

### 5.2 I "corrected" a correct number using four contaminated samples

**What happened.** The project sized budgets at 84 s/fold. I declared this a "1.65× sizing
error" and revised it to ~140 s, based on historical medians of 133–150 s plus four live
measurements averaging 141 s. The completed arm settled it: **239 folds, 6.0 h, median 84 s.**

**Why wrong.** 84 s was the *quiet-machine* rate and was labelled as such. The 133–150 s
medians came from *contended* runs. My four live samples were taken while I was running
analyses on the same box. I overrode a correctly-labelled estimate with contaminated data.

**General lesson.** The project already carries *check load before assuming a library
saturates your cores*. This is the mirror image: **check load before attributing a slow
measurement to the task rather than to the machine.** A rate measured while you work on the
machine is a rate for a busy machine. Withdrawn in place in the 2026-09-18 doc.

### 5.3 The first two shortlist-sizing answers were both wrong

**What happened.** Sizing by "retain the true top 5 with probability ≥0.95" gave depth
**119 of 239**. That is a defensible answer to a question nobody should ask: **retaining the
best design is not picking it**, and only the pick ships.

**How caught.** Simulating the *whole* procedure — one seed on all 239, take top *k*, re-seed
those, argmax — and recording the *true* score of the design finally named:

| k | extra folds | E[true score of the pick] |
|---|---|---|
| 5 | 10 | +1.347 |
| 10 | 20 | +1.384 |
| 20 | 40 | **+1.395** |
| 30 | 60 | +1.403 |
| 119 | 238 | +1.388 |
| 239 | 478 | +1.380 |

Flat past k ≈ 20; 3-seeding all 239 at 478 folds is no better than 40 folds. The pick's quality
is bounded by the reliability of the *choosing* measurement, not by list length — a deeper list
adds candidates measured just as badly, so a noisy-high mediocre design is promoted about as
often as the true best is found.

**Which points elsewhere.** At fixed budget, spend on seeds:

| budget | 3 seeds | 5 | 7 | 10 |
|---|---|---|---|---|
| 40 folds | 20×3 → +1.402 | 10×5 → **+1.434** | 6×7 → +1.412 | 4×10 → +1.385 |
| 120 folds | 60×3 → +1.388 | 30×5 → +1.459 | 20×7 → **+1.466** | 13×10 → +1.479 |
| 240 folds | 120×3 → +1.384 | 60×5 → +1.458 | 40×7 → +1.478 | 26×10 → **+1.502** |

**Three seeds is the worst allocation at every budget tested.**

**Transferable principle.** When selection is noisy there are two places to spend measurement —
*more candidates* or *more precision per candidate* — and they are not interchangeable. Returns
to breadth collapse far sooner than intuition suggests. Simulate the whole procedure including
the final argmax; do not optimise a proxy like retention.

### 5.4 The surrogate's degenerate-span bug

**What happened.** Two metrics have `medium == cutoff` (`ipsae` 0.60/0.60, `netsolp` 0.50/0.50).
My first implementation returned the medium anchor whenever *either* span was zero, which
swallowed the value including at `good`: a design sitting exactly on `ipsae = 0.80` scored 7.0
instead of 9.5, and `final` 95.00 came back as surrogate 87.50.

**How caught.** The anchor-agreement test, written immediately after the module and before any
use. Reading the code would not have found it — the guard looks obviously correct.

**General lesson.** When you build a continuous approximation to a discrete function, test that
it agrees with the original wherever both are defined. Those points are the only place the
approximation has a checkable right answer, and **a degenerate interval is exactly where
interpolation code goes wrong.**

### 5.5 A projection that was never measured drove two days of scheduling

Fold batching was costed at "~1.8×" from an unmeasured split between per-fold and
per-invocation time. Measured: **1.16×** (84 s → 72 s), saving 0.8 h on a 239-fold arm rather
than 2.4 h. The code is correct and accepted; the *justification* was the least-examined number
in the argument, and I used it in scheduling arguments too.

---

## 6. Degenerate and failure cases

| case | status |
|---|---|
| `medium == cutoff` (degenerate lower span) | **handled** — returns the poor anchor; such designs fail the gate anyway (§5.4) |
| raw value beyond `good` | **handled** — same slope continues, clamped at 10 |
| raw value below `cutoff` | **handled** — continues down, clamped at 0 |
| a metric missing entirely | **handled** — surrogate returns NaN rather than a plausible number |
| empty batch | **handled** — returns empty result, no invocation |
| duplicate labels in one batch | **handled** — raises; they would collide in the output directory |
| label containing `pae`/`plddt` | **handled** — raises; the scoring tool locates the pLDDT file by string-substituting the PAE path |
| half-failed batch | **handled** — per-label artefact assertion; one bad complex costs one fold |
| run interrupted mid-arm | **handled** — resumable, and fold order is shuffled so any prefix is balanced across arms |
| two Boltz processes on one 12 GB GPU | **not handled** — would OOM and exit 0; the chain script serialises stages by polling instead |
| shortlist smaller than 2 designs | **not handled** — reliability is undefined; not reachable at k=20 |

---

## 7. Verification — how we know it works

**Surrogate agrees with the rubric at every anchor.** The check that found the §5.4 bug:

```bash
cd locksmith-antibody-hackathon
/home/rrobin711/.venvs/locksmith/bin/python -c "
from locksmith.select import surrogate; from locksmith.score import evaluate
from locksmith.config import load
cfg=load()
for a in ('cutoff','medium','good'):
    raw={n:getattr(b,a) for n,b in cfg.bands().items() if 1 in b.challenges}
    print(a, evaluate(dict(raw),1,cfg).final, surrogate.compute(dict(raw),1,cfg).value)"
```

Healthy: the two numbers are identical at all three anchors (38.50 / 70.00 / 95.00).
**Plausible-but-wrong:** they agree at `cutoff` and `medium` but not `good` — that is the
degenerate-span bug, and it looks like a rounding issue rather than a logic error.

**Batching reproduces the unbatched path.** `scripts/34_verify_batching.py`, four tiers:

| tier | check | observed |
|---|---|---|
| 0 | is the *unmodified* path bitwise reproducible? | **yes** — sha256 `11b06b4b58b2b0e0` twice |
| 1 | batch-of-1 byte-identical to single path | **yes** — same sha256 |
| 2 | batch-of-6 DockQ within ±0.054 (3 × the 0.018 seed sd) | **all 6 pass**, max Δ 0.025, 0 failures |
| 3 | speed-up | 84 s → 72 s = **1.16×** |

Tier 0 exists because without it a tier-1 mismatch is uninterpretable: it could mean the new
code changed the result, or that the tool is not bitwise deterministic on this GPU. Those
demand opposite responses. **Transferable principle: a reproducibility test needs a control
establishing that reproducibility is achievable at all.**

**The noise model held.** Predicted 7-seed within-design sd from the 3-seed estimate: 0.529
surrogate points. Measured over 7 seeds: **0.467** (0.88×). No systematic component appeared,
so averaging kept paying and the §5.3 sizing rested on a sound premise.

**The winner's-curse correction was validated, not merely applied.** Shrinkage (2.4) predicted
**94.963** before the fresh seed was folded; seed 23 — used nowhere in selection — measured
**94.962**. The raw selection mean was 0.155 too high.

**What a plausible-but-wrong good result looks like here.** A winner with a high raw score and
no fresh-seed check: it will be biased upward by roughly `(1 − reliability) × (observed −
mean)`, which at reliability 0.629 is 37% of its apparent margin. It would look excellent and
regress on any re-measurement.

---

## 8. Honest assessment

**Solid.** All 239 folds and scores are complete and reproducible. The surrogate is a pure
function, anchor-tested. G3's verdict rests on a 10,000-sample permutation test with the null
model chosen before the data. The shrinkage correction was validated against an independent
measurement to 0.001 points — that is the strongest single result here.

**Weak — the ranking is not resolved at the top.** First and second are separated by **0.022
surrogate points = 0.1 standard errors** of the 7-seed mean. Second place has a *higher* mean
DockQ (0.750 vs 0.747) and a tighter spread. This is *a* best design, not *the* best. The
evidence does not support claiming we found the optimum.

**Weak — shortlist reliability is 0.629, not the 0.849 simulated.** The noise behaved exactly
as predicted; the *signal* was destroyed by selection. The shortlist's between-design sd is
0.290 against the pool's 0.562. Any reliability quoted for a selection stage must be computed
on the range that stage actually sees, and shortlisting is precisely the operation that
destroys range. This project has now been bitten by range restriction three times.

**Not demonstrated — G3's cost saving.** We *measured* the filter, we did not *use* it. All 239
were folded, so the 194-fold saving is a simulation over folded data. Demonstrating it needs a
separate run that prunes before folding; doing both at once is the circularity the design
avoided.

**A tension worth stating plainly.** The named winner has aromatic count **2**, so the filter
at its own pre-registered threshold would have discarded it. That is not a contradiction of G3
— the gate was deliberately written around *mean* quality because the filter was already shown
not to reach the maximum — but anyone quoting "the filter works" without that sentence is
overselling it.

**Untested.** Batching has never been used in a production run; it is accepted on a 6-complex
test. The 1/√k noise model is verified to k=7 only. Every conclusion is conditional on one
generator (ProteinMPNN), one predictor (Boltz-2), and CDR-H3 length fixed at 13.

---

## 9. Next steps

1. **More seeds on the top 2–3 designs** — the only way to resolve the ordering. ~20 folds,
   ≈30 min. Unblocks an honest claim about *which* design is best.
2. **M4/M5: the validation dossier** for the named design — specificity controls, hotspot
   ablation, epitope-overlap check. This is the deliverable a lab would actually read, and it
   now has a design to be about.
3. **RFdiffusion or RFantibody, to open the CDR-H3 length axis.** Blocked on an install and
   qualification step of its own; ProteinMPNN is fixed-backbone and asserts equal length at
   `design/mpnn.py:139`. This is the one genuinely unexplored dimension, and the aromatic
   result is explicitly not generalisable across it.
4. **A pruning run that demonstrates rather than simulates the filter's saving** — optional,
   and only worth it if the cost claim needs to be defensible.

---

## 10. Glossary

**Aromatic** — the amino acids F, W, Y, whose side chains contain a ring. **Boltz-2** — the
diffusion-based structure predictor used throughout. **CDR** — complementarity-determining
region, one of six loops doing the binding; **CDR-H3** is the third heavy-chain loop, 13
residues here. **DockQ** — 0–1 similarity of a predicted complex to the experimental one.
**Fab / Fv** — larger and smaller antibody fragments; we fold Fabs (549 residues here).
**Fold** — one structure prediction. **ipSAE / iface_plddt / ΔG / contacts / cdr_sasa** — the
structure-derived rubric metrics. **NetSolP** — a sequence-based solubility predictor.
**Novelty** — CDR-H3 sequence identity to the parent antibody; *lower* is better and the
rubric prices it at 2× any single binding metric. **PD-1** — the antigen. **pembrolizumab** —
the licensed reference antibody. **ProteinMPNN** — the fixed-backbone sequence designer;
**temperature** is its sampling-diversity dial. **Reliability** — equation (2.2). **Seed** —
the random seed of one diffusion run. **Surrogate** — the continuous ranking function of §3.1.
**Winner's curse** — the upward bias of an argmax over noisy scores, §2.3.
