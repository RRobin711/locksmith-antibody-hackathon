# Methods and limitations — LOCKSMITH_DEV, Challenge 2

## What this design is, and what we can support

A complete VH/VL antibody designed **de novo** against PD-1 with RFdiffusion (via
RFantibody), sequence-designed with ProteinMPNN, and folded as a complex with Boltz-2.
It clears all seven §7.2 cutoffs and scores 96.0/100.

**We can support exactly one claim about it, and it is not binding.**

### Supported: the design is aimed at the right epitope

RFdiffusion was conditioned on the 26-residue PD-L1 competitive footprint of PD-1. For
each backbone we recomputed the fraction of the designed interface lying on that
footprint, against **2000 random contiguous surface patches of the same size on the same
chain**: real epitope **0.712**, patch null **0.154**, and **17 of 18 backbones beat
their own null at p<0.05**. This test is deterministic per backbone, so there is no
stopping rule to violate, and it is a control that could have failed.

*Limitation, stated because we measured it:* the null patches are more compact than the
real epitope (RMS spread 7.73 Å vs 10.08 Å), so the null is the right family but is not
shape-matched. That plausibly makes the test anti-conservative by an unquantified amount.

### NOT supported: that this is the best of 30

`interaction_pae` — the only per-design ranking signal the pipeline produced — has
**ICC −0.113 against a detectable floor of 0.317** at n=10 backbones × 3 designs. We
cannot rank these designs. The submitted design was therefore chosen by a rule
**pre-registered before any score existed**: highest hotspot contact count, ties broken
on `frac_iface_on_epitope`. It is *a* design that clears the gates, chosen by a fixed
rule. It is not the best one, and we make no claim that it is.

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
