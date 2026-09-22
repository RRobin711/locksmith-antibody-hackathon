# What RF2 actually gives you to filter on — 2026-09-21

**Resolved without re-running anything: RF2 writes its metrics as `SCORE` lines directly
into each output PDB.** The Quiver path (`--output-quiver`) *strips* them from the PDB and
repacks them into the quiver score string (`model_runner.py:216-227`); the directory path
leaves them in place (`pose_to_remarked_pdblines(pose, metrics=metrics)`, line 215). So
directory I/O is not scoreless — my earlier "RF2 emitted no readable score" was wrong,
and wrong for a familiar reason: I grepped the PDB with `| head -12` and the REMARK block
filled the window before any SCORE line. **Third truncation error of the day.**

## The three metrics, and which one is real

Four designs, all from the SAME backbone (`gate0b_0`), 10 recycles:

| design | `interaction_pae` | `pae` | `pred_lddt` |
|---|---|---|---|
| dldesign_0 | 14.42 | 7.66 | 0.92 |
| dldesign_1 | 14.70 | 7.93 | 0.91 |
| dldesign_2 | 15.84 | 8.46 | 0.91 |
| dldesign_3 | 14.61 | 7.87 | 0.91 |
| **range** | **1.42** | 0.80 | **0.01** |

**`pred_lddt` does not discriminate.** It is flat to 0.01 across four different sequences
and would pass any "are scores present?" check while carrying no information — the same
failure shape as 26/26 residues mapping against the wrong chain, and the same shape as
`contacts` (ICC 0.003) and `cdr_sasa` (ICC 0.000) in the Challenge 1 audit. It is also the
metric whose name most invites use.

**`interaction_pae` moves** (14.42-15.84) and is the defensible filter key: it is the
predicted aligned error restricted to inter-chain residue pairs
(`metrics["interaction_pae"] = pae[0, ~pose.same_chain].mean()`, line 158-159), i.e. it
asks specifically how confident RF2 is about the *interface*, which is the thing being
designed. Lower is better.

## What is NOT established

These four designs share one dock. The spread above is **within-backbone only**. A filter
has to separate *backbones*, and that requires the between-backbone variance, which is
unmeasured at N=1. The honest statement today is:

> `interaction_pae` varies across sequences on a fixed dock; `pred_lddt` does not.
> Whether `interaction_pae` separates good docks from bad ones is **untested**.

The production run must therefore record, for every design row, the **backbone ID it came
from**, so the within- and between-backbone components can be separated afterwards. That
identity cannot be reconstructed later -- it has to be stamped at generation time.

## Consequence for the pass-rate estimate

A "pass rate" over N x 4 designs treats 4 designs sharing a dock as independent. They are
not. At N=100 backbones the design-level n is 400 but the effective n is somewhere between
100 and 400 depending on the intra-backbone correlation, so a CI computed on 400 is
**falsely narrow by up to ~2x**. The pre-registration must state which rate is being
quoted: **backbone-level** (a backbone passes if any of its 4 designs does) or
design-level with a clustered CI.

---

# The conditioning check — built, and it caught two of my own bugs

`pod/check_backbone.py` answers the only question that detects silent mis-conditioning:
**do the designed CDR loops actually touch the 26 hotspot residues?** Deterministic,
usable at n=1, and therefore the primary instrument — the conditioned-vs-unconditioned
arm comparison is a two-sample test with poor power at the n a pilot affords.

## Two bugs it exposed in its own first version, both false-NEGATIVE

1. **RFdiffusion RENUMBERS its output continuously across chains.** Measured on
   `gate0b_0.pdb`: **H = 1-115, L = 116-219, T = 220-332**, where the input PD-1 was
   numbered 31-143. Matching hotspots on residue *number* therefore finds nothing, and
   the check reported **"zero hotspot contacts"** for a perfectly good dock. That false
   negative would have rejected **every backbone in the production run**.
   Fix: hotspots are passed as **0-based ordinal positions within the target chain**,
   which survive any renumbering.
2. **The CDR loop REMARKs are 1-indexed ABSOLUTE indices across the whole file**, not
   per-chain residue numbers — the README says so and the first version ignored it.
   Observed range 26-209 over 332 residues.

Both failures were silent and both looked exactly like a scientific result
("conditioning isn't working") rather than a parsing error. Checked against geometry
before believing it: min distance antibody->target is **3.38 A**, and loops->target is
the *same* 3.38 A, so the loops are the contact surface — the dock was always fine.

## What it measures, on the one backbone we have

| structure | iface residues | hotspots contacted | frac of interface on epitope |
|---|---|---|---|
| RFdiffusion backbone | 8 | 4 / 26 | **0.500** |
| RF2 `dldesign_0` | 18 | 13 | **0.722** |
| RF2 `dldesign_1` | 11 | 5 | 0.455 |
| RF2 `dldesign_2` | 30 | 16 | 0.533 |
| RF2 `dldesign_3` | 15 | 8 | 0.533 |

**Conditioning works.** Half the diffused dock's interface lands on the PD-L1 footprint,
and RF2 refinement grows the interface (8 -> 11-30 residues) while raising hotspot
contact (4 -> 5-16), which is what a coarse backbone becoming a real side-chain-resolved
complex should do.

**`frac_iface_on_epitope` is a second discriminating axis, and it is NOT `interaction_pae`.**
`dldesign_2` has the *worst* interaction_pae (15.84) but the largest interface (30) and
most hotspot contacts (16); `dldesign_0` has the *best* interaction_pae (14.42) at 72%
on-epitope. Confidence in the interface and correctness of its location are separate
questions — which is the whole lesson of the Challenge 1 audit restated on new data.
Both belong in the run's output table; neither should be collapsed into the other.
