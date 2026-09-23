---
date: 2026-09-22
tags:
  - session
  - locksmith-antibody-hackathon
status: living
---

Tags: [[Learning]], [[locksmith-antibody-hackathon]]

# Session 2026-09-22 — Published, withdrawn, re-measured; and the fix that killed the antibody

## 0. Session at a glance

**Before:** Challenge 1 was packaged. Challenge 2 had 30 designs on a pod, none scored.
The project had 17 tests and two commits.

**Now:** both challenges are packaged, viable and validated from their own files —
Challenge 1 **96.0**, Challenge 2 **91.2** — with **29 tests**, twenty-odd commits, and a
submission that argues against itself in five places.

**What actually happened is a sequence of corrections, and that is the content of this
doc.** Challenge 2 was measured as `0/30`, written up with an essay, withdrawn as an
artefact, re-measured as `1/30`, audited by three independent judges who found four more
wrong claims — two of them *inside the shipped package* — and finally swapped for a
lower-scoring design that removes a developability liability the rubric does not measure.

**Prerequisites:** the rubric and its metrics —
[[2026-09-14-antibody-hackathon-spec-and-scoring|the spec extraction]]. The overnight run
that preceded this —
[[2026-09-22-the-first-test-file-and-the-winner-that-changed|the first test file]].

---

## 1. Concepts, from first principles

### 1.1 Recycling depth, and what an under-converged predictor actually does to you

Boltz-2 (like AlphaFold) runs its trunk repeatedly, feeding each pass's output back as
input. `--recycling_steps` sets how many times. More recycling means a more converged
internal representation before the structure module draws coordinates.

The naive expectation is that under-recycling adds **noise** — that rankings jitter around
the right answer. That is not what it does. It produces a **compressed** distribution,
where signal has not yet separated from the floor.

Concretely, at `recycling_steps=3` across 30 de novo designs: **15 of 30 scored ipSAE
exactly 0.000** and the best was 0.372. At `recycling_steps=10`, still 15 zeros — but one
design moved 0.263 → 0.864. The *distribution* barely changed; one member separated.

> **Transferable principle.** A metric that should span its range and instead piles up at
> a floor is a **sampling diagnosis, not a result**. Check convergence before interpreting
> a unanimous failure. And "it changed when I sampled harder" is not the same as "it has
> now converged" — the r3↔r10 rank correlation was only **0.432**.

### 1.2 ipSAE floors at zero, and that manufactures structure

ipSAE sums over residue pairs whose predicted aligned error passes a hard cutoff
(PAE < 10 Å here). No pair passing ⇒ exactly zero, regardless of how the model feels
about the complex.

This creates a discontinuity the underlying model does not have. The 15 designs at ipSAE
*exactly* 0.000 carry **ipTM 0.556–0.674** — ordinary low-moderate interface confidence.
Largest-gap-to-next-gap ratio: **3.56 on ipSAE, 2.12 on ipTM**.

> **Transferable principle.** A metric with a hard threshold inside it does not merely
> lose resolution below that threshold — it **invents a mode**. Before calling a
> distribution bimodal, look at a continuous measure of the same quantity.

### 1.3 A ranked output is an order statistic, not a sample

Boltz emits `diffusion_samples` structures and orders them by its own confidence.
`model_0` is therefore the **argmax by construction**, not a draw.

With the default of 1 you do not get a sample from the model's distribution; you get its
best guess, reported as though it were the estimate. Every pose-derived number this
project produced for a week — ipSAE, DockQ, ΔG, contacts, interface pLDDT, CDR SASA — sat
at the top of a distribution nobody had sampled.

> **Transferable principle.** When a generative model returns ranked outputs, taking the
> first and calling it "the prediction" silently reports a maximum. Sample enough to know
> the spread you are sitting on top of, and report that spread beside the number. It is
> usually cheap: five diffusion samples took **2m54s against ~2m for one**, because the
> MSA, trunk and recycling are shared and only the diffusion head reruns.

### 1.4 N-linked glycosylation sequons, and why the position of the fix matters

The sequon `N-X-S/T` (X ≠ P) is the recognition motif for oligosaccharyl transferase.
Proline at the middle position blocks the enzyme, which is why a naive `N.[ST]` regex
over-reports.

Handbook §9.2 lists *"No N-glycosylation sequons in Fv region"* as a checklist item, and
§9 Pillar 4 prescribes two fixes: **N→Q** (remove the acceptor) or **S→A** (remove the
hydroxyl at +2). They are presented as interchangeable. §4 of this doc shows they are not.

---

## 2. What was built

### 2.1 `metrics/liabilities.py` — the scan the build plan promised and nobody wrote

`BUILD.md:62` specified `liabilities.py — N-X-S/T, NG/DG motifs, exposed Met, pI, net
charge`. It did not exist. Two glycosylation sequons shipped in the Challenge 2 paratope
because of that.

It now scans sequons (proline-aware), deamidation (`NG` fast, `NS`/`NT` slower),
isomerisation (`DG` fast, `DS`/`DT` slower), oxidation-prone Met/Trp, unpaired cysteine,
net charge and pI by bisection — with severity raised inside CDRs, using the project's own
IMGT numbering so it agrees with every other metric rather than introducing a third CDR
definition.

**It found a defect on its first run that no reviewer had flagged:** Challenge 1 also
fails §9.2, carrying pembrolizumab's `NG` at heavy 55 inside CDR-H2 — at a position that
was inside our 29 designable positions, so removing it was free and we did not.

### 2.2 `submit/deck.py` — the deck, generated from the packaging run

The shipped `.pptx` had stated *"No design submitted"* for Challenge 2 while the package
contained a Challenge 2 design scoring 96.0, because the packager rebuilt the zip and not
the slides. Both structural reviewers rated it the most severe defect in the submission.

The deck now takes both challenges' live scores as arguments and **raises if Challenge 2's
are missing**, rather than guessing. Six slides, one chart.

### 2.3 Tests: 17 → 29

New this session: the challenge-dispatch invariants for germline novelty, viability
(one failed cutoff ⇒ non-viable; a missing metric ⇒ `None`, never `True`), the liability
scanner including the proline case, and `assert_artefacts` fixtures covering six ways a
fold can lie — absent, empty, no ATOM records, truncated `.npz`, non-square PAE, missing
pLDDT sibling.

---

## 3. Results

### 3.1 Challenge 2, measured three times

| fold setting | viable | best ipSAE | median | zeros |
|---|---|---|---|---|
| recycling 3 | **0/30** | 0.372 | 0.006 | 15/30 |
| recycling 10 | **1/30** | 0.864 | 0.005 | 15/30 |
| recycling 20 (top 5) | 1 | 0.795–0.883 | — | — |

The gate answer is stable r10 → r20; no further design crosses 0.60. The *score* is not:
the winner reads 0.795 / 0.883 / 0.731 at r20, and 0.795 is below the 0.80 Good edge.

### 3.2 The variance finding — the best scientific result of the session

Same three complexes, re-folded across recycling depths 3 / 10 / 20:

| | ipSAE range |
|---|---|
| crystallised pembrolizumab + PD-1 | **0.050** |
| our Challenge 1 design (near-native) | **0.036** |
| our Challenge 2 design (de novo) | **0.601** |

A near-native complex is essentially invariant to sampling depth. A de novo interface is
**12–17× more variable** and is not converged at any depth tested. One number at one
depth hides this completely.

### 3.3 The diffusion axis

Five samples each, everything else at submitted settings:

| | ipSAE spread | what moved | envelope |
|---|---|---|---|
| Challenge 1 | 0.039 | **DockQ 0.109**, crossing a band edge on 2 of 5 | **94.0–96.0** |
| Challenge 2 | **0.128**, 3 of 5 to Medium | — | **91.2–96.0** |

**Confidence stability does not imply coordinate stability.** Challenge 1's ipSAE barely
moved while DockQ — the only metric scored here that reads coordinates against an external
reference — moved enough to change a band. Recycling refines a representation the trunk
has committed to; the diffusion head *generates the coordinates*.

### 3.4 The sequon fix, and the one that killed the antibody

Contacts to PD-1 in the unfixed complex: **H N52 → 10, L N49 → 19, both serines → 0.**
The glycosylation acceptors are the binding residues.

| | mutations | sequons | §9.2 | ipSAE over 5 samples | final | viable |
|---|---|---|---|---|---|---|
| unfixed | — | 2 | FAIL | 0.736–0.864 | 96.0 | 5/5 |
| **S→A (submitted)** | H S54A + L S51A | **0** | **PASS** | **0.619–0.781** | **91.2** | **5/5** |
| N→Q | H N52Q + L N49Q | 0 | PASS | **0.013–0.014** | — | **0/5** |

**`N→Q` collapses ipSAE sixty-fold, reproducible to ±0.001.** Two of the most conservative
substitutions available — Asn→Gln, one methylene longer, identical amide chemistry —
produce a dead interface. Predicted from the contact table before folding.

> **Transferable principle.** A developability fix is a **design change**, and prescribed
> fixes are not interchangeable. Here the liability motif and the binding site are the
> same residue, the two textbook remedies differ by a factor of sixty, and the structure
> tells you which in about a minute.

`S→A` is not free either: the envelope falls to 0.619–0.781, the best sample drops below
the Good edge (**96.0 → 91.2**), and the worst sits **0.019** above the viability cutoff
against the unfixed design's 0.136. Removing a hydroxyl at a zero-contact position should
not have done that. **The cost is unexplained and is recorded as unexplained.**

We submitted the lower-scoring design anyway: §9.2 asks for it, §5.2 does not pay for it,
and a package arguing the rubric is gameable should not then optimise it.

---

## 4. What went wrong

### 4.1 `0/30` was published with an essay attached

`recycling_steps=3` was inherited from Challenge 1 and never re-examined. The result — 0 of
30, all failing the one metric that reads model uncertainty — was *interesting*, and that
was the trap. It got a long write-up about metric design before anyone checked convergence.

The tell was visible in the data that was written up: 15 of 30 at exactly 0.000.

### 4.2 The positive control passed and was blind to the real problem

I suspected the **Fv construct** (the project had failed gate G1c on exactly that:
*"Fv ipSAE reliability 0.61 vs Fab 0.96, Fab-only adopted"*), pre-registered a two-arm
control, and ran it. Fab 0.776, Fv 0.842 — the construct was exonerated cleanly.

**The control ran at recycling 3 too**, so it could not see the variable that mattered. It
printed a verdict — *"0/30 is a real property of the designs"* — that was wrong within the
hour.

> A control eliminates the confound you thought of. It is **silent** on the one you did
> not, and a passing control reads as general reassurance when it is nothing of the kind.

### 4.3 I had the signal and dropped it

A PAE diagnostic I ran hours earlier flagged `bb_2_0_dldesign_1` at **81.4%** of
cross-chain pairs under PAE 10 Å — by far the highest of the nine checked. I wrote "the
gate outcome is genuinely open" and then reported `0/30` without going back to it. It is
the design that clears.

### 4.4 Four wrong claims, two of them inside the shipped package

Found by three independent judges:

- *"everything else ≤ 0.161"* — **false**; third place is 0.311. Omitted because it never
  entered the reseed set, having been chosen by the ranking I had just called misleading.
- *"the distribution is bimodal"* — an ipSAE artefact (§1.2).
- *"real epitope 0.712"*, under a heading about **this design** — that is the **pool
  mean**. The design's own backbone is 0.625, below the pool median; on the submitted
  re-dock it is 0.581. **This project's own catalogued error, committed inside the
  deliverable.**
- *"chosen by a fixed rule"* — the pre-registered rule sorted a list of length one. Under
  its own key this design's backbone ranks below 12 of 18.

Plus two false statements in the shipped docs: *"the CLI default would fail a marketed
drug"* (NetSolP's `predict.py` defaults to ESM1b, which passes) and *"the two flags are
mandatory"* for DockQ (only `--allowed_mismatches` is, minimum **15**).

### 4.5 I wrote a `pgrep -f` wait after being told to check artefacts

A chained finisher spun for **21 minutes** after its work was done, because the heredoc
that created the script was still the command line of a live parent shell — so the
bracketed literal `[7]3_challenge2_score.py` matched from another process's cmdline. The
bracket trick stops a pattern matching its own `pgrep`; it does not stop this. Sixth
instance in this project.

### 4.6 The audit script carried the night's bug on its first run

Its summary tested `ok is True`, but numpy returns `np.bool_` and `np.True_ is True` is
`False` — so seven genuine passes printed PASS *and* were listed UNVERIFIABLE, and
`json.dumps` refused to serialise them. The script that exists to catch "the newest claim
carries the error" carried it.

---

## 5. Verification

```bash
uv run --with pytest pytest tests/ -q                      # 29 passed
uv run --with python-pptx python scripts/57_build_submission.py
uv run python scripts/75_challenge2_package.py
uv run python scripts/58_validate_submission.py submission/LOCKSMITH_DEV
```

Healthy output: `VALIDATION PASSED`, Challenge 1 **96.0 viable**, Challenge 2 **91.2
viable**, `structures/` containing exactly two files per challenge, and the Challenge 2
FASTA reading `NVA` / `NAA` with zero sequons.

**What a plausible-but-wrong result looks like here:** `VALIDATION PASSED` while the deck
says something the package contradicts. That happened, twice — once claiming Challenge 2
was not submitted, once with stale conditioning numbers. The validator only reads
`structures/`, `sequences/` and `docs/`; it has never read the `.pptx`. That gap is now
closed by generating the deck from the packaging run, not by a check.

---

## 6. Honest assessment

**Solid.** Both challenges viable and validated from their own files. 29 tests, all
mutation-verified. Three independent audits absorbed and acted on. A complete engineering
loop closed in one session: reviewer finds a shipped liability → build the scanner that
should have caught it → scanner immediately finds another → design two fixes from the
structure → predict which survives → measure both.

**Weak.** The designs. Challenge 1 is 93.5% identical to Keytruda with CDR-H2 changed at
one position, and **81% of its antigen-contact surface is unaltered pembrolizumab**.
Challenge 2 is one survivor of thirty, on a trastuzumab framework carried over unchanged.
Both judges said "partially answers the brief" and both were right.

**Unresolved.** Why `S→A` cost 0.1 ipSAE at a zero-contact position. Whether the Challenge
2 design is viable at a sixth diffusion sample — its floor is 0.019 above the cutoff.
Whether `diffusion_samples` interacts with recycling depth; we varied each alone.

**Does not support.** That either antibody binds anything. Both scores are
self-consistency measures, and this project's SKEMPI work showed a mutation that abolishes
binding scores ipSAE 0.917 against a wild type's 0.903.

**The rate that matters.** Four published claims withdrawn in one session. The corrections
were fast and self-inflicted, which is the good version — but a reviewer counts the rate at
which claims need correcting, not just whether they were eventually caught.

---

## 7. Glossary

**Recycling** — repeated passes of the folding trunk, each fed its own previous output.
**Diffusion sample** — one draw from the structure module; Boltz emits them ranked by its
own confidence, so `model_0` is an argmax, not a sample.
**ipSAE** — an interface score summing over residue pairs passing a hard PAE cutoff;
floors at exactly zero when none pass.
**ipTM** — interface predicted TM-score; continuous, no hard cutoff, which is why it
exposes structure ipSAE hides.
**Sequon** — `N-X-S/T` (X ≠ P), the N-linked glycosylation recognition motif.
**Order statistic** — a value defined by its rank in a sample (here, the maximum), as
opposed to a draw from the distribution.
**ICC** — intraclass correlation; between-group variance as a fraction of the total.
**Pre-registration** — fixing predictions and the decision rule in writing before running,
so the analysis cannot be chosen after seeing the outcome.
