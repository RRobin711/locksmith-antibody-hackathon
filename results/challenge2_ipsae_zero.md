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

**The honest reading: our own structure predictor does not believe these designs bind.**
That is a result, not a failure of the pipeline, and it is worth more than a score would
have been.
