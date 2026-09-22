---
date: 2026-09-15
tags: [project, index, locksmith-bio, resource, learning]
status: living
---

Tags: [[index|indexes and MOCs]] · [[Locksmith Bio|Locksmith Bio]] · [[Resource|resources]] · [[Learning|things I'm learning]]

# Knowledge notes

Teaching notes for the [[../PROJECT-STORY|Locksmith antibody design project]]. Written for a
reader with no background in structural biology — every term is defined on first use, and every
note leads with *why it matters* before *how it works*.

Start with [[../PROJECT-STORY|the project story]] for the narrative arc.

## The science — read in this order if you're new

| Note | Covers |
|---|---|
| [[PD-1 and Checkpoint Blockade\|PD-1 and Checkpoint Blockade]] | T cells, the off-switch tumours exploit, what Keytruda does, and the 58% coverage figure that gives us a real target |
| [[Antibody Architecture\|Antibody Architecture]] | Heavy and light chains, Fv vs Fab, the six CDR loops, why CDR-H3 dominates, and what "novelty" means |
| [[De Novo Design and the Two Challenges\|De Novo Design and the Two Challenges]] | Fixed-backbone redesign vs designing from scratch, and why Challenge 2 may not work |
| [[How Structure Prediction Works\|How Structure Prediction Works]] | Folding models, MSAs and co-evolution, pLDDT and PAE, and why antibody chains want no alignment |
| [[The Eight Metrics\|The Eight Metrics]] | Plain-language definition of each measurement, what "good" looks like, and what they collectively miss |

## Method — why we built it this way

| Note | Covers |
|---|---|
| [[Build the Judge Before the Contestant\|Build the Judge Before the Contestant]] | Validating the scoring against known answers first, and the failed test that was right |
| [[Confidence Is Not Truth\|Confidence Is Not Truth]] | Goodhart's law, the winner's curse, and the four kinds of evidence a confidence score can't produce |
| [[Screening on Fv Confirming on Fab\|Screening on Fv, Confirming on Fab]] | The cheap-screen protocol and the hidden assumption that would fail invisibly |

## Lessons — what went wrong

| Note | Covers |
|---|---|
| [[Eight Silent Failures\|Eight Silent Failures]] | Eight traps that each produced a confident wrong answer without raising an exception |
| [[The Environment Saga\|The Environment Saga]] | The dependency fault line, the four-attempt fold, the swap detour, and two mistakes of my own |

## Context — Locksmith's own science

| Note | Covers |
|---|---|
| [[Intrinsically Disordered Proteins\|Intrinsically Disordered Proteins]] | Anfinsen's dogma and its limit; why ensemble-averaging is a category error |
| [[Nanopore Sensing of Disordered Proteins\|Nanopore Sensing of Disordered Proteins]] | Single-molecule measurement, and a de novo protein design paper pointed at sensors |
| [[Locksmith Bio — Company Context\|Locksmith Bio — Company Context]] | What the company works on, where the name comes from, and how to pitch to them |

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
