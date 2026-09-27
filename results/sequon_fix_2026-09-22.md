# Removing the paratope sequons: one fix is free, the other destroys the antibody

> ⚠️ **SUPERSEDED — read before the numbers below.** Every fold in this file comes from
> `runs/sequon_fix`, which ran with the antigen alignment silently discarded. Under a
> correct alignment that design scores **0.012 regardless of its sequence**, so the two
> measurements here are readings of a *condition*, not of a substitution. The
> contact-count rule this file states — that the mutated residue's antigen contact count
> predicts which prescribed fix is safe — is **refuted**; a later arm collapsed the
> interface mutating a residue with zero contacts, and a matched framework control showed
> region, not contact count, is what matters. See
> [the register, §A2 and §B3](retractions.md).

**2026-09-22.** Run against the rule pre-registered in
[the pre-registration](prereg_2026-09-22_sequon_fix.md), written before the folds.

## Result

Both fixes are prescribed by handbook §9 Pillar 4. Both remove the two sequons. They are
not remotely equivalent.

| | mutations | sequons left | §9.2 | ipSAE over 5 diffusion samples | best band | final | viable |
|---|---|---|---|---|---|---|---|
| **baseline** (submitted) | — | 2 | **FAIL** | 0.736 – **0.864** | good | **96.0** | 5/5 |
| **S→A** | H S54A + L S51A | **0** | **PASS** | 0.619 – **0.781** | medium | **91.2** | **5/5** |
| **N→Q** | H N52Q + L N49Q | **0** | **PASS** | **0.013 – 0.014** | poor | 81.6–87.6 | **0/5** |

## N→Q destroys the interface, and that was predictable from the structure

Two conservative point mutations — asparagine to glutamine, one methylene longer, same
amide chemistry — take ipSAE from **0.864 to 0.014**. A **60-fold collapse**, reproducible
to ±0.001 across five independent diffusion samples. This is not noise; it is a dead
interface, consistently.

**We predicted this before running it**, from contact counts on the submitted structure:

| residue | heavy-atom contacts to PD-1 |
|---|---|
| H **N52** | **10** |
| H S54 | **0** |
| L **N49** | **19** |
| L S51 | **0** |

**The glycosylation acceptors are the binding residues.** N52 and N49 carry 29 antigen
contacts between them; the serines that complete the motifs carry none. So the naive
reading of §9 — "N→Q or S→A, pick one" — is actively dangerous here, and the structure
tells you which one in about a minute.

> **Transferable principle.** A developability fix is a *design change*, and prescribed
> fixes are not interchangeable. Before applying one, ask what the residue is doing. Here
> the liability motif and the binding site are the same atom on two different residues, and
> the two textbook remedies differ by a factor of sixty in outcome. "Conservative
> substitution" is a statement about chemistry, not about a particular interface.

## S→A works, and it costs something we should state

All five samples viable, both sequons removed, §9.2 satisfied, and **zero interface
contacts touched by the mutation**. But the envelope drops from 0.736–0.864 to
0.619–0.781:

- the best sample, **0.781, is below the 0.80 Good edge** → ipSAE scores Medium, and the
  composite falls **96.0 → 91.2**;
- the worst sample, **0.619, sits only 0.019 above the §7.2 viability cutoff of 0.60**,
  against the baseline's 0.136 of headroom.

Removing a hydroxyl at a non-contacting position was not free. The most likely reading is
that Ser54/Ser51 were contributing to loop conformation rather than to contacts — the
interface is intact but the model is less sure of it. We did not test that and are not
asserting it.

**The pre-registered rule says submit S→A** (viable on all five, both sequons removed) and
its conditions are met. What the rule did not anticipate is the **4.8-point score cost and
the narrowed margin**. That is a real trade, it is a decision rather than a computation,
and it is recorded here rather than resolved silently.

## The trade, stated plainly

| | baseline | S→A |
|---|---|---|
| rubric score | **96.0** | 91.2 |
| headroom over the viability cutoff | 0.136 | **0.019** |
| paratope N-glycosylation sequons | **2** | **0** |
| handbook §9.2 | FAIL | **PASS** |

Submitting S→A **lowers our score by 4.8 points to remove a liability the rubric does not
measure**. §9.2 asks for it; §5.2 does not pay for it.

Our view: a therapeutic candidate with two glycosylation sequons in the middle of its
paratope is not a candidate, and this project's entire argument is that we do not optimise
a metric we have shown to be gameable. But it changes what is submitted, so it is a
decision for the project owner and not one this script makes.

## What this demonstrates, beyond the two designs

A complete engineering loop inside one session: an outside reviewer found a liability we
shipped → we built the scanner that should have caught it (`metrics/liabilities.py`,
promised in `BUILD.md` and never written) → the scanner immediately found a second
liability in the *other* challenge → we designed two candidate fixes from the structure,
predicted which would survive, and measured both.

The prediction was right and the measurement was cheap: two folds, ~12 minutes.
