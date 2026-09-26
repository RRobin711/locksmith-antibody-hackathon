# Methods and limitations — Challenge 2

## What this design is

`bb_8_0`, a ProteinMPNN sequence on an RFdiffusion/RFantibody backbone conditioned on the
26-residue PD-L1-competitive footprint of PD-1. **All six CDRs are designed;** the
framework is RFantibody's stock humanised trastuzumab scaffold, **unchanged** — VH 86/86
and VL 80/80 framework positions identical to the stock scaffold. §3.2 asks for a complete
VH/VL designed de novo and **this does not meet that**. The rubric does not detect it,
because `cdrh3_identity` reads only CDR-H3 — genuinely novel here at **18.2%
to human germline**, the reference §6.3.1 specifies for Challenge 2. Disclosed rather than
left to be found.

## How it was found, and why that is the finding

This backbone scored ipSAE **0.011** in the original screen. It scores **0.859** here.
**The backbone did not change.** The pilot drew ~3 sequences per backbone; drawing 8 found
this one, clean on the first batch. Across 18 backbones, deeper sampling took 2 to
viability where 1 of 30 sequences had cleared before.

That is the transferable result: **sequence depth per backbone, not backbone diversity,
was the binding constraint** — and establishing it required no new backbones and no rented
hardware.

## The defect that invalidated every earlier Challenge 2 number

Every Challenge 2 fold before 2026-09-23 paired the 123-residue antigen with a cached
alignment whose query is 113 residues. Boltz compares lengths, **discards the alignment**,
substitutes a dummy, and says so only on a stdout stream this code captured and threw
away. Measured 2×2, the mutation is irrelevant and the alignment is the whole effect:

| | antigen MSA used | antigen MSA absent |
|---|---|---|
| previously-submitted design | **0.012** | 0.686 |
| its pre-fix predecessor | **0.012** | 0.773 |

**"1 of 30 clears" was measured in a condition that flatters every design.** Two guards now
prevent it: `write_input` refuses a length-mismatched alignment, and `fold()` raises on the
warning rather than discarding it. For this design the alignment is **positively verified
as used**, not merely unflagged.

## Three checks on a suspiciously good number

A de novo design outscoring real crystals is the exact shape of the artefact above, so
0.859 was checked before it was believed.

**Alignment used.** Processed MSA width 123 = antigen length 123, depth 1024.

**Matched control** — real antibodies, identical construct, alignment, sampling:

| | median ipSAE | viable |
|---|---|---|
| pembrolizumab (licensed anti-PD-1) | **0.877** | 5/5 |
| **`bb_8_0` (this design)** | **0.859** | **5/5** |
| nivolumab (licensed anti-PD-1) | 0.474 | 1/5 |
| trastuzumab (anti-HER2, negative) | **0.057** | 1/5 |

It sits **below** a licensed antibody on its own target and ~15× above an irrelevant one.

**Memorisation.** Highest CDR identity to any known anti-PD-1 is **62.5%**, on CDR-H1 —
which is germline-encoded, and an anti-VEGF antibody (bevacizumab) scores **87.5%** on that
same loop against pembrolizumab. On **CDR-H3**, where novelty lives, this design is
**23.1%** to pembrolizumab — the same as trastuzumab's and more divergent than cetuximab's
38.5%. No drift toward a known binder.

## Two things this run found about the rubric

**An anti-HER2 antibody clears the viability cutoff on one draw of five.** Trastuzumab
against PD-1, correct alignment, handbook construct: samples 0.740 / 0.210 / 0.057 / 0.000
/ 0.000. Its best sample passes §7.2. `diffusion_samples=1` returns an argmax by
construction, so a single-sample run can certify an antibody that cannot bind. **This is
why every number here is a median of five.**

**A licensed anti-PD-1 drug is non-viable on the handbook's own construct.** Nivolumab
scores **0.474** on the specified 123-mer and **0.691** when six N-terminal residues are
restored. Its epitope needs `LDSPDR` (L25–R30); the handbook construct starts at `DSPDRP`
and misses L25. The epitope analysis predicted this before either fold existed.
Pembrolizumab's epitope is 100% inside all constructs, which is why the truncation stayed
invisible for the whole project.

## Liabilities

**Passes §9.2.** No N-glycosylation sequon and no NG/DG motif in any CDR. This was achieved
at *generation* — the sequence was screened before it was folded — not by repairing a
finished design. That distinction is load-bearing: on the design this replaces, all three
prescribed repair routes were measured killing the interface, including one at a residue
with **zero** antigen contacts.

## What we can and cannot claim

**Cannot: that this binds.** ipSAE 0.859 is Boltz's confidence given evolutionary
information about the antigen. Nothing here is an affinity measurement, and this project's
SKEMPI work found no metric in the stack tracks measured ΔΔG.

**Can: that the confidence is calibrated.** Against 40 real crystallised complexes folded
through this identical pipeline, ipSAE tracks pose accuracy at Spearman **ρ = +0.702** with
error rates that **must be quoted at one threshold**. Against DockQ ≥ 0.49 (Medium+) the
ipSAE ≥ 0.60 gate gives **12.5% false-positive / 25.0% false-negative**; against DockQ ≥ 0.23
(Acceptable+) it gives **0% false-positive / 58.3% false-negative**, and that 0% rests on
only 4 negatives — a Clopper–Pearson 95% upper bound of **0.602**, i.e. uninformative. An
earlier version of this document paired the 0% with the 25%, which is the favourable half of
each threshold and is reachable at neither. The post-cutoff (novel-antigen) median is 0.165.

**Can: that the targeting is evidenced.** Backbones were conditioned on the PD-L1
competitive footprint; against 2000 random contiguous surface patches of the same size on
the same chain, 17 of 18 backbones sit at p<0.05 (real epitope 0.712 vs patch 0.154).
