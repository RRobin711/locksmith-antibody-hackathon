---
date: 2026-09-23
tags: [project, lecture, learning, problem]
status: living
---

# Corrections to this course

**One fact, one place.** When something in this course is overtaken, the correction is
recorded *here* and the affected chapters carry a pointer to it. Chapters are not
individually rewritten with provisional numbers — doing that is the exact defect the course
documents (see [Class 2, generator (iv): a convention that lived in two places, or in none](08-what-broke.md)).

Read this file before trusting any Challenge 2 number anywhere in the course.

**Scope.** This file covers what a *reader of the course* must not trust, and C1/C2 below
are the fullest treatment of those two items anywhere in the project. Every other claim the
project has withdrawn — scores, method, shipped prose, and the figures that are flagged as
not reproducing — is indexed in
[the project-wide retraction register](../../results/retractions.md).

---

## C1 — Challenge 2's computational evidence is withdrawn

**Raised 2026-09-23. Status: re-screen COMPLETE. Challenge 1 is unaffected.**

### What happened

Every Challenge 2 fold this project ever ran paired the **123-residue** antigen with a
cached alignment whose query is **113 residues**. Boltz compares the two lengths, **discards
the alignment**, and folds the antigen single-sequence. It announces this on a stdout stream
the harness captured and threw away.

So every Challenge 2 number was measured without an antigen alignment, which is the
flattering condition.

### The measurement

From `results/msa_silently_discarded.md`, a 2×2 on [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae):

| | antigen MSA used | antigen MSA absent |
|---|---|---|
| baseline (pre-fix) | **0.012** | 0.773 |
| `S→A` (the packaged design) | **0.012** | 0.686 |

The sequon mutation is irrelevant to the effect; **the alignment is the whole effect.** The
no-MSA cells reproduce this project's historical envelopes exactly, which is what identifies
the condition every prior fold was run in.

### What it invalidates

- **"1 of 30 designs clears"** — measured entirely in the flattering condition.
- **ipSAE 0.864** for `bb_2_0_dldesign_1` — the same design with a correct alignment scores
  **0.013**.
- **The composite 91.2, and its "viable" status**, as evidence of anything. The number is
  still what the packaged files re-derive; it is no longer evidence about the molecule.
- **The Challenge 2 ranking — completely.** The re-screen is now complete
  (`results/challenge2_rescreen.md`). With a correct alignment
  (`data/msa_cache/pd1_123_handbook.csv`, 3407 sequences, query matching the antigen
  exactly), **1 of 30 still clears — but it is a different molecule:**

  | | design | ipSAE, correct MSA | 5-sample range | ipSAE, old (no MSA) | old rank |
  |---|---|---|---|---|---|
  | ✅ | `bb_1_0_dldesign_0` | **0.637** | 0.423–0.855 | 0.014 | **29th of 30** |
  | | `bb_1_0_dldesign_1` | 0.440 | — | 0.116 | 18th |
  | | `bb_4_0_dldesign_1` | 0.372 | — | 0.013 | 26th |
  | ❌ | `bb_2_0_dldesign_1` *(packaged)* | **0.013** | 0.000–0.817 | 0.864 | **1st** |

  The design that clears under a correct alignment ranked **29th of 30** under the broken
  one; the design that was packaged and shipped ranked 1st and now scores **0.013**. The old
  ranking was not merely noisy — over the top of the pool it was close to **inverted**.

  The replacement winner is not a clean substitute: `bb_1_0_dldesign_0` clears the binding
  gate but **fails handbook §9.2**, carrying two HIGH developability liabilities, and its
  worst diffusion sample sits at **0.423**, so it clears without comfort. A liability fix
  would cost interface quality it does not have to spare — see
  [the contact-count result](01-the-biological-problem.md#63-nq-versus-sa-the-contact-count-result) for why that trade is not free.

### What it does NOT invalidate

- **Challenge 1.** Its folds used a server MSA matched to its own antigen; the discard
  warning appears once in `runs/diffusion_samples.log`, for the Challenge 2 arm only.
  **Narrowed 2026-09-26:** this bullet originally ended "Every Challenge 1 number in this
  course stands", which is true of *this defect* and false as a blanket assurance —
  Challenge 1's composite changed 96.0 → 94.0 on 2026-09-24 for an unrelated reason. See
  [C3](CORRECTIONS.md#c3--challenge-1s-composite-is-940-not-960). *A correction scoped
  to one defect should not be worded as a general clearance.*
- **Everything in [measurement theory](04-measurement-theory.md),
  [experiment design](05-experiment-design.md) and
  [allocation and selection](06-allocation-and-selection.md)** that is derived from the
  Challenge 1 pool of 239 designs — [reliability](04-measurement-theory.md#13-reliability), [ICC](04-measurement-theory.md#2-the-intraclass-correlation-and-metrics-that-turn-out-to-be-constants), [range restriction](04-measurement-theory.md#5-range-restriction--and-the-insight-that-selection-is-the-restricting-operation), allocation, the
  [winner's curse](06-allocation-and-selection.md#3-winners-curse), the band-grid result. None of it touches Challenge 2.
- ~~**The `N→Q` versus `S→A` contact-count finding.**~~ **This bullet was wrong and is
  withdrawn 2026-09-26.** It argued the comparison survives because both arms were measured
  within a single condition, and told the reader to "treat the 60-fold ratio as intact".
  [C2, immediately below in this same file](CORRECTIONS.md#c2--the-contact-count-rule-is-refuted-and-three-of-its-four-instances-are-void),
  raised the same day, refutes the finding outright — so C1 and C2 contradicted each other
  for three days. A within-condition comparison is not rescued by being internally
  consistent when the condition itself is the thing that moved: under a correct alignment
  that design scores **0.012 regardless of its sequence**, which is not a ratio of
  anything. Read C2, not this bullet.

  *Noted rather than quietly deleted, because it is the register's own failure mode: a
  corrections file is a generated-adjacent artefact and goes stale like any other.*

### Why it belongs in the course rather than just being fixed

This is the course's own thesis landing on the course while it was being written. It is a
**[silent failure](08-what-broke.md#class-1--silent-failures) of exactly the catalogued kind**: nothing errored, the fold completed, the
structure was confident, a plausible number came back — computed on an input the tool had
quietly changed. The one diagnostic that would have caught it, a warning on stdout, was
discarded by the harness.

It is also the eighth member of the inherited-parameter family in
[the inheritance ledger](07-the-campaign.md): the 113-mer construct entered from 5GGS, was
identified on day 9 as "the construct we fold is not the construct we submit", and its
consequence for the *alignment* was not traced until now.

**Transferable form:** *when a tool silently substitutes a degraded input, the failure is
invisible in the output and visible only in a stream you are probably discarding. Capture
tool stderr and stdout, and grep them for the words the tool uses when it gives up on
something.*

### Where this leaves Challenge 2

All 30 designs have been re-screened. Treat every Challenge 2 figure printed in the body of
this course as **superseded**.

> **Updated 2026-09-26 — the table above is itself no longer the end of the story, and the
> zip is no longer stale.** `bb_1_0_dldesign_0` was the best of the *re-screened original
> pool*; it was then superseded by the constrained re-design campaign (18 backbones × 8
> constrained sequences, 144 folds). **The shipped Challenge 2 design is `bb_8_0`** — ipSAE
> **0.904** on `model_0`, median of five diffusion samples **0.859**, composite **93.6**,
> viable on **5 of 5** samples. The package was rebuilt on 2026-09-25 and passes validation
> from its own files. The re-screen table stays as written because it is what demonstrates
> the inversion, which is the teachable part.
>
> Note the campaign that produced `bb_8_0` also withdrew two of its own claims — see
> [the retraction register, §B8](../../results/retractions.md).

The sharpest lesson is not that the number fell. It is that **the ranking inverted**: a
silently degraded input did not add noise around a roughly-correct order, it produced an
order that was actively misleading, with the eventual winner sitting 29th of 30. This is the
same shape as the `recycling_steps=3` episode in
[compression versus noise](06-allocation-and-selection.md#6-compression-versus-noise-in-an-under-converged-sampler)
— under-informed prediction compresses and scrambles a ranking rather than blurring it.

---

## C2 — The contact-count rule is refuted, and three of its four instances are void

**Raised 2026-09-23. Status: refuted as a predictor; the replacement explanation is unresolved.**

### What the course says

[Chapter 00 §4.4](00-orientation.md#44-scientific-findings) calls this "the best result in the
project", and [chapter 01 §6.3](01-the-biological-problem.md#63-nq-versus-sa-the-contact-count-result)
develops it at length: handbook §9 lists `N→Q` and `S→A` as interchangeable fixes for a
glycosylation sequon; the asparagine acceptors carried **10 and 19** antigen contacts and
the serines **zero**; `N→Q` collapsed ipSAE **0.864 → 0.014** while `S→A` stayed viable 5 of
5. The claimed generalisation was that **the contact count on the mutated residue predicts
which prescribed fix is safe**, for free, before any folding.

### Why it does not hold

**A residue with zero contacts is not safe.** A third fix arm, `N91Q`, mutates a residue
with **no antigen contacts in any of five diffusion samples** and still collapses the
interface:

| arm | mutation | antigen contacts | ipSAE median | viable |
|---|---|---|---|---|
| unfixed | — | — | **0.637** | 3/5 |
| `fix91` | `N91Q` | **0** | 0.128 | 0/5 |
| `fix31` | `G32A` | 4 | 0.140 | 0/5 |
| `fix_both` | both | — | 0.034 | 0/5 |

NetSolP holds at **0.617** across every arm, so the collapse is entirely interface-side and
not a solubility artefact.

**And three of the rule's four instances are void.** Both original measurements — `N→Q`
fatal at 10 and 19 contacts, `S→A` free at 0 — came from `runs/sequon_fix`, which folded
with the antigen alignment silently discarded (see [C1](CORRECTIONS.md#c1--challenge-2s-computational-evidence-is-withdrawn)).
Under a correct alignment that design scores **0.012 regardless of its sequence**. They are
therefore two readings of a *condition*, not of a substitution.

What survives is Challenge 1's `N55Q`, **free at 3 contacts**, and this design's `N91Q`,
**fatal at 0 contacts**. Under correct alignments the rule fails *even in direction*.

### The competing explanation, and why it is not settled

The parsimonious reading is that **a design sitting 0.037 above the cutoff cannot absorb any
single-residue change at all.** Two observations support it: all three arms land in
approximately the same place rather than the double mutant being twice as damaged, which is
not what independent per-residue damage looks like; and Challenge 1's free `N55Q` sat at
ipSAE **0.821**, comfortably clear of its edge.

The two explanations are **not distinguished by the data in hand**, and no design in this
pool has comfortable margin under a correct alignment, so the pool cannot settle it. Recorded
as unresolved rather than replaced.

### What still stands

The weaker and older claim is untouched and is the one to keep: **a prescribed developability
fix is a design change and must be measured, not assumed.** Handbook §9 presenting `N→Q` and
`S→A` on the same line as equivalents is still wrong; three of three fix arms here collapsed
a viable design. What is gone is the cheap structural *predictor* of which fix to choose.

### The meta-lesson, which is the durable part

A finding built on four instances lost three of them to a single upstream defect discovered a
day later. **Count how many of a finding's instances share one apparatus. If they all do, the
finding is one bug away from empty** — and its apparent replication across instances is not
independent evidence at all.

---

---

## C3 — Challenge 1's composite is 94.0, not 96.0

**Raised 2026-09-24. Status: settled, mechanism in place. Unrelated to C1.**

### What happened

`dockq.compute` parsed DockQ's **printed** summary line, which the tool formats to 3
decimal places, and then rounded that again itself. The true value is

```
GlobalDockQ = 0.7995794972281312
```

which is **0.00042 below** the §5.2 Good edge at 0.80 and therefore bands **medium**, worth
8 sub-score points rather than 10. The printed `0.800` banded **good**. Challenge 1's
composite is **94.0**, not 96.0, and the design is unchanged — this is a measurement
correction, not a regression.

Any true value in the half-open interval **[0.7995, 0.800)** was misbanded the same way, so
the defect is a property of the parser, not of this structure.

### Why it is worth a numbered correction

Because it is the project's own thesis turned on itself. This course argues throughout that
the rubric is gameable by whoever controls the structure; two of its points came from a
`printf`. A project making that argument cannot keep them.

It is also **not covered by C1**, which is scoped to the Challenge 2 MSA defect and
explicitly exonerates Challenge 1. That exoneration is correct *for that defect* and was
being read as general.

### What it invalidates

Every occurrence of Challenge 1 at `final 96.0`, and the convention triple
`84.0 / 90.0 / 96.0`, which is now **81.0 / 87.5 / 94.0** across the three readings §5.2
permits. Known live in this course:

**This index was 4 rows until 2026-09-28 and is now 32.** The short version was not a
judgement that the rest did not matter — it was never completed, and an index that looks
authoritative while being 12% complete spends a reader's scepticism in the wrong direction,
which is the same defect C3's own "every Challenge 1 number stands" clause had.

Regenerate it rather than trusting these line numbers:

```bash
cd docs/lecture && grep -n "96\.0" *.md | grep -v "^CORRECTIONS.md" | awk -F: '$2!=9'
```

**A — Challenge 1's composite asserted as 96.0.** Read **94.0**.

| file | line(s) |
|---|---|
| `00-orientation.md` | 307 |
| `01-the-biological-problem.md` | 19, 553, 573, 596, 602, 701 |
| `02-the-engineering-problem.md` | 283, 756 |
| `07-the-campaign.md` | 638, 640 |
| `09-critique.md` | 214, 343, 434 |

**B — envelopes with 96.0 as an endpoint.** The upper endpoint was the misbanded value; the
envelope has not been recomputed, so treat the *width* as reported and the *top* as 94.0.

| file | line(s) |
|---|---|
| `01-the-biological-problem.md` | 704 |
| `03-the-toolchain.md` | 213, 223, 224 |
| `06-allocation-and-selection.md` | 543, 613 |
| `07-the-campaign.md` | 601, 602, 681 |

**C — the band→score convention triple `84.0 / 90.0 / 96.0`.** Read **81.0 / 87.5 / 94.0**.

| file | line(s) |
|---|---|
| `02-the-engineering-problem.md` | 260 |
| `06-allocation-and-selection.md` | 388 |
| `07-the-campaign.md` | 466 |

**D — Challenge 2 seed composites `93.6 / 96.0 / 93.6`.** Superseded by **C1**, not by C3:
these folds used the discarded alignment. The packaged Challenge 2 design is `bb_8_0` at
**93.6**.

| file | line(s) |
|---|---|
| `03-the-toolchain.md` | 212 |
| `06-allocation-and-selection.md` | 612 |
| `07-the-campaign.md` | 592, 593 |

**E — historical incident records.** The number is correct *as the record of what the
package said at the time* and is left alone; it is listed so a reader does not mistake it
for a current score.

| file | line(s) | what it records |
|---|---|---|
| `02-the-engineering-problem.md` | 771 | the deck/zip divergence |
| `08-what-broke.md` | 426 | defect P13, same incident |

Eight further mentions are **self-describing** — they already say the number is stale
(`00-orientation.md:266`, `02-the-engineering-problem.md:182, 252`, `09-critique.md:327, 431`,
`README.md:91, 95, 129`) and need nothing.

### One exception to the no-rewrite policy

`02-the-engineering-problem.md` §3.3 **was rewritten** on 2026-09-28, and it is the only
place in the course that has been. It is a *worked derivation* — a reader reruns the
arithmetic — and it did not merely carry a stale total: its `dockq` row read
`0.800 | good | 10.0`, so it presented the rounding defect itself as correct working and
taught `binding = 60/6 = 10.000`. Indexing that would have left the course teaching a wrong
operation behind a pointer. It now reads `0.799579 | medium | 8.0`, `binding = 58/6 =
9.667`, `final = 94.0`, and carries the C3 pointer inline.

The distinction is the policy's actual boundary: **prose that quotes a number is indexed;
arithmetic that produces one is corrected.** Everything else in this course remains as
written.

### The mechanism

Two, because surfacing and preventing are different jobs:

1. `dockq.compute` now passes `--json` and reads `GlobalDockQ` unrounded. The returned value
   is **not** rounded at all, because banding must see the true number.
2. `score.evaluate` declares each metric's display precision and appends to
   `Scored.rounding_risk` when a value lands within ±0.5 ulp of any band edge. Packaged
   tables then print that metric at 6 dp instead of 3 — which is why the shipped
   `scores.md` reads `dockq 0.799579 | medium` rather than the self-contradictory-looking
   `0.800 | medium`.

**Transferable form:** *any parse of a **rendered** number inherits that renderer's
precision, and a threshold comparison is exactly where the lost digits matter. Parse the
machine-readable output when one exists — and when a value sits within its display
precision of a decision boundary, print more digits rather than fewer.*

---

## C4 — §6.6's preflight did not require the tools it lists

**Raised 2026-09-28. Status: FIXED in code. Affects [Class 3 §6.6](03-the-toolchain.md).**

### What the chapter says

§6.6 introduces `scripts/00_doctor.py` with "exits 0 only if every required check
passes", then enumerates, in one list: the Python version, the venv, the torch/CUDA
chain, the matmul, RAM, swap, disk, "`DockQ` and `prodigy` on PATH; `vendor/ipsae/ipsae.py`
present; `anarcii` and `freesasa` importable; and the four reference PDBs present."

Only two items in that sentence are marked as exceptions — PTX and the bf16 matmul,
both flagged "reported, not required".

### What the code did

Everything from `DockQ` onwards was `required=False`. A machine with **none** of the
five external tools installed printed `All required checks passed.` and exited 0.

The inverse error sat beside it. `check("running inside project venv", "locksmith" in
sys.prefix)` **was** required, and tests a substring of a path — so a correct checkout
in a directory not named `locksmith` failed the preflight. Verified 2026-09-28 by
copying the tree to a directory named `citest`: the old expression evaluates False on
a perfectly good checkout.

### Why this is worse than a short list

The required set was **backwards**, not merely incomplete. The README sends a grader
here from the *validator* section, and `scripts/58_validate_submission.py` imports
`dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa` and touches CUDA nowhere. So
validating the package needs the five tools and **no GPU**, while the preflight
demanded a GPU and **none of the tools**. It could not fail for a grader missing
everything it needed, and did fail for a grader whose only sin was a CPU.

A third gap the chapter's list also has: the course and the README both tell you to
install ~4.7 GB of NetSolP ONNX models, and the preflight checked NetSolP **zero**
times.

### The fix

`--scope {fold,validate,all}`, with the required set declared per scope in a
`REQUIRED` dict rather than as a flag on each call, and NetSolP's paths *imported*
from `locksmith.metrics.netsolp` so the preflight cannot drift from the metric.
Five tests in `tests/test_invariants.py` pin the sets, all mutation-verified.

Behaviour now (measured, this machine): tools off `PATH` → `2 required check(s)
failed for scope 'validate'`; `NETSOLP_DIR` unset → 2 failed; `CUDA_VISIBLE_DEVICES=""`
with `--scope fold` → 3 failed; unmutated → exit 0 in all three scopes.

*The transferable point is the one this course already makes about controls, turned on
the course's own tooling: **a check that cannot fail is not evidence**, and the way it
usually cannot fail is that its required set was written from what was easy to check
rather than from what the job needs.*

---

## C5 — the NetSolP triple `0.379 / 0.463 / 0.733`

**Raised 2026-09-28 (withdrawn project-wide 2026-09-23). Affects
[Class 0 §orientation](00-orientation.md) and [the glossary](10-glossary.md).**

*Numbering note: the project-wide register also calls this §C5. The two numbering schemes
are independent and the coincidence is accidental — this file's C1–C4 are not the
register's C1–C4.*

### The claim

Both chapters state that NetSolP "ships three model variants that score a licensed
antibody at **0.379, 0.463 and 0.733** against a 0.50 cutoff", and Class 0 adds that
"the CLI default **would have failed every design**".

### Why it is wrong

The triple **mixes VH and VL across three different variants and two different
constructs**. It reads as one antibody scored three ways; it is in fact ESM12-VH,
Distilled-VL and ESM1b-VH. The numbers are **per-chain pairs** and must be quoted as
such. [Class 3 §4.4](03-the-toolchain.md#44-netsolp-10--sequence-only-solubility-and-a-positive-control-that-chose-the-model)
already prints the correct table:

| | ESM1b (5-fold) | ESM1b-distilled | ESM12 (5-fold) |
|---|---|---|---|
| VH | 0.733 | 0.637 | 0.379 |
| VL | 0.569 | 0.463 | 0.346 |
| Fab heavy | 0.623 | 0.491 | 0.352 |
| Fab light | 0.626 | 0.448 | 0.312 |

On **Fab** chains `ESM12` gives 0.35 / 0.31 and `Distilled` 0.49 / 0.45, both failing the
cutoff, while the ESM1b ensemble passes at 0.57–0.73. On **Fv** — which is what the
handbook specifies, twice — pembrolizumab reads VH **0.733** / VL **0.569**, which inverts
*which chain limits* `min(VH, VL)`.

The second clause is separately retracted: NetSolP's `predict.py` **defaults to ESM1b**,
which passes, so the CLI default would not have failed every design. The counterfactual was
also never computed on the right input, because the construct convention was independently
wrong (Fab fed where the handbook says Fv). The shipped
`reproducing_our_numbers.md` says the opposite of the course, and the shipped document is
right. [Class 3 §4.4](03-the-toolchain.md#44-netsolp-10--sequence-only-solubility-and-a-positive-control-that-chose-the-model)
already records this self-correction; Class 0 and the glossary did not inherit it.

### What survives

The lesson the bullet was written to carry is untouched and is *stronger* stated correctly:
**anything that can move a result across a threshold belongs in the config with its
evidence, not left at whatever the tool ships.** Pinned as `netsolp_model_type: ESM1b` in
`config/metrics.yaml`. The variant choice really did decide viability — it just did so
per chain, and not via the CLI default.

*Transferable: quote a per-chain metric per chain, or you will compare two different
quantities later. A single number summarising a 4×3 table is a claim that the table has
one dimension.*

---

## C6 — "an anti-lysozyme antibody cleared all five cutoffs" is true only on the truncated antigen

**Raised 2026-09-28. Withdrawn project-wide as [register §C9](../../results/retractions.md)
on 2026-09-26; the course never inherited it.** Affects **nine** places in this course, listed
below.

### The claim

HyHEL-10, an antibody raised against hen egg lysozyme, docked onto PD-1 and **cleared all
five §7.2 hard cutoffs** — ipSAE 0.609, ΔG −12.4, 77 contacts, interface pLDDT 85.0, CDR
SASA 1084. It is the course's single most-quoted finding and the front page's rhetorical
peak.

### What is wrong with it

It is a property of **three** parameters, and the course names only one.

| parameter | course says | also true |
|---|---|---|
| estimator | ✅ `model_0`, the argmax of five draws | on the **median** it fails, 0.219 |
| **input construct** | ❌ not named | on the **113-mer** only |
| threshold | n/a here | see [C1's sibling, register §C1](../../results/retractions.md) |

On the **repaired 119-residue** antigen HyHEL-10's best of five is **0.409** and it clears
nothing:

| construct | HyHEL-10 median | best of 5 | gates cleared | positive control |
|---|---|---|---|---|
| 113-mer (used first) | 0.219 | **0.609** | **5/5** | **FAILED** — nivolumab 0.017 |
| 119-mer (repaired) | 0.228 | **0.409** | **4/5**, fails ipSAE | 2/2 clear |

The 113-mer was missing **6 of nivolumab's 14 epitope residues**. That is why the panel's own
positive control failed, and why it was pre-registered **INCONCLUSIVE** —
`results/negative_control.md` says in terms that the negative arm *"must not be read as
evidence that the gate discriminates."* It was read that way anyway. **The flattering result
and the broken control had the same cause: a truncated antigen.**

### The cetuximab margin is wrong by about 90×

Three places say cetuximab's median "sits **0.006** under the cutoff" (0.594 against 0.60).
That is the 113-mer. On the repaired construct cetuximab's median is **0.052** — **0.548
under**. This one is not merely unqualified, it is superseded, and it is built to be
memorable, which is exactly why it travelled.

### What survives, and it is still strong

**Four of the five gates reject 0 of 6 known-wrong antibodies on *both* constructs.** §7.2
rests on ipSAE alone. That claim never depended on the truncation. On the repaired construct
the control resolves cleanly: **2/2 positives clear, 6/6 negatives fail, separated by 0.184
ipSAE**.

**What does not survive:** *"the rubric accepts an antibody that cannot bind."* It accepts
one only on a construct whose own positive control it also fails.

### Where it is live in this course

Indexed rather than rewritten, per this file's standing policy — these are prose quoting a
number, not arithmetic a reader reruns (see [C3](#c3--challenge-1s-composite-is-940-not-960)
for where that boundary falls). Each site now carries an inline pointer here.

| file | line | claim |
|---|---|---|
| `README.md` | 109 | "cleared all five cutoffs as a PD-1 binder" |
| `00-orientation.md` | 296 | same |
| `01-the-biological-problem.md` | 821 | "cleared all five hard cutoffs as a PD-1 binder" |
| `01-the-biological-problem.md` | 752 | cetuximab "0.006 under the cutoff" |
| `02-the-engineering-problem.md` | 403 | "cleared all five hard cutoffs on `model_0`" |
| `05-experiment-design.md` | 649 | "sweeping all five viability gates" |
| `06-allocation-and-selection.md` | 562 | "cleared all five hard viability cutoffs" |
| `07-the-campaign.md` | 608 | "cleared all five §7.2 hard cutoffs" |
| `07-the-campaign.md` | 614 | cetuximab "0.006 under the cutoff" |

*Transferable, and stated three times in three variables now: a rate is a property of every
parameter it was computed under — threshold, estimator, input construct. Fixing one axis is
not evidence you have found them all, and each time this project fixed one it stopped
looking.*

---

*No further corrections at this time.*
