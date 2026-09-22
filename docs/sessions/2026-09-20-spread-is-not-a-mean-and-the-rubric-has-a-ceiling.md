# Spread is not a mean, and the rubric has a ceiling

**2026-09-20, ~00:30–02:00.** Planning-and-instrumentation session. Its output is three
pre-registered overnight experiments, two analyses that needed no GPU at all, and two
corrections to a plan that arrived from outside the project.

This doc is self-contained: it defines its terms and restates the background it needs.
Where an idea was developed properly in an earlier session it is summarised in a
sentence and linked, not relocated.

---

## 0. Where the project was

[[2026-09-19-three-seeds-is-the-worst-allocation|M3 closed on 2026-09-19]] with a named
Challenge-1 design, `mpnn_T0.5_s104_036`, at a winner's-curse-discounted score of
94.963 on the project's continuous ranking surrogate and **87.5** on the competition's
own banded composite. The top of the ranking was not resolved — first and second sat
0.022 surrogate points apart, which is 0.1 standard errors of a seven-seed mean.

A review from outside the project argued, correctly, that the effort had drifted: the
machinery for *choosing* among designs had become very good while the evidence that any
chosen design is *real* did not exist. It proposed three overnight jobs — widen the
CDR-H3 ensemble measurement, run specificity controls, run hotspot ablation — and
invited pushback on the sampling design.

Two of its specific numbers turned out to be wrong, and the sampling design turned out
to be backwards. Both are worth the space, because the mistakes are instructive rather
than careless.

---

## 1. The idea this session is actually about: estimating a spread is not estimating a mean

### 1.1 The two laws

Suppose a design's true quality is a fixed number and each fold of it returns that
number plus independent noise of standard deviation σ. Fold it `k` times and average:

$$\mathrm{SE}(\bar{x}) = \frac{\sigma}{\sqrt{k}}$$

Halving the error costs four times the folds. That is the law M3 reasoned with, and it
is why M3 concluded that at a fixed budget you should buy **depth** (more seeds per
design) rather than **breadth** (more designs) — up to a shortlist of about twenty, past
which extra designs are just more candidates measured equally badly.

Now suppose the quantity you want is not the mean but the **spread** — how much the
structure moves between folds. The sampling error of a variance estimate from `k`
independent draws is, for roughly normal data,

$$\mathrm{SE}(s^2) \approx s^2\sqrt{\frac{2}{k-1}}, \qquad
\frac{\mathrm{SE}(s)}{s} \approx \frac{1}{\sqrt{2(k-1)}}$$

Put numbers in it. At `k = 3` the relative error of the spread is **50%**; at `k = 5`,
**35%**; at `k = 7`, **29%**. Compare the mean, whose relative error at those same `k`
falls as 0.58, 0.45, 0.38 of σ. **A spread estimate is markedly more seed-hungry than a
mean estimate**, and — this is the part that flips the conclusion — the *marginal return
to depth decays much faster in `k` for the spread than the naive intuition suggests,
because the first pair already carries most of the information about whether a loop
moves at all.

So the allocation question has to be re-asked from scratch whenever the target quantity
changes. The M3 answer ("depth, not breadth") does not transfer to a study whose
outcome variable is a spread. This is the transferable principle of the session:

> **An optimal-allocation result is a property of the estimator, not of the pipeline.
> Change what you are estimating and you must re-derive it.**

### 1.2 Why attenuation is the thing that actually matters

The overnight study correlates a confidence metric against the spread. A correlation
between two noisy measurements is attenuated — dragged toward zero — by the square root
of each measurement's reliability:

$$\rho_{\text{obs}} \approx \rho_{\text{true}}\sqrt{r_1 r_2}$$

where reliability `r` is the fraction of a measurement's variance that is real signal
rather than sampling noise:

$$r = \frac{\mathrm{var_{between}}}{\mathrm{var_{between}} + \mathrm{var_{sampling}}}$$

This project has been bitten by the neighbouring phenomenon (range restriction) three
times, and the general rule — measure the noise floor before comparing a correlation to
a threshold — is already in `LEARNINGS.md`. What was new here is that the reliability of
*this particular estimator* had never been measured, and it could be measured **for
free**.

### 1.3 The free measurement

Twenty designs were already folded at seven seeds each during M3. Seven seeds give
C(7,2) = 21 pairwise comparisons per design, which is enough to estimate both halves of
the reliability ratio directly. `scripts/36_ensemble_power.py` does it:

| seeds k | sampling variance of a k-seed spread | reliability | attenuation √r |
|---|---|---|---|
| 2 | 0.0628 Å² | 0.591 | 0.769 |
| 3 | 0.0247 Å² | 0.792 | 0.890 |
| 4 | 0.0122 Å² | 0.885 | 0.941 |
| 5 | 0.0062 Å² | 0.938 | 0.969 |
| 7 | 0.0000 Å² | 1.000 | 1.000 |

Two things about this table are traps, and both matter.

**The k=7 row is a tautology, not a measurement.** "Truth" was *defined* as the 7-seed
spread, so a 7-seed estimate has zero error against it by construction. Correcting for
this — modelling the sampling variance as `V₁ / C(k,2)` with `V₁ = 0.0628 Å²` fitted
from the k=2 row, then subtracting the 7-seed sampling variance from the observed
between-design variance — gives a corrected k=7 reliability of **0.968**, not 1.000. The
conclusions do not change, but a table with a 1.000 in it invites a reader to believe
something no data can support.

**The whole table is carried by one design.** Among the 20 shortlist designs the
7-seed spreads are 0.31, 0.37, 0.39, 0.40, 0.45, 0.46, 0.46, 0.49, 0.50, 0.50, 0.51,
0.52, 0.52, 0.54, 0.55, 0.65, 0.68, 0.74, 0.82 … and **1.77 Å**. Drop that last one and
the between-design variance collapses by 5.7×:

| | with the outlier | without it |
|---|---|---|
| between-design variance | 0.0907 Å² | 0.0145 Å² |
| reliability at k=2 | 0.591 | **0.265** |
| reliability at k=3 | 0.813 | **0.520** |
| attenuation at k=2 | 0.769 | **0.515** |

This is the same failure mode the project already recorded once — a strong R² carried
entirely by two deliberately-dead poly-Gly anchors — arriving in a new costume. The
honest statement is that reliability is somewhere in a **factor-of-two band**, and the
overnight run is partly designed to close it.

There is a mitigating structural fact worth stating precisely. These 20 designs are the
**M3 shortlist**, i.e. the top 20 of 239 selected on a composite. Selection restricts
range, and the *within*-design sampling variance is unaffected by that (it is what it
is, per design) while the *between*-design variance is measured on a deliberately
narrowed set. The earlier 40-design discovery pool spanned a much wider range of
spreads. So the shortlist's reliability is more likely an **under**-estimate than an
over-estimate — but "likely" is not "measured", and that is precisely why the outlier
question goes into the pre-registration as a named hypothesis rather than a footnote.

### 1.4 What the arithmetic recommends

The brief proposed 40–60 designs at 5–7 seeds. Put the two effects against each other.
Going from 2 seeds to 5 costs **4×** the folds and recovers at most 0.967/0.769 = **1.26×**
of the attenuated effect. The same folds spent on breadth take `n` from 60 to 239, and
the standard error of a correlation on the Fisher-z scale is `1/√(n−3)`, so that is a
**2.0×** shrink. Breadth wins, and it wins by more than the factor-of-two uncertainty in
the reliability.

Hence the design that actually launched: **one extra seed for all 239 designs first
(k=2, complete pool), then a third seed in the same shuffled order for as long as the
night lasts.**

### 1.5 The objection to k=2, and why it does not hold

A two-seed "spread" is a single pairwise deviation. On its own you cannot separate real
between-design variation from sampling noise, because you have no replication within a
design.

You do not need replication *in the pool*, because the sampling variance is a property
of the estimator, not of the sample. `V₁ = 0.0628 Å²` is pinned down by the 21 pairs per
design in the 7-seed shortlist, and then

$$\mathrm{var_{between}}(\text{pool}) = \mathrm{var}\big(\text{observed 2-seed spreads}\big) - V_1$$

identifies the quantity of interest from the full pool. This is a variance decomposition,
not an assumption — it holds as long as the per-pair sampling variance is comparable
across designs, which the 7-seed data can itself be checked against.

It also makes the run **self-diagnosing** on the outlier question. Only a full-pool
measurement can say whether the 1.77 Å design is a freak or the visible tip of a fat
tail, and either answer is a result: a fat tail makes the ensemble axis real, and no
tail means CDR-H3 heterogeneity simply does not vary much across fixed-backbone
redesigns of one scaffold — a null that kills the axis and must be reported as loudly as
a positive would have been.

### 1.6 Nesting, shuffling, and a stopping rule that is allowed to exist

The design is **nested**: every design gets seed 2 before any design gets seed 3. Any
stopping point therefore leaves a complete, balanced k=2 pool plus a k=3 prefix — never
a half-finished arm.

Fold order is **shuffled with a fixed seed before the run**. The pool is built arm by
arm, so an unshuffled partial night would return the low-temperature arms complete and
T = 0.5 missing entirely, which does not shrink the temperature comparison, it destroys
it. This is the same reasoning as randomising collection order against drift, and it is
why a **wall-clock stopping rule is legitimate here**: the shuffle is fixed before any
data exists, so when the run stops is independent of everything about the designs. A
stopping rule that peeked at results would be a garden of forking paths; this one cannot.

---

## 2. The second thing this session established: the rubric has a ceiling, and the free points are in a different place than advertised

The external review said NetSolP was "the single highest-value hour available", worth up
to 8 final points, computed from sequence alone with no GPU, and untouched. Two of those
claims are wrong and the third is the interesting one.

### 2.1 The arithmetic, with this project's actual conventions

`final = 10 × (0.60 × mean(six binding sub-scores) + 0.20 × developability + 0.20 × novelty)`,
and this project maps bands to their **midpoints**: good 9.5, medium 7.0, poor 2.5
(`config/metrics.yaml`). The winner scores good on everything except two metrics:

| metric | winner | Good needs | band | worth if moved to Good |
|---|---|---|---|---|
| `dockq` | 0.747 | ≥ 0.80 | medium | **+2.50** |
| `netsolp` | 0.585 | ≥ 0.70 | medium | **+5.00** |

So the reachable maximum is **95.0**, not 100, and the gap is **7.5 points**, not 12.5.
NetSolP is worth **+5.00**, not +8 — the +8 comes from reading the bands as 6/10 and
10/10 rather than at their midpoints. Quoting +8 overstates the prize by 60%.

### 2.2 Why NetSolP is probably a ceiling rather than a lever

Three facts, each already in the repository, compose into a conclusion nobody had drawn:

1. `netsolp_chain_agg: min` — a design scores its **worst** chain.
2. ProteinMPNN redesigns only the 29 IMGT CDR positions of the **heavy** chain
   (`design/mpnn.py`). The entire light chain is pembrolizumab's, byte-identical across
   all 239 designs.
3. Pembrolizumab's own chains measure **0.623** (Fab heavy) and **0.626** (Fab light) on
   the ESM1b five-fold ensemble — both Medium.

If (3) holds then `min(VH, 0.626) ≤ 0.626` for every possible design, and the Good band
at 0.70 is **unreachable by heavy-CDR redesign at all**. The supporting evidence already
on disk: the 40 designs measured so far span **0.567–0.597**, every one *below* the
native heavy chain.

### 2.2a Measured — it is a ceiling

`scripts/40_rubric_headroom.py` finished at 01:09 and scored all 239 designs:

| quantity | value |
|---|---|
| ~~VH~~ **Fab heavy chain** over 239 designs | **0.5617 – 0.6187** (mean 0.5868) |
| ~~VL~~ **Fab light chain**, pembrolizumab's, identical in every design | **0.6257** |
| achievable `min(VH, VL)` | **0.6187** |
| Good band edge | 0.70 |
| shortfall | **0.0813** |
| ⚠ **corrected later the same day** | these are **Fab** chains mislabelled VH/VL. The handbook specifies the **Fv**, where pembrolizumab is VH 0.733 / VL 0.569 and **168/239 designs clear Good on VH** — the deficit is entirely the never-redesigned light chain. See `results/audit_2026-09-20.md` Check F. |
| designs reaching Good | **0 / 239** |
| shortfall ÷ pool spread of VH (0.0571) | **1.4×** |

*(An earlier draft of this doc put the shortfall at 3.4× the spread. That used the
40-design spread of 0.030; over all 239 the spread is 0.0571, so the correct multiple
is **1.4×**. Corrected in place — the conclusion is unchanged but the number was
wrong.)*

The statement is therefore not "we ignored developability" but **"20% of
this rubric is pinned at Medium for any pembrolizumab-framework Fab, including
pembrolizumab itself"** — which is a critique of the rubric, in the rubric's own terms,
of exactly the kind the ensemble result is. A design whose developability score cannot
be improved by designing is a scoring artefact, not a developability fact.

Two honest routes would remain: redesign the light-chain CDRs too, or change the
`netsolp_chain_agg` convention — and the second is a convention change rather than a
design improvement, so it would have to be declared as one.

Note the shape of the evidence: **zero of 239**, with the best design 0.081 short and
the whole axis only 0.057 wide. That is not "we did not try hard enough", it is a
constraint of the scaffold, and it means `final` has a practical ceiling of **90.0**
rather than 95.0 — with the remaining 2.5 points sitting entirely in DockQ.

### 2.3 The lever that is real, and that nobody pulled

Novelty is **banded**: CDR-H3 identity below 70% scores Good, and there is *no further
reward for going lower*. The 239 designs span **15.4–46.2%** identity. Every one of them
is buying novelty the rubric does not pay for — and identity is a strong free predictor
of pose retention, at Spearman **+0.389** across the pool (and +0.505 in the earlier
40-design set).

The entire band from 46% to 69% identity is **unexplored design space that is free on
novelty**. Pool DockQ maxes at 0.777 against a target of 0.80, and the pembrolizumab
refold reaches 0.818, so the gap is small and plausibly closable by being *less* novel
at no scored cost.

This is **Goodhart running in our favour**, and it is more interesting than the 2.5
points: a banded metric scores a design at 69% identity and one at 15% identically on
novelty while they differ substantially on binding. Worth one cheap generation arm, and
worth a sentence in any writeup about what banding does to a rubric. It is *not* worth
claiming the points before the arm is run — the implied identity for DockQ 0.80 is a
**linear extrapolation beyond the observed range**, and DockQ is bounded above by what
the predictor can do on this complex at all.

---

## 3. What was built, and the control that was added to each

Three GPU jobs and one CPU job, all pre-registered before any run directory existed.

### 3.1 Specificity — `scripts/37_specificity_fold.py`

The winner, unchanged, folded against five antigens at three fresh seeds each (31–33,
used nowhere in selection or validation):

| antigen | role | length |
|---|---|---|
| PD-1 (5GGS) | **positive control** | 113 aa |
| PD-L1 IgV (5IUS chain C) | functional decoy — the ligand the drug must outcompete | 113 aa |
| TIM-3 (8TBB) | hardest decoy — human checkpoint receptor, same Ig V-set fold | 110 aa |
| ULBP6 (8RWB) | human, MHC-I-like fold | 172 aa |
| PcrV (9JBQ) | bacterial, unrelated — the floor | 134 aa |

PD-L1 is truncated at its IgV/IgC boundary for **size parity** with PD-1 — the full
214-aa ectodomain would confound interface size with antigen identity. That is a terminal
truncation, which `seq_for_folding()` permits; when the same call was tried on 5IUS
chains A and B it **refused them**, because both have internal gaps. That guard exists
because folding a coordinate-derived sequence with an internal deletion silently predicts
a protein that does not exist, and it cost this project a withdrawn result in September.
It fired correctly tonight on the first attempt to use a new reference structure.

**The asymmetry that has to travel with the result:** a decoy scoring *high* is strong
evidence of a problem; a decoy scoring *low* is weak evidence of its absence, because a
predictor unreliable at novel placement (measured post-cutoff median DockQ 0.291) will
score novel pairings low whether or not they would bind. The honest summary of a clean
panel is "no evidence of gross promiscuity, from a test that could only have detected
gross promiscuity".

**The control this job is missing, named rather than discovered later:** a *positive
decoy* — an antibody known to bind TIM-3, folded the same way, proving the pipeline can
produce a high score against that antigen at all. 8TBB is exactly that complex and is
already on disk; it costs about three folds. Without it, a clean panel is also consistent
with "Boltz cannot dock anything to TIM-3".

### 3.2 Hotspot ablation — `scripts/38_ablation_fold.py`

Interface contacts were counted first (heavy-atom pairs within 5.0 Å of the antigen,
per heavy-chain residue, from the winner's seed-1 structure) and the mutants chosen from
the measurement, not from intuition:

| mutant | contacts | region |
|---|---|---|
| Y31A | 54 | CDR-H1 |
| D100A | 54 | CDR-H3 |
| R99A | 50 | CDR-H3 |
| N57A | 39 | CDR-H2 |
| D102A | 31 | CDR-H3 |
| R97A | 30 | CDR-H3 |
| Y31A/R99A/D100A | 158 | triple |
| **L96A** | **0** | **negative control** |
| **Y106A** | **0** | **negative control** |

The two negative controls are the experiment. An ablation without them cannot
distinguish "the score tracks the interface" from "the score punishes any mutation", and
this project has banked and then withdrawn three conclusions that lacked exactly this
kind of control. Both are alanine substitutions at CDR-H3 positions with **zero**
measured antigen contact: same loop, same kind of perturbation, no interface.

Y106A doubles as a probe of the aromatic result — it removes a non-contacting CDR-H3
aromatic, which separates "aromatics act through the interface" from "aromatics act
through loop conformation". n = 1, so it generates a hypothesis and nothing more.

A limit that must never be dropped: Boltz **re-predicts** each mutant from scratch, so
the model is free to re-dock. This measures whether the *pipeline's verdict* survives
losing the hotspots, which is the right question for a scored pipeline. It is **not** an
in-silico ΔΔG and must not be called one; real alanine scanning holds the backbone fixed.

### 3.3 Ensemble widening — `scripts/39_ensemble_wide_fold.py`

As derived in §1. Batched at 12 complexes per Boltz invocation. The batching arithmetic:
84 s serial against 72 s at batch 6 implies a fixed per-invocation cost of only ~14 s and
a marginal fold of ~70 s, so batch 12 gives ≈70.8 s/fold (1.19×) and larger batches buy
almost nothing — while a crash costs the whole in-flight batch, so 12 caps the loss at 12
folds. `--seed` is invocation-level in Boltz, which is precisely why a nested
seed-by-seed design and batching agree with each other rather than fighting.

### 3.4 Order of execution, which was also changed

The brief put the big ensemble job first, "because it is the valuable one". It runs
**last**. The ensemble job is ~4.6 h and the two tails are ~46 min combined; running the
big one first risks losing both tails to any overrun, while running the tails first risks
only the tail of a job that **degrades gracefully** — the folds are shuffled, so stopping
early costs precision rather than the experiment. Quantified: losing 46 minutes off a
shuffled pool moves `n` from ~239 to ~200 and the detectable effect by about 0.01,
against a 100% chance of losing a whole result the other way round.

> **Run the job that degrades gracefully last.** Ordering by value is right only when
> everything fails the same way.

### 3.5 The novelty probe — added at 01:30, and the bug that testing caught

The headroom audit (§2.3) said the one reachable rubric point sits in DockQ, reachable
by being *less* novel at no scored cost, because novelty is banded at < 70% identity and
the pool spans only 15.4–46.2%. Turning that into an experiment produced something
sharper than the 2.5 points.

Counting pembrolizumab's CDR-H3 contacts in the 5GGS crystal (heavy-atom pairs ≤ 5.0 Å)
gives an extremely unequal distribution across `ARRDYRFDMGFDY`:

| zero-contact | | paratope | contacts |
|---|---|---|---|
| 95 A, 96 R, 98 D, 104 G, 105 F, 107 Y | 0 each | 100 R | 81 |
| 106 D | 3 | 101 F | 52 |
| 102 D | 6 | 99 Y | 42 |
| | | 103 M | 29 |
| | | 97 R | 23 |

**Six of thirteen positions touch the antigen not at all**, and the novelty band needs
only four substitutions. So the rubric's novelty score can be maximised without touching
the paratope. Three arms test it, each redesigning *only* the listed CDR-H3 positions
with H1, H2, the light chain and the antigen held native:

| arm | positions | contacts touched | identity | band | n |
|---|---|---|---|---|---|
| A | 95, 96, 98, 104 | 0 | 69.2% | Good | 14 |
| B | 95, 96, 98, 104, 105, 107 | 0 | 53.8% | Good | 14 |
| C | 97, 99, 100, 101, 103, 106 | 227 | 53.8% | Good | 14 |

**B and C are identical on the scored axis and differ by 227 antigen contacts.** If B
keeps the pose and C loses it, the novelty metric measures sequence distance, not
interface novelty — the same shape of finding as the pLDDT/ensemble result. And note
that Challenge 2 has no DockQ at all, so nothing in *that* rubric could detect the
difference.

**The bug the test caught.** The first version asked ProteinMPNN to redesign those
positions and assumed they would change. They did not: MPNN is a sequence-*recovery*
model, and at T = 0.3 arm A came back at **92.3% identity** — one of four positions
actually differed. The arm would have run all night and tested nothing, while looking
like it had worked. The fix is `--omit_AA_jsonl`, forbidding the native residue at each
designed position, which makes identity exact by construction; re-running gave exactly
69.2 / 53.8 / 53.8, one value per arm. **"Designable" does not mean "will change"** —
and a generator's output distribution has to be checked against the design intent
before the experiment depends on it, not after.

---

### 3.6 The contention diagnosis, because it cost 2.3× and was invisible

The first fold took **307 s** against the project's 84 s quiet-machine figure. Folds two
and three came in at 207 s and 195 s. The GPU read 100% utilisation at 765 MHz and 49 °C,
which rules out thermal throttling, and `nvidia-smi -q -d PERFORMANCE` reported
`SW Power Cap: Active` — normal for this laptop under sustained load and also true during
M3, so not the cause.

The cause was CPU. `ps` showed NetSolP at **395–1568% CPU** (it sets
`intra_op_num_threads = os.cpu_count()`) and Brave at **44% CPU and 6.4 GB RSS** of
15 GB. Boltz needs CPU for featurisation and data loading between GPU phases, so a
saturated CPU stalls a GPU-bound job. Renicing NetSolP to 19 helped a little; closing
Brave and letting NetSolP finish brought folds to **86–97 s**.

| state | fold time | ensemble folds by 07:30 |
|---|---|---|
| Brave open + NetSolP running | 195–307 s | ~95 of 239 |
| Brave closed, CPU quiet | 86–97 s | all 239 |

Two things worth keeping. First, `nice` did **not** contain an ONNX runtime that had
already claimed every core — it yields on contention but the thread count is set at
session start, so the damage is done by then; the fix is to bound the library's threads,
not the process's priority. Second, the project's own operating rule (PLAN.md §2.3:
close the chat apps for batch nights) exists for exactly this and had not been followed;
**an operating rule that is not mechanised gets skipped at 1 a.m.**

---

## 4. Results

### 4.1 Specificity — the design fails its own pre-declared test, and a control was added

Complete at 01:35. Fresh seeds 31–33, ipSAE per seed:

| antigen | role | ipSAE per seed | mean | ΔG mean | seeds ≥0.60 **and** ΔG ≤ −10 |
|---|---|---|---|---|---|
| PD-1 | positive control | 0.859, 0.834, 0.847 | **0.847** | −12.5 | — |
| PD-L1 IgV | functional decoy | 0.000, 0.000, 0.000 | **0.000** | −11.6 | 0 / 3 |
| **TIM-3** | same-fold decoy | **0.624, 0.612, 0.469** | 0.568 | **−14.1** | **2 / 3 ⚠** |
| ULBP6 | MHC-I-like decoy | 0.000, 0.010, 0.012 | **0.007** | −11.8 | 0 / 3 |
| PcrV | bacterial decoy | 0.711, 0.103, 0.449 | 0.421 | −9.2 | 0 / 3 |

The positive control reproduces at 0.847 (Good band), and PD-L1 and ULBP6 collapse to
**exactly zero** — which matters, because it proves the metric *can* go to zero and so
the TIM-3 number cannot be waved away as a floor effect.

**TIM-3 triggers the pre-declared failure condition**: ipSAE ≥ 0.60 with ΔG ≤ −10 on
2 of 3 seeds. TIM-3 is a human checkpoint receptor with the same Ig V-set fold as PD-1,
i.e. the realistic off-target for an anti-PD-1 antibody.

**And the analysis code got this wrong first.** The verdict function tested the arm
*mean* (0.568, which passes) rather than the rule as pre-registered, which is per-seed
(0.624 and 0.612, which fails). Nobody would have noticed: the table would have read
"no decoy triggered the failure condition" and been wrong. Fixed, with the reasoning in
a comment at the site. **Pre-registration is worth nothing if the analysis quietly
implements a more convenient version of the rule** — and the convenient version is the
one you write when you already know the answer you would like.

**What the result does not yet mean.** The panel varies the antigen with the antibody
fixed, so it cannot separate *our design is cross-reactive* from *Boltz docks any
antibody onto TIM-3*. PcrV's 0.711 on one seed makes the second reading live. Six folds
settle it by varying the antibody with the antigen fixed — `scripts/46_decoy_reference_fold.py`,
added at 01:45 and queued first in stage 2:

- **pembrolizumab vs TIM-3** — a licensed, specific antibody that certainly does not
  bind TIM-3. If it also scores ~0.62, the finding is about the predictor.
- **8TBB Fab vs TIM-3** — a real TIM-3 binder, which sets the scale a "low" score has
  to be read against.

The three possible readings were written down before the folds ran, in the script
docstring, so whichever comes back is interpreted by a rule rather than by taste. These
folds are **exploratory** — added after seeing the result they interpret — and are
labelled that way in `results/specificity.md`.

**They came back at 08:04 and the answer is the unwelcome one:**

| antibody vs TIM-3 | ipSAE per seed | mean |
|---|---|---|
| pembrolizumab (certain non-binder) | 0.322, 0.189, 0.458 | **0.323** |
| **our design** | 0.624, 0.612, 0.469 | **0.568** |
| 8TBB Fab (real TIM-3 binder) | 0.614, 0.747, 0.684 | **0.682** |

The named design sits **between** a licensed specific antibody and a genuine TIM-3
binder, and much nearer the binder. The rule fixed in advance for this pattern reads:
*the design really is TIM-3-reactive relative to a specific antibody*. So the
pre-declared failure condition stands, and the "it is just the predictor" escape is
closed — pembrolizumab, folded identically against the same antigen with the same MSA,
scores 0.245 lower.

**Consequence, stated plainly:** `mpnn_T0.5_s104_036` shows predicted cross-reactivity
with a same-fold human checkpoint receptor. That sentence travels with the design
anywhere it appears. It is also the single most useful thing the night produced about
the molecule, and it cost fifteen folds — against six days of work on which design to
name.

### 4.2 NetSolP — measured, and it is a ceiling

§2.2a. 0 of 239 designs reach the Good band; the best is 0.0813 short; the whole
achievable range of the axis is 0.0571 wide. 20% of the rubric is pinned at Medium for
any pembrolizumab-framework Fab, including pembrolizumab itself.

### 4.3 The ensemble widening — **the headline claim does not survive its own test**

n = 239 designs (155 at k=2, 84 at k≥3), all four arms balanced. Reliability of a k=2
spread came out at **0.686**, attenuation 0.828 — comfortably above the pessimistic
0.265 that the outlier-free shortlist suggested, so the pool does have a genuine fat
tail. Spread spans **0.15–2.58 Å**, median 0.45 Å, and dropping the top three designs
only takes reliability 0.686 → 0.620. **H5 answered: the variation is a distribution,
not an artefact.**

Then the primary hypotheses, and this is the part that matters:

| predictor of spread (from the seed-1 fold) | ρ | 95% CI | p | disattenuated |
|---|---|---|---|---|
| **mean loop pLDDT** (H1 said: blind) | **−0.432** | [−0.529, −0.321] | 2.9e−12 | −0.521 |
| interface pLDDT (H2 said: sees it) | −0.344 | [−0.455, −0.221] | 4.7e−08 | −0.416 |
| CDR-H3 aromatic count (H4) | +0.197 | [+0.080, +0.308] | 0.0022 | +0.238 |

**H1 is refuted, and it was the spine of the planned pitch.** Mean loop pLDDT is not
blind to CDR-H3 heterogeneity — it is the *best* single-fold predictor of it, better
than interface pLDDT. The 2026-09-18 claim (ρ −0.168, p=0.69) was measured on **eight
designs**; at n=239 the same quantity is −0.432 with a CI nowhere near zero. That was
not a subtle effect hiding in noise, it was noise being read as an effect.

**H4 reverses too.** On 2026-09-18, aromatic fraction explained away the ensemble
signal (partial ensemble→DockQ collapsed to −0.081, p=0.62). Over the full pool the
partial correlations run the other way:

- interface pLDDT → spread, controlling aromatics: **−0.293** (p=4.4e−06) — survives
- aromatics → spread, controlling interface pLDDT: **+0.056** (p=0.39) — collapses

The temperature table (H3) explains why: aromatics correlate with spread at **+0.455**
in the T=0.1 arm and only +0.079 / +0.239 / +0.155 at T=0.2 / 0.3 / 0.5. **The aromatic
finding was a T=0.1 phenomenon and the original 40 designs were all T=0.1.** The pLDDT
relationship, by contrast, holds in every arm (−0.407, −0.253, −0.440, −0.567).

Two prior conclusions are therefore **withdrawn**: "a residue's own confidence is blind
to conformational heterogeneity" and "a free sequence feature beats the three-fold
measurement". Both were true of the sample they were measured on and false of the pool.

### 4.4 Ablation — uninformative, and alarming for a different reason

| mutant | contacts removed | ΔG (Δ) | contacts (Δ) | DockQ (Δ) |
|---|---|---|---|---|
| Y31A | 54 | −12.8 (−0.1) | 98 (+1) | 0.730 (−0.017) |
| D100A | 54 | −12.2 (+0.4) | 96 (−1) | 0.736 (−0.010) |
| R99A | 50 | −12.2 (+0.4) | 94 (−2) | 0.733 (−0.014) |
| **Y31A/R99A/D100A** | **158** | −12.6 (−0.0) | **100 (+4)** | 0.716 (−0.030) |
| L96A *(control)* | **0** | −12.4 (+0.2) | 92 (−4) | 0.752 (+0.006) |
| Y106A *(control)* | **0** | −12.4 (+0.2) | 96 (−0) | 0.739 (−0.008) |

Per the pre-registration this is the **"controls degrade about as much as hotspots"**
branch, so the ablation is reported as uninformative about hotspot importance. But read
the triple row on its own terms: **removing 158 heavy-atom contacts — including R100,
which alone makes 81 — costs 0.030 DockQ and *gains* four contacts.** Boltz simply
re-docks the mutant and rebuilds an interface that scores as well as the original.

That is not a null. It is the same phenomenon as the post-cutoff failures (large,
confident, wrongly-placed interfaces) showing up in a controlled experiment, and it
says something sharp: **on this complex the scored binding metrics cannot distinguish a
designed interface from one the predictor invented to replace it.** The caveat in the
pre-registration — that Boltz re-predicts rather than holding the backbone — is not a
limitation here, it *is* the result.

### 4.5 Novelty probe — H2 not confirmed, H3 not reached

| arm | contacts touched | identity | DockQ mean | 95% CI | ipSAE |
|---|---|---|---|---|---|
| A — 4 zero-contact | 0 | 69.2% | 0.691 | [0.674, 0.707] | 0.761 |
| B — 6 zero-contact | 0 | 53.8% | 0.689 | [0.663, 0.713] | 0.744 |
| C — 6 paratope | **227** | 53.8% | 0.657 | [0.652, 0.662] | **0.825** |

B versus C is **+0.032 DockQ** (U=155, p=0.0094) — statistically real, but far below the
pre-registered 0.10, so **H2 is not confirmed and is reported as a null**. H3 fails too:
the best probe reaches 0.757 against the 0.80 Good edge, so the headroom audit's
extrapolation is **withdrawn as a prediction** and the 2.5 DockQ points are not
claimable this way. All three arms score *below* the 239-pool mean of 0.705, so
restricting redesign to CDR-H3 alone is worse than redesigning H1/H2/H3 together.

One line worth keeping: **arm C has the highest ipSAE (0.825) and the lowest DockQ
(0.657).** The design with the paratope deliberately destroyed is the one the confidence
metric likes most. That is consistent with §4.4 and with ipSAE's long record in this
project as a liveness test rather than a ranking metric.

The honest summary of the novelty probe is that it **failed to demonstrate its
hypothesis and incidentally produced more evidence for someone else's** — the
predictor's indifference to paratope identity, which the ablation found independently
the same night.

## 5. What is crude, stubbed, or unproven

- **Three prior conclusions were withdrawn tonight** (§4.3): loop pLDDT being blind to
  heterogeneity, aromatic fraction explaining away the ensemble axis, and the headroom
  audit's extrapolation to DockQ 0.80. All three were correct about the sample they were
  measured on. The first rested on **n = 8**.
- **The ablation is uninformative about hotspot importance** by its own pre-registered
  criterion, and is reported that way. What it does show (§4.4) is about the predictor.
- **Specificity's asymmetry still holds.** A high decoy score is strong evidence; the
  clean PD-L1/ULBP6/PcrV columns remain weak evidence of specificity, and this predictor
  has a measured post-cutoff median DockQ of 0.291.
- **The reference controls are exploratory**, added after seeing the result they
  interpret, and labelled so everywhere. Three seeds each.
- **Two seeds per ablation mutant** — enough against seed noise, not enough to rank
  mutants against each other. R97A's −0.126 DockQ is 7 seed sd and unexplained.
- **`loop pLDDT sd across seeds` (ρ +0.454) is partly circular** — an sd across seeds
  predicting a spread across the same seeds. It is listed for completeness and should
  not be quoted as an independent predictor.
- **Batching ran in production for the first time**: 365 batched folds, zero failures,
  against a six-complex acceptance test. That is now evidence, but it was a risk taken.
- **Everything remains conditional** on one generator, one predictor, one scaffold, and
  CDR-H3 length fixed at 13.

## 6. Glossary

**Attenuation** — the shrinking of a correlation toward zero caused by noise in either
measured variable; equal to √(reliability) per variable.
**CDR** — complementarity-determining region, one of six antibody loops that do the
binding; **CDR-H3** is the third heavy-chain loop, 13 residues throughout this project,
and the dominant contributor to specificity.
**DockQ** — a 0–1 measure of how closely a predicted complex matches an experimental one.
**Fab / Fv** — larger and smaller antibody fragments; this project folds Fabs (549
residues).
**Fold** — one structure prediction.
**ipSAE** — a confidence score computed from the predictor's own predicted aligned error.
**pLDDT** — the predictor's per-residue confidence, 0–100; **interface pLDDT** is its
mean over residues at the antibody–antigen interface, **loop pLDDT** its mean over
CDR-H3.
**ProteinMPNN** — the fixed-backbone sequence designer; its *temperature* controls
sampling diversity.
**Reliability** — the fraction of a measurement's variance that is signal rather than
sampling noise; between 0 and 1.
**Seed** — the random seed of one diffusion run; Boltz-2 is a diffusion model, so
different seeds give genuinely different structures, not merely different scores.
**Spread (here)** — RMS Cα deviation over CDR-H3 across all pairs of seeds, after
superposing each pair on the framework.
**Surrogate** — this project's continuous ranking function, built because the rubric
composite takes only three distinct values across 40 designs.
**Winner's curse** — the upward bias of the maximum of noisy scores; corrected by
shrinking toward the pool mean by the reliability.
