---
tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [the project's guiding idea — build the evaluator before the thing evaluated](../../knowledge/Build%20the%20Judge%20Before%20the%20Contestant.md), [the session index](README.md)

# Session 2026-09-28 — Clearing the backlog, and three guards that could not see

## 0. Session at a glance

`STATE.md` §7 carried nine open items. Seven were cleared, one more was found to be free
and done, and two remain because they need a decision rather than an hour. Nine commits,
no GPU time, no design change: Challenge 1 is still **94.0**, Challenge 2 still **93.6**.

The work was meant to be janitorial. It was not, and the reason is the thing worth keeping:
**four of the nine items turned out to be a guard, a flag, or an index that could not do the
job it claimed to do**, and in three cases the defect was the same shape — a checking
mechanism that was blind to part of the corpus it was pointed at.

If you read one section, read [§6](#6-the-pattern-a-guard-that-cannot-see-its-own-corpus).

This doc is self-contained. Concepts are defined here from first principles; where an
earlier session covers something more fully it is restated briefly and linked.

---

## 1. Vocabulary, defined before use

**Guard.** Any automated check whose job is to fail when something is wrong — a test, a
pre-commit hook, a preflight script, a pre-publication auditor. This project's organising
belief is that *a lesson written in prose cannot fail a build*, so lessons get promoted into
guards. The corollary, which this session is about: **a guard that cannot fail is not
evidence**, and it can be unable to fail for reasons nobody notices.

**Required set.** For a preflight with many checks, the subset whose failure makes the whole
run exit non-zero. Everything else is advisory. The required set — not the list of checks —
is the preflight's actual contract.

**Reliability**, written *r*. The fraction of observed variance in a measurement that is
signal rather than noise:

```
r = σ²_true / (σ²_true + σ²_noise)
```

It is a property of a **measurement applied to a population**, never of an instrument alone.
Restrict the population's spread and *r* falls even though the instrument is unchanged. It
is dimensionless, so it survives rescaling the metric; a standard deviation does not.

**Estimand.** *What quantity a number is an estimate of.* Two correct calculations of
different estimands will disagree, and the disagreement is not an error. The reliability of
a **single measurement** and the reliability of the **mean of k measurements** are different
estimands, related by Spearman–Brown:

```
r_k = k·r₁ / (1 + (k−1)·r₁)          r₁ = r_k / (k − (k−1)·r_k)
```

**Empirical p-value.** Given a real statistic *x* and *N* draws from a null distribution,
`p = (#{draws ≥ x} + 1) / (N + 1)`. Note it depends on the null's **tail above x**, not on
the null's mean. This distinction decides [§5](#5-shape-matching-a-null-and-a-mechanism-i-nearly-invented).

**Slug.** The identifier a Markdown renderer derives from a heading so that `#anchor` links
work. GitHub's rule: lowercase, delete punctuation, replace each remaining space with a
hyphen. Obsidian does not use this rule — it matches heading text — which is why a link can
work locally and be broken for every reader on the web.

---

## 2. What was actually wrong (the seven items, with numbers)

### 2.1 No CI, and the obvious cheap version of it is wrong

`.github/workflows/ci.yml` now runs `uv lock --check`, then `uv sync --locked --group dev`,
then `uv run pytest`, on every push.

The tempting optimisation is to skip PyTorch. The four modules the tests import
(`config`, `metrics`, `score`, `select`) pull in **no heavy dependency at module level** —
measured, not assumed. That is misleading: `anarcii`, which performs IMGT numbering, imports
torch at **call** time. Measured consequence of `uv sync --no-install-package torch`:

| | result |
|---|---|
| full install | **34 passed** (at the time), venv 7.1 GB |
| torch excluded | **4 failed, 30 passed**, venv 5.5 GB |

It saves 1.6 GB of 7.1 GB, because torch's 4.2 GB of `nvidia-*` CUDA libraries stay in the
resolved graph regardless. A CI silently dropping those four tests would be this project's
own thesis turned on itself.

The open question was then whether a **CPU-only runner** can be green, since the lock pins
`torch 2.11.0+cu128` for Blackwell. It can: the wheel installs and imports without a GPU,
and no test launches a kernel. Verified by running the suite with `CUDA_VISIBLE_DEVICES=""`
— **34 passed in 9.2 s**.

**Mutation-tested**, because a CI that has never failed is exactly the guard this session is
about:

| mutation | result |
|---|---|
| add a dependency to `pyproject.toml`, do not re-lock | `uv lock --check` **exit 1**, naming the fix |
| declare `pytest` as an extra instead of a dependency-group | `pytest` **exit 2**, collection error |
| unmutated | **34 passed** |

Stated plainly in the workflow header: the ~7.1 GB install against a runner's ~14 GB is
tight, so there is a disk-reclaim step that **has never been observed to be necessary**,
because there is no remote and this workflow has never run.

### 2.2 The preflight's required set was backwards

`scripts/00_doctor.py` marked every external tool — `DockQ`, `prodigy`, `ipsae.py`,
`anarcii`, `freesasa` — as `required=False`. A machine with none of them printed
*All required checks passed.*

The interesting part is not that the list was short. It is that it was **inverted**:

- `README.md` sends a grader here from the **validator** section, promising it "checks all
  four before you spend time".
- `scripts/58_validate_submission.py` imports `dockq, ipsae, netsolp, novelty, plddt,
  prodigy, sasa` and — verified by grep — **touches CUDA nowhere**.
- So validating the package needs the five tools and **no GPU**. The preflight demanded a
  **GPU** and **none of the tools**.

It could not fail for a grader missing everything it needed, and *did* fail for a grader
whose only sin was owning a CPU. A third gap nobody had listed: the README tells you to
install ~4.7 GB of NetSolP ONNX models, `scripts/58` imports `netsolp`, and the preflight
checked it **zero** times.

The fix is `--scope {fold,validate,all}`, with the required ids declared per scope in a
`REQUIRED` dict rather than as a flag on each call site — so the set becomes a thing a test
can read. NetSolP's paths and `MODEL_TYPE` are **imported** from `locksmith.metrics.netsolp`
rather than repeated, because a config value and a hardcoded constant encoding one
convention will diverge, and this file is not allowed to be the copy that rots.

The venv check was also functionally wrong. It asked *"is this venv called locksmith"*
(`"locksmith" in sys.prefix`); it now asks *"if I import locksmith, do I get **this**
checkout"*. Demonstrated by copying the tree to a directory named `citest`: the old
expression evaluates **False** on a perfectly good checkout, and the new one passes and then
correctly fails on the thing genuinely missing there (`ipsae` not cloned).

Measured behaviour now:

| condition | result |
|---|---|
| tools off `PATH`, `--scope validate` | 2 required failed, **exit 1** |
| `NETSOLP_DIR` nonexistent, `--scope validate` | 2 required failed, **exit 1** |
| `CUDA_VISIBLE_DEVICES=""`, `--scope fold` | 3 required failed, **exit 1** |
| unmutated | **exit 0** in all three scopes |

### 2.3 The worked arithmetic that taught a wrong operation

The course's standing policy is that chapters are **never** retro-edited; corrections live
in `docs/lecture/CORRECTIONS.md` and chapters carry pointers. One section was rewritten
anyway, and the boundary that justifies it is now written down.

`02-the-engineering-problem.md` §3.3 is a worked derivation of Challenge 1's composite. Its
`dockq` row read `0.800 | good | 10.0`. That **is** the rounding defect the course documents
as C3 — the true `GlobalDockQ` is `0.7995794972281312`, which is 0.00042 *below* the Good
edge — presented as correct working. From it the section derived `binding = 60/6 = 10.000`
and `final = 96.0`.

A reader **reruns** a worked derivation. Indexing it would have left the course teaching a
wrong operation behind a pointer. It now reads `0.799579 | medium | 8.0`,
`binding = 58/6 = 9.667`, and

```
final = (0.60 × 9.667 + 0.20 × 8.000 + 0.20 × 10.000) × 10
      = (5.800       + 1.600        + 2.000        ) × 10
      = 94.0
```

matching the shipped `scores.md` exactly. A pleasing check fell out: the section's closing
paragraph already said a Good→Medium slip inside `binding` costs
`(10−8)/6 × 0.60 × 10 = 2.0` points, which is exactly 96.0 → 94.0 — so the arithmetic
confirms the correction touches **one term**, rather than being a rescore.

> **The boundary, stated so it can be applied without re-litigating:**
> **prose that *quotes* a number is indexed; arithmetic that *produces* one is corrected.**

Everything else was indexed — and the index was the real problem. C3 claimed to list the
live occurrences and had **4 rows**. The true count is **40** non-banner mentions: **32**
stale, **8** already self-describing. An index that looks authoritative while being 12%
complete spends a reader's scepticism in the wrong direction. The 32 are now grouped by the
*kind* of correction each needs — composite (14), envelope endpoint (9), convention triple
(3), Challenge 2 seed composites superseded by C1 (4), historical incident records (2) — and
C3 ships the command that regenerates the list.

### 2.4 The index that was not an index, and 66 links broken only on the web

`docs/sessions/README.md` promised "One line per working session" in its own first line and
ran to **5,448 words**, with single table cells at **416** (STATE.md said "over 500"; the
real maximum is 416).

Before deleting ~5,000 words of curation, the question is whether it exists anywhere else.
Measured: **93.4%** of the distinctive tokens in those cells (numbers, identifiers, code
spans) already appear in the doc each row links to, and all 26 docs open with their own
summary. The residual 6.4% are quoting artefacts — a string containing a literal newline,
spacing variants of a formula — not unique content. Now **926 words**, 26 rows.

The hooks were written by hand. Auto-truncating the old cells produced "M3 complete" and,
worse, carried `Ch1 96.0, Ch2 91.2` — two superseded scores — into a freshly cleaned file.

While verifying the links, a separate defect surfaced: **66 internal cross-references in the
course pointed at anchors that do not exist**. One cause throughout. A heading containing an
em dash slugs to a **double** hyphen, because the dash is deleted as punctuation and the
spaces either side each become a hyphen:

```
### 3.1 Boltz-2 — the primary predictor     →     #31-boltz-2--the-primary-predictor
```

Every link was written with one hyphen. They resolve in **Obsidian**, which matches heading
text rather than slugs, so the entire set was broken **only in the renderer this repo is
about to be published to** — and the repo has never been public, so nothing had ever
exercised them. Rewritten only where the mapping is unambiguous: 66 fixed, 0 ambiguous, 0
unresolved, and a rescan of all 144 Markdown files reports **0 broken**. Now pinned by
`test_every_internal_markdown_anchor_resolves`.

### 2.5 A plan whose premise had already been refuted

`docs/challenge2_regeneration_plan.md` built a budget argument on the withdrawn
`0% FP / 25% FN` pair. Those are two different DockQ thresholds quoted as though they shared
one, and the pair is reachable at neither:

| DockQ threshold | false positive | false negative |
|---|---|---|
| Acceptable+ (≥ 0.23) | **0%** | **58.3%** |
| Medium+ (≥ 0.49) | **12.5%** | **25.0%** |

The 0% also rests on **4 negatives** — Clopper–Pearson 95% upper bound **0.602**, i.e.
uninformative. Corrected per threshold; "the 40-crystal panel **validated** this week"
became "**characterised**", because ρ = +0.702 on n = 40 is an association; and a stale
`Challenge 1 at 96.0` became 94.0.

The document is also now marked **superseded**, which matters more than the numbers: its
central question — are the backbones poor, or was the selection? — was already answered *no,
do not spend the money* by the depth sweep (144 folds; viability constant at **~8% per
sequence**; χ² = 22.91 on 17 df, p = 0.152; eight times the sequences producing nothing
better than depth 1). It is kept rather than deleted because the reasoning is the record of
a decision.

### 2.6 A correction that reached one chapter and not the two people open first

The NetSolP triple `0.379 / 0.463 / 0.733` **mixes VH and VL across three variants and two
constructs** — it is ESM12-VH, Distilled-VL, ESM1b-VH, reading as one antibody scored three
ways. The correct object is a table:

| | ESM1b (5-fold) | ESM1b-distilled | ESM12 (5-fold) |
|---|---|---|---|
| VH | 0.733 | 0.637 | 0.379 |
| VL | 0.569 | 0.463 | 0.346 |
| Fab heavy | 0.623 | 0.491 | 0.352 |
| Fab light | 0.626 | 0.448 | 0.312 |

`03-the-toolchain.md` §4.4 already printed that table **and** already recorded the retraction
of the companion claim ("the CLI default would have failed every design" — NetSolP's
`predict.py` defaults to ESM1b, which passes). `00-orientation.md` and `10-glossary.md` never
inherited either. *The fix went to one chapter and not to the two a reader opens first.*

Indexed as course correction **C5**, per the boundary in §2.3, with the banner updated across
11 files.

### 2.7 A flag that was wrong, and a blocker nobody checked

This is the sharpest item and it is treated separately in [§4](#4-the-0629-flag-was-wrong-and-so-was-its-blocker).

---

## 3. Verifying any of this yourself

```bash
uv sync --locked --group dev && uv run pytest -q        # 42 passed, ~7 s, no GPU needed
uv run python scripts/00_doctor.py --scope validate     # exit 1 if a scoring tool is missing
uv run python scripts/94_shape_matched_patch_null.py    # regenerates the shape-matched null
cd docs/lecture && grep -n "96\.0" *.md | grep -v "^CORRECTIONS.md" | awk -F: '$2!=9'   # 40
```

"Healthy" looks like: 42 tests passing; the doctor exiting 0 under all three scopes on a
fully provisioned machine and **non-zero** when you hide a tool; and the anchor test
reporting zero broken links across 144 Markdown files.

---

## 4. The 0.629 flag was wrong, and so was its blocker

Register §D2 recorded that the shortlist reliability **0.629** *"does not reproduce from the
recorded inputs under any standard estimator tried"* (the plug-in variance ratio gives 0.276
/ 0.296), and that *"the original script would settle it"*.

**Both halves are false.**

**It reproduces — as a different estimand.** `results/m3_winner.md` §1 records a
between-design sd of the 7-seed means of 0.290 and a noise sd of a 7-seed mean of 0.176:

```
r₇ = 1 − 0.176² / 0.290² = 1 − 0.030976 / 0.084100 = 0.6317        (recorded 0.629)
```

and the noise chain is internally consistent: `0.467 / √7 = 0.1765 ≈ 0.176`. The 0.276/0.296
are **single-seed** reliabilities. Diffing them against 0.629 is this project's own *never
diff a single observation against an aggregate*, one level up: **never diff two reliabilities
without checking they are reliabilities of the same thing.**

**The blocker did not exist.** "The original script would settle it" reads as *the script is
lost*. `scripts/35_winner.py` has been tracked since the initial commit, and lines 202–206
are the estimator verbatim:

```python
between  = float(np.std([r["surr_mean"] for r in rows], ddof=1))
var_noise = within7 ** 2 / s_used                      # s_used = 7
rel = max(0.0, 1 - var_noise / (between ** 2))
```

Nobody opened the file. **A blocker is a claim, and it decays like any other claim.** This
one gated the entry for six days, and `STATE.md` carried a work item that four documents
dated 2026-09-23 had already completed.

**Recomputed from the raw folds**, read-only, replicating that estimator over
`runs/designs_reseed7` + seed 1, 20 designs × 7 seeds, fresh seed 23 excluded:

| quantity | recomputed | recorded |
|---|---|---|
| reliability of a 7-seed mean | **0.660** | 0.629 |
| implied single-seed reliability | **0.217** | 0.276 / 0.296 |
| within-design sd | 0.226 | 0.467 |
| between-design sd of 7-seed means | 0.147 | 0.290 |

The standard deviations are ~2× smaller and **that is expected**: they were computed under
the pre-2026-09-22 surrogate anchors (2.5 / 7.0 / 9.5) and the config is now `top`
(5 / 8 / 10). Reliability is a ratio and survives a rescale; an sd does not. So *"does not
reproduce"* was true of the **standard deviations** and never of the **reliability** — which
is the whole confusion in one sentence.

**What survives** is narrower and one-sided. The same variance components imply

```
r₁ = 0.053124 / (0.053124 + 0.467²) = 0.196
```

matching the Spearman–Brown back-implication (r₇ = 0.629 ⇒ r₁ = 0.195) rather than the
record. So **0.296 is the outlier**, adrift by roughly +0.08 to +0.10 — not a two-way puzzle.
And `grep -rn "0\.296\|0\.276" scripts/ src/` returns **nothing**: no code computes them.
They were produced in prose during an audit. *A figure that lives in prose and never in a
data file has no provenance* — and it was the number used to challenge a figure that a
tracked script does compute.

---

## 5. Shape-matching a null, and a mechanism I nearly invented

### 5.1 The experiment

`scripts/70_epitope_patch_null.py` asks whether a conditioned backbone's interface sits on
the PD-L1 epitope of PD-1 rather than on *some* equally sized patch. Statistic: the fraction
of the design's interface residues captured by the patch. Real **0.712**, contiguous-patch
null **0.154**, 17/18 backbones at p < 0.05.

Register §D4 flagged one defect: `patch_from()` takes the **k nearest** residues to a seed,
which is the most compact k-residue set that seed admits, so the drawn patches were more
compact than the real epitope (7.73 Å vs 10.08 Å RMS spread). A compact patch is a poor
shape for capturing a spread-out interface, so the null scores too low and the test is
**anti-conservative by an unquantified amount**.

`scripts/94_shape_matched_patch_null.py` quantifies it: same 18 backbones, same statistic,
patches **rejection-sampled** so their RMS spread lands within ±0.5 Å of the real epitope's.
No new folds, no GPU. Acceptance rate 0.163; zero draws failed to find a match.

It first **reproduces the flagged figures, which existed only in prose** — neither 7.73 nor
10.08 was computed by any script in this repo:

| | prose | recomputed |
|---|---|---|
| epitope RMS spread | 10.08 Å | **10.09 Å** |
| compact-patch RMS spread | 7.73 Å | **7.76 Å** |
| shape-matched RMS spread | — | **10.10 Å** |

**The mismatch is worth +0.019** on the null's mean (0.153 → 0.172) against a real value of
**0.712**. The defect was real, in the flagged direction, and was never carrying the result:
the gap to beat is 0.54. Net effect — `bb_3_0.pdb`, the single failure under the old null,
moves **p 0.0730 → 0.0115**, so the count goes **17/18 → 18/18**.

### 5.2 The part worth recording is that I got the explanation wrong

The first draft of that write-up asserted that shape-matching **thins the null's upper tail**,
and therefore that *"every p-value falls even though the null's mean rises"*. It is a tidy
mechanism and it is false. The distribution table printed **directly above that sentence**
says:

| null | mean | sd | p99 | max |
|---|---|---|---|---|
| compact (old) | 0.153 | 0.185 | 0.554 | 0.602 |
| shape-matched | 0.172 | 0.155 | **0.605** | **0.788** |

The extreme quantiles **rise**. And per backbone the p-values move mostly the way the higher
mean predicts: **12 rose, 4 fell, 2 unchanged**. The honest statement is that one marginal
backbone changed side, and the headline count with it.

Two riders. The counts are now **computed in the script** rather than asserted in prose, so
the sentence cannot drift from the table again. And because the correction moves a marginal
case **in our own favour**, the full distribution is reported beside the count — a result
that flatters you is the one to publish the most detail about.

This is the same failure shape as §C1 of the register: *a mechanism that sounds right, in a
sentence adjacent to the table that refutes it.* It was caught only by reading the numbers
underneath the claim before committing.

---

## 6. The pattern: a guard that cannot see its own corpus

Three separate mechanisms this session were blind to part of what they were pointed at, and
the blindness was invisible because **each returned a clean result**.

**(1) The pre-publication auditor could not see a bolded phrase.**
`scripts/59_prepublish_audit.py` was promoted out of `LEARNINGS.md` on 2026-09-26
specifically to be *newline-tolerant*: `_nl()` joins the words of a banned phrase with `\s+`,
so a phrase wrapped across a line is still found. That is necessary and **not sufficient**.
`\s+` bridges whitespace and nothing else, so inline markup **inside** the phrase defeats it.
Measured against its own `_nl("0% false-positive rate")`:

| text | result |
|---|---|
| `a 0% false-positive rate` | FOUND |
| `a 0%\nfalse-positive rate` | FOUND — the bug it was built for |
| `a **0%** false-positive rate` | **MISSED** |
| `a *0% false-positive* rate` | **MISSED** |
| `` a `0%` false-positive rate `` | **MISSED** |

Only emphasis bracketing the **whole** phrase survives, because then the markers fall outside
the matched span. In a repo that bolds nearly every number, that is most of the corpus. My
first sweep for the retracted claim returned **0 matches**; a corrected sweep finds **17**.
*A banned-text auditor returning zero looks exactly like a clean repo.* Fixed by searching
the text a **reader** sees as well as the bytes on disk, and labelling such a hit
`[markup-stripped]`. `_` is deliberately **not** stripped — here it is an identifier
(`scores_v2.json`) far more often than an emphasis marker, and stripping it would invent
false positives.

**(2) A test matched its own description of the bug.** The first version of
`test_doctor_venv_check_is_functional_not_a_substring_of_the_path` grepped the doctor's
source for the literal `"locksmith" in sys.prefix`. It failed on the **fixed** file, because
the module docstring quotes that expression to explain what was wrong with it. It walks the
AST now. The same thing then happened to the auditor, which flags its own source file because
its new comment contains the example phrase — noted in the comment rather than hidden.

**(3) A preflight's required set was written from what was easy to check.** §2.2. The way a
guard usually cannot fail is not that someone disabled it; it is that its required set was
assembled from convenient checks rather than from what the job actually needs.

And a fourth, adjacent: **a blocker is a guard on your attention, and it can be wrong the
same way.** §D2's "the original script would settle it" was never verified, and the script
was in the repo the whole time.

> **The transferable form.** When a check comes back clean, ask *what it would have done had
> the answer been no* — and confirm that by breaking something on purpose. Every mechanism
> repaired this session is now mutation-tested, which is the only version of that question
> that survives being forgotten.

This is the third consecutive session to produce an instance of it. On 2026-09-26 it was a
fresh clone that structurally cannot distinguish a deleted object from an orphaned one. The
mechanism built in response was itself blind to bold text.

---

## 7. What went wrong, in full

- **I nearly shipped an invented mechanism** for the shape-matched null (§5.2). Caught by
  reading the table printed above the claim.
- **My first repo-wide sweep returned 0 and I believed it** for the time it took to notice my
  own correction text should have matched. That is what exposed (1) above — luck, not method.
- **My first control for the auditor fix exited 1 on a "clean" repo.** I had committed the
  auditor *into* the test repo, and its new comment contains the example phrase. A control
  that fails for a reason you did not model is not a control; re-run with the auditor outside
  the repo, it exits 0.
- **Two edits failed on anchors I typed from memory** — an X5 table row with bold markers, and
  a study-plan sentence hard-wrapped mid-phrase. The day's own lesson, arriving twice more.
- **STATE.md's own numbers were stale in three places** (`34/34` tests, "over 500 words" for a
  416-word maximum, "~18" derivations for 32). The file that exists to be the single source of
  truth drifts like any other.

---

## 8. What is left, and why it is not an hour's work

Two items, both decisions rather than tasks.

**The GPU-blocked validity controls**, ~2–4 GPU-hours (~$1–2 on a rented sm_86 card). The
**decoy-patch control** — hotspots on the opposite face of PD-1 — is now the *only*
outstanding way the conditioning result could be shown to be wrong, since it survived
shape-matching and got stronger. **Sequencing the 18 unconditioned backbones** separates
range restriction from a dead `interaction_pae`.

**Republish.** Recreate private, push, verify old SHAs return 404 **against the remote**
(a fresh clone structurally cannot answer this), read the rendered docs, flip public. The
66-anchor repair matters here: those links are broken for every web reader and correct in
Obsidian, so the rendered read is not optional. `.github/workflows/ci.yml` has never
executed; its first push is its first real test.

---

## 9. Glossary

| term | meaning |
|---|---|
| **anti-conservative** | a test that rejects the null too readily — too many false positives |
| **blocker** | a recorded reason work cannot proceed; a claim, and checkable like one |
| **empirical p-value** | `(#{null draws ≥ real} + 1) / (N + 1)`; depends on the null's tail above the real value, not its mean |
| **estimand** | the quantity a number estimates; two estimands may disagree without either being wrong |
| **guard** | an automated check whose job is to fail when something is wrong |
| **mutation testing** | deliberately reintroducing a defect to confirm the guard turns red |
| **reliability (r)** | signal variance ÷ total variance; a property of a measurement *and a population* |
| **required set** | the checks whose failure makes a preflight exit non-zero — its real contract |
| **RMS spread** | root-mean-square distance of a residue set's centroids from their own centroid; a size-independent measure of how spread out a patch is |
| **slug** | the anchor a renderer derives from a heading; GitHub deletes punctuation and hyphenates spaces, Obsidian matches heading text |
| **Spearman–Brown** | the formula relating single-measurement reliability to k-measurement reliability |
