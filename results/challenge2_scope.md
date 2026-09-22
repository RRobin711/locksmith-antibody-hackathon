# Challenge 2 — scope, cost and recommendation

Planning only; nothing here was executed. Written 2026-09-20 after the handbook
conformance audit.

## What the handbook asks for (§3.2)

> *"Blank canvas — design from scratch."* … *"Design a complete VH/VL antibody de novo
> that binds PD-1. You may target the same epitope as pembrolizumab, a different epitope,
> or design multi-epitope approaches."*

Max 100 points. Hard cutoffs: **ipSAE ≥ 0.60**, **ΔG ≤ −6 kcal/mol**, **NetSolP ≥ 0.50**,
**CDR-H3 identity to human germline < 95%**, plus the §7.2 minimums that apply to both
challenges (contacts ≥ 10, interface pLDDT ≥ 65, CDR SASA > 250 Å²).

Scored on **seven** metrics, not eight: DockQ is Challenge 1 only, so the binding category
averages five and every remaining binding metric rises from 0.60/6 = 0.10 to 0.60/5 = 0.12
of the final. Novelty and developability are therefore worth **2.4×** any single binding
metric here, against 2× in Challenge 1.

## The blocker nobody has built: germline novelty

§6.3.1 says Challenge 2 novelty is *"Compared to human germline CDR sequences"*.
`metrics/novelty.py` hardcodes pembrolizumab's CDR-H3 as its only reference and
`data/germline/` is empty. This is not a missing constant — it is a different computation:

- CDR-H3 is produced by **V(D)J junctional recombination**, so it has no single germline
  template. The D segment contributes a short, often unrecognisable core and the N/P
  additions at both junctions are template-free.
- "human germline CDR sequences" (plural) therefore implies a **best-match search** over a
  germline set, most naturally IGHV/IGHD/IGHJ from IMGT, via ANARCI's germline assignment
  or IgBLAST.
- The handbook names no database, no segment set, and does not say whether the D region is
  included. **That ambiguity has to be recorded as a convention before any number is
  quoted**, exactly like the four in `results/handbook_conformance.md`.

Scope: ~half a day. ANARCI is already installed and already returns germline assignments;
the work is choosing the reference set, defining identity over the junction, and writing
the positive control (a known germline-reverted antibody should score near 100%).

## Route A — full de novo (RFdiffusion / RFantibody)

Target-conditioned backbone diffusion onto the PD-1 epitope → ProteinMPNN → fold → score.

| stage | cost |
|---|---|
| install + qualify RFantibody on Blackwell | **1–3 days, high risk** |
| 100 backbones × 8 MPNN sequences | ~2 h |
| sequence filters → fold ~200 survivors at 90 s | ~5 h |
| scoring + analysis | ~1 h |

**Install risk is the whole story.** RFdiffusion's SE3-Transformer/DGL stack is old and this
GPU is `sm_120` (Blackwell, CUDA ≥ 12.8). Docker is installed and is the mitigation, but the
container's pinned CUDA may predate Blackwell, in which case the fallback is CPU diffusion
(hours per backbone, not minutes) or abandoning the route. The project's own risk register
rated this High on day 1 and it was never attempted.

## Route B — germline framework + CDR design

Graft a human germline VH/VL framework onto pembrolizumab's approach geometry in 5GGS
(superpose on framework Cα, which is structurally conserved), then design all six CDRs with
ProteinMPNN in the antigen's presence. §9.1 Pillar 5 names preferred families; IGHV3-23 /
IGKV1-39 are the conventional choices.

| stage | cost |
|---|---|
| install | **none** — MPNN, ANARCI and Boltz all work today |
| germline framework grafting | ~half a day |
| germline novelty metric | ~half a day |
| generate ~200 designs, fold at 90 s | ~5 h |
| scoring + analysis | ~1 h |

**~1.5 days, low risk.** It is also *not* "blank canvas". If taken, the docs say
**"germline-framework CDR design"** and never imply otherwise — the framework is inherited,
only the CDRs are designed. That is what most real therapeutic antibody engineering does,
and the handbook's own §9.1 encourages germline frameworks for developability, so the
honest description is not a weak one. But it is a different claim from de novo.

## Recommendation

**Do the germline novelty metric. Do not run either design campaign.**

The reasoning is this project's own evidence, not schedule pressure:

1. **Challenge 2 removes the only metric that can detect a wrong pose.** With no DockQ,
   nothing in the rubric compares the prediction to anything external. Our novelty probe
   already showed two design sets at *identical* rubric novelty differing by 227 antigen
   contacts, and Challenge 2 could not have told them apart at all.
2. **The predictor is measurably unreliable at exactly this task.** Median Fab DockQ
   **0.291** on five complexes released after Boltz-2's verified cutoff — that is the
   de novo placement problem, measured, on this hardware.
3. **The SKEMPI result bounds what a Challenge 2 score could mean.** No metric in the stack
   tracks measured affinity. A de novo design clearing ipSAE ≥ 0.60 and ΔG ≤ −6 would be a
   design that clears two numbers we have shown do not report binding — ΔG failed the
   epitope-knockout control outright.

So a Challenge 2 submission would be 100 points of score attached to no evidence. The
honest artifact is the **characterised absence**: state that Challenge 2 was scoped and
declined, give these three measurements as the reason, and note that we built the germline
metric so the gap is a decision rather than an omission.

If the goal changes to "have something in the folder", take Route B, budget 1.5 days, and
label it germline-framework rather than de novo.
