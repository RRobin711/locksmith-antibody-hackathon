---
date: 2026-09-17
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# The sweep came back clean, and what to build next

**Session:** 2026-09-17, third. **Outcome:** the coordinate-sequence defect was confined to the
post-cutoff prep and is already fixed; **5GGS is clean and nothing needs re-running**. A guard
now makes the failure mechanical. Ends with a scoping recommendation.
**Prerequisite:** [the validation doc](2026-09-17-validating-the-inputs-and-withdrawing-a-result.md), which found the defect.

---

## 1. The sweep

Full table in [the sweep results](../../results/coordinate_sequence_sweep.md). The headline is
that **5GGS has zero internal deletions** in either crystal copy — every coordinate/SEQRES
difference is terminal truncation, and the coordinate sequence is a contiguous substring of
SEQRES for all six chains.

That is the answer that mattered. 5GGS underwrites the G1c/G1d panel, the 14-point
ipSAE↔DockQ curve, the seed-reliability measurements, the pembrolizumab positive control and
every novelty number. **All of it stands.**

Of the nine coordinate-to-sequence sites in the project, exactly one was ever affected — the
post-cutoff prep — and it was fixed last session.

### 1.1 The distinction that made the sweep tractable

Splicing is fatal only when a sequence is **folded**, because the predictor then builds a
protein that does not exist. Where only **coordinates** are consumed — DockQ, SASA, PRODIGY,
interface pLDDT, the 5IUS contact analysis — a missing residue is missing *data*, not a
chimera. Sorting the sites by that question reduced nine to four worth checking closely.

Two near-misses worth recording because both looked alarming before being resolved:

**5WT9 does have internal gaps** (6 residues at 127→134 in the heavy chain, 9 at 84→94 in
PD-1) and it does feed one sequence-derived number, its CDR-H3 identity of 30.8%. But ANARCII
puts its V domain at residues 0–112, so **the gap is in CH1, after the domain the number comes
from.** `ATNDDY` is intact. Unaffected — but only checkable by locating the gap, not by
counting residues.

**5IUS**, which supplies the epitope footprint, has a 2-residue hole at 87–88. Checked
directly: **all 26 footprint residues are present.** The honest caveat is that 87–88 sit
immediately before P89/G90/Q91, so whether they too contact PD-L1 is unobservable here — the
footprint is complete as far as the crystal can say, which is not quite the same as complete.

### 1.2 A methodological trap inside the sweep itself

My first pass reported 154- and 181-residue internal gaps in 5IUS and 5DK3. Both were
artefacts: I computed numbering gaps from a raw `gemmi.read_structure`, which retains ligands
and waters numbered in the 500s, so every het group registered as a hole. The project's own
`io.pdb.read()` strips them first and gives the true answer (2 and 0).

**The check that verifies a check needs verifying too.** Had I not cross-read this against the
contiguous-substring test — which disagreed — I would have reported the epitope footprint as
badly corrupted and triggered a re-run that was not needed.

---

## 2. The guard

`src/locksmith/io/pdb.py`:

- `ChainInfo` gains `internal_gaps`, plus `spliced` and `n_missing_internally`.
- `chains()` emits a `SplicedSequenceWarning` naming the chain, the count lost and the gap
  positions, and states that the string is fine for coordinate metrics and must never be folded.
- **`seq_for_folding(path, chain)` raises `SplicedSequenceError`** on an internal deletion.
  Terminal truncation passes. This is the call to use wherever a sequence reaches a predictor.

It works from **author residue numbering**, so it needs no network call and no SEQRES fetch —
which is what lets it sit in the hot path. Terminal truncation is invisible to numbering and
therefore passes for free, which is the correct semantics rather than a special case.

Tested against the known positive and negative, as with the existing hooks:

| control | expected | observed |
|---|---|---|
| 5GGS | silent, all foldable | 0 warnings, A/B/C allowed |
| 9W43 (32-residue antigen deletion) | warn + refuse | 2 warnings; A and C refused, clean B allowed |
| 8RWB (clean) | passes | nothing flagged |

Wired into `04_prepare_fold_inputs.py`, `05_make_variants.py` and `06_fold_panel.py`. All read
5GGS and pass today; the guard exists so a future reference swap cannot reintroduce the failure
silently. `05_make_variants.py` reproduces the panel byte-identically through the guarded path.

**Why a guard rather than a note.** This is the third failure in this project whose signature
was "the tool ran fine and the number was wrong" — after `boltz predict` exiting 0 on fatal
errors and ipsae writing an empty table on a renamed file. The pattern is consistent enough to
be a design rule: *when a failure produces a plausible number rather than an exception, the
check belongs in code at the point of derivation.*

---

## 3. What to build next — recommendation

**I agree M2 is the gap, and the sweep removes the condition attached to that.** 5GGS is clean,
so re-running the panel does not compete. `src/locksmith/{select,submit,validate}/` still
contain only `__init__.py`; `designs/` holds hand-mutated variants and no designs; there are no
baselines. Three sessions have characterised instruments without building anything that uses
them, and M3–M6 all sit behind M2.

Two refinements to the sequencing, and one agreement.

### 3.1 Re-specify M2's selection step before writing it — this is the one thing I'd change

The funnel in PLAN §5.2 was designed around an ipSAE-led screen. Two measurements since have
undercut that:

- **G1c**: the Fv screen is dead (reliability 0.607 vs Fab 0.965; multi-seed Fv costs more than
  the Fab it was meant to save).
- **Panel §8**: among *live* designs ipSAE barely ranks at all — Fab R² **0.755 → 0.263** once
  the two dead poly-Gly anchors are removed, slope flattening threefold.

So writing `select/` against ipSAE would build a chooser around a metric measured not to
discriminate in the regime it will operate in. The fix is cheap and is a decision, not a
milestone: **separate the selection metric from the reported metric.** The handbook scores
ipSAE and we must report it; nothing obliges us to *rank* on it. For Challenge 1 every design
has DockQ against the 5GGS crystal — the closest thing to ground truth in the project, and the
quantity ipSAE was supposed to be a proxy for. Rank on that; treat ipSAE as a **liveness gate**
(≥0.60) rather than a score.

An hour of specification that prevents rewriting `select/` after the first campaign.

### 3.2 Within M2, do Baseline 1 before the bespoke generator

PLAN lists the hand-mutated design, then Baseline 0 (pembrolizumab, already measured), then
Baseline 1 (plain ProteinMPNN, ~20 designs). I would start with **Baseline 1**, because it is
simultaneously the control *and* the first real exercise of the design path — it forces
ProteinMPNN installation, the design→fold→score plumbing and the parquet schema into existence,
and it yields the referent without which "our funnel scored 84" means nothing. Building a
bespoke generator first gets the plumbing without the control.

It also answers the open ipSAE-level-shift question for free: Challenge 1 designs are
perturbations of a memorised complex, so scoring them with both DockQ and ipSAE shows directly
whether they sit on the panel curve or below it like the novel targets did.

### 3.3 Agreed: hold the second predictor. And hold fold batching too

**Second predictor — agree, defer.** The claim it was meant to defend has been withdrawn, so
it is now a feasibility question for the dossier rather than a pipeline component. I would add
one reason to defer harder: AF2 **cannot** run on designs at all without a local MSA database,
so "cross-predictor consensus" is not currently available as a selection input regardless of
how the question is answered. It enriches the dossier; it does not unblock anything.

**Fold batching — also defer, though it is tempting.** It is worth ~1.8× on every fold after it
(the budget is ~1,290 Fab folds per invocation against ~2,380 batched) and it is self-contained.
But the right batch shape depends on the funnel's actual pattern, which M2 defines. Front-running
it means guessing the interface and probably rewriting it.

### 3.4 What I do *not* think is more urgent

The **ipSAE level shift** on novel structures (~0.19–0.28 below the panel curve, n=5) is real
and unquantified, and it is tempting to chase because it is the most scientifically interesting
loose end. It should not outrank M2: it affects gate *thresholds*, which are config and can be
re-applied to stored scores without re-folding anything — that separation is exactly what
`config/metrics.yaml` was built for. It gets partially answered as a by-product of §3.2 anyway.

**Summary of the recommendation:** M2 next; spend an hour first re-specifying selection to rank
on DockQ with ipSAE as a gate; start with Baseline 1 rather than the bespoke generator; hold
the second predictor and fold batching.

---

## 4. State

**Clean, and nothing re-run.** 5GGS verified by two independent tests; eight of nine
coordinate-to-sequence sites unaffected by construction; the ninth fixed last session.

**New mechanism.** `seq_for_folding()` / `SplicedSequenceWarning` in `io/pdb.py`, wired into
the three fold-prep scripts, tested on a known positive and negative.

**Unchanged.** M2 not started (this session was scoped not to). `select/`, `submit/`,
`validate/` empty. Fold batching outstanding. The ipSAE level shift unquantified.
