---
date: 2026-10-05
tags: [project, session, lecture, learning, documentation]
status: living
---

# Teaching the audit period, and the clause that outlived its correction

**2026-10-05.** No GPU, no money, no design change, no new measurement. Everything below is
documentation work plus two arithmetic recounts. One new lecture chapter, two new course
corrections, two new teaching sections, one new exercise, and six stale sites repaired.

The session opened on a maintenance request — *the lecture series was written before last
week's work; update what is needed* — and the useful finding is that **the update was not
where the request pointed.**

---

## 1. What prompted it, and what the request turned out to mean

The lecture series was last edited **2026-09-30**. Since then there has been one
substantial session, **2026-10-03**. The obvious reading of the request is "propagate
2026-10-03 into the chapters".

That reading is wrong in both directions, and establishing *why* took the first third of
the session.

**Too narrow.** A sweep of all fourteen lecture files for the 2026-10-03 subject matter —
the depth sweep, stratum C, backbone exchangeability, `X² = 22.91`, the rental decision —
returned **zero hits on every load-bearing term.** The single match for `exchangeab` is an
unrelated passage about random subsets retaining a pool maximum. The course does not
contain the claim that 2026-10-03 corrected, so there was nothing to correct. The work was
**additive**, not corrective.

**Too broad.** Chapter 07's narrative stops on **2026-09-22**. The entire audit period —
re-screen, constrained campaign, decoy control, publication, depth sweep, power audit — is
absent from the course. Eleven days, seven session documents, and the course's own front
page describes their output as *its main result*. The course was teaching the conclusion
and not the work.

> **The transferable form: "update the docs for last week's work" is a request about a
> date, and the answer is usually about a boundary.** What had gone stale was not a set of
> numbers; it was the course's *scope*. Checking whether the subject matter was present at
> all — one grep, thirty seconds — is what separated the two.

---

## 2. The clause that outlived its own correction

The sharpest defect found today is four words long and is not about last week at all.

`05-experiment-design.md:604` was amended on **2026-09-28** when the decoy-patch control
ran and passed. The amendment is correct and visible:

> "Finally, ~~the strongest available control remains conceded and unrun~~ — **run
> 2026-09-28 and it passed**: 0.803 on the decoy face, 0.000 on the epitope…"

The next sentence, line 605, reads:

> "It costs a GPU run."

It does not. It ran locally on CPU at ~26 min/backbone for **$0**. So from 2026-09-28 until
today the paragraph asserted both that the control had run and that it was unaffordable.

**Why this is worth a section rather than a line.** The site was not missed by a sweep — it
was *edited*, correctly, by someone who had the right information, and the stale clause sat
four words after the correction they made. Every mechanism this project has built for
propagation operates at file or corpus granularity: the register's live-text notes, the
newline-tolerant auditor, the subject+predicate sweep. None of them can see this, because
the file *was* visited and the claim *was* corrected.

> **An amendment is a change to a sentence; staleness is a property of the paragraph. After
> correcting a claim, re-read the paragraph that contained it, not the clause you changed.**

Three further sites said the decoy control "was never run" — `07-the-campaign.md:523`,
`08-what-broke.md:341`, `11-study-plan.md:230` ("A few GPU-hours and a few dollars"). Those
are ordinary propagation failures of the kind §7.1 of the new chapter catalogues. The
line-605 case is a different and worse species.

---

## 3. The course was miscounting its own central weakness

`08-what-broke.md:512` tallies generator 1 — *a small-n null read as evidence of absence* —
at **≥6**. `10-glossary.md:245` and `README.md` both said **"Four claims"**.

Three counts, in one course, for what the course calls the project's most repeated error.
And two of them were *already* inconsistent with each other before 2026-10-03 added a
seventh instance.

The resolution is not to make the numbers agree. **They count different sets, and that
distinction is itself the project's own lesson one level up:**

| claim | counts | status |
|---|---|---|
| "Four were corrected in a single day" | one day's corrections (2026-09-20) | **true, unchanged** |
| "≥6" in the frequency table | lifetime instances | → **≥7** |
| "Four claims" in README / glossary | lifetime reversals | → **at least seven** |

Conflating the first with the other two would be *a rate is a property of every parameter
it was computed under* — the project's own §C8/§C9 finding — committed inside the file that
records it. Fixed in all three places, each stating which set it counts.

**The seventh instance is qualitatively different and that is now stated:** the previous six
each cost a *rule*. This one closed a **144-fold experiment** and justified not spending
money. It is the first to carry a spending decision.

---

## 4. What was written

### 4.1 `docs/lecture/12-the-audit.md` — new chapter, 8,236 words

Teaches **2026-09-23 → 2026-10-03** from first principles. Structure:

| § | subject |
|---|---|
| 0 | what an audit period is; why this one was not cleanup |
| 1 | reading your own record finds what living in it cannot; *prose has no compiler* |
| 2 | documents are owned by their generators; orphans; rounding across a decision boundary |
| 3 | **every search answers a narrower question than the one you asked** |
| 4 | five guards that could not see their own corpus |
| 5 | convergence is not termination (13 → 0 → 1 → 0 → 0) |
| 6 | a blocker is a claim and decays like one |
| 7 | the pattern underneath all of it |
| 8 | what it cost and what it bought, including the unpaid debts |

The organising claim, and the reason the chapter is field-independent:

> **Every check you run answers a narrower question than the one you asked, and it answers
> that narrower question truthfully** — so a clean result is evidence about your instrument
> before it is evidence about the world.

§7 tabulates eight instances against that single schema — `grep` seeing **lines** not text;
the newline-tolerant auditor seeing **raw bytes** not rendered text; `git grep` seeing the
**working tree** not the repository; a fresh clone seeing **reachable objects** not retained
ones; a preflight's required set seeing **convenient checks** not job requirements; the
decoy analysis seeing **16 backbones with a defined ratio** not 18; the exchangeability null
seeing **a design** not an effect size; the rental blocker seeing **this GPU** not this
machine.

*One failure mode, eight costumes — and in every row the narrow answer and the broad answer
are indistinguishable when the answer is "nothing found".*

**Deliberately not done: the chapter is not indexed by `CORRECTIONS.md`.** It was written
after C1–C8 and incorporates them, so it carries a dated scope notice instead of the
standard warning banner. A banner saying "corrections C1–C8 apply" would be false on a
document that already contains them.

### 4.2 Two course corrections

**C7** — the undercount above, with the 2026-10-03 power table, the two riders (the
original test was *conservative*, real type-I **0.042**; the design that would have settled
it was the one declined), and the explicit warning not to merge the three counts.

**C8** — the decoy control has run; four live sites indexed; and the correction to the
course's standing advice. The course says *"before porting a pinned stack, price an hour of
the hardware it was pinned for"*, which is correct and stays. C8 adds its missing half:

> **The argument that a pinned stack cannot run on your GPU says nothing about your CPU,
> which was never in the comparison.** The advice silently assumes the only options are
> *port it* or *rent the chip it was pinned for*.

### 4.3 Two new teaching sections, both filling gaps the course had

**`05-experiment-design.md` §1.4** — *when the formula will not do.* Nothing in the course
taught **simulation-calibrated critical values** or **power in decision units**, and
2026-10-03 needed both. Contains the full derivation of why χ² was suspect here (expected
successes per cell `8 × 0.083 = 0.67`), the calibration result, and the point most likely to
be missed:

> The asymptotic test was **conservative, not liberal** — and the conclusion did not change.
> *Calibrating the critical value is how you tell "the test was wrong" apart from "the test
> was underpowered" — two diagnoses with different fixes, which an uncalibrated p-value
> cannot distinguish.*

**`06-allocation-and-selection.md` §1.5** — the allocation inversion. Depth now beats
breadth (**0.802 vs 0.699** on 288 folds), inverting §1.4 directly above it on identical
hardware and budget. The section gives the procedure rather than the answer: ask what the
estimator *is*. A maximum over designs → breadth. A population correlation → breadth. A
**within-backbone dispersion** → depth, and qualitatively so, because below k = 2 the
estimand **does not exist**.

> *When your target quantity is a spread, replicates are not precision — they are the
> measurement.*

### 4.4 Exercise A6, and the counts

`11-study-plan.md` Track A (analysis only, no GPU) gains a four-step reproduction of the
power audit, ordered so that **step 1 is reproducing the five published statistics before
computing anything new** — because a power curve measures whatever test you implemented.
Step 4 is restating the result in decision units, with the note that *steps 1–3 are the
easy part and persuade nobody.*

The README's provenance block was recomputed and had drifted a third time:

| | was | now |
|---|---|---|
| Python lines | 21,367 | **23,080** |
| tests | "34 *(42 as of 2026-09-29)*" | **44** |
| results files | 73 | **78** |
| session docs | 25 | **29** |
| Markdown words | ~280,000 | **~321,000** |

Two deliberate abstentions, both recorded in the file:

- **`5 adversarial audits` was left unchanged and unverified.** It counts work not
  identifiable from filenames (`ls results/ | grep -i audit` gives 4 files, 3 distinct, and
  audits also live in the register and the session docs). Recomputing it would have meant
  inventing a number. *A count you cannot derive is better left with its provenance
  admitted than refreshed with a guess.*
- **The word total says "in the repository", not "tracked"**, because Chapter 12 was not
  committed when the number was written: 312,770 tracked plus 8,236 untracked.

The test count itself carried a methods lesson worth the two lines it got:
`grep -c "def test_"` gives **40**; `pytest --collect-only` gives **44**, because four tests
are parametrised. *A count is a claim about its own method as well as its subject.*

---

## 5. How to verify this, and what healthy looks like

```bash
cd locksmith-antibody-hackathon
uv run pytest -q                       # 44 passed
```

The load-bearing one is **`test_every_internal_markdown_anchor_resolves`**, which
`rglob`s every `*.md` outside `.venv`/`vendor`/`node_modules` — so it scanned the new
chapter and every cross-reference written today. That is the whole verification story for
link correctness, and it is why anchors were written rather than checked by eye.

```bash
# the four decoy-control sites are struck through, not silently edited
grep -n "was never run\|costs a GPU run\|few GPU-hours" docs/lecture/*.md

# the three counts now state which set each counts
grep -n "≥7\|at least seven\|corrected in a single day" docs/lecture/08-what-broke.md \
  docs/lecture/10-glossary.md docs/lecture/README.md

# every banner carries C1–C8 (11 files, identical text)
grep -l "corrections C1–C8" docs/lecture/*.md | wc -l     # 11
```

**Healthy:** 44 passing; 11 identical banners; zero broken anchors across 145 Markdown
files; the four stale sites visibly struck through with pointers rather than rewritten.

**Plausible-but-wrong looks like:** the chapter table listing thirteen chapters while the
prose still says "twelve-chapter course" — i.e. the index updated and the sentence beside it
not. That is this project's signature defect and it was checked for explicitly
(`grep -n "twelve" docs/lecture/*.md`, three remaining hits, all unrelated: twelve-point
ambiguity, twelve hundred tries, twelve recommendations).

---

## 6. What is stubbed, crude, or not claimed

- **Chapter 12 is built from the session documents, not from the artefacts they describe.**
  Numbers were taken from the docs' own reporting; `results/retractions.md` entries and
  `scripts/59_prepublish_audit.py`'s docstring were not independently re-derived. The
  chapter is therefore as accurate as the session record, which the period itself showed to
  be good but not perfect.
- **Nothing was committed.** The tree was clean at session start, on `master`, and all
  changes sit in `docs/lecture/` plus this file.
- **Chapters 05 and 11 still carry no warning banner**, as before today. They now carry
  inline C7/C8 pointers, which is more precise. Not changed unilaterally because it alters
  the established shape of two files.
- **The 2026-09-30 → 2026-10-03 session documents were not re-audited.** This session
  trusted them.
- **No claim is made that the course is now free of stale sites.** Today found four that
  five previous sweeps for a *different* claim had no reason to look for. Per the
  convergence lesson in §5 of the new chapter: this is one more pass, not a termination.

---

## 7. What went wrong

**A near-miss on the governing policy.** The first plan was to update numbers inline across
the affected chapters. `CORRECTIONS.md`'s own preamble forbids exactly that — *"Chapters are
not individually rewritten with provisional numbers — doing that is the exact defect the
course documents"* — with the boundary stated in C3: **prose that quotes a number is
indexed; arithmetic that produces one is corrected.** Caught by reading the file's header
before editing it rather than after. The one in-place edit made today (the `≥6 → ≥7` tally)
falls on the correct side: it is a count a reader reruns from an evidence list, and leaving
it would have the course teaching a wrong count of its own central weakness.

**An agent's file-count was wrong and was checked.** The lecture map reported the warning
banner present in 8 files and absent from 06, 08 and 09. It is in **11**, including those
three. Verified with `grep -l` before the propagation script ran, which is the only reason
all eleven were updated. *A delegated enumeration is a claim like any other.*

**`git ls-files '*.md' | xargs cat` undercounted by 15,546 words**, silently, because
knowledge-note filenames contain spaces and `xargs` split them — the errors scrolled past as
`cat: knowledge/Antibody: No such file or directory` while the pipeline still printed a
plausible total. Re-run with `-z`/`xargs -0`. *A word count that printed is not a word count
that succeeded; this is §3 of the new chapter arriving while writing §3 of the new chapter.*

---

## Related

- [The audit chapter this session wrote](../lecture/12-the-audit.md)
- [The course corrections register](../lecture/CORRECTIONS.md) — C7 and C8 added today
- [A null with 23% power, and a blocker that was never real](2026-10-03-a-null-with-23-percent-power-and-a-blocker-that-was-never-real.md)
- [The project-wide retraction register](../../results/retractions.md) — §B11, §B12
