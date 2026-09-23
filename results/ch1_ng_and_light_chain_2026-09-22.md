# Challenge 1: the deamidation fix is free, and the light-chain plan is refuted

**2026-09-22.** Two experiments, both cheap, both changing what we tell a reader to do next.

---

## 1. The CDR-H2 deamidation motif — both fixes work, and one is free

`metrics/liabilities.py` found that Challenge 1 also fails §9.2: an `NG` deamidation
motif at heavy **55–56**, inside CDR-H2. It is pembrolizumab's own motif, but **both
positions were inside the 29 IMGT positions we made designable**, so leaving it was a
choice we did not know we were making.

Contacts to PD-1 first, as on Challenge 2: **N55 → 3, G56 → 0.**

| | mutation | §9.2 | ipSAE (5 diffusion samples) | DockQ | model_0 final | viable |
|---|---|---|---|---|---|---|
| baseline (submitted) | — | **FAIL** | 0.822–0.861 (sd-span 0.039) | 0.711–0.820 | **96.0** | 5/5 |
| **N55Q — SUBMITTED** | remove the acceptor | **PASS** | **0.791–0.836 (0.044)** | 0.682–0.815 | **96.0** | **5/5** |
| G56A | remove the fast +1 partner | PASS | 0.779–0.868 (0.089) | 0.695–0.820 | 94.0 | 5/5 |

**Both fixes are essentially free here**, which is the opposite of Challenge 2 — and the
contact table predicted both outcomes:

| | mutated residue's antigen contacts | result |
|---|---|---|
| Challenge 2 `N→Q` | **10 and 19** | ipSAE 0.864 → **0.014**, dead |
| Challenge 1 `N55Q` | **3** | 0.822 → 0.821, unchanged |

> **This is the same principle measured twice, in opposite directions.** `N→Q` is not
> inherently dangerous and `S→A` is not inherently safe. What predicts the outcome is
> **how much of the interface the mutated residue is carrying** — and that is a one-minute
> calculation on a structure you already have.

**Why N55Q over G56A.** Same composite (96.0 vs 94.0 at `model_0`), a tighter envelope
(0.044 vs 0.089, against the baseline's 0.039), and it is the more thorough chemistry:
deamidation happens *at the asparagine*, and glycine at +1 merely makes it fast. Removing
the Asn eliminates the liability; removing the Gly slows it.

---

## 2. "Redesign the light-chain CDRs" — measured, and it does not work

This is the recommendation in our own submission docs, in the deck, and repeated by two
independent reviewers as the single highest-value unfixed item. **We had never tested it.**

### The ceiling, checked before spending a GPU-hour

Challenge 1's NetSolP is `min(VH, VL)`. **VH is 0.699 against a Good edge of 0.70.** So
even a perfect light chain leaves `min = 0.699` and the band stays Medium. **Redesigning
the light chain alone cannot move the score — by 0.001.**

### And it cannot lift VL either

24 light chains from ProteinMPNN at T=0.1, screened on NetSolP (sequence-only, **zero
folds**), grafted onto the handbook construct:

| | value |
|---|---|
| pembrolizumab VL (baseline) | 0.5690 |
| best of 24 designs | **0.5920** (+0.0230) |
| designs reaching VL ≥ 0.70 | **0 / 24** |
| gap still to close | **0.108** |

The best design moves VL by **+0.023 against a required +0.131**. Plain ProteinMPNN over
the light-chain CDRs does not get within a factor of five of the Good edge.

### And every one of them introduces liabilities

**24 of 24 designs FAIL §9.2**, each carrying 3–5 CDR liabilities. That is the same
behaviour that put two glycosylation sequons into the Challenge 2 paratope: unconstrained
ProteinMPNN introduces developability liabilities at a high rate, and nothing in the
rubric penalises it.

> **The correction.** "Redesign the light chain" was a plausible inference from a true
> observation (VL is the limiting chain) and it does not survive contact with a
> measurement. Two things are wrong with it: the ceiling is the **heavy** chain by 0.001,
> and the achievable VL improvement is **five times too small** regardless. What the
> deficit actually needs is a solubility-aware objective — ProteinMPNN optimises sequence
> recovery given a backbone, and solubility is simply not in its loss.

**Cost of finding this out: 24 ProteinMPNN sequences and no folds at all**, because
NetSolP is sequence-only. It could have been run at any point in the past week for
essentially nothing, and would have redirected a recommendation we repeated in three
documents.
