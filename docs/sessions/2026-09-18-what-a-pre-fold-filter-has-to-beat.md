# What a pre-fold filter has to beat

**Session:** 2026-09-18 (fourth of the day) · **Kind:** design review, no new folds ·
**Artefacts:** `scripts/27_review_m3_assumptions.py`, [[m3_plan_review|results/m3_plan_review.md]]

The M3 campaign plan arrived fully specified: generate wide, prune on CDR-H3 aromatic
fraction before spending GPU time, fold the survivors, rank on the three-seed mean rubric
score, re-score the winner on a fresh seed. It also carried a rewritten Gate 3 to replace
the vacuous one, and an instruction to fold a sample of the *rejects* so the cost claim
would not be circular. All of that is sound instinct. This session tested the plan's
assumptions against folds already on disk, before committing an overnight run to them, and
four of the assumptions did not survive.

Nothing here was folded. Every number comes from re-interrogating the 40-design × 3-seed
pool built for [[2026-09-18-the-ensemble-axis-loses-to-a-free-sequence-feature|the ensemble
validation]].

---

## 1. What a pre-fold filter is actually for, stated precisely

Define the campaign as an optimisation under a compute budget. We can generate sequences
essentially for free — ProteinMPNN emits a design in well under a second — but evaluating
one costs a structure prediction. Measured on this machine: **85 s per Fab fold on a quiet
GPU, 133–137 s contended**, for a 549-residue complex. So the budget is a fold count *B*,
and the question is how to spend it.

Two strategies compete:

- **Unfiltered.** Generate *B* designs, fold all *B*, take the best.
- **Filtered.** Generate *kB* designs for *k* > 1, apply a zero-cost sequence filter to
  keep the best *B*, fold those *B*, take the best.

Both spend exactly *B* folds. The filter is worth having if and only if the second
strategy's winner is better. That framing matters because it immediately rules out the
comparison people reach for first — filtered pool versus unfiltered pool of *different*
sizes — which conflates the filter's effect with simply having folded more things.

There is a subtler trap underneath, and it is the one this session was really about.

### 1.1 Why "we kept the best design" proves nothing

Suppose a pool of *n* = 40 designs and a filter that retains half. Ask: did the filter keep
the pool's best design? If yes, that feels like evidence the filter works.

It is not. A **random** subset of size *n*/2 contains the pool maximum with probability
exactly 1/2, by symmetry — every design is equally likely to be drawn. More generally a
random subset retaining fraction *f* keeps the maximum with probability *f*, and keeps at
least one of the top *m* designs with probability 1 − (1−*f*)^*m* approximately, which for
*f* = 0.5 and *m* = 5 is **97%**. Random pruning almost always retains *some* excellent
design. "Our filter kept a good one" is therefore a claim with an enormous null.

The correct null model is a **random subset of the same size**, and it costs nothing: draw
*B* random subsets from a pool you have already folded, compute the statistic of interest
on each, and see where the filtered subset falls in that distribution. This is a
permutation test, and its logic is the same as any other — the filter must beat the thing
that would happen if the filter carried no information at all.

### 1.2 The result

20,000 random subsets per retention level, statistic computed on three-seed mean DockQ:

| keep | statistic | filtered | random mean | P(random ≥ filtered) |
|---|---|---|---|---|
| 40% (n=16) | **max** DockQ | 0.7467 | 0.7426 | **0.399** |
| 40% (n=16) | mean DockQ | 0.7163 | 0.7027 | **0.022** |
| 50% (n=20) | **max** DockQ | 0.7467 | 0.7435 | **0.499** |
| 50% (n=20) | mean DockQ | 0.7142 | 0.7026 | **0.017** |
| 60% (n=24) | **max** DockQ | 0.7467 | 0.7443 | **0.600** |
| 60% (n=24) | mean DockQ | 0.7110 | 0.7026 | **0.034** |

**The aromatic filter does not improve the maximum.** At every retention level, p ≈ 0.4–0.6
— precisely chance. It retains the pool's best design, but so does random pruning often
enough that retaining it is uninformative. The p-values rising monotonically with retention
(0.40 → 0.50 → 0.60) is the signature of pure chance: keep more, keep the max more often.

**It does improve the mean**, at p = 0.017–0.034, by **+0.0137 DockQ** at 40% retention.
For scale, the seed-to-seed standard deviation of DockQ on one design is **0.018**. So the
filter shifts typical quality by roughly one standard deviation of measurement noise — real,
modest, and worth having when the thing you care about is how many survivors reach a
shortlist.

The proposed Gate 3 read: *"the aromatic filter reaches equal-or-better **top-end** quality
using materially fewer folds."* That criterion is aimed at the one quantity the filter
demonstrably does not move, and worse, it would be **passed** by a filter that does nothing,
because equal-or-better maxima are what random pruning delivers half the time. A gate that a
coin passes is the same failure as the gate it was written to replace.

---

## 2. The feature is a step function, and "fraction" was a misnomer

Every design in this pool has a **13-residue CDR-H3**, because ProteinMPNN redesigns onto a
fixed backbone and cannot change loop length (§4). Aromatic *fraction* over a 13-residue
window is therefore *count* / 13 — a four-valued ordinal variable, not a continuous one. The
reported ρ = −0.536 is a rank correlation over four levels:

| aromatics in CDR-H3 | n | mean 3-seed DockQ | sd | max |
|---|---|---|---|---|
| 1 | 9 | **0.7326** | 0.0069 | 0.7417 |
| 2 | 17 | **0.7016** | 0.0356 | 0.7467 |
| 3 | 13 | **0.6889** | 0.0316 | 0.7307 |
| 4 | 1 | **0.6277** | — | 0.6277 |

Kruskal–Wallis over the three populated levels: H = 10.66, **p = 0.0048**.

**Leverage first,** because this project has already been burned by an R² carried entirely
by two anchor designs. The top level holds a single design at the bottom of the DockQ range —
exactly the shape of a correlation propped up by one point. Dropping it: ρ = −0.536 →
**−0.497**, p = 0.0013, n = 39. The effect survives. That is worth stating explicitly rather
than assuming.

But the *shape* is not a gradient. Designs with ≤1 aromatic average 0.7326 with **sd
0.0069**; designs with ≥2 average 0.6939 with **sd 0.0356**. The low-aromatic group is
**5.1× tighter**. It is not that low-aromatic designs are better on average — it is that
they contain no failures. The aromatic count is behaving as a *risk* variable, not a quality
variable, which is a different thing to select on and argues for an absolute cutoff rather
than a ranking.

Two consequences for the campaign:

1. **Only 9/40 (22%) of the pool clears count ≤ 1.** A rule phrased as "keep the least
   aromatic 40%" necessarily admits most of the count-2 tier and dilutes the effect it is
   selecting on.
2. **A percentile rule over a 4-valued feature is not well defined.** Seventeen designs
   share count 2; keeping 16 of 40 requires splitting that tier arbitrarily, and the number
   you report depends on your sort's tie-breaking. (This is why the +0.0137 above differs
   from a +0.017 computed with a different tie-break — same rule, same data, different
   answer, which is the definition of an ill-posed rule.)
3. **A percentile is not portable across generation regimes.** The plan's primary arm varies
   MPNN temperature specifically to see whether the aromatic relationship holds at other
   operating points. Higher temperature produces more divergent loops and a different
   aromatic distribution, so the same percentile maps to a *different absolute threshold* in
   every arm — which confounds the arm comparison with the filter definition. The filter must
   be an **absolute count** (≤1 aromatic per 13-residue CDR-H3), and the *survival rate* per
   arm becomes a reported result rather than a fixed constant.

---

## 3. The reliability of the key we actually rank on

`config/metrics.yaml` sets `selection_key: final` — the banded rubric composite, resolved on
2026-09-17 because the rubric prices one novelty band step at 14.0 points against DockQ's 7.0,
so ranking on DockQ would promote near-copies of pembrolizumab. That decision stands.

The multi-seeding in the M3 plan is justified by a **reliability of 0.727**. That number is
DockQ's. Nobody had measured `final`'s — and they are not the same number, for a reason that
is structural rather than incidental.

### 3.1 Why banding destroys reliability

Reliability here is the standard psychometric ratio: the fraction of observed variance that
is true between-design variance rather than measurement noise,

```
reliability = σ²_between / (σ²_between + σ²_noise)
```

and for a mean of *k* seeds the noise term becomes σ²_noise / *k*.

A **banded** metric maps a continuous measurement onto a step function — sub-score 10 if
ipSAE ≥ 0.80, 5 if ≥ 0.60, and so on. Steps have a pathological noise property: a design
whose true value sits far from an edge is perfectly reproducible, while a design sitting *on*
an edge flips band on arbitrarily small noise. The noise is not attenuated by banding, it is
**concentrated** into the designs near edges, and it arrives as a full band step — 2.5 points
of `final` — rather than as a small continuous wobble.

### 3.2 Measured

| quantity | value |
|---|---|
| designs whose single-seed `final` changes across 3 seeds | **22/40 (55%)** |
| within-design sd of single-seed `final` | 0.873 points |
| between-design sd of 3-seed mean `final` | 1.486 points |
| **single-seed reliability of `final`** | **0.602** |
| **3-seed-mean reliability of `final`** | **0.780** |
| distinct values of `final` across 40 designs | **{82.5, 85.0, 87.5}** |

**More than half the pool changes its rubric score depending on which Boltz seed folded it.**
The sub-scores doing the flipping are **ipSAE (16 designs)** and **ΔG (17 designs)**, both
sitting near a band edge across this pool. Single-seed reliability of the selection key is
**0.602**, materially worse than the 0.727 the plan reasons from; even the three-seed mean
reaches only **0.780**.

And the resolution problem is worse than the noise problem: `final` takes **three distinct
values across forty designs**. Scaling generation to 200 does not add resolution, because
banding is what removed it. A wide campaign ranked on `final` produces a top tier of perhaps
sixty tied designs, broken by DockQ at reliability 0.727 over a total range of 0.119 — which
is a procedure for selecting noise, dressed as a ranking.

### 3.3 What to do instead

The organisers recompute `final` deterministically from the files we hand over, so `final`
remains the **reported** score and nothing about the rubric changes. But our *internal choice*
among candidates should not throw away within-band information. Two changes:

- **Rank on a continuous surrogate** — the weighted sum of raw metrics normalised within their
  bands — and report `final`. This preserves the rubric's relative pricing (novelty 2× DockQ)
  while restoring resolution.
- **Break ties by distance from a band edge.** A design whose ipSAE sits mid-band is worth
  more than one 0.002 from the edge, because the organisers' recomputation of *our* file is
  deterministic but our *choice* was made on a noisy fold. The project already holds exactly
  this idea as `margin_fraction: 0.20` for gates; band edges deserve the same treatment, and
  the 55% flip rate is the evidence that they need it.

---

## 4. The exploratory arm needs a generator the project does not have

The plan's second arm varies CDR-H3 length, correctly reasoning that length is the main
driver of loop flexibility and that the aromatic result was measured with length held still.

**ProteinMPNN cannot do this.** It is a *fixed-backbone* method: it samples a sequence
conditioned on a given set of backbone coordinates, one residue per position. There is no
mechanism by which it emits a loop of a different length, and `src/locksmith/design/mpnn.py`
asserts as much at line 139 —

```python
if len(h) != len(heavy):
    raise RuntimeError(f"MPNN returned a heavy chain of {len(h)} aa, expected {len(heavy)}")
```

Varying loop length requires *generating new backbone geometry*, which means RFdiffusion or
RFantibody. PLAN.md §2 lists both as reachable and Docker as available, but neither has been
installed, run, or validated in this project. So the length arm is not an arm — it is an
uncosted new milestone with its own install risk, its own smoke test, its own failure modes,
and no measured fold rate. Folding it into an overnight run alongside the primary arm is how
an overnight run produces nothing by morning.

This does not kill the idea; the reasoning behind it is right, and testing the stated
boundary of the aromatic result is genuinely valuable. It belongs in its own milestone with
its own install-and-qualify step, in the same shape as M1 did for Boltz.

---

## 5. The revised campaign

### 5.1 Fold everything in the primary arm; evaluate the filter offline

The plan's reject-sampling instruction exists to avoid circularity: fold only survivors and
you can never know what you discarded. Correct diagnosis. But the machine is free overnight
and the fold count is not the binding constraint — which means the stronger design is
available: **fold the entire primary arm unfiltered at one seed**, then evaluate every
filter, threshold and null model *retrospectively* on complete data.

This is strictly better than a reject sample, for three reasons. It is the exact
counterfactual rather than an estimate with sampling error. It permits the random-subset null
of §1 to be run at every retention level rather than one. And it lets the filter's threshold
be chosen *after* seeing the data without contaminating anything, because the threshold's
value is then reported as a fit to this arm, honestly, rather than smuggled in as a
pre-registered constant it never was.

The cost of completeness is roughly 30 extra folds over the filtered plan. At 47 s per
batched fold that is **23 minutes**.

### 5.2 Sizing

> **WITHDRAWN 2026-09-19 by the run itself.** The paragraph below claimed the 85 s/fold
> figure was a 1.65× sizing error. It was not. The completed arm folded **239/239 in 6.0 h,
> median 84 s** — the original figure was right, and right for the stated reason: it was the
> **quiet-machine** rate, and the machine was genuinely quiet overnight. The 133–150 s medians
> I compared against came from *contended* runs, and the 141 s I measured live came from the
> first four folds while I was still running commands on the box. I relabelled a contention
> effect as a sizing error, on a sample of four, against a correctly-labelled prior estimate.
> **The lesson is the one already in LEARNINGS about measuring load before assuming
> contention — applied here in reverse, and got wrong.** The corrected budget table below is
> therefore pessimistic by ~1.65×; the ~9.3 h estimate was really ~6 h. Kept rather than
> deleted because the reasoning trail is the point.

**~~The 85 s/fold this project has been sizing on is wrong, and was wrong before tonight.~~**
It is the *minimum* of 120 historical folds quoted as if it were typical. The actual
distribution, over every Fab fold on disk:

| run | n | min | median | mean | p90 | max |
|---|---|---|---|---|---|---|
| `designs_wide` | 84 | 84 s | **133 s** | 121 s | 155 s | 164 s |
| `designs_baseline` | 20 | 141 s | **150 s** | 151 s | 160 s | 172 s |
| `designs_reseed` | 16 | 136 s | **145 s** | 147 s | 156 s | 172 s |

So the planning rate is **~140 s/fold**, not 85 — a **1.65× sizing error** carried in every
budget table this project has written. Corrected below. (The first fold of a cold run costs
more still: 299 s, which is model load and kernel warm-up, amortised across the run.)

Using the corrected 140 s/fold, and the ~1.8× that batching is expected to buy (≈78 s/fold
batched):

| stage | folds | at 78 s (batched) | at 140 s (unbatched) |
|---|---|---|---|
| Primary arm, 239 designs × 4 temperatures, 1 seed, **unfiltered** | 239 | 5.2 h | **9.3 h** |
| Shortlist 30 → 3 seeds (2 more each) | 60 | 1.3 h | 2.3 h |
| Fresh-seed re-score: winner + 2 runners-up | 6 | 0.1 h | 0.2 h |
| **Total** | **305** | **6.6 h** | **11.8 h** |

The unbatched primary arm **does not fit a single night** — it is ~9.3 h against a ~7 h
window. This is fine and was made fine deliberately, by shuffling (§5.2a): the run is
resumable and any prefix is a balanced sample, so a night that ends early costs precision,
not the experiment. It is also the strongest argument yet for building fold batching, which
would bring the arm inside one night. ### 5.2a Shuffle the fold order, or a partial night is a biased pool

The pool is generated arm by arm, so the natural fold order completes T=0.1, then T=0.2, and
so on. Any run that does not reach the end then leaves the **high-temperature arm entirely
unfolded** — and the temperature comparison is the whole reason the arm exists. That is not a
smaller experiment, it is a different and useless one.

Shuffling the fold order with a fixed seed makes **any prefix of the run a balanced random
sample across all four arms**. Confirmed at launch: 59 / 59 / 60 / 60 remaining by
temperature. The seed is fixed so a restart continues the same sequence rather than
re-randomising into fresh bias, and the resume logic keys on completed folds, so the two
compose.

This is the same failure family as collecting all of class A before class B and letting
sensor drift correlate with the label — a **collection-order artefact masquerading as a
result**. It cost two minutes to fix because it was caught after one fold; caught at dawn it
would have cost the night.

Temperatures 0.1 / 0.2 / 0.3 / 0.5, 60 designs each — 0.1 anchors to the existing
pool so the two are poolable, and 0.5 is far enough out to genuinely stress the aromatic
relationship. The exploratory length arm is removed from this run per §4.

### 5.3 Gate 3, rewritten again

> **G3.** On a fully-folded primary arm, the aromatic filter (count ≤ 1 per 13-residue
> CDR-H3) beats a **random subset of identical size** on mean three-seed DockQ by ≥ 0.018
> (one seed sd), one-sided p < 0.05 over 10,000 resamples — *and* a named best design is
> delivered with fresh-seed re-score, shrinkage-corrected winner's-curse discount applied,
> and its CDR-H3 ensemble characterised.

Three deliberate choices. The comparison is against **random pruning at equal budget**, so
the gate cannot be passed by a filter that carries no information. The statistic is the
**mean**, because §1 shows that is the quantity the filter moves. And the margin is **one
seed standard deviation** — chosen because the discovery-set effect was +0.0137, *below*
that bar, so this is a genuinely two-sided test rather than a threshold reverse-engineered
to pass. If it fails, the honest report is "the filter raises pool quality by less than
measurement noise and does not earn a stage," which is a real finding about the cost of
cheap features.

The top-end claim is dropped from G3 entirely. It can still be *reported* — max DockQ per
arm, with its null — but it cannot be a gate, because no filter in this regime can move it.

### 5.4 Winner's curse, correctly scaled

The plan is right that a larger pool makes the correction **larger**. The earlier value
(−0.0079 DockQ at n = 8) was estimated by re-seeding and should not be reused at n = 180.
Selection takes the argmax over scores that are true value plus noise, so the winner is
disproportionately a design whose noise was positive. The clean estimator is
empirical-Bayes shrinkage of the winner's deviation from the pool mean by the measured
reliability:

```
corrected = pool_mean + reliability × (observed − pool_mean)
```

With the three-seed-mean reliability of `final` measured at **0.780**, a winner scoring 2.0
points above the pool mean should be reported at **1.56 points above** — a discount of
**0.44 points**, five times the n = 8 estimate. Report both numbers and the estimator.

---

## 6. A second free feature — and why it should *not* be used

The original pre-registration tested six pre-fold features and found one. It did not test the
rubric metric already computed before folding: **CDR-H3 identity to the parent**.

| relationship | Spearman | p |
|---|---|---|
| aromatic count → DockQ | −0.536 | 0.0004 |
| **CDR-H3 identity → DockQ** | **+0.505** | **0.0009** |
| aromatic count → CDR-H3 identity | +0.085 | 0.601 |
| partial: aromatic → DockQ, controlling identity | **−0.674** | <0.0001 |
| partial: identity → DockQ, controlling aromatic | **+0.655** | <0.0001 |

The two features are **uncorrelated** and each *strengthens* when the other is controlled —
textbook mutual suppression, where each feature explains variance that was obscuring the
other. A combined rank score reaches **ρ = +0.781** against three-seed mean DockQ, far above
either alone, and at 40% retention keeps 5/5 of the top five designs where aromatic-only
keeps 4/5.

**And it must not be used.** CDR-H3 identity *is* the novelty axis, priced at 2× a binding
metric, and it runs the wrong way: higher identity predicts better DockQ and scores *worse*
on novelty. A filter selecting high identity buys binding with the most expensive points on
the rubric. In this particular pool the trade is invisible — identity → `final` is ρ = +0.035
(p = 0.83), because all three distinct identity values (23.1 / 30.8 / 38.5%) fall inside one
novelty band — but that is an accident of a pool with no novelty diversity, and it will not
survive a temperature sweep whose entire purpose is to create that diversity.

Aromatic count, by contrast, predicts `final` at **ρ = −0.557 (p = 0.0002)** — *better* than
it predicts DockQ. **Aromatic content is the thing to filter on; identity is a thing to hold
constant**, recorded as a covariate and checked for drift across arms.

---

## 7. What the pool fundamentally cannot say

| dimension | distinct values across 40 designs |
|---|---|
| CDR-H3 length | 13 |
| MPNN temperature | 0.1 |
| CDR-H3 identity | 23.1, 30.8, 38.5 % |
| aromatic count | 1, 2, 3, 4 |
| `final` | 82.5, 85.0, 87.5 |

Forty designs spanning four aromatic levels × three identity levels × one length × one
temperature. This is a **densely sampled single operating point**, not a design space, and
every conclusion in this document — including the aromatic effect itself — is conditional on
that point. The instinct behind the original plan's "wide and varied, not wide and uniform"
is exactly right and is the most valuable part of it.

---

## 8. Transferable principles

- **A selection rule must be tested against the null of selecting at random with the same
  budget.** Filtered-versus-unfiltered conflates the rule with the sample size; only an
  equal-size random subset isolates the information the rule carries. It costs nothing when
  the pool is already evaluated — 20,000 resamples ran in under a second here.
- **Measure the reliability of the quantity you actually rank on.** Reliability was known for
  DockQ (0.727) and reasoned about for a year of sessions, while the configured
  `selection_key` was `final`, whose single-seed reliability is **0.602** and which flips on
  55% of designs. A correlate's reliability is not the key's.
- **Discretising a metric does not average noise away, it concentrates it at the edges.**
  Banding moved ipSAE and ΔG noise from small continuous wobble into 2.5-point step changes
  on designs near an edge — 16 of 40 on ipSAE, 17 on ΔG — while simultaneously collapsing all
  40 designs onto three distinct scores.
- **A percentile threshold over a low-cardinality feature is an ill-posed rule** — it cannot
  be applied without arbitrary tie-breaking, and it silently changes meaning whenever the
  generating distribution changes, which is fatal if the experiment's purpose is to vary the
  generator.
- **Before adding an arm, check the tool can produce the variation the arm requires.**
  Varying CDR-H3 length is one sentence in a plan and a whole new generator in the code.
- **When a free feature predicts well, check what it costs on the other axes before adopting
  it.** CDR-H3 identity is the best available free predictor of DockQ and is disqualified
  precisely because it is also a scored metric running the opposite way.

## 9. State

**Ran.** No folds. `scripts/27_review_m3_assumptions.py`,
[[m3_plan_review|results/m3_plan_review.md]].

**Launched 2026-09-19 01:04.** M3's primary arm is running unattended:
`scripts/28_generate_temp_arm.py` (done — 239 unique designs over T = 0.1/0.2/0.3/0.5),
then `scripts/29_fold_temp_arm.py` → `scripts/30_score_temp_arm.py` chained by
`scripts/run_m3_overnight.sh`, detached under
`nohup setsid systemd-inhibit --what=sleep:idle:handle-lid-switch`. Log:
`runs/m3_overnight.log`. Both stages resumable; a kill costs at most the unit in flight.

**Generation yield.** 240 requested, **239 unique** (1 duplicate at T=0.2, 0 rejected).
Diversity is better than the old pool but not transformed: CDR-H3 identity now spans
**15.4–46.2%** with 4–5 distinct values per arm, against 23.1–38.5% and 3 values before.
Aromatic count now spans **0–4** where the old pool spanned 1–4. **45/239 (19%)** clear the
pre-registered filter (count ≤ 1), close to the 22% seen in the discovery pool — so the
filter's retention rate is roughly temperature-invariant, which is mildly reassuring for
the absolute-threshold choice made in §2.

**Deliberately NOT done tonight: fold batching.** It was to be built first, and the reasoning
for that still holds (~1.8×, pays for itself on this run). But building new fold-path code and
putting it on the critical path of a 6-hour unattended run is how a night produces nothing.
The unbatched run fits the window — 239 folds at the measured 85 s quiet ≈ 5.6 h — and the
existing driver has 124 folds and zero failures behind it. Batching gets built with someone
watching, and M5's dossier folds inherit it.

**Open.** Stage 3 (shortlist → 3-seed → winner) is deliberately left for the morning: it needs
the continuous-surrogate ranking of §3.3 written and checked, which should not be authored
untested at 1 a.m. and run unattended. By then the 239 folds and their scores exist, so it is
~60 folds ≈ 1.4 h.

**Also open.** `runs/` is not in the vault's `/.stignore`, so ~645 MB of new fold output will
sync to the phone relay — which is the whole vault's storage ceiling and has blocked Windows
sync once before at 6.05 GB. Not a problem at this size, and `.stignore` sits at the vault root
outside the write zone, so it is flagged rather than changed.

**Previously open.** M3 was not started. The revised design in §5 is a proposal awaiting a decision on
the length arm (defer to its own milestone, per §4) and on continuous-surrogate ranking
(§3.3). Fold batching still outstanding and still worth doing first, with the acceptance test
loosened — see below.

**One correction to the plan's batching instruction.** "Verify it reproduces a known fold
byte-identically, then switch" is the right instinct but the wrong bar for batch sizes above
one: cuDNN and cuBLAS select different kernels by batch shape, so floating-point results can
differ in the last bits even with an identical seed, and a byte-identity requirement would
report a working implementation as broken. Use a two-tier test — **byte-identity at batch
size 1**, which genuinely proves the refactor did not change the code path, and **statistical
equivalence at batch size > 1**, requiring DockQ within 3 seed sd (±0.054) of the known
value. The rest of the instruction — build alongside the live driver, never edit a script a
running job shells out to — stands, and the second half is already a LEARNINGS entry earned
the hard way.
