# Calibration against ground truth — 2026-09-15

Produced by `scripts/02_calibrate.py`. All four subjects are **experimental**
structures, so ipSAE and interface pLDDT are undefined (no PAE; the B-factor
column holds thermal displacement, not pLDDT). NetSolP is not yet installed.

Conventions in force: `cdr_sasa_state=bound`, `ipsae 10/15`, IMGT, interface 5.0 Å.

| subject | ΔG kcal/mol | contacts | CDR SASA bound | unbound | buried | DockQ vs ABZ | CDR-H3 id |
|---|---|---|---|---|---|---|---|
| **5GGS A/B/Z** (pembrolizumab, reference) | **−14.3** | 102 | 1563.6 | 2460.2 | 896.6 | 1.000 | 100% |
| **5GGS C/D/Y** (2nd copy, same crystal) | −13.9 | 103 | 1567.2 | 2428.4 | 861.3 | **0.867** | 100% |
| **5WT9** (nivolumab) | −10.0 | 73 | 1433.3 | 2036.2 | 602.9 | — | 30.8% |
| **DECOY** (Fab + non-binding PD-1 copy) | — (no contacts) | **0** | 2460.2 | 2460.2 | 0.0 | 0.002 | 100% |

## The numbers that matter downstream

**PRODIGY predicts Kd = 34 pM for pembrolizumab; the measured value is 29 pM.**
**Do not read this as accuracy.** PRODIGY is a linear regression on contact counts and
non-interacting-surface composition, with reported RMSE ~1.5–2 kcal/mol. Since ~1.4
kcal/mol is a *tenfold* change in Kd, a 0.1 kcal/mol agreement sits well inside its
noise — this is a coincidence, not precision.

What it does validate is **plumbing**: the tool ran on the correct interface with the
correct chain selection. Treat ΔG as **ordinal** — good for ranking and for the ≤ −6
gate, not for quoting absolute affinity. Note too that PRODIGY's ΔG is essentially a
function of its own contact count, so ΔG and contacts are **not independent evidence**
despite occupying two of six binding slots.

**DockQ 0.867 is an interpretive scale, not a ceiling.** Two copies of the *same
molecule* in the *same crystal* score 0.867 against each other. That measures how much
genuinely identical molecules differ when independently refined under different packing,
so it sets the scale **below which** "different pose" and "same pose, different packing"
cannot be told apart. It does **not** cap what a prediction can score — a prediction
reproducing copy 1's particular conformation can legitimately exceed it.

**ΔG crystallographic spread = 0.40 kcal/mol** (−14.3 vs −13.9 for the same
complex). A real error bar for that metric.

**An approved drug scores only *medium* on ΔG.** Nivolumab lands at −10.0, the
medium band (−10 to −12). The rubric's bands are demanding: clinical success is
not sufficient for full marks.

## Two conventions resolved empirically

**CDR SASA bound-vs-unbound is MOOT.** Bound 1564 Å², unbound 2460 Å² — both are
far above the 600 Å² "good" threshold and the 250 Å² cutoff. The ambiguity that
looked dangerous has no practical effect on viability or banding. One of the five
unresolved conventions can be set aside.

**Contacts is nearly a free metric.** 102 for pembrolizumab, 73 for nivolumab,
against bands of ">25 good" and "≥10 required". Any genuine antibody–antigen
interface clears it comfortably.

## What the decoy teaches

The decoy is pembrolizumab's Fab paired with the PD-1 copy it does *not* bind. It
is correctly rejected — contacts 0, ΔG undefined, DockQ 0.002.

But note its **CDR SASA is 2460 Å², squarely in the "good" band**. Nothing is
buried, so the paratope is maximally exposed, and the metric rewards that. **CDR
SASA alone cannot detect a non-interface.** This is the concrete case for why the
rubric uses a set of metrics and why the minimum, not the mean, is what matters.
