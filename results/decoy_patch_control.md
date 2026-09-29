# The decoy-patch control — the falsifier, and it did not fire

**2026-09-28. Verdict: pre-registered ROW 1. Conditioning works.** 18 backbones
generated on CPU, ~6 h, $0. `scripts/97_decoy_cpu.sh` → `scripts/95_decoy_patch_control.py --analyse`.

## Why this experiment and not another

Every earlier test of the conditioning claim compared the conditioned arm against a
**resampled null on the same structures** — `scripts/70` (contiguous patches) and
`scripts/94` (shape-matched patches, 18/18 at p<0.05). Those can only ever *confirm*.
None of them can separate

- *"the hotspots steered RFdiffusion to the face we named"*, from
- *"RFdiffusion docks antibodies on that face of PD-1 anyway"*,

because **nothing in them ever asked it for a different face.** This did: same target,
same framework, same loop spec, same recycles — only the 26 hotspot residues changed, to
a patch 165.9° away on the far side of the antigen
([selection and verification](decoy_patch.md)).

## Result

| quantity | decoy-conditioned | conditioned arm | unconditioned arm |
|---|---|---|---|
| backbones generated | 18 | 18 | 18 |
| **no antigen contact at all** | **2** (`dec_0`, `dec_7`) — excluded, fraction undefined | 0 | 0 |
| n analysed | **16** | 18 | 18 |
| mean `frac_iface_on_decoy` | **0.803** (95% CI ±0.133) | 0.000 | **0.000** |
| mean `frac_iface_on_epitope` | **0.000** | 0.712 | 0.500 |
| backbones with any decoy contact | **15 / 16** | 0 / 18 | **0 / 18** |
| interface size (residues) | median 6, range 1–13 | median 9, range 4–15 | median 7, range 3–11 |

**The pre-registered ROW 1 condition is met**: decoy ≥ 0.500 *and* epitope < 0.500.

## Reading it

**The steering is unambiguous.** The unconditioned baseline on the decoy face is not
"low", it is **exactly zero — 0 of 18 backbones, maximum 0.000**. RFdiffusion left to
itself never goes there. Conditioned to go there, 15 of 16 do, at 0.803 of their
interface. That is motion from nothing, not a shift in a distribution.

**And they left the real epitope completely.** All 16 read **0.000** on the PD-L1
footprint — not reduced, absent. The concern recorded in
[decoy_patch.md](decoy_patch.md) that the patches share a **4.9 Å** edge, and that a dock
straddling it could satisfy both, did not materialise: nothing straddled.

**So `frac_iface_on_epitope = 0.712` is a property of our conditioning, not of
RFdiffusion's prior.** That was the live alternative explanation and it is now excluded.

## What it does NOT buy, stated plainly

- **This is targeting, not binding.** A backbone can sit squarely on a named face and be
  an antibody that binds nothing. Nothing here touches affinity, and the composite scores
  are unchanged by this result.
- **The decoy face is harder to dock, and the data says so.** 2 of 18 produced no
  antigen contact at all (0 of 18 in both other arms), and the interfaces that did form
  are smaller — median 6 against the conditioned arm's 9. Conditioning steers; it cannot
  make an arbitrary surface as good a docking site as the one PD-L1 evolved to use.
  `dec_2` is the extreme case at a single interface residue.
- **n = 16, not 18**, and the two exclusions are named above rather than absorbed into a
  denominator. They are not parse failures; the fraction is 0/0.
- **One arm, one seed set, no replication.** 95% CI on the decoy mean is ±0.133.

## Provenance, and the checks that ran before any number was read

| check | result |
|---|---|
| ordinal mapping, chain T | **113 = 113** on all 18 — the mismatch that returns a believable zero |
| decoy hotspots resolved | **26 / 26 on every backbone** (156 lines over w2's six, 130 over five) |
| decision rule | committed **before** the data (`d04e809`), amended **before** the data (`610cdf2`) |
| rule can fire the damning branch | control: fed the conditioned arm it returns **ROW 3, REFUTED** |
| unconditioned baseline on the decoy | measured **before** the run: 0/18 |

The decision rule was amended once, on 2026-09-28, **before any decoy backbone was
read**, and only on the strength of the unconditioned arm: the original `BAR = 0.500` for
both faces was symmetric in number and asymmetric in evidence, because the unconditioned
baselines are 0.500 on the epitope and 0.000 on the decoy. See
[the register](retractions.md) and the script's own header.
