# Calibration — where do our numbers actually sit?

**2026-09-22.** Pre-registered in [[prereg_2026-09-22_calibration_and_negative_control|the pre-registration]].

## Why a bare metric value is not a result

"ipSAE 0.864" tells a reader nothing. They cannot know whether the metric saturates at 0.9 or runs to 1.0, whether real complexes cluster at 0.5 or at 0.95, or how far 0.864 sits from the noise. The handbook's band edge at 0.80 is **asserted**, not located in any distribution. This panel locates it.

3 real, crystallised antibody–antigen complexes were folded through the identical pipeline — same driver, same flags, same Fv+Fv+antigen construct, `recycling_steps=10`, `diffusion_samples=5` — and scored on the same six metrics. Each complex's value is the **median over its five diffusion samples**.

## The split, and why it is the whole point

Boltz-2's training cutoff is **2023-06-01 on PDB *release* date**. A panel mixing memorised and novel complexes would produce a distribution that means nothing, because they are different tasks:

- **pre-cutoff (n=2)** — Boltz has seen these. This is the **ceiling**: what the metrics look like when prediction is closer to recall.
- **post-cutoff (n=1)** — genuinely novel. This is the **honest bar** for a de novo design.

Both arms were drawn by one RCSB query sorted by release date, taking the entries **nearest the cutoff on each side**, so resolution practice, refinement convention and target fashion are matched and the cutoff is close to the only systematic difference between them.

## The distributions

| metric | pre-cutoff median (IQR) | post-cutoff median (IQR) | Mann–Whitney p | what memorisation is worth |
|---|---|---|---|---|

*Rank-biserial is the effect size: +1 means every pre-cutoff complex beats every post-cutoff one, 0 means the arms are interchangeable.* At n=20 per arm Mann–Whitney has roughly 80% power for a rank-biserial around 0.6, so **a non-significant row here means "no effect larger than large", not "no effect"** — the detectable effect is stated because this project has four times reported an underpowered null as a finding.

## Reading this honestly

A high percentile here is **not** evidence the design binds. It says the predictor is as confident about our design as it is about real complexes it has never seen — which is a statement about the predictor's confidence, not about a molecule. The one metric in this table that reads coordinates against an external truth is DockQ, and for our de novo design there is no crystal to read against, so it is absent exactly where it would matter most.

The panel's real contribution is the opposite of flattering: it shows what these numbers look like when the answer is known to be right, and therefore how much of the band structure in §5.2 is measuring difficulty rather than quality.
