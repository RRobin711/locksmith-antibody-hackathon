# Standing up the environment, and two traps that produce plausible wrong answers

**Date:** 2026-09-15 (Day 1 of 6) · **Phase:** 0, partial
**Goal:** get a verified GPU environment, the scoring tools installed, reference structures
on disk, and the antibody-numbering layer working — the foundation everything else sits on.

**Prerequisite reading:** [the specification and scoring rules](2026-09-14-antibody-hackathon-spec-and-scoring.md) for what the metrics are; [the build skeleton](../../BUILD.md) for why the code is
laid out as it is. This doc is self-contained on the concepts it introduces.

---

## 1. What now exists

```
pyproject.toml        uv project, torch pinned to the cu128 index
src/locksmith/
  io/pdb.py           chain sequences, complex extraction + relabelling
  numbering.py        IMGT numbering and CDR extraction via ANARCII
scripts/
  00_doctor.py        environment preflight, exits non-zero on failure
  01_fetch_refs.py    5GGS / 5DK3 / 5IUS / 5WT9 from RCSB
vendor/ipsae/         DunbrackLab IPSAE @ 6174cf9e71cb1bd660cc805856a18c4871a6dec3
~/.venvs/locksmith          main env  (torch 2.11.0+cu128, anarcii, freesasa, gemmi)
~/.venvs/…/DockQ            isolated  (numpy 1.26.4)
~/.venvs/…/prodigy-prot     isolated  (numpy 2.4.6)
```

## 2. Verifying the GPU — why `is_available()` is not the test

The machine is an RTX 5070 Ti Laptop: **Blackwell, compute capability 12.0, `sm_120`**. PyTorch
wheels built against CUDA < 12.8 contain no `sm_120` kernels. They install without complaint,
report `torch.cuda.is_available() == True`, and then fail — or worse, silently misbehave — at
kernel launch.

So the preflight asserts three separate things, because each can pass while the next fails:

1. `torch.version.cuda >= "12.8"` — the build targets a new enough CUDA.
2. `"sm_120" in torch.cuda.get_arch_list()` — kernels for *this* architecture were compiled in.
3. **A real 4096² fp32 matmul, compared against the CPU result.** This is the only check that
   exercises an actual kernel.

Measured: `torch 2.11.0+cu128`, arch list contains `sm_100 sm_120`, max absolute error
**1.02e-03** against CPU — expected for fp32 accumulation at this size, and far from the garbage
a broken build produces. bf16 matmul also runs, which matters because it is the cheap path for
tier-A screening.

Reported VRAM is **11.5 GiB usable** (not the 12.2 GiB `nvidia-smi` prints — the difference is
driver reservation). Budget against 11.5.

**Transferable principle:** for any accelerator, availability, capability and *correctness* are
three different claims. Assert the one you actually depend on.

## 3. The dependency conflict, and why the fix is architectural

`prodigy-prot` requires `numpy>=2`. `DockQ` requires `numpy<2.0`. Both are needed; they cannot
share an environment. This was found by reading PyPI metadata *before* writing any code, which
saved an hour of confused debugging.

The fix is not a pin negotiation — it is `uv tool install` for each, giving them separate
environments and CLI shims, with our metric modules shelling out and parsing stdout.

That sounds like a workaround. It is actually what we wanted anyway: it lets each tool be pinned
**independently** to whatever version the organisers are likely running. Since six of the eight
scored metrics are recomputed by the organisers from our submitted files, version agreement
matters more than convenience. The subprocess boundary is the mechanism that makes independent
pinning possible.

### 3.1 A smaller install trap

`freesasa` builds from C source and needs `Python.h`, which Ubuntu's system Python lacks without
`python3-dev` (a sudo install). Rather than requiring root, the main venv was rebuilt on **uv's
managed CPython 3.12.13**, which ships headers. Torch wheels came from cache, so the rebuild cost
seconds. `uv python install 3.12` + `--python-preference only-managed`.

## 4. The reference structures, and a chain-labelling collision

Fetched from RCSB. Chain composition read from coordinates:

| PDB | Chains | Note |
|---|---|---|
| **5GGS** | A:219 B:217 **C:220** D:217 Y:114 Z:113 | **Two copies** of the complex: A/B/Y and C/D/Z |
| 5DK3 | A:218 B:441 F:218 G:438 | Pembrolizumab Fab alone |
| 5IUS | A:117 B:115 C:214 D:211 | Two PD-1 + two PD-L1 |
| 5WT9 | G:109 H:208 L:216 | Nivolumab + PD-1, single copy |

Two consequences that will bite if ignored:

**(a) The submission convention collides with 5GGS's own labels.** The handbook requires
**Chain A = heavy, B = light, C = antigen**. In 5GGS, chain **C is a second heavy chain**. Any
code that assumes "chain C is the antigen" will compute interface metrics across the wrong pair
of chains — and it will not raise an error, it will return plausible numbers. Hence
`io/pdb.extract_complex()` takes explicit `heavy`/`light`/`antigen` arguments and **returns the
mapping it applied**, because once written the mapping is not recoverable from the output file.

**(b) Which copy to use is a real choice.** Copy C/D/Z has the more complete heavy chain (220 aa;
chain A is missing its N-terminal Gln). Copy A/B/Y has the more complete antigen (114 vs 113).
Not yet decided — it must be, and recorded, because DockQ is measured against whichever we pick.

Heavy chains are ~220 aa, i.e. **Fab length** (VH + CH1), which matches the handbook's example
FASTA. Weak evidence that Fab is the expected submission form.

## 5. IMGT numbering, and the CDR definitions that matter

### 5.1 What IMGT numbering is, and why the scheme choice is not cosmetic

Antibodies vary enormously in loop length, so raw sequence position means nothing across two
different antibodies — residue 100 in one is not the structural equivalent of residue 100 in
another. A **numbering scheme** assigns canonical position numbers, inserting gaps and insertion
codes so that structurally equivalent positions receive the same number in every antibody.

The handbook specifies **IMGT**, where the CDRs occupy fixed position ranges:

```
CDR1  27–38        CDR2  56–65        CDR3  105–117
```

This is what makes "CDR-H3 identity" a well-defined quantity. Use a different scheme (Kabat,
Chothia) and you extract a different substring and compute a different identity — against the
same reference. **The scheme is part of the metric definition, not an implementation detail.**

### 5.2 Measured CDRs

Via ANARCII (pure-Python; chosen over ANARCI specifically because ANARCI needs the HMMER binary,
which is absent here and would need a sudo install):

| | CDR-H1 | CDR-H2 | **CDR-H3** | len |
|---|---|---|---|---|
| **Pembrolizumab** (5GGS A/C) | `GYTFTNYY` | `INPSNGGT` | **`ARRDYRFDMGFDY`** | **13** |
| Nivolumab (5WT9 H) | — | — | `ATNDDY` | 6 |

Light chain (both 5GGS copies): CDR-L1 `KGVSTSGYSY`, CDR-L2 `LAS`, CDR-L3 `QHSRDLPLT`.

**The novelty arithmetic is now exact.** CDR-H3 is **13 residues**, so identity moves in steps of
1/13 ≈ 7.7%:

- `< 95%` (the hard gate): ≥ **1** substitution → 12/13 = 92.3% ✓
- `< 70%` (the Good band, worth 10/10): ≥ **4** substitutions → 9/13 = 69.2% ✓

Four substitutions in a 13-residue loop for full novelty marks. Very reachable — which confirms
the §1.2 analysis in the plan that novelty is the cheapest points on the board.

*(My earlier estimate of 11 residues was the Kabat definition, `RDYRFDMGFDY`. IMGT includes the
preceding `AR`. The distinction matters precisely because it changes the denominator.)*

### 5.3 An encouraging scientific observation

Pembrolizumab's CDR-H3 is **13 residues**; nivolumab's is **6**. Both are clinically approved
anti-PD-1 antibodies binding the same target. PD-1 is therefore bindable by radically different
H3 architectures — which is genuinely good news for Challenge 2, where we need a *novel* solution
rather than a perturbation of a known one.

## 6. The trap worth the whole session

**ANARCII confidently numbered PD-1 as an antibody chain and assigned it CDRs.**

PD-1 is a member of the **immunoglobulin superfamily** — it has an **IgV fold**, the same
β-sandwich architecture as an antibody variable domain. That is not a coincidence of shape; it is
shared ancestry. So a tool trained to recognise V domains recognises it, because by fold it *is*
one.

With a permissive score threshold the output was:

```
Y:  114aa  H score=15.8   CDR3=GAISLAPKA     <- this is the ANTIGEN
Z:  113aa  K score=16.2   CDR3=GAISLAPKA     <- also the antigen
```

Genuine antibody V domains score **30.7–30.9**. PD-1 scores **15.8–16.2**. The separation is
clean, but only if you look for it.

Had this gone unnoticed, any pipeline step that auto-detects "which chain is the antibody" would
have assigned PD-1 a CDR-H3 and computed novelty, CDR SASA and interface identity **on the
antigen**. Every number would have been real, finite, and wrong. Nothing would have crashed.

Fix: `MIN_V_DOMAIN_SCORE = 25.0`, documented in-code with the measured values and the reason,
plus explicit chain assignment rather than auto-detection for the reference structures.

**Transferable principle — and it is the same one as the mislabelled-telemetry incident:** a
classifier that returns a *confident* answer on out-of-distribution input is the most dangerous
failure mode there is, because the output is well-formed. Always check the score distribution of
your known negatives, not just that your positives pass.

## 7. A second, duller bug

`gemmi.Structure.remove_ligands_and_waters()` raises `RuntimeError: missing entity_type in chain A`
unless `setup_entities()` has been called first. It happened to work on 5GGS (which carries the
metadata) and failed on 5WT9 (which does not) — so the ordering bug was invisible on the first
file tested.

**Principle:** a pipeline step that works on your first test file has been tested once, not
validated. Run it across the whole reference set before trusting it.

## 8. A fifth unresolved convention

`ipsae.py` takes **`pae_cutoff` and `dist_cutoff`** as required command-line arguments (the
repo's examples use `10` and `15`). The handbook specifies neither. These change the computed
value materially.

Added to the list of conventions the harness must treat as configuration rather than constants:
CDR SASA bound/unbound, Fab/Fv, ipSAE chain pairing, DockQ chain mapping — and now ipSAE cutoffs.
Default to the repo's documented `10 / 15` and flag it for Ajitesh.

## 9. The scoring harness, and the crossed-chain trap

### 9.1 The trap: 5GGS's two copies are paired *crosswise*

5GGS contains two copies of the complex. The natural reading of the chain labels is that
A/B (Fab) goes with Y (antigen), and C/D with Z. **Both are wrong.** Contact analysis at
5 Å heavy-atom:

```
A-B: 103 residues     <- heavy/light, within Fab 1
C-D:  99              <- heavy/light, within Fab 2
B-D:  64              <- crystal packing between the two light chains
A-Z:  41   B-Z: 26    <- Fab A/B binds antigen Z
C-Y:  39   D-Y: 25    <- Fab C/D binds antigen Y
```

The true complexes are **A/B/Z** and **C/D/Y**. Extracting A/B/Y produced a "complex" with
**zero** interface residues.

How it surfaced, and how it nearly did not: PRODIGY refused the explicit selection with
`No contacts found for selection` — a real error. But run **without** `--selection` on the
same file it returned a confident **ΔG = −16.3 kcal/mol**, because it silently scored the
**heavy/light** interface instead. A number in exactly the right range, for entirely the
wrong interface.

Two rules follow, both now enforced in `metrics/prodigy.py`:

1. **Never let an interface-scoring tool choose its own chains.** Selection is always explicit.
2. **Verify the interface exists before measuring it.** An interface with zero contacts is a
   structural fact, not an edge case, and every metric downstream of it is meaningless.

Note also the **B-D contact of 64 residues** — larger than either real epitope. It is crystal
packing between two light chains. A heuristic like "take the largest non-heavy/light interface"
would have selected a lattice artefact as the epitope.

### 9.2 What was built

`config/metrics.yaml` holds the rubric **as data** — all eight bands, the category weights, and
the five unresolved conventions as switches. `score.py` is a pure function of (raw values, config):
nothing cached, nothing stored, so changing a convention costs a re-run rather than a re-fold.

Metric modules: `prodigy` (ΔG + contacts), `dockq`, `ipsae`, `plddt`, `sasa`, `novelty`,
`interface`, and `netsolp` (an explicit not-implemented stub — see §9.5).

Provenance is enforced in the type system. `Provenance.EXPERIMENT` structures have
`has_pae == False` and `has_plddt == False`, so ipSAE and interface pLDDT **refuse to compute**
rather than reading a B-factor column that holds thermal displacement and returning a plausible
number. A crystal B-factor of 30 Å² is not a pLDDT of 30.

### 9.3 Gate 0 — passed

```
[ ok ] DockQ(5GGS, 5GGS) == 1.000                       1.0
[ ok ] CDR-H3 identity(5GGS, Keytruda) == 100%          100.0%
[ ok ] native pembrolizumab passes every binding gate   failing: none
[ ok ] native pembrolizumab FAILS novelty (it is the clone)   identity 100.0%
[ ok ] decoy is rejected                                failing: dockq, contacts, cdrh3_identity
[ ok ] two ASU copies agree on dG (spread 0.40 kcal/mol)      -14.3 vs -13.9
```

The full calibration table is in [results/calibration.md](../../results/calibration.md).

**One assertion in the gate was wrong and had to be corrected — the harness was right.** The
first run reported "native pembrolizumab passes every computable gate: FAIL — failing
`cdrh3_identity`". Pembrolizumab's CDR-H3 is 100% identical to Keytruda's **because it is
Keytruda**. The novelty gate exists to reject trivial clones, so the reference molecule *must*
fail it. That failure is the metric working. The check now requires pembrolizumab to pass every
*binding* gate and to **fail** novelty — which is a stronger test than the original, because it
asserts the novelty metric discriminates rather than merely runs.

**Principle:** when a calibration fails, the first hypothesis is that the assertion encodes a
wrong expectation, not that the measurement is broken. Check the expectation before changing the
code.

### 9.4 Calibration numbers worth carrying forward

- **PRODIGY predicts Kd 34 pM for pembrolizumab; measured is 29 pM.** *Corrected 2026-09-16:*
  this was written up as validation of accuracy, which overstates it. PRODIGY's RMSE is
  ~1.5–2 kcal/mol and ~1.4 kcal/mol is a **tenfold** change in Kd, so a 0.1 kcal/mol
  agreement sits well inside its noise — coincidence, not precision. What it genuinely
  validates is plumbing: the tool ran on the correct interface with the correct chain
  selection. Treat ΔG as **ordinal**.
- **DockQ noise floor is 0.867** — two copies of the same molecule in the same crystal. A design
  above ~0.87 is indistinguishable from crystallographic variation, so 1.0 is neither achievable
  nor meaningful as a target.
- **ΔG spread between identical copies: 0.40 kcal/mol.** That is the metric's real error bar.
- **Nivolumab, an approved drug, scores only *medium* on ΔG (−10.0).** The bands are demanding.
- **CDR SASA bound-vs-unbound is moot**: 1564 vs 2460 Å², both far above the 600 Å² good band.
  One of the five unresolved conventions has no practical effect. Resolved by measurement.
- **The decoy passes CDR SASA** (2460 Å², "good") because nothing is buried, so the paratope is
  maximally exposed. **CDR SASA alone cannot detect a non-interface** — the concrete argument for
  why the binding score must be driven by its *minimum* member, not its mean.

### 9.5 What is still unknown

Three of eight metrics were not exercised: **ipSAE** and **interface pLDDT** are undefined on
experimental structures and get their first real test in Phase 1 on a predicted complex;
**NetSolP** is not installed, and `metrics/netsolp.py` returns an explicit skip rather than
substituting a different solubility predictor and reporting it under NetSolP's name.

Consequently `viable` is reported as `None`, not `True`, for every subject — the harness will not
assert viability while any metric is unknown.

## 10. The DockQ default that would have silently killed every Challenge 1 design

Flagged as a loose end, tested, and it turned out to be a genuine blocker rather than a
theoretical one.

### 10.1 The test

DockQ must first solve a **correspondence problem** — which model residue is which native
residue, which chain maps to which. To isolate *alignment* failure from *pose* difference, the
test changes the sequence while leaving **every coordinate byte-identical**. The pose is then
unchanged by construction, so any DockQ below 1.000 is pure correspondence failure.

Five variants against native 5GGS A/B/Z: 4 substitutions in CDR-H3 (the realistic Challenge 1
case), 8 substitutions across H1/H2/H3, two residues deleted from H3, two duplicated, and the
chains written in C,B,A order.

### 10.2 The result, which was the opposite of the prediction

```
identity  (control)     1.000
sub4      (realistic)   FAILED      <- no score at all
sub8      (aggressive)  FAILED      <- no score at all
del2      (H3 shorter)  1.000
ins2      (H3 longer)   1.000
reorder   (C,B,A)       1.000
```

I had predicted **indels** would be the hard case and substitutions trivial. Exactly backwards.
DockQ's message:

```
WARNING: Some chains have a limited number of sequence mismatches and are treated as
non-homologous. Try increasing --allowed_mismatches: Model chain A, native chain A: 4 mismatches
ERROR: For chains ['A'] no identical corresponding chain was found between in the native.
```

**`--allowed_mismatches` defaults to 0.** DockQ assumes it is comparing the same complex
predicted-versus-experimental, so any sequence mismatch reads as "you have paired the wrong
chains" and it refuses to score. Insertions and deletions pass because they do not create
mismatches *at aligned positions* — the aligner simply skips them. Only substitutions trip it.

### 10.3 Why this mattered

**Every Challenge 1 design is pembrolizumab with mutated CDRs.** At the default, DockQ would
have refused to score **every design the pipeline produces** — returning `None`, propagating to
`viable=None`, leaving nothing selectable. The pipeline would have run to completion, thrown no
exception, and produced an empty shortlist. We would have gone looking for a bug in the design
code.

Four substitutions is enough to trigger it, and four substitutions is the *minimum* to reach the
Good novelty band (§5.2 arithmetic: 9/13 = 69.2%). So the failure would have hit on literally
the first design worth submitting.

### 10.4 The fix, and a second flag worth pinning

`metrics/dockq.py` now passes `--allowed_mismatches 40`. A full heavy-chain redesign spans
CDR-H1(8) + H2(8) + H3(13) = **29 positions**, so 40 leaves headroom. After the fix: sub4 →
1.000, sub8 → 0.960.

It also now pins `--mapping ABC:ABC`. Left free, DockQ *searches* for a chain mapping; a wrong
one would score a good design badly, and the output gives no obvious sign. Our files are always
A=heavy, B=light, C=antigen, so the mapping is known and should be asserted rather than
rediscovered per run.

The residual 0.960 on sub8 is **test artefact, not pose change**: the test renames residues
without rebuilding side chains, so a renamed residue carries atoms that do not belong to its new
type and DockQ discards them, costing a few atom-level contacts. Coordinates are identical, so
the pose cannot have moved. Said plainly rather than papered over with a threshold.

### 10.5 The principle

**A tool's defaults encode its author's assumed use case, not yours.** DockQ's default is correct
for its intended use — validating a prediction of a *known* complex, where a sequence mismatch
really does mean you have made a mistake. Our use case is the adjacent one the default was never
written for: comparing a *deliberately mutated* design against a reference.

The general form: when a tool refuses to produce output, that is the *good* failure. The
dangerous defaults are the ones that produce a number anyway. This one announced itself; the
B-factor/pLDDT collision and the crossed-chain pairing did not.

## 11. What is not done

No folding stack: neither ColabFold nor Boltz is installed, so the JAX-on-Blackwell risk is still
unmeasured and ipSAE has never actually run. NetSolP absent. No MPNN, no designs, nothing
generated. The submission validator and its dummy-file dry run are unwritten.

Also unresolved: DockQ returned **no interfaces at all** when comparing 5WT9 (nivolumab) against
5GGS — expected, since the sequences are unrelated, but it means DockQ's tolerance to sequence
divergence is untested. Challenge 1 designs differ from pembrolizumab by only a few CDR residues,
so this probably will not bite; it should still be checked before it matters.

**Next:** install a predictor, re-predict 5GGS from sequence with **templates disabled**, and
score it — that exercises ipSAE and interface pLDDT for the first time and answers the deepest
scientific risk in the project.
