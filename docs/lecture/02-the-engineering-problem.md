---
date: 2026-09-23
tags: [project, lecture, learning, coding, python, pattern]
status: review
---

# 02 — The Engineering Problem

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1, C2 and C3](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding, and **C3 applies to Challenge 1**: its composite is **94.0**, not the 96.0 this course derives in several places. Challenge 1 is unaffected *by the alignment defect*, which is narrower than "unaffected".

**What this chapter teaches.** How to build a system that turns a prose rubric into a number you can
defend. We work through the five-stage pipeline and the contract each stage signs; then we spend the
bulk of the chapter on the scoring harness, which is the project's central artefact — the eight
metrics, their bands, the composite formula with the arithmetic worked out digit by digit, and the
twelve-point ambiguity hiding inside a phrase like "Good (9-10)". Then two engineering lessons that
generalise far beyond antibodies: **programs that exit 0 having done the wrong thing**, catalogued
with mechanisms; and **a configuration value and a hardcoded constant encoding the same convention**,
which reordered the project's own winner in a way that looks impossible until you see why it isn't.
We close on reproducibility engineering, and on the ratio that characterises the whole codebase:
roughly 53% of the code exists to check the other half.

The biology this system is scoring is in [the biology chapter](01-the-biological-problem.md); the
individual tools and their gotchas are in [the toolchain chapter](03-the-toolchain.md). No prior
exposure to either is needed here.

**Scale, for orientation.** 18,020 lines of Python across `src/`, `scripts/` and `tests/`; 3,407 of
them in the `src/locksmith/` library, 14,095 in 86 numbered driver scripts, 518 in a single test
file with 26 test functions collecting 30 cases. 33 modules under `src/locksmith/`. 442 lines of
shell. 165,333 words of documentation across 22 session docs, 62 results files (11 of them
pre-registrations), 13 knowledge notes and 6 root documents. Version control arrived on **day 9 of
9** with a first commit of 12,430 lines; 35 commits total.

---

## 1. The brief, as an engineering problem

The organisers hand over a PDF handbook and take back, per challenge, **three files** —
`design_X_complex.pdb`, `design_X_pae.json`, `design_X.fasta` — inside a fixed directory tree, plus
a pitch deck (`src/locksmith/submit/package.py:9-20`, quoting handbook §4.1). They then recompute
eight numbers and combine them.

One structural observation determines the whole architecture (`PLAN.md:19-23`):

> **Six of the eight scored metrics are computed from the two files we hand over.**
> `design_X_complex.pdb` and `design_X_pae.json` are the sole inputs to ipSAE, DockQ, ΔG, contacts,
> interface pLDDT and CDR SASA. **The organisers do not re-fold our designs.** Only NetSolP and
> CDR-H3 identity are derived from sequence.

Two consequences follow, opposite in sign.

**The structure predictor is not infrastructure; it is a scored component** (`PLAN.md:28-31`).
Choosing it and configuring it is a first-class design decision, on the same footing as choosing the
sequence. If [Boltz-2](03-the-toolchain.md#31-boltz-2-the-primary-predictor) produces an optimistic pose, that optimism is *in the submitted file* and is
what gets graded.

**The evaluation is deterministic given our files.** Nothing the organisers do introduces variance.
This is what kills the project's original margin rule (§7) and it is what makes the artefact-only
validator (§9) possible at all: if an evaluator's numbers are a pure function of the package, you
can reproduce them exactly from the package.

A third fact shapes selection: **eight hard cutoffs, all must pass, one submission per challenge**
(`PLAN.md:45-56`). Failing any one ranks you below every viable design. So the objective is not
"maximise expected score" but

> maximise score **subject to** every gate clearing by a margin larger than our own reproduction
> error.

That is a constrained optimisation over a discontinuous objective, which is why
[the selection chapter](06-allocation-and-selection.md) spends so long on it.

---

## 2. The pipeline and its contracts

```
 generate ──► fold ──► score ──► select ──► package ──► validate
 (sequence/  (coords  (8 raw    (rank +   (handbook  (re-derive
  backbone)   + PAE)   numbers)  gates)    §4.1 tree) from files)
```

| stage | input contract | output contract | why it must be a separate stage |
|---|---|---|---|
| **generate** | a parent backbone (5GGS) or an epitope spec | `Design` rows with provenance stamped at creation — seed, temperature, parent, generator | provenance "cannot be reconstructed after aggregation" (`BUILD.md` §1) |
| **fold** | `Design` | `FoldResult{pdb, pae, plddt, seconds, chain_lengths}` — *paths in place, never copied or renamed* (`src/locksmith/fold/__init__.py:18-25`) | the only expensive step (~95% of compute); must be resumable and content-keyed |
| **score** | `(pdb, pae, fasta)` | **raw values only** — no banding, no verdicts | several scoring conventions were unresolved; a convention change must cost a re-run of the scorer, not a re-fold |
| **select** | raw values + config | a ranking plus a viability verdict | ranking and reporting use *different scales* — a continuous surrogate versus the banded rubric (§8) |
| **package** | the chosen design | the handbook §4.1 tree, asserted **on the bytes written** | "submissions not following the exact structure will fail automated validation and may be disqualified" |
| **validate** | **the package and nothing else** | exit 0, or exit 1 naming the violated handbook section | a check that reuses pipeline state proves nothing about what an evaluator sees |

The load-bearing architectural rule is stated in `BUILD.md` §1 and implemented at
`src/locksmith/score.py:1-7`:

> **Metrics derived on demand, never stored.** … changing a convention in `config/metrics.yaml` and
> re-running costs seconds rather than a re-fold. That is the single most important architectural
> property of this file.

`PLAN.md:539-547` prices it. If a convention is baked into a stored result and turns out wrong, "we
re-fold everything and lose a day"; if metrics are derived on demand, the same discovery costs "a
10-second re-run". Disk was 776 GB free; **GPU-hours were the scarce resource**, so the right thing
to store is the *input* to a convention, never its output. This is the single cheapest architectural
decision in the project and it paid off at least five times — every entry in §6 below.

`score.py` and `select/surrogate.py` are therefore **pure functions of (raw values, config)**, and
`fold/__init__.py` holds the artefact contract that every driver and both batch paths route
through, so that "a fold happened" has exactly one definition in the codebase.

---

## 3. `config/metrics.yaml`: the rubric as data

The file is 182 lines and is the rubric encoded as data rather than as code. Its own header states
the rationale (`config/metrics.yaml:1-5`):

> Five conventions are NOT specified by the handbook. They are switches here, not constants in code,
> so that resolving one costs a re-run of `06_score.py` rather than re-folding every design.

(By the end it was seventeen keys, not five; the principle scaled.)

### 3.1 The eight metrics

All eight band triples and all eight minimums were later verified against the handbook PDF directly
in `results/handbook_conformance.md` §1, with the verdict **MATCH** on all sixteen.

| metric | direction | good | medium | hard cutoff | strict edges | challenges | needs |
|---|---|---|---|---|---|---|---|
| `ipsae` | high | 0.80 | 0.60 | 0.60 | — | 1, 2 | PAE |
| `dockq` | high | 0.80 | 0.49 | 0.23 | — | **1 only** | reference structure |
| `dg` (kcal/mol) | low | −12.0 | −10.0 | −6.0 | — | 1, 2 | — |
| `contacts` | high | 25 | 15 | 10 | `strict_good` (`> 25`) | 1, 2 | — |
| `iface_plddt` | high | 80 | 70 | 65 | `strict_good` (`> 80`) | 1, 2 | pLDDT |
| `cdr_sasa` (Å²) | high | 600 | 300 | 250 | `strict_good` (`> 600`), `strict_cutoff` (`> 250`) | 1, 2 | — |
| `netsolp` | high | 0.70 | 0.50 | 0.50 | — | 1, 2 | — |
| `cdrh3_identity` (%) | low | 70 | 90 | 95 | `strict_good` (`< 70`), `strict_cutoff` (`< 95`) | 1, 2 | — |

Note two degeneracies that later caused a real bug: `ipsae` and `netsolp` have `cutoff == medium`
(0.60/0.60 and 0.50/0.50), so the *lower* interpolation span is zero.
`select/surrogate.py:108-124` handles this explicitly and records that getting it wrong "scored a
design sitting exactly on `good` as 7.0 instead of 9.5".

**Weights** (`config/metrics.yaml:84-87`): `binding: 0.60`, `developability: 0.20`, `novelty: 0.20`.

**Categories** (`:172-175`): binding = `[ipsae, dockq, dg, contacts, iface_plddt, cdr_sasa]`;
developability = `[netsolp]`; novelty = `[cdrh3_identity]`.

Read those two blocks together and the structural consequence jumps out: **developability and
novelty are each a single metric carrying a full 0.20 weight**, while binding's 0.60 is split six
ways. That asymmetry drives everything in §5.

**Margin** (`:93`): `margin_fraction: 0.20`.

### 3.2 The composite formula

Handbook §5.2, transcribed at `docs/sessions/2026-09-14-...:144-146`:

```
Final Score (0–100) = [ 0.60 × Binding_struct + 0.20 × Developability + 0.20 × Novelty ] × 10
```

Each category is the **unweighted mean of its members' 0–10 sub-scores**. Challenge 1's binding mean
is over **six** metrics; Challenge 2's over **five**, because [DockQ](03-the-toolchain.md#41-dockq-213-two-flags-that-both-default-wrong) is excluded. Implemented at
`src/locksmith/score.py:76-84`:

```python
for cat, members in cfg.categories.items():
    present = [s.sub[m] for m in members if m in s.sub]
    if present:
        s.categories[cat] = sum(present) / len(present)
...
s.final = round(sum(cfg.weights[c] * v for c, v in s.categories.items()) * 10, 2)
```

`results/handbook_conformance.md` §9 verifies both arities empirically, and confirms that **a
missing DockQ is never counted as a zero** — it is dropped from the mean, not scored 0.

A mathematical consequence worth naming before we do arithmetic: because a category is a *mean*, it
is dragged down by its worst member. **Optimise the minimum**, not the average. Effort spent
improving a metric that is not the current argmin of its category is wasted, and effort on the argmin
is wasted past the point where it stops being the argmin.

### 3.3 Worked arithmetic: how a design reaches 94.0

> **Recomputed 2026-09-28.** This section derived **96.0** from a `dockq` row reading
> `0.800 | good | 10.0`, until the rounding defect in
> [C3](CORRECTIONS.md#c3--challenge-1s-composite-is-940-not-960) was found. It is the
> **one** place in this course rewritten rather than indexed, because a worked derivation
> is arithmetic a reader reruns — leaving it would have taught both the wrong sum *and*
> the rounded parse that produced it. Prose elsewhere is unchanged and indexed in C3.

Challenge 1, design `mpnn_T0.5_s104_036` with the `N55Q` [deamidation](01-the-biological-problem.md#62-the-ng-deamidation-motif-in-challenge-1s-cdr-h2) fix, folded on the handbook
§4.2.2 constructs under conventions `band_value=top`, `dockq_interface_agg=global`,
`netsolp_construct=fv`, `netsolp_chain_agg=min` (`submission/.../Challenge1/metrics/scores.md`):

| metric | raw value | band | sub-score |
|---|---|---|---|
| `cdr_sasa` | 1596.500 Å² | good | 10.0 |
| `cdrh3_identity` | 38.500 % | good | 10.0 |
| `contacts` | 97 | good | 10.0 |
| `dg` | −13.300 kcal/mol | good | 10.0 |
| `dockq` | 0.799579 | **medium** | 8.0 |
| `iface_plddt` | 88.630 | good | 10.0 |
| `ipsae` | 0.821 | good | 10.0 |
| `netsolp` | 0.569 | **medium** | 8.0 |

Category means. `binding` is the six metrics `[ipsae, dockq, dg, contacts, iface_plddt,
cdr_sasa]` (`config/metrics.yaml:181`), so the `dockq` band change moves one term of six:

- binding = (10.0 + **8.0** + 10.0 + 10.0 + 10.0 + 10.0) / 6 = 58/6 = **9.667**
- developability = 8.0 / 1 = **8.000**
- novelty = 10.0 / 1 = **10.000**

Composite:

```
final = (0.60 × 9.667 + 0.20 × 8.000 + 0.20 × 10.000) × 10
      = (5.800       + 1.600        + 2.000        ) × 10
      = 9.400 × 10
      = 94.0
```

**Read the `dockq` row carefully — it is why this section changed.** The true
`GlobalDockQ` is `0.7995794972281312`, which is **0.00042 below** the §5.2 Good edge at
0.80 and therefore bands `medium`. `dockq.compute` used to parse DockQ's *printed* summary
line, which the tool formats to 3 dp, and `0.800` bands `good`. Two of this design's points
came from a `printf`, in a course whose central argument is that the rubric is gameable by
whoever controls the structure. The value is printed at 6 dp here for the same reason the
packaged `scores.md` prints it that way: *when a number sits within its display precision of
a decision boundary, print more digits, not fewer.*

> **The Challenge 2 half below is superseded, and is left as written.** Its arithmetic is
> correct for the design it names; the *design* is withdrawn. `bb_2_0_dldesign_1` was folded
> against a silently discarded antigen alignment and falls from ipSAE 0.864 to 0.013 under a
> correct one — see [C1](CORRECTIONS.md#c1--challenge-2s-computational-evidence-is-withdrawn).
> The packaged Challenge 2 design is now `bb_8_0` at **93.6**. Unlike §3.3's Challenge 1
> derivation, nothing here teaches a wrong operation, so it is indexed rather than rewritten.

And the Challenge 2 design, `bb_2_0_dldesign_1` with the S→A sequon fix, on **seven** metrics:
`cdr_sasa` 1066.500 good 10.0 · `cdrh3_identity` 30.000 (germline) good 10.0 · `contacts` 97 good
10.0 · `dg` −11.000 **medium 8.0** · `iface_plddt` 85.170 good 10.0 · `ipsae` 0.781 **medium 8.0** ·
`netsolp` 0.570 medium 8.0.

- binding = (10 + 10 + 8 + 10 + 8) / 5 = 46/5 = **9.200**
- developability = **8.000**; novelty = **10.000**

```
final = (0.60 × 9.200 + 0.20 × 8.000 + 0.20 × 10.000) × 10
      = (5.52        + 1.60         + 2.00         ) × 10
      = 91.2
```

Notice what you can read off the arithmetic. One metric slipping from Good to Medium inside
Challenge 1's *binding* category costs (10−8)/6 × 0.60 × 10 = **2.0 points** — which is
exactly the 96.0 → 94.0 this section was recomputed to, and a useful check that the
correction is the one term it claims to be, not a rescore. The same slip on
`netsolp` costs (10−8)/1 × 0.20 × 10 = **4.0 points**, and on `cdrh3_identity` likewise 4.0 — twice
as much, because those categories have one member each. This is not a quirk; it is the rubric's
stated priorities made visible by doing the division.

---

## 4. The band→score ambiguity: 84.0 / 90.0 / 96.0

This is the sharpest "the specification is underdetermined" problem in the project, and the way it
was handled is the model to copy.

Handbook §5.2 gives band **ranges** only — **"Good (9-10)", "Medium (6-8)", "Poor (0-5)"** — and
never says how to pick a value inside one. Three readings are implementable from the text alone
(`src/locksmith/config.py:102-106`):

```python
BAND_VALUES = {
    "bottom":   {"good": 9.0,  "medium": 6.0, "poor": 0.0},   # caps the maximum at 90
    "midpoint": {"good": 9.5,  "medium": 7.0, "poor": 2.5},   # caps it at 95
    "top":      {"good": 10.0, "medium": 8.0, "poor": 5.0},   # the only one that reaches 100
}
```

A fourth reading — interpolating *within* a band on the raw value — is equally permitted by the text
and is **not implemented**, because it needs an upper anchor (what raw value maps to 10?) that the
handbook never gives (`config.py:97-99`). Saying so is better than inventing one.

The finalist under all three:

- **top**: binding 10.0, dev 8.0, novelty 10.0 → (6.00 + 1.60 + 2.00) × 10 = **96.0**
- **midpoint**: binding 9.5, dev 7.0, novelty 9.5 → (5.70 + 1.40 + 1.90) × 10 = **90.0**
- **bottom**: binding 9.0, dev 6.0, novelty 9.0 → (5.40 + 1.20 + 1.80) × 10 = **84.0**

**A 12-point swing on a 0–100 scale, determined entirely by a reading of prose.** For the
DockQ-Medium variant (`global` on the coordinate construct = 0.755, or any `min` reading), binding
under `top` is (10+8+10+10+10+10)/6 = 9.6667 and the final is (0.6 × 9.6667 + 1.6 + 2.0) × 10 =
**94.0**; under midpoint **87.5**; under bottom **81.0**. That is why `results/m3_winner.md` §6
reports `final = 87.5`: it predates the convention change and is superseded rather than
wrong-at-the-time.

**Why `top` was chosen** (`config/metrics.yaml:7-18`): handbook §7.3 states the Challenge score
range as **"0 - 100"**, and only `top` attains it — midpoint caps at 95, bottom at 90. And then, in
the same comment block, the project argues against its own default: `"0 - 100"` is *"a scale label,
not a claim that 100 is attainable"*; `top` is *"also the most flattering reading, awarding 10/10 to
a metric that merely clears the Good edge"*; and within-band interpolation is a fourth reading the
text permits equally. **The mitigation is to report under all three and never quote one alone.**

That last move is the transferable one. When a specification is genuinely ambiguous, the choice is
not between "pick one and hope" and "refuse to score". It is: implement every defensible reading,
make the choice a named switch, attach the evidence for and against it in the same place, and report
the spread. The cost of reversing the decision is then one re-run of the scorer — measured in
seconds — instead of one re-fold of 239 designs, measured in hours.

---

## 5. Why five unspecified conventions became switches, not constants

`config/metrics.yaml:6-82` encodes each place the handbook is silent as a switch **with its evidence
attached**. The full list of seventeen keys, with the interesting ones annotated:

- `band_value: top` — §4 above.
- `cdr_sasa_chains: AB` — all six CDRs versus heavy-only. Costs 0 points here: 1544.6 Å² versus
  1565.0 Å², Good either way.
- `cdr_sasa_state: bound` — **UNRESOLVED.** `sasa.py` computes *both* `cdr_sasa_bound` and
  `cdr_sasa_unbound` (and `cdr_sasa_buried` as the difference); config picks. Worth noting that the
  two conventions **conflict in sign with the contacts metric**: a better-buried interface means
  more contacts but *less* bound CDR SASA.
- `submission_form: fab` — UNRESOLVED; the handbook's example FASTA is Fab-length.
- `ipsae_pae_cutoff: 10`, `ipsae_dist_cutoff: 15`, `ipsae_row_type: max`.
- `numbering_scheme: imgt` — see [why the scheme is part of the metric](01-the-biological-problem.md).
- `interface_dist_cutoff: 5.0` Å heavy-atom.
- `dockq_allowed_mismatches: 40`, `dockq_chain_mapping: ABC:ABC`, `dockq_interface_agg: global`
  (default **changed 2026-09-20** from `min`; the aggregation choice is worth a full band and
  +2.5 final points under midpoint).
- `netsolp_model_type: ESM1b` — **RESOLVED 2026-09-16 by a positive control.** ESM12 (0.379/0.346)
  and ESM1b-distilled (0.463/0.491) both **fail pembrolizumab** against the 0.50 cutoff; the ESM1b
  5-fold ensemble passes under every construct convention (0.569–0.733). Costs ~11 s/sequence versus
  ~2 s, paid on CPU off the GPU critical path.
- `netsolp_construct: fv` — RESOLVED 2026-09-20; the handbook says Fv twice. **This flips which
  chain limits**: pembrolizumab Fv gives VH 0.733 / VL 0.569 (light limits) versus Fab 0.623 / 0.626
  (heavy limits) — and flipping it inverted a whole project recommendation.
- `netsolp_chain_agg: min` — "a design is only as soluble as its worst chain."
- `selection_key: final`; `selection_tiebreak: [dockq, cdrh3_identity]`.

**The economics.** Every one of these is a decision that, encoded as a Python constant, would be
discovered wrong only after a lot of compute had been spent under it — and would then require
re-folding to undo, because the wrong convention would be baked into stored results. Encoded as
config, with the metrics derived on demand, the discovery costs a re-score. Four of them actually
did change during the project (`band_value`, `dockq_interface_agg`, `netsolp_model_type`,
`netsolp_construct`) and none of them cost a fold.

**The transferable principle: encode the specification as data, with its ambiguities as switches and
its evidence attached.** The YAML carries the handbook quote, the alternatives, the measured cost of
each reading, and the date each was resolved. That turns a config file into a decision log that
cannot drift from the running system — and it is why the project could answer "what would this score
under the other reading?" in ten seconds.

---

## 6. Build the judge before the contestant

`README.md:176-181`: *"Build the judge before the contestant: the first gate is our harness scoring
pembrolizumab itself correctly."* Gate 0 in the plan reads: "Harness reproduces ground truth;
pembrolizumab passes every binding gate and fails novelty; decoy rejected."

Why this ordering is mechanically correct, not merely tidy: every downstream decision — which
designs to fold, which to keep, which to ship — is a comparison against a threshold. If the
thresholds are mis-transcribed, every one of those decisions is wrong and **nothing else in the
system can detect it**. There is no crash available for a threshold that is 0.70 when it should be
0.80. The harness is also the only component whose ground truth is available on day one:
pembrolizumab bound to PD-1 (5GGS) is a solved complex whose correct answer is known.

**What it bought, concretely.**

*The canary works in both directions.* **Pembrolizumab itself scores 76.0 and is NON-VIABLE**,
because 100% CDR-H3 identity to itself fails the novelty gate (`README.md:157`). A harness that
returned "viable" for the reference molecule would have been silently mis-specified. `BUILD.md` §8
makes it an assertion rather than a manual check: *"`score.py` on the native 5GGS **must** return
viable. Wire it as a test, not a manual check."* — and the eventual test,
`test_pembrolizumab_fails_challenge1_novelty_and_passes_challenge2`, encodes the gate in both
directions, because the Challenge 2 germline reference must *pass* pembrolizumab at 53.8%.

*Fix the expectation, not the code.* The first calibration run printed
`[FAIL] native pembrolizumab ... failing: cdrh3_identity`, and the correct response was to change
the *expectation*: pembrolizumab must fail novelty, because it is the molecule you are not allowed
to copy. The rewritten assertion — passes all binding gates **and** fails novelty — is strictly
stronger than the one it replaced.

*Three-valued viability.* With [ipSAE](03-the-toolchain.md#43-ipsae-interface-confidence-from-the-pae), interface pLDDT and [NetSolP](03-the-toolchain.md#44-netsolp-10-sequence-only-solubility-and-a-positive-control-that-chose-the-model) unmeasurable at that point, the
harness reported viability **UNKNOWN**, not `True`. Returning "viable because nothing measured
failed" is the bug. `score.py:71-74` makes this structural: a missing metric yields `viable=None`,
never `True`, and `final` is withheld unless every category is present. `select.rank` then partitions
UNKNOWN out with the non-viable rather than optimistically including it.

*The gates do not bite on fixed-backbone redesign.* The 20-design baseline arm — plain [ProteinMPNN](03-the-toolchain.md#21-proteinmpnn)
at T=0.1, no filtering, no reranking, no cherry-picking — had **20/20 clear all eight gates**. That
is a real, slightly deflating piece of information: for Challenge 1 the hard cutoffs are not the
binding constraint, so any claim that a clever filter "produced viable designs" has to beat 100%
baseline viability, not 0%.

*Four known-answer subjects, one of which must fail.* 5GGS A/B/Z must pass every binding gate;
5GGS C/D/Y must agree with it; 5WT9 nivolumab must look like a genuine binder; and a **deliberate
decoy** — pembrolizumab paired with the PD-1 copy it does *not* touch — **must be rejected**.
*"Showing your measurement gives good scores to good things is only half a validation."* Three of
the project's eight catalogued [silent failures](08-what-broke.md#class-1-silent-failures) were caught *only* because the harness was running on
structures whose answers were known.

What Gate 0 did **not** buy is equally important and the project says so: the real negative control
— a real antibody against an unrelated target, docked onto PD-1 — "costs eight folds and nobody ran
it for a week". When finally run, HyHEL-10 (anti-lysozyme) cleared all five hard cutoffs on
`model_0`. That story is in [the biology chapter's closing section](01-the-biological-problem.md) and
[the critique](09-critique.md).

---

## 7. Two calibration decisions: strict edges, and a margin rule justified wrongly

**Boundary inclusivity.** `src/locksmith/config.py:34-48` implements `band_of` with strict or
inclusive edges read from config. The handbook writes four Good edges with **strict** inequalities
(`> 25` contacts, `> 80` interface pLDDT, `> 600` Å² CDR SASA, `< 70%` identity) and two viability
cutoffs likewise. Treating them as inclusive "scores a boundary value one band too high", worth
**5.0 final points** on `cdrh3_identity`, because novelty carries the full 0.20 weight on a single
metric and a 10-residue CDR-H3 with 7 matches is *exactly* 70.0%. This was found on 2026-09-20 by an
independent audit; **previously every edge was inclusive.** `results/handbook_conformance.md` §2 now
tabulates all 16 band edges plus 8 minimums and reports **24/24 MATCH** at the exact edge value.

**The margin rule, and why its original justification was wrong.** The original rule (`PLAN.md:650-676`)
was: "≥2σ margin on every gate because our estimates will not agree with the organisers' run." That
reasoning is simply false — *the organisers do not re-fold.* Given the same PDB and PAE, ipSAE,
DockQ, [PRODIGY](03-the-toolchain.md#42-prodigy-240-δg-and-contacts) and SASA are deterministic. What actually varies between our run and theirs is
**implementation**: tool version, numbering scheme, SASA probe radius, bound versus unbound, chain
pairing. That is reducible by *pinning*, not by margin.

And the rule was self-defeating on its own terms: 2σ on ipSAE (σ ≈ 0.10–0.20) above the 0.60 gate
demands 0.80–1.00 on every metric simultaneously. *"A constraint that nothing satisfies is not a
constraint, it is a bug."* Replaced by `margin_fraction: 0.20` — clear each gate by 20% of the
cutoff→good span — with cross-predictor spread moved into the evidence dossier "for truth, not
margin".

The principle: **size a safety margin against the source of variation that actually exists.** Here
the variation is convention and version risk, not prediction noise, and those have different
remedies.

---

## 8. `selection_key`: why rank on the composite and not on DockQ

DockQ is the only metric that compares a prediction to something external, so the intuitive move is
to rank on it. The arithmetic says otherwise (`config/metrics.yaml:70-81`).

One band step on `cdrh3_identity` moves `final` by **14.0 points**. One band step on `dockq` moves
it by **7.0**. Those two figures are exact, and they are worth deriving because the derivation is
the argument. They were computed on 2026-09-17, when `band_value` was still `midpoint`
(good 9.5, medium 7.0, poor 2.5), and a "band step" here means the full Good→Poor drop:

```
novelty  : (9.5 − 2.5) × 0.20 × 10           = 7.0 × 2.0 = 14.0
dockq    : (9.5 − 2.5) / 6 × 0.60 × 10       = 7.0 × 1.0 =  7.0
```

Identity is the sole member of a category carrying weight 0.20, so its move lands undiluted; DockQ's
identical move is divided across binding's six members before being multiplied by 0.60. Under the
later `top` anchors the absolute numbers become 10.0 and 5.0, and the **ratio is unchanged at
exactly 2×**, which is the part that matters. **The rubric already prices novelty at 2× DockQ.**

The consequence, stated with worked examples in the config:

- a **faithful** design — 96% CDR-H3 identity, DockQ 0.88 — scores **81.0 and is NON-VIABLE**,
  because 96% fails the `< 95%` novelty cutoff;
- a **divergent** design — 55% identity, DockQ 0.55 — scores **92.5 and is viable**.

Ranking on DockQ would invert that and promote near-copies of pembrolizumab, which is the one thing
the challenge explicitly forbids. So `selection_key: final`, with DockQ as tiebreaker.

**But the banded key is a poor ranker, and the project measured that too.** Reliability of `final`
had never been measured while the project reasoned for four sessions from DockQ's 0.727. Measured,
`final` is **0.602 single-seed, 0.780 at 3 seeds**, with **22 of 40 designs changing their score
across Boltz seeds** via `ipsae` (16 designs) and `dg` (17) crossing band edges as full 2.5-point
steps. And [banding](06-allocation-and-selection.md#4-banding-what-a-step-function-costs-and-what-changes-when-you-relabel-it) destroys resolution: 40 designs collapsed onto **three distinct values of
`final`**, {82.5, 85.0, 87.5}. A wider pool then adds candidates without adding any ordering.

Two properties of a step function are at work and both are worth internalising. A step function does
not *attenuate* measurement noise — it **concentrates it at the band edges and delivers it as a full
2.5-point jump**. And a metric pinned in the same band for every live design contributes a constant:
it adds no signal, but it also injects no noise. Whether banding helps or hurts therefore depends
entirely on where your designs sit relative to the edges.

The response was `src/locksmith/select/surrogate.py`: a **continuous surrogate** with the same
metrics, the same weights and the same pricing, replacing the band step with piecewise-linear
interpolation through the same three anchors. Rank on the surrogate, report the banded score, break
ties by distance from a band edge. Gating is deliberately **not** done in the surrogate — "a gate is
a property of the rubric, not of our ranking" — and missing metrics return `NaN` rather than being
skipped, because "a category mean over the SURVIVING members silently rewards a design whose worst
metric failed to compute". Two further properties, both stated in the module: the surrogate is
**absolute, not pool-relative** (a rank-normalised surrogate would make two runs incomparable and
would let the pool's composition change a design's score); and it **cannot agree with the step
function at a strict edge, and that is intrinsic** — no continuous function agrees with a step
function *at* the step. Since `contacts` is an integer count, "exactly 25" is an ordinary outcome,
not a measure-zero curiosity, so a value on a strict Good edge is **Medium in the reported score
(8.0 under `top`) and Good in the surrogate (10.0)**, by design and pinned by a test.

That surrogate is also where the project's best engineering bug lived. §10.

---

## 9. The recurring failure mode: programs that exit 0 having done the wrong thing

This is the project's signature theme. The canonical statement is
`src/locksmith/fold/__init__.py:6-16`:

> **A fold counts only when its artefacts exist and parse. The exit code is never consulted.** On
> 2026-09-15, three of four failed Boltz runs exited 0 — a missing CUDA kernel, a host-RAM kill, and
> a CUDA OOM that printed `Number of failed examples: 1` underneath a `100%` progress bar. A batch
> keyed on return status marks all three complete and skips them forever, and the resulting gap is
> invisible because the output directory exists and looks plausible.

The catalogue, with mechanisms, because the mechanism is the teachable part:

**9.1 `boltz predict` exits 0 after `ModuleNotFoundError: No module named 'cuequivariance_torch'`.**
The import error is raised *inside* Boltz's prediction loop; the exception is swallowed; the
traceback is printed to **stdout**; the process exits 0. No structure, no PAE produced. Fixed by
running with `--no_kernels`.

**9.2 A host-RAM kill.** The Linux OOM killer terminates a worker inside the run; the parent survives
and returns 0. Detected only because the artefacts were absent. Fixed by `--num_workers 0` —
dataloader workers multiply host RAM.

**9.3 A CUDA VRAM OOM printing `Number of failed examples: 1` beneath a `100%` progress bar.** The
worst of the four, because **the surface signal is positive**: the bar reads 100%. The failure line
is one row of text in a stream nobody reads when the exit code is 0. The structural fix was to stop
paying VRAM for antibody MSAs at all — peak VRAM measured at **7,603 MiB of 12,227** afterwards, 38%
headroom.

**9.4 An MSA path truncated at a space.** Boltz's FASTA MSA field is `>C|protein|<path>`, which
**splits on whitespace**. With the project root at `/home/rrobin711/Obsidian Personal/…` it reported
`MSA file /home/rrobin711/Obsidian not found.`, printed a traceback, **then initialised the GPU and
carried on**. The distinguishing detail is worth carrying: *argv is safe because the shell quotes
it; a path inside a FASTA/YAML/config field is not.* Fix: `_stage()` in `fold/boltz.py` copies the
MSA to `~/.cache/` and raises if a space survives; pinned by
`tests/test_invariants.py::test_msa_path_with_space_is_staged`.

**9.5 `ipsae.py` writes an EMPTY table and exits 0.** The vendored script locates the pLDDT array by
**string-substituting the PAE path** — literally `pae_file.replace("pae", "plddt")`. So a Boltz PAE
must keep its `pae_<name>_model_<n>.npz` name *and* keep `plddt_<name>_model_<n>.npz` as a sibling in
the same directory. Rename or relocate either — or even use a run label that happens to contain the
substring `pae` — and ipsae writes an empty table and exits 0. The architectural response is
elegant: the fold module **returns paths in place and never copies or renames them**; callers get
paths, not files. Three defences ship: the metric checks the sibling exists before calling; `fold()`
refuses any label containing `pae` or `plddt`; and the output directory is never "tidied".

**9.6 `ProcessPoolExecutor` forks and kills 239/239 CUDA workers.** Every scoring worker died with
`RuntimeError: Cannot re-initialize CUDA in forked subprocess`. Mechanism: a refactor merged the
serial NetSolP stage and the 6-worker parallel structure-scoring stage into one script; NetSolP
initialises CUDA **in the parent**; `ProcessPoolExecutor` defaults to **fork** on Linux; a forked
child inherits a CUDA context it cannot re-initialise. The original code had kept the two stages in
separate *processes* (`scripts/25` and `25p`) "and that boundary was load-bearing with nothing
recording why."

Two aggravating defects turned a visible failure into a nearly silent one:

- the stage **returned 0** despite 239/239 failures, so the shell logged `exit=0`;
- the resume logic **skipped any design that had *a row* in the output file — and an error row is a
  row** — so the obvious re-run would have skipped all 239 for ever, "leaving a file that looks
  complete."

It was caught by **reading the log rather than the exit status**. Fixes:
`mp_context=multiprocessing.get_context("spawn")`; `return 1 if n_err else 0`; and
`done_keys(..., require="dockq")`, i.e. resume keyed on a *value* that only exists if the work
succeeded. Pinned by `test_resume_keys_on_the_artefact_not_on_the_row_existing`, which greps three
driver scripts for `get("ok")` or `"ipsae" in`. **General rule: a refactor that removes a process
boundary must state what was crossing it.**

**9.7 A resume predicate whose *check* was broken, read as "not done".** Four driver scripts had each
grown their own resume check, and every one called `assert_artefacts(dir, label)` — **not its
signature**. The `TypeError` was caught by a bare `except Exception` and read as "not folded yet", so
a finished 40-complex panel would have been **silently refolded from scratch on any restart**, and
nothing would have reported it, because *re-doing finished work looks exactly like doing work.* The
asymmetry is the lesson: had the swallowed exception meant *done*, the same bug would have skipped
every fold and produced an empty panel that looked complete. Fixed as `fold_is_complete()`, which
catches **only** `FoldFailed` and lets every other exception propagate; pinned by a test that
monkeypatches `assert_artefacts` to raise `TypeError` and asserts the `TypeError` propagates.

**9.8 The audit script's own `np.bool_` bug.** `scripts/76_audit_tonight.py:34-38` tested `ok is
True`, but numpy comparisons return `np.bool_` and `np.True_ is True` is `False`. Seven genuine
passes printed **PASS** *and* were listed **UNVERIFIABLE**, and `json.dumps` refused to serialise
them. Found by the script auditing itself on its first run — "the same failure class it exists to
catch, one level up."

**9.9 `pgrep -f` self-matching.** A chained finisher waited on
`while pgrep -f "[7]3_challenge2_score.py"` and spun **21 minutes** after the work had finished,
because the heredoc that created the script was still the command line of a live parent shell, so the
bracketed literal matched from another process's cmdline. An earlier instance idled the GPU **2 h
39 m**. Rule: **gate long jobs on artefacts, never on process tables.** Full tally in
[the workflow section of the toolchain chapter](03-the-toolchain.md) — six occurrences, about 4 h 22 m
of measured idle GPU.

**9.10 The adjacent class: a program that runs correctly on the wrong input.** `io/pdb.py`'s
`chains()` built sequences from **coordinates**, so unresolved loops were silently spliced out and
the folder was handed a chimera. Four of five post-cutoff targets were affected; 9W43's antigen
folded **83 aa against a true 115**; 9BQW's 132 against 163. Re-folding from SEQRES moved 9BQW's
DockQ **0.064 → 0.370** and flipped the verdict FAIL → MARGINAL (panel median 0.157 → 0.291).
Internal gaps are fatal; terminal truncation is harmless. Guard: `seq_for_folding()` raises
`SplicedSequenceError` on an internal deletion.

### 9.11 The mechanism the instances share

In every case, **the success signal being consulted is not causally downstream of the work.** Exit
code, row existence, progress bar, `torch.cuda.is_available()`, a passing control run at the wrong
setting — each is a proxy that can be satisfied without the work having happened.

The fix is always the same shape: **assert on the artefact**, and make the assertion strict enough to
catch the ways an artefact can exist and still be useless. `assert_artefacts`
(`fold/__init__.py:55-85`) is that rule as code, and its six test cases are the enumeration:

> **absent · present-but-empty · present-with-no-`ATOM`-records · a truncated `.npz` that exists with
> the right name and fails at read time · a PAE that loads but is not square · a missing pLDDT
> sibling.**

Existence is not enough. "It parsed" is not enough either, unless you check the shape.

---

## 10. Config-versus-constant divergence, and why a relabelling reordered the ranking

This is the best engineering lesson in the project, and it is subtle enough to be worth getting
exactly right.

### 10.1 What happened

`config/metrics.yaml:7` was switched `midpoint → top` on 2026-09-20.
`src/locksmith/select/surrogate.py` kept `ANCHOR_POOR, ANCHOR_MEDIUM, ANCHOR_GOOD = 2.5, 7.0, 9.5`
**hardcoded**, because it never read the config. Nothing failed. **There is no crash available for
two numbers agreeing with different documents.** For two days, the thing the project **ranked on** and
the thing it **reported** were two conventions apart: an all-medium design scored `final = 80.0` and
`surrogate = 70.0`. Found on 2026-09-21 by an independent judge; fixed on 2026-09-22 by `_anchors(cfg)`
reading `cfg.band_scores`.

A twin defect surfaced in the same pass: `dockq.compute` had `interface_agg: str = "min"` as a
**signature default** while config declared `global`. Every caller happened to pass the value
explicitly, so nothing failed — but two callers used `c.get("dockq_interface_agg", "min")`, which
would have silently reintroduced the old convention had the key gone missing. The rule now stated in
the code: **"A default that restates a convention is a second source of truth, and the second one
rots."**

### 10.2 The consequence, recomputed

Over the 20-design shortlist with the seeds actually used
(`results/audit_response_2026-09-22.md` §B0, independently re-derived by `scripts/76_audit_tonight.py`):

| anchors | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| **midpoint** (what selection ran on) | `mpnn_T0.5_s104_036` | `…_053` | `…_057` | `…_047` |
| **top** (what config declared) | `mpnn_T0.2_s102_032` | `mpnn_T0.5_s104_011` | `mpnn_T0.3_s103_032` | **`mpnn_T0.5_s104_036`** |

**The shipped design falls 1st → 4th. 18 of 20 designs change rank. Spearman = 0.755, not 1.0.**

### 10.3 Why this looks impossible, and why it isn't

Here is the apparent contradiction. `config/metrics.yaml:17-18` claims — and `config.py:100-101`
repeats — that the band-value choice "is a uniform monotone relabelling, so it moves the headline
number and never the ranking." That claim is **true**. And the ranking changed. Both are correct,
because they are statements about *two different functions*.

**For the banded score `final`, a monotone relabelling provably cannot reorder.** `score.evaluate`
maps each raw value to one of exactly three labels — good, medium, poor — and then maps each label to
a number. Changing the three numbers is a **uniform** map applied to every metric of every design.
The composite is a fixed non-negative linear functional of the sub-scores. If design X's label
vector yields a higher composite than design Y's under one assignment, it does so under any other
assignment that preserves `good > medium > poor`, because you have applied the *same* substitution
everywhere and the functional is linear with non-negative coefficients. Monotone relabelling of a
common finite label set cannot invert a weighted sum of those labels. Done.

**For the surrogate it can, and the reason is the slope ratio.** The surrogate replaces the step with
a piecewise-linear function pinned at three anchors (`surrogate.py:94-124`):

- the **upper** segment runs from `(medium_raw, a_med)` to `(good_raw, a_good)`;
- the **lower** segment runs from `(cutoff_raw, a_poor)` to `(medium_raw, a_med)`.

The *raw* breakpoints are fixed by the rubric and do not move. Only the three anchor **values**
change. So the two segments' rises change by **different factors**:

```
midpoint anchors:  upper rise = 9.5 − 7.0 = 2.5 ;  lower rise = 7.0 − 2.5 = 4.5
                   lower/upper = 4.5 / 2.5 = 1.8

top anchors:       upper rise = 10.0 − 8.0 = 2.0 ;  lower rise = 8.0 − 5.0 = 3.0
                   lower/upper = 3.0 / 2.0 = 1.5
```

The project states it as: *"the ratio changes from 4.5/2.5 = 1.8 (midpoint) to 3.0/2.0 = 1.5 (top).
Non-uniform slopes reorder."*

Worked through: going midpoint → top **compresses the lower segment relative to the upper one** by a
factor 1.5/1.8 = 0.833. A design that banks its advantage *below* the medium anchor — a metric
sitting between `cutoff` and `medium`, where the lower slope applies — has that advantage discounted
by 16.7% relative to a design that banks the same raw advantage *above* the medium anchor. Since
designs differ in **which** of their eight metrics sit in which segment, the two scoring functions
are genuinely different orderings on the same raw data. The surrogate is **not an affine function of
itself across conventions**. Only if every design placed every metric in the same segment would the
map be affine and the order preserved.

**The distinction to carry away.** A monotone relabelling of a *finite label set* is order-preserving
for any non-negative weighted sum of those labels. A monotone relabelling of the *anchors of a
piecewise-linear interpolant* is not, because it changes the relative slopes of the pieces, and
relative slopes are exactly what determines the exchange rate between advantages banked in different
pieces. **Whenever you interpolate through anchors, you are choosing slopes.** The moment you replace
a step function with a smooth stand-in "so the ranking is better behaved", you have introduced a new
free parameter that the original specification never constrained.

### 10.4 The decision that followed, which is the interesting part

The design was **not** swapped. The reasoning (`audit_response` §B0, `README.md:60-66`): the 1st–4th
gap is **0.191** surrogate points against a pooled within-design seed sd of **0.226** and a 7-seed
standard error of **0.086**. The whole top six spans **0.205** — less than one seed. Single-seed
[reliability](04-measurement-theory.md#13-reliability) on this shortlist is **0.296**. *"Swapping now would mean acting on a ranking this
project has already measured as unable to rank."*

And then the line that makes the whole episode worth teaching: **"the winner changing is itself
further evidence for the claim we already make — within the viable pool, our metrics do not
discriminate."**

One residual is flagged rather than fixed: the reliability figure **0.629** quoted for the 20-design
shortlist "does not reproduce from the recorded inputs under any standard estimator we tried" — the
plug-in variance ratio gives **0.276** under `midpoint` and **0.296** under `top`. Flagged, because
"the original script would settle it and guessing would add a fifth number."
[The measurement chapter](04-measurement-theory.md) works through what those numbers mean.

---

## 11. Reproducibility engineering

### 11.1 The artefact-only validator

`scripts/58_validate_submission.py`, 177 lines. Its docstring is the whole idea:

> Reads ONLY the packaged folder. It does not import anything from `runs/`, does not consult any
> cached score, and re-derives every number from the three files per design. That is the whole point:
> the evaluator has the package and nothing else, so a check that reuses our own intermediate state
> proves nothing about what they will see.

Its **one** external input is the DockQ reference structure, PDB 5GGS — "public and named in §3.1" —
passed as a CLI argument "so the validator cannot silently fall back to anything of ours."

What it asserts: every required file present, with the handbook quote attached to the failure message
(`§7.1 step 1: 'Missing files = disqualification'`); the FASTA is **exactly 6 lines / 3 records** with
headers exactly `(">Heavy_Chain", ">Light_Chain", ">Antigen")` **in order**; exactly **one design per
challenge**; all eight (or seven) metrics **recomputed from scratch**, with the challenge threaded
through the novelty metric so a Challenge 2 package is not scored against Keytruda's CDR-H3 — which
"would produce a plausible number for the wrong question"; DockQ applicability read **from config**
rather than from `if challenge == 1`; a non-viable design's `final` annotated as not comparable; and
the pitch deck's existence ("§4.4, worth 50 points").

Two operational refinements that are themselves lessons. **It validates an isolated copy, never the
artefact**: `ipsae.py` writes scratch `.txt` and `.pml` files next to whatever PDB it is handed, so
validating the real package used to **litter `structures/` with three stray files** that §4.2.1 does
not list — and the packager now refuses any file §4.2.1 does not list. *"Reading a thing must not
modify it. The copy is also a better test: it proves the package works somewhere other than where it
was built."* And it **fails loudly**: any structural problem, any missing file, any hard-cutoff
failure exits non-zero with the reason. *Nothing here warns.*

Verified in both directions: a correct package exits **0**; **lowercasing one FASTA header exits 1**
and names the violation with its handbook section. Result: `VALIDATION PASSED`, Challenge 1
`final 96.0 viable True`, Challenge 2 `final 91.2 viable True`, from the packaged files alone.

The packaging side is equally paranoid. `write_fasta()` writes the file, **re-reads it, and asserts
on the bytes**. `write_structure()` synthesises the missing `TER` records — Boltz terminates the
first two chains and then goes straight from the last chain-C atom to `END`, which the project's own
stack parses happily "*but a stricter parser is entitled to merge chains B and C, which would
silently score the wrong interface*" — and then compares each PDB chain to the FASTA **residue by
residue**, reporting the first differing position. `submit/pae.py` emits a JSON **object** and
explicitly not the AlphaFold-DB list-wrapped form (which `json.load` returns as a list, making
ipsae's `'pae' in data` test *list membership* and silently find nothing), and asserts
`pae.shape[0] == n_CA`, because Boltz indexes the PAE by **token** and one token equals one residue
only for protein-only complexes.

And a gap the validator does **not** close, recorded rather than hidden: the pitch deck. The shipped
`.pptx` once said *"No design submitted"* for Challenge 2 while the package contained a Challenge 2
design scoring 96.0, because the packager rebuilt the zip and not the slides. Both structural
reviewers rated it the most severe defect in the submission. *"`VALIDATION PASSED` while the deck
says something the package contradicts. That happened, twice."* The validator reads only
`structures/`, `sequences/` and `docs/` — **it has never read the `.pptx`.** The fix was to make
`deck.build(path, *, c1, c2, calib)` take both challenges' live scores and **raise** if Challenge 2's
are missing.

### 11.2 The checksum pass — 258/258

`results/checksum_pass_2026-09-22.md`:

```
total files : 258   verified : 258   mismatched : 0   unreachable : 0
complete : true     finished : 2026-09-22T07:59:02Z
```

The manifest `runs/challenge2_pod/CHECKSUMS.jsonl` carries both hashes per line, with a summary JSON
and a `CHECKSUMS.DONE` sentinel. The hash is **computed server-side** by the Jupyter contents API, so
it is genuinely independent of the local copy. **258 rather than 256** because the first pull skipped
two `workspace/lock/` files, so the pass covers strictly more than the transfer did.

The prior state was **amber, and deliberately not rounded up**: the first attempt verified about 130
of 256 hashes before Jupyter returned 502 mid-walk. Root cause, found on stopping the pod: RunPod's
"Start Pod using CPUs" fallback provisioned **vCPU 0, Memory 0 GB**, and the Jupyter server was
OOM-killed while serving a recursive directory walk. *"A provider's 'start without a GPU' fallback is
not the same machine minus the GPU."*

Three transport lessons, all reusable: **write the manifest incrementally or it is not a manifest**
(the first pull lost ~130 computed hashes to a `JSONDecodeError` because it wrote only at the end;
the script now appends and `fsync`s each record, "which also lets an external watcher poll the
artefact rather than the process table"); after a pod restart the Jupyter token must be passed as a
**query parameter** (`?token=<t>` returns 200, the `Authorization: token <t>` header form returns
**403** with the same valid token, and a 403 reads as "credential expired"); and prefer one HTTP
transfer over paste or keystroke simulation above about 1 KB — see
[the 11,092-of-11,096-character transfer](03-the-toolchain.md).

Scope discipline, stated explicitly: the pass says the bytes are *unaltered in transit*. It says
nothing about whether the data is *correct*.

### 11.3 Mutation testing

A green test suite is a claim about the code. To get evidence about the *suite*, five bugs were
reintroduced into the working tree one at a time, the suite run, and the tree restored from a backup
between each (`results/mutation_test_2026-09-22.md`):

| # | mutation | result |
|---|---|---|
| 1 | `surrogate.py`: restore hardcoded `ANCHOR_* = 2.5, 7.0, 9.5` and the literal anchors in `compute()` | **5 failed** — all four `test_surrogate_equals_final_at_the_anchors` cases plus `test_surrogate_anchors_match_config_band_values` |
| 2 | `dockq.py`: restore `interface_agg: str = "min"` signature default | **1 failed**, exactly that test |
| 3 | `fold/boltz.py`: delete the space check in `_stage()` | **1 failed**, exactly that test |
| 4 | `io/pdb.py`: make `seq_for_folding` tolerate an internal gap | **1 failed**, exactly that test |
| 5 | `config/metrics.yaml`: flip `strict_good: true → false` on `cdrh3_identity` | **2 failed** |

The suite returned to 17 passed after every restore, verified between each. The stated conclusion is
the point: *"a green suite is a claim about the code; a suite shown to go red on reintroduced defects
is evidence about the suite. Only the second one is worth quoting."* And the stated limit is equally
important: five invariants are pinned, and "nothing here touches the scoring maths beyond the band
edges."

The selection rule for what belongs in the suite at all (`tests/test_invariants.py:11-13`) is the
best one-line testing heuristic in the project: **"an invariant whose violation is INVISIBLE. A crash
does not need a test. A number that quietly becomes wrong does."**

### 11.4 Pre-registration and self-auditing

Eleven pre-registration documents in `results/prereg_*.md`, each written **before** the run it
governs, fixing the design, the point estimate, the predictions and the decision rule.
`results/prereg_2026-09-22_diffusion_samples.md` is representative: it fixes the construct, recycling
depth, seed and MSA per challenge; explains *"Why one run of five rather than five runs of one"* (the
MSA is fetched once, so the spread is pure diffusion variability); records numeric predictions
("Challenge 1 … ipSAE spread < 0.05"; "Challenge 2 … spread > 0.10"); and tabulates four outcomes
with their verdicts, closing: *"No other reading is permitted after the fact. If the numbers land
awkwardly, that is what gets written down."*

This machinery is what makes the project's withdrawals legible rather than embarrassing: the
pre-registered Rule 3 fired on the negative-control panel and the project reported the experiment
**INCONCLUSIVE** rather than harvesting the favourable half.

The audit layer goes one further. `scripts/76_audit_tonight.py` re-derives every headline number in
the audit response **from the files**, and additionally checks another script against its own
docstring. Its rationale: *"the NEWEST claims carry the errors the audits exist to catch … there is
no reason to assume last night's corrections are exempt, and they were written by the same process
that produced the errors."* Every check prints PASS/FAIL with **both** numbers, and anything not
checkable from files is printed **UNVERIFIABLE**, never quietly assumed. Result: **PASS 46, FAIL 0,
UNVERIFIABLE 0**. Two of its three findings were about this very failure mode — a figure written as
0.28 that was a `midpoint` value quoted in a `top` context (correct value 0.296): "convention-mixing,
committed in the document that reports convention-mixing" — and the script's own `np.bool_` bug from
§9.8.

### 11.5 The headline ratio

Rolled up by intent rather than by directory, out of 18,462 lines of Python and shell:

| Intent | LOC | Share |
|---|---|---|
| **Measuring / analysing / auditing what was built** (analysis, experiments, calibration, conformance and audit, the metrics library, tests, batching acceptance, germline validation) | **9,832** | **53.3%** |
| Producing designs and structures (generation, folding, scoring drivers, the fold/io/design/core/select libraries, post-cutoff panel, variant panel, Gate 0, setup, orchestration) | 6,398 | 34.7% |
| The Challenge 2 route (RFantibody, pod retrieval, Ch2 fold/score/package) | 1,623 | 8.8% |
| Shipping (packaging, validator, deck, PAE converter) | 1,242 | 6.7% |

**More than half the code exists to check the other half.** The largest single script
(`42_analyse_tonight.py`, 600 lines) and the largest phase (analysis, 3,757 lines across 15 scripts)
both do measurement rather than production.

One nuance worth noting: the *test file* is small — 518 lines, 2.8% — because most of the checking
lives in **assertions inside the pipeline**: `assert_artefacts`, `seq_for_folding`'s internal-gap
guard, `_stage`'s space check, `cdr_residues`'s numbering cross-check, `write_pae_json`'s CA-count
assertion, `select.rank`'s structural gating, and `75_challenge2_package.py`'s refusal to build a
folder unless a design clears every §7.2 cutoff. The test file is reserved, by its own stated rule,
for invariants whose violation would otherwise be invisible. That refusal guard is worth quoting as
an example of a well-designed exit-code ladder: **exit 2** = no design clears every cutoff, refuse to
package (*"§7.2 ranks a non-viable design below every viable one, so a folder here would be worse
than no folder. This is a legitimate end state, not a failure of this script."*); **exit 3** = viable
designs exist but none carries a conditioning record, so the pre-registered selection rule cannot be
applied; **exit 0** = built.

---

## What to take away

1. **Derive metrics on demand; store only inputs.** A convention discovered wrong then costs a
   10-second re-score instead of a day of re-folding. Four conventions did change; none cost a fold.
2. **Encode the specification as data, with its ambiguities as named switches carrying their
   evidence.** `config/metrics.yaml` is simultaneously the rubric, the decision log and the answer to
   "what would this score under the other reading?".
3. **Build the judge before the contestant, and make it fail on the right things.** Pembrolizumab
   scoring 76.0 and NON-VIABLE is the single most informative test in the project. Fix the
   expectation, not the code.
4. **Exit codes, progress bars, row existence and `is_available()` are proxies that can be satisfied
   without the work happening. Assert on the artefact** — and enumerate the ways an artefact can
   exist and still be useless.
5. **A default that restates a convention is a second source of truth, and the second one rots.** The
   failure is invisible precisely because both numbers are individually plausible.
6. **A monotone relabelling is order-preserving for a step function and not for its continuous
   surrogate.** Interpolating through anchors means choosing slopes; non-uniform slope changes
   reorder. Get this distinction right and you will never again assume "it's just a rescaling".
7. **Validate the artefacts, not the pipeline that produced them** — on an isolated copy, so reading
   cannot modify.
8. **A green suite is a claim about the code; a suite shown to go red on reintroduced defects is
   evidence about the suite.**

Next: [every tool, how it was invoked, and what it silently gets wrong](03-the-toolchain.md). For the
statistics underneath the reliability numbers used here, see
[the measurement-theory chapter](04-measurement-theory.md); for how the shortlist and seed budget were
sized, [allocation and selection](06-allocation-and-selection.md).
