# Pre-registration — hotspot ablation on the named design

**Written 2026-09-20 ~01:55, before `runs/ablation/` exists.**
Fold script `scripts/38_ablation_fold.py`.

## 1. Question

Does the score actually report the interface? If ΔG, contacts and ipSAE survive the
removal of the residues that make the interface, then they are measuring "two chains
are adjacent", not binding.

## 2. Mutants, chosen from measured contacts before folding

Heavy-atom pairs within 5.0 Å of antigen chain C, counted per heavy-chain residue in
the winner's seed-1 structure. 0-based indices into the 219-aa heavy chain:

| mutant | index | residue | contacts | region | role |
|---|---|---|---|---|---|
| Y31A | 31 | TYR | 54 | CDR-H1 | hotspot (joint largest) |
| D100A | 100 | ASP | 54 | CDR-H3 | hotspot (joint largest) |
| R99A | 99 | ARG | 50 | CDR-H3 | hotspot |
| N57A | 57 | ASN | 39 | CDR-H2 | hotspot |
| D102A | 102 | ASP | 31 | CDR-H3 | hotspot |
| R97A | 97 | ARG | 30 | CDR-H3 | hotspot |
| **Y31A/R99A/D100A** | — | — | 158 | CDR-H1+H3 | triple — can the score be made to fall at all? |
| **L96A** | 96 | LEU | **0** | CDR-H3 | **negative control** |
| **Y106A** | 106 | TYR | **0** | CDR-H3 | **negative control** |

2 seeds each (41, 42) — enough to see whether a change exceeds seed noise, not enough
to rank mutants against each other. The comparison is mutant-vs-parent, and the parent
has 7 seeds plus a fresh one.

## 3. Why the controls are the experiment

An ablation without a negative control is uninterpretable. If every mutant degrades,
you cannot distinguish "the score tracks the interface" from "the score punishes any
mutation", and this project has already banked and then withdrawn three conclusions
that lacked exactly this kind of control. Both controls are alanine substitutions at
CDR-H3 positions with **zero** measured antigen contact, so they carry the same kind of
perturbation — same loop, same substitution, no interface.

Y106A doubles as a probe of the aromatic result (aromatic fraction predicted spread
+0.621 and DockQ −0.536 on 2026-09-18): it removes a **non-contacting** CDR-H3 aromatic,
which separates "aromatics act through the interface" from "aromatics act through loop
conformation". n=1 — hypothesis-generating only, and it will be labelled as such.

## 4. Thresholds, fixed now

Seed noise on the parent: DockQ sd **0.018**, surrogate sd **0.467**, ipSAE sd ~**0.02**.
A change counts as real at **3×** the relevant sd.

- **H1.** Hotspot singles degrade ΔG and contacts relative to parent; the triple
  degrades more than any single.
- **H2.** Both negative controls stay within 3 seed sd of the parent on every metric.
- **H3.** ipSAE degrades **less** than ΔG and contacts do, in relative terms — the
  prediction being that a self-assessed confidence metric is partly blind to interface
  destruction, consistent with it behaving as a liveness test rather than a ranking
  metric (Fab R² 0.755 → 0.263 once the dead poly-Gly anchors are dropped).

## 5. Pre-declared interpretations

| outcome | reading |
|---|---|
| hotspots fall, controls hold | The score reports the interface. The dossier claim is earned. |
| hotspots and controls both fall | The readout is mutation-sensitive, not interface-sensitive. **The ablation says nothing** and must be reported as uninformative rather than spun. |
| nothing falls, including the triple | The score is not measuring this interface at all. That is the most alarming outcome and the most valuable one — it would mean 158 removed heavy-atom contacts cost nothing, and the binding metrics are reporting proximity. |
| ipSAE holds while ΔG and contacts fall | Fourth instance of ipSAE behaving as a liveness test; strengthens an existing, already-documented claim. |

## 6. Known limits

Boltz **re-predicts** each mutant from scratch, so a mutant's structure is not the
parent's structure minus a side chain — the model is free to re-dock. This measures
"does the predicted complex degrade when the designed sequence loses its hotspots",
which is the right question for a scored pipeline but is **not** an in-silico ΔΔG and
must never be called one. Real alanine-scanning holds the backbone fixed.
