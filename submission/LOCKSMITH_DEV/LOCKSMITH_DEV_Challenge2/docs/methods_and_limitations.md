# Methods and limitations — LOCKSMITH_DEV, Challenge 2

## What this design is, and what we can support

A complete VH/VL antibody designed **de novo** against PD-1 with RFdiffusion (via
RFantibody), sequence-designed with ProteinMPNN, and folded as a complex with Boltz-2.
It clears all seven §7.2 cutoffs and scores 91.2/100 as folded and submitted.

**THAT SCORE IS NOT STABLE, and the instability is the most important thing in this
document.** The submitted structure was folded at Boltz `recycling_steps=10`. Re-folding
the identical input at other sampling depths moves the headline metric across a band edge:

| Boltz recycling | ipSAE (seeds) | ipSAE band | composite |
|---|---|---|---|
| 3 | 0.263 / 0.354 / 0.474 | poor | **non-viable** |
| 10 (submitted) | 0.864 / 0.842 / 0.856 | good | **96.0** |
| 20 | 0.795 / 0.883 / 0.731 | medium / good / medium | **93.6 / 96.0 / 93.6** |

Convergence is **non-monotone**, and 96.0 reproduces in one of three recycling-20 seeds.
For contrast, measured on the same machine: a real crystallised complex (pembrolizumab +
PD-1, PDB 5GGS) moves 0.842 → 0.835 → 0.885 across the same depths — a range of 0.050 —
and our Challenge 1 design moves 0.824 → 0.850 → 0.859, a range of 0.036. **This de novo
design swings 0.601, twelve to seventeen times more.** A near-native complex is
essentially invariant in sampling depth; this one is not converged at any depth we tested.

**A second axis, measured the same day and cheaper still.** Boltz's `--diffusion_samples`
defaults to 1, so this and every other pose-derived number here came from a single
diffusion draw. Asking for five (2m54s against ~2m — the MSA, trunk and recycling are
shared, only the diffusion head reruns):

| diffusion sample | 0 (submitted) | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| ipSAE | **0.864** | 0.773 | 0.757 | 0.859 | 0.736 |
| composite | **96.0** | 93.6 | 91.2 | 96.0 | 91.2 |

**Three of five fall to the Medium band.** No sample goes near the 0.60 viability cutoff —
the lowest is 0.736 — so the design is viable under every draw we took. What moves is the
score.

**And the submitted model is the best of the five.** Boltz orders its output by its own
confidence, so `model_0` is the argmax *by construction*. With one diffusion sample you do
not get a draw from the distribution, you get the model's best guess reported as if it
were the estimate. That is true of every pose-derived number in this submission and, we
suspect, of most submissions scored this way.

Read the headline as **91.2–96.0 across diffusion samples and 93.6–96.0 across recycling
depth**, on a design that is viable throughout. The variance is the real result about de
novo design; the score is a point on it.

**We can support exactly one claim about this molecule, and it is not binding.**

### Supported: the design is aimed at the right epitope

RFdiffusion was conditioned on the 26-residue PD-L1 competitive footprint of PD-1. For
each backbone we recomputed the fraction of the designed interface lying on that
footprint, against **2000 random contiguous surface patches of the same size on the same
chain**. Across the 18 conditioned backbones: mean **0.712**, patch null **0.154**, and
**17 of 18 beat their own null at p<0.05**. Deterministic per backbone, so there is no
stopping rule to violate, and a control that could have failed.

**THIS DESIGN SPECIFICALLY — because a pool mean is not a property of one member.**
Its own backbone scores **0.625**, *below* the pool median of 0.684, on 5 of 26 hotspots.
And the number above is measured on the RFdiffusion backbone, not on the Boltz re-dock
that is actually in `structures/`: recomputed on the submitted complex, **0.581 of the
interface lies on the conditioned epitope, contacting 18 of the 26 epitope residues**.
Still far above the 0.154 null, and the honest number to quote for this molecule.

*Limitation, stated because we measured it:* the null patches are more compact than the
real epitope (RMS spread 7.73 Å vs 10.08 Å), so the null is the right family but is not
shape-matched. That plausibly makes the test anti-conservative by an unquantified amount.

### NOT supported: that this is the best of 30

`interaction_pae` — the only per-design ranking signal the pipeline produced — has
**ICC −0.113 against a detectable floor of 0.317** at n=10 backbones × 3 designs. We
cannot rank these designs. A rule was **pre-registered before any score existed** —
highest hotspot contact count, ties broken
on `frac_iface_on_epitope`, applied only to gate-clearing designs.

**The rule was then inapplicable, and we will not pretend otherwise.** Exactly one design
cleared the gates, so the rule sorted a list of length one and made no choice at all.
Worse for us: applied to the pool as a *ranking*, this design's backbone scores 5 hotspot
contacts against a pool mean of 6.33 — **12 of 18 backbones score higher**, and the rule
would have chosen a different one. The accurate statement is not "chosen by a fixed rule"
but: **this is the only design that cleared, and under our own pre-registered key it
would have ranked near the bottom.**

No viable design scored higher on the composite than the one the pre-registered rule selected, so nothing was given up by following it.

### NOT supported: agreement between predictors

RF2 re-predicted these designs and sits a mean **24.87 Å** from the designed dock
(median 28.94 Å). We tested the charitable reading — that this reflects an *unfiltered*
pool failing a standard filter rather than RF2 being unreliable — and it does not hold:
exactly **1 of 30** designs passes the conventional `interaction_pae < 10` filter, and
**that design sits at 32.86 Å**, worse than the median. Model agreement is not evidence
here, and we do not offer it as any.

### NOT supported: binding

Nothing in this submission is evidence that this antibody binds PD-1. On 45 point
mutants with measured ΔΔG (SKEMPI 2.0, 3HFM), **no metric in this stack tracks affinity**
— a mutation that abolishes binding scored ipSAE 0.917 against the wild type's 0.903.
The seven metrics above separate a destroyed interface from an intact one. They do not
rank intact interfaces, and they do not measure binding.

## What is designed, and what is not — scaffold disclosure

**The framework is not ours and is not designed.** This design was produced with
RFantibody, whose stock antibody scaffold is the humanised **4D5-8 (trastuzumab) Fv**.
All six CDRs of BOTH chains were designed de novo onto it; the frameworks were carried
over unchanged. Measured against trastuzumab: **VH framework 86/86 identical, VL
framework 80/80 identical**.

Using a fixed humanised framework is standard practice and is what "de novo antibody
design" operationally means with current tooling — the novelty lives in the CDRs and the
pose. But "designed de novo" without this sentence would let a reader assume more was
designed than was, so the sentence belongs here. It also explains why the humanness and
framework metrics look excellent: they are a marketed antibody's.

## The liability we found, the fix we made, and the one that killed the antibody

The design that cleared the gates carried **two N-linked glycosylation sequons in its
CDRs**, both on antigen-contacting residues — `N52-V53-S54` (CDR-H2) and `N49-A50-S51`
(CDR-L2). Neither exists in the parent scaffold; ProteinMPNN introduced both. Handbook
§9.2: *"No N-glycosylation sequons (N-X-S/T) in Fv region."*

**The submitted design is the fixed one.** What follows is the whole loop, including the
arm that failed.

### The structure said which fix to use, before we folded anything

§9 Pillar 4 prescribes two remedies — `N→Q` or `S→A` — and presents them as
interchangeable. Heavy-atom contacts to PD-1 in the unfixed complex say otherwise:

| residue | contacts to PD-1 |
|---|---|
| H **N52** | **10** |
| H S54 | **0** |
| L **N49** | **19** |
| L S51 | **0** |

**The glycosylation acceptors are the binding residues.** The two asparagines carry 29
antigen contacts between them; the serines completing the motifs carry none.

### Both fixes, measured over five diffusion samples each

| | mutations | sequons | §9.2 | ipSAE range | final | viable |
|---|---|---|---|---|---|---|
| unfixed (first packaged) | — | 2 | FAIL | 0.736 – 0.864 | 96.0 | 5/5 |
| **S→A — SUBMITTED** | H S54A + L S51A | **0** | **PASS** | **0.619 – 0.781** | **91.2** | **5/5** |
| N→Q | H N52Q + L N49Q | 0 | PASS | **0.013 – 0.014** | — | **0/5** |

**`N→Q` collapses ipSAE sixty-fold, reproducibly to ±0.001 across five independent
diffusion samples.** Two of the most conservative substitutions available in protein
engineering — asparagine to glutamine, one methylene longer, identical amide chemistry —
produce a dead interface. We predicted this from the contact table above before folding.

> **The transferable point, and the most useful thing we learned this week:** a
> developability fix is a *design change*, and prescribed fixes are not interchangeable.
> Here the liability motif and the binding site are the same residue, the two textbook
> remedies differ by a factor of **sixty** in outcome, and the structure tells you which
> one in about a minute. "Conservative substitution" is a claim about chemistry, not
> about a particular interface.

### What the fix cost, stated precisely

`S→A` touches zero interface contacts and removes both sequons. It is still not free:

- **Viable in 5 of 5 diffusion samples, with the lowest sample 0.019 above the §7.2
  cutoff** (0.619 vs 0.60). The unfixed design had 0.136 of headroom. Five samples is
  five samples — that margin means a further draw could plausibly land underneath, and
  we have not taken one.
- The best sample, 0.781, falls **below the 0.80 ipSAE Good edge**, so the composite drops
  **96.0 → 91.2**.

**Why the cost is unexplained.** Removing a hydroxyl at a position making *zero* antigen
contacts should not have moved the envelope, and it did — 0.736–0.864 down to 0.619–0.781.
The plausible story is that Ser54 and Ser51 were doing conformational work on the loops
rather than making contacts. **We did not test that and we are not asserting it.** It is
an unexplained cost, recorded as one.

### Why we submitted the lower-scoring design

Submitting `S→A` **costs 4.8 rubric points to remove a liability the rubric does not
measure.** §9.2 asks for it; §5.2 does not pay for it. We think a therapeutic candidate
with two glycosylation sequons in the middle of its paratope is not a candidate, and a
submission arguing that this rubric is gameable should not then optimise it.

The unfixed design, its measurements and its liabilities remain documented above. This
records what we submitted first; it does not replace it.

## Other developability observations

## Novelty

CDR-H3 identity is measured **against human germline** per §6.3.1, not against Keytruda.
CDR-H3 spans the V(D)J junction and the N-region insertions have no germline counterpart
at all, so there is no single string to compare to: the metric is a best-match search
over IGHV/IGHD/IGHJ segments (V as an exact prefix, J as an exact suffix, D as a
substring in any of 3 reading frames). Validated on four derivable cases — a verbatim
germline junction scores 100.0%, and 242 of 249 IGHV alleles return themselves.

**Worth knowing: this gate is free.** Pembrolizumab's own CDR-H3 scores 53.8% to germline
against a <95% cutoff, so no de novo design can plausibly fail it.

## Provenance

Backbones and sequences were generated on a rented RTX 3090 and retrieved to local disk;
**every one of the 258 artefact files is sha256-verified against the server** — see
`results/checksum_pass_2026-09-22.md`. The structure and PAE here were folded locally.
