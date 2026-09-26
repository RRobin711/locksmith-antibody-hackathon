# Building a twelve-chapter course from the project record — and the three defects that fell out

**2026-09-23.** No GPU time, no new science. This session read the entire
project record back and turned it into a teaching course at
[docs/lecture/](../lecture/README.md). The interesting part is not the course; it
is that *reading nine days of work as a single document* surfaced three defects
that nine days of working inside it did not.

That is the transferable finding, and it is worth stating before the detail:

> **A record that is correct locally can be wrong globally.** Every one of the
> three defects below sits in a file that was right when it was written. They
> became wrong when something elsewhere changed and the propagation was manual.
> No individual session could have caught them, because each is a disagreement
> *between* documents.

---

## 1. What was built

`docs/lecture/`, twelve chapters, 75,485 words, 148 internal links.

| # | chapter | words |
|---|---|---|
| 00 | orientation — the four questions answered directly | 2,589 |
| 01 | the biological problem | 8,035 |
| 02 | the engineering problem | 8,644 |
| 03 | the toolchain | 9,857 |
| 04 | measurement theory | 5,192 |
| 05 | experiment design | 6,337 |
| 06 | allocation and selection | 6,194 |
| 07 | the campaign, day by day | 8,038 |
| 08 | what broke — 104 incidents in six classes | 10,477 |
| 09 | critique | 4,593 |
| 10 | glossary | 2,214 |
| 11 | study plan | 2,197 |
| — | README / index | 1,118 |

Method: eight research agents, one per dimension (biology, engineering,
prerequisite knowledge, tooling, statistics, artefact inventory, failure
catalogue, critique), each writing a verified report to scratch; then three
writing agents consuming those reports; then the spine chapters — 00, 09, 10,
11 and the index — written directly. Research reports are in the session
scratchpad and are not preserved.

Two agents independently reproduced the band-grid result in §2.1 from scratch
before it was written down. That redundancy was deliberate and it is the only
reason the finding is stated as fact rather than as a suspicion.

---

## 2. The three defects

### 2.1 `config/metrics.yaml` states a false theorem

The config defends its `band_value: top` default with this:

> "The choice is a uniform monotone relabelling, so it moves the headline number
> and never the ranking."

**This is false as stated.** The claim is repeated in
`results/handbook_conformance.md`.

The mechanism is worth understanding because it generalises. The relabelling
maps midpoint sub-scores to top-of-band sub-scores:

```
2.5 -> 5      7.0 -> 8      9.5 -> 10
```

That map is **monotone**. It is **not affine**. Fit a line through the two lower
anchors: the slope is `(8-5)/(7.0-2.5) = 0.6667`, which predicts `5 + 0.6667 x 7
= 9.667` at the Good anchor, not 10. The gap is +0.333.

The composite is a **weighted mean** of eight sub-scores. A monotone but
non-affine transform applied componentwise to the arguments of a weighted mean
*can* change the ordering of the results — only an affine transform is
guaranteed not to, because only an affine transform commutes with a weighted
mean.

Enumerated exactly. The composite depends only on the multiset of the six
binding bands plus the developability and novelty bands, so the grid has
`C(6+2,2) x 3 x 3 = 252` distinct designs and 31,626 pairs. Under exact rational
arithmetic there are **39 strict ordering reversals**, maximum margin **1.000**
composite points. Worked instance:

| design | binding bands | dev | nov | midpoint | top |
|---|---|---|---|---|---|
| A | P P P P P G | G | G | **60.000** | 75.000 |
| B | M M M M M M | P | M | 61.000 | **74.000** |

B wins under `midpoint`; A wins under `top`.

**What the project actually observed** is that no such flip occurred in its own
239-design pool. That is a contingent fact about where those designs happened to
sit on the grid. It was written down as a theorem and then used to dismiss the
band choice as methodologically inert. It is not inert.

*Note the distinction this does NOT disturb:* the reordering caused by
`select/surrogate.py`'s anchors (winner 1st -> 4th, 18/20 ranks changed,
Spearman 0.755) is a different and already-documented effect, operating through
the interpolation segment slope ratio 1.8 -> 1.5. The finding here is that the
*banded* score, believed safe, is not safe either.

### 2.2 `STATE.md` is stale on a headline, upward

`STATE.md` opens by declaring itself *"the single place to find out where the
project is"* and its headline table gives Challenge 2 a score of **96.0**.

`README.md:34` and the shipped
`submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge2/metrics/scores.md:18` both say
**91.2**. The design that shipped is the `S->A` sequon-fixed variant, and the
substitutions are physically present in the packaged FASTA (heavy `NVA` at 52,
light `NAA` at 49). The 4.8-point gap was paid deliberately.

A stale headline is minor. A stale headline **in the designated source of truth,
biased upward, in a project whose thesis is that flattering numbers are the
danger**, is not. Same class as `PROJECT-STORY.md` — the file `README.md:13`
designates as the entry point — still carrying the refuted aromatic filter, the
corrected allocation claim, the superseded 87.5, and the line *"No antibodies
designed yet."*

### 2.3 The `0.629` puzzle resolves, and a real one survives

`STATE.md` §8 lists as unresolved: the reliability figure 0.629 *"does not
reproduce (plug-in gives 0.276 midpoint / 0.296 top)"* — flagged, not corrected.

**The flag is itself a category error**, of exactly the kind this project
catalogues under *never diff a single observation against an aggregate*. The two
numbers estimate different things:

```
0.629  = reliability of a 7-SEED MEAN.  Reproduces: 1 - 0.176^2/0.290^2 = 0.6317
0.296  = reliability of a SINGLE SEED.
```

0.629 is the correct quantity for shrinking a 7-seed mean, which is what it was
used for. So the flagged discrepancy dissolves.

**And a real one survives underneath it.** Spearman-Brown relates the two:

```
r1 = 0.296, k = 7  =>  r7 = 0.746   (not 0.629)
r7 = 0.629, k = 7  =>  r1 = 0.195   (not 0.296)
```

Both directions checked. There is a genuine inconsistency in the record, it is
not the one that was flagged, and it is a two-line check for which
`tests/test_invariants.py:177` already has the idiom.

### 2.4 Also found, lower severity

- **The canonical exit-0 list is mis-enumerated.** `fold/__init__.py:9-11` and
  `tests/test_invariants.py:398-401` both list the host-RAM kill as an exit-0
  case. It was `SIGKILL`. The correct third member is ipSAE's empty table. The
  project's most-repeated rule has been mechanised in its wrong version.
- **The reliability triple `0.591 / 0.813 / 0.938` is a mixture.**
  `results/ensemble_power.md`'s table is internally consistent under a
  between-design variance of **B = 0.09372 A^2** (giving 0.599/0.792/0.938), while
  0.591 uses the *same noise term* with the session doc's **B = 0.0907 A^2**, and
  0.813 requires a third combination. The disagreement is in the signal term, not
  the noise, and the triple quoted downstream splices two estimates.
- **`results/calibration.md`** ships an empty results table beside power language
  for an n=20/arm design it has three observations of.
- `LEARNINGS.md` still carries a NetSolP claim the submission retracted, and that
  entry's `0.379/0.463/0.733` mixes VH and VL across three variants.

---

## 3. A seventh `pgrep` self-match, committed while writing about the first six

While verifying §2.1 I ran `pkill -f "from itertools import product"` to clear a
slow search. The pattern matched **its own command line** and killed the shell
that issued it. Exit 144.

Seventh instance in this project's history, first not committed by the author,
and committed *while writing the chapter that documents the other six*. The fix
is the one already written down — gate on artefacts, never on process tables —
and the reason it kept happening is the lesson:

> **A lesson recorded in prose is not a lesson mechanised.** Six write-ups did
> not stop the seventh occurrence. `.claude/hooks/pkill-guard.sh` is what stops
> it, and it was written only after the sixth.

The immediate workaround, for the record: put the script in a file and run the
file, rather than passing the code on the command line. Then there is no
distinctive pattern in any argv to match.

---

## 4. What this says about the project's real weakness

`results/audit_2026-09-20.md` records *"fourth overstatement of the day, fourth
toward a more interesting finding."* Noise is symmetric; four errors in one day
pointing the same way is a property of the generating process.

This session adds a second, quieter failure mode that no audit caught, because
every audit ran inside a session and these defects live *between* sessions:

| defect | each file correct when written? | what made it wrong |
|---|---|---|
| band-value theorem | yes | generalised an observation about one pool |
| `STATE.md` 96.0 | yes | the Ch2 design changed after it was written |
| `0.629` flag | yes | compared two different estimands |
| exit-0 list | yes | copied forward, then pinned by a test |
| `0.591` triple | yes | two estimates merged by quotation |

Every one is **two places encoding one fact, never reconciled**. The project
names this pattern itself and fixed three instances of it in code. It did not
fix it in prose, because prose has no compiler.

The remedy is the one the project reached on its last day and did not have time
to build: **one machine-readable results store, with the prose reading from it
rather than duplicating it.** Combined with the four-field stamp proposed in
[the critique](../lecture/09-critique.md) — every number carries its `n`, its
estimand, its detectable effect, and its provenance — it closes most of the
class.

---

## 5. What was deliberately not done

- **Nothing in the project record was corrected.** The three defects are
  documented in [chapter 09](../lecture/09-critique.md) and here; `STATE.md`,
  `config/metrics.yaml`, `PROJECT-STORY.md` and `LEARNINGS.md` are untouched.
  Correcting them is a separate, deliberate pass.
- **No science was re-run.** Every number in the course is quoted from the
  existing record, and every arithmetic check is a recomputation from recorded
  inputs, never a new measurement.
- **The decoy-patch control is still unrun**, and remains the only experiment
  that could falsify the conditioning result.

---

## 6. Verification

- 12 chapters + index on disk, 75,485 words.
- 148 wikilinks: **0 bare, 0 split across a newline, 0 dead targets**. Three
  split links in chapter 01 were found and repaired; the split-wikilink failure
  is the one `.claude/hooks/wikilink-guard.sh` exists for.
- Every chapter carries its "What this chapter teaches" and "What to take away"
  framing (the glossary omits the latter, correctly — it is a reference).
- The §2.1 band-grid result was derived twice, independently, before being
  written: 39 reversals, max margin 1.000, same worked instance both times.
- The §2.3 arithmetic was checked in both directions.
