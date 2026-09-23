# Methods and limitations — Challenge 2

## What this design is

`bb_1_0_dldesign_0`, one of 30 ProteinMPNN sequences on RFdiffusion/RFantibody backbones conditioned on
the 26-residue PD-L1-competitive footprint of PD-1. **All six CDRs are designed;** the
framework is RFantibody's stock humanised trastuzumab scaffold, **unchanged** — VH 86/86
and VL 80/80 framework positions identical to the stock scaffold. §3.2 asks for a complete
VH/VL designed de novo and **this does not meet that**. The rubric does not detect it,
because `cdrh3_identity` reads only CDR-H3 — genuinely novel here at **33.3% to human
germline**, which is the reference §6.3.1 specifies for Challenge 2 (Challenge 1 compares
to Keytruda instead). Against pembrolizumab's CDR-H3 it is 20.0%, but that is the other
challenge's metric and is noted only to prevent the two numbers being confused.
Disclosed rather than left to be found.

## The defect that invalidated our previous submission

Every Challenge 2 fold this project ran before 2026-09-23 paired the 123-residue antigen
with a cached alignment whose query is 113 residues. Boltz compares lengths, **discards the
alignment**, substitutes a dummy, and announces it only on a stdout stream this code
captured and threw away. Measured 2×2:

| | antigen MSA used | antigen MSA absent |
|---|---|---|
| previously-submitted design | **0.012** | 0.686 |
| its pre-fix predecessor | **0.012** | 0.773 |

The mutation is irrelevant; the alignment is the whole effect. **"1 of 30 clears" was
measured in a condition that flatters every design.** Re-screened under a correct
alignment, the previously-submitted design scores **0.013** and this one — ranked 29th of
30 before — scores **0.637**. Old-vs-new ranking correlation across all 30 is
ρ = +0.366.

Two guards now make the failure impossible to repeat: `write_input` refuses a
length-mismatched alignment, and `fold()` raises on the warning rather than discarding it.

## Known liabilities, unfixed and deliberate

This design **fails handbook §9.2**, carrying two HIGH liabilities in CDRs:

| severity | motif | chain | position | region | contacts to PD-1 (median of 5) |
|---|---|---|---|---|---|
| HIGH | N-glycosylation `NKS` | light | 91 | CDR-L3 | **0** |
| HIGH | deamidation `NG` | light | 31 | CDR-L1 | **13** |

**All three repair routes were measured and all three killed the interface:**

| arm | change | median ipSAE | viable/5 |
|---|---|---|---|
| unfixed (shipped) | — | **0.637** | **3/5** |
| `fix91` | N91Q | 0.128 | 0/5 |
| `fix31` | G32A | 0.140 | 0/5 |
| `fix_both` | N91Q + G32A | 0.034 | 0/5 |

`fix91` mutates a residue with **zero antigen contacts in all five samples** and the design
still collapses. Whether that is residue-specific or simply reflects this design sitting
0.037 above the cutoff — a margin that may absorb no change at all — is
under test with a framework control and is **not** claimed either way here.

So the liabilities ship. A glycosylation site in CDR-L3 is a real developability problem
and we are not pretending otherwise; the alternative was a design that does not bind.

## What we can and cannot claim

**Cannot: that this binds.** ipSAE 0.637 means Boltz places this antibody on
PD-1 with moderate confidence given evolutionary information about the antigen. That is a
statement about a predictor. Nothing here is an affinity measurement, and this project's
SKEMPI work found no metric in the stack tracks measured ΔΔG.

**Can: that the targeting is evidenced.** Backbones were conditioned on the PD-L1
competitive footprint, and against 2000 random contiguous surface patches of the same size
on the same chain, 17 of 18 backbones sit at p<0.05 (real epitope 0.712 vs patch 0.154).

**Calibration.** Against 40 real crystallised antibody–antigen complexes folded through
this identical pipeline, ipSAE tracks pose accuracy at Spearman ρ = +0.702 with a **0%
false-positive rate** — it never accepted a wrong pose — and a **25% false-negative rate**.
The post-cutoff (genuinely novel) median ipSAE in that panel is 0.165.
