> ## ❌ SUPERSEDED 2026-09-22 — this verdict does not license a design rule
>
> The statistics below stand. What they were measured ON does not support the conclusion.
> Re-running this document's own equal-budget test with each scored metric as the outcome
> shows the filter beats its null on **2 of 6** — `dockq` and `iface_plddt` — and **both
> are properties of the predictor, not the interface**. `contacts` runs the wrong way
> (−1.80, p=0.988 for 'more contacts'). See [[g3_outcome_variable|the outcome-variable
> test]]. Read what follows as a record of the method, not as a validated filter.

# G3 — verdict

Adjudicated on **239 designs, single Boltz seed each**, `scripts/33_g3_verdict.py`. 10,000 random subsets.

## The verdict

> ## PASS

| quantity | value | required |
|---|---|---|
| filtered group size (aromatic count ≤ 1) | 45 / 239 (19%) | — |
| mean DockQ, filtered | **0.7301** | — |
| mean DockQ, equal-size random subset | 0.7060 | — |
| **margin over the null** | **+0.0241** | ≥ 0.018 |
| one-sided p (random ≥ filtered) | **0.0000** | < 0.05 |
| mean DockQ, whole pool | 0.7060 | — |
| mean DockQ, discarded group | 0.7004 | — |

The margin is **1.34x** the one-seed-sd bar. The bar was set ABOVE the discovery-set effect (+0.0137) precisely so the test could fail; it did not.

## The filter's value depends on where the generator sits

Adjudicating the pooled number alone would hide the most useful thing in the data. The aromatic↔quality relationship **decays monotonically with sampling temperature**:

| arm | n | ρ (aromatic → DockQ) | p | filtered n | filtered mean | null mean | margin |
|---|---|---|---|---|---|---|---|
| T=0.1 | 60 | **-0.535** | 0.0000 | 8 | 0.7503 | 0.7122 | **+0.0380** |
| T=0.2 | 59 | **-0.551** | 0.0000 | 10 | 0.7477 | 0.7059 | **+0.0418** |
| T=0.3 | 60 | **-0.390** | 0.0020 | 14 | 0.7205 | 0.7082 | **+0.0123** |
| T=0.5 | 60 | **-0.326** | 0.0110 | 13 | 0.7145 | 0.6973 | **+0.0172** |

Arms clearing the one-seed-sd margin on their own: **[0.1, 0.2]**; arms that do not: **[0.3, 0.5]**. Per-arm *n* is ~60, so these are underpowered individually and should be read as a trend, not four verdicts — but the trend is monotone in ρ (−0.535, −0.551, −0.390, −0.326) and that is not noise-shaped.

**What this means operationally.** The filter is a property of the *generator's operating point*, not a universal truth about CDR-H3. It is strongest exactly where ProteinMPNN stays close to the native loop and weakens as sampling temperature pushes sequences away. A funnel that over-generates at high temperature for novelty — which is what the rubric's 2× novelty pricing pushes you toward — is operating in the regime where this filter helps least. Quoting the pooled ρ = −0.418 as though it applied everywhere would hide that.

## What the filter would have cost and saved

Applied as a production stage, the filter keeps 19% of generated designs. To fold 45 survivors instead of 239 saves **194 folds = 4.5 h** at the measured 84 s/fold. What it gives up:

- pool maximum DockQ **0.7770**; best design the filter would have KEPT **0.7770** (rank 1 of 239)
- so the filter retains the pool's best design, costing **0.0000 DockQ** at the top end (0.0 seed sd)

**But that retention has to face the same null as everything else.** A random subset of 45 from 239 contains the pool maximum with probability 0.188 by construction, so keeping it is weak evidence at best. Measured over 10,000 random subsets: P(random subset's max ≥ filtered max) = **0.189**, against the < 0.05 that would be needed to call it a real top-end effect.

So the filter **did** retain the best design here, and that is worth 5.3:1 odds at most — not significant. The mean effect is significant (p < 0.0001); the max effect is not (p = 0.189). This reproduces the plan review's §1 finding on wholly new data: the filter moves the **mean**, not the maximum. It is a tool for raising the yield of a shortlist, not for finding the single best design — a campaign that ships one design should apply it to save compute, never to choose.

