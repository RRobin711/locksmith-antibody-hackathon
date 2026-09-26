---
date: 2026-09-15
tags: [project, antibody, protein-design, structural-biology, learning]
status: living
---

Tags: [[Antibody|antibodies]] · [[Protein Design|protein design]] · [[Structural Biology|structural biology]] · [[Learning|things I'm learning]]

# Antibody Architecture

**Why this note exists:** we are designing antibodies. Almost every technical decision in the
project — what we mutate, what gets scored, what "novel" means, even how much GPU memory a
job needs — follows from the shape of this molecule.

Read [the target note](PD-1%20and%20Checkpoint%20Blockade.md) first if you haven't.

---

## 1. The overall shape

An antibody is a **Y-shaped protein**. It is built from four separate protein chains:

- **two identical heavy chains** (~50 kDa each — kDa, kilodalton, is a unit of molecular mass;
  bigger number, bigger protein)
- **two identical light chains** (~25 kDa each)

They clip together into the Y. The two tips of the Y are the business end — that is where the
antibody grabs its target. The stem is what the rest of the immune system recognises.

Because the two arms are identical, an antibody has two identical grabbing sites.

## 2. Fv and Fab — two ways to talk about "the tip"

You will see both terms constantly and the difference is practical, not pedantic.

A protein chain is made of **domains** — semi-independent folded units, like beads on a
string. Both the heavy and light chains are made of several domains.

- **Variable domain** — the domain at the very tip. It differs enormously between antibodies.
  Called **VH** on the heavy chain and **VL** on the light chain.
- **Constant domains** — everything behind it. Nearly identical across all antibodies of a
  given class. Called CH1, CL, and so on.

That gives two useful fragments:

| Term | What it contains | Size (our case) |
|---|---|---|
| **Fv** (*fragment variable*) | VH + VL only — the minimal binding unit | ~230 residues |
| **Fab** (*fragment antigen-binding*) | VH + CH1 + VL + CL — the whole arm of the Y | ~436 residues |

**Why we care:** predicting a structure costs compute that grows faster than linearly with
size. Fv is much cheaper. But the constant domains physically clamp the angle between VH and
VL — the "elbow" — so a bare Fv has an under-constrained wobble the Fab does not.

That trade-off is a whole decision on its own: see
[the Fv-screen/Fab-confirm protocol](Screening%20on%20Fv%20Confirming%20on%20Fab.md). We measured the
consequence directly — in our first prediction, the VH/VL interface was the *worst*-scoring
part of the model, exactly as the theory predicts.

## 3. The CDRs — six loops that do all the binding

Within the variable domains, the actual contact with the target is made by six short,
floppy loops called **CDRs** — *Complementarity-Determining Regions*. The name means "the bits
whose shape is complementary to the target."

Three are on the heavy chain (CDR-H1, H2, H3) and three on the light (CDR-L1, L2, L3).

Two more pieces of vocabulary:

- **Paratope** — the surface of the *antibody* that touches the target. Mostly the CDRs.
- **Epitope** — the surface of the *target* that gets touched.

Everything outside the CDRs in the variable domain is **framework** — structural scaffolding
that holds the loops in place. In design work, framework is usually kept fixed and the CDRs
are what you change.

## 4. Why CDR-H3 is special

The six loops are not equal. **CDR-H3 dominates**, and the reason is genetic rather than
structural.

Five of the six loops are encoded more or less directly in your genome. CDR-H3 is not — it is
assembled by **V(D)J recombination**: three separate gene segments (V, D and J) are cut and
spliced together, and at each of the two joins the cell randomly adds and deletes a few
nucleotides.

That junctional randomness means CDR-H3 varies enormously in **both sequence and length**, far
more than the other five loops. The consequences:

- CDR-H3 contributes **30–50% of the paratope surface**
- it is the primary determinant of *what* the antibody recognises
- it is the hardest loop to design, and the hardest to predict

We measured this concretely on two approved drugs:

| Drug | CDR-H3 sequence | Length |
|---|---|---|
| Pembrolizumab | `ARRDYRFDMGFDY` | **13 residues** |
| Nivolumab | `ATNDDY` | **6 residues** |

Both bind PD-1. Both work in patients. **PD-1 can be bound by radically different loop
architectures** — which is genuinely encouraging for designing something new, because it means
there isn't one narrow correct answer.

## 5. Numbering schemes, and why "CDR-H3" needs a definition

Here is a subtlety that bit us.

If two antibodies have different CDR-H3 lengths, then "residue 100" in one is not the
structural equivalent of "residue 100" in the other. Raw position means nothing across
antibodies.

A **numbering scheme** fixes this. It assigns canonical position numbers, inserting gaps and
insertion codes so that structurally equivalent positions get the same number in every
antibody. We use **IMGT** (the scheme the competition specifies), where:

```
CDR1 = positions 27–38    CDR2 = 56–65    CDR3 = 105–117
```

**This is part of the metric definition, not an implementation detail.** Use a different
scheme — Kabat, Chothia — and you extract a different substring and compute a different
answer. Early on I guessed pembrolizumab's CDR-H3 was 11 residues (`RDYRFDMGFDY`); that is the
*Kabat* definition. IMGT includes the preceding `AR`, making it **13**. The difference matters
because length is the denominator when you compute percent identity.

## 6. What "novelty" means and why it is scored

The competition scores **CDR-H3 sequence identity** against a reference — how similar your
loop is to the original. **Lower is better.**

Why? Because otherwise you could submit pembrolizumab with one atom changed and claim you
designed a drug. The novelty metric exists to reject trivial clones. It is the competition
asking: *did you actually design something, or did you copy?*

Because we measured CDR-H3 as 13 residues, the arithmetic is exact — identity moves in steps
of 1/13 ≈ 7.7%:

| Substitutions | Identity | Verdict |
|---|---|---|
| 0 | 100% | fails the hard cutoff (<95%) — a clone |
| **1** | 92.3% | passes the cutoff |
| **4** | 69.2% | reaches the top band (<70%) — full marks |

**Four substitutions in a 13-residue loop earns full novelty marks.** That is very reachable,
which is a useful thing to know before you start: novelty is among the cheapest points
available. See [the metrics note](The%20Eight%20Metrics.md) for how the scoring bands work.

## 7. One thing that surprised us

A tool we used to identify antibody domains (ANARCII) confidently numbered **PD-1 itself** as
an antibody and assigned it CDRs.

That is not a bug — PD-1 belongs to the **immunoglobulin superfamily**. It has an **IgV
fold**: the same β-sandwich architecture as an antibody variable domain, by shared
evolutionary ancestry. A tool trained to recognise V domains recognises it because, by fold,
it *is* one.

Real antibody domains scored ~31 on the tool's confidence measure; PD-1 scored ~16. Clean
separation — but only if you look for it. Full story in [the traps note](Eight%20Silent%20Failures.md).

---

**Next:** [what we're actually being asked to design](De%20Novo%20Design%20and%20the%20Two%20Challenges.md).
