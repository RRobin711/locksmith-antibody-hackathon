# Pre-registration — calibration panel and negative control

**Written 2026-09-22, before the folds completed.** Two experiments, one shared GPU run.

## Honest disclosure of what was already seen

One complex, **7ZOZ** (post-cutoff arm), was folded and scored first as a *timing test* to
size the GPU budget before committing to the full run. Its numbers were therefore visible
when this document was written: median ipSAE **0.015**, DockQ **0.377**, 59–86 contacts,
interface pLDDT 76–78. Nothing else had been folded.

This matters and is stated rather than buried, because a pre-registration written after
seeing part of the data is a weaker instrument than one written before. Concretely: the
decision rules below could have been chosen to suit that one observation. The mitigations
are that 7ZOZ is 1 of 40, that it is not in the negative-control experiment at all, and
that the thresholds used (0.60 ipSAE, 0.23/0.49/0.80 DockQ) are **pre-existing** — they
come from handbook §7.2 and the CAPRI convention, not from anything chosen tonight.

---

## Experiment A — negative control

**Question.** Does the §7.2 viability gate distinguish a cognate antibody–antigen pair
from a non-cognate one, or does it merely register that two proteins were placed adjacent?

**Design.** Eight folds. Identical antigen (the exact 113-residue PD-1 construct every
design in this project was folded against), identical cached MSA
(`data/msa_cache/pd1_5ggs.csv`, 3787 sequences), identical flags, `recycling_steps=10`,
`diffusion_samples=5`. The only variable across rows is which antibody Fv is present.

| arm | antibodies | expectation |
|---|---|---|
| negative (n=6) | HyHEL-10, trastuzumab, bevacizumab, cetuximab, CR9114, BO2C11 | FAIL the gate |
| positive (n=2) | pembrolizumab, nivolumab | PASS the gate |

**Point estimate.** Median ipSAE across the five diffusion samples. Fixed now because
`diffusion_samples=1` reports an argmax, and choosing max-vs-median after seeing the data
would be the same error this project has already made.

**Decision rules, fixed in advance.**

1. **If both positives clear ipSAE ≥ 0.60 and all six negatives fall below it** — the gate
   discriminates cognate from non-cognate. Report the margin between the arms.
2. **If any negative clears 0.60** — the gate does not measure binding. Report this as a
   failure of the rubric, name the antibody, and state plainly that every ipSAE-derived
   claim in the submission inherits the weakness.
3. **If either positive fails 0.60** — the pipeline is broken for this construct and the
   negative arm is *uninterpretable*, not reassuring. This project has already published a
   "0/30 viable" that was the sampler's floor rather than a finding; a uniform result with
   no working positive is exactly that error. In this case report the control as
   inconclusive and do not use the negatives as evidence for anything.

**What this cannot establish, stated in advance.** Passing shows the metric separates
cognate from non-cognate. It says nothing about whether it *ranks* correctly among
plausible designs — this project has already measured that failing (ipSAE wandered within
±0.04 while DockQ fell 0.820 → 0.601). Discrimination and ranking are different properties.

---

## Experiment B — calibration panel

**Question.** Where do this submission's numbers sit in the distribution of real
antibody–antigen complexes folded by the same pipeline?

**Design.** 40 complexes, 20 either side of Boltz-2's **2023-06-01 release-date** cutoff,
drawn by one RCSB query sorted by release date and taken nearest the cutoff on each side,
so that era, resolution practice and target fashion are matched and the cutoff is the only
systematic difference. Filters: ≥3 protein entities, resolution ≤ 3.0 Å, deduplicated on
antigen sequence. Constructs are Fv+Fv+antigen, antigen rebuilt from SEQRES and trimmed to
the resolved span. `recycling_steps=10`, `diffusion_samples=5`, antigen MSA from the public
server (every sequence is already public in the PDB; no disclosure issue).

**Primary readout.** For each of `ipsae, dockq, dg, contacts, iface_plddt, cdr_sasa`, the
percentile of each submitted design within the **post-cutoff** arm. The pre-cutoff arm is
reported as a ceiling, not as the comparison.

**Secondary.** Mann–Whitney U between arms on each metric, to quantify how much
memorisation is worth.

**Power, stated before the fact so a null is interpretable.** At n=20 per arm,
Mann–Whitney has roughly 80% power to detect a rank-biserial correlation of about 0.6
(a large effect). **A null result here means "no effect larger than large", not "no
effect".** This project has four times reported an underpowered null as a finding; the
detectable effect is therefore stated up front, and any null will be reported with it.

**Percentile caveat, fixed in advance.** With n=20, a percentile has a resolution of 5
points and a 95% CI of roughly ±20 points near the median. Percentiles will be reported as
ranks ("3rd of 20"), never as a bare decimal implying precision the sample size does not
support.

**Expected failure mode to watch for.** If a large fraction of the post-cutoff arm scores
near the ipSAE floor (as 7ZOZ did), the honest conclusion is about the metric, not about
the designs — and the check is whether DockQ and contact count agree. A complex with a
real interface (contacts > 40, DockQ > 0.23) and ipSAE ≈ 0 is evidence the gate is
mis-scaled, not evidence the crystal is wrong.
