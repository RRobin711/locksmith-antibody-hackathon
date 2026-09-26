# The post-training-cutoff test — result

Analysis exactly as fixed in [the pre-registration](prereg_post_cutoff_test.md), which was written before target selection and before any fold. Targets and the novelty screen are in [the target record](postcutoff_targets.md). Five antibody–antigen complexes released 2024-09 to 2026-07, all ≥7 months clear of Boltz-2's **2023-06-01** release-date cutoff, each with a closest pre-cutoff CDR-H3 relative ≤44.4% identical.

**DockQ here is genuine prediction accuracy** — each target scored against its own released crystal, same molecule, known answer the model has not seen. That differs from the variant panel, where mutants were scored against the 5GGS crystal and DockQ measured retention of the native binding mode.

## 1. The numbers

| target | released | antigen | CDR-H3 novelty | Fv DockQ | Fv ipSAE | Fab DockQ | Fab ipSAE |
|---|---|---|---|---|---|---|---|
| 9JBQ | 2024-09-11 | PcrV (P. aeruginosa) | 21.4% | 0.074 | 0.000 | 0.061 | 0.128 |
| 9BQW | 2025-08-06 | DbpA (Borrelia) | 28.6% | 0.053 | 0.000 | 0.064 | 0.707 |
| 8TBB | 2024-08-28 | TIM-3 (human) | 31.2% | 0.852 | 0.674 | 0.676 | 0.579 |
| 9W43 | 2026-07-01 | PD-1 (human) | 38.5% | 0.070 | 0.722 | 0.157 | 0.104 |
| 8RWB | 2025-02-12 | ULBP6 (human) | 44.4% | 0.236 | 0.319 | 0.291 | 0.353 |
| *5GGS (memorised, reference)* | *2017* | *PD-1* | *—* | *0.820* | *0.841* | *0.818* | *0.807* |

## 2. Level — the Challenge 2 go/no-go

- **FAB**: DockQ 0.061, 0.064, 0.157, 0.291, 0.676 → median **0.157**, 1/5 ≥ 0.49 → **FAIL**
- **FV**: DockQ 0.053, 0.070, 0.074, 0.236, 0.852 → median **0.074**, 1/5 ≥ 0.49 → **FAIL**

Against 5GGS's 0.818 (Fab), the median novel target scores **0.157** — a drop of **0.661 DockQ**. Four of five fall below 0.23, the CAPRI 'acceptable' floor, meaning the binding mode is **not recovered at all**. The single success (8TBB, Fab 0.676 / Fv 0.852) shows the pipeline is capable — these are model failures, not harness failures.

## 3. Relationship — does the ipSAE calibration survive novel structures?

Residual against the panel curve for the same construct, in units of the panel's residual sd.

**FV curve** — `ipSAE = 0.421 + 0.527 × DockQ`, residual sd 0.043, n=14

| target | DockQ | ipSAE predicted | ipSAE observed | residual | in sd |
|---|---|---|---|---|---|
| 9JBQ | 0.074 | 0.460 | 0.000 | -0.460 | **-10.8** |
| 9BQW | 0.053 | 0.449 | 0.000 | -0.449 | **-10.5** |
| 8TBB | 0.852 | 0.870 | 0.674 | -0.196 | **-4.6** |
| 9W43 | 0.070 | 0.458 | 0.722 | +0.265 | **+6.2** |
| 8RWB | 0.236 | 0.545 | 0.319 | -0.226 | **-5.3** |

- mean residual **-0.213** (SE 0.022) → **-9.6 SE**
- but the residuals themselves have sd **0.294**, versus the panel's **0.043** — a **6.9×** inflation
- Spearman ipSAE vs DockQ on these five: **rho = +0.308**, p = 0.614 (panel: +0.815 Fv / +0.754 Fab)

**FAB curve** — `ipSAE = 0.364 + 0.566 × DockQ`, residual sd 0.088, n=14

| target | DockQ | ipSAE predicted | ipSAE observed | residual | in sd |
|---|---|---|---|---|---|
| 9JBQ | 0.061 | 0.399 | 0.128 | -0.271 | **-3.1** |
| 9BQW | 0.064 | 0.400 | 0.707 | +0.306 | **+3.5** |
| 8TBB | 0.676 | 0.747 | 0.579 | -0.167 | **-1.9** |
| 9W43 | 0.157 | 0.453 | 0.104 | -0.349 | **-4.0** |
| 8RWB | 0.291 | 0.529 | 0.353 | -0.175 | **-2.0** |

- mean residual **-0.131** (SE 0.046) → **-2.9 SE**
- but the residuals themselves have sd **0.256**, versus the panel's **0.088** — a **2.9×** inflation
- Spearman ipSAE vs DockQ on these five: **rho = +0.200**, p = 0.747 (panel: +0.815 Fv / +0.754 Fab)

## 4. The failure mode that matters most

The pre-registration asked whether ipSAE sits above or below the curve. Neither describes what happened: **the relationship collapses**, and it collapses in both directions at once.

| | ipSAE | DockQ | what it means |
|---|---|---|---|
| 9W43 Fv | **0.722** | **0.070** | confident, and completely wrong |
| 9BQW Fab | **0.707** | **0.064** | confident, and completely wrong |
| 8TBB Fv | 0.674 | **0.852** | the one correct prediction — and it scores *lower* than both failures |
| 9JBQ Fv | 0.000 | 0.074 | correctly unconfident |

**ipSAE ranks two catastrophically wrong predictions above the only correct one.** Both false positives clear the rubric's 0.60 ipSAE cutoff comfortably; one clears 0.70. A funnel keyed on ipSAE would have promoted both and discarded nothing.

## 5. Why ipSAE is fooled — the failures are not failures to dock

| prediction | Ab–Ag contacts <5 Å | min distance | DockQ |
|---|---|---|---|
| 9JBQ Fab | 428 | 1.6 Å | 0.061 |
| 9BQW Fab | 470 | 2.0 Å | 0.064 |
| 8TBB Fab | 629 | 1.7 Å | 0.676 |
| 9W43 Fab | 608 | 2.2 Å | 0.157 |
| 8RWB Fab | 544 | 1.8 Å | 0.291 |

**Every failed prediction builds a large, well-packed interface.** The model is not failing to dock; it is docking confidently to the **wrong epitope or the wrong orientation**. That is the mechanism behind the false positives: ipSAE scores the interface the model built, and a confidently-built wrong interface is indistinguishable, to ipSAE, from a confidently-built right one. Nothing in the PAE can see that the epitope is wrong, because the PAE is the model's opinion of its own output.

This also means the failure is **not** about antibody novelty per se:

- FV: Spearman(CDR-H3 novelty, DockQ) = **+0.300**, p = 0.624
- FAB: Spearman(CDR-H3 novelty, DockQ) = **+0.700**, p = 0.188

If anything the sign is positive — the *most* novel antibody (9JBQ, 21.4%) and the least (8RWB, 44.4%) both failed, and the one success sits in the middle. Antibody–antigen docking is simply hard once the answer is not in the training data.


---

# VALIDATION (2026-09-17, later) — the original run above was partly invalid

Three controls were run before building anything further on this result. **Two passed.
A fourth check, not in the brief, failed — and it invalidated most of the run.**
Everything above this line is superseded by the corrected numbers below.

## Control 1 — reference integrity: **PASS**

Interface measured directly in each crystal, between the chains assigned antibody and antigen:

| target | Ab–Ag contacts <5 Å | min distance | H–L contacts |
|---|---|---|---|
| 9JBQ | 440 | 2.6 Å | 960 |
| 9BQW | 334 | 2.5 Å | 853 |
| 8TBB | 514 | 2.4 Å | 987 |
| 9W43 | 458 | 2.3 Å | 928 |
| 8RWB | 669 | 2.5 Å | 1038 |

Every reference has a large genuine interface. No crossed pairing, no reference whose
assigned chains barely touch. ANARCII's role assignment was correct in all five
(V domains scored 30.2–31.0, every antigen 0.0). **The 5GGS crossed-pairing failure mode
did not recur.**

## Control 1b — sequence integrity: **FAIL on 4 of 5.** This is the real problem.

`io.pdb.chains()` builds sequences from the residues present in the **coordinates**.
Residues unresolved in the crystal are silently absent and the flanking residues are
concatenated. **The folded sequence was therefore a chimera** — a protein with internal
loops deleted and the ends fused — not the molecule the crystal contains.

Internal gaps, from author residue numbering (terminal truncation is harmless; internal
deletion is not):

| target | chain | internal gaps | residues lost |
|---|---|---|---|
| 9JBQ | heavy | 134→143, 197→200 | 10 (CH1, outside the Fv) |
| 9BQW | heavy | 135→142 | 6 (CH1) |
| **9BQW** | **antigen** | **53→73** | **19 — across the epitope face** |
| 8TBB | heavy | 138→143 | 4 (CH1) |
| 9W43 | heavy | 133→140 | 6 (CH1) |
| **9W43** | **antigen** | **57→65, 70→75, 83→95 …** | **32 — across the epitope face** |
| 8RWB | — | none | 0 |

The failure is invisible without this check: a spliced sequence is a valid protein
sequence, folds without error, and yields a confident structure.

**All five targets were re-prepared from SEQRES and re-folded** (`scripts/13`–`16`,
`runs/postcutoff_v2/`). Original numbers are superseded, not repaired.

## Control 2 — antigen fold quality: **PASS**

Each antigen folded alone (correct SEQRES sequence) against its crystal chain:

| target | CA RMSD | mean pLDDT | antigen MSA depth |
|---|---|---|---|
| 9JBQ | 0.68 Å | 96.0 | 255 |
| 9BQW | 0.76 Å | 91.3 | **99** |
| 8TBB | 0.77 Å | 90.9 | 4416 |
| 9W43 | 0.60 Å | 91.6 | 3997 |
| 8RWB | 1.59 Å | 90.0 | 2533 |

Every antigen folds essentially perfectly on its own. **The failure is genuinely in
placement, not in antigen structure.** Two alignments are thin (9BQW 99 sequences,
9JBQ 255) and are recorded, but neither prevented an accurate monomer.

## Control 3 — seed stability: **PASS**

9W43 Fab, the worst remaining target, on three seeds: DockQ **0.054, 0.051, 0.056**
(sd 0.003). The failure is completely stable; it is not one bad draw.

## Corrected results

| target | Fab DockQ old → new | Fv DockQ old → new |
|---|---|---|
| 9JBQ | 0.061 → **0.071** | 0.074 → 0.063 |
| 9BQW | 0.064 → **0.370** | 0.053 → **0.469** |
| 8TBB | 0.676 → **0.696** | 0.852 → 0.713 |
| 9W43 | 0.157 → **0.054** | 0.070 → 0.049 |
| 8RWB | 0.291 → **0.291** | 0.236 → 0.236 |

9BQW moved **+0.306** once its antigen was intact — its apparent catastrophic failure was
substantially our bug. 9W43 moved down and its failure is real and seed-stable.

### Level: **FAIL → MARGINAL**

- **Fab**: 0.054, 0.071, 0.291, 0.370, 0.696 → median **0.291**, 1/5 ≥ 0.49 → **MARGINAL**
- **Fv**: 0.049, 0.063, 0.236, 0.469, 0.713 → median **0.236**, 1/5 ≥ 0.49 → **MARGINAL**

Still far below the memorised 5GGS (Fab 0.818) and still only one target clearing the
plan's 0.49 bar. But 2/5 now fail completely rather than 4/5, and the pre-registered
verdict is **MARGINAL, not FAIL**.

### Relationship: the "collapse" was mostly our bug — **claim withdrawn**

| | original (invalid) | corrected |
|---|---|---|
| Spearman ipSAE↔DockQ, Fv | +0.308 (p=0.61) | **+0.900 (p=0.037)** |
| Spearman ipSAE↔DockQ, Fab | +0.200 (p=0.75) | **+0.900 (p=0.037)** |
| residual sd vs panel, Fv | 6.9× | **2.7×** |
| residual sd vs panel, Fab | 2.9× | **1.3×** |

The rank relationship on novel complexes is **as strong as on the panel** (+0.900 vs
+0.815/+0.754). What survives is a **level shift**: ipSAE sits systematically *below* the
panel curve — mean residual −0.283 (−12.7 SE) Fv, −0.188 (−4.1 SE) Fab.

**That is the opposite direction from what was originally concluded.** On novel structures
ipSAE is **conservative**, not optimistic.

### The false positives were artifacts

| | original | corrected |
|---|---|---|
| 9W43 Fv | ipSAE **0.722** @ DockQ 0.070 | ipSAE **0.109** @ DockQ 0.049 |
| 9BQW Fab | ipSAE **0.707** @ DockQ 0.064 | ipSAE **0.450** @ DockQ 0.370 |

Both "confident and completely wrong" points came from chimeric antigens. **Withdrawn.**
With correct inputs no prediction clears the 0.60 gate on a wrong structure.

### The wrong-epitope mechanism survives — with the opposite conclusion about ipSAE

| target | contacts <5 Å | DockQ | ipSAE |
|---|---|---|---|
| 9JBQ | 417 | 0.071 | **0.085** |
| 9W43 | 600 | 0.054 | **0.115** |

The genuine failures still build large, well-packed interfaces at the wrong epitope. But
**ipSAE correctly reports low confidence on them.** The structural observation stands; the
inference drawn from it — that a self-assessed confidence metric cannot detect this — does
not, and is withdrawn.

## What this means for M4

The original suspension of M4 rested on median 0.157 with inverted confidence. The
corrected evidence is weaker: median **0.291**, confidence ranking **intact and
conservative**. That is still below the project's bar and still a large drop from the
memorised complex, so Challenge 2 remains **high-risk** — but **suspension is no longer
supported by this result alone**, and the PLAN entry has been revised accordingly.
