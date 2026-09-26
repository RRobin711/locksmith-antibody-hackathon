---
date: 2026-09-15
tags: [project, antibody, structural-biology, learning]
status: living
---

Tags: [[Antibody|antibodies]] · [[Structural Biology|structural biology]] · [[Learning|things I'm learning]]

# PD-1 and Checkpoint Blockade

**Why this note exists:** everything in this project is aimed at one molecule. Before any of
the tooling makes sense, it helps to know what we are aiming at and why anyone cares.

---

## 1. The problem: your immune system can already kill cancer

You have cells called **T cells** — white blood cells that patrol the body looking for things
that shouldn't be there. They are genuinely capable of recognising and killing cancer cells.

So why does cancer happen? Partly because tumours learn to switch the T cells off.

## 2. The off-switch

T cells carry a receptor on their surface called **PD-1** (*Programmed cell Death protein 1*).
A **receptor** is a protein that sticks out of a cell and waits for something to bind to it;
when something does, the cell changes behaviour.

PD-1 is an **inhibitory** receptor — a brake. When something binds it, the T cell calms down.
That is useful in normal life: it stops your immune system attacking your own tissue.

The thing that binds it is called **PD-L1** (*Programmed Death-Ligand 1*). A **ligand** is just
"the thing that binds a receptor". Healthy cells display PD-L1 to say *I'm one of yours, stand
down.*

## 3. How tumours cheat

Many tumours **upregulate** PD-L1 — they produce lots of it and stud their surface with it.
Often they do this *in response to being attacked*: T cells release a signalling molecule
called interferon-gamma (IFN-γ), and the tumour responds by displaying more PD-L1.

The sequence is:

1. T cell finds the tumour and starts attacking
2. Tumour responds by covering itself in PD-L1
3. PD-L1 presses PD-1 on the T cell
4. The T cell becomes **exhausted** — it stops multiplying, stops releasing its killing
   signals, stops killing
5. The tumour survives

The tumour has essentially shown the immune system a forged ID card.

## 4. Checkpoint blockade: the fix

A **checkpoint** is one of these natural brakes on the immune system. **Checkpoint blockade**
means using a drug to physically get in the way of the brake being applied.

If you make a molecule that sticks to PD-1 and covers the exact patch where PD-L1 would
attach, PD-L1 can no longer reach it. The brake is never applied. The T cell stays awake and
carries on killing.

Crucially, this drug does **not** attack the tumour. It attacks the tumour's *defence*. The
killing is done by the patient's own immune system — which is why responses can be so durable
when it works.

## 5. Pembrolizumab (Keytruda) — the molecule we are benchmarking against

**Pembrolizumab**, sold as **Keytruda**, is an [antibody](Antibody%20Architecture.md) that does
exactly this. It binds human PD-1 and blocks PD-L1.

Two numbers worth knowing:

- **Kd ≈ 29 pM.** Kd is the *dissociation constant* — a measure of how tightly two molecules
  stick together. **Lower means tighter.** Picomolar (pM) is extremely tight; it means that
  even at vanishingly low concentrations, the drug stays attached. For intuition: a weak
  interaction might be micromolar (µM), a millionfold looser.
- **Over $25 billion a year in sales.** This is one of the most commercially and clinically
  successful drugs ever made.

Pembrolizumab is our reference point throughout. It is the answer key: when we build a scoring
system, it has to score pembrolizumab correctly, because we *know* pembrolizumab works.

## 6. How pembrolizumab actually blocks PD-L1 — and by how much

This is where it stops being a cartoon. We measured it.

An **epitope** is the specific patch of surface on a target that a binder actually touches.
Using two published crystal structures — one of pembrolizumab stuck to PD-1, one of PD-L1
stuck to PD-1 — we listed which PD-1 residues each partner contacts.

- **PD-L1's footprint on PD-1: 26 residues.**
- **Pembrolizumab's epitope on PD-1: 27 residues.**
- **Shared: 15 residues.**

So pembrolizumab covers **58% of the PD-L1 site**, not 100%. It does not bury the whole thing
— it parks over a bit more than half, and that is enough to stop PD-L1 docking. Roughly half
of pembrolizumab's own contacts are on adjacent surface that PD-L1 never touches.

**Why this number matters to us:** it turns a weak yes/no question into a calibrated one.
"Does our designed antibody overlap the PD-L1 site?" is nearly meaningless — a single shared
residue would pass. "Does it cover as much of the PD-L1 site as a drug that works in
patients?" has a concrete target: **~58%**.

That is a validation criterion grounded in clinical reality rather than in the competition's
scoring rules — which, notably, never ask whether the molecule blocks anything at all. See
[why we care about checks the rubric doesn't make](Confidence%20Is%20Not%20Truth.md).

## 7. Structures we work from

A **PDB** is the Protein Data Bank, a public archive of experimentally determined 3D protein
structures. Each entry has a four-character code.

| Code | What it is | Why we need it |
|---|---|---|
| **5GGS** | Pembrolizumab bound to PD-1 | The primary reference — our answer key |
| 5DK3 | Pembrolizumab alone | The unbound state for comparison |
| 5IUS | PD-1 bound to PD-L1 | Defines the site we must block |
| 5WT9 | Nivolumab (another approved anti-PD-1 drug) bound to PD-1 | An independent real solution to the same problem |

One caution we hit in practice: **5IUS and 5GGS do not contain the identical PD-1 sequence**
(90.1% identical). Residue numbering therefore cannot be assumed transferable between them —
we had to align the sequences explicitly to map one structure's numbering onto the other's.
See [the traps note](Eight%20Silent%20Failures.md) for why assuming would have been dangerous.

---

**Next:** [what an antibody actually is, and which bit does the binding](Antibody%20Architecture.md).
