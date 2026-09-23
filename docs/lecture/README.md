---
date: 2026-09-23
tags: [project, lecture, course, protein-design, antibody, measurement, learning, index]
status: living
---

# Designing a cancer drug on a laptop — a complete course

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
| 00 | [[00-orientation\|Orientation]] | The four questions answered directly: what we had to do, what we needed to know, what we used, what we made |
| 01 | [[01-the-biological-problem\|The biological problem]] | T cells, PD-1, checkpoint blockade, antibody architecture, epitopes, developability chemistry, and what the scores do not say |
| 02 | [[02-the-engineering-problem\|The engineering problem]] | The pipeline, the rubric as data, build-the-judge-first, and programs that exit 0 having done the wrong thing |
| 03 | [[03-the-toolchain\|The toolchain]] | Every tool with versions and gotchas, the dependency fault line, the Blackwell GPU saga, and what it all cost |
| 04 | [[04-measurement-theory\|Measurement theory]] | Reliability, ICC, Spearman–Brown, attenuation, range restriction — how good is my measurement? |
| 05 | [[05-experiment-design\|Experiment design]] | Power, nulls, null geometry, controls, pre-registration — what would have to be true for me to be wrong? |
| 06 | [[06-allocation-and-selection\|Allocation and selection]] | Depth versus breadth, the winner's curse, banding, order statistics — where should the next measurement go? |
| 07 | [[07-the-campaign\|The campaign]] | The nine days as narrative, with the fold ledger and the parameters inherited unexamined |
| 08 | [[08-what-broke\|What broke]] | The full failure catalogue: silent failures, withdrawn claims, blind controls, wasted hours |
| 09 | [[09-critique\|The critique]] | The adversarial re-evaluation — what was excellent, what was mis-sequenced, and three findings that contradict the project's own record |
| 10 | [[10-glossary\|Glossary]] | Every term, acronym and metric defined |
| 11 | [[11-study-plan\|Study plan]] | Reading orders, prerequisite curriculum, self-tests, exercises, and a checklist |

---

## Where to start

- **Just want the answers?** [[00-orientation|Chapter 00]] alone, about twenty minutes.
- **Want the story?** [[07-the-campaign|Chapter 07]], then follow its links.
- **Don't care about antibodies?** Chapters [[04-measurement-theory|04]],
  [[05-experiment-design|05]] and [[06-allocation-and-selection|06]] are
  field-independent and are where the compounding knowledge lives. This is the
  recommendation for most readers.
- **Going to build something like this?** [[02-the-engineering-problem|Chapter 02]]
  with `config/metrics.yaml` open beside it, then
  [[08-what-broke|Chapter 08]], then the Track C exercises in
  [[11-study-plan|Chapter 11]].
- **Want to know what went wrong?** [[09-critique|Chapter 09]].

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
| Challenge 1 | `mpnn_T0.5_s104_036` + N55Q | **96.0** | CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to pembrolizumab |
| Challenge 2 | `bb_2_0_dldesign_1` + S→A | **91.2** | 1 of 30; ships 4.8 points low on purpose, to strip two glycosylation sequons from the paratope |

**18,020 lines of Python** (of which roughly 53% exists to check the other half),
30 tests, 1,274 predicted structures, 11 pre-registrations, 3 adversarial audits,
and 165,333 words of documentation.

And five results that matter more than either score:

1. Four of five hard cutoffs reject **0 of 6** known-wrong antibodies.
2. **HyHEL-10, an anti-lysozyme antibody, cleared all five cutoffs as a PD-1 binder.**
3. Five of eight metrics are constants; the harness ranks on three; one of those is blind to the epitope.
4. Median DockQ on genuinely novel antibody–antigen pairs: **0.291**, against **0.818** on the memorised reference.
5. A mutation that abolishes binding experimentally (ΔΔG **+21.8 kcal/mol**) scores ipSAE **0.917** against the wild type's **0.903**.

---

## Provenance and known defects

This course was assembled on 2026-09-23 from the project's own record: 62 results
files, 23 session documents, 14 knowledge notes, `config/metrics.yaml`, `PLAN.md`,
`STATE.md`, and the source. Every figure is cited to a file so you can check it.

Three findings in [[09-critique|the critique]] contradict statements in the
project's own files and were produced while writing this course:

- `config/metrics.yaml`'s claim that the band→score choice *"moves the headline
  number and never the ranking"* is **false as stated** — the relabelling is
  monotone but not affine, and there are 39 strict ordering reversals on the band
  grid.
- `STATE.md`, which declares itself the single source of truth, is **stale on a
  headline number** — it reports Challenge 2 at 96.0 where the shipped design
  scores 91.2.
- The open `0.629` reliability question resolves as an estimand mismatch, but a
  **real Spearman–Brown inconsistency survives underneath it**.

Other live defects inherited from the record and flagged in
[[08-what-broke|Chapter 08]]: `PROJECT-STORY.md` — the designated entry point —
still carries three refuted or superseded claims; `results/calibration.md` ships
an empty results table beside power language it has three observations for.

Where the project's own documents disagree with each other, this course follows
the shipped submission package and says so.

---

## Related reading in this project

[[../../PROJECT-STORY|The project story]] (stale in places — see above) ·
[[../../STATE|Current state]] · [[../../knowledge/README|The knowledge notes]] ·
[[../sessions/README|Session logs]] · [[../../PLAN|The delivery plan]]
