# Challenge 2 pilot — RFantibody on a rented GPU — 2026-09-22

> ⚠️ **SUPERSEDED in two ways.** (1) The hotspot-conditioning result below (d=1.47,
> p=0.0016) came from an interim look at n=10 v 5 extended to 18 v 18 and tested at
> nominal α — **optional stopping**, so that p is not the type-I rate and d is upward
> biased (95% CI [0.73, 2.22]). It was replaced by a deterministic per-backbone
> contiguous-patch null in `challenge2_patch_null.md`. (2) "`interaction_pae` CANNOT
> select between docks" is recorded as **too strong as stated** at §D5. See
> [the register](retractions.md).

**Run:** RunPod RTX 3090 (`sm_86`), upstream pins unmodified (torch 2.3.1+cu118, dgl 2.4.0+cu118).
~5.5 h wall, **$2.77**. Pre-registration: `results/prereg_2026-09-21_challenge2.md`.

## What ran

| Stage | Count | Failures |
|---|---|---|
| RFdiffusion backbones, conditioned | **18** | 0 |
| RFdiffusion backbones, **unconditioned control** | **18** | 0 |
| ProteinMPNN sequences (3 per backbone, first 10) | 30 | 0 |
| RF2 predictions, 10 recycles | 30 | 0 |

**All 36 backbones carry `T: 113` residues** — the PD-1 chain rebuilt from 5GGS **chain Z**,
not the 219-residue heavy chain that every planning document called "chain C". Every
conditioned run resolved **26/26** hotspots; every unconditioned run resolved **0**. The arms
are cleanly separated, so the comparison is not an accidental unconditioned-vs-unconditioned
null.

Throughput: **2.5-2.7 min per backbone** (139-162 s across 21 consecutive runs), MPNN 41 s for
30 sequences, RF2 ~35 s per design. Peak VRAM 3.4 GB of 24.

## Result 1 — hotspot conditioning WORKS (and needed the power)

| arm | n | `frac_iface_on_epitope` | hotspots contacted |
|---|---|---|---|
| conditioned | 18 | **0.712** (sd 0.110) | **6.33** / 26 |
| unconditioned | 18 | **0.501** (sd 0.164) | **3.56** / 26 |

```
diff = +0.211   pooled sd 0.143   Cohen d = 1.47
Mann-Whitney U = 262.0/324   P(cond > uncond) = 0.809   z = 3.16   p = 0.0016
```

**This is the finding the extra backbones bought.** At the first look (n=10 vs 5) it was
d=0.96, P=0.58, *below* the pre-registered detectable effect of ~1.3 SD — genuinely
ambiguous, and writing it up then as "conditioning is indistinguishable from chance" would
have been a **fifth underpowered null presented as a finding**. At n=18 vs 18 it is
unambiguous.

Note what the null arm shows: unconditioned docks still put **50%** of their interface on the
PD-L1 footprint. PD-1 is a 113-residue IgV domain and the footprint is 26 of those residues,
so a randomly placed antibody hits that face often. **Conditioning adds ~21 percentage points
on top of a high baseline** — it is real but it is not the whole story, and any claim should
say so.

> **Consequence for the write-up:** §7.4's phrase *"produced by target-conditioned backbone
> diffusion against the PD-L1 competitive epitope"* is now a **measured** claim (p=0.0016),
> not an assumption.

## Result 2 — `interaction_pae` CANNOT select between docks

One-way variance decomposition, k=10 backbones x m=3 sequences:

```
MS_between = 3.539   MS_within = 5.087   F = 0.70   ICC = 0.000
```

Between-dock variance is **below** within-dock variance: three sequences on one dock differ
as much as different docks do. Per the pre-registered rule, selection **falls back to hotspot
contact count**, tie-broken on `frac_iface_on_epitope`.

Stated honestly: **no between-dock signal larger than ICC 0.32 is detectable at k=10.**

## Result 3 — RF2 does NOT confirm the designed docks

| RF2 metric (n=30) | mean | sd | min | max |
|---|---|---|---|---|
| `interaction_pae` | 15.60 | 2.11 | 9.31 | 19.64 |
| `pred_lddt` | **0.91** | **0.01** | 0.88 | 0.93 |
| `target_aligned_antibody_rmsd` | **24.87 A** | 10.58 | 5.29 | 41.96 |
| `target_aligned_cdr_rmsd` | **19.20 A** | 7.92 | 4.79 | 31.42 |

RF2 places the antibody a mean **24.9 A** from the dock RFdiffusion designed. An antibody
variable domain is ~40 A across, so this is a different pose, not a refinement. **Audit 10.5
assumed RF2-as-filter bought independent confirmation; measured, it contradicts.**

And `pred_lddt` is flat at 0.91 +/- 0.01 across 30 designs — the third metric in this project
that is confidently constant while the thing it names varies enormously (cf. `contacts` ICC
0.003, `cdr_sasa` 0.000).

## What this supports, and what it does not

- **Supported:** the route runs end to end on rented hardware; the designs are aimed at the
  PD-L1 competitive epitope at p=0.0016.
- **Not supported:** that any one design is better than another (ICC 0.000); that an
  independent predictor agrees with the docks (24.9 A); that anything binds (no DockQ in
  Challenge 2, and SKEMPI showed nothing in the stack tracks affinity).

## Process failures, recorded

- `uv` absent from PATH in `01_run.sh` while `00_setup.sh` exported it. Same author, one
  missing line. Caught in seconds by the artefact assertion.
- `inference.seed` **does not exist** in RFantibody's config; passing it aborts every run.
  Invented the key instead of reading the schema -- same shape as assuming chain C was PD-1.
- The ICC first read "0 backbones with >=2 designs" because the parser broke at the first
  `ATOM`; RF2 writes `SCORE` lines at **line 5190**, after the coordinates. Free to fix, but
  it is the number that would have been read unattended.
- **~2.5 h of idle pod billing (~$1.25, more than the pilot itself)** because the session
  waited to be prompted instead of polling after the pilot finished at 01:36.
