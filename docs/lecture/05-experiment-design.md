---
date: 2026-09-23
tags: [project, lecture, learning, statistics, pattern]
status: review
---

# 05 — Experiment Design

**What this chapter teaches.** One question, asked relentlessly: *what would have to be true for me
to be wrong?* An experiment that cannot answer that is not an experiment, it is a demonstration. We
build the machinery for asking it — sampling error and the detectable-effect standard for nulls, the
partial correlation for adjudicating between two competing explanations, the taxonomy of controls
(positive, negative, matched), and the art of constructing a **null that matches the geometry of the
alternative** rather than merely its size. Then two moves that are rarer and more powerful than any
of those: **equal-budget resampling**, which asks whether your clever rule beats the same rule
applied at random, and **varying the outcome rather than the test**, which is how this campaign
refuted one of its own headline findings after it had survived a perfectly good null.

We close on the two integrity mechanisms: optional stopping, and pre-registration. The campaign
committed the first and used the second, and the most interesting thing it did with
pre-registration was document the contamination of its own.

This chapter consumes the [reliability](04-measurement-theory.md#13-reliability) numbers built in
[the measurement-theory chapter](04-measurement-theory.md) and feeds
[the allocation chapter](06-allocation-and-selection.md), which asks where the *next* measurement
should go once you know how noisy the current one is. Failures referenced here are catalogued in
full in [the failure catalogue](08-what-broke.md); terms are in [the glossary](10-glossary.md).

---

## 1. Sampling error, and the detectable-effect standard

### 1.1 The Fisher-z machinery

Correlations are awkward to reason about because their sampling distribution is skewed and bounded:
a sample ρ near 1 cannot wander far upward. Fisher's transform fixes this. For a correlation ρ,

```
z  =  artanh(ρ)  =  ½ ln((1 + ρ)/(1 − ρ))                                    (5.1)
```

is approximately normally distributed with a standard error that **does not depend on ρ at all**:

```
SE(z)  =  1 / √(n − 3)                                                       (5.2)
```

*n* is the number of independent items, dimensionless; `z` is dimensionless. A 95% confidence
interval for ρ is `tanh(z ± 1.96·SE)`, which is asymmetric on the ρ scale — correctly so.

Now invert it for power. To detect a true effect `ρ_true` at 80% power with a two-sided α = 0.05
test, the true `z` must exceed the sum of the critical value and the power quantile, both in SE
units: `z_detect = (1.96 + 0.84)/√(n−3) = 2.80/√(n−3)`, hence

```
ρ_detect  =  tanh( 2.80 / √(n − 3) )                                         (5.3)
```

This is the single most useful formula in the chapter and it takes ten seconds to evaluate. The
campaign states it verbatim at `results/ensemble_power.md` §Allocation.

### 1.2 Worked: why an n = 14 experiment cannot adjudicate a 0.6 gate

At n = 14, `SE(z) = 1/√11 = 0.3015`. That is enormous: a whole 0.30 in `z` units, which near ρ = 0.5
is roughly 0.23 in ρ units per standard error. The campaign wrote it down:
*"At n=14, SE in Fisher-z is 1/√(n−3) = 0.30, so **no n=14 experiment can** adjudicate a 0.6 gate"*
(`docs/sessions/2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test.md:222`).

The companion measurement makes it concrete. The restricted-range Fv-vs-Fab correlation was
**ρ = +0.469** with a 95% CI of **[−0.14, +0.82]** (`results/panel_g1c_g1d.md` §2, a bootstrap
interval at n = 12 for that restricted set). Reconstruct it analytically: `artanh(0.469) = 0.5087`,
`1.96/√9 = 0.6533`, so the interval is `tanh(0.5087 ± 0.6533) = [−0.144, +0.822]`. The bootstrap and
the Fisher-z interval agree, which means the conclusion does not depend on which interval you build.

An interval spanning −0.14 to +0.82 contains "strong negative association", "nothing at all", and
"almost perfect agreement". The correct disposition of the gate was therefore **not answerable at
that n** — not a pass, not a fail on the point estimate. That is a disposition most people never
write down, and it is the honest one.

### 1.3 The standard, stated

> **"A null is only meaningful as 'no effect larger than x'. State the detectable effect at the n you
> actually have, or do not report the null."**
> (`docs/sessions/2026-09-20-auditing-the-judge-reliability-is-not-validity.md` §2.2, verbatim.)

Everything in §2 is what happens when you do not. Everything below is what it looks like when you
do — the campaign applied it, pre-registered, in at least four places:

- `results/ensemble_wide.md` §2: *"At n=239 and [attenuation](04-measurement-theory.md#4-attenuation-why-correlations-between-noisy-things-look-weak) 0.828, the smallest true effect detectable
  at 80% power (α=0.05) is ρ_true ≈ **0.218**."* Check it: `2.80/√236 = 0.1823`, `tanh(0.1823) =
  0.1803` on the observed scale, and dividing by the attenuation ceiling 0.828 (see
  [the attenuation formula](04-measurement-theory.md)) gives `0.1803/0.828 = 0.2178`.
- `results/skempi_validity.md`: *"At n=45 the smallest effect detectable at 80% power (α=0.05) is
  ρ ≈ **0.41**."* Check: `tanh(2.80/√42) = tanh(0.4320) = 0.4072`.
- `results/calibration.md`: *"At n=20 per arm Mann–Whitney has roughly 80% power for a rank-biserial
  around 0.6, so **a non-significant row here means 'no effect larger than large', not 'no
  effect'**."*
- `results/prereg_2026-09-20_ensemble_wide.md` §3 — the bound written *before* the data existed,
  which is the only version that cannot be reverse-engineered to flatter the result.

A related discipline, and a cheap one: **compute the smallest p your design can produce before you
read its output.** With 3 versus 3 observations a two-sided Mann–Whitney test has exactly
`C(6,3) = 20` equally likely rank assignments, so the most extreme gives one-tailed 1/20 = 0.05 and
two-tailed **0.100** — and 0.100 is precisely what the cross-reactivity experiment measured
(`results/audit_2026-09-20.md` Check D). *The test was at its ceiling before it began.* At 8 versus 8
the floor is `2/C(16,8) = 2/12870 = 1.554e−4`, which is room to breathe; re-run at n = 8 the same
comparison gave p = 0.038.

---

## 2. The four reversals, and why they are one error

By its own reckoning this is the campaign's most repeated mistake:
*"**All four are the same error: a small-sample null read as evidence of absence**"*.

| # | claim as published | as measured | later measurement | status |
|---|---|---|---|---|
| 1 | "mean loop pLDDT is **blind** to CDR-H3 heterogeneity" | ρ **−0.168**, p **0.69**, **n = 8** (`results/reseed_ensemble.md` §5.3) | ρ **−0.432**, p **2.9e−12**, **n = 239** (`results/ensemble_wide.md` §2) | **REVERSED** |
| 2 | "the ensemble carries no information the sequence didn't" | partial **−0.081**, p **0.62**, **n = 40** (`results/ensemble_validation.md` §6) | **−0.289**, p **5.7e−06**, n = 239; **−0.303** on the same arm at n = 60 (`results/audit_2026-09-20.md` Check B) | **WITHDRAWN** |
| 3 | "three seeds is the worst allocation at every budget tested" | — | refuted by the table printed directly above it | **CORRECTED** |
| 4 | "winner's-curse shrinkage validated to 0.001" | — | one fold, sd 0.467 | **CORRECTED** |

Items 3 and 4 are not literally nulls — they are a misread table and a single confirming
measurement mistaken for a validation, and both are dissected in
[the allocation chapter](06-allocation-and-selection.md). But they belong in the same family, because
all four share one structure: **a quantity that could not have been resolved at the sample size
available was read as though it had been resolved.**

Take #1 apart with (5.3). At n = 8, `SE(z) = 1/√5 = 0.447`, so a 95% CI is `±0.877` in z units — the
interval on ρ is roughly ±0.7 wide, covering nearly the entire admissible range. The smallest
detectable effect at 80% power is `tanh(2.80/√5) = tanh(1.252) = 0.849`. **An n = 8 experiment could
only have detected a correlation above 0.85.** The measured −0.168 is therefore perfectly consistent
with the true −0.432 that 239 designs later revealed; the two are statistically indistinguishable.
Nothing surprising happened. What happened is that a number inside a ±0.7 interval was written into
a rules file as a finding.

The second-order correction on #1 is the most instructive thing in the whole record, and it runs in
both directions. A morning audit (`results/audit_2026-09-20.md` Check A) observed that the −0.432 was
**inflated by construction**, because the pLDDT value and the k = 2 spread share the seed-1
structure; it re-ran on disjoint data (pLDDT from seed 1, spread from seeds 2 and 3, n = 84) and got
**−0.233 (p = 0.033)**, against −0.351 for those same 84 designs sharing seed 1. It concluded the
circularity inflated things "by roughly a third". **Then that correction was itself corrected:**
*"my own correction over-shot too: I said the circularity inflation was 'roughly a third' by
comparing a 1-pair estimate to a 3-pair one without disattenuating both. Done properly it is about
**13%**, and the honest value is ρ ≈ −0.28 to −0.32."* A further mechanical deflation is recorded
separately: spread correlates with mean deviation-from-crystal at **+0.589**, and partialling that
out collapses the spread→[DockQ](03-the-toolchain.md#41-dockq-213-two-flags-that-both-default-wrong) link to **−0.167**.

Three passes, three different answers, converging. That is what a working correction process looks
like — and note that the *second* pass erred in the opposite direction from the first, which is
mildly reassuring: the process is not simply regressing toward whatever the author wants.

> **Transferable principle.** *A null is a bound, and the bound is part of the result. Reporting
> "p = 0.69" without "at n = 8, where the 95% CI is ±0.7 wide and only ρ > 0.85 was detectable" is
> reporting nothing at all — and worse than nothing, because it looks like something.*

---

## 3. Partial correlation, and a result that half-reversed

### 3.1 The formula

Given variables X and Y and a control Z, the partial correlation of X and Y holding Z fixed is

```
ρ_{XY·Z}  =  (ρ_XY − ρ_XZ·ρ_YZ) / √((1 − ρ_XZ²)(1 − ρ_YZ²))                  (5.4)
```

Derivation in one line: regress X on Z and Y on Z, then correlate the residuals; (5.4) is that
correlation written out. Dimensionless, in [−1, 1].

One caveat the project never states and which matters for teaching: applied to **Spearman** (rank)
coefficients, as it is here, (5.4) is a first-order Gaussian-copula approximation rather than an
exact nonparametric quantity. It is standard practice and it is fine for adjudication, but it is not
"the rank partial correlation" in any exact sense.

### 3.2 The adjudication: does an expensive measurement add anything to a free one?

The question was economically serious. To measure a design's **ensemble spread** you must fold it
three times on a GPU (three folds per design). To compute its **CDR-H3 aromatic fraction** you count
aromatic residues in a string (zero folds). Both predicted design quality. Was the expensive one
redundant?

From `results/ensemble_validation.md` §6 — 40 designs, CDR-H3 length held constant at 13 across all
of them:

| relationship | Spearman | p |
|---|---|---|
| aromatic fraction → CDR-H3 ensemble RMSD | **+0.621** | 0.00002 |
| aromatic fraction → 3-seed mean DockQ | **−0.536** | 0.00036 |
| ensemble RMSD → 3-seed mean DockQ | −0.387 | 0.014 |
| **partial: ensemble → DockQ, controlling aromatics** | **−0.081** | **0.621** |
| **partial: aromatics → DockQ, controlling ensemble** | **−0.410** | 0.0086 |

Verify both partials with (5.4):

```
ensemble → DockQ | aromatics:
  (−0.387 − 0.621 × (−0.536)) / √((1 − 0.621²)(1 − 0.536²))
  = (−0.0541) / √(0.6144 × 0.7127)  =  −0.0541 / 0.6617  =  −0.0818   ✓

aromatics → DockQ | ensemble:
  (−0.536 − 0.621 × (−0.387)) / √((1 − 0.621²)(1 − 0.387²))
  = (−0.2957) / √(0.6144 × 0.8502) =  −0.2957 / 0.7228  =  −0.4091   ✓
```

The arithmetic is sound. The **ensemble axis was dropped from selection** on the strength of it: the
free feature out-predicts the expensive one *and* explains it away.

### 3.3 The half-reversal

Re-run on independent data (`results/audit_2026-09-20.md` Check B):

| quantity | 2026-09-18 (n=40) | T = 0.1 arm (n=60) | all designs (n=239) |
|---|---|---|---|
| aromatics → DockQ, raw | −0.536 | **−0.535** | — |
| aromatics → DockQ, controlling spread | −0.410 | **−0.408** | **−0.381** (p = 1.2e−09) |
| aromatics → spread, raw | +0.621 | +0.455 | +0.197 |
| **spread → DockQ, controlling aromatics** | **−0.081 (p = 0.62)** | **−0.303** | **−0.289 (p = 5.7e−06)** |

Read those two blocks against each other. **The aromatic half replicated to within 0.002 on an
independent sample** — as clean an out-of-sample confirmation as the project produced. **The
exclusion half did not.** The verdict is flat: *"The ensemble axis does carry independent signal.
That conclusion is withdrawn."*

Apply §1's arithmetic to see why this was foreseeable. At n = 40 a partial with one control has
roughly `SE(z) = 1/√(40−4) = 0.167`, so a 95% CI is about ±0.33 in z — the observed −0.081 carried an
interval of roughly [−0.40, +0.25]. It never excluded −0.289.

The same audit also catches a *mis-statement of its own reversal*: a morning summary wrote "the
aromatic-fraction result reverses", which was wrong, because the overnight partials used **spread**
as the outcome while the original used **DockQ**. *"Different outcome variable, so they were never
comparable."* Hold that thought: it is the seed of §6.

> **Transferable principle.** *A partial correlation near zero at n = 40 is not evidence of
> redundancy; its CI spans roughly ±0.3. "X explains away Y" needs exactly the same power standard as
> "X predicts Y" — and it almost never gets it, because an explaining-away claim feels like a tidy-up
> rather than a finding.*

---

## 4. Controls: positive, negative, matched

A **positive control** is an input known to produce the effect; if your assay does not see it, the
assay is broken. A **negative control** is an input known *not* to produce the effect; if your assay
sees it anyway, the assay has a false-positive rate you did not know about. A **matched control** is
the same intervention applied where it should have no effect, holding everything else — size,
procedure, cost — constant.

### 4.1 The epitope knockout: a matched control plus a dose–response

This is the strongest single experiment in the campaign (`results/validity.md` §1). The antigen PD-1
is held fixed except that its binding face is progressively destroyed by mutating contact residues to
alanine. The matched control, `ctrl6`, places the **same number of alanines on non-contacting
surface**. Every mutant antigen gets a **fresh multiple-sequence alignment**, because reusing the
wild-type alignment would leak the native residues back in through the alignment and quietly undo the
mutation.

| arm | antigen contacts removed | ipSAE | ΔG (kcal/mol) | contacts | interface pLDDT |
|---|---|---|---|---|---|
| `wt` | 0 | 0.869 ± 0.014 | −12.9 | 99 | 89.9 |
| `ctrl6` | 0 | 0.823 ± 0.026 | −13.0 | 97 | 89.1 |
| `ko6` | 349 | 0.720 ± 0.090 | −13.6 | 97 | 79.2 |
| `ko12` | 527 | 0.625 ± 0.091 | −12.5 | 94 | 71.0 |

The decision rule was fixed in advance and has **two bars**: an effect counts only if it clears
**3× the metric's own seed sd on this complex** *and* **3× the matched off-interface control**.
Results, with the arithmetic:

```
ipSAE           :  −0.245  =  17.1× seed sd  (control −0.046)   → sees it
interface pLDDT : −18.957  =  64.0× seed sd  (control −0.807)   → sees it
                   check: 18.957 / 0.296  =  64.04
PRODIGY ΔG      :  +0.333  =   0.9× seed sd                     → BLIND
                   check: 0.333 / 0.351   =  0.949
contacts        :  −4.667  =   1.2× seed sd                     → BLIND
                   check: 4.667 / 4.000   =  1.167
```

Two metrics fall **monotonically** with the number of epitope contacts removed (0 → 349 → 527) while
the matched control barely moves. That is a dose–response against a matched control, which is about
as close to a clean positive as this kind of experiment gets, and the monotonicity is doing real work:
a single knockout arm could be explained by any disruption, while a graded response is hard to fake.

And the sting. **[PRODIGY](03-the-toolchain.md#42-prodigy-240-δg-and-contacts) ΔG is blind — and it carries the largest single share of the ranking
variance.** The metric the selection leaned on hardest fails the specificity check outright.

### 4.2 The composition-matched scramble null

For each of 30 real designs, permute the **order** of its CDR-H3 residues. Length, composition,
aromatic count and net charge are all identical by construction — so every cheap sequence feature the
project used as a predictor is **held constant** and cannot explain a difference
(`results/negative_control.md` §2).

| | n | DockQ mean | sd | range |
|---|---|---|---|---|
| source designs | 30 | **0.706** | 0.040 | 0.624–0.766 |
| their scrambles | 30 | **0.565** | 0.153 | 0.037–0.708 |
| the full 239 pool | 239 | 0.706 | 0.039 | 0.596–0.777 |

Paired difference **+0.141**, median +0.118, **28 of 30 paired wins**, Wilcoxon **p = 2.4e−06**. A
crushing headline — and the file insists the *next* table matters more:

| | count |
|---|---|
| scrambles landing inside the pool's DockQ range (0.596–0.777) | **15/30 (50%)** |
| scrambles above the pool **median** | **0/30** |
| scrambles collapsing below 0.40 | 2/30 |

*"Half of all random permutations score like a real design, and none scores like a good one."* Both
halves are load-bearing. The second half is the strongest defence of the ranking apparatus any
experiment here produced: the pool's **upper** range is genuinely design-dependent. The first half is
the strongest indictment: **nothing below the pool median should be described as a design result at
all.**

> **Transferable principle.** *A paired null that holds every known confounder constant is the
> strongest cheap null available — and its informative content usually sits in the **overlap** of the
> two distributions, not in the p-value of the difference.*

### 4.3 The negative-control panel: what a known-wrong input does to your gates

Six antibodies with unrelated targets were docked onto the identical 113-residue PD-1 construct with
the identical cached alignment, and passed through the campaign's five hard viability cutoffs. The
result, run on day 9 of 9 (`results/negative_control.md`):

**HyHEL-10 — an anti-hen-egg-lysozyme antibody, which has no business binding a human immune
receptor — cleared all five cutoffs** on `model_0`: [ipSAE](03-the-toolchain.md#43-ipsae-interface-confidence-from-the-pae) **0.609**, ΔG **−12.4**, **77** contacts,
interface pLDDT **85.0**, CDR SASA **1084 Å²**. Its **median over five diffusion samples is ipSAE
0.219**, which tells you exactly what happened and is the subject of
[the order-statistics section of the next chapter](06-allocation-and-selection.md).

Across the panel, **four of the five hard cutoffs reject 0 of 6 known-wrong antibodies**: viability
rests on ipSAE alone, and ipSAE was itself read off a maximum. *"It costs eight folds and nobody ran
it for a week"* (`results/negative_control.md:9`).

The panel also demonstrates the second use of a negative control — as a **diagnostic instrument**.
Nivolumab, a licensed anti-PD-1 antibody that *should* pass, scored median ipSAE **0.017** (max
0.263). A pre-registered rule fired and the experiment was declared **INCONCLUSIVE** rather than
rescued. The diagnosis cost **zero GPU time**, from crystallography alone: the 113-residue PD-1
construct covers **24/24** of pembrolizumab's epitope but only **8/14** of nivolumab's, missing
`L25 D26 S27 P28 D29 R30` — **43% of nivolumab's binding site is not present in the molecule it was
docked against.** The construct had been inherited from a template on day 2 and never re-examined;
*"the only reference antibody ever folded was the one incapable of detecting the truncation."*

### 4.4 SKEMPI: the one comparison against a laboratory measurement

Everything above compares predictions to other predictions. `results/skempi_validity.md` compares
them to experiment: 45 single mutants of a crystallised antibody–antigen system with measured binding
free energies, where `ΔΔG = RT·ln(K_d,mut / K_d,wt)` and positive ΔΔG means the mutation **weakens**
binding — so a metric where higher is better should correlate **negatively**.

| metric | ρ (all 45) | p | ρ (\|ΔΔG\| ≤ 6, n = 27) | expected sign |
|---|---|---|---|---|
| PRODIGY ΔG | +0.221 | 0.14 | +0.050 | positive |
| ipSAE | +0.059 | 0.7 | **+0.300** | negative |
| DockQ | −0.101 | 0.51 | −0.198 | negative |
| interface pLDDT | +0.047 | 0.76 | **+0.275** | negative |
| contacts | −0.246 | 0.1 | −0.223 | negative |

The detectable bound is stated (ρ ≈ 0.41 at n = 45), and so is the essential companion check —
**a null is only informative if the metrics moved at all.** Between-mutant sd over seed sd: **2.5×**
for ΔG, **19.5×** for ipSAE, **13.0×** for DockQ, **82.9×** for interface pLDDT, 0.8× for contacts.
*"They are moving a great deal; they are simply not moving with the measured affinity."*

The individual cases are more persuasive than any correlation. Of five mutants that experimentally
abolish binding (ΔΔG > +20 kcal/mol), **four score essentially like the wild type**. `NL31A`, at
ΔΔG **+21.8 kcal/mol**, scores ipSAE **0.917 against the wild type's 0.903** — the pipeline rates a
non-binder *above* the real complex. Note that ipSAE and interface pLDDT, the two metrics that
**passed** the epitope-knockout control of §4.1, carry the **wrong sign** on the reliable subset.

The verdict bounds everything upstream of it: *"the pipeline can tell a destroyed interface from an
intact one, and cannot rank two intact ones by affinity. Every ranking claim in this project sits in
the second category."*

---

## 5. Null geometry: a null must match the shape of the alternative

### 5.1 The construction

Question: does the designed antibody bind the *functionally important* patch of the target — the face
that the natural ligand uses — or merely *some* patch of the target? The observable is
`frac_iface_on_epitope`, the fraction of the design's interface residues that fall on the intended
epitope.

The null is the hard part. For each of 18 backbones, recompute that fraction against **2000 random
contiguous surface patches of the same size (26 residues) drawn from the same chain**, and locate the
real value in that distribution (`results/challenge2_patch_null.md`, `scripts/70_epitope_patch_null.py`,
seed 20260922).

### 5.2 The numbers, and why one candidate null is a strawman

Pooled over 18 backbones:

| reference | `frac_iface_on_epitope` |
|---|---|
| **the real epitope** | **0.712** |
| contiguous-patch null | **0.154** |
| uniform-26-residue null | **0.231** |

and **17 of 18 backbones beat their own contiguous-patch null at p < 0.05** (the exception,
`bb_3_0.pdb`, at empirical p = 0.0785; nine backbones sit at 0.0005, the resolution floor of 2000
draws).

Now look hard at the uniform column. The target chain has 113 residues and the epitope is 26 of them:

```
26 / 113  =  0.2301
```

which is the uniform figure to three decimals. **The uniform null is the denominator, not a result.**
Scattering 26 residues at random over a surface produces an object no dock could ever land on, so the
expected overlap is simply the base rate, and beating it establishes nothing about the design. *"A
real dock lands on contiguous surface, so the null must too."* Matching the geometry moves the null
from 0.231 down to 0.154 — a null four and a half times below the observation instead of three.

> **Transferable principle.** *A null must match the **geometry** of the object it is a null for, not
> merely its size. A size-matched but shape-wrong null produces an expected value that is an artefact
> of the parameterisation, and "we beat the null" then means "we beat an arithmetic identity".*

### 5.3 The audit's own caveat: the null may be anti-conservative

This is the part most projects would omit. An audit of the test
(`results/audit_of_audit_2026-09-22.md` finding 3) measured the **compactness** of the drawn patches
against the real one:

| patch type | mean RMS spread |
|---|---|
| drawn contiguous patch | **7.73 Å** |
| the real PD-L1 footprint | **10.08 Å** |
| uniform draw | **13.21 Å** |

The drawn patches are **more compact than the thing they stand in for**. A more compact patch covers
less surface area and is therefore *easier for a spread-out interface to miss* — which plausibly
makes the test **anti-conservative by an unquantified amount**. The result stands (17/18, 0.712 vs
0.154), but the honest statement of the null is *"a compact 26-residue patch elsewhere on the same
chain"*, not *"an epitope-like patch elsewhere"*. Shape-matching the null is listed as blocked on
**nothing** — it is cheap, and it has not been done.

There is a second limit, also conceded: *"the epitope is also the largest contiguous patch the loops
could plausibly reach given where the generator was told to build, so a portion of this effect is
mechanical rather than evidential."* Both caveats are the right kind: they name a direction of bias
and decline to quantify it rather than pretending it is zero.

---

## 6. Equal-budget resampling, and varying the outcome

### 6.1 What a filter must actually beat

Suppose you invent a cheap rule that prunes a pool of *n* evaluated designs down to *fn*, and you
report that the survivors include the best design. How impressive is that?

By exchangeability, **a uniformly random subset retaining fraction *f* contains the pool maximum with
probability exactly *f***, and contains at least one of the top *m* with probability

```
P(top-m retained)  =  1 − C(n − m, fn)/C(n, fn)  ≈  1 − (1 − f)^m            (5.5)
```

At f = 0.5 and m = 5 that is `1 − 0.5⁵ = 0.96875`, about **97%**. So "our filter kept one of the top
five" is a claim a coin passes 97 times in 100. A gate worded around top-end quality *"would be
**passed** by a filter that does nothing"*.

The correct null is a **random subset of the same size** — an equal-budget permutation test whose
reference distribution costs nothing once the pool is already evaluated. The campaign's ran in under
a second on 20,000 resamples.

### 6.2 The measurements

Discovery set, n = 40, 20,000 random subsets per retention level, statistic on 3-seed mean DockQ:

| keep | statistic | filtered | random mean | P(random ≥ filtered) |
|---|---|---|---|---|
| 40% (n=16) | **max** | 0.7467 | 0.7426 | **0.399** |
| 40% (n=16) | mean | 0.7163 | 0.7027 | **0.022** |
| 50% (n=20) | **max** | 0.7467 | 0.7435 | **0.499** |
| 50% (n=20) | mean | 0.7142 | 0.7026 | **0.017** |
| 60% (n=24) | **max** | 0.7467 | 0.7443 | **0.600** |
| 60% (n=24) | mean | 0.7110 | 0.7026 | **0.034** |

Two readings. First, the filter genuinely moves the **mean** (+0.0137 DockQ at 40% retention, against
a one-seed DockQ sd of 0.018 — roughly one standard deviation of measurement noise; real, modest).
Second, and more instructive: *"the p-values rising monotonically with retention (0.40 → 0.50 → 0.60)
is the signature of pure chance: keep more, keep the max more often."* A statistic whose p-value
tracks your retention fraction is telling you it is reading the retention fraction.

On the confirmation set (239 designs, 10,000 subsets, filter keeping 45/239), the closed form and the
resampler agree beautifully: a random subset of 45 from 239 contains the maximum with probability
`45/239 = 0.18828` by construction, and the measured `P(random max ≥ filtered max) = 0.189`. That
agreement is itself a useful sanity check on the resampler.

*Decision:* the gate was **re-worded before it was run**, away from top-end quality and toward the
mean, because the mean was the only statistic the null could discriminate.

> **Transferable principle.** *A filter must beat the **same rule applied at random at equal budget**
> — never the unfiltered pool. And before you write the gate, check whether a coin would pass it.*

### 6.3 Varying the OUTCOME rather than the test

The filter survived that null, twice, on independent data. It also **contradicted a strong domain
prior**: it selects *against* large aromatic residues, which are the most robustly enriched residues
in real antibody binding sites. Something had to give.

The refutation is the most important methodological move in the campaign, and it is almost free.
Re-run **the filter's own equal-budget random-subset test, unchanged**, with each of the six scored
metrics in turn as the outcome (`results/g3_outcome_variable.md` §2;
`scripts/74_g3_outcome_variable.py`; n = 239, seed 20260922, 10,000 resamples, k = 45 of 239, **no new
compute**):

| outcome | filtered mean | random mean | margin | one-sided p |
|---|---|---|---|---|
| `dockq` | 0.7287 | 0.7050 | **+0.0237** | **0.0001** ✅ |
| `iface_plddt` | 91.5243 | 90.3994 | **+1.1248** | **0.0001** ✅ |
| `dg` | −12.3546 | −12.1961 | +0.1585 | 0.0641 |
| `ipsae` | 0.7981 | 0.7947 | +0.0034 | 0.2405 |
| `cdr_sasa` | 1519.0587 | 1519.8488 | −0.7901 | 0.5466 |
| `contacts` | 99.8159 | 101.6163 | **−1.8004** | **0.9884** |

**It wins on 2 of 6, and both winners are properties of the *predictor*, not of the interface.** DockQ
here is measured against the parent crystal, so it is *pose retention*; interface pLDDT is the
predictor's own confidence. Every quantity about the interface itself is null or against it. And
`contacts` **runs the wrong way**: filtered designs make **1.80 fewer** heavy-atom contacts, with a
one-sided p of **0.988** for "more contacts" — meaning the *reverse* test is significant. That is
exactly what the chemistry predicts when you select against the largest, most contact-rich residues.

The killer sentence: *"neither surviving quantity even exists for a de novo target."* There is no
parent crystal to retain a pose against, and confidence is not affinity. The filter *"selects for
designs the predictor finds easy, which is the definition of a metric gaming its own scorer."* The
gate flipped from PASS to **REFUTED**.

Two details worth copying. First, the refutation was **checked downstream rather than assumed**: the
shortlisting script sorts on the surrogate score at `scripts/32_shortlist_and_reseed.py:76`, with
aromatic count appearing only in a reporting line, so the filter was never a selection step and
refuting it does not disturb the shipped winner. Second — the winner carries aromatic count **2** and
would have been **discarded** by the filter at its own pre-registered threshold of ≤1.

> **Transferable principle.** *When a result survives a good null but contradicts a strong prior, vary
> the **outcome**, not the test. A rigorous test of the wrong dependent variable is a rigorous answer
> to a question you did not ask. And the cheapest diagnostic for "am I measuring the phenomenon or the
> instrument?" is to re-run the identical test on every other outcome you already have on disk.*

---

## 7. Optional stopping

### 7.1 The offence

The published conditioning result (`results/challenge2_pilot.md` Result 1): conditioned
`frac_iface_on_epitope` **0.7119** (sd 0.1130) versus unconditioned **0.5005** (sd 0.1684), difference
**+0.211**, pooled sd **0.143**, **Cohen's d = 1.4747**, Mann–Whitney U = 262.0/324,
P(cond > uncond) = 0.809, z = 3.16, **p = 0.0016**, 95% CI **[0.733, 2.216]**, n = 18 versus 18.

The arithmetic is impeccable:

```
pooled sd  =  √((0.1130² + 0.1684²)/2)  =  √0.0205635  =  0.14340
d          =  0.2114 / 0.14340          =  1.4742
SE(d)      ≈  √((n₁+n₂)/(n₁n₂) + d²/(2(n₁+n₂)))  =  √(36/324 + 2.174/72)  =  0.3759
CI         =  1.4747 ± 1.96 × 0.3759    =  [0.738, 2.212]      (reported [0.733, 2.216])
```

And the result is worthless as reported, for a reason that has nothing to do with the arithmetic.
*"The pilot looked at n = 10 v 5 (d = 0.96, ambiguous), extended to n = 18 v 18, and tested at nominal
α with no pre-registered stopping rule. **The reported p = 0.0016 is not the true type-I rate and
d = 1.47 is upward-biased** by exactly the winner's-curse logic this project applies elsewhere."*

### 7.2 Why that p is not a type-I rate

Under a look-then-extend protocol with no alpha-spending, the statistic you finally report is a
**maximum over looks**, and the maximum of several correlated draws exceeds any fixed threshold more
often than a single draw does. Two looks at nominal α = 0.05 give an actual rate around 0.08; the
exact inflation depends on the correlation between the interim and final statistics *and* on the rule
that governed the extension.

That last clause is where the real damage lies, and it generalises far beyond this project. The
extension rule here was never declared, so it cannot be modelled. **An undeclared stopping rule is not
merely an inflated α; it is an α that cannot be computed at all.** The same reasoning biases the
effect size: extension was conditioned on the interim being *ambiguous*, which pushes the final
estimate away from the interim value by construction.

### 7.3 The fix, and why it is strictly better

The replacement is §5's **deterministic per-backbone permutation test on data already on disk**, and
it wins on three named axes:

1. **It is deterministic per backbone, so there is no stopping rule to violate.** Each backbone's
   2000-patch reference distribution is fixed by the seed and the geometry; you cannot peek your way
   to significance because there is nothing to peek at.
2. **It asks a sharper question** — did conditioning hit *the right face*, not merely *do something*.
3. **It is a control that could have failed**, and one backbone of eighteen did fail it.

There is a structural point here too. The original test's null was "conditioning does nothing", and
the null arm already scored **0.501**, because a randomly placed antibody on a 113-residue domain hits
a 26-residue face reasonably often. **A null whose expected value is already high is a weak null.**
The patch null's expected value is **0.154**, over four times lower, precisely because it is matched
to the geometry of the alternative. Improving the null did more for the result than tripling the
sample size would have.

Finally, the strongest available control remains conceded and unrun: a **decoy-patch control**, with
the generator aimed at the *opposite* face of the target. It costs a GPU run.

---

## 8. Pre-registration, and the rarer virtue

Eleven pre-registration documents exist in the project. The test of a pre-registration is not that it
exists but that it **cost something**, and at least three fired against the author's interest:

- `results/specificity.md`: *"PRE-DECLARED FAILURE CONDITION TRIGGERED on `tim3` (2/3 seeds)… Note the
  arm **mean** would have passed; the rule was written per-seed before the data existed and is applied
  as written."* The design ships with a cross-reactivity caveat it would not have carried under a
  post-hoc analysis choice. That sentence — *the mean would have passed* — is the whole value of
  pre-registration in fifteen words.
- `results/negative_control.md`: pre-registered Rule 3 fired when nivolumab scored median ipSAE 0.017,
  and the entire negative-control experiment was declared **INCONCLUSIVE** rather than rescued — even
  though the negative arm was the interesting part and was unaffected.
- `results/prereg_2026-09-22_calibration_and_negative_control.md` contains a section headed *"Honest
  disclosure of what was already seen"*, naming one complex (7ZOZ) that had been folded as a timing
  test **before** the pre-registration was written, giving its numbers (median ipSAE 0.015, DockQ
  0.377), and explaining why its presence weakens the instrument.

The third is rarer than pre-registration itself. Almost nobody documents the contamination of their
own pre-registration, and it is exactly what makes the *other* two credible when they fire: a reader
now knows that this author reports the awkward cases, so a clean prereg from the same hand carries
weight it could not otherwise carry.

What pre-registration did **not** do here is worth naming too. The `prereg_*` files carry a detectable
effect for every planned test — but the rule was **never applied to numbers computed outside a
pre-registered experiment**, and every one of the campaign's nine withdrawals came from exactly there.
The cheap fix, proposed in [the critique chapter](09-critique.md), is a four-field stamp on every number
that enters a results file: **its n; its estimand in words ("single seed", "7-seed mean", "median of
five samples"); the effect it could have detected at that n; and its provenance.** Each of the four
fields kills at least one of the nine withdrawals on its own.

---

## What to take away

1. **`SE(z) = 1/√(n−3)` and `ρ_detect = tanh(2.80/√(n−3))` cost ten seconds and would have prevented
   half the campaign's withdrawals.** At n = 8 only ρ > 0.85 was detectable; a measured −0.168 was
   written down as "blind" and turned out to be −0.432.
2. **A null is a bound.** State it as "no effect larger than x at the n I have", or do not report it.
   The same standard applies to explaining-away claims: a partial of −0.081 at n = 40 carries a ±0.3
   interval and excluded nothing.
3. **Controls come in three kinds and you need all three.** A matched control with a dose–response
   (0 → 349 → 527 contacts removed) partitioned the metrics cleanly — ipSAE at 17.1× seed sd and
   interface pLDDT at 64.0× see the epitope; ΔG at 0.9× and contacts at 1.2× are blind. A negative
   control run on day 9 showed an anti-lysozyme antibody sweeping all five viability gates **on
   `model_0`** (the argmax of five draws; on the median it fails, ipSAE 0.219 vs 0.609), and — **on
   the median** — four of five gates rejecting **0 of 6** known-wrong inputs. The two figures use
   different estimators and neither is quotable without one.
4. **Match the null's geometry, not just its size.** Contiguous patches 0.154 against the real epitope
   0.712 is a result; uniform draws at 0.231 = 26/113 is the denominator. And then check your own
   null: the drawn patches are more compact (7.73 Å vs 10.08 Å), so the test is plausibly
   anti-conservative by an unquantified amount.
5. **A filter must beat the same rule applied at random at equal budget.** A random subset keeping
   fraction f keeps the maximum with probability exactly f; at f = 0.5 it keeps one of the top five
   97% of the time. p-values rising monotonically with retention are the signature of luck.
6. **When a result survives a good null but contradicts a strong prior, vary the outcome, not the
   test.** Six outcomes, one unchanged test, zero new compute: 2 wins, both properties of the
   predictor, and `contacts` significant in the wrong direction at p = 0.988.
7. **An undeclared stopping rule does not inflate α, it makes α uncomputable.** Prefer a deterministic
   per-item null — it removes the stopping rule entirely and usually asks a sharper question.
8. **A pre-registration is worth exactly what it costs you.** Three fired here against their author,
   and one document discloses its own contamination — which is what makes the other two believable.

Next: [where should the next measurement go](06-allocation-and-selection.md), which takes these
reliability and power numbers and turns them into a budget.
