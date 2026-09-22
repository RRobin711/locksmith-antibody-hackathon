# Pre-registration — what does the rubric's novelty metric actually measure?

**Written 2026-09-20 ~01:30, before `runs/novelty_probe/` exists.** Designs already
generated and frozen in `designs/novelty_probe/designs.json` (42 designs); fold script
`scripts/44_novelty_probe_fold.py`; generation `scripts/43_novelty_probe_generate.py`.

## 1. The observation

Pembrolizumab's CDR-H3 is `ARRDYRFDMGFDY` (13 aa). Its antigen contacts in the 5GGS
crystal (heavy-atom pairs ≤ 5.0 Å) are extremely unequal:

| zero / near-zero | contacts | | paratope | contacts |
|---|---|---|---|---|
| 95 A | 0 | | 97 R | 23 |
| 96 R | 0 | | 103 M | 29 |
| 98 D | 0 | | 99 Y | 42 |
| 104 G | 0 | | 101 F | 52 |
| 105 F | 0 | | 100 R | 81 |
| 107 Y | 0 | | | |
| 106 D | 3 | | | |
| 102 D | 6 | | | |

**Six of thirteen positions touch the antigen not at all.** The rubric scores novelty
as CDR-H3 sequence identity to the parent, banded: `< 70%` is Good, and at 13 residues
that is 4 substitutions. All four can come from the zero-contact set.

## 2. The three arms

Only the listed CDR-H3 positions are redesigned; H1, H2, the rest of the heavy chain,
the whole light chain and the antigen are held native, so the paratope is the only
thing that varies between arms. The native residue is **forbidden** at each designed
position (`--omit_AA_jsonl`), which makes identity exact by construction.

| arm | positions redesigned | contacts touched | CDR-H3 identity | novelty band | n |
|---|---|---|---|---|---|
| **A** | 95, 96, 98, 104 | **0** | **69.2%** | Good | 14 |
| **B** | 95, 96, 98, 104, 105, 107 | **0** | **53.8%** | Good | 14 |
| **C** | 97, 99, 100, 101, 103, 106 | **227** | **53.8%** | Good | 14 |

**B and C are identical on the scored axis** — same metric, same band, same sub-score,
same contribution to `final` — and differ by 227 antigen contacts in what they may
change. Verified in the generation log: both arms return `cdrh3_identity [53.8]`, a
single value, for all 14 designs.

## 3. Hypotheses

- **H1.** Arms A and B retain the pose: mean DockQ ≥ **0.78**, against the 239-design
  pool's mean of 0.705 and max of 0.777, and approaching the pembrolizumab self-refold
  at 0.818.
- **H2 (the one that matters).** Arm C loses it: mean DockQ at least **0.10** below arm
  B. B and C are matched on novelty, so any difference is invisible to the scored
  novelty metric.
- **H3.** Arm A or B reaches DockQ ≥ **0.80**, moving that metric from Medium to Good
  and `final` from 87.5 to 90.0 — demonstrating that the one reachable rubric point
  (NetSolP's being pinned; see [[rubric_headroom|the headroom audit]]) is claimable
  without touching the paratope.
- **H4.** `cdrh3_identity` is, by construction, unable to separate B from C. Stated as a
  prediction so that the result is a measurement rather than a tautology: the point is
  not that a constant is constant, it is **how large the DockQ difference is that the
  constant conceals.**

**Statistics:** arm means with bootstrap 95% CIs (10,000 resamples over designs);
Mann–Whitney U for B vs C, which is the pre-specified primary comparison. One seed per
design: the SE of an arm mean over 14 designs at DockQ seed sd 0.018 is 0.005, and the
effect sought is of order 0.1, so seeds would buy precision the comparison does not
need while breadth guards against one odd design carrying the arm.

## 4. What each outcome means

| outcome | reading |
|---|---|
| H1 and H2 both hold | The novelty metric measures **sequence distance, not interface novelty**. A design can max the novelty band while leaving the paratope untouched, and the rubric cannot tell that from one that destroys it. This is the novelty analogue of the pLDDT/ensemble finding. |
| H2 fails — C retains the pose too | Boltz is insensitive to paratope identity on this complex, which is a finding about the *predictor* and would undercut DockQ as evidence of anything. Would need saying loudly. |
| H1 fails — A and B lose the pose too | Even zero-contact CDR-H3 substitutions disrupt the prediction, so the loop's conformation is sequence-sensitive well beyond its contacts. Interesting, and it would weaken the "free novelty" reading. |
| H3 holds | The +2.5 rubric points are reachable. **They are reported, not banked** — see §5. |

## 5. The declaration that has to come with this

**These are rubric probes, not design candidates, and no arm-A or arm-B design will be
proposed as "our design".** An arm-A molecule is a near-copy of pembrolizumab with four
substitutions at positions that touch nothing; submitting it because it scores well
would be gaming a metric that this very experiment is demonstrating to be gameable, and
the project's entire position is that its numbers should correspond to something real.
The deliverable here is a **measurement about the rubric**.

M3 is closed and `mpnn_T0.5_s104_036` remains the named design regardless of what any
arm scores. If a probe outscores it, that fact is reported as evidence about the
rubric, not acted on.

## 6. Note for Challenge 2

Challenge 2 has **no DockQ** — the binding mean is over five metrics, none of which
compares against a reference structure. Whatever difference this experiment finds
between B and C, nothing in the Challenge 2 rubric could detect it at all. That is
worth one sentence in any writeup about what the scoring geometry rewards.
