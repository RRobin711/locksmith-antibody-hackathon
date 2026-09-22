# Locksmith Bio × IBAB — De Novo Antibody Design Hackathon

Computational design of anti-PD-1 antibodies for the Locksmith Bio / IBAB EC
"De Novo Antibody Design Hackathon". The organisers' brief, in their words:

> *"Can we computationally design antibodies that don't just bind, but that look like
> real drugs?"*

Two challenges — **remix Keytruda** (redesign pembrolizumab's heavy-chain CDRs while
preserving the binding pose) and **invent the future** (design a complete VH/VL antibody
against PD-1 from scratch) — plus a 3-minute pitch. 250 points total.

**Start here:** [[PROJECT-STORY|the project story — the whole arc, written for someone new to structural biology]], or [[knowledge/README|the knowledge notes index]] for the teaching
material. For the working documents: [[PLAN|the delivery plan and its own review]], then [[docs/sessions/2026-09-14-antibody-hackathon-spec-and-scoring|the full specification — scoring formula, all eight hard cutoffs, metric definitions, and submission-format invariants]], extracted from the handbook so nobody has to re-read the
PDF.

## Layout

| Path | Contents |
|---|---|
| `PLAN.md` | Live delivery plan — phases, gates, risks, and a review of its own weaknesses (§14). |
| `BUILD.md` | Code skeleton — layout, types, config schema, build order. |
| `source/` | The organisers' handbook (PDF + plain-text extraction). Read-only ground truth. |
| `PROJECT-STORY.md` | The narrative spine — goal, strategy, what broke, where we are. |
| `knowledge/` | 13 teaching notes on the science, method and lessons — [[knowledge/README\|index]]. |
| `docs/sessions/` | One self-contained doc per working session; [[docs/sessions/README\|index here]]. |
| `designs/` | Candidate designs — structures, PAE files, sequences. Empty. |
| `scripts/` | Local re-implementation of the scoring pipeline. Empty. |

## Status — 2026-09-22

> ### The 2026-09-21 audit findings are closed — see [[results/audit_response_2026-09-22|the full response]]
>
> 1. **DockQ's required flags now ship inside the package** (`docs/reproducing_our_numbers.md`),
>    verified by running them: defaults exit 1 with no output, `--allowed_mismatches 40
>    --mapping ABC:ABC` reproduces **0.816**. The disqualification risk is closed.
> 2. **The selection surrogate now reads `config/metrics.yaml`** instead of hardcoding
>    midpoint anchors — and the consequence was larger than the audit found:
>    **under the declared convention the winner changes**, `mpnn_T0.5_s104_036` → 4th,
>    `mpnn_T0.2_s102_032` → 1st, with 18/20 designs changing rank (Spearman 0.755).
>    We did **not** swap the design: the 1st–4th gap is 0.191 surrogate points against a
>    0.226 seed sd, so the change is inside the noise and swapping would mean acting on a
>    ranking we have measured as unable to rank.
> 3. **`LOCKSMITH_DEV` is a deliberate placeholder**, not an unfixed §4.1 failure — this
>    project is not submitting (see [[PLAN|§15]]), so there is no team name. Recorded at
>    `scripts/57_build_submission.py:23`, which is the single place to change it.
> 4. **The project has tests and version control for the first time.**
>    `tests/test_invariants.py` (17 passing) makes findings 1 and 2 impossible rather than
>    merely documented; the repo is under git.
>
> ❌ **The G3 aromatic filter is REFUTED as a design rule** (2026-09-22, resolved — no
> longer merely flagged). Re-running G3's own equal-budget test with every scored metric as
> the outcome: it beats its null on **2 of 6**, `dockq` and `iface_plddt`, and **both are
> properties of the predictor rather than the interface**. Every interface quantity is null
> or against it — and **`contacts` runs the wrong way**, filtered designs making 1.80 fewer
> heavy-atom contacts, exactly as the chemistry predicts for selecting against Tyr/Trp.
> The filter selects for designs Boltz places confidently; neither surviving quantity exists
> for a de novo target. See [[results/g3_outcome_variable|the outcome-variable test]].
> The **germline inversion** on pitch slide 4 is corrected: pembrolizumab at 53.8% is the
> **maximum** of 2000 scrambles (~+5.3 sd, p ≈ 1/2000), so the metric discriminates
> decisively; the surviving true claim is only that the <95% gate is free.
>
> An independent judge re-derived all eight metrics from the packaged files alone and every
> reported value reproduced. The problems are in conventions and prose, not in the data.

**Challenge 2 — SUPERSEDED, see the 2026-09-22 status above. A design was subsequently packaged and validated.** *(kept as the record of where the project stood on 2026-09-21)*  RFantibody ran end to end on a rented
RTX 3090 (2026-09-21, $2.82): 18 conditioned + 18 unconditioned backbones, 30 sequences, 30 RF2
predictions, zero failures. **Hotspot conditioning works** — 71.2% vs 50.1% of interface on the
PD-L1 footprint, d=1.47, p=0.0016 — though that test was **optional stopping** (interim look at
n=10v5, extended to 18v18) with CI [0.73, 2.22], and the decoy-patch control that could have
failed was never run. **`interaction_pae` cannot rank docks** (ICC 0.000 against a 0.32
detectable floor) and **RF2 sits 24.9 Å from the designed poses**. **None of the seven
Challenge 2 metrics has a value, and every artefact is on a stopped pod volume that was never
retrieved.** See [[results/challenge2_pilot|the pilot]] and
[[results/challenge2_remaining_work|what remains]].

## Status — 2026-09-20

**M0–M3 closed. Challenge 1 is packaged and validated *as an artifact*. Its scientific
claims are deliberately narrow — see "What the metrics can and cannot support" below.**

**The deliverable:** `submission/LOCKSMITH_DEV.zip`, built to the handbook's §4.1 tree and
checked by `scripts/58_validate_submission.py`, which reads **only the packaged files** —
no `runs/`, no cached scores — and re-derives all eight metrics. It passes: **viable,
`final` 96.0**.

The design is `mpnn_T0.5_s104_036` — CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to
pembrolizumab, folded on the handbook's §4.2.2 constructs. See
[[results/m3_winner|the winner report]] and [[results/handbook_conformance|the conformance
audit]].

> **96.0 is convention-dependent and that is the handbook's doing, not ours.** §5.2 gives
> band *ranges* ("Good (9-10)") and never says how to pick a value inside one. The same
> design scores **84.0 / 90.0 / 96.0** under bottom / midpoint / top. `top` is the default
> because §7.3 states the range as 0–100 and only `top` attains it. The choice is a uniform
> monotone relabelling, so it moves the number and **cannot reorder two designs**. Earlier
> reports of `final` **87.5** were computed under midpoint + a `min()` DockQ aggregation
> that appears nowhere in the handbook; they are superseded, not wrong-at-the-time.

**What the metrics can and cannot support.** This is the project's main result and it
constrains every number above:

- **Epitope knockout** (delete PD-1's binding face, matched off-interface control): ipSAE
  and interface pLDDT respond at **17×** and **64×** their own seed sd. **PRODIGY ΔG and
  the contact count do not** — and ΔG carries the largest single share of the ranking
  variance.
- **SKEMPI** (45 point mutants with measured ΔΔG): **no metric tracks affinity**, bound at
  ρ ≈ 0.41 for n=45. `NL31A` abolishes binding (ΔΔG +21.8 kcal/mol) and scores ipSAE
  **0.917** against the wild type's 0.903.
- **Composition-matched scramble**: designs beat their own CDR-H3 permutations 28/30
  (p=2.4e-06), but **15/30 scrambles land inside the pool's DockQ range and 0/30 exceed its
  median** — so only the upper half of the distribution is design-dependent.
- **Metric validity**: `contacts` ICC **0.003** and `cdr_sasa` ICC **0.000** are pure
  sampler noise; five of eight metrics are constants across the pool. The eight-metric
  harness ranks on three.

> **The supported claim: this pipeline distinguishes a destroyed interface from an intact
> one, and cannot rank two intact ones by affinity. Ranking within the viable pool is not
> supported by our own metrics and is not claimed.**

**Specificity caveat that travels with the design:** predicted cross-reactivity with TIM-3,
a same-fold human checkpoint receptor — ipSAE **0.513** (n=8) against pembrolizumab's
**0.331** and a real TIM-3 binder's **0.682** (p=0.038, bootstrap CI [+0.045, +0.320]).

**Challenge 2 — SUPERSEDED (2026-09-20 status). Not attempted at that date; subsequently run and packaged.**
RFantibody is the right method (§3.2 asks for de novo) but pins CUDA 11.8 while this GPU is
`sm_120`. Measured, not assumed: both cuBLAS and a plain ReLU fail with `no kernel image`,
the wheels ship **no PTX**, DGL tops out at cu124, and DGL's exact `torch==2.4.0` pin closes
the bring-your-own-torch workaround. See
[[results/rfantibody_risk_scope|the risk scope]] and
[[results/challenge2_colab_plan|the off-machine plan]]. The **germline CDR-H3 novelty
metric does not exist** and blocks any Challenge 2 score regardless of route.

**What works.** The eight-metric harness reproduces ground truth. Boltz-2 recovers the
pembrolizumab–PD-1 pose untemplated at DockQ 0.820. ProteinMPNN generates designs over the 29
IMGT heavy-CDR positions, folded as Fab at **~84 s each on a quiet machine** (measured over 239
folds; the same fold costs 133–150 s on a contended one, which is a machine-load difference and
not a budgeting error). Ranking uses a continuous surrogate
(`src/locksmith/select/surrogate.py`) that preserves the rubric's pricing but not its banding.

**Four results that shaped everything after them:**

- **The Fv screen is dead.** Fv ipSAE seed reliability 0.607 vs Fab 0.965 — the unclamped VH/VL
  elbow shows up as measurement noise, and recovering the precision by averaging seeds costs more
  than folding the Fab. **Fab-only.** (G1c failed.)
- **ipSAE is a liveness test, not a ranking metric.** Its correlation with structural correctness
  was carried by dead control designs; among live ones Fab R² collapses 0.755 → 0.263. Report it,
  gate on it at 0.60, never rank on it.
- **Boltz does not place novel antibodies reliably.** Post-cutoff test on 5 complexes released
  clear of the verified 2023-06-01 training cutoff: median Fab DockQ **0.291** against 0.818 on
  the memorised 5GGS. Challenge 2 is high-risk. (G1f marginal.)
- **The gates do not discriminate.** Plain ProteinMPNN at defaults clears **all eight gates on
  20/20 designs** — the binding geometry is guaranteed by redesigning onto the native backbone.
  Pembrolizumab itself scores 76.0 and is **non-viable** (100% CDR-H3 identity fails novelty).

**Newest results (2026-09-19).**

- **G3 PASS.** The CDR-H3 aromatic filter beats an equal-size random subset on mean DockQ by
  **+0.0241** (1.34× the one-seed-sd bar), p<0.0001, n=239. But ρ decays monotonically with
  MPNN temperature (−0.535 → −0.326), so the filter is a property of the *generator's operating
  point*; and it does not move the maximum (p=0.189). The named winner has aromatic count 2, so
  the filter at its own threshold would have discarded it. [[results/m3_g3_verdict|Verdict]].
- **Folds belong on seeds rather than candidates — once the budget is large enough.** Shortlist
  depth plateaus at k≈20; at 120 folds 60×3 → +1.388 against 20×7 → +1.466.
  ⚠ **An earlier version of this line said "three seeds is the worst allocation at every budget
  tested"; that is refuted by the table it was drawn from** — at budget 40, 20×3 (+1.4024) beats
  4×10 (+1.3847) and 2×15 (+1.2992). Corrected 2026-09-20 in `results/m3_shortlist_depth.md` and
  LEARNINGS, but the refuted wording survived here until 2026-09-22.
  [[results/m3_shortlist_depth|Sizing]].
- **The winner's-curse discount was applied, but NOT validated** (corrected 2026-09-20) — shrinkage predicted 94.963,
  the uncontaminated fresh seed measured 94.962, against a raw mean 0.155 too high.
- **Fold batching: correct but 1.16×, not the projected 1.8×** (84 s → 72 s/fold). Accepted;
  it changes no scheduling decision. [[results/m3_batching|Acceptance test]].

**Open.** The top two designs are separated by **0.1 standard errors**, so the ordering is
unresolved — more seeds on the top 2–3 would settle it (~20 folds). M4/M5 (validation dossier)
not started; they now have a design to be about. The CDR-H3 **length** axis is unexplored and
needs RFdiffusion/RFantibody installed and qualified — ProteinMPNN is fixed-backbone. G3's
194-fold saving is **simulated, not demonstrated**: all 239 were folded, by design, to keep the
filter's evaluation non-circular. `submit/` empty.

See [[docs/sessions/README|the session index]] for the full arc.

Not submitting — see [[PLAN|§15]]. No deadline.

## The organising idea

Six of the eight scored metrics are computed from the two files we submit — the
organisers do not re-fold our designs. So the structure predictor is a scored component,
and the evaluation is gameable by anyone willing to submit a flattering structure. We are
not doing that. Every design ships with an orthogonal-evidence dossier (independent
predictors, specificity controls, hotspot ablation, epitope-overlap check) showing the
numbers correspond to something real. **Build the judge before the contestant:** the
first gate is our harness scoring pembrolizumab itself correctly.

## Contacts (from the handbook)

- [organiser email removed]
- [organiser email removed]
- [organiser email removed]
- WhatsApp channel: *Bio-hackathon (IBAB EC × Locksmith Bio)*
