---
date: 2026-09-26
tags: [project, locksmith, learning, problem]
status: living
---

# Retraction register — every claim this project withdrew

**One fact, one place.** A claim that has been withdrawn, refuted or superseded is recorded
here with the number that replaced it and the file that settles it. Chapters, results files
and session docs are **not** retro-edited into agreement; that is the defect the project
documents (see [the generated-artefact failure classes](../docs/lecture/08-what-broke.md)).
Where a document still carries retracted text it is named in the **live text** column, so
the register is a work list rather than a monument.

This file exists because "the five stale-document retractions and four overstated claims"
had been carried as a *pointer* in three consecutive session docs without anyone ever
enumerating them. A retraction that is only gestured at cannot be checked off, and
`STATE.md` could not be cleaned while the list did not exist.

**Scope.** The whole project.
[The course's own corrections file](../docs/lecture/CORRECTIONS.md) is narrower — it covers what a reader of the lecture course must not trust — and its
C1/C2 remain the fuller treatment of those two items. Where both cover a claim, this file
is the index and that file is the detail.

---

## How to read the status column

| status | meaning |
|---|---|
| **WITHDRAWN** | the claim is false; nothing replaces it |
| **SUPERSEDED** | a corrected value replaces it |
| **REFUTED** | tested against new evidence and failed |
| **FLAGGED** | known not to reproduce; not yet corrected, and deliberately not guessed at |

---

## A. Scores and deliverables

### A1 — Challenge 1 scores 96.0 · **SUPERSEDED → 94.0**

`dockq.compute` parsed DockQ's **printed** summary, which formats to 3 dp, then rounded
again itself. True `GlobalDockQ = 0.7995794972281312` bands **medium**; the printed `0.800`
banded **good**, worth 2 composite points. The true value is **0.00042 below** the 0.80
Good edge, and any true value in `[0.7995, 0.800)` was misbanded the same way.

Settled 2026-09-24. Mechanism: `dockq.compute` now passes `--json`; `score.evaluate`
populates `Scored.rounding_risk` for any value within ±0.5 ulp of a band edge.
Evidence: `submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge1/metrics/scores.md`, which now
prints `dockq 0.799579`.

**Live text — this entry originally read "none known", which was wrong.** A newline-tolerant
sweep on 2026-09-26 (§C1's lesson, applied) found the stale `final 96.0` and the superseded
convention triple `84.0 / 90.0 / 96.0` in **four places in the lecture course**
(`01-the-biological-problem.md:701`, `02-the-engineering-problem.md:234` and `:730`,
`07-the-campaign.md:466`) and in `results/pitch_outline.md`. The chapters are indexed rather
than rewritten, per policy, under the new
[C3 of the course corrections file](../docs/lecture/CORRECTIONS.md); `pitch_outline.md` is
marked superseded at its head. `PLAN.md:862` and `BUILD.md:204` already carried the
correction inline.

**And the course's C1 had to be narrowed**, because it ended "Every Challenge 1 number in
this course stands" — true of the MSA defect it was scoped to, and read as a general
clearance. *A correction scoped to one defect must not be worded as a blanket exoneration;
the next defect will be unrelated.*

### A1b — the shipped Challenge 1 §9.2 section and novelty table described the PRE-FIX molecule · **WITHDRAWN**

The submitted variant is `mpnn_T0.5_s104_036` **+ N55Q**. Two shipped blocks described the
design *before* that fix, for as long as the package existed.

**The §9.2 self-report was false about its own molecule.**
`Challenge1/docs/methods_and_limitations.md` stated the design "carries `NG` at heavy chain
position 55" and that the redesign "left `N55-G56` intact". The shipped heavy chain reads
**`LQGG`** at 54–57 — **position 55 is Q** — and line 133 of the same file says the fix was
applied. A motif scan of the shipped CDRs returns **none**; the wild type returns
`[('NG', 55)]`.

**The novelty table was wrong in four ways**, verified by positional diff against the
handbook's 232-aa wild type (`scripts/55::HB_HEAVY`):

| quantity | shipped | true |
|---|---|---|
| substitutions | 15 | **16** |
| whole-chain identity | 93.5% | **93.1%** |
| designable positions changed | 15 of 29 | **16 of 29** |
| CDR-H2 | `INPSNGGT -> INPLNGGT` (1 change) | `INPSNGGT -> INPLQGGT` (**2**) |

`INPLNGGT` **exists nowhere in the package** — it is the pre-fix loop with the N55Q edit
never applied to the prose. Three other things in the same package already said 16,
including the `--allowed_mismatches 16` minimum, which *is* the substitution count. The
table was the sole dissenter, and `_BANNED` already carried `"our 15 substitutions"` — the
guard banned one phrasing and the table evaded it as a `|`-row.

**Fixed by computation, not correction.** `submit/docs.py::challenge1_novelty_table` and
`::deamidation_motifs` derive both blocks from the shipped sequence, with a length guard
that refuses to emit a table if the chain and the wild type differ in length.

**Live text:** `results/audit_response_2026-09-22.md:268` still carries `15` and `93.5%`.
Left unedited — it is a historical audit recording what was believed that day — and covered
by this entry.

*The transferable point: a hand-written table beside a generated artefact will describe
whichever molecule it was written for, and no per-file check can see the mismatch, because
the table is internally consistent and the structure is valid. Only recomputation catches
it.*

---

### A2 — every Challenge 2 number before 2026-09-23 · **WITHDRAWN**

Boltz compares the MSA's query length to the input chain and, on mismatch, **discards the
alignment and folds single-sequence**, announcing it only on stdout, which the harness
captured and threw away. Every Challenge 2 fold paired a **123-residue** antigen with a
**113-residue** cached alignment. Measured 2×2 on ipSAE in
[the 2×2 that isolates the alignment](msa_silently_discarded.md): with a correct alignment
**0.012** both pre- and post-fix; without, **0.773 / 0.686**.

Specifically withdrawn: **"1 of 30 designs clears"** as measured then; **ipSAE 0.864** for
`bb_2_0_dldesign_1`; and **composite 91.2** as evidence about a molecule.

**Superseded twice, which matters.** The re-screen against a correct alignment promoted
`bb_1_0_dldesign_0` (**0.637**, previously ranked 29th of 30) while the packaged design fell
to **0.013** from 1st — the ranking was close to inverted, not merely noisy. That design was
then itself superseded by the constrained re-design campaign, and the shipped Challenge 2 is
now **`bb_8_0`**, ipSAE **0.904** on `model_0` (median of 5 diffusion samples **0.859**),
composite **93.6**, viable 5 of 5.

**Live text:** [the course corrections file](../docs/lecture/CORRECTIONS.md) §C1 still ends on
`bb_1_0_dldesign_0` and still calls the zip stale. Fixed 2026-09-26; see §D1 below.

### A3 — `submission/LOCKSMITH_DEV.zip` is stale · **SUPERSEDED**

True from 2026-09-23 until the rebuild on 2026-09-25 11:47. The package now carries
Challenge 1 at **94.0** and Challenge 2 at **93.6**, both viable, `VALIDATION PASSED` from
the package's own files, and all timestamps inside the tree within seconds of each other.

---

## B. Claims about method

### B1 — "three seeds is the worst allocation at every budget tested" · **WITHDRAWN**

False against the table it was summarised from. At a **40-fold** budget, 20 candidates × 3
seeds scores **+1.4024**, beating 4 × 10 (**+1.3847**) and 2 × 15 (**+1.2992**). The
surviving claim is narrower: depth beats breadth **once the budget is large enough** — at
120 folds, 60 × 3 → +1.388 against 20 × 7 → **+1.466** and 13 × 10 → **+1.479**, so the best
row of that budget was not even the one actually run.

Caught by an independent audit 2026-09-20. The sentence had been promoted to `LEARNINGS.md`
verbatim from a results file **where the refuting row was printed directly above it**.
Evidence: [the allocation simulation](m3_shortlist_depth.md).

**Live text:** the phrase survives as the *filename* of the 2026-09-19 session doc, which
cannot be renamed without breaking links; the session index line carries the correction.
`README.md` and `PLAN.md` carry it with a ⚠ correction attached.

### B2 — "redesign the light-chain CDRs" · **REFUTED**

Wrong twice, and the whole refutation cost **zero GPU folds** because NetSolP is
sequence-only. (1) Under `min(VH, VL)` the ceiling is the *other* chain: VH is **0.699**
against a Good edge of **0.70**, so `max over all light chains of min(0.699, VL) = 0.699` —
the band cannot move, by **0.001**. (2) 24 ProteinMPNN light chains at T=0.1 moved VL from
0.5690 to at best **0.5920** (+0.023 against a required **+0.131**), **0/24** reached the
edge, and **24/24** introduced new CDR liabilities.

Note this refutes a recommendation *this project's own audit made* — see §B6 — which is the
cleanest instance of a correction needing a correction.
Evidence: [the light-chain sweep](ch1_ng_and_light_chain_2026-09-22.md).

### B3 — the contact-count rule · **REFUTED**

Claimed: the antigen contact count on a mutated residue predicts whether a prescribed §9
developability fix is safe. A third arm mutates `N91Q` on a residue with **zero antigen
contacts in all five samples** and still collapses the interface **0.637 → 0.128** median,
0/5 viable. A matched framework control settles the competing "no margin" explanation:
`N77Q` **0.561** and `N84Q` **0.696**, both zero-contact, both `N→Q`, averaging the
**0.637** baseline to within noise — so the design absorbs a single-residue change fine and
**region**, not contact count, is the predictor.

**Three of its four instances were void anyway**, having been measured in the discarded-MSA
condition of §A2. What survives is the weaker and older claim: *a prescribed fix is a design
change and must be measured, not assumed.*
Evidence: [the fix arms](liability_fix_arms.md), [the matched control](two_findings_from_the_matched_control.md).

### B4 — the winner's-curse discount "was validated" · **WITHDRAWN**

It was **applied**, not validated. Shrinkage predicted **94.963** and the fresh seed
measured **94.962**, but that validation was **one fold**, whose sd is the measured
within-design sd of **0.467**. The shrunk prediction missed by 0.03 sd and the *unshrunk*
one (95.117) by 0.33 sd, so both sit inside one standard error and the test cannot
distinguish a 0.153-point discount from no discount. Landing within ±0.0005 of any
prediction is a 1-in-1200 event. Discriminating the discount at 80% power needs **k ≈ 73**
fresh seeds. The estimator stands on theory; the confirming measurement does not.

### B5 — two small-sample nulls promoted to rules · **WITHDRAWN, both**

One mistake made twice: a wide confidence interval around zero read as evidence of absence.

| claim as published | at n=8/40 | at n=239 |
|---|---|---|
| "loop pLDDT is blind to conformational heterogeneity" | ρ = **−0.168**, p=0.69, n=8 | ρ = **−0.432**, p=2.9e-12 |
| "the ensemble carries no information the sequence didn't" | partial **−0.081**, p=0.62, n=40 | **−0.289**, p=5.7e-06 |

The n=8 estimate carried a 95% CI roughly ±0.7 wide and is statistically indistinguishable
from −0.43. **The ensemble axis was dropped from selection on the strength of an n=40
partial that does not replicate.** A null is only meaningful as *"no effect larger than x"*.

Two riders, both corrections to the correction: the pLDDT↔spread correlation's inflation was
first reported as "about a third" and is **about 13%** after disattenuating properly; and
the aromatic half of the same analysis **replicated almost exactly** (−0.536 → −0.535 raw),
so "the aromatic result reversed" was itself wrong.
Evidence: [the checks that found both](audit_2026-09-20.md).

### B6 — "ProteinMPNN degraded developability in 239/239 cases" · **WITHDRAWN**

Computed on **Fab** chains where the handbook specifies **Fv**, twice. On the correct input
**168 of 239 (70%)** designs have a heavy chain in the Good band and **4** beat the parent's
own heavy chain; mean VH is **0.7061** against pembrolizumab's **0.7328**. 0/239 still reach
Good overall, so the conclusion survives and **its explanation inverts** — the composite is
held down by the one chain ProteinMPNN never touches.

*A convention error does not merely shift a number; it can invert the causal story you tell
about it.* And the lever this audit concluded existed was then refuted at §B2.

### B7 — the G3 CDR-H3 aromatic filter as a design rule · **REFUTED**

It beat 10,000 equal-budget random subsets at p<0.0001 on mean DockQ and still fails,
because the outcome variable was wrong. Re-running its own equal-budget test against each of
six scored metrics (n=239), it wins on **2 of 6** — `dockq` (+0.0237) and `iface_plddt`
(+1.12) — and **both are properties of the predictor**, not of the interface. Every quantity
about the interface itself is null or against it: `dg` p=0.064, `cdr_sasa` p=0.547, and
`contacts` runs the **wrong way** (filtered designs make **1.80 fewer** heavy-atom contacts,
one-sided p for 'more contacts' **0.988**) — exactly what chemistry predicts when selecting
against large aromatics. The rule selects for designs the scorer finds easy to place
confidently: a metric gaming its own scorer.

*When a result survives a good null but contradicts a strong prior, vary the **outcome**,
not the test.* Evidence: [the six-outcome re-run](g3_outcome_variable.md).

### B8 — "depth rescues backbones" and "bb_17_0 is a genuinely good backbone" · **WITHDRAWN**

144 folds, 18 backbones × 8 constrained sequences. Coverage grew 4 → 8 of 18 against a
homogeneous binomial's expected **5.3** and **9.0**: the growth is an order statistic
behaving as a flat rate predicts. Per-stratum rates **5.6%** vs **11.1%**, Fisher exact
**p=0.367**. No overdispersion (χ² = 22.91 on 17 df, p=0.152; beta-binomial LRT p=0.202).
For bb_17_0, P(≥3 clears in 8) = 0.0235, so the expected count over 18 backbones is **0.42**
and we saw 1.

Both are the same error — reading structure off small counts without asking what a
structureless model predicts — and it is the **third** instance on this project, after B7
and the n=8 heterogeneity null. Evidence: [the depth sweep](depth_sweep.md).

### B9 — fold batching · **SUPERSEDED, then DISQUALIFIED**

Costed at "~1.8×" from an unmeasured split between per-fold and per-invocation time, and
that projection justified scheduling decisions for two days. Built and measured: **1.16×**
(84 s → 72 s per fold), saving 0.8 h on a 239-fold arm rather than 2.4 h.

A separate throughput arm later measured batching at **1.65×** and **disqualified it
outright**. Only 1 of 4 structures was byte-identical to its serial
reference; ipSAE moved up to **0.30** and atoms by **72–89 Å**. Staggering gives 1.30× and
is byte-identical 4 of 4, below the pre-registered 1.5× bar, so folding runs serially.

---

### B10 — the batch-corruption MECHANISM ("Boltz pads a batch to its longest sequence") · **WITHDRAWN**

The batching arm is disqualified and that is not in dispute: 1.65×, only 1 of 4 structures
byte-identical to its serial reference, ipSAE moving up to **0.30**, atoms by **72–89 Å**.

What is withdrawn is the *explanation*. The project asserted that Boltz pads a batch to its
longest sequence, so a design's score depends on which other designs share its batch. **The
four folds ran 94 seconds apart — no batch ever formed.** Padding cannot be the cause.

**The cause is unknown, and no replacement mechanism is offered.** That is the honest state:
a reproducible corruption with no explanation is a better record than a plausible
explanation that the timing refutes.

**Where this was found is the interesting part.** The withdrawal existed in exactly one
place — `src/locksmith/submit/deck.py`, i.e. only on a shipped slide — while `README.md`,
`results/throughput_arms.md` and §B9 of this register all still stated the mechanism as
fact. A withdrawal that lives only in a generator, is shown to a reviewer, and never
reaches the register whose purpose is enumerating withdrawals. Propagated 2026-09-26.

---

## C. Numbers in shipped or published prose

### C1 — "0% false-positive rate against a 25% false-negative rate" · **WITHDRAWN**

Two different DockQ thresholds, quoted as though they shared one. Recomputed from
`runs/calibration/scores.json`, n=40, for the ipSAE ≥ 0.60 gate:

| DockQ threshold | false positive | false negative |
|---|---|---|
| Acceptable+ (≥ 0.23) | **0%** | **58.3%** |
| Medium+ (≥ 0.49) | **12.5%** | **25.0%** |

The quoted pair takes the flattering half of each and **is reachable at neither**. The 0%
also rests on **4 negatives** — Clopper–Pearson 95% upper bound **0.602**, i.e.
uninformative. It was live in a shipped document and had survived **four** independent
audits, found only because the figure was recomputed for a deck slide instead of copied from
an earlier message.

*An error rate is a property of a threshold.* And: a figure that lives in prose and never in
a data file has no provenance — which is how the interface-pLDDT-vs-ipSAE AUCs
(**0.992** / **0.911** at Medium+) also went unrecorded, an ordering that **reverses** at
Acceptable+ (0.750 vs 0.833).

**Live text.** Correcting the shipped document did not correct the claim, which had spread
to two other files. `results/constrained_paired.md` carried it **twice** (lines 93 and 172);
both are corrected in place 2026-09-26.
`results/prereg_2026-09-23_depth_sweep.md:82` also carries it and is **deliberately left
alone**: a pre-registration records what was believed *before* the experiment, and editing
one destroys the only thing it is for. This register is the right place for its correction.

*A correction applied where the error was found, rather than everywhere it had been copied,
is half a correction.* The grep costs under a minute and should have run on the day the
shipped document was fixed.

**And the grep itself under-reported, which is the sharper lesson.** A line-oriented
`grep -rn "0% false-positive"` found **one** of the two instances in `constrained_paired.md`.
The other was wrapped as `with a 0%\nfalse-positive rate` — the phrase straddled a newline,
so no single line contained it. The second instance surfaced only by accident, while reading
the file for something else. **In hard-wrapped prose, a line-oriented search silently
under-reports every phrase longer than a few words**, and it fails *quietly*: a grep that
returns one hit looks like a complete answer. Search prose with a newline-tolerant matcher:

```python
re.compile(r'0%\s+false[- ]positive', re.I)   # \s+ spans the wrap
```

This is the same family as [the silent-failure classes](../docs/lecture/08-what-broke.md) —
a tool answering a slightly different question than the one asked, and saying nothing about
the difference. The project's own wikilink guard exists because `[[a|b]]` split across a
newline breaks the same way.

### C2 — "the minimum `--allowed_mismatches` that works is 15" · **SUPERSEDED → 16**

15 still exits 1 and prints nothing. Measured, not inferred. This mattered beyond tidiness:
the text told a grader to pass a value producing no output under a §7.2 hard cutoff — a
route to a score of 0 instead of 94.

### C3 — DockQ `0.816`, and the per-interface triple `0.931 / 0.723 / 0.794` · **WITHDRAWN**

All four belong to `model_0` of the **pre-`N55Q`** diffusion sweep, a structure differing
from the shipped one at a single position (heavy 55, N→Q). The submitted design scores
**0.7996**.

**Worth reading for the near-miss.** The triple was first "explained" as the AB **LRMSD**
column misread as DockQ — and AB's LRMSD genuinely *is* 0.931, so the story was
self-consistent and wrong. It was caught only because that explanation accounted for **one
of three** numbers. *A coincidence that explains part of the evidence terminates the search;
require an explanation to cover every observation before accepting it.*

### C4 — "40.0% against all 6,864 IGHV × IGHD × IGHJ recombinations" · **WITHDRAWN**

Not merely stale but **unreproducible**. The germline database holds 249 V × 76 D × 14 J =
**264,936** combinations, divisible evenly by none of 6,864, and nothing in this repo
enumerates recombinations. Cut rather than re-derived, and replaced with
`germline.compute(convention="best_segment")` — the alternative reading this project
actually implements, which is *computed* and so cannot be orphaned by the next design swap.

### C5 — the NetSolP triple `0.379 / 0.463 / 0.733` · **WITHDRAWN**

Mixed VH and VL across **three different variants and two constructs**. The numbers are
per-chain pairs and must be quoted as such: on **Fab** chains (VH/VL), `ESM12` gives
**0.35 / 0.31** and `Distilled` **0.49 / 0.45**, both failing the 0.50 cutoff, while the
`ESM1b` 5-fold ensemble passes at **0.57–0.73**; on **Fv**, pembrolizumab reads VH **0.733**
/ VL **0.569**, which inverts *which chain limits* `min(VH, VL)`.

Also retracted from that entry: the claim that the CLI default *"would have failed every
design"*. The construct convention was separately wrong (Fab fed where the handbook says
Fv), so the counterfactual was never computed on the right input. What survives is the
general rule: **anything that can move a result across a threshold belongs in the config
with its evidence.** Pinned as `netsolp_model_type: ESM1b` in `config/metrics.yaml`.

### C6 — an `ipsae.py` code-path discrepancy · **WITHDRAWN — it does not exist**

Reported as 0.8491 (AlphaFold-style JSON) against 0.8560 (npz route). Both routes agree to
five decimals per chain pair (A–C **0.823561** vs **0.823574**, the residual being 2-dp PAE
rounding). **0.8560 was the 8-seed mean** in `results/m3_winner.md`; seed 1 alone is 0.8491.

*A value quoted from a results table is an aggregate until proven otherwise — read its n.*

### C7 — shortlist single-seed reliability "0.28" · **SUPERSEDED → 0.296**

0.28 is the value under `midpoint`, quoted in a `top` context — the same convention-mixing
error the document was reporting elsewhere, made while reporting it. Note this is a
different quantity from §D2, which remains unresolved.

---

### C8 — "an anti-lysozyme antibody clears all five hard cutoffs", unqualified · **SUPERSEDED**

The project's single most-quoted finding, and for nine days it was stated as a property of
the molecule when it is a property of **the molecule and the estimator**.

| estimator | HyHEL-10 ipSAE | vs the 0.60 cutoff |
|---|---|---|
| `model_0` (argmax of 5 diffusion draws) | **0.609** | clears — all five gates pass |
| median of the same 5 draws | **0.219** | fails — §7.2's own table has ipSAE rejecting **6/6** |

Same molecule, same run, same five structures. Boltz ranks its outputs by its own
confidence and `diffusion_samples=1` keeps the top one, so `model_0` is an argmax by
construction.

**`model_0` is the right number to headline, but that has to be the argument, not an
omission.** It is what a grader following the tool's defaults actually computes, which is
exactly what makes the result a criticism *of the rubric* rather than a curiosity about one
antibody. Stated with the estimator the claim is also **stronger**, because it survives
someone re-running it; stated without, the first person to check the median concludes the
project overstated its headline.

**Where the unqualified version had spread** (found 2026-09-26 by a newline-tolerant sweep;
4 of 10 instances were unqualified):

| file | note |
|---|---|
| `PROJECT-STORY.md` | the narrative's central claim; the estimator *was* explained 12 lines below, which is not the same as being in the sentence |
| `docs/lecture/00-orientation.md` | adjacent to the `0/6` figure, which is median-derived |
| `docs/lecture/01-the-biological-problem.md` | numbered lesson list |
| `docs/lecture/README.md` | adjacent to the `0/6` figure, same mixing |

**It never shipped.** No packaged document and no deck slide contains the claim in any
phrasing, so no generator fix and no rebuild were required — checked explicitly rather than
assumed.

**The sibling figure was swept at the same time.** The `four of five gates reject 0/6`
claim is median-derived and was stated correctly everywhere, but **4 of its 13 instances
did not say so**, and one — `STATE.md` — carried *both* figures in a single sentence with
only the `model_0` half labelled. That is §C1's failure mode exactly: two rates from two
parameters, adjacent, neither named. Labelled in `STATE.md`,
`docs/lecture/09-critique.md` and `docs/lecture/05-experiment-design.md`; left unedited in
`docs/sessions/2026-09-22-...md`, which is a historical record and is covered by this
entry instead.

**Why this is its own entry rather than a footnote to §C1.** §C1 is *an error rate is a
property of a threshold*. This is *a pass rate is a property of an estimator*. Same disease,
different variable, and the project made it twice without noticing the first was a special
case — which is the argument for stating the general form: **a rate is meaningless without
the parameter it was computed at, and "which parameter" is a different question each time.**

In two of the four locations the two estimators sat in **adjacent numbered points** — `0/6`
from the median directly above "cleared all five" from the argmax, neither labelled. That
adjacency is precisely how §C1 happened, and both are now labelled explicitly.

---

### C9 — "an anti-lysozyme antibody clears all five hard gates" · **SUPERSEDED, a third time**

§C8 attached the *estimator* to this claim and stopped. The claim is also a property of the
**antigen construct**, and on the better construct it is false.

| construct | HyHEL-10 median | best of 5 | gates cleared | positive control |
|---|---|---|---|---|
| 113-mer (used first) | 0.219 | **0.609** | **5/5** | **FAILED** — nivolumab 0.017 |
| 119-mer (repaired) | 0.228 | **0.409** | **4/5**, fails ipSAE | 2/2 clear |

The 113-mer was missing 6 of nivolumab's 14 epitope residues, which is why its positive
control failed and why the panel was **pre-registered INCONCLUSIVE** — `negative_control.md:53`
says in terms that the negative arm "must not be read as evidence that the gate
discriminates." It was read that way anyway, on the front page, for days.

On the repaired construct the gate resolves cleanly: **2/2 positives clear, 6/6 negatives
fail, separated by 0.184 ipSAE**. So the flattering result and the broken positive control
had the **same cause** — a truncated antigen.

**What survives, and it is still strong:** four of the five gates reject **0 of 6** on
*both* constructs. §7.2 rests on ipSAE alone. That claim never depended on the truncation.

**What does not:** "the rubric accepts an antibody that cannot bind." It accepts one only
on a construct whose own positive control it also fails.

Also corrected by the same table: `README.md` said "even there cetuximab's median lands
**0.006** under the cutoff." That is the 113-mer figure (0.594). On the repaired construct
cetuximab's median is **0.052**, i.e. 0.548 under — the 0.006 was the flattering construct.

*The generalisation, now stated three times in three variables: a rate is a property of
every parameter it was computed under — threshold (§C1), estimator (§C8), and input
construct (§C9). Each time the project fixed one axis and assumed it had finished.*

---

## D. Flagged — known not to reproduce, deliberately not guessed at

### D1 — the course corrections file had gone stale, and self-contradictory

[C1](../docs/lecture/CORRECTIONS.md) listed the contact-count finding under *"what this does
**not** invalidate"* ("treat the 60-fold ratio as intact") while **C2, in the same file**,
refutes that finding outright. It also ended on `bb_1_0_dldesign_0` as the replacement
Challenge 2 design and called the zip stale, both overtaken. Corrected 2026-09-26.

*A corrections register is an artefact like any other and goes stale like any other.*

### D6 — the rented-GPU cost, `$2.77` vs `$2.82` · **FLAGGED**

The run write-up that owns the number says **$2.77** (`results/challenge2_pilot.md`).
**Fourteen** downstream files say **$2.82**, including `README.md`'s front page and
`docs/challenge2_regeneration_plan.md`, which calls "the pilot's $2.82 … the honest
anchor" while citing the file that says 2.77.

Neither is derivable from anything in the repo — both are bare assertions of a ~5.5 h
rental, with no rate recorded. **Not corrected, because picking one would be a guess**, and
this register exists partly to stop that. The magnitude is five cents and nothing turns on
it; what is worth recording is that a primary source and fourteen copies disagreed and the
copies won by weight of numbers.

The front page now says **~$2.80** rather than asserting a precision the record does not
support.

---

### D2 — shortlist reliability **0.629** · **RESOLVED 2026-09-28. The flag was wrong.**

This entry said the figure "does not reproduce from the recorded inputs under any standard
estimator tried", and that "the original script would settle it". **Both claims are false**,
and four documents dated 2026-09-23 had already said so — the register never absorbed them,
so `STATE.md`'s blocked list carried a work item that was already done.

**1. It reproduces. It is a *k*-seed-mean reliability, not a single-seed one.**
From the recorded components (`results/m3_winner.md` §1: between-design sd of the 7-seed
means 0.290, noise sd of a 7-seed mean 0.176):

```
r₇ = 1 − 0.176² / 0.290² = 1 − 0.030976 / 0.084100 = 0.6317      (recorded 0.629)
```

and the noise chain is internally consistent: 0.467 / √7 = 0.1765 ≈ 0.176. The 0.276/0.296
are **single-seed** plug-in estimates. Diffing them against 0.629 is the project's own
*never diff a single observation against an aggregate*, one level up: never diff two
reliabilities without checking they are reliabilities *of the same thing*.

**2. The stated blocker does not exist.** "The original script would settle it" implies it
was lost. `scripts/35_winner.py` is tracked and has been since the initial commit, and
lines 202–206 are the estimator verbatim:

```python
between  = float(np.std([r["surr_mean"] for r in rows], ddof=1))
var_noise = within7 ** 2 / s_used
rel = max(0.0, 1 - var_noise / (between ** 2))
```

`s_used` is 7. Nobody opened the file. *A blocker is a claim and decays like any other; this
one was never checked and it gated the entry for six days.*

**3. Independently recomputed from the raw folds**, 2026-09-28, replicating that estimator
read-only over `runs/designs_reseed7` + seed 1, 20 designs × 7 seeds, fresh seed 23 excluded:

| quantity | recomputed | recorded |
|---|---|---|
| reliability of a 7-seed mean | **0.660** | 0.629 |
| implied single-seed reliability | **0.217** | 0.276 / 0.296 |
| within-design sd | 0.226 | 0.467 |
| between-design sd of 7-seed means | 0.147 | 0.290 |

**The sds are ~2× smaller and that is expected, not a discrepancy:** they were computed
under the pre-2026-09-22 surrogate anchors (2.5 / 7.0 / 9.5) and today's config is `top`
(5 / 8 / 10). Reliability is a ratio and survives the rescale; an sd does not. So "does not
reproduce" was true of the *standard deviations* and never of the *reliability*.

---

**What survives, narrower, and now quantified.** The recorded single-seed figures are
inconsistent with the same variance components. Spearman–Brown, both directions:

```
r₁ = 0.296, k = 7  ⇒  r₇ = 0.746   (recorded r₇ = 0.629)
r₇ = 0.629, k = 7  ⇒  r₁ = 0.195   (recorded r₁ = 0.296)
```

and the components imply r₁ = 0.053124 / (0.053124 + 0.467²) = **0.196** directly, matching
the back-implication rather than the record. Recomputed from raw folds: **0.217**. So
**0.296 is the outlier, adrift by roughly +0.08 to +0.10**, and the inconsistency is
one-sided rather than a two-way puzzle.

**And 0.276/0.296 have no provenance.** `grep -rn "0\.296\|0\.276" scripts/ src/` returns
nothing: no code computes them. They were produced in prose during the 2026-09-22 audit.
*A figure that lives in prose and never in a data file has no provenance* — the register's
own §C1 lesson, and it was the number used to challenge a figure that a tracked script
does compute.

**Status:** 0.629 stands as the 7-seed-mean reliability and is correct for its one use,
shrinking a 7-seed mean. Anything quoting 0.276/0.296 as *the* single-seed reliability
should read **≈0.20** with the caveat that no script produces any of the three.

**Live text:** `STATE.md`, `PLAN.md`, `docs/lecture/04-measurement-theory.md:470`,
`docs/lecture/08-what-broke.md:454` (X5, which still says "does not reproduce and has never
been corrected").

### D3 — `results/rubric_headroom.md` · **FLAGGED, does not ship**

Generated by `scripts/40_rubric_headroom.py` under **midpoint** bands (9.5/7.0/2.5, max
95.0) while `config/metrics.yaml` declares `band_value: top`, and it quotes a design at
`dockq 0.747`. Regenerate under `top` or retract explicitly. It does not ship, which is why
it has survived this long.

### D4 — the patch null is not shape-matched · **RESOLVED 2026-09-28. Quantified: +0.019.**

The flag was correct and is now measured rather than estimated.
`scripts/94_shape_matched_patch_null.py` re-runs the null with patches
**rejection-sampled to match the epitope's own RMS spread** (±0.5 Å), on the same 18
backbones, same statistic, no new folds and no GPU.

First, it **reproduces the flagged figures, which until now existed only in prose** —
neither 7.73 nor 10.08 was computed by any script in this repo:

| | prose | recomputed |
|---|---|---|
| epitope RMS spread | 10.08 Å | **10.09 Å** |
| compact-patch RMS spread | 7.73 Å | **7.76 Å** |
| shape-matched RMS spread | — | **10.10 Å** (matching achieved) |

**The mismatch was worth +0.019 on the null's mean** — 0.153 compact → 0.172
shape-matched, against a real value of **0.712**. So the defect was real, its direction was
as flagged (anti-conservative in the mean), and it was **never carrying the result**: the
gap to beat is 0.54.

**What did not hold is the tail story.** A first draft of this write-up asserted that
matching thins the null's upper tail and that "every p-value falls". The distribution table
printed directly above it says otherwise: sd falls (0.185 → 0.155) but p99 and max both
**rise** (0.554 → 0.605, 0.602 → 0.788), and per backbone **12 p-values rose, 4 fell, 2 were
unchanged** — mostly the way a higher null mean predicts. The claim was corrected before it
shipped, by reading the numbers under it. *Same defect as §C1's: a mechanism that sounds
right, in a sentence next to the table refuting it.*

**Net effect on the conclusion: it strengthens.** `bb_3_0.pdb` was the single backbone
failing the old null at α = 0.05 and moves **p 0.0730 → 0.0115**, so the count goes
**17/18 → 18/18**. That is a result moving in our own favour on one marginal case, which is
the direction deserving most suspicion, so the full distribution is reported rather than the
headline count.

The honest statement is now *"a 26-residue patch elsewhere on the same chain, matched to the
epitope in both size and RMS spread"*.

### D5 — "`interaction_pae` CANNOT rank, ICC 0.000" · **FLAGGED, softened**

Too strong as stated. Retained in the record as softened rather than deleted; the
distinguishing experiment (sequencing the 18 unconditioned backbones, ~2–4 GPU-hours) has
not been run.

---

## What the register is for

Two of the entries above exist only because a claim was recomputed rather than copied
(§C1, §C3), and one because a *correction* was audited (§C7, §D1). The register is cheap to
extend and the pattern it makes is the point: **this project's errors cluster in the
sentences it had already written down**, not in the code. Nine of the twenty-odd entries
here were found by an audit of prose, not by a failing test.

Three of them now have mechanisms and cannot recur silently — §A1 (`--json` plus
`rounding_risk`), §C1/§C2/§C3/§C4 (`check_docs_against_scores`, which cross-checks every
number a packaged document asserts against a recomputation from the package itself), and
§A2 (the MSA-length and stdout guards in `tests/test_invariants.py`). The rest are knowledge,
and knowledge is what this file is holding.
