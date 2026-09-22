# Boltz-2 vs AlphaFold2-multimer on 5GGS — Gate 1d, partially resolved

**2026-09-16.** Same complex, same `ipsae.py`, same 10/15 cutoffs, same crystal
reference. The question G1d asks: may the rubric's AF2-calibrated ipSAE bands
(cutoff 0.60, good 0.80) be applied to Boltz-2 output?

## The two runs

| | Boltz-2 | AlphaFold2-multimer_v3 |
|---|---|---|
| via | `boltz predict --no_kernels` | ColabFold 1.6.3 (`colabfold_batch`) |
| input | Fv, 343 res, chains A/B/C | identical |
| MSA | antibody `empty`, PD-1 ≤1024 | **full pipeline on all three chains** (mmseqs2_uniref_env, paired+unpaired, max_seq 508 / max_extra 2048) |
| templates | none | none |
| recycles / seed | 3 / 1 | 3 / 1 |
| wall clock | 34 s | 29 s fold (+ ~3 min MSA server) |

## Results

**ipSAE**, `Type = max` rows, PAE cutoff 10, dist cutoff 15:

| interface | AF2 | Boltz-2 | Boltz − AF2 |
|---|---|---|---|
| A–B heavy–light *(not scored by the rubric)* | 0.864 | 0.941 | +0.077 |
| **A–C heavy–antigen** | **0.654** | **0.841** | **+0.187** |
| **B–C light–antigen** | **0.615** | **0.827** | **+0.211** |

Handbook rule — best antibody-vs-antigen `max` row:

| | ipSAE | band | margin over the 0.60 cutoff |
|---|---|---|---|
| AF2-multimer_v3 | **0.654** | medium | +0.054 |
| Boltz-2 | **0.841** | **good** | +0.241 |

## The control that changes the reading

The tempting conclusion — "Boltz inflates ipSAE by ~0.19, so discount it" — does
not survive the obvious control. **Is the AF2 structure as good?** It is not:

| | DockQ vs 5GGS crystal | heavy–antigen | light–antigen |
|---|---|---|---|
| Boltz-2 | **0.820** | 0.838 | 0.820 |
| AF2-multimer_v3 | **0.690** | 0.698 | 0.690 |

AF2 produced a genuinely *less accurate* pose (both are CAPRI-acceptable; 0.820 is
High quality, 0.690 is Medium). So some of the ipSAE gap is **deserved** — AF2 is
less confident because it is less right. A confidence metric reporting a lower
number on a worse structure is the metric working, not a scale offset.

**Therefore G1d is NOT resolved.** One complex cannot separate "Boltz's PAE head is
on a different scale" from "Boltz built a better model of this particular
complex". The two effects are confounded at n=1, and they push the same direction.

Second confound: the MSA treatments are not matched. AF2 saw deep alignments for
all three chains; Boltz saw none for the antibody. That is each tool's intended
production protocol, so the comparison is operationally meaningful — *what our
pipeline reports* versus *what the thresholds were calibrated on* — but it is
mechanistically uninterpretable.

## What would actually resolve it

Fold **n ≥ 8 complexes of varying quality** with both predictors, then regress
ipSAE on DockQ separately for each. The offset is the gap between the two fitted
lines *at matched DockQ* — which is the quantity the rubric's thresholds need,
and which a single point cannot estimate. Cheap now: 34 s/fold on Boltz, ~30 s on
AF2 once MSAs are cached.

## Operating rule until then

Treat Boltz ipSAE as **provisional and probably optimistic**. The single
measurement puts a Boltz 0.80 at roughly an AF2 0.61 — i.e. at the cutoff, not in
the good band. Do not let a Boltz ipSAE in the 0.80s alone justify calling a
design good; require the cross-predictor consensus and the binding gates that do
not depend on PAE.

## Incidental observation, offered as a hint and not as evidence

AF2 had *strictly more* information here — deep MSAs on all three chains — and
built the *worse* complex. That is consistent with the premise behind folding
antibodies from single sequences (an antibody and its antigen have not
co-evolved, so an antibody MSA carries no interface signal). It is confounded with
model identity and rests on one example, so it is a hint, not support.
