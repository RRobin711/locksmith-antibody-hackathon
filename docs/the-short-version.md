# The short version

*For someone with five minutes. Everything here is linked to its evidence; nothing in this
file is a number you have to take on trust.*

## What it is

An antibody-design pipeline built for the Locksmith hackathon: generate a candidate
antibody's 3-D shape (RFdiffusion), fill in its amino-acid sequence (ProteinMPNN), predict
the complex and score it (Boltz-2). Two challenges — redesign an existing drug, and design
one from scratch against PD-1.

Both are finished and packaged: **94.0** and **93.6** out of 100, each validated by
re-deriving every metric from the package's own files.

## What it actually is

The score stopped being the point about two weeks in. There is no deadline and it is not
being submitted. What the repository is now is **a worked example of measuring a design
pipeline honestly** — which means the most useful thing in it is the list of things it got
wrong and how each was caught.

That list is [`results/retractions.md`](../results/retractions.md): every claim the project
withdrew, with the recomputation that killed it. Twenty-odd entries. A few samples:

- **Two points came from a `printf`.** Challenge 1 scored 96.0 for nine days because the
  DockQ parser read a summary rounded to 3 decimal places. The true value is
  **0.7995794972281312** — 0.00042 below the band edge, so the honest score is 94.0.
- **Nine days of Challenge 2 results were measured on a silently degraded input.** Boltz
  compares an alignment's length to the input chain and, on mismatch, discards the
  alignment and folds single-sequence — announcing it only on stdout, which the harness
  threw away. Re-screening with a correct alignment nearly **inverted the ranking**: the
  design that clears had ranked 29th of 30; the packaged one fell from 1st.
- **A negative control that cut against us.** An anti-lysozyme antibody — the wrong
  antibody for this target entirely — clears all five hard cutoffs. That result is in the
  shipped submission, not buried.

## The two findings from the final audit (2026-10-03)

**A spending decision rested on a test with a 23% chance of seeing what it looked for.**
The campaign decided not to pay for more backbones because a test found no difference
between them (p = 0.152). That test was correctly implemented — it reproduces to three
decimal places — but it was far too blunt: a pool in which three of eighteen backbones
cleared *five times* more often than the rest would have been **missed three times in
five**. "We found no difference" meant "we could not have found one."

The general form, and the reason it matters everywhere: **a null result is only meaningful
as "no effect larger than x", where x is what you could actually have detected.** Most
reported nulls never state x.
→ [the power analysis](../results/heterogeneity_power.md)

**A blocker carried for eleven days did not exist.** The roadmap said one step needed a
rented GPU, because the library pins an old PyTorch with no forward-compatible GPU code.
Every clause of that argument is true and the conclusion is false, because *CPU* was never
in the comparison. It runs on a laptop CPU in one second. The project had already proved
this five days before writing down that it was impossible.

**A blocker inherited from a neighbouring task is not evidence; re-run the check per task.**
Cost of checking: one minute.
→ [register §B12](../results/retractions.md)

## What's verified versus what's taken on trust

**Verified here:** the package re-derives its own scores from its own files; 258/258
retrieved artefacts checksum-match; 44 invariant tests, most mutation-verified; and the
hotspot-conditioning claim survived a **decoy-patch control** — the one experiment that
could have falsified it. Pointed at a patch 165.9° away, 15 of 16 backbones followed it and
all 16 read exactly 0.000 on the real epitope.

**Taken on trust, and stated in the shipped documents rather than buried:** Boltz-2's
confidence as a proxy for binding. Six of the eight scored metrics come from files we
generated, so a confidently wrong pose scores exactly like a right one. **Nothing here is
wet-lab evidence**, and no claim in the package says otherwise.

## Where to go next

| | |
|---|---|
| Current state, everything verified and everything open | [`STATE.md`](../STATE.md) |
| Every withdrawn claim | [`results/retractions.md`](../results/retractions.md) |
| One line per working session | [`docs/sessions/README.md`](sessions/README.md) |
| The whole thing as a twelve-chapter course | [`docs/lecture/README.md`](lecture/README.md) |

**One warning, from the repo's own front matter:** this project's errors cluster in
sentences, not in code. Where a results file and a generated artefact disagree, the artefact
is right — it was recomputed, and the sentence was copied.
