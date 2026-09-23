# Calibration — where do our numbers actually sit?

**2026-09-22.** Pre-registered in [[prereg_2026-09-22_calibration_and_negative_control|the pre-registration]].

## Why a bare metric value is not a result

"ipSAE 0.864" tells a reader nothing. They cannot know whether the metric saturates at 0.9 or runs to 1.0, whether real complexes cluster at 0.5 or at 0.95, or how far 0.864 sits from the noise. The handbook's band edge at 0.80 is **asserted**, not located in any distribution. This panel locates it.

40 real, crystallised antibody–antigen complexes were folded through the identical pipeline — same driver, same flags, same Fv+Fv+antigen construct, `recycling_steps=10`, `diffusion_samples=5` — and scored on the same six metrics. Each complex's value is the **median over its five diffusion samples**.

## The split, and why it is the whole point

Boltz-2's training cutoff is **2023-06-01 on PDB *release* date**. A panel mixing memorised and novel complexes would produce a distribution that means nothing, because they are different tasks:

- **pre-cutoff (n=20)** — Boltz has seen these. This is the **ceiling**: what the metrics look like when prediction is closer to recall.
- **post-cutoff (n=20)** — genuinely novel. This is the **honest bar** for a de novo design.

Both arms were drawn by one RCSB query sorted by release date, taking the entries **nearest the cutoff on each side**, so resolution practice, refinement convention and target fashion are matched and the cutoff is close to the only systematic difference between them.

## Coverage — how many complexes each metric actually produced

Stated before any distribution, because a metric that silently drops rows reports a distribution of the rows where it happened to work. DockQ is the one at risk here: it needs a native, and it refuses rather than guessing when chains cannot be mapped.

| metric | pre-cutoff | post-cutoff |
|---|---|---|
| ipSAE | 20/20 | 20/20 |
| DockQ | 20/20 | 20/20 |
| ΔG (kcal/mol) | 20/20 | 20/20 |
| contacts | 20/20 | 20/20 |
| interface pLDDT | 20/20 | 20/20 |
| CDR SASA (Å²) | 20/20 | 20/20 |

`dockq.compute` returns **None with a reason**, never 0, when it cannot score an interface. That distinction is load-bearing: 8 of these 40 natives initially paired an Fv with the antigen of a *different copy* in the asymmetric unit, and a fabricated 0 would have entered the distribution as eight genuine docking failures instead of being caught. (See [[2026-09-22-calibrating-the-rubric-against-things-that-should-fail|the session doc]] §5b.) Model antigens carry SEQRES-filled internal gaps that the crystal does not, up to **38 residues** on 8EQ6 — against `dockq_allowed_mismatches: 40`, a margin of 2. Any row exceeding it appears as a gap in this table, not as a zero.

## The distributions

| metric | pre-cutoff median (IQR) | post-cutoff median (IQR) | Mann–Whitney p | what memorisation is worth |
|---|---|---|---|---|
| ipSAE | 0.646 (0.180–0.759) | 0.165 (0.012–0.424) | 0.008 | rank-biserial +0.50 |
| DockQ | 0.826 (0.329–0.931) | 0.310 (0.254–0.373) | 0.001 | rank-biserial +0.62 |
| ΔG (kcal/mol) | -11.150 (-12.675–-10.550) | -11.500 (-12.125–-10.400) | 0.745 | rank-biserial -0.06 |
| contacts | 78.500 (64.250–84.250) | 78.500 (66.250–92.250) | 0.448 | rank-biserial -0.14 |
| interface pLDDT | 92.280 (85.383–97.325) | 78.910 (77.015–82.608) | 0.000 | rank-biserial +0.71 |
| CDR SASA (Å²) | 1435.150 (1257.875–1567.850) | 1330.150 (1225.900–1521.450) | 0.285 | rank-biserial +0.20 |

*Rank-biserial is the effect size: +1 means every pre-cutoff complex beats every post-cutoff one, 0 means the arms are interchangeable.* At n=20 per arm Mann–Whitney has roughly 80% power for a rank-biserial around 0.6, so **a non-significant row here means "no effect larger than large", not "no effect"** — the detectable effect is stated because this project has four times reported an underpowered null as a finding.

## Our designs, as percentiles

Percentiles are against the **post-cutoff** arm, because that is the distribution a novel design belongs in. Reported as ranks, since with n=20 a percentile has 5-point resolution and a 95% CI near ±20 points at the median — a decimal percentile would imply precision the sample size cannot support.

**One asymmetry to declare before reading the ranks.** Every panel row takes its antigen alignment from a live MMseqs2 query; our own designs take theirs from `data/msa_cache/pd1_5ggs.csv`, cached so that a ranking of designs could not drift with the server. Both are the same pipeline and the same source, built at different times — antibody chains carry `empty` in every row alike — but they are not the *identical* operation, and alignment depth moves confidence metrics. The negative control is free of this (every row there shares the one cached alignment), which is why it, not this table, is the experiment that isolates a single variable.

### Challenge 1 design

| metric | our value | rank in post-cutoff arm | percentile | post-cutoff median |
|---|---|---|---|---|
| ipSAE | **0.863** | 1 of 20 | 100th | 0.165 |
| ΔG (kcal/mol) | **-12.400** | 5 of 20 | 80th | -11.500 |
| contacts | **97.000** | 2 of 20 | 95th | 78.500 |
| interface pLDDT | **92.250** | 3 of 20 | 90th | 78.910 |
| CDR SASA (Å²) | **1554.100** | 5 of 20 | 80th | 1330.150 |

### Challenge 2 design

| metric | our value | rank in post-cutoff arm | percentile | post-cutoff median |
|---|---|---|---|---|
| ipSAE | **0.012** | 17 of 20 | 20th | 0.165 |
| ΔG (kcal/mol) | **-9.900** | 19 of 20 | 10th | -11.500 |
| contacts | **68.000** | 14 of 20 | 30th | 78.500 |
| interface pLDDT | **72.320** | 20 of 20 | 5th | 78.910 |
| CDR SASA (Å²) | **1443.900** | 7 of 20 | 70th | 1330.150 |

## Does the gate agree with the crystal?

This is the question the panel exists to answer and the one the submission cannot answer about itself. For every complex here there is a **real structure**, so we have both the number the rubric gates on (ipSAE) and the accuracy of the predicted pose against ground truth (DockQ). On our own de novo design there is no crystal, so this comparison is impossible — which is exactly why it has to be made somewhere.

Across **n=40** real complexes, Spearman **rho = +0.702** (p = 0.0000) between ipSAE and DockQ.

- pre-cutoff (n=20): rho = **+0.674** (p = 0.0011)
- post-cutoff (n=20): rho = **+0.461** (p = 0.0408)

*Caveat on the correlation, stated rather than left for a reader to find:* at n=40 the Fisher-z standard error is 0.16, so the 95% CI on rho is roughly ±0.32 — wide. This establishes direction and rough magnitude, not a precise value.

### The gate scored against ground truth

Taking the CAPRI convention as truth — DockQ ≥ 0.49 is a *Medium or better* pose, DockQ < 0.23 is *Incorrect* — and the handbook's ipSAE ≥ 0.60 as the gate:

| | complexes | gate says | |
|---|---|---|---|
| **Good pose** (DockQ ≥ 0.49) | 16 | 12 pass, **4 FAIL** | false-negative rate **25%** |
| **Incorrect pose** (DockQ < 0.23) | 4 | 4 fail, **0 PASS** | false-positive rate **0%** |

**4 complexes with a genuinely good predicted pose are rejected by the gate:** 7WN8 (DockQ 0.934, ipSAE 0.157), 8DFI (DockQ 0.738, ipSAE 0.412), 8DCN (DockQ 0.630, ipSAE 0.250), 9BQW (DockQ 0.621, ipSAE 0.260).

These are real, crystallised antibody–antigen complexes whose structure Boltz reproduced correctly, and the rubric would discard every one of them. A false negative here is not a near miss — it is the gate refusing a right answer.

**Why this matters more than the percentiles.** A percentile says where our number sits among other numbers. This says whether the number tracks the thing it claims to measure. Note also that both error rates are computed against DockQ, which is itself a *prediction-versus-crystal* comparison and not a binding assay — so this validates the gate against pose accuracy, not against affinity. Nothing in this project measures affinity, and the SKEMPI arm already showed no metric in the stack tracks it.

## Is ipSAE a confidence, or a coin flip?

Each complex was folded five times from one trunk pass, so the five values differ *only* in the diffusion draw. Across the panel the within-complex spread is not small: it reaches 0.775 ipSAE on a single complex — wider than the entire Medium band.

Counting how many of each complex's five samples sit on the ipSAE floor (< 0.05):

| samples at floor | complexes | |
|---|---|---|
| 0 of 5 | 19 | ███████████████████ |
| 1 of 5 | 8 | ████████ |
| 2 of 5 | 3 | ███ |
| 3 of 5 | 5 | █████ |
| 4 of 5 | 3 | ███ |
| 5 of 5 | 2 | ██ |

**19 of 40 complexes never touch the floor, 2 are always on it, and 19 are mixed.** Overall 51/200 samples (26%) sit at the floor.

**A substantial fraction of complexes are mixed, and that is the finding.** For those, whether the complex 'passes' is decided by which diffusion samples happen to be drawn — the quantity being thresholded is not a stable property of the complex. ipSAE's hard PAE < 10 Å cutoff means a pose either has inter-chain pairs inside the window or it does not, so the score collapses toward a two-state indicator rather than degrading smoothly. **Reading a gate off one sample, on a mixed complex, is a coin flip with the model's confidence ranking as the thumb on the scale.**

## Reading this honestly

A high percentile here is **not** evidence the design binds. It says the predictor is as confident about our design as it is about real complexes it has never seen — which is a statement about the predictor's confidence, not about a molecule. The one metric in this table that reads coordinates against an external truth is DockQ, and for our de novo design there is no crystal to read against, so it is absent exactly where it would matter most.

The panel's real contribution is the opposite of flattering: it shows what these numbers look like when the answer is known to be right, and therefore how much of the band structure in §5.2 is measuring difficulty rather than quality.
