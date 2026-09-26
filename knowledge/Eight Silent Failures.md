---
date: 2026-09-15
tags: [project, pattern, problem, learning]
status: living
---

Tags: [[Pattern|patterns worth reusing]] · [[Problem|problems and debugging]] · [[Learning|things I'm learning]]

# Nine Silent Failures

*(The filename still says eight. It was eight when written; the ninth arrived on
2026-09-26, and renaming the file would break ten inbound links for no gain.)*

**Why this note exists:** these are the most valuable things we found. Not one of them raised an
exception on its own. Every one would have produced a confident, well-formed, *wrong* number and
let the pipeline run happily to completion.

The unifying lesson is at the bottom, but it is worth stating up front:

> **A tool that refuses to produce output is the good failure. The dangerous ones hand you a
> number anyway.**

---

## 1. Crystal B-factors masquerading as confidence scores

**What:** structure files have a column historically called the **B-factor**. In an
experimental structure it holds the *atomic displacement parameter* — how much an atom jiggles
or is smeared in the crystal, in Å², typically 10–80. Folding models write **pLDDT** (their
per-residue confidence, 0–100) into that same column.

**Why it's dangerous:** you cannot tell them apart by looking at the values. And the meanings
run **opposite**:

> **Low B-factor = well-ordered = good.  Low pLDDT = uncertain = bad.**

A beautifully resolved crystal structure with B-factors around 15 would read as *pLDDT 15* —
catastrophically unconfident. The best possible input scores worst. That is sign inversion, not
a units error.

**How caught:** anticipated rather than suffered, while designing the type system.

**Fix:** structures carry **provenance** — tagged experimental or predicted. Confidence metrics
refuse to run on experimental ones and report *undefined*, not zero. Returning 0 would be a
false claim; returning the B-factor would be a lie.

**Generalises to:** any field that two different producers populate with different meanings.
Track where data came from, not just what it looks like.

---

## 2. A tool numbering the target as if it were an antibody

**What:** ANARCII, which identifies antibody domains and labels their loops, confidently
numbered **PD-1** — the target — as an antibody chain and assigned it CDRs.

**Why it happened:** this is not a bug. PD-1 belongs to the **immunoglobulin superfamily**; it
has an **IgV fold**, the same β-sandwich architecture as an antibody variable domain, by shared
evolutionary ancestry. A tool trained to recognise V domains recognises it because, by fold, it
*is* one.

**Why it's dangerous:** any step that auto-detects "which chain is the antibody" would have
assigned PD-1 a CDR-H3 and then computed novelty, CDR SASA and interface identity **on the
target molecule**. Every number finite, well-formed, and about the wrong thing.

**How caught:** printing the numbering output for every chain rather than only the ones we
expected to be antibodies. Genuine V domains scored ~31 on the tool's confidence measure; PD-1
scored ~16. Clean separation — visible only because we looked.

**Fix:** a minimum-confidence threshold of 25, documented in code with the measured values, plus
explicit chain assignment instead of auto-detection.

**Generalises to:** **a classifier that returns a confident answer on out-of-distribution input
is the most dangerous failure mode there is**, because the output is well-formed. Always check
the score distribution of your known *negatives*, not just that your positives pass.

---

## 3. Crossed chain pairing in the reference structure

**What:** the reference crystal (5GGS) contains **two copies** of the complex. The natural
reading of the chain labels is that antibody chains A/B go with target Y, and C/D with Z. Both
are wrong: **A/B binds Z, and C/D binds Y.**

**Why it's dangerous:** our extracted "complex" had **zero** contact between antibody and
target. Every interface metric would have been computed across an interface that does not exist.

**How caught:** PRODIGY refused with `No contacts found for selection` — a real error — and our
own contact analysis confirmed zero contacting residues.

**Fix:** determine pairing by **measuring contacts**, never by reading labels. Extraction now
takes explicit chain arguments and returns the mapping it applied, because once written the
mapping is not recoverable from the output file.

**A second trap inside the first:** the largest non-antibody contact in that crystal is between
the two *light chains* — 64 residues, **larger than either real epitope**. It is crystal
packing, an artefact of how molecules stack in the crystal, not biology. A heuristic like "take
the biggest interface that isn't heavy–light" would have selected a lattice artefact as the
binding site.

**Generalises to:** labels are a claim; measurements are evidence. Where a file's structure
encodes a relationship, verify the relationship physically.

---

## 4. A tool silently choosing its own interface

**What:** PRODIGY computes binding energy for an interface. Run on a three-chain file **without
telling it which chains to compare**, it returned a confident **−16.3 kcal/mol** — for the
*heavy–light* interface inside the antibody, not the antibody–target interface.

**Why it's dangerous:** −16.3 kcal/mol is entirely plausible for an antibody–antigen interface.
Nothing about the number looks wrong. We only knew because we were simultaneously investigating
trap #3 and the explicit selection was failing while the implicit one succeeded.

**Fix:** selection is **always** explicit — `--selection A,B C` — and the code refuses to call
the tool without it.

**Generalises to:** when a tool has to choose something you care about and you didn't specify
it, it chose. Find out what.

---

## 5. DockQ's zero-mismatch default

**What:** DockQ compares your structure's pose to a reference. It defaults to
`--allowed_mismatches 0`, and **any** sequence difference makes it refuse to score:

```
ERROR: For chains ['A'] no identical corresponding chain was found
```

**Why it's dangerous:** every Challenge 1 design *is* pembrolizumab with mutated loops. At the
default, DockQ would have refused to score **every design the pipeline produces** — returning
nothing, propagating to "viability unknown", producing an empty shortlist with no error
anywhere. We would have gone hunting for a bug in the design code.

Worse: four substitutions is enough to trigger it, and four substitutions is the *minimum* to
reach the top novelty band. It would have failed on the first design actually worth having.

**Why the default exists:** it is correct for DockQ's intended use — validating a prediction of
a *known* complex, where a sequence mismatch really does mean you have paired the wrong chains.
Ours is the adjacent use case it was never written for.

**How caught:** a deliberate stress test. We mutated residue *names* while leaving every
coordinate byte-identical, so the pose was unchanged by construction and any score below 1.000
had to be pure alignment failure.

**The result was the opposite of the prediction.** I expected insertions and deletions to be the
hard case and substitutions to be trivial:

```
sub4  (4 substitutions)   FAILED — no score at all
sub8  (8 substitutions)   FAILED
del2  (2 residues removed) 1.000
ins2  (2 residues added)   1.000
reorder (chains shuffled)  1.000
```

Indels pass because they do not create mismatches *at aligned positions* — the aligner simply
skips them. Only substitutions trip the check.

**Fix:** `--allowed_mismatches 40` (a full heavy-chain redesign spans 29 positions) and
`--mapping ABC:ABC` to pin the chain correspondence, because a free search could silently map
chains wrongly and score a good design badly.

**Generalises to:** **a tool's defaults encode its author's assumed use case, not yours.** When
you are using something for the adjacent problem, read the defaults.

---

## 6. A folding model exiting 0 after failing

**What:** Boltz hit a fatal error inside its prediction loop, printed a traceback, produced no
structure — and **exited with status 0**. Twice, for two different reasons: once a missing CUDA
module, once a GPU out-of-memory. The second even displayed a cheerful `100%|██████████`
progress bar and `Number of failed examples: 1`.

**Why it's dangerous:** our batch design assumed exit status could drive resumability — skip
what's done, retry what failed. A job that reports success while producing nothing would be
marked complete and skipped forever, leaving silent holes in a campaign that only surface much
later as *"why do I have 200 designs and 40 scores?"*

**How caught:** checking for the output files rather than trusting the return code.

**Fix:** a hard invariant — **a fold counts as successful only when the expected structure and
confidence files both exist and parse.** Never when the process merely returned.

**Generalises to:** the same lesson as a previous project's mislabelled telemetry, one level
nastier. There, a subprocess died and the parent carried on. Here the subprocess actively
*claims* it succeeded. **Assert on the artefact, not the exit code.**

---

## 7. ipSAE writing an empty file without complaining

**What:** the ipSAE script locates its confidence data by string-substituting the filename —
`pae_file_path.replace("pae", "plddt")`. We copied the prediction files to a working directory
and renamed them. The sibling file was no longer findable, so ipSAE wrote a **zero-byte results
table** and exited without error.

**How caught:** our parser crashed trying to read a header from an empty file — a lucky crash,
because the failure itself was silent. Had the parser been more forgiving, we would have got a
missing value with no explanation.

**Fix:** the metric now checks for the sibling file explicitly and returns a descriptive skip,
and treats an empty table as an error with the tool's stderr attached.

**Generalises to:** implicit coupling between filenames is a real dependency. Renaming files is
not a cosmetic operation when a downstream tool parses paths.

---

## 8. A bug invisible on the first test file

**What:** a structure-loading call raised `RuntimeError: missing entity_type in chain A` because
two library calls were in the wrong order.

**Why it matters more than an ordinary bug:** it **worked** on the first file we tested (5GGS,
which happens to carry the metadata) and failed only on the second (5WT9, which does not). Had
we validated on one file and moved on, the bug would have shipped and surfaced later, on
different data, far from its cause.

**Generalises to:** **a pipeline step that works on your first test file has been tested once,
not validated.** Run it across the whole reference set before trusting it.

---

## 9. A sweep that read the working tree and was asked about the repository

**What:** before making the repository public, a pre-publication sweep grepped every tracked
file for third-party email addresses, credentials, cloud keys and the organisers' handbook.
It reported **CLEAN** on all four. Both the handbook — a 712 KB PDF — and three people's
email addresses were nonetheless still *in the repository*, reachable from 77 earlier
commits, and were pushed to the remote.

**Why it matters more than an ordinary miss:** both removals had been made as ordinary
commits — `git rm --cached` for the handbook, a text edit for the emails. That changes what
`HEAD` contains and **nothing about what the repository contains**. `git grep`, `find`, and
any script that opens files all read the *working tree*; none of them can observe a blob
that is reachable only from an old commit. So the sweep returned a true answer to a narrower
question than the one being asked, and said nothing about the difference — which is this
project's signature defect, in a new syntax.

It also had a deadline the other traps did not. The repository was private and had never
been public, so the fix was a history rewrite and a force-push. After public exposure it
would have been unfixable: GitHub retains unreachable objects, and forks and caches index
quickly.

**Generalises to:** **removing a file from a repository and removing it from a
repository's history are two different operations, and every tool that greps files reports
the first as though it were the second.** For anything that must not ship, verify over
history rather than over the checkout:

```bash
git log --all --diff-filter=A --name-only -- '<path>'   # was it ever added?
git log -p --all | grep -c '<secret>'                   # is it in any diff?
```

And do it at the moment you are already rewriting history, because the second rewrite costs
a second force-push. A related trap sits one step further on: `refs/original/*` and any
backup branch left by an earlier rewrite still hold the unscrubbed commits, so they must be
deleted and the objects expired — and such a repository must never be pushed with `--mirror`
or `--all`.

---

## The unifying lesson

Sort these by how they announced themselves:

**Announced loudly** — #3 (tool refused), #5 (explicit error message), #8 (exception).
**Announced by luck** — #7 (our parser happened to be strict).
**Did not announce at all** — #1, #2, #4, #6, #9. Each would have handed us a plausible number.

**#9 is the worst of the set**, because the others merely produce a wrong number: a wrong
number can be recomputed. #9 publishes someone else's data irreversibly, and it does so
while a check is actively reporting that everything is clean.

The dangerous failures are not the ones that crash. They are the ones that return something in
the right range, with the right units, computed on the wrong thing.

Which is why the [validate-against-known-answers](Build%20the%20Judge%20Before%20the%20Contestant.md)
discipline is not fussiness. Three of these were caught *only* because we were running the
harness on structures whose answers we already knew. On novel designs there would have been
nothing to notice.

---

**Related:** [the infrastructure failures](The%20Environment%20Saga.md) ·
[why we validated first](Build%20the%20Judge%20Before%20the%20Contestant.md) ·
[the conceptual version of the same problem](Confidence%20Is%20Not%20Truth.md)
