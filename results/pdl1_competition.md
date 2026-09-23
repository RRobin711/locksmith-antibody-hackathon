# Does either design block PD-L1?

**2026-09-22.** Every metric in the rubric asks whether the antibody binds PD-1. None asks whether it does the job. An anti-PD-1 antibody is a checkpoint inhibitor: its mechanism is occluding the PD-L1 site. **An antibody that binds PD-1 confidently on the wrong face scores identically on all eight metrics and is worthless.** We had never checked.

Method: superpose each design's PD-1 onto PDB **5IUS** (PD-1/PD-L1), carry the Fv with it, then measure the overlap with PD-L1. Clash = 3.0 Å heavy-atom (below the van der Waals sum, so the two cannot coexist); contact = 4.5 Å. In 5IUS, PD-L1 contributes **18** interface residues and PD-1 **23**.

| challenge | superposed on | CA RMSD | Fv↔PD-L1 clashes (<3 Å) | PD-L1 footprint occluded | PD-1 epitope shared with PD-L1 |
|---|---|---|---|---|---|
| **Challenge 1** | 106 PD-1 residues | 1.80 Å | **2007** | **16/18 (89%)** | 7 residues |
| **Challenge 2** | 106 PD-1 residues | 1.79 Å | **4522** | **17/18 (94%)** | 9 residues |

- **Challenge 1: **blocks PD-L1**.** 2007 atomic clashes with PD-L1 and 16 of 18 PD-L1 interface residues occluded (88.9%). Its own PD-1 epitope is 23 residues, 7 of them shared with PD-L1's.
- **Challenge 2: **blocks PD-L1**.** 4522 atomic clashes with PD-L1 and 17 of 18 PD-L1 interface residues occluded (94.4%). Its own PD-1 epitope is 25 residues, 9 of them shared with PD-L1's.

## What this does and does not establish

**Does:** whether the *predicted* pose is geometrically incompatible with PD-L1 binding. That is the therapeutic mechanism of a checkpoint inhibitor, and it is not measured anywhere in the rubric.

**Does not:** that the design binds at all. This analysis takes the predicted pose as given; if the pose is wrong the competition result is wrong with it. It is a conditional statement — *if* it binds as predicted, *then* it blocks — and the antecedent is exactly what this project has spent a week failing to establish.

**Also does not** account for PD-1's own glycosylation (N49/N58/N74/N116 in vivo, modelled bare here) or for conformational change on binding. Both are rigid-body approximations and both could change the answer at the margin.
