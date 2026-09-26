---
date: 2026-09-15
tags: [project, pattern, protein-design, learning]
status: living
---

Tags: [[Pattern|patterns worth reusing]] · [[Protein Design|protein design]] · [[Learning|things I'm learning]]

# Build the Judge Before the Contestant

**Why this note exists:** the single decision that shaped the project. Before designing a
single molecule, we rebuilt the scoring system and tested it on answers we already knew.

---

## 1. The reasoning

We are going to generate thousands of candidate antibodies and pick the best one. That means
[the scoring function](The%20Eight%20Metrics.md) decides everything — which designs survive, which
get discarded, what we eventually claim.

So: **what happens if the scoring is subtly wrong?**

Nothing visible. Every design gets a number. The numbers are plausible. We pick the highest
one. The pipeline runs to completion and reports success — and the answer is garbage, with no
error message anywhere.

That is not a hypothetical worry. It is the default outcome when a measurement is wrong, and
it is far more dangerous than a crash, because a crash tells you.

**Hence the rule: the judge gets validated before the contestant exists.** If the scoring
harness can't reproduce answers we already know, nothing downstream is worth computing.

## 2. The four test subjects

We ran our harness on four structures chosen so that *we know in advance what it should say*:

| Subject | What it is | What must happen |
|---|---|---|
| **5GGS A/B/Z** | Pembrolizumab bound to PD-1 — a real, approved drug | Must pass every binding gate |
| **5GGS C/D/Y** | A second copy of the same complex in the same crystal | Should agree closely with the first |
| **5WT9** | Nivolumab bound to PD-1 — a *different* real drug | Should also look like a genuine binder |
| **DECOY** | Pembrolizumab paired with the PD-1 copy it does **not** touch | Must be **rejected** |

The decoy is the important one and the one most often skipped. Showing that your measurement
gives good scores to good things is only half a validation. You also have to show it gives bad
scores to bad things — otherwise you have not demonstrated that it *discriminates*, only that
it is generous.

## 3. What it found

**It passed** — and the numbers it produced became reference points we now use constantly:

- Pembrolizumab's real interface: ΔG −14.3 kcal/mol, 102 contacts, CDR SASA 1564 Å²
- The two crystal copies agree to within **0.40 kcal/mol** on ΔG — that is the metric's real
  error bar, measured rather than assumed
- Two copies of the same molecule score **DockQ 0.867** against each other, establishing what
  "indistinguishable poses" looks like
- The decoy was correctly rejected: zero contacts, undefined binding energy, DockQ 0.002

And one genuinely useful surprise: **nivolumab — an approved drug — scores only *medium* on
ΔG** (−10.0). The competition's bands are demanding. Clinical success is not full marks.

## 4. The moment the test failed, and why that was the best part

The first run reported:

```
[FAIL] native pembrolizumab passes every computable gate — failing: cdrh3_identity
```

My instinct was to go looking for a bug.

There wasn't one. Pembrolizumab's CDR-H3 is 100% identical to pembrolizumab's CDR-H3, because
it *is* pembrolizumab. The [novelty gate](The%20Eight%20Metrics.md) exists specifically to reject
trivial clones. **The reference molecule must fail it.** The harness was right; my expectation
was wrong.

The fix was to rewrite the assertion: pembrolizumab must pass every *binding* gate **and must
fail novelty**. That is a strictly stronger test than the original, because it now asserts the
novelty metric actually *discriminates* rather than merely runs.

**The principle:** when a calibration fails, the first hypothesis should be that your
expectation encodes something wrong — not that the measurement is broken. Check the
expectation before you change the code. If I had "fixed" the harness to make the test pass, I
would have broken the one metric that stops us submitting a copy.

## 5. What it could not test, and why we said so

Three of the eight metrics never ran in calibration:

- **ipSAE** and **interface pLDDT** are undefined on experimental structures — a crystal has no
  confidence matrix, because nobody was guessing. They got their first real exercise later, on
  a predicted structure.
- **NetSolP** was not installed.

So the harness reported viability as **unknown**, not **true**.

That is deliberate three-valued logic. The tempting implementation returns "viable" when
nothing *measured* failed — which is exactly the bug. If an unmeasured metric would have
failed, you would have labelled a dead design alive. `None` propagates the uncertainty instead
of swallowing it, and forces the gap to be closed before anything gets locked in.

## 6. Where this generalises

This is not a biology idea. It is the same move as:

- writing the test before the feature
- checking your instrument against a known standard before measuring the unknown
- back-testing a trading strategy on a period where you know what happened
- validating a metric on labelled data before trusting it on unlabelled data

The common structure: **whenever a measurement will be used to make selections you cannot
otherwise check, validate the measurement against known answers first — including negative
controls.** The cost is a day. The cost of skipping it is discovering at the end that every
decision was made on a broken number.

---

**Related:** [why passing the metrics still isn't proof](Confidence%20Is%20Not%20Truth.md) ·
[the traps this discipline caught](Eight%20Silent%20Failures.md)
