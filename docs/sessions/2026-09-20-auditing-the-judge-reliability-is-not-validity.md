# Auditing the judge: reliability is not validity

**2026-09-20, ~10:00–17:00.** The day the project stopped measuring how precisely it
could rank designs and started asking whether the ranked quantities mean anything.
Two independent audits, four corrections to published claims, four handbook fixes, and
three controls that had never been run.

Self-contained: terms are defined where used, and earlier work is summarised in a line
and linked rather than assumed.

---

## 0. Why this day happened

The overnight run of
[[2026-09-20-spread-is-not-a-mean-and-the-rubric-has-a-ceiling|the previous session]]
landed 404 folds. Reviewing them, I gave a verdict — "the craft is top-decile, the
target selection was poor" — and was challenged on whether I was being generous because
I had done the work.

That challenge was correct, and the evidence was already on the table: **three claims I
made that morning were wrong, and all three erred toward a more dramatic finding.** So
the audit was handed to two independent agents with no access to my reasoning: one
reading the competition handbook against the code, one recomputing every headline claim
from the raw `.jsonl` rather than the write-ups.

They found four things I had missed and corrected two of my own claims. Everything
below that says "verified" means I recomputed it myself afterwards.

---

## 1. The distinction the whole day turns on

**Reliability** is how consistently a measurement reproduces itself. **Validity** is
whether it measures the thing its name claims.

This project had been exemplary about the first and had never once tested the second.
It had reliability coefficients, attenuation corrections, pre-registration,
winner's-curse shrinkage and a seeds-versus-designs power analysis — an apparatus for
ranking designs precisely — sitting on top of metrics nobody had checked were
measuring binding.

The two are independent. A bathroom scale that reads 3 kg heavy is perfectly reliable
and invalid. Six days of work had been spent making the scale more precise.

> **The transferable principle: reliability is cheap to measure and feels like rigour.
> Validity needs a control, and a control needs something external to the pipeline.**

---

## 2. What the audits found

### 2.1 The handbook was never read against the code

Every scoring conclusion — including mine — came from `config/metrics.yaml`, *this
project's own encoding* of the rubric. Auditing the arithmetic downstream of an
unverified premise is the same error the project was being criticised for.

Correct as transcribed: all eight metrics, their bands and cutoffs, the 60/20/20
weights, the aggregation formula, ipSAE's `Type = max` rule, and the A/B/C chain
convention. Four things were not.

**NetSolP was fed the wrong molecule.** The handbook says the **Fv (VH + VL)** twice;
every scoring call passed the full 219/217 aa **Fab** chains. The function's own
parameters were named `fv_heavy, fv_light`; the callers ignored that. See §3.2 — this
one inverted a conclusion.

**DockQ's multi-interface aggregation was an unrecorded convention worth a full band.**
A three-chain complex has three interfaces; the code hardcoded `min()` over the two
binding ones. On the named design:

| reading | DockQ | band |
|---|---|---|
| `min(A-C, B-C)` — what was used | 0.755 | Medium |
| mean of binding interfaces | 0.805 | **Good** |
| DockQ v2's own `Total DockQ` | 0.850 | **Good** |
| `max(A-C, B-C)` | 0.855 | **Good** |

Three of four readings put the design a band higher, and `Total DockQ` is what an
organiser gets by running the tool and reading its summary line. Now a recorded switch
with the measurement in the comment.

**Four band edges were inclusive where the handbook is strict.** Contacts `> 25`,
interface pLDDT `> 80`, CDR SASA `> 600`, CDR-H3 identity `< 70%`, plus two viability
cutoffs. Worth 5.0 final points on identity alone — and the project's own next step was
to generate designs against the 70% edge. Fixed; exactly 70.0% now scores Medium.

**The required PAE deliverable did not exist.** The handbook requires
`design_X_pae.json`; Boltz writes `.npz` and nothing converted it. Without it the
submission fails validation *and* ipSAE — the only metric scored in both challenges —
cannot be recomputed. Written, and round-tripped through the pinned `ipsae.py`.

~~That round-trip found something else: ipSAE from our JSON is 0.8491, from the npz path
0.8560 — a real code-path difference inside `ipsae.py`.~~

**WITHDRAWN 2026-09-20, later the same day. There is no code-path difference.** Running
`ipsae.py` on the same structure via both routes gives, per chain pair:

| pair | npz route | our JSON route |
|---|---|---|
| A–B | 0.898372 | 0.898371 |
| A–C | 0.823561 | 0.823574 |
| B–C | 0.804935 | 0.804978 |

Agreement to 5 decimals; the 1e-5 residual is the 2-dp rounding the writer applies to the
PAE matrix. **The converter round-trips exactly.**

The 0.8560 I compared against was the **8-seed mean** from `results/m3_winner.md`, not a
single-fold npz value. Seed 1 alone is 0.8491 — precisely what the JSON reproduced. I
compared a one-seed number to a multi-seed mean and called the gap a bug.

**This is the fourth overstatement I made today and the fourth in the direction of a more
interesting finding.** The pattern is now the most reliable thing about my own reporting
in this project, and it is why the independent audits were worth running.

### 2.2 Three published claims were false

**"Three seeds is the worst allocation at every budget tested"** — the project's
flagship methodology result, promoted verbatim into `LEARNINGS.md`. It is refuted by
the table printed *directly above it*: at budget 40, 20×3 scores **+1.4024**, beating
4×10 (+1.3847) and 2×15 (+1.2992). Over-seeding a tiny shortlist is worse than
under-seeding a broad one. The claim holds at budgets 120 and 240 only.

**"Winner's-curse shrinkage validated to 0.001"** — in the README, the results file and
`LEARNINGS.md`. The validation was **one fold**, whose standard deviation is the
measured within-design sd of **0.467**. The shrunk prediction missed by 0.03 sd; the
*unshrunk* one by 0.33 sd. Both sit inside one standard error, so the measurement cannot
distinguish a 0.153-point discount from no discount at all. Landing within ±0.0005 of
any prediction is a 1-in-1200 event. Discriminating the discount at 80% power needs
**k ≈ 73 fresh seeds**. The estimator is sound on theory; the validation was a
coincidence.

**"A residue's own confidence is blind to conformational heterogeneity"** — measured at
**n = 8** (ρ −0.168, p = 0.69), whose 95% CI is roughly ±0.7 wide. At n = 239 the same
quantity is **−0.432**, and loop pLDDT *beats* interface pLDDT (−0.344). But my own
correction over-shot too: I said the circularity inflation was "roughly a third" by
comparing a 1-pair estimate to a 3-pair one without disattenuating both. Done properly
it is about **13%**, and the honest value is ρ ≈ −0.28 to −0.32.

A fourth, which I found while fixing the third: **"the ensemble carries no information
the sequence didn't already have."** The aromatic half replicated almost exactly on 239
independent designs (aromatics→DockQ raw **−0.535** against the original −0.536;
controlling for spread **−0.408** against −0.410). But the partial that justified
dropping the ensemble axis from selection — spread→DockQ controlling aromatics,
**−0.081, p = 0.62** at n = 40 — is **−0.289 (p = 5.7e-06)** over the pool and −0.303 on
the very same T = 0.1 arm. *The axis was dropped on the strength of an underpowered
partial that does not replicate.*

**All four are the same error: a small-sample null read as evidence of absence.** The
project already knew this failure mode — `LEARNINGS.md` carries "measure the noise floor
before comparing any correlation to a threshold", with the Fisher-z arithmetic showing
n = 14 cannot adjudicate a 0.6 gate. That discipline was applied to *positive* findings
and never to *nulls*.

> **A null is only meaningful as "no effect larger than x". State the detectable effect
> at the n you actually have, or do not report the null.**

### 2.3 Most of the metric stack carries no design information

Verified independently. Within-design variance from 20 designs × 7 seeds; total from
the 239-design pool. `ICC = 1 − within/total` is the fraction of the spread that is the
design rather than the sampler:

| metric | ICC | reading |
|---|---|---|
| DockQ | 0.870 | usable |
| interface pLDDT | 0.841 | usable |
| ipSAE | 0.647 | usable |
| PRODIGY ΔG | 0.618 | usable |
| **contacts** | **0.003** | **pure seed noise** |
| **CDR SASA** | **0.000** | **pure seed noise** |

And separately, five of the eight rubric metrics are **constants** across this pool —
contacts, interface pLDDT, CDR SASA and CDR-H3 identity are 100% in the Good band,
NetSolP is 0% — so they contribute nothing to ranking. **The eight-metric harness ranks
on three.** The hotspot ablation of the previous night had its verdict decided on
`contacts`, i.e. on a comparison of two noise draws.

---

## 3. What was fixed, and two conclusions that inverted

### 3.1 Predicted structures are close to the memorised crystal

Cα RMSD over CDR-H3 after framework superposition, against the 5GGS crystal loop:

| | RMSD |
|---|---|
| crystal copy 2 vs copy 1 (experimental floor) | **0.183 Å** |
| Boltz refolding pembrolizumab's **own** sequence | **0.400 Å** |
| **239 designs at 15–46% CDR-H3 identity** | **1.119 Å** (86% within 1.5 Å) |

*(My first attempt at the experimental floor returned 12.5 Å. The prepared second
crystal copy is also chained A/B/C, so "chain C" is the antigen, not the heavy chain —
and its heavy chain is 220 aa against 219, so fixed indices do not transfer either.
A number that absurd is the check; the fix locates the loop by motif.)*

Read with the post-cutoff control — median Fab DockQ **0.291** on five complexes
released after Boltz-2's verified 2023-06-01 cutoff, against 0.818 on 5GGS — the pool's
DockQ spread is variation *around* a recalled template.

### 3.2 NetSolP: the ceiling is real, the explanation was backwards

On the Fab input, the heavy chain looked limiting and every design scored below the
parent. On the **Fv** the handbook specifies, the ordering reverses:

| | Fab (what was scored) | **Fv (what the handbook says)** |
|---|---|---|
| pembrolizumab VH / VL | 0.623 / 0.626 | **0.733 / 0.569** |
| designs, VH range | 0.562 – 0.619 | **0.668 – 0.742** |
| designs with VH in the Good band | 0 | **168 / 239 (70%)** |
| which chain limits `min()` | heavy | **light** |

0/239 still reach Good, so developability is still pinned at Medium — but **not because
redesign hurts solubility. 70% of the designs have a heavy chain in the Good band**, and
the composite is held down entirely by the one chain ProteinMPNN never touches.

"20% of the rubric is an unreachable ceiling" was wrong. **"20% of the rubric is gated by
a chain we never designed"** is right, and it names a concrete lever: light-chain CDR
redesign would move `final` from 87.5 to 92.5.

> **A convention error does not merely shift a number; it can invert the causal story
> you tell about it.**

---

## 4. The three controls that had never been run

### 4.1 Epitope knockout — the metrics split, and it is the better news

The decoy panel varied the *antigen*, which confounds "is the antibody site-selective"
with "does the predictor respond to antigen identity at all". This holds PD-1 fixed and
alanines only its binding face, against a matched control of the same number of
alanines placed off the interface. Both mutant arms take a fresh MSA, so the control
absorbs the MSA asymmetry as well as the mutation burden.

| metric | wt | off-interface ctrl | epitope removed (527 contacts) | effect in its own seed sd | verdict |
|---|---|---|---|---|---|
| **ipSAE** | 0.869 ± 0.014 | 0.823 | **0.625** | **17.1×** | **sees it** |
| **interface pLDDT** | 89.9 ± 0.3 | 89.1 | **71.0** | **64.0×** | **sees it** |
| PRODIGY ΔG | −12.87 ± 0.35 | −13.00 | −12.53 | 0.9× | **blind** |
| contacts | 99 ± 4 | 97 | 94 | 1.2× | **blind** |

Dose-dependent across 0 → 349 → 527 contacts removed, with the matched control flat.
**The confidence metrics do report the interface** — which cuts against the harsher
reading I had given, and is the clearest positive result of the day.

The split is what matters. **PRODIGY ΔG carries the largest single share of the ranking
variance and is blind to the epitope**: deleting half the binding face moves it less
than its own seed noise. Taken with it scoring the named design better against TIM-3
(−14.1) than against PD-1 (−12.5), the selection leaned hardest on the metric that
fails every specificity check put to it.

Note the contrast with the antibody-side ablation, where removing 158 contacts did
nothing: a mutated *antigen* has no memorised partner for the model to fall back on.

*(A verdict rule matters here. My first version used "effect > 2% of the mean" and
passed ΔG on a +0.333 kcal/mol shift, producing a table that contradicted its own
prose. The rule now tests against each metric's measured seed sd on this complex and
against the matched control — 3× both.)*

### 4.2 Scramble null — the designs win, in the upper half only

Permuting a design's CDR-H3 **order** holds length, composition, aromatic count and
charge exactly constant, so every cheap sequence feature this project used as a
predictor is fixed by construction. It is a far stronger null than an MPNN redesign,
which still produces sequences the model likes.

| | n | DockQ mean | range |
|---|---|---|---|
| source designs | 30 | **0.706** | 0.624 – 0.766 |
| their scrambles | 30 | **0.565** | 0.037 – 0.708 |

28 of 30 sources beat their own scramble; median paired difference **+0.118**,
p = 2.4e-06. **CDR-H3 order carries information its composition does not.**

The precise version matters more: **15/30 scrambles land inside the pool's DockQ range,
and 0/30 exceed the pool median.** Half of random permutations pass for a real design;
none passes for a good one. So the top of the distribution is genuinely
design-dependent — the strongest defence of the M3 ranking any experiment here has
produced — while anything below the median is indistinguishable from a scrambled loop
and should not be called a design result.

### 4.3 SKEMPI — the metrics do not track measured affinity

45 single mutants of 3HFM (HyHEL-10 Fab vs hen lysozyme) with experimental ΔΔG, plus the
wild type at 3 seeds. The only experiment in this project that compares a predicted
number to a laboratory measurement. 48/48 folded, zero failures.

| metric | ρ vs ΔΔG (all 45) | ρ (27 reliable) | expected sign |
|---|---|---|---|
| PRODIGY ΔG | +0.221 | +0.050 | positive |
| ipSAE | +0.059 | **+0.300** | negative — **wrong way** |
| DockQ vs crystal | −0.101 | −0.198 | negative |
| interface pLDDT | +0.047 | **+0.275** | negative — **wrong way** |
| contacts | −0.246 | −0.223 | negative |

Nothing is significant, and at n=45 the bound is "no monotone effect stronger than
ρ ≈ 0.41". **The null is informative rather than an insensitive assay**: across mutants
ipSAE varies 19.5× its own seed sd and interface pLDDT 82.9×. The metrics move a great
deal; they do not move with affinity.

The worked examples are more persuasive than the coefficients. ΔΔG above ~+20 kcal/mol
means binding was not detectable:

| | measured ΔΔG | ipSAE | DockQ | ΔG |
|---|---|---|---|---|
| **wild type** | 0.00 | **0.903** | **0.844** | **−12.0** |
| `KY96M` | +28.35 | 0.713 | 0.820 | **−12.8** |
| `KY96A` | +28.19 | 0.560 | 0.797 | −11.4 |
| `KY97A` | +24.52 | 0.184 | 0.799 | −10.8 |
| `WH98A` | +23.06 | 0.875 | 0.806 | −11.5 |
| `NL31A` | +21.81 | **0.917** | 0.837 | −12.2 |

**Four of five score like the wild type.** `NL31A` abolishes binding and scores ipSAE
0.917 *above* the wild type's 0.903; `KY96M` gets a *more* favourable ΔG than the real
complex. Only `KY97A` is caught.

Note the combination with §4.1: **ipSAE and interface pLDDT pass the epitope-knockout
control and fail this one, with the wrong sign.** They detect gross interface
destruction and mis-rank point mutations — which is precisely the "liveness test, not a
ranking metric" pattern first recorded for ipSAE on 2026-09-17 from the poly-Gly
anchors. This is its **fifth instance and the first validated against experimental data**
rather than against another prediction.

> **What the pipeline can claim: it distinguishes a destroyed interface from an intact
> one. It cannot rank two intact ones by affinity. Every ranking claim in this project
> sits in the second category.**

---

## 5. Process failures worth recording

**`pgrep -f` self-matched for the third time this session, in a new way.** The SKEMPI
chain waited on `pgrep -f "scripts/run_validity\.sh"`. I verified that pattern could not
match the waiting script's own *filename* — true — but I created the script with a
heredoc inside `bash -c`, so the **launcher shell's argv contained the entire script
body**, including the pattern. The loop matched its own grandparent and idled the GPU
for **2 h 39 min**. The guard was against the wrong object: not the filename, the argv.

**A generated document contradicted itself.** `results/specificity.md` printed the
3-seed TIM-3 mean (0.568) while I quoted the 8-seed value (0.513) in conversation,
because `_reference_controls()` iterated only the reference arms and took "ours" from
the panel — so five folds made specifically to power that comparison sat unread in the
same file. Fixed to pool them and to report the CI (+0.182, [+0.045, +0.320], p = 0.038)
rather than a branch verdict: with n = 3 per arm the smallest attainable two-sided p is
exactly 0.100, which is what the original test returned. **A decision tree on point
estimates is not a test — check the attainable p before reading the output.**

---

## 6. What is crude, stubbed or unproven

- **SKEMPI's target, 3HFM, predates the training cutoff.** Acceptable for a ΔΔG
  *ranking* test, but a positive result would need re-testing post-cutoff.
- **Eighteen of the 45 SKEMPI mutants are detection-limit values**, not measurements.
  Kept for rank order; the analysis reports with and without them.
- **The epitope knockout is n = 3 per arm** and the mutant arms use server MSAs where
  the wild type uses the cache. The matched control absorbs that, but it is an
  asymmetry.
- **The scramble null is one seed per design.** Fine for a 30-pair paired test, not for
  per-design statements.
- **Two of the eight metrics are noise** and remain in the reported rubric because the
  organisers recompute them; they have been removed from *internal* reasoning only.
- **The band→score mapping is still this project's invention.** The handbook gives
  ranges (Good 9-10, Medium 6-8, Poor 0-5) and never says how to pick within one. The
  same design scores **81.0 / 87.5 / 94.0** under bottom / midpoint / top-of-band, and
  the handbook's own stated maximum of 100 is unreachable under midpoints — which is
  evidence the midpoint reading is wrong. Unresolved; needs the organisers.

---

## 7. Glossary

**Attenuation** — shrinkage of a correlation toward zero caused by noise in either
variable; √(reliability) per variable.
**Censored value** — a measurement reported at an assay's detection limit rather than
measured; its rank is meaningful, its magnitude is not.
**DockQ** — 0–1 similarity of a predicted complex to a reference; a *pose* metric, not
an affinity one.
**ICC (intraclass correlation)** — fraction of a measurement's total variance that is
between-subject rather than within-subject; here, design rather than random seed.
**ipSAE** — a confidence score computed from the predictor's own predicted aligned
error.
**PRODIGY ΔG** — a binding-affinity estimate regressed from interface contact counts.
**Reliability** — see ICC; how consistently a measurement reproduces itself.
**SKEMPI** — a database of experimentally measured binding affinities for point mutants
of protein complexes.
**Validity** — whether a measurement corresponds to the quantity it is named for.
**ΔΔG** — change in binding free energy on mutation, `RT ln(Kd_mut/Kd_wt)`; positive
means weaker binding.
