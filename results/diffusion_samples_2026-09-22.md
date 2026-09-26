# The diffusion draw moves BOTH challenges, and we have been reporting the argmax

**2026-09-22.** Run against the rule pre-registered in
[the pre-registration](prereg_2026-09-22_diffusion_samples.md), written before the folds.

## Result

Five diffusion samples per challenge, one run each, everything else at the exact submitted
settings (Ch1: Fab, recycling 3, seed 71, live MSA. Ch2: Fv, recycling 10, seed 1, cached
MSA). Within one invocation the MSA is shared, so this spread is **pure diffusion
variability**. `*` marks a metric outside the Good band.

### Challenge 1

| model | ipSAE | DockQ | ΔG | contacts | iface pLDDT | CDR SASA | final |
|---|---|---|---|---|---|---|---|
| **0 (submitted)** | 0.822 | **0.816** | −12.7 | 94 | 89.42 | 1565.0 | **96.0** |
| 1 | 0.841 | 0.798 `*` | −13.2 | 99 | 88.72 | 1583.5 | 94.0 |
| 2 | 0.827 | 0.801 | −13.0 | 92 | 89.05 | 1553.3 | 96.0 |
| 3 | 0.840 | 0.820 | −12.4 | 98 | 88.17 | 1526.7 | 96.0 |
| 4 | 0.861 | **0.711** `*` | −12.5 | 93 | 88.65 | 1529.5 | 94.0 |
| **spread** | **0.039** | **0.109** | 0.80 | 7 | 1.25 | 56.8 | **94.0–96.0** |

### Challenge 2

| model | ipSAE | ΔG | contacts | iface pLDDT | CDR SASA | final |
|---|---|---|---|---|---|---|
| **0 (submitted)** | **0.864** | −12.4 | 98 | 83.58 | 1066.8 | **96.0** |
| 1 | 0.773 `*` | −12.1 | 94 | 84.03 | 1144.3 | 93.6 |
| 2 | 0.757 `*` | −11.8 | 102 | 84.00 | 1060.3 | 91.2 |
| 3 | 0.859 | −12.6 | 98 | 81.41 | 1198.9 | 96.0 |
| 4 | 0.736 `*` | −11.5 | 95 | 82.90 | 1131.0 | 91.2 |
| **spread** | **0.128** | 1.10 | 8 | 2.62 | 138.6 | **91.2–96.0** |

## Verdict against the pre-registered rule

**Challenge 2 crosses a band edge but never the cutoff.** Lowest ipSAE across five samples
is **0.736**, comfortably above the §7.2 minimum of 0.60. By the rule: *"fold into the
existing envelope and widen it; no new severity."* **Viability is not diffusion-sample
dependent** — the outcome I was most concerned about did not occur.

**Challenge 1 also crosses a band edge, which I did not predict.** By the rule: *"the claim
that Challenge 1 survives must be qualified."* It is qualified below.

## What I predicted, and what I got wrong

| prediction | outcome |
|---|---|
| Ch1 ipSAE spread < 0.05 | ✅ **0.039** |
| Ch1 "no band changes" | ❌ **wrong** — DockQ moves 0.711–0.820 and crosses the 0.80 edge on 2 of 5 |
| Ch2 ipSAE spread > 0.10 | ✅ **0.128** |
| Ch2 "at least one sample crosses 0.80" | ✅ **three of five do** |

I reasoned that because Challenge 1 is invariant to *recycling* depth it would be invariant
to the *diffusion* draw. That was wrong, and the error is instructive: recycling refines a
representation the trunk has already committed to, while the diffusion head **generates the
coordinates**. A memorised complex can have a confidently-determined interface (ipSAE
stable at 0.039) and still have its atoms placed differently enough between draws to move a
structural comparison by 0.109 DockQ. **Confidence stability does not imply coordinate
stability**, and DockQ is the only metric we score that reads coordinates against an
external reference.

## The finding that matters most

**In both challenges, `model_0` — the one we submitted — is the best or joint-best of five.**

Ch1 model_0 scores 96.0 (joint-best). Ch2 model_0 has the **highest ipSAE of the five**,
0.864 against a median of 0.773.

This is not luck: Boltz orders its output by its own confidence, so `model_0` is the argmax
by construction. But the consequence is that **every pose-derived number this project has
ever reported is the top of a distribution we never sampled.** With `diffusion_samples=1`
you do not get a random draw — you get the model's best guess, reported as if it were the
estimate.

> **Transferable principle.** A generative predictor that returns its outputs ranked hands
> you an order statistic, not a sample. Taking the first one and calling it "the prediction"
> silently reports a maximum. The fix is not to stop using it — the argmax is usually what
> you want to submit — but to **sample enough to know the spread you are sitting at the top
> of**, and to report that spread beside the number. It costs almost nothing: five diffusion
> samples took 2m54s against roughly 2m for one, because the MSA, the trunk and the
> recycling are shared and only the diffusion head reruns.

## Consequences for what we report

| | was | now |
|---|---|---|
| Challenge 1 | 96.0 | **94.0–96.0** across diffusion samples (recycling-stable) |
| Challenge 2 | 93.6–96.0 across recycling | **91.2–96.0** across diffusion samples, and 93.6–96.0 across recycling |

Both submitted designs remain **viable under every sample tested** — no metric in either
challenge approached a §7.2 cutoff. What moves is band membership, and therefore the
headline score.

## What is now closed, and what is not

**Closed:** `diffusion_samples` was the last unexamined setting inherited into the
Challenge 2 path. It has been varied, it moves the score in both challenges, it does not
move viability in either, and the numbers are recorded.

**Not closed:** this was one run of five samples per challenge, at one seed. A proper
characterisation would cross diffusion samples with seeds and recycling depth, which we
have not done and are not going to before submission. The honest statement is a measured
lower bound on the variability, not the variability.
