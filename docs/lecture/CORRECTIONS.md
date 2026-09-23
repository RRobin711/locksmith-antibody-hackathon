# Corrections to this course

**One fact, one place.** When something in this course is overtaken, the correction is
recorded *here* and the affected chapters carry a pointer to it. Chapters are not
individually rewritten with provisional numbers — doing that is the exact defect the course
documents (see [[08-what-broke|Class 2, generator (iv): a convention that lived in two places, or in none]]).

Read this file before trusting any Challenge 2 number anywhere in the course.

---

## C1 — Challenge 2's computational evidence is withdrawn

**Raised 2026-09-23. Status: LIVE, re-screen in progress. Challenge 1 is unaffected.**

### What happened

Every Challenge 2 fold this project ever ran paired the **123-residue** antigen with a
cached alignment whose query is **113 residues**. Boltz compares the two lengths, **discards
the alignment**, and folds the antigen single-sequence. It announces this on a stdout stream
the harness captured and threw away.

So every Challenge 2 number was measured without an antigen alignment, which is the
flattering condition.

### The measurement

From `results/msa_silently_discarded.md`, a 2×2 on [[03-the-toolchain#4.3 ipSAE — interface confidence from the PAE|ipSAE]]:

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
- **The Challenge 2 ranking.** In the first 5 designs re-screened with a correct alignment
  (`data/msa_cache/pd1_123_handbook.csv`, 3407 sequences, query matching the antigen
  exactly): **0 of 5 clear**, the packaged design falls **0.864 → 0.013**, and the worst of
  the five *rises* from 0.116 to **0.440**. The old ranking carries no information about the
  correct one.

### What it does NOT invalidate

- **Challenge 1.** Its folds used a server MSA matched to its own antigen; the discard
  warning appears once in `runs/diffusion_samples.log`, for the Challenge 2 arm only. Every
  Challenge 1 number in this course stands.
- **Everything in [[04-measurement-theory|measurement theory]],
  [[05-experiment-design|experiment design]] and
  [[06-allocation-and-selection|allocation and selection]]** that is derived from the
  Challenge 1 pool of 239 designs — [[04-measurement-theory#1.3 Reliability|reliability]], [[04-measurement-theory#2. The intraclass correlation, and metrics that turn out to be constants|ICC]], [[04-measurement-theory#5. Range restriction — and the insight that selection is the restricting operation|range restriction]], allocation, the
  [[06-allocation-and-selection#3. Winner's curse|winner's curse]], the band-grid result. None of it touches Challenge 2.
- **The `N→Q` versus `S→A` contact-count finding.** Its *relative* claim — that the fix
  mutating 10 and 19 antigen contacts destroys the interface while the one mutating zero does
  not — was measured within a single condition, so the comparison survives even though the
  absolute values were inflated. Treat the 60-fold ratio as intact and the 0.864 baseline as
  withdrawn.

### Why it belongs in the course rather than just being fixed

This is the course's own thesis landing on the course while it was being written. It is a
**[[08-what-broke#Class 1 — Silent failures|silent failure]] of exactly the catalogued kind**: nothing errored, the fold completed, the
structure was confident, a plausible number came back — computed on an input the tool had
quietly changed. The one diagnostic that would have caught it, a warning on stdout, was
discarded by the harness.

It is also the eighth member of the inherited-parameter family in
[[07-the-campaign|the inheritance ledger]]: the 113-mer construct entered from 5GGS, was
identified on day 9 as "the construct we fold is not the construct we submit", and its
consequence for the *alignment* was not traced until now.

**Transferable form:** *when a tool silently substitutes a degraded input, the failure is
invisible in the output and visible only in a stream you are probably discarding. Capture
tool stderr and stdout, and grep them for the words the tool uses when it gives up on
something.*

### Open

The re-screen covers 5 of 30 designs. Until it completes, treat every Challenge 2 figure in
this course as **withdrawn, not replaced**. `STATE.md` carries the current status.

---

*No further corrections at this time.*
