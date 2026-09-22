---
date: 2026-09-17
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# The Fv screen fails, and ipSAE turns out to be a liveness test

**Session:** 2026-09-16 evening → 2026-09-17. **Built:** the fold driver (`src/locksmith/fold/`),
the variant generator, and the scoring/analysis pipeline. **Gates:** G1c **fails** (recorded, with
a cost decision); G1d **cannot be discharged on designs** under the disclosure constraint, but the
part that can be answered now has a much better answer.
**Prerequisites:** [[2026-09-16-first-prediction-and-the-four-attempt-fold|the first-prediction doc]] for the Boltz baseline and [[2026-09-16-netsolp-colabfold-and-the-control-that-changed-the-answer|the NetSolP/ColabFold doc]] for the install and the first G1d attempt. Everything needed is restated below.

---

## 1. What this session had to answer

Three things, in order of how much they matter:

1. **Does ipSAE track structural correctness at all?** This is the substantive question. Every
   viability decision in the project leans on ipSAE, and 5GGS is one of the only places where a
   confidence metric can be checked against ground truth.
2. **Gate 1c** — does Fv ipSAE *ranking* predict Fab ipSAE ranking? The Fv-screen/Fab-confirm
   protocol rests on this and it had never been tested.
3. **Gate 1d** — is the Boltz/AF2 ipSAE gap a scale offset or deserved?

And underneath all three: `src/locksmith/fold/` was empty, and every remaining milestone needs it.

---

## 2. The fold driver

`src/locksmith/fold/` — `__init__.py` (common types + artefact assertion), `boltz.py`,
`colabfold.py`. Sequences in, paths out.

### 2.1 The invariant it exists to enforce

**A fold counts only when its artefacts exist and parse. The exit code is never consulted.** On
2026-09-15 three of four failed Boltz runs exited 0. `assert_artefacts()` therefore requires: the
PDB exists, is non-empty, and contains `ATOM` records; the PAE `.npz` loads and is square. Anything
less raises `FoldFailed`.

This paid for itself within the hour — see §3.

### 2.2 Two things the driver deliberately does not do

**It does not rename or move output files.** `vendor/ipsae/ipsae.py` locates the pLDDT array by
string-substituting the PAE path (`pae_file.replace("pae", "plddt")`). Tidying the output into
nicer names breaks that substitution and ipsae then writes an *empty table and exits 0*. The driver
returns paths in place. It also refuses any label containing `pae` or `plddt`, which is a two-line
assertion against the same silent failure.

**It does not let a designed sequence reach the public MMseqs2 server.** `colabfold.py` defaults to
`--msa-mode single_sequence` and raises unless a server-backed mode is explicitly unlocked with
`allow_public_server=True`. The guard is in code because the failure is silent and one-way.

### 2.3 The antigen MSA is cached, for a scientific reason as well as a disclosure one

`data/msa_cache/pd1_5ggs.csv`, 3787 sequences, reused for every fold. Beyond removing the server
from the loop: **every variant in a ranking panel must see the identical antigen alignment.**
Re-querying per fold would let the alignment drift between designs and inject uncontrolled variance
straight into the quantity being ranked.

---

## 3. Two bugs, one of which is the interesting kind

**A space in the vault path silently destroyed the MSA.** The first Fab fold failed with

```
FileNotFoundError: MSA file /home/rrobin711/Obsidian not found.
```

Boltz's FASTA MSA field splits on whitespace, and the vault lives at `.../Obsidian Personal/...`.
Boltz then **printed a 100% progress bar, initialised the GPU and carried on** — a fatal error
followed by an apparently normal run. Without the artefact assertion this would have been recorded
as a successful fold that silently had no antigen alignment, which is exactly the kind of corruption
that only surfaces as inexplicably bad numbers weeks later.

Fix: `_stage()` copies any whitespace-containing MSA path to `~/.cache/locksmith/msa/` and the FASTA
only ever carries the space-free path. **Transferable:** this project's working directory contains a
space, so any tool that takes a path *inside a config or FASTA field* rather than as an argv element
is a candidate for the same bug. argv is safe because the shell quotes it; config fields are not.

**`self._stop` shadowed `threading.Thread._stop`.** The VRAM sampler named its `Event` `_stop`,
which is a real method on `Thread`; `join()` then called the Event and raised
`TypeError: 'Event' object is not callable`. Renamed to `_done`. Mundane, but it turned a clean
failure report into a confusing traceback on top of the real error.

---

## 4. The Fab smoke fold, run before anything queued

No Fab had ever been folded on this machine. 549 residues against the Fv's 343.

| | Fv (343 res) | Fab (549 res) |
|---|---|---|
| peak VRAM | — | **7,603 MiB of 12,227** |
| wall clock, mean over the panel | **92 s** | **126 s** |

No OOM, 38% headroom. Worth having checked rather than assumed, and worth noting *why* it fits:
the antibody chains carry `empty` alignments, and alignments dominate the pair representation.

### 4.1 An unwelcome budget finding

The previously recorded Fv fold time was **34 s**. Measured per *invocation* it is **92 s** (median
104, range 42–143). The Fab is 126 s despite 1.6× the residues — the two being so close means a
large fixed cost per `boltz predict` call: checkpoint load plus parsing the 3787-sequence MSA.

That matters, because the 4,700-fold budget in the plan was derived from 34 s:

| basis | folds in ~45 GPU-hours |
|---|---|
| 34 s (the number the plan used) | ~4,700 |
| 126 s measured per invocation (Fab) | **~1,290** |
| ~68 s if the fixed overhead were amortised | ~2,380 |

**Boltz accepts a directory of inputs and folds them in one process.** Batching is worth roughly
1.8× and is not yet implemented. Until it is, the honest budget is ~1,300 Fab folds, not 4,700 —
back near the plan's original 1,400–1,800 estimate. This is stated as a correction to
[[2026-09-16-first-prediction-and-the-four-attempt-fold|the earlier doc's §7]], which revised the
budget upward on the 34 s figure.

---

## 5. The panel

14 variants of pembrolizumab, `src/locksmith/design/variants.py`, fixed seed 20260916. Substitutions
at IMGT CDR positions: 0 (positive control), then 1, 2, 3, 4, 6, 8, 10, 13 in CDR-H3, three variants
touching H1/H2, and two poly-Gly anchors to fix the bottom of the range.

Substitution alphabet is the 20 amino acids **minus cysteine** — a stray Cys can form a spurious
disulfide, which is a structural failure of a different kind and would put cliff-edge outliers into
what should be a graded series. Proline is kept; it is a legitimate backbone disruptor that real
designs produce.

Each variant folded as Fv and as Fab, seed 1. The **same mutated variable domain** goes into both,
grafted onto the constant domains for the Fab — that is what makes the comparison paired rather than
two unrelated measurements.

**48 folds, 82 minutes, zero failures.** The driver reproduced the previous session exactly:
`v00_wt` Fv gave ipSAE 0.8407 / DockQ 0.820 against the recorded 0.841 / 0.820, through entirely new
code. That agreement is the driver's correctness check.

---

## 6. The noise floor, measured before anything was concluded

Boltz-2 is a diffusion model: different seeds give genuinely different structures, not merely
different confidence. So every ipSAE value is a noisy draw, and a correlation between two noisy
measurements is **attenuated**:

$$\rho_{\text{obs}} \approx \rho_{\text{true}}\sqrt{r_{\text{Fv}}\, r_{\text{Fab}}}$$

3 variants × 3 seeds × both constructs:

| variant | construct | mean ipSAE | sd | spread |
|---|---|---|---|---|
| v00_wt | fv | 0.843 | 0.019 | 0.038 |
| v00_wt | fab | 0.831 | 0.021 | 0.038 |
| v04_h3_4 | fv | 0.768 | **0.122** | **0.215** |
| v04_h3_4 | fab | 0.792 | 0.048 | 0.095 |
| v08_h3_13 | fv | 0.714 | **0.095** | **0.187** |
| v08_h3_13 | fab | 0.753 | 0.019 | 0.036 |

Reliability (intraclass, `1 − σ²_within/σ²_observed`):

> **Fv r = 0.607.  Fab r = 0.965.**

**This is the session's sharpest result, and it was not the one being looked for.** The bare Fv is a
*much noisier instrument* than the Fab. The mechanism is the one the project already suspected when
it chose Fv-screen/Fab-confirm: a bare Fv has nothing to clamp the relative orientation of VH and
VL, so the sampler explores genuinely different elbow angles between seeds, while the constant
domains pin it. Predicted qualitatively; measured here, it **undermines** the screen instead of
supporting it.

Caveat: estimated from 3 variants chosen to span the range, so it assumes seed noise is roughly
constant across quality. `v04_h3_4`'s Fv sd of 0.122 against `v00_wt`'s 0.019 says it is not — this
is an average over a heteroscedastic quantity.

### 6.1 The cost inversion

Averaging seeds recovers reliability (Spearman–Brown, $r_k = kr/(1+(k-1)r)$) but has to be paid for:

| Fv seeds | Fv reliability | Fv wall clock | vs one Fab fold |
|---|---|---|---|
| 1 | 0.607 | 92 s | 0.74× |
| 2 | 0.756 | 185 s | 1.47× |
| 3 | 0.823 | 277 s | 2.21× |
| 4 | 0.861 | 370 s | 2.94× |

**At two seeds the "cheap" screen already costs more wall clock than the Fab it was meant to save,
and is still less reliable.** No practical number of Fv seeds reaches the Fab's 0.96. The 2.5×
residue-count saving does not survive contact with the fixed per-invocation overhead plus the elbow
noise. The Fv screen is dead on cost grounds independently of the rank correlation.

---

## 7. Gate 1c — failed, and recorded as failed

| | Spearman ρ | 95% CI | p | n |
|---|---|---|---|---|
| **Restricted range** (both forms clearing the 0.60 cutoff) | **+0.469** | **[−0.14, +0.82]** | 0.124 | 12 |
| Full panel | +0.662 | [+0.20, +0.88] | 0.010 | 14 |

**Lead with the restricted number: ρ = 0.469, below the 0.6 threshold, with a CI that spans zero.**
The screen's real job is separating designs that have *already* passed earlier filters, so the
restricted range is its operating regime. The full-panel 0.662 clears the gate but describes a task
that never occurs — ranking a poly-Gly corpse below a live design is trivial and the funnel would
have removed it long before.

Attenuation-corrected, the restricted ρ is **+0.612** and the full-panel ρ is **+0.864**. Those are
*corrected* figures, not observations, and 0.612 straddling the threshold is not a pass.

**Decision: adopt Fab-only.** This is a cost decision, not a problem to engineer around. It is also
much cheaper than when the plan was written: §6.1 shows Fab-only is not 2.5× more expensive, it is
*less* expensive than a Fv screen run at usable reliability.

Note the CI width. At n=14, SE in Fisher-z is $1/\sqrt{n-3} = 0.30$, so **no n=14 experiment can
resolve a 0.6 threshold.** Reaching a ±0.15 CI would need n ≈ 45. Given the cost inversion already
settles the protocol question on its own, spending ~90 more folds to sharpen a number that changes
nothing would be waste — so this is recorded as failed-and-closed rather than escalated.

---

## 8. The substantive question: ipSAE is a liveness test, not a ranking metric

ipSAE regressed on DockQ against the 5GGS crystal:

| predictor | construct | slope | R² | Spearman | n |
|---|---|---|---|---|---|
| Boltz-2 | Fv | +0.527 | **0.919** | +0.815 | 14 |
| Boltz-2 | Fab | +0.566 | **0.755** | +0.754 | 14 |

Looks excellent. It is not. Remove the two poly-Gly anchors:

| predictor | construct | slope | R² | n |
|---|---|---|---|---|
| Boltz-2 | Fv | +0.646 | **0.683** | 12 |
| Boltz-2 | Fab | +0.186 | **0.263** | 12 |

**The correlation is carried almost entirely by the two dead designs.** Within the plausible range
the Fab R² collapses from 0.76 to 0.26 and the slope flattens by a factor of three. The raw numbers
show it plainly — as substitutions accumulate, DockQ falls steadily while ipSAE barely moves:

| variant | subs | Fv DockQ | Fv ipSAE |
|---|---|---|---|
| v00_wt | 0 | 0.820 | 0.841 |
| v04_h3_4 | 4 | 0.727 | 0.836 |
| v05_h3_6 | 6 | 0.742 | **0.867** |
| v06_h3_8 | 8 | 0.671 | 0.793 |
| v07_h3_10 | 10 | 0.601 | 0.788 |
| v12_h3_polyG | 13 | 0.035 | 0.407 |

**`v05_h3_6` scores the highest ipSAE in the entire panel — 0.867, above pembrolizumab itself — on a
structure whose DockQ is 0.742 against pembrolizumab's 0.820.** DockQ drops 0.22 across the live
series while ipSAE wanders within ±0.04 of 0.82.

This is a direct, measured confirmation of the hypothesis recorded on 2026-09-16 that *"an ipSAE
much above 0.85 on a designed molecule warrants suspicion, not celebration"*. It was a guess from a
single calibration point. It is now an observation.

**What ipSAE is good for:** telling a dead design from a live one. It does that cleanly — 0.41 and
0.49 for the poly-Gly anchors against 0.79–0.87 for everything else.

**What it must not be used for:** ranking among live designs, which is precisely what the funnel was
going to use it for. Selection should lean on DockQ where a reference exists (Challenge 1), and on
the binding gates that do not derive from PAE. For Challenge 2 there is no reference, which makes
this materially worse news there than for Challenge 1.

---

## 9. Gate 1d

### 9.1 AlphaFold2 cannot be run on the designs at all

All seven ColabFold folds used `--msa-mode single_sequence`, per the disclosure constraint. Every one
failed to build a complex:

| | AF2 single-sequence | AF2 with MSAs, same complex |
|---|---|---|
| pLDDT | 37.1 | 94.4 |
| pTM / ipTM | 0.231 / 0.111 | 0.917 / 0.891 |
| ipSAE | 0.000 | 0.654 |
| DockQ | 0.017 | 0.690 |
| min inter-chain distance | **0.5–0.9 Å** (interpenetrating) | normal |

Checked directly rather than inferred from the low scores: the chains are physically overlapping.
This is a property of AlphaFold2, not a pipeline fault — AF2 draws its structural signal from
co-evolution in the MSA and does not fold complexes without one. Boltz-2's robustness to
single-sequence input is precisely why antibody chains can be given `empty` alignments at all.

**So G1d cannot be discharged on designed sequences.** AF2 needs MSAs; MSAs need either the public
server (forbidden for designs) or a local database (not installed). Three options, all costs rather
than fixes:

1. **Install a local sequence database** for `colabfold_search`. Correct and expensive — ColabFoldDB
   is ~1 TB+; UniRef30 alone is ~150 GB. Buys full AF2 capability on designs.
2. **Drop AF2 as a consensus predictor** and use Chai-1, which handles single sequences, for
   cross-predictor agreement instead.
3. **Accept AF2 numbers only for published molecules** — i.e. calibration only, never on designs.

### 9.2 What the panel does resolve

The one legitimate AF2-with-MSA point is pembrolizumab, whose sequence is published. Previously this
was one number against one other number. The panel now supplies a **Boltz calibration curve**, so
the question can be asked properly: *given a structure of DockQ 0.690, what ipSAE would Boltz have
reported?*

- Boltz-2 Fv curve: `ipSAE = 0.421 + 0.527 × DockQ` (n=14, R² 0.919, residual sd 0.043)
- At DockQ 0.690 it predicts ipSAE **0.784**
- AF2 reported **0.654** → residual **−0.131**, or **3.1 residual sd**

**So there is a genuine scale offset of roughly 0.13, on top of the part explained by structure
quality.** The raw gap was 0.187; about 0.06 of it was AF2 deserving a lower score for a worse
structure, and ~0.13 is the PAE scale differing.

This **refines** the 2026-09-16 conclusion rather than reversing it. That session found the gap was
partly deserved and correctly declined to call it an offset at n=1. With a calibration curve the
residual separates out. But **n is still 1 for AF2** — one point cannot establish an offset, only
fail to find one. What improved is the reference, not the sample size.

Operating rule, unchanged in direction and now quantified: treat Boltz ipSAE as optimistic by
~0.13 relative to the AF2-calibrated bands. A Boltz 0.80 is about an AF2 0.67.

---

## 10. Pushback on the brief

Requested, and three points are worth making.

**DockQ-vs-crystal is not "correctness" for the mutants, and the writeup says so throughout.** For
`v00_wt` it is genuine accuracy — same molecule, known answer. For a variant with 13 substitutions
the true structure is unknown and the crystal belongs to a *different molecule*. DockQ then measures
**retention of the native binding mode** and conflates prediction error with real structural change
caused by the mutation, which is an effect and not an error. That is still the right quantity for
Challenge 1, but the §8 regression is "does confidence track retention of the native pose", not
"does confidence track correctness". The distinction matters most for Challenge 2, where no
reference exists at all.

**n=14 cannot adjudicate a 0.6 threshold and the brief's gate implicitly assumed it could.** SE in
Fisher-z is 0.30 at n=14; the CI on the restricted ρ is [−0.14, +0.82]. The gate was answerable only
because the *reliability* measurement (§6) settled the protocol question independently and more
cheaply than the correlation did. If the noise floor had been skipped, this panel would have
produced a number with no interpretation.

**The ColabFold arm was doomed by a constraint conflict that should have been caught at design
time** — mine to catch, and I did not. "Fold designs on AF2" and "never let a designed sequence
reach the public MMseqs2 server" cannot both hold without a local database. Seven folds, ~9 minutes,
were spent discovering it. Cheap, but it was predictable from the ColabFold docs before any GPU time
was spent.

---

## 11. State after this session

**Built.** `src/locksmith/fold/` (`__init__`, `boltz`, `colabfold`),
`src/locksmith/design/variants.py`, `scripts/05_make_variants.py`, `06_fold_panel.py`,
`07_score_panel.py`, `08_analyse_panel.py`. Runs are resumable — every fold appends to
`runs/panel/index.jsonl` and completed labels are skipped.

**Gates.** G1c **failed → Fab-only adopted.** G1d **partially resolved**: offset ≈ 0.13 at n=1 for
AF2, and blocked for designs pending a local MSA database.

**Open.**
- The post-training-cutoff test. 5GGS is from 2017 and near-certainly in Boltz's training data, so
  every DockQ here is partly retrieval. This is now the **largest** unquantified risk, because §8's
  conclusion about ipSAE rests on DockQ values that may be optimistic.
- Fold batching (§4.1), worth ~1.8× on the whole remaining budget.
- Baselines and the funnel. M2 is still not started; no ProteinMPNN designs exist.
- `src/locksmith/{select,submit,validate}/` remain empty.
