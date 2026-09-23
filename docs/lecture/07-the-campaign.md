# 07 — The Campaign: nine days, 1,266 folds, in order

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [[CORRECTIONS|correction C1, and what it does and does not invalidate]]. Challenge 1 is unaffected.

## What this chapter teaches

Earlier chapters taught the pieces: checkpoint biology, the rubric, the tools, measurement
theory, experiment design, allocation. This chapter puts them back into the order in which
they happened, 2026-09-14 to 2026-09-22.

Order matters more than usual here, because **the largest defect in this project is an
ordering defect** and it is invisible from a topic-by-topic treatment: almost every expensive
thing was done before the cheap thing that would have said whether it was worth doing. For
each day you should finish able to say what was attempted, what was learned, what broke, what
it cost, and — the part that teaches — *what the next day inherited, including what it
inherited for bad reasons*.

---

## The ledger, before the narrative

**Folds per day**, from the modification times of the `pae_*.npz` files [[03-the-toolchain#3.1 Boltz-2 — the primary predictor|Boltz-2]] writes for
every completed prediction. One fold = one prediction that produced a parseable Predicted
Aligned Error (PAE) matrix.

| day | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | total |
|---|---|---|---|---|---|---|---|---|---|---|
| date (2026-09-) | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | |
| folds | 0 | 2 | 18 | 49 | 120 | 375 | **507** | 0 | 195 | **1,266** |

One fact dominates. **564 of 1,266 folds — 45% — were spent before the project's first
validity experiment existed.** That experiment is `scripts/48_epitope_knockout.py`, created
2026-09-20 11:53, and its job is to ask whether the metrics respond at all when you destroy
what they claim to measure. Everything through day 6 measured more precisely; nothing before
day 7 asked whether the measured quantity carried information. Most of day 7's 507 folds ran
*concurrently* with the knockout rather than informed by it.

The same defect as first-appearance dates: session doc day 1; `src/` code and first fold day
2; positive control day 3; pre-registration day 4 (10:45); **validity experiment day 7**
(11:53); **git day 9** (00:20); **tests day 9**; **negative control with known-wrong
antibodies day 9** (23:42). All **35 git commits are dated 2026-09-22**, the first reading
*"Initial commit: put 12,430 lines under version control"*. For eight days ~12,000 lines of
scientific code had no version history and no automated invariant checking, so every
correction lived in prose — and, per `results/audit_response_2026-09-22.md:8`, *"prose cannot
fail a build."*

---

## Day 1 — 2026-09-14. Reading the specification. 0 folds.

The whole day went into the organisers' handbook, read from the PDF rather than a summary.
Output: a 497-line session doc, no code, no compute.

```
Final Score (0–100) = [ 0.60 × Binding_struct + 0.20 × Developability
                        + 0.20 × Novelty ] × 10
```

Each category term is 0–10. `Binding_struct` is the **mean** of six sub-scores for Challenge 1
([[03-the-toolchain#4.3 ipSAE — interface confidence from the PAE|ipSAE]], [[03-the-toolchain#4.1 DockQ 2.1.3 — two flags that both default wrong|DockQ]], ΔG, interface contacts, interface pLDDT, CDR SASA) and of five for Challenge 2,
which has no DockQ because a de novo design has no reference structure. `Developability` is
one metric ([[03-the-toolchain#4.4 NetSolP-1.0 — sequence-only solubility, and a positive control that chose the model|NetSolP]] solubility); `Novelty` is one (CDR-H3 identity). Each of the eight metrics
maps a raw value onto 0–10 through three bands and carries a hard cutoff below which the
design is not penalised but **non-viable**. Challenge 1 redesigns pembrolizumab's heavy-chain
CDRs on PDB entry **5GGS**; Challenge 2 designs a VH/VL de novo. 100 + 100 + 50 presentation =
250 points.

Three pieces of arithmetic, done with no compute, shaped everything after. **One design per
challenge** — the checklist permits one folder each, no "submit ten, keep the best" — converts
the task from *generate-and-rank* into *generate, rank internally, bet on one*, which is why so
much of the project is about the [[04-measurement-theory#1.3 Reliability|reliability]] of a ranking; see
[[06-allocation-and-selection|how a fixed fold budget splits between candidates and seeds]].
**Optimise the minimum of the binding sub-scores, not the mean**: binding is a mean over six, so
lifting the weakest sub-score from 5 to 9 is worth `0.60 × (4/6) × 10 = 4.0` points and lifting an
already-good one is worth nothing — the same insight (*under an aggregator, find the argmin
first*) that refutes the project's own top recommendation on day 9. And **novelty is nearly
free**: push CDR-H3 identity below 70% for 10/10, the two single-metric categories being 40% of
the score and far cheaper to max than the six-metric binding mean.

**Seven handbook contradictions were logged rather than guessed away**, which is why the project
could later separate "we chose a convention" from "the handbook said so". CDR SASA is not
specified bound or unbound, and the two readings *conflict in sign* with the contacts metric
(better burial ⇒ more contacts but **less** bound CDR SASA). The example FASTA is Fab-length with
a His-tag while NetSolP is documented on Fv. Band-edge ties are undefined. And contacts and ΔG
both come from [[03-the-toolchain#4.2 PRODIGY 2.4.0 — ΔG and contacts|PRODIGY]] on the same interface yet occupy two of six binding slots — prophetic,
since on day 7 PRODIGY's ΔG proves blind to the interface.

**Inherited by day 2:** a rubric expressed as data, and the commitment in `PLAN.md` §3 —
*[[02-the-engineering-problem#6. Build the judge before the contestant|build the judge before the contestant]]*, gated behind G0: *"Harness reproduces ground truth;
pembrolizumab passes every binding gate and fails novelty; decoy rejected."* The best decision
in the project.

---

## Day 2 — 2026-09-15. The environment, and two traps that produce plausible wrong answers. 2 folds.

`knowledge/The Environment Saga.md` opens honestly: **roughly half the day went into getting
software to run at all.**

**The [[03-the-toolchain#5. The numpy 2.0 fault line, and isolation as architecture|numpy 2.0]] fault line.** `prodigy-prot` 2.4.0 requires `numpy>=2` (2.4.6); DockQ 2.1.3 and
Boltz-2 2.2.1 require `numpy<2` (1.26.4); the main environment wants `numpy>=2` (2.5.3). Genuine
incompatibilities — **the tools physically cannot share an environment**. Resolution:
`uv tool install` per conflicting tool, each with its own environment and a CLI shim, invoked as
subprocesses with stdout parsed. Framed as an asset, not a workaround: the organisers recompute
six of eight metrics from the submitted files, so pinning each tool independently to a grader's
likely version beats convenience, and the architecture absorbed Boltz as a third conflict with no
redesign. Real layout: **four hand-made venvs plus three `uv tool` environments = seven**, two
more than `BUILD.md` documents.

Two smaller lessons. `freesasa` compiles from C and the system Python ships no development
headers, which need root — fixed by rebuilding on uv's managed CPython 3.12.13, which ships
them. And resizing the 8 GB swapfile needs `swapoff`, which faults **every** swapped page back
into RAM one at a time; 3.2 GB took minutes and looked like a hang. Additive beats mutative:
`fallocate -l 16G` + `mkswap` + `swapon` ≈ five seconds, total 24 GB, `vm.swappiness=10`.

**The GPU was verified by arithmetic, not introspection.** `scripts/00_doctor.py` requires
`sm_120` in `torch.cuda.get_arch_list()` *and* a real 4096² fp32 matmul matching the CPU to
`max abs err < 1e-2`. Not fussiness: on day 7 the project meets two environments where
`is_available()` returns `True` and every kernel fails.

**Two traps that would have produced confident wrong numbers**, caught only because the harness
was run on molecules whose answers were known.

*[[03-the-toolchain#4.5 ANARCII 2.0.8 — IMGT numbering, and the antigen it numbered as an antibody|ANARCII]] numbers PD-1 as an antibody.* PD-1 is an immunoglobulin-superfamily member with an
**[[01-the-biological-problem#2.5 The IgV fold, and the trap it set|IgV fold]]** — by fold it *is* a V domain — so ANARCII assigns it `CDR3=GAISLAPKA`. Correct
behaviour on out-of-distribution input, not a bug. The separation is in the score: true V
domains **30.7–30.9**, PD-1 **15.8–16.2**. Mitigation: `MIN_V_DOMAIN_SCORE = 25.0` plus explicit
chain assignment, never auto-detection. Without it, every CDR metric can be computed on the
antigen.

*A gemmi call-ordering bug invisible on the first test file.* `remove_ligands_and_waters()`
needs `setup_entities()` first. It **worked on 5GGS**, which carries the metadata, and failed on
5WT9, which does not: `RuntimeError: missing entity_type in chain A`. *A pipeline step that works
on your first test file has been tested once, not validated.*

**A third trap sits in the reference structure.** 5GGS holds two copies and the natural reading
of the labels is wrong: **A/B binds Z and C/D binds Y**. The first extracted "complex" had
**zero** antibody–antigen contacts, caught because PRODIGY refused with `No contacts found for
selection`. Worse, the largest non-heavy/light interface in the crystal is **B–D, 64 contacting
residues between the two light chains** — lattice packing, larger than either real epitope (A–Z
41, B–Z 26; C–Y 39, D–Y 25), so a "biggest interface that isn't heavy–light" heuristic would have
picked a crystal artefact as the binding site. `extract_complex()` now takes explicit chains and
**returns the mapping it applied**, which is unrecoverable from the file afterwards.

Pembrolizumab's CDR-H3 was confirmed as `ARRDYRFDMGFDY`, 13 residues. One overstatement entered
and was corrected next day: PRODIGY's Kd 34 pM against a measured 29 pM, written up as validation
of accuracy; PRODIGY's own RMSE makes a single-point agreement uninformative.

**Inherited by day 3:** seven environments, a verified GPU, four reference structures — and,
invisibly, the **113-residue PD-1 construct** from 5GGS chain Z, never re-examined for the whole
project, which on day 9 costs a positive control.

---

## Day 3 — 2026-09-16. The first real prediction, and the four attempts it took. 18 folds.

**The four-attempt fold** is the origin of the project's hardest rule:

| attempt | failure | exit | real cause | fix |
|---|---|---|---|---|
| 1 | killed partway | killed | **host RAM**: 15 GiB box, ~9 GB held by browser/chat, ~4 GB of weights, and *three concurrent decompressions of a 6 GB archive* run by the author | stop competing with yourself |
| 2 | `ModuleNotFoundError: cuequivariance_torch` | **0** | optional CUDA kernels not installed; Boltz imports them anyway rather than falling back | `--no_kernels` |
| 3 | `OOM on device 0 … 1616904192 bytes`, `Number of failed examples: 1`, **under a `100%` bar** | **0** | **GPU VRAM**, not host RAM — a different resource, so the swap work had fixed the wrong one | drop antibody-chain MSAs |
| 4 | success | 0 | — | **34 s** |

**Three of four reported success or said nothing useful.** That turned *"check the artefacts,
not the exit code"* into a hard rule, now enforced by `assert_artefacts()` in
`src/locksmith/fold/__init__.py`, which rejects a missing PDB/PAE/pLDDT, a zero-byte PDB, a PDB
with no `ATOM` records, a truncated `.npz` that exists but fails at read time, a non-square PAE,
and a missing pLDDT sibling. Existence is not enough. Second lesson: *"out of memory" is at least
two different problems on a GPU machine, with different fixes.*

The attempt-3 fix is the day's nicest result, because cheap and correct coincide. An antibody and
its antigen have not co-evolved, so a multiple sequence alignment over antibody chains carries
**no interface signal** — which is why antibody-specific predictors work from single sequences.
Dropping two of three chains' MSAs is scientifically right *and* cut VRAM by ~2/3.

**The result: Boltz-2 recovered the pembrolizumab–PD-1 pose untemplated at DockQ 0.820.** DockQ
measures how close a predicted complex is to a reference; above 0.80 is CAPRI "high quality".
Every later claim is calibrated against this number — and, as the project noted the same day, it
is a structure the model has almost certainly memorised, which is why day 4 spends its budget on
a memorisation test.

**A fourth failure, downstream.** ipSAE locates its pLDDT array by *string-substituting the PAE
path*: `pae_file.replace("pae", "plddt")`. Files had been renamed, the sibling was unfindable,
and `ipsae.py` **wrote a zero-byte table and exited 0**. Caught by luck — the project's own parser
crashed reading a header from an empty file.

**NetSolP, and the positive control that changed the answer.** NetSolP-1.0 predicts solubility
from sequence and ships three variants. On **pembrolizumab**, a licensed antibody that must pass
a developability screen, against the 0.50 cutoff:

| construct | ESM1b (5-fold) | ESM1b-distilled | ESM12 (5-fold) |
|---|---|---|---|
| VH | **0.733** | 0.637 | 0.379 |
| VL | **0.569** | 0.463 | 0.346 |
| Fab heavy | **0.623** | 0.491 | 0.352 |
| Fab light | **0.626** | 0.448 | 0.312 |

Only the ESM1b 5-fold ensemble clears the cutoff everywhere. The other two **fail a marketed
antibody**, which would have discarded good designs silently and looked exactly like a design
problem rather than a configuration one. The spread across variants is **0.35, wider than the
0.20 cutoff-to-Good span**. ESM1b became a *declared convention* in `config/metrics.yaml` with
evidence attached. Cost ~11 s/sequence against ~2 s for ESM12, paid on CPU while the GPU folds.

[[03-the-toolchain#3.2 ColabFold / AlphaFold2-multimer|ColabFold]]/AF2 was installed and JAX verified on Blackwell by matmul. The first cross-predictor
number looked like a scale offset — Boltz ipSAE **0.841** versus AF2's **0.654** on the same
complex — until DockQ showed AF2's pose was genuinely worse (0.690 vs 0.820), so part of the gap
was *deserved*. **When comparing two estimators' confidence, first compare their accuracy.**

**Inherited by day 4, and for how long.** `recycling_steps=3` and `diffusion_samples=1` (both
`fold/boltz.py:80`) entered here and were examined on **day 9**. The **antigen-only MSA** —
correct for redesigning a known antibody — was carried unchanged into a de novo VH/VL on day 8
and **never examined**; `STATE.md:350` still lists testing it as step 2 of the shortest path
forward. The fold budget was set at 34 s/fold ⇒ **~4,700 folds**, withdrawn on day 4.

---

## Day 4 — 2026-09-17. The Fv screen fails; the memorisation test fails; the memorisation test is withdrawn. 49 folds.

Four session documents, and the best teaching episode in the project.

**The variant panel and G1c.** Fourteen hand-mutated pembrolizumab variants — test articles for
the *scoring protocol*, not designs — folded as both Fv (variable domains) and Fab (variable plus
first constant domains): 48 folds, 82 minutes, zero failures. Could the cheaper Fv fold screen
for the Fab? **No.** Fv ipSAE seed reliability is **0.607** against Fab's **0.965**, so the cheap
screen costs *more* at usable precision. Fab-only adopted. Note this: on day 8, Challenge 2 is
folded as **Fv** anyway.

**ipSAE is a liveness test, not a ranking metric.** ipSAE versus DockQ over the panel looked
excellent at Fab R² = **0.755** — until the two deliberately-dead poly-Gly variants were dropped,
at which point R² collapsed to **0.263** and the slope flattened threefold. Across the plausible
series DockQ fell 0.820 → 0.601 while ipSAE wandered within ±0.04 of 0.82, and the *highest*
ipSAE in the panel (0.867) belonged to a variant at DockQ 0.742 against the wild type's 0.820.
Rule: **report it, gate at 0.60, never rank on it**; see
[[04-measurement-theory|why an outlier-anchored R² is not a ranking claim]].

**The memorisation test, pre-registered at 10:45.** Boltz-2's training cutoff was read from the
paper's own PDF — **2023-06-01 on PDB *release* date**, not deposition. Five complexes released
after it were selected, with novelty screened on **CDR-H3 identity (21–44%)** rather than
whole-chain, because framework conservation puts every antibody at 86–94% identity to something
pre-cutoff; antibody and antigen were screened separately.

**Verdict FAIL.** Median Fab DockQ **0.157** against 5GGS's 0.818, 4 of 5 below the CAPRI
acceptable floor. The ipSAE↔DockQ calibration appeared to collapse (Spearman **+0.815 → +0.308**
Fv, **+0.200** Fab; residual spread **6.9×**), with 9W43 at Fv ipSAE 0.722 on a DockQ-0.070
structure. Conclusion: *"Challenge 2 should not proceed as designed."*

**Then a control not in the brief fired.** The check was cheap: read the *author residue
numbering* and look for internal gaps. `chains()` built sequences from **coordinates**, and
residues unresolved in a crystal are simply absent, so flanking residues concatenate — the
sequence handed to the folder describes a **chimera with internal loops deleted and the ends
fused**. Four of five targets were affected: 9W43's antigen folded **83 aa against a true 115**,
losing 32 residues across the epitope face; 9BQW's folded 132 against 163, losing 19.

Re-prepared from **SEQRES** — the record of what the crystallographers put in the tube, as
opposed to the atoms they could see:

| as published | corrected |
|---|---|
| verdict **FAIL**, median Fab DockQ **0.157** | verdict **MARGINAL**, median **0.291**; 9BQW **0.064 → 0.370** |
| calibration collapses: Spearman **+0.308** / **+0.200**, residual **6.9×** | **+0.900** both (p=0.037); residual **2.7×** Fv, **1.3×** Fab |
| "confident but completely wrong": 9W43 Fv ipSAE 0.722 at DockQ 0.070 | 9W43 Fv ipSAE **0.109** at DockQ 0.049. **Nothing clears the 0.60 gate on a wrong structure** — the direction *inverts*: ipSAE is conservative on novel complexes, mean residual **−0.283** |

Two of three conclusions withdrawn; milestone M4 un-suspended. The rule: **a large interface at
near-zero DockQ is as easily your input preparation as the model's error.** The check "takes
seconds and would have caught this before 16 minutes of GPU time and a milestone decision."

**The sweep.** Every coordinate-to-sequence site was then swept. **5GGS has zero internal
deletions**, so the variant panel, calibration curve, positive control and novelty numbers all
stand and nothing was re-run; 5WT9's gap is in CH1 after its V domain, 5IUS's two-residue hole
misses no footprint residue. `seq_for_folding()` now **raises on an internal deletion and permits
terminal truncation**, which leaves no gap in author numbering and is harmless.

The budget was corrected too: 34 s is the *fold*, but a `boltz predict` **invocation** costs
**92 s (Fv) / 126 s (Fab)** because ~60 s of checkpoint load and MSA parsing is fixed. Budget
**~4,700 → ~1,290 Fab folds** — a 3.6× overestimate that had shaped the design space for a day.

---

## Day 5 — 2026-09-18. A baseline that passes everything. 120 folds.

**The selection key, argued with arithmetic.** A prior session recommended ranking on DockQ. The
rubric disagrees: one band step on `cdrh3_identity` moves `final` by **14.0 points** and one step
on `dockq` by **7.0** — novelty is priced at **2× DockQ**. A faithful design (96% identity, DockQ
0.88) scores **81.0 and is non-viable**; a divergent one (55%, DockQ 0.55) scores **92.5 and is
viable**. Ranking on DockQ would promote near-copies and then fail them on novelty.
`selection_key: final`.

**The baseline, and the most load-bearing negative result in Challenge 1.** Twenty plain
[[03-the-toolchain#2.1 ProteinMPNN|ProteinMPNN]] designs at defaults, no filtering: **20 of 20 clear all eight gates.** The gates do
not bite on fixed-backbone redesign, because the binding geometry is guaranteed by the native
backbone you did not change. Without this, "our funnel produced 20 viable designs" would later
have read as a result. In the same pass **pembrolizumab itself scores 76.0 and is non-viable**,
failing novelty at 100% CDR-H3 identity to itself — a harness that scored the parent as viable
would have been silently wrong about the one molecule whose answer is known. Among designs,
ipSAE↔DockQ Spearman is **+0.013**: no ranking information at all.

**Re-seeding, with the prediction made first.** The top 8 were re-folded (16 Fab folds).
Reliability — the fraction of observed score variance that is real between-design variance rather
than seed noise — was **predicted at 0.700** from `seed_sd / between_design_sd = 55%` *before*
running, and **measured at 0.727**. Single-seed ranking resolves tiers but not neighbours: the
top two differed by **0.001 DockQ**, one eighteenth of the 0.018 seed sd, and the winner changed
with the seed. Winner's curse **−0.0079 DockQ**.

**The CDR-H3 ensemble.** Across 8 designs *identical on the rubric* — same composite, all gates
passed — CDR-H3 backbone RMSD between seeds spanned **0.33–1.45 Å (4.4×)**, maximum deviation
**4.31 Å**. One design carried mean loop pLDDT **90.5**, nominally very high confidence, on a
loop moving 4.31 Å. Mean loop pLDDT was reported **blind** to this: Spearman **−0.168, p=0.69,
n=8**. Hold that number.

**The free feature that beat the paid one.** A pre-registered test asked whether ensemble
tightness earned a selection axis: 40 designs × 3 seeds, no gating before the correlation,
deliberately, because shortlisting first restricts the range of the variable under test. Primary:
spread→DockQ **−0.387 (p=0.014)**. But **CDR-H3 aromatic fraction**, computable from sequence at
zero fold cost, predicted spread at **+0.621** *and* DockQ at **−0.536**. The [[05-experiment-design#3. Partial correlation, and a result that half-reversed|partial correlation]]
settled it: ensemble→DockQ controlling aromatics collapsed to **−0.081 (p=0.62)** while
aromatics→DockQ controlling ensemble survived at **−0.410 (p=0.009)**. The **ensemble axis was
dropped from selection**; aromatic fraction became a candidate pre-fold filter. Hold this too.

**What a pre-fold filter has to beat**, established over folds already paid for: a filter must
beat **the same rule applied at random, at equal budget**, not the unfiltered pool — a random
subset retaining fraction *f* keeps the pool maximum with probability exactly *f*. Measured, the
aromatic filter beat 20,000 equal-size random subsets on **mean** DockQ (p=0.017–0.034, +0.0137 ≈
one seed sd of 0.018) but was **indistinguishable from chance on the maximum** (p=0.399 / 0.499 /
0.600 at 40/50/60% retention, rising monotonically with retention — the signature of pure luck).

**The composite's own reliability was measured for the first time**, after four sessions of
reasoning from DockQ's 0.727: `final` is **0.602 single-seed, 0.780 at 3 seeds**, with **22 of 40
designs changing score across seeds** as `ipsae` (16) and `dg` (17) cross band edges in full
2.5-point steps. Banding destroys resolution too: 40 designs collapse onto **three distinct
values, {82.5, 85.0, 87.5}**.

The day ended by launching M3's primary arm unattended: **239 designs across four ProteinMPNN
sampling temperatures** (T ∈ {0.1, 0.2, 0.3, 0.5}), CDR-H3 length fixed, **fold order shuffled
with `random.Random(0)`** so any prefix of an interrupted night is a balanced sample across all
four arms, and **everything folded unfiltered** (~30 extra folds ≈ 23 min) because folding only
the survivors makes any claim about what the filter discarded circular. One thing written this
day was wrong and withdrawn the next: the session recast the 85 s/fold rate as a 1.65× sizing
error on four samples taken while the author ran analyses on the same machine — *a
correctly-labelled estimate overridden with contaminated data.*

---

## Day 6 — 2026-09-19. The 239-design campaign, and 239/239 scoring failures. 375 folds.

**The folding went perfectly**: 239 of 239 in **6.0 hours at median 84 s/fold**, retroactively
withdrawing the previous day's "correction".

**The scoring failed completely and told nobody.** Three defects stacked in one incident, three
different classes of the same mistake.

*The fork.* A refactor merged a serial NetSolP stage into the same script as a six-worker
parallel scorer. `ProcessPoolExecutor` uses `fork` by default on Linux, and a forked child
**cannot re-initialise CUDA** if the parent has touched it — which NetSolP does. Every worker
died with `RuntimeError: Cannot re-initialize CUDA in forked subprocess`: **239 of 239**. The
original code had kept the stages in separate processes and *that boundary was load-bearing with
nothing recording why*. Fix: `mp_context=multiprocessing.get_context("spawn")`. **A refactor that
removes a process boundary must state what was crossing it.**

*The exit code.* The stage returned **exit 0** after 239/239 failures, because nothing wrote
`return 1 if n_err else 0`.

*The resume predicate, which is worst.* Resume asked "does this design have a row in the
output?" — and **an error row is a row**. A re-run would have skipped all 239 designs forever,
leaving a file that looks complete: permanent silent data loss, avoided by reading the log. Fix:
`done_keys(..., require="dockq")` — key resume on the artefact you need, never on a record
existing.

The rest of the day built what the next three sessions reason about. The continuous ranking
**surrogate** was written — the banded composite with the step replaced by interpolation,
reliability **0.689** against `final`'s 0.602 — and here `select/surrogate.py:46` hardcoded the
band anchors `2.5, 7.0, 9.5`, which on day 9 turns out to have changed the winner. The G3
aromatic filter **PASSED** its [[05-experiment-design#6. Equal-budget resampling, and varying the outcome|equal-budget]] null at **+0.0241, p<0.0001**. The winner was named
`mpnn_T0.5_s104_036`, with a **winner's-curse discount**: raw 7-seed mean 95.117, shortlist mean
94.703, reliability 0.629 ⇒ predicted **94.963**; a fresh uncontaminated seed measured
**94.962**. Batching was measured at **1.16×** (84 s → 72 s) against a projected 1.8×. And
*"three seeds is the worst fold allocation"* was promoted verbatim into `LEARNINGS.md` — false at
a 40-fold budget, where 20×3 = **+1.4024** beats 4×10 = +1.3847 and 2×15 = +1.2992, with the
refuting row printed *directly above the sentence that made the claim*.

---

## Day 7 — 2026-09-20. The pivot: 404 folds, four pre-registered experiments, three withdrawn conclusions. 507 folds.

The busiest day by compute and the most important by content: this is when the project asks
whether its measurements measure anything.

**Re-deriving the sizing.** Averaging *k* replicates shrinks the error of a **mean** as `1/√k`,
which had made "depth beats breadth" right for ranking. The target had changed to a **spread**,
whose relative error obeys `SE(s)/s ≈ 1/√(2(k−1))` — **50% at k=3, 35% at k=5, 29% at k=7**.
Measured on 20 designs × 7 seeds *before* spending new folds, the reliability of a *k*-seed
CDR-H3 spread ran **0.591 / 0.813 / 0.938** at k = 2/3/5: going 2 → 5 costs 4× the folds for at
most 1.26× of effect, while the same folds take *n* from 60 to 239 and halve the Fisher-z
standard error. **Breadth won — the opposite of the previous week's answer.** The run became +1
seed on all 239 (measured k=2 reliability 0.686). Also: dropping a single 1.77 Å outlier moved
that k=2 figure 0.591 → **0.265**.

**Three published conclusions were withdrawn**, all the same error — a small-*n* null read as
evidence of absence:

- *"Mean loop pLDDT is blind to conformational heterogeneity"* — **ρ −0.168, p=0.69, n=8**, and
  the spine of the planned pitch. At n=239: **−0.432, p=2.9e−12**. An n=8 correlation carries a
  95% interval roughly ±0.7 wide.
- *"The ensemble carries no information the sequence didn't"* — partial **−0.081, p=0.62, n=40**,
  on which **a selection axis had been deleted**. At n=239: **−0.289, p=5.7e−06**.
- *"Three seeds is the worst allocation at every budget tested"* — false at budget 40.

A fourth went the same day: a claimed code-path split in `ipsae.py` (0.8491 from our JSON versus
0.8560 from the npz) was a single seed compared against an **8-seed mean**; both routes agree to
five decimals. The session records it as *"the fourth overstatement of the day, and the fourth
toward a more interesting finding"* — the sharpest observation in the project. **Noise is
symmetric; four errors in one day all pointing the same way is a property of the process.**

**The first validity experiments, at 11:53 and 11:54.** The **epitope knockout** destroys PD-1's
binding face while keeping the antigen, with a **matched off-interface alanine control**
(`ctrl6`), a fresh MSA per mutant so the alignment cannot leak native residues back, and a
dose–response over 0 → 349 → 527 deleted antigen contacts. In units of each metric's own seed sd:

| metric | epitope effect | matched control | verdict |
|---|---|---|---|
| ipSAE | **17.1×** | 0.046 | sees the epitope |
| interface pLDDT | **64.0×** | 0.807 | sees the epitope |
| PRODIGY ΔG | **0.9×** | 0.133 | **blind** |
| contacts | 1.2× | 2.000 | **blind** |

**ΔG carries the largest single share of the ranking variance and cannot see a 527-contact
epitope deletion.** The composition-matched CDR-H3 scramble null — holding length, composition,
aromatic count and charge constant by construction — found designs beat their own scrambles 28/30
(p=2.4e−06), but **15 of 30 scrambles land inside the pool's DockQ range and 0 of 30 above its
median**, so only the upper half of the pool is design-dependent.

**And the metric ICCs, at zero fold cost.** `contacts` [[04-measurement-theory#2. The intraclass correlation, and metrics that turn out to be constants|ICC]] **0.003**; `cdr_sasa` ICC **0.000** —
pure seed noise. **Five of eight rubric metrics are constants across the pool**; the harness ranks
on three (`dg`, `ipsae`, `dockq`), one of which is the blind one. This is arithmetic over folds
already on disk; run after the day-5 baseline it would have redesigned the campaign.

**The other pre-registered experiments.** *Specificity*: the named design is **[[01-the-biological-problem#6.4 TIM-3 cross-reactivity — a specificity failure|TIM-3]]-reactive** —
ipSAE **0.568** against pembrolizumab's 0.323 and a real TIM-3 binder's 0.682 on the same antigen
— tripping its **own pre-declared per-seed failure condition** on 2 of 3 seeds. The arm *mean*
would have passed; the rule was written per-seed before the data existed and was applied as
written, so the design ships with a cross-reactivity caveat it would not have carried under a
post-hoc analysis choice. *Ablation*: removing 158 antigen contacts costs **0.030 DockQ and gains
four contacts** — Boltz re-docks and rebuilds an interface, so the scored metrics cannot tell a
designed interface from an invented one. *Novelty probe*: two arms matched at 53.8% identity and
differing by **227 antigen contacts** returned a null at **+0.032 DockQ**, withdrawing an
extrapolation to DockQ 0.80.

**The handbook-versus-code audit** found four convention divergences: NetSolP had been fed **Fab**
chains where the handbook specifies **Fv**, twice — inverting *which chain limits* `min(VH, VL)`
(Fab: heavy 0.623 limits; Fv: light 0.569 limits) and turning "0/239 in Good" into **168/239 with
VH in Good**; DockQ's interface aggregation was an unrecorded convention worth a full band (winner
**0.755** under `min` vs **0.850** under `global`); four band edges were treated as inclusive where
the handbook is strict; and the required `design_X_pae.json` did not exist at all.

**Conformance.** The handbook was read directly for the first time and `config/metrics.yaml`
treated as a hypothesis about it. Transcription is sound — all 8 band triples, all 8 minimums,
weights, formula, ipSAE selection rule and chain convention match, and **24 of 24 boundary checks
pass at their exact edge values**. What remains is genuine ambiguity, now named: **band→score is
undefined and worth 12 points** — the same design scores **84.0 / 90.0 / 96.0** under bottom /
midpoint / top of band. `top` was chosen because §7.3 states the range as 0–100 and only `top`
attains it; the YAML records against its own interest that this is the most flattering reading.

**Blackwell, and a feasibility gate done right.** Challenge 2 needs RFantibody ([[03-the-toolchain#2.2 RFdiffusion via RFantibody|RFdiffusion]] +
ProteinMPNN + RoseTTAFold2), which pins `torch==2.3.*` built against CUDA 11.8; the local GPU is
an RTX 5070 Ti Laptop at compute capability **`sm_120`**, needing CUDA ≥ 12.8. The probe ran
*before* the ~10 GB install and tested with arithmetic: a 512² fp32 matmul against numpy (cuBLAS)
and a plain elementwise **ReLU** (PyTorch's own kernels). Both failed with `CUDA error: no kernel
image is available for execution on the device` while `torch.cuda.is_available()` returned
**True**, and `get_arch_list()` printed **`PTX entries: NONE`** — a CUDA binary carries [[03-the-toolchain#6.2 SASS versus PTX — the mechanism you need|SASS]]
(machine code for one architecture) and/or PTX (a virtual ISA the driver can JIT to a newer chip),
and with no PTX there is no forward-compatibility fallback. DGL's wheels stop at cu124 (cu126 and
cu128 both HTTP 403), and `dgl-2.4.0+cu124` **pins `torch==2.4.0` exactly**, silently replacing
the requested build with the generic cu121 PyPI one — closing the "install the library, then force
a newer torch" workaround. Docker does not help: a container isolates userspace, not the
instruction set. **Gate 0 FAIL in 25 minutes**, inside its 30-minute box, 9.8 GB reclaimed.

The day's fifth self-correction sits inside that result, and is the first in the *conservative*
direction: the author asserted *"no PTX JIT path exists from CUDA 11 to sm_120"* as the mechanism.
**False in general** — PTX forward-compatibility is exactly that mechanism; the conclusion held
because these wheels ship no PTX. *A claim about a mechanism and a claim about an outcome are
different claims, and only one was cheap to test.*

**Two costs.** `pgrep -f` self-matched for the third time — a wait loop gated on a process pattern
matched a shell whose own argv contained the pattern — idling the GPU **2 h 39 min**. And CPU
contention cost **2.3×** on fold rate: the first fold took 307 s against 84 s, not from heat (GPU
100%, 765 MHz, 49 °C) but because NetSolP ran at 395–1568% CPU (`intra_op_num_threads =
os.cpu_count()`) beside a browser at 44% CPU and 6.4 GB RSS of 15 GB. Closing the browser returned
folds to 86–97 s.

---

## Day 8 — 2026-09-21. Renting the right chip, and three judges. 0 local folds.

**The CPU port, and why it should not have been built.** Having established at minute 25 of day 7
that the GPU cannot run the stack, the project spent the first half of day 8 building a CPU-only
route: seven scripts (`62_`–`68_`) and three environment walls worked around — DGL's torch-ABI
constraint (PyPI's `dgl` 2.1.0 ships `libgraphbolt` for torch 2.0.0–2.2.1 only, forcing torch
2.2.1+cpu), `torchdata==0.7.1` (DGL 2.x imports `torchdata.datapipes`, removed in 0.11.0), and an
**NVTX shim in `sitecustomize.py`**, because NVIDIA's vendored SE3Transformer does
`from torch.cuda.nvtx import range` unconditionally at `basis.py:32` and that raises on a CPU-only
build. Measured: **19.5 min/backbone** diffusion, **7.1 min/design** RF2, **~48 min/backbone** end
to end, projecting 20 backbones at **16 hours** — a projection itself 1.75× wrong on RF2, which
had been *derived* at ~4 min/sequence rather than measured.

**Renting deleted all of it.** An `sm_86` RTX 3090 at **$2.82 for 5.5 hours** runs upstream's own
pins **untouched** at **2.5–2.7 min/backbone**. The full pilot — 18 hotspot-conditioned plus **18
unconditioned control** backbones, 30 ProteinMPNN sequences, 30 RF2 predictions — finished in one
sitting with zero failures. *Before porting a pinned stack, price an hour of the hardware it was
pinned for.* The decision rule should have fired at the Gate 0 failure, not after the port.

**What the pilot found.** Hotspot conditioning appeared to work — `frac_iface_on_epitope`
**0.712** conditioned against **0.501** unconditioned, d = 1.47, p = 0.0016 — but this was
**[[05-experiment-design#7. Optional stopping|optional stopping]]**: an interim look at n = 10 v 5 (d = 0.96, ambiguous) extended to n = 18 v
18 and tested at nominal α with no pre-registered rule, so the p is not the true type-I rate and
d is upward-biased, CI **[0.733, 2.216]**. And the null arm is the wrong one: the decoy-patch
control, hotspots on the opposite face of PD-1, **was never run and is still open**.
`interaction_pae` **cannot rank docks** (ICC 0.000, F = 0.70 against a detectable floor of 0.32),
and RF2's own prediction sits **24.9 Å** from the designed pose.

**The germline novelty metric** was built and validated. Challenge 2 has no reference antibody,
so novelty is measured against human germline — except there *is* no germline CDR-H3, because the
loop **is** the V(D)J junction and the N regions are non-templated. The database came from
ANARCI's `germlines.py` (249 V alleles, 14 J) plus riot-na's D genes translated in all three
forward frames (76 peptides). Consequence: **the <95% novelty gate is free** — roughly 5 of 13
positions are germline-templated. A claim that the metric *cannot* separate pembrolizumab from a
permutation of its own residues was **inverted and withdrawn**: scrambles (n=2000) average
**21.5%, sd 6.1%**, and pembrolizumab at **53.8%** is the **maximum of 2000 draws**, ≈ +5.3 sd,
p ≈ 1/2000.

**Three independent adversarial judges** then found four things: (1) `select/surrogate.py:46`
**hardcodes midpoint anchors while `config/metrics.yaml` has declared `top` since 2026-09-20**,
and the shipped winner was selected on the diverged scale; (2) **DockQ at its defaults REFUSES
this submission** — `ERROR: For chains ['A'] no identical corresponding chain was found`, exit 1,
no output, with the required flags documented nowhere in the package, a disqualification risk;
(3) the G3 aromatic filter **selects against Tyr and Trp**, which dominate real antibody
paratopes; (4) the winner's CDR-H3 carries **net charge +2** against pembrolizumab's **0** — a
leading polyreactivity predictor, and the unconnected sequence-level explanation for the project's
own TIM-3 result.

**And the pod was stopped without retrieving the data.** 36 backbones, 30 sequences, 30 RF2
predictions — **443 MB** — left on a stopped volume, so d = 1.47, ICC 0.000 and the 24.9 Å existed
only as prose for a day; nothing could be re-analysed or checked. Two adjacent losses: **~2.5
hours of idle pod billing ≈ $1.25** because the session waited to be prompted instead of polling
— **42% of the entire cloud spend, more than the pilot's own compute** — and `pgrep -f`
self-matching for the fifth time, **1 h 22 min** of idle GPU, exit code 144.

---

## Day 9 — 2026-09-22. Tests, git, and the day the project refuted itself. 195 folds.

**Version control and tests arrive at 00:20.** `f28870d`, 249 files.
`tests/test_invariants.py` is written the same night under an explicit rule: *"an invariant whose
violation is INVISIBLE. A crash does not need a test. A number that quietly becomes wrong does."*
It grows 17 → 20 → 29 → 30 tests, and is **mutation-tested**: five bugs reintroduced, five
*localised* failures (5/1/1/1/2 tests red), suite green after each restore. *A green suite is a
claim about the code; a suite shown to go red on reintroduced defects is evidence about the
suite.*

**The winner changes.** Making the surrogate read its anchors from config was bigger than the
judge who found it knew. Moving anchors from midpoints to tops changes the interpolation **slope
ratio** from 4.5/2.5 = **1.8** to 3.0/2.0 = **1.5**, and non-uniform slopes **reorder**. Under the
declared convention the shipped design falls **1st → 4th**, **18 of 20 designs change rank**,
Spearman **0.755**. `config/metrics.yaml` had explicitly claimed the choice *"CANNOT change the
ordering"* — true of the banded `final`, false of the surrogate actually used to rank. Not
swapped, deliberately: the 1st–4th gap is **0.191** against a pooled seed sd of **0.226**.

**The recycling withdrawal, and the control that was blind.** Challenge 2's 30 designs had been
folded at `recycling_steps=3`, inherited from Challenge 1, and scored **0 of 30 viable**, best
ipSAE 0.372, **15 of 30 at exactly 0.000**. A pile-up at the floor is a convergence diagnosis, not
a result — and it was written up as a finding, with a long essay on metric design, before anyone
checked. At **recycling 10**, `bb_2_0_dldesign_1` moves **0.263 → 0.864 / 0.842 / 0.856** across
three seeds, above the positive control's 0.842 on a real crystallised pair. At recycling 3 the
ranking was actively misleading: **the design that clears ranked 2nd; the one ranked 1st still
fails.**

**The positive control built to catch exactly this passed and was blind to it**, because it ran
at recycling 3 too. It correctly exonerated the Fv-versus-Fab construct (Fab 0.776, Fv 0.842) and
printed a verdict — *"0/30 is a real property of the designs"* — that was **wrong within the
hour** and had already been published.

The correction was then narrowed. The pool distribution is **unchanged** by depth: r3 mean 0.0640,
median 0.0056, 15/30 zeros; r10 mean 0.0646, median 0.0050, **still 15/30 zeros**; r3↔r10 rank
correlation only **0.432**. One design moved. So the defensible statement is *"it changed when I
sampled harder"*, not *"it has converged"* — and at recycling 20 the same input gives ipSAE
**0.795 / 0.883 / 0.731**, composite **93.6 / 96.0 / 93.6**, non-monotone (0.263 → 0.864 →
0.795), with 96.0 reproducing in **one of three** r20 seeds. Across the same depths a real
crystallised complex moves **0.050** and the Challenge 1 design **0.036**, while this de novo
design swings **0.601**. *That variance is the real finding, and it is larger than the score.*

**The argmax discovery.** `diffusion_samples` defaults to **1**, and Boltz **orders its output
models by its own confidence** — so `model_0` at one sample is an **[[06-allocation-and-selection#5. Order statistics: when your prediction is silently a maximum|argmax by construction]]**.
Every pose-derived number reported for a week (ipSAE, DockQ, ΔG, contacts, interface pLDDT, CDR
SASA) was the top of a distribution never sampled. At five samples the Challenge 1 design moves
ipSAE 0.039 but **DockQ 0.109**, turning 96.0 into a **94.0–96.0** envelope; the de novo design
moves ipSAE 0.128 with 3 of 5 falling to Medium, **91.2–96.0**. Note which metric moved:
*confidence stability does not imply coordinate stability.* And it costs almost nothing to know —
**2 m 54 s for five samples against roughly 2 m for one**, because MSA, trunk and recycling are
shared and only the diffusion head reruns.

**The negative control — eight folds, on day 9 of 9.** One variable: identical PD-1, identical
cached MSA, only the antibody changes. **HyHEL-10, raised against hen egg lysozyme, cleared all
five §7.2 hard cutoffs on `model_0`** — ipSAE 0.609, ΔG −12.4, 77 contacts, interface pLDDT 85.0,
CDR SASA 1084 — because `model_0` is the maximum of five draws Boltz ranked by its own confidence;
its median is **0.219**. The general result: **four of five gates reject 0 of 6 negatives**,
because ΔG, contacts, interface pLDDT and CDR SASA measure *that a complex was built*, not that it
is the right one. §7.2 rests on ipSAE alone, and even there cetuximab's median (0.594) sits
**0.006** under the cutoff.

The pre-registered Rule 3 fired and was not retracted: **nivolumab**, a licensed anti-PD-1
antibody used as the positive arm, scored ipSAE **0.017**, making the experiment **INCONCLUSIVE**
as designed. The diagnosis cost **zero GPU time**: nivolumab's 14-residue epitope is only **57.1%
present** in the folded 113-residue construct (`L25 D26 S27 P28 D29 R30` missing) while
pembrolizumab's 26 residues are 100% inside it. *The only reference antibody ever folded was the
one incapable of detecting the truncation.* Damage is bounded and in the project's favour: the
PD-L1 footprint, the face the designs target, is **23/23** inside the folded construct.

**The developability work, and the best science in the project.** `metrics/liabilities.py` —
promised at `BUILD.md:62`, never written — was finally written and immediately reproduced the two
N-[[01-the-biological-problem#6.1 Two N-glycosylation sequons in the Challenge 2 paratope|glycosylation sequons]] a reviewer had found in the Challenge 2 paratope (`N-V-S` at heavy 52,
`N-A-S` at light 49, both introduced by ProteinMPNN) **and** caught an `NG` [[01-the-biological-problem#6.2 The NG deamidation motif in Challenge 1's CDR-H2|deamidation]] motif in
Challenge 1 nobody had flagged. *A planned check that does not exist is indistinguishable from a
check that passed.*

Handbook §9 lists `N→Q` and `S→A` as interchangeable sequon fixes. **They are not**, and the
contact table predicted it before any folding: antigen heavy-atom contacts are **N52 → 10, N49 →
19, both serines → ZERO** — the glycosylation acceptor *is* the binding residue. Over five
diffusion samples each, **`S→A` stayed viable 5/5 (ipSAE 0.619–0.781) while `N→Q` collapsed ipSAE
0.864 → 0.014**, reproducible to ±0.001: a sixtyfold difference between two substitutions listed
on the same line. Confirmed in the *opposite* direction the same day — Challenge 1's `NG` motif
has acceptor **N55 making only 3 antigen contacts**, and there `N55Q` was **free**: composite
holds 96.0, ipSAE 0.822 → 0.821, envelope 0.044 against a 0.039 baseline. **The contact count on
the mutated residue predicts both outcomes.** The `S→A` design was submitted at **91.2 instead of
the unfixed 96.0** — 4.8 points paid deliberately to remove glycans from a paratope the rubric
does not score, recorded as unexplained rather than rationalised.

**The project refuted its own top recommendation, for free.** *"Redesign the light-chain CDRs"*
had stood in three documents and been echoed by two independent reviewers for about five days. It
fails twice. (i) NetSolP aggregates as **`min(VH, VL)`**, and the design's **VH is 0.699 against a
Good edge of 0.70**, so `max over all VL of min(0.699, VL) = 0.699` — the band cannot move, **by
0.001**. Two lines of arithmetic, available since the day-7 Fv correction. (ii) Empirically, 24
ProteinMPNN light chains at T=0.1 moved VL from **0.5690 to at best 0.5920 (+0.023) against a
required +0.131**; **0 of 24** reached the edge and **24 of 24 introduced new CDR liabilities** —
expected, since ProteinMPNN optimises sequence recovery given a backbone and solubility is not in
its loss. Cost: **zero GPU folds**.

**And the G3 aromatic filter was refuted as a design rule.** Re-running its own equal-budget
resampling test with each of six scored metrics as the outcome (n=239, 10,000 resamples), it wins
on **2 of 6**: `dockq` (+0.0237, p=0.0001) and `iface_plddt` (+1.12, p=0.0001) — **both properties
of the predictor**, DockQ here being pose retention against the parent crystal and interface pLDDT
being Boltz's own confidence. Everything about the interface itself is null or against it: `dg`
p=0.064, `ipsae` p=0.241, `cdr_sasa` p=0.547, and **`contacts` runs the wrong way** — filtered
designs make **1.80 fewer** heavy-atom contacts, one-sided p for "more contacts" **0.988**,
exactly what the chemistry predicts when you select against large aromatics. The statistics were
never the problem. **When a result survives a good null but contradicts a strong prior, vary the
*outcome*, not the test.** The filter would also have discarded the project's own winner, aromatic
count 2 against a threshold of ≤1.

Finally the pod volume was retrieved (256 files, 427 MB; later 258 after the first pull skipped
two), d = 1.4747 reproduced from data, and the optional-stopping test was replaced by a
deterministic per-backbone **contiguous-surface-patch null**: for each backbone, recompute
`frac_iface_on_epitope` against 2000 random contiguous 26-residue surface patches on the same
chain. **Real epitope 0.712, contiguous patch 0.154, 17 of 18 backbones at p<0.05.** Drawing 26
residues uniformly scores 0.231 — just 26/113 of the chain, the denominator rather than a result.

---

## The inheritance ledger

**A parameter that crossed a task boundary is an untested hypothesis, not a default.**

| inherited thing | entered | examined | consequence when examined |
|---|---|---|---|
| `recycling_steps=3` | day 3, `fold/boltz.py:80`, for Challenge 1 | **day 9** | published `0/30` → `1/30`; ipSAE 0.263 → 0.864 |
| `diffusion_samples=1` | day 3, Boltz's own default | **day 9** | every pose number was an argmax; Ch1 94.0–96.0, Ch2 91.2–96.0; an anti-lysozyme antibody sweeps all five gates |
| antigen-only MSA | day 3, correct for redesigning a known antibody | **never** | `STATE.md:350` lists it as step 2 of the shortest path forward; still open |
| Fv vs Fab | day 4 — G1c concluded "Fab-only" (0.607 vs 0.965); Ch2 folded as Fv anyway | day 9, positive control | exonerated (Fab 0.776 / Fv 0.842) — but the control ran at recycling 3 and was blind to the real problem |
| NetSolP on Fab | day 3, unrecorded | **day 7** | inverts which chain limits `min(VH,VL)`; 0/239 Good → 168/239 VH-in-Good |
| 113-residue PD-1 construct | day 2, from 5GGS chain Z | **day 9** | 43% of nivolumab's epitope absent; **the construct folded is not the construct shipped** (113-mer vs 123-mer) |
| DockQ `interface_agg` | day 4, a signature default `"min"` restating a convention | **day 9** | one full band: 0.755 (min) vs 0.850 (global) |
| surrogate anchors `2.5/7.0/9.5` | day 6, hardcoded at `select/surrogate.py:46` | **day 9**, by an external judge | **changed the identity of the winner**: 1st → 4th, 18/20 ranks change |

Six of the eight are one abstract error: **a value chosen once, for one purpose, in one place,
that travelled into a context where it was wrong — and nothing could notice, because the value
lived in prose, in a signature default, or in a tool's defaults rather than in an assertion.**
Every one was free to check; none was, until something downstream broke. The full taxonomy is
[[08-what-broke|the failure catalogue and its frequency analysis]].

---

## What to take away

**The compute went where the theory was, not where the uncertainty was.** 818 folds — 65% of
everything — refined the precision of a 239-design ranking under a rubric later shown to have 5 of
8 metrics constant, to rank on three, and to have its largest ranking contributor blind to the
interface. The entire de novo challenge got **75 Boltz folds and 5.5 rented GPU-hours**. The
negative control that undermined the whole gate set cost **eight folds** and, in its own file's
words, *"nobody ran it for a week."*

**Almost everything that took nine days was learnable in two.** The project's own record proves
it: the negative control cost 8 folds, the metric ICCs 0, the light-chain refutation 0, the
aggregator ceiling two lines of arithmetic, the nivolumab diagnosis no GPU time, the
diffusion-sample envelope 54 extra seconds.

**Ordering is a design decision.** The correct order is harness → baseline → ICC and dynamic range
on the baseline pool → *then* size the campaign. This project did 1, 2, 4, 3.

**The written record is what made self-correction possible at all.** Every one of the nine
substantive withdrawals was found by re-reading the project's own record against fresh data, not
by a tool: the −0.081 → −0.289 reversal because the partial correlation *and its n* were written
down; the allocation refutation because the refuting row sat directly above the claim. None of
that is recoverable from code. The failure mode is not writing too much — it is using prose as the
**storage medium** for facts that belong in a checked, single-source store, which is what day 9's
test file started to fix, eight days late.

Continue with [[08-what-broke|the failure catalogue, organised by generating mechanism]], then
[[09-critique|the adversarial reading of what the nine days established]].
