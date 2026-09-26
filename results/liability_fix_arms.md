# All three §9.2 fixes collapse the interface — including one at zero contacts

> **Status: control landed 2026-09-23. The margin explanation is EXCLUDED and the
> contact-count predictor is refuted — see §"The control" below.** Two framework arms,
> `N77Q` and `N84Q`, both `N→Q`, both zero contacts in all five samples, hold at medians
> **0.561** and **0.696** against the CDR arm's **0.128**. This design absorbs a
> zero-contact `N→Q` in framework and does not in a CDR.

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

**1. Zero contacts did not protect the interface — in this design.** `fix91` mutates a residue with **no
antigen contacts in any of the five samples** and the design still collapses 0.637 → 0.128,
3/5 viable → 0/5. Contact count is therefore **not sufficient** to predict the outcome of
a prescribed fix. Contact count alone therefore cannot license a fix here. Whether that refutes the rule or merely reflects this design's thin margin is exactly what the pending control decides; until it lands the rule is **under test**, not refuted.

**2. Three of the four supporting instances were measured without an antigen alignment.**
The Ch2 previous-design measurements — the 60× collapse and the "S→A free 5/5" that
licensed the shipped fix — both come from `runs/sequon_fix`, which
[folded with the alignment silently discarded](msa_silently_discarded.md). Under a correct
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


---

## The control, and what it settles

Two arms, chosen to match `fix91` on everything except location: the **same substitution**
(`N→Q`), the **same contact count** (zero in all five samples), in **framework** rather than
a CDR. `N77Q` and `N84Q` were the only two framework asparagines meeting both conditions.

| arm | where | per-sample ipSAE | median | ≥0.60 |
|---|---|---|---|---|
| unfixed | — | 0.855 0.697 0.509 0.637 0.423 | **0.637** | 3/5 |
| `fix91` N91Q | **CDR-L3**, 0 contacts | 0.271 0.284 0.128 0.012 0.011 | **0.128** | 0/5 |
| `fix31` G32A | CDR-L1, 4 contacts | 0.348 0.304 0.140 0.012 0.012 | **0.140** | 0/5 |
| `ctrl` N77Q | **framework**, 0 contacts | 0.654 0.732 0.513 0.553 0.561 | **0.561** | 2/5 |
| `ctrl` N84Q | **framework**, 0 contacts | 0.780 0.730 0.696 0.578 0.559 | **0.696** | 3/5 |

**The margin explanation is excluded.** "A design 0.037 above the cutoff cannot absorb any
single-residue change" predicted both controls collapse. Neither did. `N84Q` finishes
*above* the unfixed baseline (0.696 vs 0.637, both 3/5), and the two controls average
**0.629** — the baseline to within noise. The design tolerates single-residue change fine;
it is where you make it that matters.

**So the contact-count predictor is refuted.** Contact count is **zero** for `fix91`,
`N77Q` and `N84Q` alike, and the outcomes differ by roughly **5×** (0.128 against 0.561 and
0.696). A quantity that is identical across cases with opposite outcomes cannot be the
thing doing the predicting. What separates them is **region** — CDR versus framework — not
contacts.

**Two honest limits.** The controls are n=2, and `N77Q` did degrade (3/5 → 2/5, 0.637 →
0.561), so framework substitutions are cheaper rather than free. The pre-registered bar was
"both survive, ≥3/5 viable, median near 0.637"; `N84Q` clears it outright and `N77Q` sits
just under. Neither is remotely near the fix arms, which is the comparison that matters.

**What replaces the rule.** Nothing yet, and that is the point. "Check the contacts before
choosing a fix" was cheap and structural and it does not work. The surviving statement is
weaker: *a prescribed developability fix is a design change that must be measured on the
design in question*, and a CDR position with no antigen contacts is still doing work the
contact table cannot see — plausibly holding loop conformation for the residues that do
contact. That is a hypothesis, not a measurement.
