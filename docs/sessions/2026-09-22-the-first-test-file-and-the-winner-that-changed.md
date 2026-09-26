---
date: 2026-09-22
tags:
  - session
  - locksmith-antibody-hackathon
status: living
---

Tags: [[Learning]], [[locksmith-antibody-hackathon]]

# Session 2026-09-22 — The first test file, and the winner that changed

## 0. Session at a glance

**Before:** three independent audits on 2026-09-21 had found a disqualification risk
(DockQ refuses the package at its defaults), a config/code divergence in the selection
surrogate, and an inverted claim on a pitch slide. Every Challenge 2 artefact sat on a
stopped RunPod volume and had never been retrieved, so the newest results — `d=1.47`,
`ICC=0.000`, `24.9 Å` — existed **only as prose in a markdown file**. The project had
**zero tests and no version control** across 12,430 lines.

**Now:** the DockQ invocation ships inside the submission and was verified by running
it; the pod volume is retrieved (256 files, 427 MB) and the headline recomputes from
the data; `tests/test_invariants.py` exists with 17 passing tests; the repo is under
git. Two config/code divergences are fixed and a third is documented.

**The finding that mattered most was not on anyone's list.** Fixing the surrogate
**changes which design wins** — the shipped design falls from 1st to 4th, and 18 of 20
shortlisted designs change rank. The change is inside one seed's noise, which is why we
did not swap the design, and why the result is better read as *confirmation* of an
existing claim than as a new problem.

**Prerequisites:** the rubric and its eight metrics —
[the spec extraction](2026-09-14-antibody-hackathon-spec-and-scoring.md). Why a continuous
surrogate exists at all — [the
allocation session](2026-09-19-three-seeds-is-the-worst-allocation.md). What the audits found —
[the previous session](2026-09-21-renting-a-gpu-and-what-three-judges-found.md).

---

## 1. The problem this session addressed

One sentence, and it is the project's own: **every lesson this project learned went into
prose, and prose cannot fail a build.**

That is not a stylistic complaint. It is a mechanical account of why four separate
numbers rotted out of sync in a codebase that is otherwise obsessive about silent
failure. The project had written down, repeatedly and well, that `boltz predict` exits 0
after fatal errors, that a piped `grep | head` lies twice, that a program running without
error is not evidence it did what you intended. It then encoded each of those lessons as
a **paragraph**. A paragraph cannot be violated. It can only be un-read.

`LEARNINGS.md` had named the unlock precisely — *"the real unlock is one minimal test
file"* — on 2026-09-19, and named it again on 2026-09-21. It had never been written.

---

## 2. Concepts introduced (first principles)

### 2.1 What a band convention is, and why two of them can coexist undetected

The rubric scores each metric into one of three **bands** — Good, Medium, Poor — and the
handbook gives only *ranges* for what a band is worth: "Good (9-10)", "Medium (6-8)",
"Poor (0-5)". It never says how to pick a number inside a range. Three readings are
implementable from the text alone:

| reading | good | medium | poor | max attainable |
|---|---|---|---|---|
| `bottom` | 9.0 | 6.0 | 0.0 | 90 |
| `midpoint` | 9.5 | 7.0 | 2.5 | 95 |
| `top` | 10.0 | 8.0 | 5.0 | 100 |

The project chose `top` on 2026-09-20, reasoning that §7.3 states the score range as
"0 – 100" and only `top` attains it.

Now the key structural fact. For the **reported** score this choice is a *uniform
monotone relabelling*: every design's every metric moves from one fixed triple to
another fixed triple, so the ordering of two designs cannot change. `config/metrics.yaml`
says exactly this, and for `score.evaluate` it is correct.

**It is not correct for the surrogate**, and the reason is worth understanding because it
generalises.

### 2.2 Why a *continuous* surrogate is not invariant to the same relabelling

The rubric composite takes only three distinct values across our 40-design pool
({82.5, 85.0, 87.5}), so it cannot rank. The project therefore ranks on a **surrogate**:
the same metrics, the same weights, but the band *step* replaced by a piecewise-linear
interpolation through the three band scores as anchors:

```
raw == cutoff  ->  poor score
raw == medium  ->  medium score
raw == good    ->  good score
```

The function has two segments. Their **slopes** are set by the anchor spacing:

- lower segment rise = `medium_score − poor_score`
- upper segment rise = `good_score − medium_score`

Under `midpoint` those are `7.0 − 2.5 = 4.5` and `9.5 − 7.0 = 2.5`, a ratio of **1.8**.
Under `top` they are `8.0 − 5.0 = 3.0` and `10.0 − 8.0 = 2.0`, a ratio of **1.5**.

A relabelling that changes the *ratio* of the two segments is not an affine
transformation of the surrogate. Two designs whose metrics sit in different segments are
re-weighted against each other, and their order can invert. Formally: the surrogate is
`Σ_c w_c · mean_m f(raw_m)` and changing the anchors replaces `f` with a `g` that is
**not** of the form `a·f + b`, so `Σ` is not monotone in the old `Σ`.

> **Transferable principle.** A monotone relabelling of *categories* preserves ranking.
> A monotone relabelling of the *anchors of an interpolation between* those categories
> does not, because it changes the local exchange rate between metrics. If you replace a
> step function with a continuous one "through the same points", you have introduced the
> spacing of those points as a new parameter, and it is now load-bearing.

### 2.3 Intraclass correlation and its detectable floor

`ICC = σ²_between / (σ²_between + σ²_within)` — does knowing the group predict the value?
Estimated by one-way ANOVA over `n` groups of `k`:

```
ICC = (MS_between − MS_within) / (MS_between + (k−1)·MS_within)
```

The quantity that makes an ICC *interpretable* is the smallest value the design can
detect. At `n=10, k=3` the F-test has df = (9, 20) and `F_crit(0.05) = 2.393`, which
corresponds to

```
ICC_floor = (F_crit − 1) / (F_crit + k − 1) = 1.393 / 4.393 = 0.317
```

So an observed ICC of −0.113 supports *"no effect larger than ≈0.32 is detectable here"*.
It does **not** support "cannot rank" or "delete this metric". Those are statements about
the world; the measurement is a statement about this experiment.

### 2.4 Why a contiguous patch is the right null for an epitope

To ask "did conditioning put the loops on the **right face**", you need a null that a
wrong answer could produce. Two candidates:

- **26 residues drawn uniformly** from the 113-residue target. Any interface overlaps
  such a set by ≈ 26/113 = **0.230** purely by construction. This is a strawman: a real
  dock contacts a contiguous piece of surface, and a scattered set has no chance of
  matching it.
- **26 residues forming a contiguous surface patch** — pick a seed residue, take its 25
  nearest neighbours by centroid distance. This is the same *shape* of object as a real
  epitope, placed somewhere else.

The second is the test. Measured below, the uniform null scores 0.231 and the contiguous
null scores **0.154** — the contiguous null is *harder to beat in the right way*, because
it either overlaps the real epitope substantially or barely at all.

> **Transferable principle.** A null must be drawn from the same *shape space* as the
> thing it is a null for. Matching only the size of a set, and not its geometry, produces
> a null whose expected value is an artefact of the denominator.

---

## 3. What was built — mechanism, not narrative

### 3.1 `tests/test_invariants.py` — 17 tests, the first in the project

The selection rule for what belongs in this file, stated in its own docstring:
**an invariant whose violation is invisible.** A crash does not need a test. A number
that quietly becomes wrong does.

| test | pins |
|---|---|
| `test_surrogate_anchors_match_config_band_values` | the three module constants equal `cfg.band_scores` |
| `test_surrogate_equals_final_at_the_anchors` | behavioural form of the above — fails even if the divergence is reintroduced elsewhere |
| `test_surrogate_diverges_only_at_strict_edges_and_only_upward` | the one disagreement that is intrinsic, so it can never be rediscovered as a surprise |
| `test_surrogate_refuses_a_design_with_a_missing_metric` | a metric we could not compute must not raise the score |
| `test_dockq_module_defaults_match_the_declared_conventions` | no signature default restating a convention |
| `test_dockq_is_invoked_with_the_flags_the_submission_documents` | `--allowed_mismatches` / `--mapping ABC:ABC` stay in the call |
| `test_spearman_brown_roundtrip` + `…_is_the_consistent_one` | a quoted reliability must follow from its inputs |
| `test_strict_band_edges_are_exclusive` | `70.0%` identity is Medium, not Good — worth 5 final points |
| `test_every_metric_band_is_monotone_in_its_direction` | `cutoff → medium → good` improves, or `band_of` misclassifies silently |
| `test_msa_path_with_space_is_staged` | the `Obsidian Personal` space bug, as a mechanism |
| `test_seq_for_folding_refuses_a_spliced_chimera` | the internal-gap chimera, as a mechanism |

The last two are the ones `LEARNINGS.md` had been blocked on: their fixes already
existed as code, but a guard buried inside a driver function is not a mechanism a future
reader will find. A test named `test_msa_path_with_space_is_staged` is.

### 3.2 The two fixes the tests forced

**`select/surrogate.py`** no longer hardcodes `2.5, 7.0, 9.5`. `_anchors(cfg)` reads
`cfg.band_scores`, `compute()` passes them through to `_interp`, and the module constants
are derived at import from the live config.

**`metrics/dockq.py`** no longer carries `interface_agg="min"` as a signature default
while the config declares `global`. Both parameters default to `None` and resolve through
`_convention()` at call time. The general form: *a default that restates a convention is
a second source of truth, and the second one rots.* Two call sites were additionally
using `c.get("dockq_interface_agg", "min")` — a fallback that would have silently
reinstated the abandoned convention had the key ever gone missing.

### 3.3 The packaging fixes

`build_challenge` now **asserts** that `structures/` contains exactly the two files
§4.2.1 lists. This was not hypothetical: `ipsae.py` writes its scratch `.txt`/`.pml`
beside whatever PDB it is handed, so **merely validating the built package littered it**
with three stray files. `scripts/58_validate_submission.py` now copies the package to a
temporary directory and validates the copy — *reading a thing must not modify it*, and
the copy is a better test anyway because it proves the package works somewhere other
than where it was built.

### 3.4 `scripts/70_epitope_patch_null.py`

The contiguous-surface-patch null of §2.4, run over the 18 retrieved conditioned
backbones, 2000 draws each, seed 20260922.

---

## 4. Results

### 4.1 The pod volume, and what it cost to be honest about it

The volume survived. Retrieval used the Jupyter contents API over HTTPS — **one GET per
file**, which is the transport lesson from 2026-09-21 applied in reverse (typing 11,096
base64 characters had delivered 11,092; a heredoc paste truncated mid-word; only a real
HTTP transfer was exact).

The GPU the pod had held was gone by the time we restarted it. Since a file copy needs no
GPU, it was restarted **CPU-only** at $0.25/hr — which also sidestepped RunPod's
data-migration path entirely.

**The published headline reproduces from the retrieved data:**

| quantity | published 2026-09-21 | recomputed 2026-09-22 |
|---|---|---|
| conditioned `frac_iface_on_epitope` | 0.712 (sd 0.110) | **0.7119** (sd 0.1130) |
| unconditioned | 0.501 (sd 0.164) | **0.5005** (sd 0.1684) |
| Cohen's d | 1.47 | **1.4747** |
| 95% CI | [0.73, 2.22] | **[0.733, 2.216]** |

They are no longer unfalsifiable. That is the entire point of the exercise.

### 4.2 The surrogate fix changes the winner

Recomputed over the 20-design shortlist using the seeds selection actually ran on:

| rank | midpoint anchors (what ran) | top anchors (what config declared) | mean | sd |
|---|---|---|---|---|
| 1 | `mpnn_T0.5_s104_036` | `mpnn_T0.2_s102_032` | 97.5465 | 0.1801 |
| 2 | `mpnn_T0.5_s104_053` | `mpnn_T0.5_s104_011` | 97.4611 | 0.1950 |
| 3 | `mpnn_T0.5_s104_057` | `mpnn_T0.3_s103_032` | 97.3638 | 0.1894 |
| 4 | `mpnn_T0.5_s104_047` | **`mpnn_T0.5_s104_036`** ← shipped | 97.3557 | 0.0646 |

**18 of 20 designs change rank. Spearman between the two rankings is 0.755, not 1.0.**

And then the number that decides what to do about it:

| quantity | value |
|---|---|
| 1st − 4th gap | **0.191** surrogate points |
| pooled within-design (seed) sd | **0.226** |
| standard error of a 7-seed mean | **0.086** |
| span of the whole top six | **0.205** |
| single-seed reliability on this shortlist | **0.28** |

The gap between the old winner and the new one is **0.84 of one seed's noise**. We did
not swap the submitted design, and the reasoning is the substance: swapping would mean
acting on a ranking this project has already measured as unable to rank. **The winner
changing is not a new problem — it is a sharper instance of the finding we already
publish.**

*Confidence check on the computation itself:* under the `midpoint` convention it
reproduces the project's recorded 7-seed within-design sd of **0.467** to three decimals.

### 4.3 The patch null — a better test than the one we published

| | value |
|---|---|
| real PD-L1 epitope, pooled mean | **0.712** |
| contiguous same-size patch elsewhere | **0.154** |
| 26 residues drawn uniformly | 0.231 |
| backbones beating their own contiguous null at p<0.05 | **17 / 18** |

This is superior to the `d=1.47` comparison on three counts: it is **deterministic per
backbone** so there is no stopping rule to violate; it asks whether conditioning hit *the
right face* rather than whether it did *anything*; and it is a control that could have
failed.

### 4.4 RF2 metrics, recomputed with their detectable floor

| metric | ICC | mean | sd |
|---|---|---|---|
| `interaction_pae` | −0.113 | 15.60 | 2.15 |
| `pae` | −0.120 | 8.28 | 0.99 |
| `target_aligned_antibody_rmsd` | +0.196 | 24.87 | 10.76 |
| **`pred_lddt`** | **+0.836** | 0.908 | 0.012 |

Detectable floor at n=10, k=3: **0.317**.

Two corrections fall straight out. `interaction_pae` is *undetected*, not *absent*. And
`pred_lddt`, which had been grouped with "constant and useless" metrics, has the
**highest ICC of the four** and is the only one clearing the floor — its small sd (0.012)
reflects that the complex is ~85% fixed framework, and **low variance is not
uninformativeness.**

### 4.5 A proposed correction that did *not* survive testing

The adversarial audit suggested the 24.9 Å RF2 disagreement was more parsimoniously read
as *unfiltered designs failing a standard filter* than as RF2 being unreliable. Good
hypothesis; the retrieved data lets us test it, and it fails.

- `interaction_pae` min is 9.31, the conventional filter is `< 10`, so **1 of 30 passes**
  — which is exactly what an unfiltered pilot should look like, and that half of the
  reasoning is right.
- **But that one passing design sits at 32.86 Å**, against a pool median of 28.94 Å.

There *is* a weak real association (Spearman `interaction_pae` vs rmsd = **+0.415**,
p = 0.023, n = 30), so the metric is not noise. But "filter first and RF2 agrees" is
refuted by the only design that passes the filter. **We are not adopting the
re-reading.**

> This is the most useful kind of result in the session: an offered correction, tested
> rather than accepted, and declined on evidence. Accepting a plausible correction
> uncritically is the same failure as making the original claim uncritically.

---

## 5. What went wrong

### 5.1 The checksum pass is incomplete, and saying so is the point

The plan said "verify by checksum". The Jupyter contents API returns a **server-side
sha256** — exactly the right instrument — and roughly 130 of 256 files were verified
against it before **Jupyter 502'd mid-walk and never recovered**. The pod stayed up; the
service died. A restart put it back into "Initializing" and it stayed there.

What we have instead: server-reported byte size vs bytes written for every file (curl
fails on a short read against `Content-Length`), exact directory-count agreement with the
server listing, **168/168 PDBs parsing with numeric coordinates**, 4/4 JSONL parsing on
every line, and the published headline recomputing to four decimals.

That is strong evidence. **It is not a completed checksum pass**, and in a project whose
argument is that it checks things, the difference is the whole argument. Recorded as
amber in [the audit response §A2](../../results/audit_response_2026-09-22.md) rather than rounded
up to done.

**Root cause of the 502, found on stopping the pod.** RunPod's Details panel reports
**"Out of Memory (OOM) Detected"**, and the pod's own spec reads **vCPU 0, Memory 0 GB**.
The "Start Pod using CPUs" fallback — taken because the original RTX 3090 was no longer
available — provisioned a pod with **no CPU or RAM allocation**, so the Jupyter server
was OOM-killed partway through serving a recursive directory walk. It was never going to
recover, and the restart that put it into "Initializing" could not have succeeded.

*Transferable:* a provider's "start without a GPU" fallback is not the same machine minus
the GPU. Check the allocated vCPU/RAM before assuming a degraded pod can serve even a
file copy, and treat a service that dies under a directory walk as an infrastructure
symptom rather than a transient.


### 5.2 The first retrieval script had no retries, and lost its manifest

`pull.py` v1 walked the API recursively with no retry and no resume. A single transient
empty response 130 files in killed it with a `JSONDecodeError`, **and because the
manifest was written only at the end, every checksum it had computed was lost.** The
files were on disk; the evidence about them was not.

The project's own rule — *make the job resumable, count completed work on disk* — was
applied to overnight GPU jobs and not to a ten-minute download. Write the manifest
incrementally or it is not a manifest.

### 5.3 A convoluted one-liner silently disabled a failure report

In `pull.py` v2 the mismatch-recording line was written as a nested conditional
expression with a walrus:

```python
(bad.append(...) if (got != sha or n != size) else None) or (ok := ok + 1) \
    if got == sha and n == size else None
```

Python binds this as `X if (match) else None`, so **`bad.append` is unreachable on a
mismatch** — the exact branch it exists to record. No mismatch occurred, so nothing was
lost, and the final report was driven by a separate recount from the manifest. But it is
a failure-reporting path that was dead on arrival, written while fixing a different
failure-reporting path. Clever expression syntax in error handling is how you get error
handling that does not run.

### 5.4 The anchor-agreement test was initially too strong, and finding out was the value

The first version asserted the surrogate equals `final` at **every** anchor. It failed on
four metrics — and the reason was not the bug it was written for. Four good-edges are
written by the handbook with **strict** inequalities (`contacts > 25`, `iface_plddt > 80`,
`cdr_sasa > 600`, `cdrh3_identity < 70`), so a value exactly on the edge is Medium in the
report and Good in the surrogate.

That disagreement is **intrinsic** — no continuous function agrees with a step function
*at* the step — and it is **not measure-zero**, because `contacts` is an integer count and
"exactly 25" is an ordinary outcome. The honest resolution was to correct the module's
own docstring (which overclaimed "agrees at every anchor"), scope the test to inclusive
edges, and add a separate test pinning the known divergence so it can never be
rediscovered as a surprise.

Attempting to "fix" it would have produced a **non-monotone** surrogate: forcing
`v == good` to score the Medium value while `v == good − ε` scores the Good value makes
the ranking function decrease as the metric improves.

### 5.5 A reliability figure that still does not reproduce

The record quotes single-seed reliability **0.629** for the 20-design shortlist. The
plug-in variance ratio on these data gives **0.28**, and no standard estimator tried
(ANOVA ICC, sampling-error-corrected between-variance, Spearman–Brown at k=3 or 7)
reproduces 0.629 from the recorded inputs. **Flagged, not corrected** — the original
script would settle it, and guessing would add a fifth number to a project already
carrying four.

---

## 6. Verification — how to know this works

```bash
uv run --with pytest pytest tests/ -q          # 17 passed
uv run --with python-pptx python scripts/57_build_submission.py
uv run python scripts/58_validate_submission.py submission/LOCKSMITH_DEV
uv run python scripts/70_epitope_patch_null.py
```

Healthy output, concretely:

- `17 passed`
- `built submission/LOCKSMITH_DEV.zip (0.7 MB)`, `final=96.0 viable=True`
- `(validating an isolated copy at /tmp/validate_…)` … `VALIDATION PASSED`, and
  `structures/` still contains **exactly two files** afterwards
- patch null: pooled real **0.712** vs contiguous **0.154**, 17/18 at p<0.05

**What a plausible-but-wrong result looks like here:** `VALIDATION PASSED` while
`structures/` has grown to five files. The package validates and is *also* no longer the
package §4.2.1 describes. That is why the assertion is on the directory listing rather
than on the two files being present.

---

## 7. Honest assessment

**Solid.** The disqualification risk is closed and was verified by running the tool
rather than by recalling the flag. The pod data is retrieved and the headline reproduces.
The project has tests and history for the first time. Two divergences are now impossible
rather than documented.

**Better than expected.** The patch null is a genuinely stronger instrument than the
test it replaces, and it cost nothing — the data was already on disk.

**Weak.** The checksum pass is incomplete (§5.1). The decoy-patch control still has not
been run, and it remains the only control that could falsify conditioning.

**Not established.** Whether any Challenge 2 design clears the seven gates — still no
metric computed for any of them, unchanged by tonight. Whether the G3 aromatic filter
means anything once the outcome variable is not pose retention.

**Does not support.** That the newly-first design is better than the shipped one (0.191
against a 0.226 seed sd). That `interaction_pae` is useless (undetected ≠ absent). That
RF2 agreement can be rescued by filtering (§4.5).

---

## 8. Next steps

1. **Finish the sha256 pass** when the pod's Jupyter is reachable, or re-pull with an
   incremental manifest. `verify.py` is written and idempotent.
2. **Run the decoy-patch control** — hotspots on the opposite face of PD-1. The one
   remaining control that could fail. GPU run.
3. **Sequence the 18 unconditioned backbones** (~2–4 GPU-hours, ~$1–2) to separate range
   restriction from a dead `interaction_pae`.
4. **Re-examine G3** against an outcome that is not pose-retention-to-parent.
5. **Extend the test file as findings arrive** — the standing rule is now that a
   correction ships as an assertion, not only as a paragraph.

---

## 9. Glossary

**Band** — one of Good/Medium/Poor, into which each metric's raw value falls.
**Band value convention** — how a band becomes a 0–10 number; the handbook gives ranges
only, so `bottom`/`midpoint`/`top` are all defensible readings.
**Surrogate** — a continuous stand-in for the banded composite, used for *ranking* only,
because the composite takes three distinct values across the pool.
**Anchor** — the (raw value, sub-score) pair the surrogate interpolates through.
**Strict edge** — a band boundary the handbook writes with `>` or `<` rather than `≥`/`≤`.
**ICC** — intraclass correlation; between-group variance as a fraction of the total.
**Detectable floor** — the smallest ICC an experiment of a given `n, k` can distinguish
from zero at α=0.05; an ICC without one is uninterpretable.
**Optional stopping** — extending a sample after an interim look, then testing at nominal
α; inflates type-I error and biases the effect estimate upward.
**Contiguous surface patch** — a set of residues formed by taking a seed residue's
nearest neighbours; the correct null for an epitope, because it matches the geometry and
not merely the size.
**`frac_iface_on_epitope`** — of the target residues the designed loops contact, the
fraction that are conditioned hotspots.
