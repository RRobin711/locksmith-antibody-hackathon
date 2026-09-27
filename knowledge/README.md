---
date: 2026-09-15
tags: [project, index, locksmith-bio, resource, learning]
status: living
---

Tags: [[index|indexes and MOCs]] · [[Locksmith Bio|Locksmith Bio]] · [[Resource|resources]] · [[Learning|things I'm learning]]

# Knowledge notes

Teaching notes for the [Locksmith antibody design project](../PROJECT-STORY.md). Written for a
reader with no background in structural biology — every term is defined on first use, and every
note leads with *why it matters* before *how it works*.

Start with [the project story](../PROJECT-STORY.md) for the narrative arc.

## The science — read in this order if you're new

| Note | Covers |
|---|---|
| [PD-1 and Checkpoint Blockade](PD-1%20and%20Checkpoint%20Blockade.md) | T cells, the off-switch tumours exploit, what Keytruda does, and the 58% coverage figure that gives us a real target |
| [Antibody Architecture](Antibody%20Architecture.md) | Heavy and light chains, Fv vs Fab, the six CDR loops, why CDR-H3 dominates, and what "novelty" means |
| [De Novo Design and the Two Challenges](De%20Novo%20Design%20and%20the%20Two%20Challenges.md) | Fixed-backbone redesign vs designing from scratch, and why Challenge 2 may not work |
| [How Structure Prediction Works](How%20Structure%20Prediction%20Works.md) | Folding models, MSAs and co-evolution, pLDDT and PAE, and why antibody chains want no alignment |
| [The Eight Metrics](The%20Eight%20Metrics.md) | Plain-language definition of each measurement, what "good" looks like, and what they collectively miss |

## Method — why we built it this way

| Note | Covers |
|---|---|
| [Build the Judge Before the Contestant](Build%20the%20Judge%20Before%20the%20Contestant.md) | Validating the scoring against known answers first, and the failed test that was right |
| [Confidence Is Not Truth](Confidence%20Is%20Not%20Truth.md) | Goodhart's law, the winner's curse, and the four kinds of evidence a confidence score can't produce |
| [Screening on Fv, Confirming on Fab](Screening%20on%20Fv%20Confirming%20on%20Fab.md) | The cheap-screen protocol and the hidden assumption that would fail invisibly |

## Lessons — what went wrong

| Note | Covers |
|---|---|
| [Eight Silent Failures](Eight%20Silent%20Failures.md) | Eight traps that each produced a confident wrong answer without raising an exception |
| [The Environment Saga](The%20Environment%20Saga.md) | The dependency fault line, the four-attempt fold, the swap detour, and two mistakes of my own |

## Context — Locksmith's own science

| Note | Covers |
|---|---|
| [Intrinsically Disordered Proteins](Intrinsically%20Disordered%20Proteins.md) | Anfinsen's dogma and its limit; why ensemble-averaging is a category error |
| [Nanopore Sensing of Disordered Proteins](Nanopore%20Sensing%20of%20Disordered%20Proteins.md) | Single-molecule measurement, and a de novo protein design paper pointed at sensors |
| *Locksmith Bio — Company Context* (kept private, not published) | A private assessment of the organising company and the people running the event. It names identifiable individuals and a private channel, so it is deliberately excluded from this repository. |

## Still to write

From the competition handbook's own reference list, not yet started: the structural basis of
PD-1 recognition (Tan 2017, Na 2017); how ProteinMPNN and RFdiffusion actually work (Dauparas
2022, Watson 2023); the antibody developability guidelines (Raybould 2019, Jain 2017).

## Tag hubs used

These notes tag into hubs in `3- Tags/`. Existing hubs reused: `[[Learning]]`, `[[Idea]]`,
`[[Resource]]`, `[[index]]`, `[[Pattern]]`, `[[Problem]]`, `[[Coding]]`, `[[Python]]`,
`[[AI, ML]]`, `[[Job Search]]`.

**New hubs that need creating** (I can't write to `3- Tags/`): `[[Antibody]]`,
`[[Protein Design]]`, `[[Structure Prediction]]`, `[[Structural Biology]]`, `[[IDP]]`,
`[[Nanopore]]`, `[[Locksmith Bio]]`. Until they exist these render as unresolved links, which
is harmless.
