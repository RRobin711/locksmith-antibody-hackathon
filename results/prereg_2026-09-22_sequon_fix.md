# PRE-REGISTERED: removing the two paratope glycosylation sequons

**Written 2026-09-22 BEFORE the folds ran.**

## The problem

The submitted Challenge 2 design carries two N-linked glycosylation sequons in its CDRs —
`N52-V53-S54` (CDR-H2) and `N49-A50-S51` (CDR-L2). Handbook §9.2 lists *"No
N-glycosylation sequons (N-X-S/T) in Fv region"* as a checklist item. §9 Pillar 4 gives
two prescribed fixes: **N→Q** or **S→A**.

## The structural fact that decides which to try

Measured on the submitted complex, heavy-atom contacts to PD-1 within 4.5 Å:

| residue | contacts |
|---|---|
| **H N52** | **10** |
| H V53 | 0 |
| **H S54** | **0** |
| **L N49** | **19** |
| L A50 | 0 |
| **L S51** | **0** |

**The asparagines carry 29 contacts between them; the serines carry none.** So `S→A`
removes the sequon without touching a single interface contact, while `N→Q` mutates the
two most contact-rich residues in the motif.

This is not a coincidence worth glossing: the glycosylation acceptor is the residue doing
the binding, which is exactly why the liability is worth removing and exactly why the
naive fix is the dangerous one.

## Arms

Both folded at the submitted settings (Fv, recycling 10, seed 1, cached PD-1 MSA) with
**`diffusion_samples=5`**, because we established earlier today that `model_0` is an argmax
by construction — so these are compared on **envelopes, not points**.

| arm | mutations | rationale |
|---|---|---|
| **SA** | H S54A + L S51A | removes both sequons, touches zero interface contacts |
| **NQ** | H N52Q + L N49Q | the other prescribed fix; mutates 29 contacts' worth of residue |
| baseline | none | the submitted design, already measured: ipSAE 0.736–0.864 over 5 samples |

## Predictions

- **SA: essentially free.** ipSAE envelope overlapping the baseline's 0.736–0.864; all
  seven gates clear; both sequons gone. Ser→Ala at a non-contacting position removes a
  hydroxyl and nothing else.
- **NQ: the risky arm.** Gln is one methylene longer than Asn and a weaker H-bond donor
  geometry at the same position. I expect a measurable drop and would not be surprised by
  a gate failure. If it survives, that is informative about how forgiving the interface is.

## Decision rule, fixed in advance

1. **If SA clears all seven §7.2 cutoffs across all five diffusion samples** → **submit
   SA.** It is strictly better than the shipped design: same interface, one fewer
   handbook violation, no liability.
2. **If SA fails and NQ clears** → submit NQ, and report that the fix cost interface
   contacts.
3. **If both fail** → keep the original, and report that **the liability is not removable
   without losing the design** — that the glycosylation acceptor and the binding residue
   are the same atom. That is a real and publishable finding about this design, not a
   failure of the exercise.
4. **If either arm's envelope is wider than the baseline's**, say so; a fix that buys
   compliance at the cost of stability is not obviously a fix.

The original design and its liabilities stay documented in the package either way. We are
not deleting the record of what we submitted first.
