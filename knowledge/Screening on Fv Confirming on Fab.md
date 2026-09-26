---
date: 2026-09-15
tags: [project, protein-design, structure-prediction, pattern]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Pattern|patterns worth reusing]]

# Screening on Fv, Confirming on Fab

**Why this note exists:** a small protocol decision with a hidden assumption that could have
invalidated an entire screening campaign without ever announcing itself.

Background: [Fv versus Fab](Antibody%20Architecture.md).

---

## 1. The trade-off

We can predict either fragment:

| | Residues | Cost | Fidelity |
|---|---|---|---|
| **Fv** (VH + VL) | 343 with the target | cheaper | elbow angle unconstrained |
| **Fab** (VH + CH1 + VL + CL) | 549 with the target | ~2.6× more | constant domains clamp the elbow |

The size difference is 1.6×, but the compute difference is larger — the attention mechanisms in
folding models scale roughly with the *square* of sequence length, so 1.6× in residues is
closer to **2.6× in compute**.

Against that, the constant domains do real structural work. They physically brace the angle
between VH and VL. Strip them off and that angle can drift, so a bare Fv is a slightly less
faithful model of the real molecule.

## 2. The protocol

**Screen wide on Fv, confirm the shortlist on Fab.**

Thousands of candidates get the cheap treatment; only the handful that survive get the
expensive, faithful one. Standard cheap-reject-before-expensive-confirm.

## 3. The hidden assumption — and why it needs testing

The protocol only works if **Fv ranking predicts Fab ranking**. We use Fv to decide what
survives, so if the cheap screen ranks designs differently from the expensive one, we are
selecting on noise.

Here is what makes it insidious: **we would never notice.** We only ever compute Fab numbers
for designs the Fv screen already liked. The designs it wrongly rejected are never folded as
Fab, so there is no comparison to reveal the error. The screen would be silently discarding
good molecules and we would see nothing but a shortlist of plausible-looking results.

*Any time a cheap proxy gates access to an expensive measurement, the proxy's failures are
invisible by construction.*

## 4. The check

Fold 10–15 designs spanning the quality range **both ways**, and measure rank correlation
(Spearman's ρ) on ipSAE.

- **ρ ≥ 0.6** → the screen tracks; keep the protocol and the 2.6× saving
- **ρ < 0.6** → the screen is not tracking; go Fab-only and accept fewer folds

This is a gate in the plan, not an intention. It costs about half an hour.

## 5. Early evidence that the theory is right

Our first prediction was an Fv, and the scoring broke down per interface:

| Interface | DockQ | iRMSD |
|---|---|---|
| heavy–antigen | 0.838 | 1.10 Å |
| light–antigen | 0.820 | 1.16 Å |
| **heavy–light** | **0.791** | **0.25 Å** |

The **heavy–light interface scored worst** — exactly the under-constrained elbow the theory
predicts, showing up in real data before we went looking for it.

Note the odd combination: heavy–light has the *lowest* positional error (0.25 Å) but the
*lowest* DockQ. The residues are geometrically in the right place, but the set of contacts
differs from the Fab's — which is what you would expect when the domains that normally brace
that interface have been removed.

That is not proof the protocol works. It is confirmation that the phenomenon it is designed
around is real and measurable on our own data.

---

**Related:** [what folding costs](How%20Structure%20Prediction%20Works.md) ·
[what DockQ and iRMSD mean](The%20Eight%20Metrics.md)
