# Challenge 2, end to end: **0 of 30 designs clear the §7.2 cutoffs**

**2026-09-22.** All 30 RFantibody designs folded with Boltz-2 (30/30 successful, zero
failures) against the handbook's §4.2.2 antigen, scored on the seven metrics §7.2 applies
to Challenge 2. **No design is viable. Nothing was packaged, and step 3 was correctly left
undone.**

## The result

```
n = 30      clear every §7.2 cutoff = 0
```

| metric | cutoff | min | median | max | failed on | margin at best |
|---|---|---|---|---|---|---|
| `cdr_sasa` | ≥ 250 Å² | 929.1 | 1344.6 | 2209.5 | 0/30 | +1959.5 |
| `cdrh3_identity` | < 95 % | 16.7 | 32.1 | 44.4 | 0/30 | +78.3 |
| `contacts` | ≥ 10 | 44 | 77.5 | 114 | 0/30 | +104 |
| `dg` | ≤ −6 kcal/mol | −14.0 | −10.95 | −8.0 | 0/30 | +8.0 |
| `iface_plddt` | ≥ 65 | 65.91 | 73.74 | 94.29 | 0/30 | +29.3 |
| `netsolp` | ≥ 0.50 | 0.552 | 0.586 | 0.629 | 0/30 | +0.129 |
| **`ipsae`** | **≥ 0.60** | **0.000** | **0.006** | **0.372** | **30/30** | **−0.228** |

**Six of seven metrics pass on every single design, most of them by enormous margins. One
metric fails on every single design.** The best ipSAE in the pool is 0.372 against a 0.60
minimum — **1.6× short** — and the median is **0.006**. Fifteen of the thirty are *exactly
zero*.

## Why this is the interesting result and not a disappointment

Look at which metric failed.

- `cdr_sasa`, `contacts`, `dg`, `iface_plddt` are computed **from the coordinates** of a
  predicted structure (ΔG via PRODIGY is a regression on contact counts; interface pLDDT
  is a per-residue confidence averaged over a contact set defined geometrically).
- `cdrh3_identity` and `netsolp` are computed **from the sequence** and never see a
  structure at all.
- `ipsae` is the only one computed **from the PAE** — the model's own uncertainty about
  *where the chains are relative to each other*.

**Every metric that reads the coordinates says the design is fine. The single metric that
reads the confidence says the pose is meaningless.** They are not in conflict; they are
measuring different things, and only one of them can tell you that the structure it was
handed is not to be believed.

Concretely, on `bb_10_0_dldesign_0`: **61 heavy-atom contacts, ΔG −9.6 kcal/mol, interface
pLDDT 75.7 — and ipSAE 0.000**, because *not one* antibody–antigen residue pair has PAE
below 10 Å (minimum cross-chain PAE **18.40 Å**). PRODIGY dutifully counted contacts in a
pose Boltz does not believe in.

> **Transferable principle.** A geometric metric computed from a predicted structure
> inherits **none** of the prediction's uncertainty. A confidently-placed interface and a
> coin-flip interface produce the same contact count, the same buried surface, and a
> similar ΔG. Any rubric that scores several coordinate-derived metrics and one
> confidence-derived metric, then **averages** them, is double-counting the pose and
> single-counting the doubt — and this pool is the clean demonstration: it scores
> 81.6–87.6 out of 100 on a set of designs its own predictor cannot place.

## This is exactly what we said would happen

`results/challenge2_scope.md` (2026-09-20) declined Challenge 2 on three evidential
objections, the second of which was: *"the predictor is measurably unreliable at exactly
this task"* — median Fab DockQ **0.291** on five complexes released after Boltz-2's
verified 2023-06-01 cutoff. These designs are more novel than that test set: a de novo
backbone against a target it was never co-evolved with.

The prediction was correct, and it is worth more as a *confirmed* prediction than a score
would have been. We built the whole pipeline, ran it end to end, and it returned the
answer our own prior evidence said it would.

## What this does and does not establish

**Establishes:** on this pipeline, RFantibody backbones + ProteinMPNN sequences do not
produce complexes that Boltz-2 will place with any confidence against PD-1. The failure is
unanimous (30/30), large (1.6× short at the best), and isolated to the one metric that
measures placement confidence.

**Does not establish that the designs do not bind.** ipSAE is a statement about Boltz-2's
uncertainty, not about chemistry. `results/skempi_validity.md` showed this stack does not
track measured affinity in either direction — a mutation that abolishes binding scored
ipSAE 0.917 against a wild type's 0.903. A predictor that cannot place a novel complex
tells you about the predictor.

**Does not establish that the conditioning failed.** It plainly worked: 17 of 18 backbones
put their interface on the PD-L1 footprint against a contiguous-patch null
(`results/challenge2_patch_null.md`). The designs are aimed correctly and folded
unconvincingly. Those are separate claims about separate tools.

## Method, for reproduction

```bash
uv run python scripts/72_challenge2_fold.py     # 30/30, Boltz-2, seed 1, handbook antigen
uv run python scripts/73_challenge2_score.py    # seven metrics + §7.2 gates
uv run python scripts/75_challenge2_package.py  # refuses; exit 2
```

- **Inputs** are the pilot's ProteinMPNN outputs, retrieved from the pod volume and
  **sha256-verified 258/258** against the server (`results/checksum_pass_2026-09-22.md`).
- **The antigen is the handbook's 123-residue §4.2.2 construct**, verified to be an exact
  superstring of the 113-residue target RFdiffusion was conditioned against (offset 5,
  trailing 5 — terminal extension only, which is harmless where an internal deletion would
  be fatal).
- **Novelty is scored against human germline**, not Keytruda, per §6.3.1 — wired on
  2026-09-22 and pinned by `tests/test_invariants.py`. Every design scores 16.7–44.4%, far
  inside the <95% cutoff, confirming that gate is free.
- **Seven metrics, not eight.** DockQ is Challenge 1 only (§5.2), read from config rather
  than hardcoded. Note what its absence removes: it was the only metric comparing the
  prediction to anything external.

## The one number not to quote

The `final` scores run **81.6 – 87.6**. They are **not comparable to anything**, because
§7.2 ranks a non-viable design below every viable one. A design that fails a hard cutoff
does not have a score; it has a disqualification. Quoting 87.6 would be the single most
misleading number this project could produce, which is why
`scripts/75_challenge2_package.py` refuses to build a folder at all rather than package a
design carrying it.
