---
date: 2026-09-15
tags: [project, structure-prediction, protein-design, AI, learning]
status: living
---

Tags: [[Structure Prediction|structure prediction]] · [[Protein Design|protein design]] · [[AI, ML|AI and ML]] · [[Learning|things I'm learning]]

# How Structure Prediction Works

**Why this note exists:** we have no laboratory. The only way to ask "would this antibody
work?" is to predict its 3D structure computationally and measure the prediction. So the
folding model is not background infrastructure — it *is* the experiment, and its limitations
are our limitations.

---

## 1. The problem being solved

A protein is made as a linear chain of amino acids, and then it folds into a specific
three-dimensional shape. The shape determines what it does. Predicting the shape from the
sequence was an unsolved problem for fifty years.

**AlphaFold** largely solved it in 2020 for single proteins. Predicting how two proteins fit
*together* — the **complex** prediction problem — is harder and still only partly solved. That
harder problem is ours: we need to know not just what our antibody looks like, but how it sits
against PD-1.

## 2. MSAs — and why our antibody chains don't want one

An **MSA** is a *Multiple Sequence Alignment*. You take your protein's sequence, search a huge
database for related sequences from other organisms, and stack them up so equivalent positions
line up in columns.

This is enormously informative, and the reason is **co-evolution**. If two positions in a
protein touch each other in 3D, then a mutation at one tends to be compensated by a mutation
at the other — otherwise the protein breaks. Over evolutionary time, touching pairs of
positions vary *together*. So a column-pair that co-varies across hundreds of species is
evidence those two residues are near each other in space. The MSA is, in effect, a fuzzy
contact map read out of evolutionary history.

**Now the antibody problem.** For a complex, you would like co-evolutionary signal *between*
the two partners. That works for proteins that have evolved together for millions of years.

But **a drug and its target have not co-evolved.** There is no evolutionary record of
pembrolizumab binding PD-1 — pembrolizumab was made in a lab a few years ago. A paired
antibody–antigen alignment therefore contains no signal about the interface. It is noise.

This is not a minor optimisation. It explains why antibody-specific predictors like IgFold and
ABodyBuilder2 work from single sequences, and it is why we give our antibody chains **no MSA at
all** and build one only for PD-1.

**And it was also the fix for a crash.** Our first successful fold came after three failures,
the last of which was the GPU running out of memory. MSA data is one of the largest things a
folding model holds — memory scales with alignment depth × sequence length — and we were
building deep alignments for all three chains, including the two that shouldn't have had any.
Removing them was simultaneously the scientifically correct choice and a two-thirds cut in
memory. See [the environment note](The%20Environment%20Saga.md).

*When the right thing and the cheap thing coincide, it usually means the right thing was right
for a structural reason.*

## 3. Boltz-2, and why not AlphaFold

We use **Boltz-2**, an open model in the AlphaFold-3 family. Two reasons:

- **It runs.** Our GPU is an RTX 5070 Ti, which uses NVIDIA's new *Blackwell* architecture.
  Software has to be compiled for it specifically. Boltz is built on PyTorch, which supports
  Blackwell; AlphaFold's usual distribution is built on JAX, which was an unknown. Getting
  *one* working predictor mattered more than getting the canonical one.
- **It is a diffusion model**, which means different random seeds produce genuinely different
  structures rather than just different confidence numbers. That is useful to us: it gives an
  ensemble for free. More on why that matters below.

AlphaFold remains valuable as an *independent second opinion* — see
[the validation note](Confidence%20Is%20Not%20Truth.md).

## 4. pLDDT and PAE — the model's two confidence outputs

A prediction comes with the model's own assessment of how much to trust it. Two measures,
answering different questions.

**pLDDT** — *predicted Local Distance Difference Test*. A score from 0 to 100 for **each
residue**, answering: *how sure am I about this bit, locally?* Above 90 is very confident;
below 50 usually means the region is disordered or the model has no idea.

**PAE** — *Predicted Aligned Error*. A matrix with one number for **every pair of residues**,
in ångströms (Å — a tenth of a nanometre, roughly the width of an atom). PAE[i][j] answers:
*if I line up my prediction with the truth at residue i, how far off would residue j be?*

The distinction matters enormously for complexes. pLDDT can be high everywhere — both proteins
individually well-modelled — while the model has no idea how they fit together. That shows up
in the **inter-chain block** of the PAE matrix: the numbers describing residue pairs where one
is in each protein. Low inter-chain PAE means the model is confident about the docking. That
block is the raw material for [ipSAE](The%20Eight%20Metrics.md), the interface-confidence metric.

## 5. A trap: pLDDT and B-factors live in the same place

Structure files (PDB format) have a column historically called the **B-factor**. In an
experimentally determined structure it holds the *atomic displacement parameter* — how much
the atom jiggles or is smeared out in the crystal, in Å². Typical values 10–80.

AlphaFold and Boltz write **pLDDT** into that same column. Also roughly 0–100.

**There is no way to tell them apart by looking at the numbers.** And it is worse than a units
mismatch, because the meanings run in opposite directions:

> **Low B-factor = well-ordered = good.  Low pLDDT = uncertain = bad.**

So reading a beautifully resolved crystal structure as if its B-factors were pLDDT would
report the best possible input as maximally unconfident. We handle this by tracking
*provenance* in the type system: a structure is tagged as experimental or predicted, and
confidence metrics simply refuse to run on experimental ones. Full story in
[the traps note](Eight%20Silent%20Failures.md).

## 6. Confidence is not correctness

This deserves its own note and has one — [Confidence Is Not Truth](Confidence%20Is%20Not%20Truth.md) —
but the short version belongs here too.

Every confidence number a folding model emits describes **the model's opinion of its own
output**. None of them touch reality. They cannot: for a molecule that has never been made,
there is no truth to compare against.

So a confidently wrong answer scores well. And since these numbers are cheap to compute and
smooth in sequence space, they can be *optimised against* — you can hill-climb them, finding
sequences the model happens to feel good about, which is not the same as sequences that bind.

This is the central methodological hazard of the whole project.

## 7. What we actually measured

We gave Boltz-2 nothing but the sequences of pembrolizumab and PD-1 — no template, no antibody
MSA — and asked it to predict the complex.

| | Result |
|---|---|
| Wall clock | **34 seconds** (343 residues) |
| Pose accuracy vs the real crystal structure (DockQ) | **0.820** |
| Interface confidence (ipSAE) | 0.841 |
| Interface pLDDT | 94.4 |

For scale: two independently solved copies of the *same* complex in the *same* crystal score
0.867 against each other. **Our prediction recovers the pose about as well as a second copy of
the real structure does.** Interface atoms sit roughly 1 Å from their crystallographic
positions.

### ⚠ The caveat, stated plainly

**5GGS was published in 2017 and is almost certainly in Boltz-2's training data.** This is
partly retrieval, not clean prediction.

It establishes that our pipeline works end to end. It does **not** establish that Boltz can
place a never-before-seen antibody onto PD-1 — exactly what Challenge 2 requires. The honest
test is a post-training-cutoff complex, and **we have not run it.** Until then, Challenge 2
confidence is discounted and independent evidence carries more weight.

## 8. Calibration points worth remembering

- **A correct pose scored ipSAE 0.841.** The competition's "good" band starts at 0.80 — so a
  genuinely correct antibody–antigen interface sits only *just* inside it. An ipSAE much above
  0.85 on a designed molecule deserves suspicion rather than celebration.
- **Boltz's own confidence summary reported 0.948 for the same structure where ipSAE read
  0.841.** Different scales measuring related things. They are not interchangeable, and the
  competition's thresholds were calibrated on AlphaFold's, not Boltz's.
- **The heavy/light interface was the worst-scoring part of the model** — exactly the
  under-constrained elbow predicted in [the Fv/Fab note](Screening%20on%20Fv%20Confirming%20on%20Fab.md).

---

**Next:** [what we actually measure, and what good looks like](The%20Eight%20Metrics.md).
