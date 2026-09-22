# Pre-registration — specificity controls on the named design

**Written 2026-09-20 ~01:55, before `runs/specificity/` exists.**
Fold script `scripts/37_specificity_fold.py`.

## 1. Question

`mpnn_T0.5_s104_036` scores ipSAE 0.856, ΔG −12.7 kcal/mol, 97 contacts and interface
pLDDT 90.0 against PD-1. None of that is evidence of **specificity**. A sticky,
well-packed surface produces the same numbers against whatever it is docked to, and
this project has already measured Boltz building large, confident, wrongly-placed
interfaces (post-cutoff median DockQ 0.291, with ipSAE 0.72 on a DockQ-0.07 structure
before the input fix, +0.900 rank correlation after it).

## 2. Panel, and why each member is there

| antigen | source | role | length |
|---|---|---|---|
| PD-1 | 5GGS antigen, cached MSA | **positive control**, fresh seeds 31–33 | 113 aa |
| PD-L1 IgV | 5IUS chain C, truncated at the IgV/IgC boundary | **functional decoy** — the ligand we exist to block; binding it is a mechanism failure | ~112 aa |
| TIM-3 | 8TBB antigen, cached MSA | **hardest decoy** — human checkpoint receptor, same Ig V-set fold | 110 aa |
| ULBP6 | 8RWB antigen, cached MSA | human, MHC-I-like fold | ~180 aa |
| PcrV | 9JBQ antigen, cached MSA | bacterial, unrelated — the floor | ~230 aa |

PD-L1 is truncated to its IgV domain for **size parity** with PD-1: the full 214-aa
ectodomain would confound interface size with antigen identity. This is a terminal
truncation, which `seq_for_folding()` permits; an internal deletion would be refused.

3 seeds (31, 32, 33) per antigen, used nowhere in M3 selection (1–7) or validation (23).

## 3. Hypotheses and thresholds, fixed now

- **H1.** ipSAE against every decoy is below the rubric's viability cutoff of **0.60**.
- **H2.** ipSAE against PD-1 at fresh seeds is ≥ **0.80** (the Good band), i.e. the
  positive control reproduces.
- **H3 (the discriminating one).** The PD-1 − decoy gap exceeds **0.20 ipSAE**, which is
  ~10× the shortlist's single-seed ipSAE sd of ~0.02 and comfortably larger than the
  0.13 residual Boltz-vs-AF2 scale offset measured at G1d.

**Pre-declared failure condition:** any decoy scoring ipSAE ≥ 0.60 **and** ΔG ≤ −10
kcal/mol on 2 of 3 seeds is a specificity failure, and the design does not go into a
pitch as a PD-1 binder without that sentence attached. TIM-3 and PD-L1 count double —
one is the nearest structural relative, the other is the molecule the drug must
outcompete.

Metrics reported per fold: ipSAE, ΔG, contacts, interface pLDDT, CDR SASA. **DockQ is
not computed for decoys** — there is no reference complex, and a DockQ against 5GGS
would be a category error.

## 4. The asymmetry, which must travel with the result

A decoy scoring **high** is strong evidence of a problem. A decoy scoring **low** is
weak evidence of its absence, because a predictor that is unreliable at novel placement
will score novel pairings low whether or not they would bind in reality. The
post-cutoff test measured exactly that unreliability on this predictor. So the
honest summary of an all-clean result is *"no evidence of promiscuity, from a test that
could only have detected gross promiscuity"* — not "the design is specific".

## 5. What would make this test stronger, and is not being done tonight

A **positive decoy control**: an antibody known to bind one of the decoys, folded the
same way, to show the pipeline *can* produce a high score against that antigen. Without
it, a uniformly low decoy panel is also consistent with "Boltz cannot dock anything to
TIM-3". 8TBB is a Fab–TIM-3 complex we already have, so this costs ~3 folds and is the
first thing to add if the panel comes back clean. Recorded here so it is a deferred
decision rather than an omission discovered later.
