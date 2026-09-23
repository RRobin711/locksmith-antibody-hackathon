# All three §9.2 fixes collapse the interface — including one at zero contacts

**2026-09-23.** Three arms, folded under `pd1_123_handbook.csv`, recycling 10, five
diffusion samples, seed 1 — identical to the re-screen in every respect except the
substitution. The unfixed design stayed on disk throughout, so nothing here could cost it.

## Result

| arm | change | contacts on the mutated residue | per-sample ipSAE | median | viable/5 |
|---|---|---|---|---|---|
| **unfixed** | — | — | 0.855 0.697 0.509 0.637 0.423 | **0.637** | **3/5** |
| `fix91` | N91Q | **0** (all five samples) | 0.271 0.284 0.128 0.012 0.011 | **0.128** | **0/5** |
| `fix31` | G32A | 4 (median) | 0.348 0.304 0.140 0.012 0.012 | **0.140** | **0/5** |
| `fix_both` | N91Q + G32A | 0 and 4 | 0.341 0.042 0.034 0.012 0.011 | **0.034** | **0/5** |

NetSolP is **0.617 for every arm** — none of the substitutions touched solubility, so the
collapse is entirely on the interface side.

**Pre-registered decision rule applied:** `fix_both` fails (0/5) → check `fix91` → `fix91`
also fails → **ship the unfixed design with both liabilities disclosed.** That is the rule
as written before the folds, and it is followed.

## The finding: the contact rule does not hold, and its evidence base was contaminated

The rule this project has been operating under is *"the contact count on the mutated
residue predicts whether a prescribed fix survives"*, resting on four instances:

| design | substitution | contacts | outcome | alignment |
|---|---|---|---|---|
| Ch2 previous | N→Q (heavy 52, light 49) | 10, 19 | fatal, 0.864 → 0.014 | **none — discarded** |
| Ch2 previous | S→A | 0 | free, viable 5/5 | **none — discarded** |
| Ch1 | N55Q | 3 | free, 96.0 → 96.0 | correct (server) |
| **Ch2 candidate (new)** | **N91Q** | **0** | **fatal, 0.637 → 0.128** | **correct** |

Two things follow and both matter.

**1. Zero contacts did not protect the interface.** `fix91` mutates a residue with **no
antigen contacts in any of the five samples** and the design still collapses 0.637 → 0.128,
3/5 viable → 0/5. Contact count is therefore **not sufficient** to predict the outcome of
a prescribed fix. The rule is refuted as a decision procedure, not merely qualified.

**2. Three of the four supporting instances were measured without an antigen alignment.**
The Ch2 previous-design measurements — the 60× collapse and the "S→A free 5/5" that
licensed the shipped fix — both come from `runs/sequon_fix`, which
[[msa_silently_discarded|folded with the alignment silently discarded]]. Under a correct
alignment that same design scores **0.012** whatever its sequence. So those two instances
cannot support any rule about mutations; they are two readings of a condition, not two
readings of a substitution.

**What survives is one valid instance either way**: Ch1's `N55Q` free at 3 contacts, and
this design's `N91Q` fatal at 0. Under correct alignments the rule does not even hold in
direction.

## The more parsimonious explanation, offered against my own finding

A marginal design may simply be unable to absorb any single-residue change. The unfixed
candidate sits at ipSAE **0.637 against a 0.60 cutoff** — 0.037 of margin — with its worst
sample already at 0.423 and three metrics within half a band edge. A design that close to a
cliff plausibly falls off under *any* perturbation, regardless of where it is made.

That reading is consistent with everything here: all three arms collapse to roughly the
same place (medians 0.128, 0.140, 0.034) rather than the double mutant being twice as bad
as either single, which is what independent per-residue damage would look like. It is also
consistent with Ch1's `N55Q` being free — Ch1 sits at ipSAE 0.821, far from its edge.

**These two explanations are not distinguished by the data in hand.** Distinguishing them
needs a fix applied to a design with comfortable margin under a correct alignment, and no
such design exists in this pool. Stated as unresolved rather than resolved in favour of the
more interesting reading.

## What this means for the submission

- Challenge 2 ships **unfixed**, carrying two HIGH CDR liabilities: N-glycosylation `NKS`
  at light 91 (CDR-L3) and deamidation `NG` at light 31 (CDR-L1). Both are disclosed in
  the package docs and on the deck.
- It is viable on **3 of 5** diffusion samples, not 5 of 5. No "viable throughout" language
  survives from the previous design.
- The shipped structure is `model_0` — the model's own top-ranked prediction — carrying
  ipSAE 0.855 and composite 90.0, with **median 0.637 / 91.2 reported as the central
  estimate** wherever the number appears.

## Cost

Three folds, 8.6 minutes, on a design that was never at risk. The information — that a
zero-contact substitution can collapse an interface, and that three of the rule's four
instances are unusable — is worth considerably more than the fix would have been.
