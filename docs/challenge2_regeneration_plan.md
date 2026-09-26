# Challenge 2 re-generation — scoped plan, no compute spent

**2026-09-23. Written to be read before anything starts.** Nothing in this document has
been run.

## Why re-generate at all

The existing pool yields **1 viable design in 30** under a correct fold, and that one
([`bb_1_0_dldesign_0`](../results/challenge2_rescreen.md)) sits 0.037 above the viability cutoff with a
worst sample of 0.423. It is a real candidate and it is also the thinnest possible one.

The question is whether the pool is thin because the *backbones* are poor or because the
*selection* was. There is a specific answer, and it is the reason this plan exists.

## What is actually different this time: the filter

The pilot selected backbones on RF2 `interaction_pae`. That quantity was later measured on
this project's own data at **ICC 0.000** (F = 0.70, against a detectable floor of 0.32) and
its poses sat **24.9 Å** from the designed docks. **The pilot screened on noise.** Whatever
survived did so for reasons unrelated to the objective.

Boltz ipSAE under a correct alignment is a different instrument, and it is the one the
40-crystal panel validated this week:

| property | measured | where |
|---|---|---|
| tracks pose accuracy | Spearman **ρ = +0.702** vs DockQ, n=40 | [calibration](../results/calibration.md) |
| accepts a wrong pose | **0%** false positive (0 of 4 incorrect poses passed) | [calibration](../results/calibration.md) |
| rejects a right pose | **25%** false negative (4 of 16 good poses failed) | [calibration](../results/calibration.md) |
| separates cognate from non-cognate | **0.184** ipSAE, positives vs negatives | [negative_control](../results/negative_control.md) |

**This would be the first campaign in which the selection filter and the final score are
the same measured quantity, on an instrument with a published error rate on real
crystals.** That is what the panel licenses, and it is the entire justification for
spending money again. A 25% false-negative rate is the price: we will discard roughly one
good backbone in four. That is acceptable when generation is cheap and evaluation is the
bottleneck, and it is stated here so the yield is not later mistaken for the backbones'
quality.

## Budget, from measured rates only

Pilot, measured: **36 backbones, 5.5 h, $2.82** on a rented RTX 3090 (RFdiffusion →
ProteinMPNN → RF2). Local folding, measured over 64 folds this session: **2.8–3.0 min**
per design at 5 diffusion samples, recycling 10, on the laptop 5070 Ti.

| stage | where | count | rate | wall-clock | cost |
|---|---|---|---|---|---|
| RFdiffusion backbones | rented 3090 | 150 | pilot rate ×4.2 | ~4.5 h | ~$2.30 |
| ProteinMPNN, 4 seqs/backbone | same pod, same session | 600 | minutes | ~0.5 h | — |
| liability + novelty screen | local, CPU | 600 | seconds | ~5 min | $0 |
| **Boltz fold of survivors** | **local GPU** | **~120** | 2.9 min | **~6 h** | **$0** |
| scoring | local, 6 threads | 120 | — | ~15 min | $0 |

**Serial vs overlapped.** The rented stages are strictly serial with each other
(diffusion → MPNN → RF2 filter) and must complete before local folding begins, because the
sequences do not exist until MPNN runs. The **liability screen is free and runs between
them**, which is the point of putting it there. Local folding is the long pole at ~6 h and
overlaps nothing, since it needs the finished sequences and one GPU.

**Total: ~5 h rented (~$2.50) + ~6 h local, across two sessions.** Round to **$3 and a
working day.** The pod is stopped between stages; the pilot's $2.82 is the honest anchor
because it is the same pipeline at a quarter the scale.

**The 120 folded is a budget decision, not a pool size.** 600 sequences enter the free
screen; whatever survives it, capped at 120, is folded. If fewer than 120 survive, fold
fewer.

## Where the correct alignment enters, and the assertion that fails the run

The alignment is `data/msa_cache/pd1_123_handbook.csv` (3407 sequences, query matching the
123-residue handbook antigen exactly). It is built **once**, before any fold, and reused
for every design — re-querying per design would put alignment drift into the ranking,
which is the original reason for caching.

Two guards already exist and both must be on:

1. `write_input` **raises** if the cached query length differs from the antigen
   (`test_write_input_refuses_an_msa_that_boltz_would_discard`).
2. `fold()` **scans captured stdout** and raises on `MSA does not match input sequence`
   (`test_fold_raises_on_a_boltz_warning_that_only_reaches_stdout`).

One more is needed and does not exist yet: **a positive assertion that the alignment was
used**, rather than two guards that fire when it was not. Concretely — after the first
fold of the campaign, read `processed/msa/*.npz`, confirm the stored width equals the
antigen length, and **abort the whole run** if it does not. Absence of a warning is not
evidence of presence; this project has already been wrong in exactly that direction.

## Selection rule, pre-registered

- **Point estimate: median of five diffusion samples.** Not best-of-five. `model_0` is an
  argmax by construction, and on the current 30-design pool a best-of-five reading would
  have called **5 of 30 viable where the median calls 1**.
- **Viability bar: the handbook's §7.2 set**, unchanged, with ipSAE ≥ 0.60 doing the work —
  the negative control showed the other four cutoffs reject 0 of 6 known-wrong antibodies.
- **Rank on ipSAE median**, report the banded composite. Break ties by distance from a band
  edge, not by composite, since three of this candidate's metrics sit within half an edge.
- **Shipped structure is `model_0`** — the model's own top-ranked prediction — with the
  median reported as the central estimate. Both appear in the write-up, in their own
  places.
- No metric is added, removed or re-weighted after seeing the pool.

## The liability screen moves INSIDE selection

`liabilities.py` is sequence-only, costs seconds, and needs no structure. Running it
**post hoc is exactly what produced the current situation**: two designs selected, then
found to carry HIGH CDR liabilities, then a fix attempted under time pressure that
collapsed one interface 60× and left the other needing a judgement call.

So: **every MPNN sequence is scanned before it is folded**, and anything carrying a HIGH
CDR liability is dropped from the pool rather than fixed later. This costs nothing and
removes an entire class of end-stage crisis. On the current pool it would have removed both
the shipped design and the re-screen winner — which is the correct behaviour, not an
argument against it.

Contacts still matter for anything that survives with a MODERATE liability, and the contact
rule now has a sampling axis: **measure contacts across all five samples, never on
`model_0` alone.** On the current candidate `model_0` reads 0 contacts at light 31 where
the five-sample median is 13.

## Targeting, and how it gets evidenced

Hotspot conditioning as in the pilot: the 26-residue PD-L1 competitive footprint of PD-1,
passed as **0-based ordinals within the target chain** (RFdiffusion renumbers continuously
across chains, so residue-number hotspots silently resolve to nothing).

Evidence of targeting is the **contiguous-surface-patch null**, not a conditioned-vs-
unconditioned two-sample test: for each backbone, recompute `frac_iface_on_epitope` against
2000 random contiguous surface patches of the same size on the same chain. The pilot gave
real epitope **0.712** vs patch **0.154**, with **17 of 18** backbones at p<0.05. It is
deterministic per backbone, so there is no stopping rule to violate. A uniform-random
residue null would score 0.231, which is just 26/113 of the chain — the denominator, not a
result.

## What a null looks like, decided in advance

**If the new pool's yield is not better than 1 in 30, that is a result about the method,
not a reason to generate more.** Specifically:

- Yield ≥ 5/120 (~4%) — the filter change worked; the pilot's problem was selection.
- Yield ~1–4/120 (1–3%) — indistinguishable from the current pool at this n. **The
  bottleneck is the backbones, not the screen.** Report it as such and stop.
- Yield 0/120 — stronger version of the same. Report and stop.

In the second and third cases the honest next step is **not** more backbones from the same
generator against the same target. It is either a different generative approach or the
conclusion that de novo anti-PD-1 at this scale is beyond what this pipeline produces —
which is a finding worth writing up, and cheaper than discovering it at 500 backbones.

Sample size note: at n=120 a true yield of 4% gives a 95% CI of roughly 1.6–9%, so this
design **cannot** distinguish 4% from 8%. It can distinguish "roughly as bad as before"
from "several times better", and that is all it is being asked to do.

## What this does NOT fix

**RFantibody's framework is fixed.** Generation runs on its stock humanised trastuzumab
scaffold (`hu-4D5-8_Fv`) and only the CDR loops are designed. Measured on the current
submission: **VH 86/86 and VL 80/80 framework positions identical to the stock scaffold.**

§3.2 asks for a complete VH/VL designed de novo. **This does not meet that, and no number
of backbones changes it**, because the constraint is in the generator rather than in the
sampling. The rubric does not catch it — `cdrh3_identity` reads only CDR-H3, which is
genuinely novel (20.0% to pembrolizumab) — so the gap is invisible to the score and visible
to anyone who reads the sequences.

Stated here so it appears in the plan rather than being discovered in the write-up. The
alternatives are a framework-designing generator or disclosure; this plan assumes
disclosure.

## Order of operations

**Package the current submission first.** Challenge 1 at 96.0 and Challenge 2 at whatever
the §9.2 decision lands on, validated from packaged files alone, zipped, on disk. Nothing
above starts until something shippable exists — the pilot's artefacts were left on a
stopped pod once already.
