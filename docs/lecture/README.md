---
date: 2026-09-23
tags: [project, lecture, course, protein-design, antibody, measurement, learning, index]
status: living
---

# Designing a cancer drug on a laptop — a complete course

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1–C6](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding, and **C3 applies to Challenge 1**: its composite is **94.0**, not the 96.0 this course derives in several places. Challenge 1 is unaffected *by the alignment defect*, which is narrower than "unaffected". **C4** (the preflight), **C5** (the NetSolP triple) and **C6** were added 2026-09-28 — and **C6 applies to this course's most-quoted finding**: "an anti-lysozyme antibody cleared all five cutoffs" holds on the **truncated 113-mer only**; on the repaired 119-mer it clears nothing.

A twelve-chapter lecture course built from the nine-day Locksmith Bio antibody
design campaign (2026-09-14 → 2026-09-22). It teaches the whole thing from first
principles: the biology, the engineering, the mathematics, the nine-day
narrative, everything that broke, and an adversarial re-evaluation of the process
itself.

**Written for** a reader with a general CS or maths background and no prior
exposure to structural biology. Every term is defined on first use. The stated
bar is that you should be able to **rebuild the system from these documents
alone.**

**The honest summary before you start.** The campaign produced two scoring
antibody designs and then spent most of its remaining effort establishing that
its own scores do not mean what they appear to mean. Neither headline number is
evidence that anything binds. That is not a failure of the project — it is its
main result, and it is why the course is worth reading.

---

## The chapters

| # | Chapter | What it covers |
|---|---|---|
| 00 | [Orientation](00-orientation.md) | The four questions answered directly: what we had to do, what we needed to know, what we used, what we made |
| 01 | [The biological problem](01-the-biological-problem.md) | T cells, PD-1, checkpoint blockade, antibody architecture, epitopes, developability chemistry, and what the scores do not say |
| 02 | [The engineering problem](02-the-engineering-problem.md) | The pipeline, the rubric as data, build-the-judge-first, and programs that exit 0 having done the wrong thing |
| 03 | [The toolchain](03-the-toolchain.md) | Every tool with versions and gotchas, the dependency fault line, the Blackwell GPU saga, and what it all cost |
| 04 | [Measurement theory](04-measurement-theory.md) | Reliability, ICC, Spearman–Brown, attenuation, range restriction — how good is my measurement? |
| 05 | [Experiment design](05-experiment-design.md) | Power, nulls, null geometry, controls, pre-registration — what would have to be true for me to be wrong? |
| 06 | [Allocation and selection](06-allocation-and-selection.md) | Depth versus breadth, the winner's curse, banding, order statistics — where should the next measurement go? |
| 07 | [The campaign](07-the-campaign.md) | The nine days as narrative, with the fold ledger and the parameters inherited unexamined |
| 08 | [What broke](08-what-broke.md) | The full failure catalogue: silent failures, withdrawn claims, blind controls, wasted hours |
| 09 | [The critique](09-critique.md) | The adversarial re-evaluation — what was excellent, what was mis-sequenced, and three findings that contradict the project's own record |
| 10 | [Glossary](10-glossary.md) | Every term, acronym and metric defined |
| 11 | [Study plan](11-study-plan.md) | Reading orders, prerequisite curriculum, self-tests, exercises, and a checklist |

---

## Where to start

- **Just want the answers?** [Chapter 00](00-orientation.md) alone, about twenty minutes.
- **Want the story?** [Chapter 07](07-the-campaign.md), then follow its links.
- **Don't care about antibodies?** Chapters [04](04-measurement-theory.md),
  [05](05-experiment-design.md) and [06](06-allocation-and-selection.md) are
  field-independent and are where the compounding knowledge lives. This is the
  recommendation for most readers.
- **Going to build something like this?** [Chapter 02](02-the-engineering-problem.md)
  with `config/metrics.yaml` open beside it, then
  [Chapter 08](08-what-broke.md), then the Track C exercises in
  [Chapter 11](11-study-plan.md).
- **Want to know what went wrong?** [Chapter 09](09-critique.md).

---

## The three ideas the course is built on

1. **A program that runs without error is not evidence it did what you intended.**
   The dangerous failure is not the crash. It is the number in the right range,
   with the right units, computed on the wrong thing. This project catalogued 26
   of them.

2. **Reliability is not validity.** You can measure something very precisely and
   still be measuring the wrong thing. The campaign spent five sessions refining
   how precisely it measured, then discovered that five of its eight metrics were
   constants, that it was really ranking on three, and that the largest
   contributor of those three was blind to the interface it was supposed to score.

3. **A null is only meaningful as "no effect larger than x."** Four claims were
   published here as findings of absence and later reversed — all from the same
   error, all at small n, all in the direction of the more interesting story.

---

## What the campaign produced

| | design | shipped | note |
|---|---|---|---|
| Challenge 1 | `mpnn_T0.5_s104_036` + N55Q | **94.0** | CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to pembrolizumab |
| Challenge 2 | **`bb_8_0`** | **93.6** | viable on 5/5 diffusion samples |

> **Updated 2026-09-26.** This table read `96.0` and `bb_2_0_dldesign_1` + S→A at `91.2`
> until today. Both were superseded: Challenge 1 fell to 94.0 when DockQ was read unrounded
> (see [C3](CORRECTIONS.md)), and `bb_2_0_dldesign_1` is the design the silently-discarded
> MSA promoted — it scores **0.013** under a correct alignment and was replaced by `bb_8_0`
> (see [C1](CORRECTIONS.md)). The course body still derives 96.0 in places; those are
> indexed in C3 rather than rewritten.

**21,367 lines of Python** (src 3,699 · scripts 16,834 · tests 710), 34 tests *(42 as of 2026-09-29)*,
13 pre-registrations, 5 adversarial audits, and ~280,000 words of tracked Markdown
(the twelve chapters here are 75,166 of it).

*These were frozen at 2026-09-23 and were wrong by 2026-09-26 — the block previously
claimed 18,020 lines, 30 tests, 11 pre-registrations and 165,333 words. A count in prose
is a claim like any other; these were recomputed from `git ls-files` on 2026-09-26.*

And five results that matter more than either score:

1. Four of five hard cutoffs reject **0 of 6** known-wrong antibodies (on the **median of five** draws).
2. **HyHEL-10, an anti-lysozyme antibody, cleared all five cutoffs as a PD-1 binder on `model_0`** — the argmax of five draws and the grader's default; on the **median** it fails (ipSAE 0.219 vs 0.609). Points 1 and 2 use different estimators, deliberately stated: a pass rate is a property of the estimator.
   *(⚠️ **113-mer only** — see [C6](CORRECTIONS.md). On the repaired 119-residue antigen HyHEL-10's best of five is **0.409** and it clears nothing; that panel's own positive control failed on the 113-mer, and it was pre-registered INCONCLUSIVE. What survives on both constructs: four of five gates reject 0 of 6.)*
3. Five of eight metrics are constants; the harness ranks on three; one of those is blind to the epitope.
4. Median [DockQ](03-the-toolchain.md#41-dockq-213--two-flags-that-both-default-wrong) on genuinely novel antibody–antigen pairs: **0.291**, against **0.818** on the memorised reference.
5. A mutation that abolishes binding experimentally (ΔΔG **+21.8 kcal/mol**) scores [ipSAE](03-the-toolchain.md#43-ipsae--interface-confidence-from-the-pae) **0.917** against the wild type's **0.903**.

---

## Provenance and known defects

This course was assembled on 2026-09-23 from the project's own record — at the time
62 results files, 23 session documents and 14 knowledge notes; today 73, 25 and 13 — `config/metrics.yaml`, `PLAN.md`,
`STATE.md`, and the source. Every figure is cited to a file so you can check it.

Three findings in [the critique](09-critique.md) contradict statements in the
project's own files and were produced while writing this course:

- `config/metrics.yaml`'s claim that the band→score choice *"moves the headline
  number and never the ranking"* is **false as stated** — the relabelling is
  monotone but not affine, and there are 39 strict ordering reversals on the band
  grid.
- ~~`STATE.md` … is **stale on a headline number** — it reports Challenge 2 at 96.0
  where the shipped design scores 91.2.~~ **Resolved 2026-09-26, and this bullet had
  itself gone stale:** `STATE.md` and the package both now read **93.6**, and the design
  is `bb_8_0`, not the one named here. Kept struck through because a defect list that
  quietly drops its own entries is worth less than one that shows them closing.
- The open `0.629` [reliability](04-measurement-theory.md#13-reliability) question resolves as an estimand mismatch, but a
  **real [Spearman–Brown](04-measurement-theory.md#3-spearmanbrown-what-averaging-buys) inconsistency survives underneath it**.

Other live defects inherited from the record and flagged in
[Chapter 08](08-what-broke.md): `PROJECT-STORY.md` — the designated entry point —
still carries three refuted or superseded claims; `results/calibration.md` ships
an empty results table beside power language it has three observations for.

Where the project's own documents disagree with each other, this course follows
the shipped submission package and says so.

---

## Related reading in this project

[The project story](../../PROJECT-STORY.md) (stale in places — see above) ·
[Current state](../../STATE.md) · [The knowledge notes](../../knowledge/README.md) ·
[Session logs](../sessions/README.md) · [The delivery plan](../../PLAN.md)
