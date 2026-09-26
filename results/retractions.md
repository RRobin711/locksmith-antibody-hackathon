---
date: 2026-09-26
tags: [project, locksmith, learning, problem]
status: living
---

# Retraction register — every claim this project withdrew

**One fact, one place.** A claim that has been withdrawn, refuted or superseded is recorded
here with the number that replaced it and the file that settles it. Chapters, results files
and session docs are **not** retro-edited into agreement; that is the defect the project
documents (see [[../docs/lecture/08-what-broke|the generated-artefact failure classes]]).
Where a document still carries retracted text it is named in the **live text** column, so
the register is a work list rather than a monument.

This file exists because "the five stale-document retractions and four overstated claims"
had been carried as a *pointer* in three consecutive session docs without anyone ever
enumerating them. A retraction that is only gestured at cannot be checked off, and
`STATE.md` could not be cleaned while the list did not exist.

**Scope.** The whole project. [[../docs/lecture/CORRECTIONS|the course's own corrections file]] is narrower — it covers what a reader of the lecture course must not trust — and its
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

**Live text:** none known.

### A2 — every Challenge 2 number before 2026-09-23 · **WITHDRAWN**

Boltz compares the MSA's query length to the input chain and, on mismatch, **discards the
alignment and folds single-sequence**, announcing it only on stdout, which the harness
captured and threw away. Every Challenge 2 fold paired a **123-residue** antigen with a
**113-residue** cached alignment. Measured 2×2 on ipSAE in
[[msa_silently_discarded|the 2×2 that isolates the alignment]]: with a correct alignment
**0.012** both pre- and post-fix; without, **0.773 / 0.686**.

Specifically withdrawn: **"1 of 30 designs clears"** as measured then; **ipSAE 0.864** for
`bb_2_0_dldesign_1`; and **composite 91.2** as evidence about a molecule.

**Superseded twice, which matters.** The re-screen against a correct alignment promoted
`bb_1_0_dldesign_0` (**0.637**, previously ranked 29th of 30) while the packaged design fell
to **0.013** from 1st — the ranking was close to inverted, not merely noisy. That design was
then itself superseded by the constrained re-design campaign, and the shipped Challenge 2 is
now **`bb_8_0`**, ipSAE **0.904** on `model_0` (median of 5 diffusion samples **0.859**),
composite **93.6**, viable 5 of 5.

**Live text:** [[../docs/lecture/CORRECTIONS|the course corrections file]] §C1 still ends on
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
Evidence: [[m3_shortlist_depth|the allocation simulation]].

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
Evidence: [[ch1_ng_and_light_chain_2026-09-22|the light-chain sweep]].

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
Evidence: [[liability_fix_arms|the fix arms]], [[two_findings_from_the_matched_control|the matched control]].

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
Evidence: [[audit_2026-09-20|the checks that found both]].

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
not the test.* Evidence: [[g3_outcome_variable|the six-outcome re-run]].

### B8 — "depth rescues backbones" and "bb_17_0 is a genuinely good backbone" · **WITHDRAWN**

144 folds, 18 backbones × 8 constrained sequences. Coverage grew 4 → 8 of 18 against a
homogeneous binomial's expected **5.3** and **9.0**: the growth is an order statistic
behaving as a flat rate predicts. Per-stratum rates **5.6%** vs **11.1%**, Fisher exact
**p=0.367**. No overdispersion (χ² = 22.91 on 17 df, p=0.152; beta-binomial LRT p=0.202).
For bb_17_0, P(≥3 clears in 8) = 0.0235, so the expected count over 18 backbones is **0.42**
and we saw 1.

Both are the same error — reading structure off small counts without asking what a
structureless model predicts — and it is the **third** instance on this project, after B7
and the n=8 heterogeneity null. Evidence: [[depth_sweep|the depth sweep]].

### B9 — fold batching · **SUPERSEDED, then DISQUALIFIED**

Costed at "~1.8×" from an unmeasured split between per-fold and per-invocation time, and
that projection justified scheduling decisions for two days. Built and measured: **1.16×**
(84 s → 72 s per fold), saving 0.8 h on a 239-fold arm rather than 2.4 h.

A separate throughput arm later measured batching at **1.65×** and **disqualified it
outright**: Boltz pads a batch to its longest sequence, so a design's score depends on which
other designs share its batch. Only 1 of 4 structures was byte-identical to its serial
reference; ipSAE moved up to **0.30** and atoms by **72–89 Å**. Staggering gives 1.30× and
is byte-identical 4 of 4, below the pre-registered 1.5× bar, so folding runs serially.

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

This is the same family as [[../docs/lecture/08-what-broke|the silent-failure classes]] —
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

## D. Flagged — known not to reproduce, deliberately not guessed at

### D1 — the course corrections file had gone stale, and self-contradictory

[[../docs/lecture/CORRECTIONS|C1]] listed the contact-count finding under *"what this does
**not** invalidate"* ("treat the 60-fold ratio as intact") while **C2, in the same file**,
refutes that finding outright. It also ended on `bb_1_0_dldesign_0` as the replacement
Challenge 2 design and called the zip stale, both overtaken. Corrected 2026-09-26.

*A corrections register is an artefact like any other and goes stale like any other.*

### D2 — shortlist reliability **0.629** · **FLAGGED**

Does not reproduce from the recorded inputs under any standard estimator tried: the plug-in
variance ratio gives **0.276** under `midpoint` and **0.296** under `top` (scale-invariant,
as it should be). The original script would settle it; guessing would add a fifth number.

**Live text:** `STATE.md`, `PLAN.md`, `docs/lecture/04-measurement-theory.md:470`. Each
should carry the flag until the script is found or the figure recomputed.

### D3 — `results/rubric_headroom.md` · **FLAGGED, does not ship**

Generated by `scripts/40_rubric_headroom.py` under **midpoint** bands (9.5/7.0/2.5, max
95.0) while `config/metrics.yaml` declares `band_value: top`, and it quotes a design at
`dockq 0.747`. Regenerate under `top` or retract explicitly. It does not ship, which is why
it has survived this long.

### D4 — the patch null is not shape-matched · **FLAGGED**

The contiguous surface patches are **more compact** than the real epitope: mean RMS spread
**7.73 Å** for a drawn patch against **10.08 Å** for the PD-L1 footprint (uniform draws:
13.21 Å). The right *family* of null — clearly compact rather than scattered — but not size-
and-shape matched, which plausibly makes the test **anti-conservative by an unquantified
amount**. It does not overturn the result (17/18 backbones beat their null, 0.712 vs 0.154).
The honest statement is *"a compact 26-residue patch elsewhere on the same chain"*, not
*"an epitope-like patch elsewhere"*.

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
