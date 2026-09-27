# Challenge 2: **1 of 30 designs clears every §7.2 cutoff** (provisional)

> ⚠️ **SUPERSEDED.** "1 of 30 designs clears" and `bb_2_0_dldesign_1` scoring 96.0 were
> both measured with the antigen alignment silently discarded. Under a correct alignment
> that design scores **0.013** and ranks last; the shipped Challenge 2 design is
> **`bb_8_0`** at composite **93.6**. See [the register, §A2](retractions.md).

**2026-09-22 — PROVISIONAL, corrected after adversarial review.** All 30 RFantibody designs folded with Boltz-2 at
`recycling_steps=10`, seed 1, against the handbook's §4.2.2 antigen (30/30 successful) and
scored on the seven metrics §7.2 applies to Challenge 2.

> ### ⚠ This supersedes an earlier `0/30` result from the same night
> The first pass folded at `recycling_steps=3` and returned **0 of 30**, all failing
> ipSAE. That was an **under-sampling artefact** and is withdrawn. See §4.

## The result

**`bb_2_0_dldesign_1` is viable and scores 96.0 / 100**, re-derived by the artefact-only
validator from the packaged files alone:

| metric | value | band | sub-score |
|---|---|---|---|
| `ipsae` | **0.864** | good | 10.0 |
| `dg` | −12.400 | good | 10.0 |
| `contacts` | 98.000 | good | 10.0 |
| `iface_plddt` | 83.580 | good | 10.0 |
| `cdr_sasa` | 1066.900 | good | 10.0 |
| `cdrh3_identity` (**to germline**) | 30.000 | good | 10.0 |
| `netsolp` | 0.562 | medium | 8.0 |

Categories: binding 10.000, developability 8.000, novelty 10.000. **VIABLE: True.**

The remaining 29 all fail on `ipsae` and nothing else, range **0.000 – 0.331**.

## The distribution is bimodal, and that is the interesting part

| | ipSAE |
|---|---|
| `bb_2_0_dldesign_1` | **0.864** |
| `bb_4_0_dldesign_2` (2nd) | 0.331 |
| `bb_9_0_dldesign_1` (3rd) | 0.311 |
| everything else | ≤ 0.161 |
| gate | 0.600 |
| **positive control** (wild-type pembrolizumab Fv, identical pipeline) | **0.842** |

**CORRECTED 2026-09-22 after adversarial review. The bimodality claim was wrong twice.**

First, factually: this table previously read "everything else ≤ 0.161", which is false —
`bb_9_0_dldesign_1` scores **0.311**. It was omitted because it never entered the
top-5 reseed set, having been selected by the recycling-3 ranking we had just declared
misleading.

Second, and more seriously: **the gap is an artefact of ipSAE's hard PAE < 10 Å cutoff,
not a property of the designs.** Reading Boltz's own `confidence_*.json` — which nobody
here had opened — the same 30 designs show:

| | top | 2nd | median | min |
|---|---|---|---|---|
| ipSAE | 0.864 | 0.331 | **0.000** | 0.000 |
| ipTM | 0.950 | 0.863 | **0.664** | 0.556 |

The 15 designs sitting at ipSAE *exactly* 0.000 carry ipTM **0.556–0.674** — ordinary
low-moderate interface confidence, not "no placement at all". ipSAE floors at zero and
manufactures a discontinuity the underlying model does not have. Largest-gap ratio: 3.56
on ipSAE, 2.12 on ipTM. **The winner is the top of a continuum, not a separate mode**, and
the earlier sentence "twenty-nine it will not place at all" was a statement about the
metric, not about the molecules.

## The failure mode that produced `0/30`, and why it matters

`recycling_steps` was inherited from Challenge 1's fold settings and never re-examined.
Re-folding the top 5 at recycling 10 (`scripts/78_challenge2_reseed.py`):

| design | recycling 3, seed 1 | recycling 10, seeds 1 / 2 / 3 |
|---|---|---|
| `bb_2_0_dldesign_1` | 0.263 | **0.864 / 0.842 / 0.856** |
| `bb_4_0_dldesign_2` | 0.372 | 0.331 / 0.416 / 0.361 |
| `bb_6_0_dldesign_2` | 0.242 | 0.011 / 0.267 / 0.105 |
| `bb_4_0_dldesign_0` | 0.235 | 0.000 / 0.000 / 0.000 |
| `bb_7_0_dldesign_1` | 0.234 | 0.161 / 0.169 / 0.000 |

**Extra recycling does not lift the pool — it resolves it.** Four of five moved sideways
or down; one moved decisively and reproducibly across three seeds. At recycling 3 the pool
was too under-converged to distinguish a design that works from one that does not, and the
ranking was actively misleading: **the design that clears was ranked 2nd, and the one
ranked 1st still fails.**

> **Transferable principle, CORRECTED.** The original version of this box said extra
> recycling "resolves" the pool. **The pool data does not support that.** At recycling 3:
> mean 0.0640, median 0.0056, **15/30 at exactly zero**. At recycling 10: mean 0.0646,
> median 0.0050, **still 15/30 at exactly zero**. The distribution is unchanged; one
> design moved. The r3↔r10 rank correlation is only **0.432**, so the ranking is not
> stable either — `bb_9_0_dldesign_1` went from rank 29 to rank 3.
>
> The tell we cited for under-sampling (a pile-up at zero) **applies identically at
> recycling 10**, so by our own criterion we have not demonstrated convergence at the
> depth we submitted. What survives is narrower and still worth having: **check
> convergence before interpreting a unanimous failure — and "it changed when I sampled
> harder" is not the same as "it has now converged."**

## What the positive control did and did not do

`results/challenge2_positive_control.md`: wild-type pembrolizumab through the identical
call scored **Fab 0.776, Fv 0.842**, clearing pre-registered bars of ≥0.75 and ≥0.60. It
correctly exonerated the **Fv construct** — a well-grounded hypothesis, since `PLAN.md`
G1c failed on *"Fv ipSAE reliability 0.61 vs Fab 0.96, Fab-only adopted"* and Challenge 2
was folded as Fv without revisiting that.

**And it was blind to the real problem, because it ran at recycling 3 as well.** It printed
a verdict — *"0/30 is a real property of the designs"* — that was wrong within the hour.

> **A control eliminates the confound you thought of. It is silent on the one you did
> not, and a passing control can read as general reassurance when it is nothing of the
> kind.** The control's *numbers* are sound and its *construct finding* stands; only its
> verdict about Challenge 2 was wrong.

## What this establishes

**Does:** one de novo design produces a complex Boltz-2 places with high confidence, and
it clears all seven hard cutoffs. The conditioning demonstrably worked (17/18 backbones
beat a contiguous-patch null). The pipeline runs end to end and the gate machinery,
packager guard and validator all behave.

**Does not establish binding.** ipSAE is Boltz-2's uncertainty about chain placement.
`results/skempi_validity.md` shows this stack does not track measured affinity in either
direction — a mutation that abolishes binding scored ipSAE 0.917 against a wild type's
0.903. **A 96.0 here is a statement about self-consistency, not about a molecule.**

**Does not establish that this is the best of 30.** It is the only viable one, so the
pre-registered rule (hotspot contacts, tie-broken on `frac_iface_on_epitope`) selected it
without needing to discriminate. Had there been several, the project's own evidence says
we could not have ranked them.

## Reproduction

```bash
uv run python scripts/79_challenge2_refold_r10.py   # 30/30 at recycling 10
uv run python scripts/80_challenge2_score_r10.py    # seven metrics + §7.2 gates -> 1/30
uv run python scripts/75_challenge2_package.py      # pre-registered selection, builds §4.3
uv run python scripts/58_validate_submission.py submission/LOCKSMITH_DEV
```

Inputs are the pilot's ProteinMPNN outputs, **sha256-verified 258/258** against the pod.
Novelty is scored against **human germline** per §6.3.1 (30.0% here), not against Keytruda.
