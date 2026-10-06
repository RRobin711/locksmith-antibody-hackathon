---
date: 2026-10-05
tags: [project, lecture, course, measurement, learning, problem, audit]
status: living
---

# 12 — The audit: eleven days in which nothing was designed

> ⚠️ This chapter covers **2026-09-23 → 2026-10-03**, after the campaign in
> [Chapter 07](07-the-campaign.md) ended. It was written on 2026-10-05, so unlike chapters
> 00–11 it already incorporates [C1–C8](CORRECTIONS.md) rather than being indexed by them.

## What this chapter teaches

[Chapter 07](07-the-campaign.md) ends on 2026-09-22 with two scored designs. This chapter
covers the eleven days after that, and the first thing to understand about them is what they
did **not** contain:

- **No design changed.** Not one sequence, not one backbone.
- **No metric was recomputed from a structure.** No new folds for scoring purposes.
- **The headline scores moved exactly once, and downward**: Challenge 1 from **96.0 to
  94.0**, on 2026-09-25, because a [DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong) value was read unrounded. That is a *correction*,
  not an improvement.

Eleven days, no science, and the project's front page now says that what came out of them
*is its main result*. This chapter explains why that is not a paradox.

The campaign produced numbers. The audit produced the knowledge of **what the numbers are
numbers of** — and, more durably, a catalogue of the ways a careful person checks something
and gets a true answer to a question they did not ask. That second thing is the
transferable part, and it is why this chapter is field-independent in the way
[04](04-measurement-theory.md), [05](05-experiment-design.md) and
[06](06-allocation-and-selection.md) are. Nothing below requires you to care about
antibodies.

**The one-sentence version.** *Every check you run answers a narrower question than the one
you asked, and it answers that narrower question truthfully* — so a clean result is
evidence about your instrument before it is evidence about the world.

---

## 0. What an audit period is, and why this one was not cleanup

The instinct is to read "audit" as tidying: fixing typos, updating stale numbers, closing
tickets. Two of these sessions began with exactly that expectation and neither stayed there.
The 2026-09-28 session states it directly:

> "**The work was meant to be janitorial. It was not**, and the reason is the thing worth
> keeping: **four of the nine items turned out to be a guard, a flag, or an index that could
> not do the job it claimed to do.**"

That is the shape of the whole period. The project did not discover that its records
contained *mistakes*. It discovered that several of its **verification mechanisms were
structurally incapable of detecting the thing they existed to detect** — and that each one
had been returning a clean result the entire time.

A clean result from a blind check and a clean result from a clean corpus are **the same
observation**. Distinguishing them is not a matter of care. It requires a second question:
*what would this check have done if the answer were no?*

### The sessions, and what each was for

| date | the question it opened on | what it turned out to be about |
|---|---|---|
| **09-23** | can nine days of record be taught? | a record correct locally can be wrong globally |
| **09-25** | why did yesterday's correction vanish? | documents are **owned** by whatever generates them |
| **09-26a** | what exactly has been retracted? | a count is a claim; and `grep` under-reports |
| **09-26b** | is this safe to publish? | a clone cannot distinguish deleted from [orphaned](12-the-audit.md#23-the-orphaned-artefact--worse-because-nothing-ever-looks-wrong) |
| **09-28** | close nine open items | five [guards](12-the-audit.md#4-guards-that-could-not-see-their-own-corpus) that could not see their own corpus |
| **09-29** | publish it properly | convergence is not termination |
| **10-03** | was that null real? | 23% power, and a blocker that never existed |

Read the right-hand column downward. **Not one of them is about biology, and not one is
about being careless.** Every defect below was produced by a competent action taken for a
good reason.

---

## 1. Why reading your own record finds what living in it cannot

### 1.1 The method, and why it mattered

On 2026-09-23 the project read its entire nine-day record back and rewrote it as a teaching
course — the twelve chapters you are reading. No GPU time, no new science. The session's
own opening is the thesis:

> "The interesting part is not the course; it is that *reading nine days of work as a single
> document* surfaced three defects that nine days of working inside it did not."

> "**A record that is correct locally can be wrong globally.** Every one of the three
> defects below sits in a file that was right when it was written. They became wrong when
> something elsewhere changed and the propagation was manual. No individual session could
> have caught them, because each is a disagreement *between* documents."

This is worth sitting with, because it describes a defect class that **no amount of care
within a session can prevent.** Each file was checked. Each file was right. The error lives
in the *relation* between files, and nobody's attention is ever pointed there — there is no
moment in normal work at which you read two documents side by side and ask whether they
still agree.

**Why writing it as teaching was the instrument.** Explaining something forces you to
traverse joins you otherwise never traverse. To write "the [composite](02-the-engineering-problem.md#32-the-composite-formula) is computed like
this, and here is a worked example", you must read the config, the code and the results
file *together* — and that is the only operation that can detect them disagreeing.

### 1.2 Defect 1: a config file stating a false theorem

`config/metrics.yaml` defended its `band_value: top` setting with a claim that reads like
mathematics:

> "The choice is a uniform monotone relabelling, so it moves the headline number and never
> the ranking."

**It is false as stated, and it had been repeated into `results/handbook_conformance.md`.**

Here is the reasoning, from first principles, because the error is instructive and entirely
general.

The relabelling maps each [band](06-allocation-and-selection.md#4-banding-what-a-step-function-costs-and-what-changes-when-you-relabel-it)'s sub-score from the midpoint of its range to the top:
`2.5 → 5`, `7.0 → 8`, `9.5 → 10`. That is **monotone** — order within any single metric is
preserved. The composite, however, is a **weighted mean** of eight sub-scores, and the
operation that commutes with a weighted mean is not monotonicity. It is **affinity**.

Check whether the map is affine. The slope through the two lower anchors is

```
(8 − 5) / (7.0 − 2.5)  =  3 / 4.5  =  0.6667
```

An affine map with that slope through `(2.5, 5)` predicts `5 + 0.6667 × (9.5 − 2.5) = 9.667`
at the Good anchor. The actual value is **10**. The gap is **+0.333**, and a piecewise map
with a kink does not commute with averaging.

Because the composite depends only on the *multiset* of six binding bands plus the
developability and novelty bands, the whole space is finite and can be enumerated exactly:
`C(6+2,2) × 3 × 3 = 252` distinct designs, giving **31,626 pairs**. Under exact rational
arithmetic there are **39 strict ordering reversals**, with a maximum margin of **1.000
composite points**. A worked pair:

| design | binding bands | dev | nov | midpoint | top |
|---|---|---|---|---|---|
| A | P P P P P G | G | G | **60.000** | 75.000 |
| B | M M M M M M | P | M | 61.000 | **74.000** |

Under `midpoint`, B beats A. Under `top`, A beats B. The "never" is false.

**The epistemics are the lesson, not the algebra:**

> "What the project actually observed is that no such flip occurred in its own 239-design
> pool. That is a contingent fact about where those designs happened to sit on the grid. It
> was written down as a theorem and then used to dismiss the band choice as
> methodologically inert. It is not inert."

**An observation about your data was promoted to a claim about the operation, and then used
to close an inquiry.** The upgrade from *"we saw no reversals"* to *"it cannot reverse"* is
invisible when you make it, because both sentences feel like the same fact. One is a
measurement with a sample size; the other is a theorem with a proof obligation.

*Transferable: when a document says something "never" happens, ask whether that word was
earned by a proof or by a sample — and if by a sample, the claim inherits that sample's n.*

### 1.3 Defect 2: the designated source of truth, stale and biased upward

`STATE.md` opens by declaring itself *"the single place to find out where the project is"*
and gave Challenge 2 at **96.0**. `README.md:34` and the shipped
`submission/…/metrics/scores.md:18` both said **91.2**. The shipped design was the `S→A`
sequon-fixed variant — the substitutions are physically present in the packaged FASTA
(heavy `NVA` at 52, light `NAA` at 49) — and the 4.8-point gap had been paid deliberately
for developability.

The severity argument is the part to keep:

> "A stale headline is minor. A stale headline **in the designated source of truth, biased
> upward, in a project whose thesis is that flattering numbers are the danger**, is not."

Same class, same day: `PROJECT-STORY.md` — the file `README.md:13` designates as *the entry
point* — still carried the refuted aromatic filter, a corrected allocation claim, a
superseded 87.5, and the sentence *"No antibodies designed yet."*

**Note the pattern: both stale documents were the ones a newcomer is told to read first.**
That is not coincidence. A document everybody works in gets corrected by the work; a
document that exists to be read by *other* people is touched only when someone remembers to
touch it.

### 1.4 The structural diagnosis — and the sentence that explains the whole period

The session tabulated its defects by asking one question of each: *was the file correct when
it was written?*

| defect | correct when written? | what made it wrong |
|---|---|---|
| band-value theorem | yes | generalised an observation about one pool |
| `STATE.md` 96.0 | yes | the Challenge 2 design changed afterwards |
| the `0.629` flag | yes | compared two different estimands |
| the exit-0 list | yes | copied forward, then pinned by a test |
| the `0.591` triple | yes | two estimates merged by quotation |

Five for five. And then:

> "Every one is **two places encoding one fact, never reconciled**. The project names this
> pattern itself and fixed three instances of it in code. It did not fix it in prose,
> **because prose has no compiler.**"

That last clause is the best four-word summary of this chapter. In code, a convention
encoded twice eventually produces a type error, a failing test, or a visible wrong answer.
In prose it produces two sentences that are each individually defensible, sitting in
different files, for as long as nobody reads both.

The remedy the session proposed and **never built** is worth recording as an unpaid debt:
*one machine-readable results store, with the prose reading from it rather than duplicating
it*, plus the four-field stamp from [the critique](09-critique.md) — every number carries
its **n**, its **[estimand](04-measurement-theory.md#6-the-0629-that-does-not-reproduce-an-estimand-mismatch-and-a-residual-inconsistency)**, its **[detectable effect](05-experiment-design.md#13-the-standard-stated)**, and its **provenance**.

### 1.5 A seventh `pgrep` self-match, committed while writing about the first six

While writing the chapter that catalogues six previous incidents of `pkill -f` matching its
own command line, the author ran `pkill -f "from itertools import product"` to clear a slow
search. It matched its own `argv` and killed the issuing shell. **Exit 144.**

> "**A lesson recorded in prose is not a lesson mechanised.** Six write-ups did not stop the
> seventh occurrence. `.claude/hooks/pkill-guard.sh` is what stops it, and it was written
> only after the sixth."

There was an eighth on 2026-09-29 (`pgrep -f '97_decoy_cpu.sh'`, exit 144 again), *with the
hook already in place.* The workaround is a bracketed pattern (`'[9]7_decoy_cpu'`), and the
better answer is structural: **gate long jobs on artefacts, never on process tables.**

---

## 2. A document is owned by whatever writes it

### 2.1 The trigger: a correction that vanished

On 2026-09-25 a correction made the previous day to Challenge 1's packaged
`reproducing_our_numbers.md` had **silently disappeared**. The document had been edited by
hand. It is generated by a script. The next packaging run overwrote it.

The reverting run was **+11 −61 lines**, and what it restored was not cosmetic: text telling
a grader to run DockQ with a flag value that **exits 1 and prints nothing**. Because
handbook §7.2 makes DockQ a hard viability cutoff, *"a grader following that instruction
could record 'no DockQ' and mark Challenge 1 non-viable — a 94-point item."*

The user found it by diffing the package. No check caught it.

### 2.2 The concept, stated generally

> "*Editing a projection does not change what it is a projection of.*"
>
> "**An edit to a derived object has a lifetime bounded by the next derivation.**"

The reason this is hard to see in practice:

> "Nothing about a `.md` file announces that a script owns it."

A `.py` file in a build directory looks generated. A Markdown document in a documentation
folder looks authored. They can be the same kind of object, and the filesystem will not tell
you which. The cheapest detector that requires no knowledge of the codebase is a
**timestamp comparison between sibling files in a generated directory** — which is exactly
how the next defect was caught.

### 2.3 The orphaned artefact — worse, because nothing ever looks wrong

Formalise it. Generator `A` writes files `{w, x, y, z}`. Generator `B` writes `{w, x, y}`.
Run `A`, then run `B`. File `z` is now an **orphan**: no generator will ever update it
again, and nothing announces that.

> "Worse than the reverted edit, because there is no moment at which anyone observes
> something being undone. Every per-file check passes: `z` exists, parses, is internally
> consistent, and its numbers are all real numbers that were true once."
>
> "**A partial writer is more dangerous than a broken one.**"

This happened. Two scripts can package Challenge 2: `scripts/75_challenge2_package.py`
passes `extra_docs={"reproducing_our_numbers.md": repro_md}`;
`scripts/105_package_bb8.py` — which swapped in the current `bb_8_0` design — passes **no**
`extra_docs`. The shipped package was built by 105. The timestamps:

```
methods_and_limitations.md   2026-09-23 23:01:54
scores.md                    2026-09-23 23:01:54
design_1.fasta               2026-09-23 23:01:53
reproducing_our_numbers.md   2026-09-22 22:16:10     <-- a full day older
```

That orphan contradicted the structure shipped beside it on **all seven** of its metrics:

| metric | orphan said | truth |
|---|---|---|
| `ipsae` | 0.781 | **0.904** |
| `netsolp` | 0.570 | **0.555** |
| `iface_plddt` | 85.17 | **88.62** |
| `cdr_sasa` | 1066.5 | **1110.5** |
| `contacts` | 97 | **99** |
| `cdrh3_identity` | 30.0 | **18.2** |

**The fix was structural rather than textual**, which is the point. The template was lifted
verbatim out of `scripts/75` into a library module `src/locksmith/submit/docs.py`, called by
both packagers. Rejected alternatives, each with its reason: *copy it into `scripts/105`*
(duplication re-creates the drift one generator at a time); *delete the orphan* (removes a
document Challenge 1 ships, which a grader would notice as an asymmetry).

> "**A template reachable by only one of two generators is a bug waiting for the second
> generator.**"

**Detection requires a cross-check against a recomputation from declared inputs**, because
residue of this kind is invisible to any check that examines files one at a time.

### 2.4 Rounding across a decision boundary

This produced the project's single largest score change, and the mechanism is worth deriving
because it generalises to every threshold comparison you will ever write.

With printed precision `p = 3`, the half-width of a displayed value is

$$
\varepsilon \;=\; 0.5 \times 10^{-p} \;=\; 0.0005
$$

Any true value `x ∈ [t − ε, t)` **prints as `t`** and therefore bands *above* a threshold at
`t`, despite being below it. Here `t = 0.80`, so the dangerous interval is
`[0.7995, 0.800)`.

The submitted design's true DockQ is

```
0.7995794972281312
```

— inside that interval by **0.00042**. It printed `0.800`, banded `good`, "and scored 2
points it had not earned." Challenge 1's composite fell **96.0 → 94.0**.

> "Rounding is harmless *except within half a display unit of a decision boundary*… the
> error rate is not 'small' — it is **1 for values in that interval and 0 elsewhere**."

That last sentence is the part people get wrong. Display rounding feels like a small,
diffuse inaccuracy. It is not: it is a **deterministic, total failure on a narrow set**, and
the set is defined by exactly the thing you care about.

The fix was two mechanisms, because surfacing and preventing are different jobs:

1. `dockq.compute` passes `--json` and reads `GlobalDockQ` unrounded — the returned value is
   **not rounded at all**, because banding must see the true number.
2. `score.evaluate` declares each metric's display precision and records a
   `Scored.rounding_risk` entry when a value lands within ±0.5 ulp of any band edge.
   Packaged tables then print that metric at **6 decimals** instead of 3 — which is why the
   shipped `scores.md` reads `0.799579 | medium` rather than the self-contradictory-looking
   `0.800 | medium`.

> **Transferable:** *any parse of a **rendered** number inherits that renderer's precision,
> and a threshold comparison is exactly where the lost digits matter. Parse the
> machine-readable output when one exists — and when a value sits within its display
> precision of a decision boundary, print more digits rather than fewer.*

**The honest sub-finding is as instructive as the finding.** Was the five-sample diffusion
sweep also affected? *"Yes in mechanism, no in consequence."* `scripts/81` parsed 3-dp
printed values, so the defect was present — but re-banding at stored versus recomputed
values (0.8160/0.7980/0.8010/0.8200/0.7110 versus
0.8160/0.7979/0.8011/0.8201/0.7109) leaves every band unchanged, because **no sample lies in
`[0.7995, 0.800)`**. It was recorded anyway:

> "Reporting only defects that changed something teaches the wrong lesson."

### 2.5 "What is this number *of*?"

> "**'Is this number right?' is the wrong question; 'what is this number *of*?' is the right
> one.**"

The instance: a document about design *D* quoted three genuine, correctly-measured DockQ
values — of *D′*, a design differing at **one amino acid**.

The packaged doc listed per-interface `A,B 0.931 / A,C 0.723 / B,C 0.794`. Recomputing from
`--json` on the shipped structure gives something else entirely:

```
GlobalDockQ : 0.7995794972281312
  AB: DockQ=0.8716  LRMSD=0.931  iRMSD=0.839  fnat=0.865
  AC: DockQ=0.7308  LRMSD=2.015  iRMSD=0.738  fnat=0.441
  BC: DockQ=0.7963  LRMSD=1.970  iRMSD=1.026  fnat=0.759
```

**And here is the trap.** The first explanation written was that `0.931` was AB's **LRMSD**
column misread as a DockQ column. Look at the output: AB's LRMSD *is* exactly 0.931. The
story is seductive, internally coherent, and names a plausible human error.

It is wrong, and the tell is that **it explains one of the three numbers.** Recomputing the
five-sample sweep's `model_0` gives `AB=0.9307  AC=0.7229  BC=0.7945` — **all three match.**
Confirmed by sequence comparison: that model and the shipped design differ at exactly one
position, heavy chain 55, `N → Q`. The numbers are the **pre-`N55Q`** design's.

> "**A coincidence that explains part of the evidence is more dangerous than no explanation
> at all, because it terminates the search.** Require an explanation to account for every
> observation before accepting it."

### 2.6 Four more failures from the same session, each its own lesson

**(a) Reading a pipeline's exit status as the script's.** The command was
`python scripts/57_build_submission.py 2>&1 | tail -30`. The script crashed with
`ModuleNotFoundError: No module named 'pptx'`; the reported exit status was **0** — `tail`'s.
Three compounding consequences: the deck is a **50-of-250-point** deliverable and was never
rebuilt; `build_zip` sits at **line 473**, after the crashing call at **471**, so the zip was
not rebuilt either; and the package `.md` files *were* written, because `build_challenge`
runs first.

> "**So the verification that was performed passed, on a package produced by a script that
> had failed.**"
>
> "**A crash partway through a build leaves a directory that looks complete.**"

**(b) An undeclared dependency on a scored deliverable.** `submit/deck.py` imports `pptx`;
`python-pptx` appeared nowhere in `pyproject.toml`; no interpreter on the machine had it.
*"The previously shipped deck had been built in an environment that no longer exists."*

> "**A dependency used only by the last step of a pipeline is the one most likely to be
> undeclared.**"

**(c) A guard whose first version missed the case it was written for.** Extending the
numeric check from table rows to prose, the mutation test — flipping the germline figure in
the sentence — **did not fire**, because the sentence named the metric as "the V(D)J-coverage
reading" rather than in backticks, and the prose rule requires a backticked name.

> "**A guard is only tested by the mutation it was written to catch.** Writing a plausible
> mutation elsewhere and watching the guard fire proves the guard runs, not that it covers."

The fix is the counter-intuitive part: rather than loosening the matcher and inviting false
positives, **the document was changed to name the metric it asserts.** *Write artefacts so
the checker can see them.*

**(d) A false mechanism, declined twice.** The package documented the minimum
`--allowed_mismatches` for DockQ as **15**, justified as "exactly the number of substitutions
in this design". Re-measured by bisection: 15 exits 1, **16 works**. And the justification
was independently false — aligning model against native with `difflib.SequenceMatcher`
gives **10 aligned substitutions** on the heavy chain, not 15 and not 16. (A naive
*positional* diff instead reports **197**, because the chains differ in length and the
comparison goes out of register — *"visible immediately in the output as `V1Q Q2V L3Q V4L`,
a shift, not a mutation pattern. A substitution list that reads like a rotation of the
alphabet is an alignment failure, not a result."*)

The corrected text states **16 as measured, with no derivation at all**:

> "A reader who is told 'we measured it' can reproduce it; a reader given a false mechanism
> will reason from it."

*Two successive attempts to supply a mechanism had both been wrong. A false mechanism is
worse than an acknowledged gap.*

---

## 3. Every search answers a narrower question than the one you asked

This is the chapter's central section, because the same defect appeared **on three different
tools in a single day**, and then a fourth time in the mechanism built to fix it.

> "**Every search answers a narrower question than the one you asked, and it answers it
> truthfully.** Before believing a clean result, ask what the search would have done had the
> answer been *no*."

### 3.1 Three ways a text search silently under-reports

All three were hit for real. All three fail **quietly** — *a search returning fewer hits
looks exactly like a cleaner corpus.*

**(1) Hard-wrapped prose.** `grep` is line-oriented. Having corrected a retracted
error-rate claim, the sweep was:

```bash
grep -rn "0% false-positive" results/ docs/lecture/ README.md PLAN.md STATE.md
```

Two hits. The register was then written saying there were two instances.

> "That was wrong. There were **three**, and the same file contained two of them."

The missed one was wrapped:

```
... ipSAE tracks pose accuracy at ρ = +0.702 with a 0%
false-positive rate — which is why the number is worth something ...
```

The phrase straddles a newline, so no single line contains it, so a line-oriented matcher
cannot see it. *"It surfaced only by accident, in the `tail` output I happened to read for a
different purpose."*

> "**Why this is worse than an ordinary miss.** It fails quietly and plausibly: a grep that
> returns two hits looks like a complete answer, and there is no signal distinguishing 'two
> occurrences exist' from 'two occurrences happen to fit on one line each'. **The error rate
> scales with phrase length and with how hard the prose is wrapped, so it is worst exactly
> where it matters — long, quotable claims in hard-wrapped documentation.**"

The fix: `r"\s+".join(re.escape(w) for w in phrase.split())`, run over the file's full text.

**The carry-forward failure is the sharper half.** This project *already knew* the shape of
this bug — `.claude/hooks/wikilink-guard.sh` exists because `[[a|b]]` split across a newline
breaks in exactly the same way, and the 17-link incident that motivated it is in
`LEARNINGS.md`.

> "**Knowing the shape of a bug in one syntax did not transfer to the same bug in prose.**"

**(2) Inline markup — and this one defeated the fix for (1).** `scripts/59_prepublish_audit.py`
was promoted out of `LEARNINGS.md` *specifically* to be newline-tolerant. But `\s+` bridges
whitespace and **nothing else**. Measured against its own `_nl("0% false-positive rate")`:

| text | result |
|---|---|
| `a 0% false-positive rate` | FOUND |
| `a 0%`⏎`false-positive rate` | FOUND — the bug it was built for |
| `a **0%** false-positive rate` | **MISSED** |
| `a *0% false-positive* rate` | **MISSED** |
| ``a `0%` false-positive rate`` | **MISSED** |

Only emphasis bracketing the *whole* phrase survives, because then the markers fall outside
the matched span.

> "In a repo that bolds nearly every number, that is most of the corpus. **My first sweep
> for the retracted claim returned 0 matches; a corrected sweep finds 17.** *A banned-text
> auditor returning zero looks exactly like a clean repo.*"

Fixed by searching the text a **reader** sees as well as the bytes on disk, and labelling
such a hit `[markup-stripped]`. Note one deliberate exclusion: `_` is **not** stripped,
because in this codebase it is an identifier (`scores_v2.json`) far more often than an
emphasis marker, and stripping it would manufacture false positives.

**(3) Corpus scope.** Covered in §3.3.

### 3.2 A claim is a subject plus a predicate

Sweeping for a retracted claim looks like string matching and is not. The claim was *"a
wrong antibody clears all five gates"*.

| search | fails because |
|---|---|
| `grep "all five"` | **150 hits** — mostly "all five **samples**" (diffusion draws) and "all five **external tools**". Different claims. |
| `grep` + *is "construct" nearby?* | **proximity is not qualification** — an unrelated sentence can contain the word |
| require the predicate only | a *correct* statement of the claim contains the predicate too |

What worked: require the **subject** (`hyhel|lysozyme|cetuximab|wrong antibody`) within
±260 characters, *then* ask whether a qualifier (`113|119|C6|C9|truncat|repaired`) is
present. That cut 79 flagged sites to 17 and found `05-experiment-design.md:327`, which
**two earlier sweeps had marked clean**.

> "**A claim is subject + predicate; searching for half of it returns the wrong set in both
> directions.** … encode *what the claim asserts about what*, not the memorable phrase. The
> memorable phrase is why it spread; it is not what makes it the claim."

And the reason `05-experiment-design.md:327` survived two sweeps is worth its own line: the
first sweep scored it "construct named nearby: yes" because the word *construct* appeared
within ±400 characters of an unrelated sentence. **Proximity is not qualification** — a
lesson written down after sweep 1 and then relied on again in sweep 2.

### 3.3 Three corpora, three tools, and the one everybody reaches for

Git stores every version of every file as an immutable **blob**, addressed by the SHA-1 of
its contents. A commit points to a tree mapping paths to blobs. `git rm --cached foo` writes
a *new* commit whose tree omits `foo` — **the blob is untouched and remains reachable from
every earlier commit.**

> "So `HEAD` no longer contains the file and the repository still does. **Every tool that
> reads *files* — `git grep`, `find`, `cat`, any script that opens paths — inspects the
> working tree or a single commit, and reports the first condition as though it were the
> second.**"

| you ask | the tool that answers | the tool people use |
|---|---|---|
| is it in the checkout? | `git grep`, `find`, any file read | ✅ same |
| is it in the repository? | `git log --all --diff-filter=A --name-only -- <path>` | ❌ `git grep` |
| does the remote still hold it? | `gh api repos/<o>/<r>/commits/<old-sha>` | ❌ a fresh clone |

> "*A question about a repository is not a question about a directory, and no error tells
> you which one you asked.*"

### 3.4 Reachability, and why a fresh clone proves nothing

`git clone` performs a **reachability walk**: it starts from the remote's refs and
transitively fetches only objects those refs can reach. Objects no ref points to are
**unreachable** and are never sent.

A history rewrite plus a force-push makes old commits unreachable *from the branch*. **It
does not delete them from the server.** GitHub retains unreachable objects indefinitely and
will serve any of them by SHA.

> "Therefore: cloning the remote and finding nothing is exactly what you would see whether
> the objects were deleted or merely orphaned. **The clone cannot distinguish the two
> cases.** This is not a subtle failure — it is a *structural* one, and I did not see it
> until an agent pointed at it."

**The timeline, all on 2026-09-26:**

| time | event |
|---|---|
| 15:46 | repo created on GitHub, **private** |
| ~15:50 | pushed — history still contained the organisers' handbook and three email addresses |
| 16:10 | `git filter-repo` scrubbed both; force-pushed |
| 16:15 | verified with a **fresh clone**: five checks, all zero. **Reported clean.** |
| ~19:00 | an agent probed the **remote by old SHA**: **HTTP 200** |

Still retrievable at 19:00 from a repository declared clean three hours earlier:

```
gh api ".../contents/README.md?ref=8930022..."  -> 3 organiser email addresses
gh api ".../git/trees/8930022...?recursive=1"   -> handbook.pdf, 727,284 bytes
```

Three checks had been run, each with a different blind spot, and **each answered
truthfully**: `git grep` read the working tree; `git log --all` and
`git cat-file --batch-all-objects` read the *local* object database, which after
`filter-repo` genuinely *was* clean; the fresh clone performed a reachability walk.

> "**Each answered truthfully. None answered the question.**"

A detail that destroys the local evidence too: `filter-repo` **deletes the `origin`
remote**, which resets the remote-tracking reflog — so even the record that a pre-rewrite
push happened is gone.

**Remediation.** Force-pushing does not help. The repository was one day old with 0 forks,
0 stars, 0 issues, so it was **deleted and recreated** rather than requesting a GitHub
Support garbage-collection: *"immediate and independently verifiable."* Afterwards the old
SHAs return **404** where they returned 200.

*The window matters: with a single fork, the orphans live in the fork and deletion does not
reach them. Deleting a remote is only cheap while the repository is young.*

### 3.5 A probe needs a control in **both** directions

The September incident used a negative control — a never-pushed SHA, which returned **422**,
proving the 200s were real retention. That is half of it.

Later, probing a stray repository for a SHA from a rejected push returned **404** — and so
did the never-pushed control. **Both outcomes were identical, so the probe proved nothing.**

> "That probe is worthless without **two** controls — a **negative control**, a never-pushed
> SHA which must 404 ('without it a 200 might just mean *the API returns 200 for
> anything*'), and a **positive control**, a SHA known to be present which must 200
> ('without it, a 404 might mean *the probe is broken* rather than *nothing is there*')."
>
> "**One control tells you the instrument can say 'no'; the other tells you it can say
> 'yes'.**"

---

## 4. Guards that could not see their own corpus

A **guard** is any automated check whose job is to fail. The project's organising belief is
that *a lesson written in prose cannot fail a build*, so lessons get promoted into guards.
The corollary is the trap:

> "**A guard that cannot fail is not evidence** — and it can be unable to fail for reasons
> nobody notices."

Five instances, in one session:

**(1) The pre-publication auditor could not see a bolded phrase.** (§3.1 above.) Built
specifically for newline-tolerance; blind to `**0%**`. First sweep 0 matches, corrected
sweep 17.

**(2) A test matched its own description of the bug.** The first version of
`test_doctor_venv_check_is_functional_not_a_substring_of_the_path` grepped the doctor's
source for the literal `"locksmith" in sys.prefix` — and **failed on the *fixed* file,
because the module docstring quotes that expression to explain what was wrong with it.** It
walks the AST now.

**(3) A preflight whose required set was backwards.** `scripts/00_doctor.py` marked every
external tool — `DockQ`, `prodigy`, `ipsae.py`, `anarcii`, `freesasa` — as `required=False`,
so a machine with **none** of them printed `All required checks passed.` and exited 0.
Meanwhile the venv check *was* required and tested a **substring of a path**
(`"locksmith" in sys.prefix`), so a correct checkout in a directory named `citest` failed.

The inversion is the finding, not the omission:

> "Validating the package needs the five tools and **no GPU**. The preflight demanded a
> **GPU** and **none of the tools**. It could not fail for a grader missing everything it
> needed, and *did* fail for a grader whose only sin was owning a CPU."

A third gap: the README tells you to install ~4.7 GB of NetSolP ONNX models, and the
preflight checked NetSolP **zero** times.

> "**The way a guard usually cannot fail is not that someone disabled it; it is that its
> required set was assembled from convenient checks rather than from what the job actually
> needs.**"

**(4) A blocker is a guard on your attention.** See §6.

**(5) A guard written to catch silent exclusion silently excluded.** The decoy analysis
printed `n = 16` from 18 backbones with no explanation. Two backbones produced **no antigen
contact at all**, making the fraction 0/0 — undefined, *a real observation, not a parse
failure* — and the script `continue`d past them.

> "I caught it only by asking why n wasn't 18. **This is the fourth instance this session of
> a check that could not see part of its own corpus, and the first where the blind spot was
> in code written that same day to fix exactly that class of bug.**"

*A mean printed without its denominator is a silent exclusion.*

### 4.1 The only durable answer: mutation testing, with a control

> "When a check comes back clean, ask *what it would have done had the answer been no* — and
> confirm that **by breaking something on purpose.** Every mechanism repaired this session is
> now mutation-tested, which is the only version of that question that survives being
> forgotten."

The discipline, worked: each mutation applied to a *copy* of the package — table-row
`0.904 → 0.781` → exit 1; prose `18.2% → 40.0%` → exit 1; fenced total `0.800 → 0.931` →
exit 1; a banned string reintroduced → exit 1; and **the control, an unmodified package →
exit 0, zero findings.**

> "A guard that only ever passes is not evidence."

And a failure *of the control*, which is the subtlest thing in the whole period:

> "**My first control for the auditor fix exited 1 on a 'clean' repo.** I had committed the
> auditor *into* the test repo, and its new comment contains the example phrase. **A control
> that fails for a reason you did not model is not a control.**"

---

## 5. Convergence is not termination

Five sweeps were run for one retracted claim. Counts: **13 → 0 → 1 → 0 → 0.**

Read that series carefully, because every term teaches something:

- **Sweep 1 found 13.** Named files, proximity heuristic.
- **Sweep 2 found 0** — and that zero was produced by an over-narrow pattern, not a clean
  corpus. *"A sweep reporting 0 live occurrences on its first run — that is what an
  over-narrow pattern produces, and it is indistinguishable from a clean corpus."*
- **Sweep 3 found 1**, at a site sweep 2 had explicitly marked clean.
- **Sweeps 4 and 5 found 0.**

> "**A converging series is not a proof of termination.** Sweeps 1→3 each found sites the
> previous had marked clean. That the finds are decreasing is evidence of **convergence**; it
> is **not** evidence that zero remain. The honest claim is **'no known unqualified
> occurrences after five sweeps, with the per-sweep counts shown'**, which lets a reader
> judge the trend — not **'zero'**, which asserts a termination that was never
> demonstrated."
>
> "**When a search process keeps finding what the last pass missed, report the series rather
> than its last term.**"

The project went further and listed "a sixth sweep finding a new site" as **expected, not
excluded**. That is what an honest claim about an incomplete process looks like.

**And the rule was broken in the very next paragraph.** Sweep 4 cleared a hit on the grounds
that "the file names the 113-mer in its §Design section" — *file-level* proximity, a weaker
version of the ±400-character proximity that had been written up as invalid two screens
above.

> "**A rule you just wrote applies to you first, and the place it is most likely to be
> broken is the next paragraph.**"

---

## 6. A blocker is a claim, and it decays like any other claim

Two instances, eleven days apart, and the second cost real money that was nearly spent.

### 6.1 The blocker nobody opened the file to check

Register §D2 recorded that a [reliability](04-measurement-theory.md#13-reliability) figure of **0.629** *"does not reproduce from the
recorded inputs under any standard estimator tried"*, and that *"the original script would
settle it"*.

**Both halves were false.**

It reproduces — as a *different estimand*. With between-design sd of the 7-seed means
**0.290** and noise sd of a 7-seed mean **0.176**:

```
r₇ = 1 − 0.176² / 0.290² = 1 − 0.030976 / 0.084100 = 0.6317      (recorded 0.629)
```

and the noise chain is internally consistent: `0.467 / √7 = 0.1765 ≈ 0.176`. The competing
figures 0.276 / 0.296 are **single-seed** reliabilities.

> "Diffing them against 0.629 is this project's own *never diff a single observation against
> an aggregate*, one level up: **never diff two reliabilities without checking they are
> reliabilities of the same thing.**"

And *"the original script would settle it"* reads as *the script is lost*.
`scripts/35_winner.py` had been tracked since the initial commit, with the estimator at
**lines 202–206**.

> "**Nobody opened the file. A blocker is a claim, and it decays like any other claim.** This
> one gated the entry for **six days**, and `STATE.md` carried a work item that four
> documents dated 2026-09-23 had already completed."

A beautiful sub-result fell out. Recomputing from raw folds gave standard deviations **~2×
smaller** than recorded — because those were computed under the pre-2026-09-22 surrogate
anchors. But:

> "**Reliability is a ratio and survives a rescale; a standard deviation does not.** So *'does
> not reproduce'* was true of the **standard deviations** and never of the **reliability** —
> which is the whole confusion in one sentence."

### 6.2 The rental that was never needed

For **eleven days**, three separate documents stated that sequencing the unconditioned arm
required a rented `sm_86` card. The argument:

> RFantibody pins `torch==2.3.*`. PyPI's DGL ships `libgraphbolt_pytorch_<v>.so` for
> 2.0.0–2.2.1 only. Those wheels carry **no PTX**, so there is no forward-JIT to `sm_120`
> (Blackwell). Therefore it cannot run on this machine.

> "**Every clause is true. The conclusion is false.** The argument establishes that it cannot
> run on *this GPU*; it says nothing about the *CPU*, which was never in the comparison."

Verified by running the tool instead of reasoning about it:

```
$ PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 2 -t 0.2
No GPU found, running ProteinMPNN on CPU
MPNN generated 2 sequences in 1 seconds
```

**The one real obstacle is not a device problem and looks nothing like one.** The CLI
subprocesses a bare `python` (`cli/inference.py:294`), so without the venv's `bin` on `PATH`
it dies with `FileNotFoundError: 'python'` — *"a plausible reading of that traceback is 'the
environment is broken, as predicted', which is probably why the CPU route was never
pursued."*

**This is the canonical instance of the chapter's other theme.** The decoy-patch control had
been believed GPU-blocked on *identical* reasoning and ran locally on CPU for **\$0** on
2026-09-28 — and that discovery was never carried **one row down the same table**. The
2026-09-29 session's next-steps list proved the CPU route in item 1 and then asserted the
rental in item 2.

Worse: `prereg_2026-09-23_depth_sweep.md:24` had already costed sequence generation at
*"~8 s per 8 draws per backbone"* — **five days before** the opposite was written down.

> "**A blocker inherited from a neighbouring task is not evidence. Re-run the check per
> task.** Cost of checking: one minute. Cost of assuming: eleven days of a false blocker on
> the roadmap, and two offers to spend money that did not need spending."

### 6.3 The null that closed a budget line

The period's last finding is treated in full at
[§1.4 of the experiment-design chapter](05-experiment-design.md#14-when-the-formula-will-not-do-simulate-the-critical-value-and-report-power-in-decision-units),
[§1.5 of the allocation chapter](06-allocation-and-selection.md#15-and-a-third-time-in-the-other-direction--the-inversion-that-proves-the-rule)
and [C7](CORRECTIONS.md#c7--the-course-undercounts-its-own-most-repeated-error-and-the-newest-instance-bought-something);
the short version belongs here because of *when* it happened.

On 2026-09-28 a planning document was marked superseded on the grounds that the depth sweep
had already answered *"no, do not spend the money"* — χ² = 22.91 on 17 df, **p = 0.152**. On
2026-10-03 that decision was priced: the test had **23% power against the ρ the data
themselves fitted**, and 80% power arrives only at ρ ≈ 0.24, five times larger.

> **A pool in which three of eighteen backbones cleared five times more often than the rest
> would have been missed three times in five.**

This is the project's **seventh** small-*n* null read as evidence of absence, and the first
to carry a **spending decision** rather than a rule. The analysis cost no folds, no GPU and
no money, and would have been equally free before the decision.

---

## 7. The pattern underneath all of it

Every section above is an instance of one thing. Lay them side by side:

| the check | the corpus it actually saw | the corpus the question was about |
|---|---|---|
| `grep` on hard-wrapped prose | **lines** | the document's text |
| the newline-tolerant auditor | **raw bytes** | the text a reader sees |
| `git grep` | the **working tree** | the repository |
| a fresh clone | objects **reachable from refs** | objects the remote retains |
| the preflight's required set | checks that were **easy to write** | what the job needs |
| the decoy analysis | backbones with a **defined ratio** | all 18 backbones |
| the exchangeability null | 18 backbones × 8 sequences | effects it had power to see |
| the rental blocker | **this GPU** | this *machine* |

**One failure mode, eight costumes.** In every row the check was correct, ran successfully,
and returned a true answer — to a question narrower than the one being asked. And in every
row, the narrow answer and the broad answer **look identical when the answer is "nothing
found"**.

That is why *"it came back clean"* is never, on its own, a finding.

### 7.1 The second pattern: corrections do not propagate by themselves

The period produced sixteen recorded instances of a finding that reached one place and not
its neighbour. A representative few:

- The 96.0 → 94.0 change reached the repository and the package and **nothing else** — four
  lecture chapters carried the stale number *under a sentence assuring the reader that
  Challenge 1's numbers stood*.
- The NetSolP correction reached `03-the-toolchain.md` and **not** `00-orientation.md` or
  `10-glossary.md` — *"the fix went to one chapter and not to the two a reader opens
  first."*
- An index of a correction claimed to list live occurrences and had **4 rows**; the true
  count was **40**. *"An index that looks authoritative while being 12% complete spends a
  reader's scepticism in the wrong direction."*
- A retraction that lived **only** in the retraction register. *"A retraction that lives
  only in the retraction register is a retraction nobody reads."*

And the structural reason, from §5.4 of the 2026-09-26 session, which is the most useful
sentence in the period for anyone who writes documentation:

> "**A stale number is an ordinary defect a reader may catch. A stale number plus an
> explicit assurance that the number is current is worse than either: it spends the reader's
> scepticism budget in the wrong direction.**"
>
> "*A correction is scoped to the defect that prompted it, and its wording must say so.
> 'X is unaffected by this' is a claim about one causal pathway; 'every X in this document
> stands' is a claim about all future pathways, which no author is in a position to make.*"

### 7.2 The taxonomy that made the register work

Worth stealing wholesale. Four statuses, and the fourth is the one people skip:

| status | meaning | example |
|---|---|---|
| **WITHDRAWN** | false, and **nothing replaces it** | "there is a code-path discrepancy in `ipsae.py`" — there is none. *"The correct end state is silence, not a new number."* |
| **SUPERSEDED** | a corrected value replaces it | composite 96.0 → **94.0**. *"The claim's shape was right; its value was wrong."* |
| **REFUTED** | tested against new evidence and failed | the contact-count rule. *"The claim was coherent and testable and the test was run — the refutation carries information the withdrawal does not."* |
| **FLAGGED** | known not to reproduce, **deliberately not corrected** | *"An unreproduced number must be marked as such rather than silently replaced by your best current guess, because a guess entered into the record is indistinguishable from a measurement one week later."* |

And the rule that keeps the record worth having:

> "A results file is a **record of what was measured and believed at a time**. Editing it to
> agree with today's understanding destroys the evidence that the understanding changed —
> and that evidence is the most valuable thing the project has produced."

With exactly one class of exception, stated absolutely:

> "*For most documents, staleness is a defect to fix; for a pre-registration, staleness is
> the point.*"

---

## 8. What it cost, and what it bought

**Cost.** Zero GPU-hours for scoring. Zero dollars. The only compute spent was ~6 CPU-hours
on the decoy control, which had been budgeted at *"a few GPU-hours and a few dollars"* and
ran for **\$0**. Against that: one leaked repository (caught, deleted, nothing public), two
killed shells, and eleven days of a false blocker.

**Bought.** A retraction register with 20 withdrawn claims and 5 flagged figures, where
before there was a pointer saying "five and four" that nobody had ever counted. A test
suite that went from **34 to 44** tests, every repaired mechanism mutation-tested. CI that
did not exist. A published repository with a verified-clean history. And the course you are
reading, corrected.

**The honest ledger** — things still wrong, named rather than hidden:

- *"Nineteen of twenty live-text notes rest on line-oriented greps. The register is
  **correct** about what was retracted and **unreliable** about where stale copies remain."*
- The sweep's subject list is hand-written; a claim phrased without any of its six words
  would be missed.
- `_BANNED` is a hand-maintained grep that only catches repeats.
- The machine-readable results store — the remedy proposed on day one of the audit — was
  never built.

---

## What to take away

1. **Every check answers a narrower question than the one you asked, truthfully.** Before
   believing a clean result, ask what the check would have done had the answer been *no* —
   and then break something on purpose to find out. A check that cannot fail is not
   evidence.

2. **A record correct locally can be wrong globally, because prose has no compiler.** Two
   places encoding one fact will diverge, and nothing will tell you. The only durable fixes
   are to have one place, or to generate one from the other.

3. **An edit to a derived object has a lifetime bounded by the next derivation.** Correct
   documents at their generator, and verify the fix from the artefact a consumer reads,
   produced by the process that produces it.

4. **"What is this number *of*?" beats "is this number right?"** Three correct measurements
   of the wrong molecule pass every numeric check you can write.

5. **A coincidence that explains part of the evidence terminates the search.** Require an
   explanation to account for *every* observation.

6. **Convergence is not termination.** Report the series, not its last term.

7. **A blocker is a claim and decays like one.** Re-run the check per task; a blocker
   inherited from a neighbour is not evidence. Cost of checking: usually a minute.

8. **A correction is scoped to the defect that prompted it, and must say so.** The most
   dangerous document is a stale number underneath an assurance that it is current.

---

*Next: nothing. This is the last chapter, and the project is still open —
[STATE.md](../../STATE.md) carries what remains. For the five-minute version of everything
above, see [the short version](../the-short-version.md).*
