# Response to the 2026-09-21 audits — what was fixed, what was corrected, what was refuted

**2026-09-22.** Three independent judges audited this project on 2026-09-21. This file
records what happened to each finding. Everything here was **executed**, not recalled;
where a number is quoted it was recomputed tonight from files on this machine.

The one structural point worth keeping: every correction this project had ever made
lived in prose, and **prose cannot fail a build**. Tonight that changed —
`tests/test_invariants.py` exists, the repo is under git, and two of the findings below
are now impossible rather than merely documented.

---

## Part A — the artefact

### A1. DockQ refused to score the submission at its defaults ✅ FIXED

**Verified, not recalled.** Run against the packaged files:

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb      →  exit 1, no output
  ERROR:root:For chains ['A'] no identical corresponding chain was found …
$ DockQ … --allowed_mismatches 40 --mapping ABC:ABC       →  exit 0
  Total DockQ over 3 native interfaces: 0.816
```

0.816 reproduces `metrics/scores.md` exactly. The invocation now ships **inside** the
package as `docs/reproducing_our_numbers.md`, and the short form is at the top of
`metrics/scores.md` where a grader will hit it first. The doc also names the trap that
chain **C of the deposited 5GGS is a second heavy chain**, not the antigen.

It records one thing the previous docs did not: `global` averages in the **heavy–light
framework interface at 0.931**, which no design touches. The interface our design is
actually responsible for is **A–C = 0.723**.

### A2. The pod volume ✅ RETRIEVED

The volume survived. Retrieved over the Jupyter HTTP API (a single GET per file — the
one transfer route that did not silently drop bytes on 2026-09-21): **256 files,
427 MB**, into `runs/challenge2_pod/`. Every directory matches the server-side listing
count exactly (`bb` 36, `rf2` 30, `seq` 31, `unconditioned` 36, `logs` 20, `c2` root 5).

The GPU this pod held was gone by the time we restarted it, so it was restarted
**CPU-only** at $0.25/hr — a file copy needs no GPU, and that also avoided RunPod's
data-migration path.

**Integrity — stated precisely, because it is not the check that was asked for.**
The plan said "verify by checksum". The Jupyter contents API returns a **server-side
sha256**, which is exactly the right instrument, and the first ~130 files were verified
against it. Then Jupyter **502'd mid-walk** and did not recover (the pod stayed up; the
service died). So the evidence we actually have for the remaining files is:

| check | status |
|---|---|
| per-file server-side sha256 | **partial** — ~130 of 256 before the service died |
| per-file server-reported byte size vs bytes written | ✅ all files (curl fails on a short read against `Content-Length`) |
| directory file counts vs server-side listing | ✅ exact, every directory |
| all 168 PDBs parse, chains present, coordinates numeric | ✅ 168/168 |
| all 4 JSONL parse on every line | ✅ |
| published headline recomputes from the data | ✅ d = 1.4747 vs published 1.47 |

That is strong evidence and it is **not** a completed checksum pass. `scripts/`-adjacent
`verify.py` is written and will finish the sha256 comparison whenever the service
returns; until it does, this row stays amber. The distinction matters in a project whose
argument is that it checks things: HTTP with `Content-Length` is a fundamentally
different transport from the keystroke simulation that dropped four characters on
2026-09-21, so the risk here was always low — but "low risk" is not "verified".

**Root cause of the 502, found on stopping the pod.** RunPod's Details panel reports
**"Out of Memory (OOM) Detected"**, and the pod's own spec reads **vCPU 0, Memory 0 GB**.
The "Start Pod using CPUs" fallback — taken because the original RTX 3090 was no longer
available — provisioned a pod with **no CPU or RAM allocation**, so the Jupyter server
was OOM-killed partway through serving a recursive directory walk. It was never going to
recover, and the restart that put it into "Initializing" could not have succeeded.

*Transferable:* a provider's "start without a GPU" fallback is not the same machine minus
the GPU. Check the allocated vCPU/RAM before assuming a degraded pod can serve even a
file copy, and treat a service that dies under a directory walk as an infrastructure
symptom rather than a transient.


**The headline claim now reproduces from the retrieved data**: conditioned
`frac_iface_on_epitope` **0.7119** (sd 0.1130) against unconditioned **0.5005**
(sd 0.1684), Cohen's **d = 1.4747**, 95% CI **[0.733, 2.216]**. Those matched the
published 0.712 / 0.501 / 1.47 / [0.73, 2.22]. They are no longer unfalsifiable.

### A3. Tests and version control ✅ DONE

`tests/test_invariants.py`, **17 tests passing**, the first in the project's life. The
rule used for what belongs there: *an invariant whose violation is invisible*. A crash
does not need a test; a number that quietly becomes wrong does.

The repo is now under git (first commit `f28870d`, 249 files).

Two real bugs were caught by the tests and fixed:

- **`select/surrogate.py` hardcoded the midpoint anchors** (2.5/7.0/9.5) while
  `config/metrics.yaml` had said `band_value: top` since 2026-09-20. Now read from
  config. **See §B0 — this one is worse than the audit thought.**
- **`dockq.compute` defaulted to `interface_agg="min"`** while config declared
  `global`. Defaults are now resolved from config at call time; a signature default
  that restates a convention is a second source of truth and the second one rots.

A third problem surfaced while writing the tests and is **documented rather than
fixed**, because the alternative is worse: four metrics have **strict** Good edges
(`contacts > 25`, `iface_plddt > 80`, `cdr_sasa > 600`, `cdrh3_identity < 70`). A value
sitting exactly on such an edge is Medium in the reported score and Good in the
surrogate. No continuous function agrees with a step function *at* the step. This is
**not** measure-zero: `contacts` is an integer count, so "exactly 25" is ordinary.
Pinned by `test_surrogate_diverges_only_at_strict_edges_and_only_upward`.

Also fixed: `scripts/58_validate_submission.py` used to **litter the package it was
validating** — `ipsae.py` writes scratch `.txt`/`.pml` next to the PDB it is handed, so
three stray files appeared in `structures/`. Validation now runs on an isolated copy,
and the packager refuses any file in `structures/` that §4.2.1 does not list.

### A4. Previously-reported fixes ✅ CONFIRMED ON DISK

Both were genuinely applied, not merely reported:

- `README.md:148` and `PLAN.md:878` carry the correction to the "three seeds is the
  worst allocation at every budget tested" claim.
- `config/metrics.yaml:43` carries the note that the comment used to say `min` while
  the live value was already `global`.

---

## Part B — the claims

### B0. NEW, and the largest finding of the night: the surrogate bug changed the winner

The audit said the submitted winner "was selected on" the diverged surrogate. That
understates it. Recomputed over the 20-design shortlist with the seeds actually used:

| | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| **midpoint anchors** (what selection ran on) | `mpnn_T0.5_s104_036` | `…_053` | `…_057` | `…_047` |
| **top anchors** (what config declared) | `mpnn_T0.2_s102_032` | `mpnn_T0.5_s104_011` | `mpnn_T0.3_s103_032` | **`mpnn_T0.5_s104_036`** |

**The shipped design falls from 1st to 4th. 18 of 20 designs change rank; Spearman
between the two rankings is 0.755, not 1.0.**

`config/metrics.yaml` states that the band-value choice "is a monotone relabelling, so
it moves the headline number and CANNOT change the ordering of two designs." **That is
true of the banded `final` and false of the surrogate** — the anchors set the *slopes*
of the two interpolation segments, and the ratio changes from 4.5/2.5 = 1.8 (midpoint)
to 3.0/2.0 = 1.5 (top). Non-uniform slopes reorder.

**We are not swapping the submitted design, and the reason is the point.** The 1st–4th
gap is **0.191** surrogate points against a pooled within-design seed sd of **0.226**
and a 7-seed standard error of **0.086**. The whole top six spans 0.205 — less than one
seed. Single-seed reliability on this shortlist is **0.28**. Swapping now would mean
acting on a ranking this project has already measured as unable to rank. The correct
reading is that **the winner changing is itself further evidence for the claim we
already make**: within the viable pool, our metrics do not discriminate.

*(Cross-check that this computation is sound: it reproduces the project's recorded
7-seed within-design sd of 0.467 under the midpoint convention, to three decimals.)*

### B1. The conditioning result — optional stopping ⚠️ CONCEDED, and replaced with a better test

Conceded in full. The pilot looked at n=10 v 5 (d=0.96, ambiguous), extended to
n=18 v 18, and tested at nominal α with no pre-registered stopping rule. **The reported
p = 0.0016 is not the true type-I rate and d = 1.47 is upward-biased** by exactly the
winner's-curse logic this project applies elsewhere. The CI is [0.733, 2.216].

The audit also proposed a free re-analysis, and it was run — `scripts/70_epitope_patch_null.py`,
on files already on disk, no new folds:

> For each conditioned backbone, recompute `frac_iface_on_epitope` against 2000 random
> **contiguous surface patches** of the same size (26 residues) drawn from the same
> chain, and ask where the real epitope falls.

**Result: real epitope mean 0.712 against a contiguous-patch null at 0.154.
17 of 18 backbones beat their own null at p < 0.05.**

This is a better instrument than the one we published, for three reasons: it is
deterministic per backbone (no stopping rule to violate), it asks whether conditioning
hit **the right face** rather than whether it did anything, and it is a control that
could have failed. A 26-residue set drawn *uniformly* scores 0.231 — because 26/113 of
the chain is captured by construction — which is why the uniform draw is a strawman and
the contiguous patch is the test.

**Still not run, still conceded:** hotspots swapped to a decoy patch on the opposite
face. That remains the strongest available control and it costs a GPU run.

### B2. "ICC 0.000 → `interaction_pae` CANNOT rank, DELETED" ⚠️ TOO STRONG, softened

Recomputed from the retrieved RF2 outputs (n=10 backbones × 3 designs):

| metric | ICC | mean | sd |
|---|---|---|---|
| `interaction_pae` | **−0.113** | 15.60 | 2.15 |
| `pae` | −0.120 | 8.28 | 0.99 |
| `target_aligned_antibody_rmsd` | +0.196 | 24.87 | 10.76 |
| `pred_lddt` | **+0.836** | 0.908 | 0.012 |

`F_crit(0.05, 9, 20) = 2.393`, so **the smallest ICC this design can detect is 0.317.**

The honest claim is therefore *"no between-dock signal larger than ICC ≈ 0.32 is
detectable at n=10, k=3"* — **not** "cannot select" and **not** "DELETED". Those are
permanent conclusions resting on a bound this experiment cannot support, and this
project has already published four underpowered nulls as findings. The word to use is
*undetected*, not *absent*.

Two further caveats the audit raised and we accept: `MS_within` mixes three genuinely
different molecules, so the ICC may be answering "does the backbone predict the score"
rather than "can this rank designs"; and **18 unconditioned backbones were never
sequenced** — that is the experiment separating range restriction from a dead metric.
**Is it cheap?** The backbones already exist on disk; it needs ProteinMPNN + RF2 on 18
inputs, which the pilot measured at ~7.1 min/sequence for RF2, so roughly **2–4 GPU-hours
(~$1–2)**. Cheap in money, not free in session time.

### B3. "RF2 sits 24.9 Å away" — proposed re-reading ❌ TESTED AND NOT SUPPORTED

The audit proposed a more parsimonious reading: the 24.9 Å reflects *unfiltered designs
failing a standard filter*, not RF2 being unreliable. It is a good hypothesis and the
retrieved data lets us test it. It does not hold.

- `interaction_pae` min is **9.31**; the conventional RFantibody filter is `< 10`, so
  **exactly 1 of 30 passes** — which is indeed what an unfiltered pilot should look like,
  and that part of the audit's reasoning is right.
- **But that one passing design sits at 32.86 Å** — worse than the pool median of 28.94 Å.

So filtering does not rescue agreement; it selects a design further from the designed
pose than average. There *is* a weak rank association across the pool
(Spearman `interaction_pae` vs `target_aligned_antibody_rmsd` = **+0.415, p = 0.023**,
n = 30), so the metric is not noise — but the specific claim "filter first and RF2
agrees" is refuted by the only design that passes the filter. **Do not put the
re-reading on a slide.** Three of 30 designs are within 10 Å; the median is 28.94 Å.

### B4. `pred_lddt` was unfairly grouped ✅ CONFIRMED, and more strongly than stated

`pred_lddt` was grouped with "constant and useless" metrics alongside contacts at
ICC 0.003. Measured, it has **ICC = +0.836 — the highest of the four RF2 metrics**, and
the only one clearing the 0.317 detectable floor. Its *sd* is small (0.012) because the
complex is ~85% fixed framework, but **low variance is not uninformativeness**: it is
highly reproducible within a backbone and does distinguish between them.

Removed from that grouping in the docs and the pitch outline. The confusion was
treating dynamic range as if it were signal — the same error, inverted, that
`results/metric_validity.md` warns about.

### B5. The CDR-H3 aromatic filter ⚠️ FLAGGED, removed from anything that says "validated"

The G3 verdict is marked PASS, and the filter keeps CDR-H3s with **≤ 1 aromatic** —
selecting *against* Tyr/Trp, whose enrichment in paratopes is among the most robust
compositional facts in antibody biology.

It passed a genuinely rigorous test: it beat 10,000 equal-budget random subsets at
p < 0.0001. **The problem is the outcome variable, not the statistics.** The outcome was
**DockQ to the parent crystal** — pose retention — so the filter demonstrably predicts
*how stably Boltz reproduces the parent pose*, which is a property of the predictor and
the generator's operating point, not of binding. `results/metric_validity.md` already
says the outcome variable is pose retention; nobody connected that to the direction of
the filter.

Concretely, in this design: CDR-H3 aromatic count is **2** (F, Y) against
pembrolizumab's **4** (Y, F, F, Y). Note also that the filter at its pre-registered
threshold of ≤1 **would have discarded our own winner**.

**Until this is re-examined against an outcome that is not pose-retention, it appears
nowhere as validated.** Flagged in PLAN §15.6 G3, README, and the pitch outline.

### B6. Novelty is overstated at the whole-chain level ✅ CONFIRMED, now in the submission

Measured against pembrolizumab over the 232-residue heavy construct:
**15 substitutions, 93.5% identity**; CDR-H1 6 changes, **CDR-H2 exactly 1**, CDR-H3 8;
**15 of 29 designable positions changed**; light chain untouched.

`cdrh3_identity` is 38.5% and scores Good — correctly, that is the metric §6.3.1 asks
for. But a human reading §3.1's "significant sequence novelty" sees a nearly identical
antibody with one rewritten loop. Now stated plainly in
`docs/methods_and_limitations.md` under *"How novel is this, really"* rather than left
for the metric to imply.

### B7. The NetSolP claim ✅ CORRECTED

Measured on the shipped design: **VH = 0.699, VL = 0.569**, `min` = 0.569.

The docs said "70% of our designs already clear the Good band on VH" next to this
design's score. True of the pool (168/239) — and **this design is not one of them**. Its
VH is 0.699 against a 0.70 edge, i.e. **0.001 short**, and below pembrolizumab's own
0.733. The juxtaposition implied the opposite. Corrected in the package and the deck.

### B8. CDR net charge ✅ ADDED

CDR-H3 `ALRPRDVDRGFYK` carries **net +2** (4 basic: R,R,R,K; 2 acidic: D,D) where
pembrolizumab's `ARRDYRFDMGFDY` carries **0** (3 basic, 3 acidic). High CDR positive
charge is one of the better-established sequence predictors of polyreactivity, and this
project independently measured and reported TIM-3 cross-reactivity without connecting
the two.

Added to the submission docs. **Stated as an observation, not a mechanism** — it is one
predicted cross-reactivity and one sequence feature, which is a hypothesis, not a
demonstration. What is fair to say is that it was computable from the sequence for free,
before any structure existed, and nothing in the rubric would ever have surfaced it.

---

## Still open

1. **The decoy-patch control** (hotspots on the opposite face). The one control that
   could falsify conditioning. Needs a GPU run.
2. **Sequencing the 18 unconditioned backbones** — separates range restriction from a
   dead `interaction_pae`. ~2–4 GPU-hours.
3. **Re-examining G3 against an outcome that is not pose-retention.**
4. **Whether any Challenge 2 design clears the seven gates** — still no metric computed
   for any of them, and that is unchanged by tonight.
5. **The reliability figure 0.629** quoted for the 20-design shortlist does not
   reproduce from the recorded inputs under any standard estimator we tried (the
   plug-in variance ratio on these data gives 0.28). Flagged rather than corrected,
   because the original script would settle it and guessing would add a fifth number.
