# The PD-L1 competitive footprint on PD-1 — 2026-09-15

Produced by `src/locksmith/design/epitope.py`. Serves Challenge 2 hotspot conditioning
and epitope-overlap validation for both challenges.

## The footprint (Challenge 2 design target)

**26 PD-1 residues contact PD-L1** in 5IUS (5 Å heavy-atom), chain A vs chains C/D:

```
H64 V66 H68 E70 S73 G74 Q75 T76 D77 T78 L79 A80 A81 D85 P89 G90 Q91
C123 G124 I126 L128 I132 I134 K135 E136 R139
```

Two spatial clusters — roughly 64–91 (the C'D loop region) and 123–139 — consistent with
PD-L1 engaging one face of the PD-1 IgV β-sandwich.

## A caveat that had to be handled, not assumed

**5IUS and 5GGS do not carry the same PD-1 sequence.** Aligned identity is **90.1%** over
111 residues — roughly eleven differences. Residue numbers are therefore *not* directly
transferable between the two entries, and the footprint is mapped across by explicit
sequence alignment. All 26 residues transfer cleanly.

Worth stating plainly: the footprint is measured on **5IUS's PD-1 construct**, which is not
byte-identical to the PD-1 we are designing against. The interface region is the same and the
mapping is unambiguous, but if 5IUS uses an engineered or stabilised PD-1 variant then its
PD-L1 binding mode may differ subtly from wild-type. Adequate for hotspot conditioning;
flagged rather than buried.

## Pembrolizumab's epitope, and what the overlap means

**27 PD-1 residues** are contacted by pembrolizumab in 5GGS:

```
S60 S62 F63 V64 N66 Y68 Q75 T76 D77 K78 A81 F82 P83 E84 D85 R86 S87 Q88 P89 G90
I126 L128 A129 K131 A132 Q133 I134
```

**Overlap with the PD-L1 site: 15 shared residues.**

| | |
|---|---|
| Fraction of the PD-L1 site covered by pembrolizumab | **58%** |
| Fraction of pembrolizumab's epitope lying on the PD-L1 site | **56%** |

This *quantifies the drug's mechanism*. Pembrolizumab does not bury the PD-L1 site entirely —
it covers a little over half of it, which is sufficient for competitive blockade. Roughly half
of its own paratope contacts lie outside the PD-L1 footprint, on adjacent surface.

## Why this is the most useful number in the project so far

It converts a binary question into a calibrated one. "Does the design overlap the PD-L1 site?"
is weak — a single shared residue would pass. **"Does the design achieve PD-L1-site coverage
comparable to a drug that works in patients?"** has a concrete target: **~58%**.

That gives Challenge 2 a validation criterion grounded in clinical reality rather than in the
rubric, which never asks whether the molecule would block anything. A design can score
perfectly on ipSAE, ΔG and contacts while binding the wrong face of PD-1 entirely.
