---
date: 2026-09-17
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# Validating the inputs, and withdrawing a result

**Session:** 2026-09-17, later. **Outcome:** the post-cutoff result was **partly invalid**.
Its headline verdict moves **FAIL → MARGINAL**, and two of its three conclusions are
**withdrawn**. The cause was ours, not the model's.
**Prerequisite:** [the post-cutoff session doc](2026-09-17-the-memorisation-test-and-what-it-cost-challenge-2.md), which this corrects.

---

## 1. Why controls were run at all

The post-cutoff result had been used to suspend M4 and was about to justify a
multi-predictor campaign. Before spending that, the question was whether the observed
signature — a large, well-packed interface scoring near-zero DockQ — was the model's
failure or ours. **That signature is exactly what a bad reference, a wrong chain
assignment, or a corrupted antigen also produces.**

The defence on offer was 8TBB at DockQ 0.676 through the identical path, which argues
against a *global* pipeline bug. It says nothing about a *per-target* prep error. That
distinction is the whole reason the controls were per-target, and it turned out to be the
right distinction.

---

## 2. What passed

**Control 1 — reference integrity.** Every crystal reference has a large genuine
antibody–antigen interface: 334–669 heavy-atom contacts under 5 Å, minimum distances
2.3–2.6 Å, normal H–L packing. ANARCII's chain-role assignment was correct in all five
(true V domains 30.2–31.0, every antigen 0.0). The 5GGS crossed-pairing failure did not
recur.

**Control 2 — antigen fold quality.** Each antigen folded alone reproduces its crystal
chain at **CA RMSD 0.60–1.59 Å, mean pLDDT 90.0–96.0.** The antigens are not the problem;
the failure is genuinely in *placement*. Two alignments are thin — 9BQW **99** sequences,
9JBQ **255**, against 2500–4400 for the others — recorded because it is the kind of thing
that matters later, but neither prevented an accurate monomer.

**Control 3 — seed stability.** 9W43 Fab on three seeds: DockQ **0.054, 0.051, 0.056**,
sd 0.003. Not one bad draw.

---

## 3. What failed — a check that was not in the brief

`io.pdb.chains()` builds a sequence from the residues present in the **coordinates**. Every
residue unresolved in the crystal is silently absent, and the flanking residues are
concatenated. **The sequence handed to Boltz was therefore a chimera: a protein with
internal loops deleted and the ends fused.**

Comparing coordinate-derived length against the SEQRES entity length, and locating the
gaps from author residue numbering:

| target | chain | internal gaps | lost | where |
|---|---|---|---|---|
| 9JBQ | heavy | 134→143, 197→200 | 10 | CH1, outside the Fv |
| 9BQW | heavy | 135→142 | 6 | CH1 |
| **9BQW** | **antigen** | **53→73** | **19** | **epitope face** |
| 8TBB | heavy | 138→143 | 4 | CH1 |
| 9W43 | heavy | 133→140 | 6 | CH1 |
| **9W43** | **antigen** | **57→65, 70→75, 83→95 …** | **32** | **epitope face** |
| 8RWB | — | none | 0 | — |

**Four of five targets were affected.** The distinction that matters is *internal deletion*
versus *terminal truncation*: a disordered Fab C-terminus is harmless, an excised loop is
not. The two worst-scoring targets in the original run were precisely the two with gutted
antigens.

**Why it was invisible.** A spliced sequence is a perfectly valid protein sequence. It
folds without error, produces a confident structure, and scores badly against the crystal —
which reads as a model failure. Nothing raises an exception. The artefact assertion in the
fold driver cannot catch this, because the artefact is fine; it is the *input* that is
wrong. **The driver checks that the tool did what it was told. Nothing was checking that it
was told the right thing.**

---

## 4. The corrected result

All five re-prepared from SEQRES and re-folded (`scripts/13`–`16`, `runs/postcutoff_v2/`).
Original numbers superseded, not repaired.

| target | Fab DockQ old → new | Fv DockQ old → new |
|---|---|---|
| 9JBQ | 0.061 → 0.071 | 0.074 → 0.063 |
| 9BQW | 0.064 → **0.370** | 0.053 → **0.469** |
| 8TBB | 0.676 → 0.696 | 0.852 → 0.713 |
| 9W43 | 0.157 → 0.054 | 0.070 → 0.049 |
| 8RWB | 0.291 → 0.291 | 0.236 → 0.236 |

**9BQW moved +0.306 once its antigen was intact.** Its "catastrophic failure" was
substantially our bug. 9W43 moved down, and its failure is real and seed-stable.

### 4.1 Level: FAIL → **MARGINAL**

Fab median **0.291** (was 0.157); Fv median **0.236** (was 0.074). Both land in the
pre-registered MARGINAL band [0.23, 0.49). Still only 1/5 clears the plan's 0.49 bar, and
still a long way below the memorised 5GGS at 0.818 — but 2/5 now fail completely rather
than 4/5.

### 4.2 The "calibration collapse" — **withdrawn**

| | original (invalid) | corrected |
|---|---|---|
| Spearman ipSAE↔DockQ, Fv | +0.308 (p=0.61) | **+0.900 (p=0.037)** |
| Spearman ipSAE↔DockQ, Fab | +0.200 (p=0.75) | **+0.900 (p=0.037)** |
| residual sd vs panel, Fv | 6.9× | 2.7× |
| residual sd vs panel, Fab | 2.9× | 1.3× |

The rank relationship on novel complexes is **at least as strong as on the panel**
(+0.900 against +0.815/+0.754). What survives is a **level shift**: ipSAE sits
systematically *below* the panel curve, mean residual −0.283 (−12.7 SE) Fv and −0.188
(−4.1 SE) Fab.

**That is the opposite direction from the original conclusion.** On novel structures ipSAE
is **conservative**, not optimistic.

### 4.3 The false positives — **withdrawn**

| | original | corrected |
|---|---|---|
| 9W43 Fv | ipSAE 0.722 @ DockQ 0.070 | ipSAE **0.109** @ DockQ 0.049 |
| 9BQW Fab | ipSAE 0.707 @ DockQ 0.064 | ipSAE **0.450** @ DockQ 0.370 |

Both "confident and completely wrong" points were chimeric-antigen artefacts. With correct
inputs **nothing clears the 0.60 gate on a wrong structure**, and the claim that ipSAE
"ranks catastrophic failures above the correct one" is gone.

### 4.4 The wrong-epitope mechanism — **stands, with the opposite inference**

| target | contacts <5 Å | DockQ | ipSAE |
|---|---|---|---|
| 9JBQ | 417 | 0.071 | **0.085** |
| 9W43 | 600 | 0.054 | **0.115** |

The genuine failures *do* still build large, well-packed interfaces at the wrong epitope —
that structural observation was never in doubt and survives. But **ipSAE correctly reports
low confidence on them.** The inference drawn from the observation — that a self-assessed
confidence metric cannot detect this — was built on the two artefact values and is
withdrawn. What can be said is narrower and duller: the model sometimes docks confidently
in geometric terms to the wrong place, and its confidence metric usually notices.

---

## 5. What I got wrong, and the general lesson

I built a three-part conclusion, suspended a milestone, and wrote a LEARNINGS entry, on
inputs I had never checked. The pipeline was verified carefully — artefact assertions,
a reproduction of a prior result to three decimal places, a successful target proving the
path works — and **all of that verification was downstream of the error**. A perfectly
executed pipeline on a corrupted input produces a confident, reproducible, wrong answer.

Two specific lessons:

**Verify inputs with the same rigour as outputs.** The fold driver asserts that Boltz
produced a parseable PDB and PAE. Nothing asserted that the sequence handed to it was the
protein it was supposed to be. The cheap check — coordinate-derived length against SEQRES
length, then residue-numbering gaps to separate internal deletion from terminal truncation
— takes seconds and would have caught this before 16 minutes of GPU time and a milestone
decision.

**"A large interface at near-zero DockQ" is as easily your prep as the model's error.**
That signature is ambiguous, and I treated it as diagnostic. The per-target controls
existed precisely because a single successful target does not clear the other four.

**The successful target was actively misleading.** 8TBB at 0.676 felt like proof the
pipeline was sound. It only proved the pipeline was sound *for 8TBB*, whose antigen happened
to be nearly complete (2 missing residues, none internal to the epitope).

---

## 6. Pushback on the control design

**Control 2 as specified would have been misread.** Folding the antigen alone was specified
to test whether a bad antigen explained a wrong epitope. Run on the *original* spliced
sequences it would have shown chimeras folding confidently — the control would have "passed"
on a sequence that was already wrong, because a chimera folds perfectly well as the chimera
it is. The control is only meaningful after the sequence is known to be correct, so the
sequence check has to come first. It was not in the brief.

**Control 1 was specified around chain assignment and biological assembly**, which is the
failure this project had seen before. That is availability bias in the control design, mine
as much as anyone's — we checked for the bug we had already met and missed the one we
hadn't. Both are "the reference is not what you think", but only one was on the list.

**A fourth failure mode, on the MSA policy, which the brief asked about.** The antigen MSA
is fetched once per target and cached for the second construct. That is correct and it is
what keeps the two constructs comparable. But depths vary by a factor of 45 across targets
(99 to 4416) with no floor and no warning, and a thin alignment on an unusual antigen is a
silent quality difference between targets. It did not bite here — every antigen folded well
— but there is no check that would have told us if it had.

---

## 7. Where this leaves things

**The post-cutoff test stands as MARGINAL**, with Controls 1–3 passed and the input defect
fixed at source. Challenge 2 is **high-risk, not excluded**; the M4 suspension is lifted and
PLAN revised.

**Corrected in place:** `results/postcutoff_result.md` (validation appended below the
original, which is marked superseded), the PLAN G1f row and M4 block, and the LEARNINGS
entry — which now records the SEQRES lesson instead of the withdrawn confidence-metric
claim.

**Still open and unchanged:** the ipSAE level shift on novel structures is real and worth
quantifying properly (n=5, and it is a level shift not a ranking failure). Fold batching.
M2 baselines and the funnel. `select/`, `submit/`, `validate/` remain empty.
