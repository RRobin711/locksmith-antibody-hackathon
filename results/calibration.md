# Calibration — where do our numbers actually sit?

**2026-09-22.** Pre-registered in [[prereg_2026-09-22_calibration_and_negative_control|the pre-registration]].

## Why a bare metric value is not a result

"ipSAE 0.864" tells a reader nothing. They cannot know whether the metric saturates at 0.9 or runs to 1.0, whether real complexes cluster at 0.5 or at 0.95, or how far 0.864 sits from the noise. The handbook's band edge at 0.80 is **asserted**, not located in any distribution. This panel locates it.

23 real, crystallised antibody–antigen complexes were folded through the identical pipeline — same driver, same flags, same Fv+Fv+antigen construct, `recycling_steps=10`, `diffusion_samples=5` — and scored on the same six metrics. Each complex's value is the **median over its five diffusion samples**.

## The split, and why it is the whole point

Boltz-2's training cutoff is **2023-06-01 on PDB *release* date**. A panel mixing memorised and novel complexes would produce a distribution that means nothing, because they are different tasks:

- **pre-cutoff (n=20)** — Boltz has seen these. This is the **ceiling**: what the metrics look like when prediction is closer to recall.
- **post-cutoff (n=3)** — genuinely novel. This is the **honest bar** for a de novo design.

Both arms were drawn by one RCSB query sorted by release date, taking the entries **nearest the cutoff on each side**, so resolution practice, refinement convention and target fashion are matched and the cutoff is close to the only systematic difference between them.

## Coverage — how many complexes each metric actually produced

Stated before any distribution, because a metric that silently drops rows reports a distribution of the rows where it happened to work. DockQ is the one at risk here: it needs a native, and it refuses rather than guessing when chains cannot be mapped.

| metric | pre-cutoff | post-cutoff |
|---|---|---|
| ipSAE | 20/20 | 3/3 |
| DockQ | 20/20 | 3/3 |
| ΔG (kcal/mol) | 20/20 | 3/3 |
| contacts | 20/20 | 3/3 |
| interface pLDDT | 20/20 | 3/3 |
| CDR SASA (Å²) | 20/20 | 3/3 |

`dockq.compute` returns **None with a reason**, never 0, when it cannot score an interface. That distinction is load-bearing: 8 of these 40 natives initially paired an Fv with the antigen of a *different copy* in the asymmetric unit, and a fabricated 0 would have entered the distribution as eight genuine docking failures instead of being caught. (See [[2026-09-22-calibrating-the-rubric-against-things-that-should-fail|the session doc]] §5b.) Model antigens carry SEQRES-filled internal gaps that the crystal does not, up to **38 residues** on 8EQ6 — against `dockq_allowed_mismatches: 40`, a margin of 2. Any row exceeding it appears as a gap in this table, not as a zero.

## The distributions

| metric | pre-cutoff median (IQR) | post-cutoff median (IQR) | Mann–Whitney p | what memorisation is worth |
|---|---|---|---|---|
| ipSAE | 0.646 (0.180–0.759) | 0.104 (0.015–0.260) | 0.115 | rank-biserial +0.60 |
| DockQ | 0.826 (0.329–0.931) | 0.377 (0.251–0.621) | 0.139 | rank-biserial +0.57 |
| ΔG (kcal/mol) | -11.150 (-12.675–-10.550) | -10.900 (-11.900–-10.500) | 0.648 | rank-biserial -0.18 |
| contacts | 78.500 (64.250–84.250) | 70.000 (66.000–77.000) | 0.338 | rank-biserial +0.37 |
| interface pLDDT | 92.280 (85.383–97.325) | 78.160 (75.960–84.920) | 0.012 | rank-biserial +0.87 |
| CDR SASA (Å²) | 1435.150 (1257.875–1567.850) | 1531.800 (1247.800–1635.400) | 0.698 | rank-biserial -0.17 |

*Rank-biserial is the effect size: +1 means every pre-cutoff complex beats every post-cutoff one, 0 means the arms are interchangeable.* At n=20 per arm Mann–Whitney has roughly 80% power for a rank-biserial around 0.6, so **a non-significant row here means "no effect larger than large", not "no effect"** — the detectable effect is stated because this project has four times reported an underpowered null as a finding.

## Does the gate agree with the crystal?

This is the question the panel exists to answer and the one the submission cannot answer about itself. For every complex here there is a **real structure**, so we have both the number the rubric gates on (ipSAE) and the accuracy of the predicted pose against ground truth (DockQ). On our own de novo design there is no crystal, so this comparison is impossible — which is exactly why it has to be made somewhere.

Across **n=23** real complexes, Spearman **rho = +0.696** (p = 0.0002) between ipSAE and DockQ.

- pre-cutoff (n=20): rho = **+0.674** (p = 0.0011)

*Caveat on the correlation, stated rather than left for a reader to find:* at n=23 the Fisher-z standard error is 0.22, so the 95% CI on rho is roughly ±0.44 — wide. This establishes direction and rough magnitude, not a precise value.

### The gate scored against ground truth

Taking the CAPRI convention as truth — DockQ ≥ 0.49 is a *Medium or better* pose, DockQ < 0.23 is *Incorrect* — and the handbook's ipSAE ≥ 0.60 as the gate:

| | complexes | gate says | |
|---|---|---|---|
| **Good pose** (DockQ ≥ 0.49) | 14 | 10 pass, **4 FAIL** | false-negative rate **29%** |
| **Incorrect pose** (DockQ < 0.23) | 0 | 0 fail, **0 PASS** | false-positive rate **0%** |

**4 complexes with a genuinely good predicted pose are rejected by the gate:** 7WN8 (DockQ 0.934, ipSAE 0.157), 8DFI (DockQ 0.738, ipSAE 0.412), 8DCN (DockQ 0.630, ipSAE 0.250), 9BQW (DockQ 0.621, ipSAE 0.260).

These are real, crystallised antibody–antigen complexes whose structure Boltz reproduced correctly, and the rubric would discard every one of them. A false negative here is not a near miss — it is the gate refusing a right answer.

**Why this matters more than the percentiles.** A percentile says where our number sits among other numbers. This says whether the number tracks the thing it claims to measure. Note also that both error rates are computed against DockQ, which is itself a *prediction-versus-crystal* comparison and not a binding assay — so this validates the gate against pose accuracy, not against affinity. Nothing in this project measures affinity, and the SKEMPI arm already showed no metric in the stack tracks it.

## Is ipSAE a confidence, or a coin flip?

Each complex was folded five times from one trunk pass, so the five values differ *only* in the diffusion draw. Across the panel the within-complex spread is not small: it reaches 0.775 ipSAE on a single complex — wider than the entire Medium band.

Counting how many of each complex's five samples sit on the ipSAE floor (< 0.05):

| samples at floor | complexes | |
|---|---|---|
| 0 of 5 | 13 | █████████████ |
| 1 of 5 | 5 | █████ |
| 2 of 5 | 1 | █ |
| 3 of 5 | 2 | ██ |
| 4 of 5 | 2 | ██ |
| 5 of 5 | 0 |  |

**13 of 23 complexes never touch the floor, 0 are always on it, and 10 are mixed.** Overall 21/115 samples (18%) sit at the floor.

**Note the asymmetry, which is sharper than the bimodality itself: not one complex has all five samples on the floor.** Every floor value in this panel belongs to a complex that also produced at least one non-floor sample. A floor reading is therefore never a property of the complex here — it is always a property of the draw. A single sample landing at 0.000 says the diffusion head missed on that attempt, not that the pair cannot be placed, and this project spent a week reading exactly that signal as the latter (`0/30 viable`, 15 designs at exactly 0.000).

**A substantial fraction of complexes are mixed, and that is the finding.** For those, whether the complex 'passes' is decided by which diffusion samples happen to be drawn — the quantity being thresholded is not a stable property of the complex. ipSAE's hard PAE < 10 Å cutoff means a pose either has inter-chain pairs inside the window or it does not, so the score collapses toward a two-state indicator rather than degrading smoothly. **Reading a gate off one sample, on a mixed complex, is a coin flip with the model's confidence ranking as the thumb on the scale.**

## Reading this honestly

A high percentile here is **not** evidence the design binds. It says the predictor is as confident about our design as it is about real complexes it has never seen — which is a statement about the predictor's confidence, not about a molecule. The one metric in this table that reads coordinates against an external truth is DockQ, and for our de novo design there is no crystal to read against, so it is absent exactly where it would matter most.

The panel's real contribution is the opposite of flattering: it shows what these numbers look like when the answer is known to be right, and therefore how much of the band structure in §5.2 is measuring difficulty rather than quality.
