# Coordinate-derived sequence sweep — 2026-09-17

Following the input-validation failure in [the post-cutoff result](postcutoff_result.md), where
four of five targets were folded from sequences with unresolved loops spliced out. That fix
was applied to the post-cutoff targets only. This is the sweep of everywhere else.

**Result: clean. 5GGS is unaffected and nothing needs re-running.**

## The test

Two independent checks, because either alone can mislead:

1. **Contiguous-substring**: is the coordinate-derived sequence a contiguous substring of the
   SEQRES entity sequence? If yes, only termini are missing and the string is a real piece of
   the real protein.
2. **Author residue numbering**: internal gaps in the numbering. Terminal truncation leaves
   no gap; an excised loop does. This needs no network call and is what the guard uses.

A caution learned during the sweep: computing gaps from a **raw** `gemmi.read_structure` counts
ligands and waters (numbered in the 500s) as phantom gaps. Use the project's cleaned
`io.pdb.read()`, which strips them first. The first pass of this sweep reported 154- and
181-residue "internal gaps" in 5IUS and 5DK3 that were entirely this artefact.

## 5GGS — clean, checked first

It underwrites the G1c/G1d panel, the 14-point calibration curve, the pembrolizumab positive
control and every novelty calculation.

| file | chain | coords | SEQRES | internal gaps | contiguous substring? |
|---|---|---|---|---|---|
| 5GGS_ABZ | A heavy | 219 | 232 | **none** | yes |
| 5GGS_ABZ | B light | 217 | 218 | **none** | yes |
| 5GGS_ABZ | C PD-1 | 113 | 123 | **none** | yes |
| 5GGS_CDY | A heavy | 220 | 232 | **none** | yes |
| 5GGS_CDY | B light | 217 | 218 | **none** | yes |
| 5GGS_CDY | C PD-1 | 114 | 123 | **none** | yes |

Every difference is **terminal truncation** — disordered N/C termini, harmless. Zero internal
deletions in either copy.

**Consequence: nothing from the panel needs re-running.** The 14-point ipSAE↔DockQ curve, the
seed-reliability measurements, G1c's Fab-only decision, the pembrolizumab control and the
novelty baseline all stand as recorded.

## Every site that turns coordinates into a sequence

| site | what it does with the sequence | source | affected |
|---|---|---|---|
| `04_prepare_fold_inputs.py` | **folds** it (5GGS Fv + Fab) | 5GGS_ABZ | **no** — 5GGS clean |
| `05_make_variants.py` | **folds** it (variant panel base) | 5GGS_ABZ | **no** |
| `06_fold_panel.py` | **folds** it (Fv/Fab constructs) | 5GGS_ABZ | **no** |
| `09_prepare_postcutoff.py` | **folds** it | raw PDB entries | **YES — fixed** by `13_reprepare_postcutoff.py` |
| `02_calibrate.py:65,67` | CDR-H3 novelty + NetSolP | predictions, 5GGS, 5WT9 | **no** — see below |
| `02_calibrate.py:103` | CDR-H3 identity of the native | 5GGS | **no** |
| `design/epitope.py` | **coordinates only** (`NeighborSearch`) | 5IUS | **no** — see below |
| `metrics/{dockq,sasa,plddt,prodigy,interface}.py` | coordinates only | various | **no** |
| 5DK3, DECOY | fetched / coordinate-only | — | **no** |

**The distinction that governs the whole table:** splicing is fatal when a sequence is
**folded**, because the predictor builds a protein that does not exist. It is irrelevant when
only **coordinates** are used — DockQ, SASA, PRODIGY, interface pLDDT and contact analysis
describe the atoms that are there, and missing atoms are missing data rather than a chimera.

### 5WT9 — has internal gaps, but they do not reach anything used

Chain A (nivolumab heavy) loses 6 residues at 127→134 and chain C (PD-1) 9 at 84→94. 5WT9 is
never folded; it is a coordinate-scored independent reference. The one sequence-derived number
is its CDR-H3 identity (30.8%), and ANARCII puts its V domain at residues 0–112 — **the gap at
127 is in CH1, after the V domain.** CDR-H3 `ATNDDY` is intact and the 30.8% in
`calibration.md` is correct.

### 5IUS — the epitope footprint is complete

Chain A (PD-1) has a single 2-residue hole at **87–88**. The footprint is derived from
coordinates, so the only risk is under-reporting. Checked directly: **no footprint residue is
absent from the coordinates.** All 26 are present.

One honest caveat: residues 87–88 sit immediately before footprint residues P89/G90/Q91. They
are unresolved, so whether they also contact PD-L1 cannot be known from this structure. The
footprint may therefore be complete-as-observable but two residues short of complete-in-fact,
at one edge. This does not affect its use as hotspot conditioning.

## The guard

`src/locksmith/io/pdb.py`:

- `ChainInfo` gains `internal_gaps` and the properties `spliced` / `n_missing_internally`.
- `chains()` now emits a `SplicedSequenceWarning` naming the chain, the residue count lost and
  the gap positions, and says plainly that the string is safe for coordinate metrics and must
  never be folded.
- **`seq_for_folding(path, chain)` raises `SplicedSequenceError`** on an internal deletion and
  returns the sequence otherwise. This is the call to use anywhere the result reaches a
  predictor. Terminal truncation passes.

Wired into the three fold-prep sites (`04`, `05`, `06`). They read 5GGS and pass today; the
guard is there so a future reference swap cannot reintroduce the failure silently.

Tested as with the existing hooks:

| control | expected | observed |
|---|---|---|
| 5GGS (clean) | 0 warnings, all chains foldable | 0 warnings; A/B/C all allowed |
| 9W43 (32-residue antigen deletion) | warn + refuse | 2 warnings; A and C **refused**, clean B allowed |
| 9BQW / 9JBQ / 8TBB | caught | spliced chains flagged |
| 8RWB (clean) | passes | no chains flagged |

`05_make_variants.py` reproduces the 14-variant panel byte-identically through the guarded path
(WT CDR-H3 `ARRDYRFDMGFDY`), confirming the guard changed no behaviour on clean input.
