> # ⛔ WITHDRAWN 2026-09-22 — `0/30` WAS A SAMPLING ARTEFACT
>
> This document reported 0 of 30 designs clearing, all failing ipSAE, at
> `recycling_steps=3`, seed 1. **That conclusion is withdrawn.**
>
> `scripts/78_challenge2_reseed.py` re-folded the top 5 at **recycling 10**:
> `bb_2_0_dldesign_1` moved **0.263 → 0.864 / 0.842 / 0.856** across seeds 1/2/3 —
> above the §7.2 gate of 0.60 and above the positive control (0.842). Consistency across
> three seeds says the driver is **recycling, not seed luck**.
>
> The positive control passed and was **irrelevant to the actual failure mode**: the
> configuration was fine, the *sampling* was not. A control that rules out one confound
> says nothing about the confounds you did not think of.
>
> The full pool is being re-folded at recycling 10; the real gate result replaces this.
> Everything below is kept as the record of what an under-sampled fold produced.

# Boltz-2 assigns these de novo designs **no interface confidence at all**

**2026-09-22.** The first Challenge 2 design to be scored returned `ipsae = 0.000`
against a §7.2 minimum of **≥ 0.60**. An exact zero is the signature of a known silent
failure in this project (`ipsae.py` locating its pLDDT array by string-substituting the
PAE path, then writing an empty table and exiting 0), so it was checked before being
believed. **It is genuine.**

## The check

`ipsae.py` wrote a **fully populated 14-line table**, not an empty one:

| chain pair | ipSAE | ipTM |
|---|---|---|
| A–B (heavy–light) | **0.876** | 0.952 |
| A–C (heavy–antigen) | **0.000** | 0.122 |
| B–C (light–antigen) | **0.000** | — |

The heavy–light interface scores healthily, which is what proves the tool ran correctly.
Only the interfaces involving the antigen are zero.

The reason is in the PAE matrix itself:

```
PAE (349 x 349)           min  0.25   median  5.80
antibody-antigen block    min 18.40   median 23.83   fraction < 10 A:  0.0000
```

**Not one residue pair across the antibody–antigen interface has PAE below the 10 Å
cutoff.** ipSAE is a sum over pairs passing that cutoff, so it is exactly zero by
construction, not by error.

## What it means

Boltz-2 places the antibody and the antigen in *some* relative position — PRODIGY counts
**61 heavy-atom contacts** in that pose — but the model expresses **no confidence
whatsoever** in where the antigen sits relative to the antibody. The two numbers are not
in conflict; they measure different things:

- **`contacts` is computed from coordinates.** It counts atoms near atoms in whatever
  pose was emitted. It is blind to whether the model believes that pose.
- **`ipsae` is computed from the PAE.** It asks whether the model believes it.

*Transferable principle, and it is the sharpest form of a thing this project keeps
rediscovering:* **a geometric metric computed from a predicted structure inherits none of
the prediction's uncertainty.** A confidently-placed interface and a coin-flip interface
produce the same contact count. Any rubric that scores both, and weights them equally, is
double-counting the pose while single-counting the doubt.

## Consistency with what we already measured

This is exactly what the post-cutoff test predicted. Boltz-2's median Fab DockQ on five
complexes released after its verified 2023-06-01 cutoff was **0.291**, and these designs
are *more* novel than that test set — a de novo backbone against a target the antibody
was never co-evolved with. `results/challenge2_scope.md` named this as the standing reason
to be sceptical of any Challenge 2 score. It was right.

## CORRECTION, same session — this does NOT generalise to all 30

The paragraph that stood here read *"our own structure predictor does not believe these
designs bind"*. **That was an extrapolation from n=1 and it is wrong.** It is precisely
the error this project has catalogued four times: a single observation stated as a
property of the pool.

Measured across the folds available at the time of writing, with per-design chain
boundaries (the first attempt hardcoded the antibody/antigen split at residue 226, which
is only correct for designs whose chains happen to be 119+107 — an error that mixed
intra-antibody pairs into the "cross-chain" block and inflated the apparent confidence):

| design | H | L | Ag | min cross-chain PAE | fraction < 10 Å |
|---|---|---|---|---|---|
| `bb_10_0_dldesign_0` | 119 | 107 | 123 | 18.40 | 0.0000 |
| `bb_10_0_dldesign_1` | 119 | 107 | 123 | 17.08 | 0.0000 |
| `bb_10_0_dldesign_2` | 119 | 107 | 123 | 17.22 | 0.0000 |
| `bb_1_0_dldesign_0` | 122 | 109 | 123 | 7.02 | 0.0487 |
| `bb_1_0_dldesign_1` | 122 | 109 | 123 | **4.34** | **0.4264** |
| `bb_1_0_dldesign_2` | 122 | 109 | 123 | 10.65 | 0.0000 |
| `bb_2_0_dldesign_0` | 117 | 108 | 123 | 5.97 | 0.2464 |
| `bb_2_0_dldesign_1` | 117 | 108 | 123 | **4.76** | **0.8142** |
| `bb_2_0_dldesign_2` | 117 | 108 | 123 | 8.15 | 0.0145 |

**Some designs have a strongly confident predicted interface.** `bb_2_0_dldesign_1` has
81% of its cross-chain residue pairs below PAE 10 Å. The `bb_10_*` family has none, and
that family is what the original paragraph was written from.

**What survives from the section above:** the ipSAE zero on `bb_10_0_dldesign_0` is
genuine and not the empty-table failure — that check stands, and the mechanism (zero pairs
under the cutoff) is exactly right for *that design*. The distinction between `contacts`
(computed from coordinates, blind to uncertainty) and `ipsae` (computed from the PAE) also
stands, and is if anything sharpened: `bb_10_0_dldesign_0` has **61 heavy-atom contacts and
zero interface confidence**, which is the cleanest single illustration of that gap in the
whole project.

**What does not survive:** any claim about whether *these designs* are believed by the
predictor. The gate pass rate is the measurement that answers it, and it is reported in
`STATE.md` §2 from all 30 designs rather than from the first one scored.

*The lesson is the project's own, and I repeated it inside the document warning about it:
state a null or a negative as a property of the observation until the pool has been
measured.*
