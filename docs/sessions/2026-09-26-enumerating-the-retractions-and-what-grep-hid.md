---
tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [the register this session produced](../../results/retractions.md), [the session index](README.md)

# Session 2026-09-26 — Enumerating the retractions, and what a line-oriented grep hid

## 0. Session at a glance

No experiments, no GPU time, no new designs. This was a **record-integrity** session: the
project had been carrying a pointer to "the five stale-document retractions and four
overstated claims" in three consecutive session docs **without anyone ever writing the
list**, and `STATE.md` could not be made honest while that list did not exist.

What changed:

| # | thing | outcome |
|---|---|---|
| 1 | The 2026-09-25 working tree | **committed** — 7 commits, `4241bb6..d5cf334`, 22 files |
| 2 | `results/retractions.md` | **new** — 20 withdrawn/superseded/refuted claims + 5 flagged |
| 3 | `docs/lecture/CORRECTIONS.md` | **fixed** — it contradicted itself and had gone stale |
| 4 | `STATE.md` | **rewritten** — §8/§9 described the pre-MSA-discovery world |
| 5 | A live retracted claim in `results/constrained_paired.md` | **corrected, twice** |
| 6 | Stale Challenge 1 `96.0` in four lecture chapters + the pitch outline | **indexed as course correction C3** |

The one genuinely new piece of knowledge is in §5, and it is about `grep`, not about
antibodies.

**Nothing about the designs changed.** Challenge 1 is `mpnn_T0.5_s104_036 N55Q` at **94.0**
and Challenge 2 is `bb_8_0` at **93.6**, both viable, both unchanged by this session.

---

## 1. The problem this session addressed

A project that corrects itself in public accumulates a second-order problem: **the
corrections themselves become a body of knowledge that can go stale, scatter, and
contradict each other.** This project had reached that point.

The concrete symptom. `docs/sessions/2026-09-25-...md` §9 item 1 read:

> **The five stale-document retractions and four overstated claims** flagged by the audits —
> still outstanding, and now the largest known gap between what the record says and what is
> true. Unblocks a clean `STATE.md`.

That sentence had been carried forward across sessions. But **there was no list.** Grepping
the repo for an enumeration returns nothing: the claims live scattered across
`results/audit_2026-09-20.md`, `results/audit_response_2026-09-22.md`,
`results/audit_of_audit_2026-09-22.md`, `docs/lecture/CORRECTIONS.md`, several session docs,
and the `_BANNED` dictionary inside `scripts/58_validate_submission.py`.

Why that is worse than it sounds:

1. **A pointer cannot be checked off.** "Five retractions are outstanding" has no
   falsifiable completion condition, so it is carried forward forever at zero cost to the
   carrier. It had been.
2. **It blocked a downstream deliverable.** `STATE.md` is the file a cold reader is told to
   trust first. It could not be made accurate without knowing which of its own numbers were
   retracted — and in fact it was still quoting Challenge 2 as needing "a design its own
   predictor will place", a statement made obsolete by two subsequent campaigns.
3. **The count itself was unverified.** "Five and four" turns out to be an undercount: the
   register lists **20** withdrawn/superseded/refuted claims plus **5** flagged figures.
   Nobody had counted; the number was inherited.

**The transferable form, and it generalises well past this project:** *a known-issues list
that exists only as a summary count is not a list. Until the items are enumerated
individually, "we know about those" is indistinguishable from "we have forgotten which ones
they were."*

---

## 2. Concepts introduced, from first principles

### 2.1 Four different things people call "a correction"

These are routinely conflated, and conflating them destroys the register's usefulness
because they imply different actions. The register uses four explicit statuses:

- **WITHDRAWN** — the claim is false and **nothing replaces it**. Example: "there is a code-path
  discrepancy in `ipsae.py`". There is no discrepancy; the two routes agree to five
  decimals. The correct end state is silence, not a new number.
- **SUPERSEDED** — a corrected value replaces it. Example: Challenge 1's composite
  96.0 → **94.0**. The claim's *shape* was right; its value was wrong.
- **REFUTED** — it was tested against new evidence and failed. Example: the contact-count
  rule. This differs from WITHDRAWN in that the claim was *coherent and testable* and the
  test was run — which means the refutation carries information the withdrawal does not.
- **FLAGGED** — known not to reproduce, **deliberately not corrected**. Example: shortlist
  reliability **0.629**, where the plug-in variance ratio gives 0.276 (`midpoint`) / 0.296
  (`top`). The original script would settle it; guessing would add a fifth number to a
  question that already has four.

The FLAGGED status is the one people skip, and it is the most important. Its discipline:
**an unreproduced number must be marked as such rather than silently replaced by your best
current guess**, because a guess entered into the record is indistinguishable from a
measurement one week later.

### 2.2 Why artefacts are not retro-edited into agreement

The tempting move is to sweep the repo and rewrite every stale sentence. This project
deliberately does not, and the reasoning is worth stating because it is counter-intuitive.

A results file is a **record of what was measured and believed at a time**. Editing it to
agree with today's understanding destroys the evidence that the understanding changed — and
that evidence is the most valuable thing the project has produced. The re-screen table
showing the Challenge 2 ranking near-inverting (the eventual winner at **29th of 30**) is
only legible *because* the old ranking is still written down somewhere.

So the rule is **one fact, one place, plus a pointer**: the correction lives in exactly one
file, and affected documents point at it. The failure mode this avoids is the one the
project already suffered — a convention living in two places and diverging (`surrogate.py`
hardcoding midpoint anchors `2.5/7.0/9.5` while `config/metrics.yaml` declared
`band_value: top`, which changed the selected winner from 1st to 4th).

### 2.3 The pre-registration exception

One class of document must **never** be corrected in place: a pre-registration.

A pre-registration's entire function is to record what was predicted *before* the data
existed. Its evidential value comes precisely from being unmodifiable — an edited prereg
proves nothing, because the edit could have been made after seeing the result. So
`results/prereg_2026-09-23_depth_sweep.md:82`, which carries a retracted error-rate claim,
was **left exactly as written**, and its correction lives only in the register.

This is a genuine asymmetry and worth internalising: *for most documents, staleness is a
defect to fix; for a pre-registration, staleness is the point.*

### 2.4 Hard-wrapped prose and line-oriented search

This one is new to the project and is §5's finding, so it is developed there.

---

## 3. What was built

### 3.1 The 2026-09-25 tree, committed

22 modified files and 2 untracked had been sitting uncommitted — the unrounded-DockQ fix,
the shared `submit/docs.py` template, the documentation guard, the rebuilt package, and the
`python-pptx`/`pytest` declarations. HEAD was still `2e490fe` from the 24th.

Split into 7 commits by unit of work, matching the repo's convention, on `master` (no
remote, linear history, every prior session committed directly there):

```
4241bb6  Read DockQ unrounded: Challenge 1 is 94.0, not 96.0
65ece97  Fix the orphaned Challenge 2 repro doc at its generator, not in the file
c1bd3ed  Guard: cross-check every number a packaged doc asserts against a recomputation
17ecd7c  Pin every ProcessPoolExecutor to spawn; the test found a live offender
6c6293c  Rebuild the deck to the approved six slides; declare python-pptx and pytest
834b9a0  Rebuild the package from the corrected generators: 94.0 and 93.6, VALIDATION PASSED
d5cf334  Session doc for 2026-09-25: correcting documents at their generator
```

Reviewing the diff before committing was not ceremony — it is what surfaced that
`scripts/57`'s corrected text now says the minimum `--allowed_mismatches` is **16**, not
15, which is a live instruction to a grader and belongs in the register (§C2).

### 3.2 `results/retractions.md`

Twenty entries in four groups — **A** scores and deliverables, **B** claims about method,
**C** numbers in shipped or published prose, **D** flagged — each carrying the claim as it
was stated, the replacement value, the file that settles it, and a **live text** note naming
any document that still carries the retracted wording.

The live-text column is what makes it a work list rather than a monument. Without it the
register records that a claim was retracted while saying nothing about whether the
retraction was *propagated*, and §5 shows those are very different things.

Two entries exist only because a number was **recomputed rather than copied** (§C1's
mixed-threshold error rate, §C3's `0.931/0.723/0.794`), and two because a *correction* was
itself audited (§C7, §D1). That distribution is the register's own argument: this project's
errors cluster in sentences it had already written down, not in its code. **Nine of the
twenty were found by auditing prose, not by a failing test.**

### 3.3 The course's corrections file contradicted itself

`docs/lecture/CORRECTIONS.md` is the project's existing, good corrections mechanism —
narrower in scope (what a reader of the lecture course must not trust) and the fuller
treatment of its two items. It had two defects, both found by reading it end to end:

**(a) C1 and C2 contradicted each other, in the same file, for three days.** C1's *"what it
does NOT invalidate"* section listed the contact-count finding as surviving, and told the
reader to "treat the 60-fold ratio as intact". C2, ~80 lines below and raised the same day,
**refutes that finding outright.**

The reasoning error in C1's bullet is instructive. It argued the comparison survives because
both arms were measured *within a single condition*, so the condition cancels. That is
usually sound — but here the condition is not a constant offset, it is the thing that
collapsed the signal: under a correct alignment the design scores **0.012 regardless of its
sequence**, and a ratio of two numbers that are both artefacts of a broken input is not a
ratio of anything. *A within-condition comparison is not rescued by internal consistency
when the condition itself is what moved.*

**(b) C1's ending had gone stale.** It closed on `bb_1_0_dldesign_0` (0.637) as the
replacement Challenge 2 design and declared the zip stale and unsendable. Both were true
when written and neither is now: the constrained re-design campaign superseded that design
with `bb_8_0`, and the package was rebuilt on 2026-09-25.

Both fixed by *annotation*, not deletion — the wrong bullet is struck through and its
reasoning error explained, because *a corrections register is an artefact like any other and
goes stale like any other*, and that is worth showing rather than hiding.

### 3.4 `STATE.md`, rewritten

The old file was 21 KB of interleaved fragments from three sessions, with a correct headline
bolted onto a body that still said Challenge 2 "needs a design its own predictor will
place". Its §8 (blocked) and §9 (shortest path) were pure pre-MSA-discovery text.

Rewritten to eight sections: headline, the two challenges with their full metric tables,
verified-vs-trusted, tests and repo, blocked, what is left, and a reading order. Corrections
are **not** inlined — they point at the register — which is what stops the file re-accreting
into the state it was just rescued from.

One detail worth keeping: Challenge 1's DockQ is printed in `STATE.md` at six decimals
(**0.799579**) rather than three. At three it renders as `0.800 | medium` against a ≥0.80
Good edge, which reads as a bug rather than as the correction it is. The packaged
`scores.md` does the same thing, driven by `Scored.rounding_risk`.

### 3.5 A retracted claim still live in a results file

Found while reading `results/constrained_paired.md` for its conclusions: the unqualified
*"0% false-positive rate — it never accepted a wrong pose in 40 tries"*, which §C1 of the
register retracts. Correcting the shipped document on 2026-09-25 **had not propagated**.

Corrected in place at both occurrences, with the correction stating the numbers an error
rate actually needs:

| DockQ threshold | false positive | false negative |
|---|---|---|
| Acceptable+ (≥ 0.23) | 0% | **58.3%** |
| Medium+ (≥ 0.49) | **12.5%** | 25.0% |

and noting the 0% rests on **4 negatives** — Clopper–Pearson 95% upper bound **0.602**, i.e.
uninformative. The conclusion of that section is unchanged, because ρ = +0.702 was always
what made the confidence worth reading; the error rate was never doing the work.

`results/prereg_2026-09-23_depth_sweep.md:82` carries the same claim and was left alone
under §2.3.

---

## 4. Design decisions

| decision | chosen | rejected | why | cost to reverse |
|---|---|---|---|---|
| Where the register lives | `results/retractions.md`, project-wide | extending `docs/lecture/CORRECTIONS.md` | the course file is scoped to *course readers*; scores, method and shipped prose are not course concerns, and widening it would bury C1/C2 | low — it is one file with inbound pointers |
| Relationship between the two | register = index, course file = detail for its two items | merging, or duplicating C1/C2 into the register | duplication is the exact defect both files document | low |
| Stale artefacts | annotate in place, point at the register | sweep and rewrite | rewriting destroys the evidence that understanding changed (§2.2) | **high** — the original wording is gone once swept |
| Pre-registrations | never edit | correct like any other doc | an edited prereg proves nothing (§2.3) | irreversible |
| C1's wrong bullet | strike through + explain the reasoning error | delete it | the error is instructive and the file's own staleness is the lesson | low |
| Commit granularity | 7 commits by unit of work | one "session" commit | matches the repo's convention and makes `git log` a readable history of *why* | medium — hard to split later |
| Branch | `master` directly | a feature branch | no remote, linear history, every prior session did this; a branch adds friction with no reviewer | trivial |
| The 0.629 figure | leave FLAGGED | recompute and replace | four numbers already exist for this quantity; a fifth guess is worse than a marked gap | n/a |

---

## 5. What went wrong

### 5.1 A line-oriented grep silently under-reported, and I believed it

This is the session's real finding and it cost a wrong claim in a written document.

Having corrected the error-rate claim in `constrained_paired.md`, I ran:

```bash
grep -rn "0% false-positive" results/ docs/lecture/ README.md PLAN.md STATE.md
```

Two hits. I fixed one, deliberately left the prereg, and **wrote into the register that
there were two instances, one corrected and one left alone.** That was wrong. There were
**three**, and the same file contained two of them.

The missed one was wrapped:

```
... ipSAE tracks pose accuracy at ρ = +0.702 with a 0%
false-positive rate — which is why the number is worth something ...
```

The phrase `0% false-positive` **straddles a newline**, so no single line contains it, so a
line-oriented matcher cannot see it. It surfaced only by accident, in the `tail` output I
happened to read for a different purpose.

The re-run that found it:

```python
import re, pathlib
pat = re.compile(r'0%\s+false[- ]positive', re.I)   # \s+ spans the wrap
for p in pathlib.Path('.').rglob('*.md'):
    t = p.read_text(errors='replace')
    for m in pat.finditer(t):
        print(f"{p}:{t[:m.start()].count(chr(10))+1}")
```

**Why this is worse than an ordinary miss.** It fails *quietly and plausibly*: a grep that
returns two hits looks like a complete answer, and there is no signal distinguishing "two
occurrences exist" from "two occurrences happen to fit on one line each". The error rate
scales with phrase length and with how hard the prose is wrapped, so it is worst exactly
where it matters — long, quotable claims in hard-wrapped documentation.

**The general rule: in hard-wrapped prose, search with a newline-tolerant matcher, not with
`grep`.** Replace every inter-word space with `\s+` and run it over the file's full text.
This project already knows the shape of this bug — its own `wikilink-guard.sh` hook exists
because `[[a|b]]` split across a newline breaks the same way, and the 17-link incident that
motivated it is recorded in `LEARNINGS.md`. **Knowing the shape of a bug in one syntax did
not transfer to the same bug in prose.**

Note also the sequencing error underneath it: I wrote the register's live-text claim
**from the grep output** rather than from a verified enumeration. That is the same defect as
the guard written from a `LEARNINGS.md` sentence instead of from the tool's real output,
recorded three days ago in this same repo.

### 5.2 The "five and four" count was inherited and never checked

The session began by trying to locate a list of five retractions and four overstated claims.
No such list exists, and the true counts are 20 and 5. I spent the first part of the session
searching for an artefact that had never been written, on the strength of a number repeated
across three documents.

*A count quoted in prose is a claim like any other and has the same provenance problem as a
metric.* The register now carries the enumeration, so the count is derivable rather than
asserted.

### 5.3 A split wikilink, in the file about propagating corrections

The first draft of `results/retractions.md` contained a wikilink broken across a newline:

```text
[[../docs/lecture/CORRECTIONS|The course's own corrections
file]]
```

> **Restored 2026-09-26, after a second tool broke it.** When the repository's 558
> wikilinks were converted to standard markdown links for GitHub, the converter rewrote
> *this* block too — turning the illustration of a broken wikilink into a working
> markdown link, and deleting the only evidence the section is about. The regex matched
> across the newline exactly as Obsidian's parser does not.
>
> **A source-rewriting tool must skip fenced blocks**, because a documentation repo's code
> fences hold deliberately-wrong examples, and "fixing" them destroys the record. The
> fence is now tagged `text` and the check for this is: after any bulk rewrite, grep
> inside fences for the pattern you just introduced. That check found exactly one hit —
> this one.

This is precisely what `.claude/hooks/wikilink-guard.sh` exists to catch, written into a
file whose subject is corrections failing to propagate. Caught by a scripted check
(`re.finditer(r'\[\[[^\]]*\]\]')` filtering for `'\n' in match`) run over all four touched
files before committing, which also verified `[[` and `]]` counts balanced. Fixed, along
with two heading anchors that embedded bold markers and quotation marks and would have
resolved unreliably.

---

### 5.4 A correction scoped to one defect, worded as a general clearance

Found during the end-of-session sweep, which is the second time today the sweep found what
the work itself missed.

`docs/lecture/CORRECTIONS.md` C1 — the Challenge 2 MSA defect — ended its *"what it does
NOT invalidate"* section with:

> **Challenge 1.** Its folds used a server MSA matched to its own antigen [...] **Every
> Challenge 1 number in this course stands.**

Each clause is true of *that defect*. The final sentence is not true in general, and it
became false three weeks later for a completely unrelated reason: Challenge 1's composite
moved **96.0 → 94.0** on the DockQ display-rounding fix. The course consequently carried
the stale `final 96.0` in **four places** (`01:701`, `02:234`, `02:730`, `07:466`) with no
correction covering them, *and* a sentence telling the reader those numbers were fine.

**Why it was dangerous.** A stale number is an ordinary defect a reader may catch. A stale
number plus an explicit assurance that the number is current is worse than either: it
spends the reader's scepticism budget in the wrong direction. The assurance was also the
load-bearing reason nobody re-checked Challenge 1 when the rounding fix landed.

**How it was caught.** Only by sweeping for `final 96.0` across the whole vault rather than
trusting the corrections file's own account of its coverage. Notably the sweep was run
because of §5.1, not because anyone suspected C1.

**The general lesson.** *A correction is scoped to the defect that prompted it, and its
wording must say so. "X is unaffected by this" is a claim about one causal pathway; "every
X in this document stands" is a claim about all future pathways, which no author is in a
position to make.* C1 is now narrowed to the first form, and the rounding correction has
its own entry (C3) naming the four affected lines.

This also exposes a structural gap the register does not close: **the course's corrections
file had no entry for the project's single largest score change**, because that change was
made in the repo and propagated to the package without anyone asking what else quoted the
number.

---

## 6. Degenerate and failure cases for the register itself

A register is a data structure with invariants, and it is worth stating what breaks them.

- **An entry with no settling file** is a rumour. Every entry names the file that settles
  it; one that cannot is not ready to be an entry.
- **An entry with no live-text note has not been checked for propagation.** This is the
  invariant §5.1 violated, and the whole register currently sits in a weakened form of it:
  nineteen of twenty live-text notes rest on line-oriented greps. The register is *correct*
  about what was retracted and *unreliable* about where stale copies remain.
- **A claim retracted twice** — an entry superseded, then its replacement superseded again.
  §A2 is the live instance: Challenge 2's numbers were withdrawn, replaced by
  `bb_1_0_dldesign_0` (0.637), and replaced *again* by `bb_8_0` (0.904). Recording only the
  latest state loses the fact that the ranking inverted, which is the teachable part. The
  register therefore records the chain, not the endpoint.
- **A correction that is itself wrong.** Happened twice here — §C7 (a reliability figure
  corrected 0.28 → 0.296, where 0.28 was the `midpoint` value quoted in a `top` context, the
  same convention-mixing error the document was reporting) and §D1 (the course's corrections
  file going stale and self-contradictory). There is no structural defence; the only
  mitigation is that corrections are audited like any other claim.
- **A pre-registration containing a retracted claim.** Cannot be fixed without destroying
  the document's function (§2.3). Handled by policy — the correction lives only in the
  register — and it means the repo will always contain at least one uncorrected copy of
  some retracted claims. That is intended, and stating it here is the alternative to
  someone "fixing" it later.
- **The register growing without bound.** Not yet a problem at 25 entries. The natural exit
  is the same as `LEARNINGS.md`'s: an entry whose recurrence is prevented by a mechanism can
  be compressed to a pointer at that mechanism. Four already qualify — §A1, §C1, §C2, §C3
  are covered by `--json`/`rounding_risk` and `check_docs_against_scores`.

---

## 7. Verification — how we know it worked

| check | result |
|---|---|
| `uv run pytest tests/` | **34 passed** |
| `scripts/58_validate_submission.py submission/LOCKSMITH_DEV` | re-derives all metrics from the package alone |
| Split wikilinks across the 4 touched files | **0**, `[[`/`]]` counts balanced |
| Newline-tolerant sweep for the §C1 claim | 3 found, 2 corrected, 1 prereg left by policy |
| Vault-wide sweep, 5 corrected facts | 6 stale sites found (4 lecture chapters + pitch outline; `PLAN.md`/`BUILD.md` already correct) |
| Frontmatter conforms to the vault rule | date / two-axis tags / `status: living` |
| Working tree | clean before this session's doc commit |

**What "healthy" looks like for the register specifically:** every entry names a file that
settles it, and every *live text* note names a file and line. An entry with no settling file
is a rumour; an entry with no live-text note has not been checked for propagation, which
§5.1 shows is the half that gets skipped.

---

## 8. Honest assessment

**Solid.** The enumeration exists and is checkable. The two stale places in the course's
corrections file were found by reading it rather than by being told, and one of them was a
direct self-contradiction. `STATE.md` no longer contains statements that contradict its own
headline.

**Weak, and named.** The register is **hand-maintained prose with no mechanism behind it**.
Nothing prevents entry 21 from never being written. The `_BANNED` dictionary in
`scripts/58_validate_submission.py` is the only automated part and it is a grep over five
strings — it catches repeats of mistakes already made, and (per §5.1) it is line-oriented,
so it inherits the wrap problem for any banned string long enough to wrap.

**Not claimed.** No design changed, no metric was recomputed from structures, and nothing
here makes either design better. The scores are exactly what they were at the start of the
session. This was bookkeeping, and bookkeeping that found three errors is still bookkeeping.

**Unverified.** I did not re-run the newline-tolerant sweep for the *other* nineteen
retracted claims. §C1 was swept because an instance surfaced by accident; the rest have
live-text notes based on line-oriented greps and **should be assumed under-reported** by
exactly the mechanism §5.1 describes. That is the first item in §8 and it is not a small
caveat — it is the same defect, known and not yet acted on across the register.

---

## 9. Next steps

1. **Re-sweep every register entry with a newline-tolerant matcher.** The live-text column
   is currently built on the search method §5.1 shows to under-report. Cheap, scriptable,
   and the register's honesty depends on it.
2. **Mutation-test the inert tests**, MSA guard first — several assert over source text
   rather than behaviour.
3. **`results/rubric_headroom.md`** — regenerate under `band_value=top` or retract it
   explicitly (register §D3).
4. **Split the NetSolP entry in `LEARNINGS.md`, then promote the `ESM1b` half** to a test.
   It has absorbed a second, unrelated lesson, so promoting it whole would strand one.
5. The GPU-blocked validity controls, if a card becomes available (`STATE.md` §6).

---

## 10. Glossary

- **Clopper–Pearson interval** — an exact confidence interval for a binomial proportion,
  valid at small *n* and at 0 or 100%, where the normal approximation is not. It is what
  turns "0% false positives" into "0%, 95% upper bound 0.602" on 4 observations.
- **FLAGGED** — this register's status for a figure known not to reproduce and deliberately
  not replaced by a guess.
- **Hard-wrapped** — prose manually broken at a fixed column (~90 here), so a sentence spans
  several physical lines. The precondition for §5.1.
- **Line-oriented matcher** — a search that tests each line independently (`grep`, `rg`
  without `-U`). Cannot match a pattern spanning a newline.
- **Orphan** — a generated artefact a later, partial generator does not rewrite, so it
  describes inputs no longer present. The Challenge 2 defect of 2026-09-25.
- **Pre-registration** — a record of predictions and decision rules written *before* data
  exists. Never edited afterwards; see §2.3.
- **Provenance** — the computation and inputs that produced a value. A number in prose that
  appears in no data file has none.
- **Retraction register** — a single file enumerating every withdrawn claim, its
  replacement, and where stale copies still live.
- **`Scored.rounding_risk`** — a field populated when a metric lands within ±0.5 ulp of a
  band edge, so display rounding cannot silently change a band.
- **ulp** — unit in the last place; here, the smallest difference a value's printed
  precision can represent. At 3 dp, 1 ulp = 0.001.
