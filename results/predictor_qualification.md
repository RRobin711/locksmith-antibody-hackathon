# Predictor qualification — Boltz-2 on 5GGS, untemplated

**2026-09-15.** Gates G1a and G1b. Can an AF-class model recover a known
antibody–antigen pose *without being shown the answer*?

## Configuration

| | |
|---|---|
| Model | Boltz-2 (`boltz2_conf.ckpt`), `--no_kernels` (pure PyTorch) |
| Templates | **none** — Boltz uses no templates unless given a YAML that specifies them |
| Input | Fv only: VH 119 + VL 111 + PD-1 113 = **343 residues** |
| MSA | **antibody chains `empty`** (single-sequence); PD-1 only, capped at 1024 |
| Sampling | 1 diffusion sample, 3 recycling steps, seed 1 |
| **Wall clock** | **34 seconds** |

## Result — every computed metric in the Good band

| metric | raw | band | margin over cutoff | crystal reference |
|---|---|---|---|---|
| **DockQ** vs crystal | **0.820** | good | +104% | 0.867 between two crystal copies |
| **ipSAE** | **0.841** | good | +120% | undefined on crystals |
| **interface pLDDT** | **94.4** | good | +196% | undefined on crystals |
| ΔG (kcal/mol) | −12.8 | good | +113% | −14.3 |
| contacts | 106 | good | +640% | 102 |
| CDR SASA (Å²) | 1444 | good | +341% | 1564 |
| CDR-H3 identity | 100% | **fails, correctly** | — | it *is* pembrolizumab |
| NetSolP | — | unknown | — | not yet installed |

Per-interface DockQ: **heavy–antigen 0.838, light–antigen 0.820**, both CAPRI
*High quality* (≥0.80). iRMSD ≈ 1.1 Å, fnat 0.86–0.88 — the interface atoms sit
about one ångström from their crystallographic positions and ~87% of native
contacts are recovered.

**The prediction recovers the pose about as well as a second crystal copy does
(0.82 vs 0.867).** From sequence alone, no template, no antibody MSA.

## ⚠ The caveat that governs how far this generalises

**5GGS was published in 2017 and is almost certainly in Boltz-2's training set.**
So this is not a clean test of de novo prediction — it is partly retrieval. The
result proves the *machinery* works end to end (fold → PAE → ipSAE → score) and
that our harness produces sensible numbers on a prediction. It does **not**
establish that Boltz-2 can place a novel, never-before-seen antibody onto PD-1.

A fair test needs a complex released after the training cutoff. Until then,
**Challenge 2 confidence numbers should be discounted accordingly**, and the
cross-predictor consensus and specificity controls in the dossier carry
correspondingly more weight.

## Calibration points worth carrying forward

**A correct pose scores ipSAE 0.841.** First reference value for what "right"
looks like on this metric. The rubric's Good band starts at 0.80, so a genuinely
correct antibody–antigen interface sits only just inside it — the band is tight,
and an ipSAE much above 0.85 on a *designed* molecule deserves suspicion rather
than celebration.

**Boltz's own iptm was 0.948 while ipSAE was 0.841 on the same structure.** They
are different scales, as anticipated. Do not substitute one for the other, and do
not read Boltz's confidence summary as if it were the scored metric.

**Predicted ΔG −12.8 vs crystal −14.3** (Kd 390 pM vs 34 pM). A ~1.5 kcal/mol gap
on the *same molecule* — comfortably inside PRODIGY's stated RMSE, and a concrete
demonstration of why ΔG is ordinal, not cardinal.

**Fv heavy–light interface scored lowest (DockQ 0.791, fnat 0.405)** despite a
very low iRMSD of 0.251 Å. The VH/VL packing is geometrically close but its
contact set differs from the Fab's — which is exactly the under-constrained elbow
predicted when we chose Fv for screening and Fab for confirmation. Direct support
for that protocol.

## Compute budget — revised sharply upward

34 s per Fv fold on the **slow** pure-PyTorch path. Against ~45 GPU-hours that is
roughly **4,700 folds**, against a planned estimate of 1,400–1,800.

> **CORRECTED 2026-09-17.** That 34 s is the fold, not the *invocation*. Measured over 40
> panel folds, a `boltz predict` call costs **92 s (Fv) / 126 s (Fab)** — a fixed ~60 s of
> checkpoint load and MSA parsing dominates. Real budget: **~1,290 Fab folds**, not 4,700.
> Batching several targets into one invocation would recover ~1.8× and is not yet done.
> See [the 2026-09-17 session doc](../docs/sessions/2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test.md) §4.1. The funnel in
PLAN §5.2 can be several times wider than budgeted, and chasing `boltz[cuda]`
kernels on Blackwell is not currently worth the compatibility risk.
