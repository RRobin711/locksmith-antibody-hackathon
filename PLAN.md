# Delivery plan — Locksmith Bio × IBAB antibody design hackathon

**Written:** 2026-09-14 · **Revised:** 2026-09-15 after review

> ### ⚠ Read §15 first
> **We are not submitting to this hackathon.** Ajitesh shared it; we are doing it for the
> learning and to produce something genuinely good for a potential collaborator. The value is
> the quality of the science, not a rank.
>
> **§3–§11 below describe the submission-oriented plan and are superseded by [§15](#15-revised-plan-milestones-not-calendar).**
> They are kept because the reasoning trail is worth more than a tidy document — several
> decisions in §15 only make sense against what they replaced. §12 (open questions), §13
> (performance), and §14 (plan review) all still stand.

---

## 1. The one thing that determines everything else

Read the evaluation section carefully and a structural fact falls out:

> **Six of the eight scored metrics are computed from the two files we hand over.**
> `design_X_complex.pdb` and `design_X_pae.json` are the sole inputs to ipSAE, DockQ,
> ΔG, contacts, interface pLDDT and CDR SASA. **The organisers do not re-fold our
> designs.** Only NetSolP and CDR-H3 identity are derived from sequence.

So 60% of the score is a function of a coordinate file we generate ourselves, with a
confidence matrix we also generate ourselves. Two consequences, and they point in
opposite directions:

1. **Practically:** the structure predictor is not infrastructure, it is a *scored
   component*. Choosing it, and choosing how to run it, is a first-class design decision
   that deserves the same rigour as the sequence design.
2. **Ethically, and this is the part that matters for an audition:** the evaluation is
   trivially gameable by anyone willing to submit a flattering structure. Confidence
   metrics measure self-consistency, not truth — a confidently wrong pose scores well.
   Any team can hill-climb ipSAE. **The differentiator is not hitting the numbers; it is
   demonstrating that our numbers correspond to something real.**

That turns into a concrete commitment: every submitted design carries an
**orthogonal-evidence dossier** (§6) — independent predictors agreeing on the pose,
specificity controls, hotspot ablation, and an epitope-overlap check against the actual
PD-L1 footprint. We will report where our design is *weak*, too. That dossier is the
deliverable I would most want a computational-biology company to see.

### 1.1 The second structural fact: gates dominate scores

Eight hard cutoffs, all must pass, and **one submission per challenge**. Failing any one
ranks us below every viable design. Combined with the fact that our local metric
estimates will not exactly reproduce the organisers' run, the objective is not
"maximise expected score" but:

> **maximise score subject to every gate clearing by a margin larger than our own
> reproduction error.**

This changes the selection rule (§5.4) and it is why Phase 0 measures that error before
we design anything.

### 1.2 Where the points actually are

Binding is 60% but averaged over six metrics; Novelty and Developability are 20% each on
a *single* metric. Per sub-score point, in Challenge 1:

| Moving one metric's sub-score by +1 | Final-score value |
|---|---|
| Any one binding metric (÷6 in the mean) | `0.60 × (1/6) × 10` = **1.0 pt** |
| NetSolP | `0.20 × 1 × 10` = **2.0 pt** |
| CDR-H3 novelty | `0.20 × 1 × 10` = **2.0 pt** |

Novelty and solubility are worth **2× any single binding metric** (2.4× in Challenge 2,
where the binding mean is over five). Both are *sequence-only* — computable in
milliseconds, before any structure exists. That dictates the funnel order in §5.2: filter
on the cheap high-value axes first, spend GPU only on survivors.

And within the binding mean, the score is dragged by its **worst** member. Optimise the
minimum, not the average.

---

## 2. Machine reality — measured, not assumed

Surveyed 2026-09-14:

| Resource | Value | Verdict |
|---|---|---|
| GPU | RTX 5070 Ti Laptop, **12.2 GB VRAM**, driver 595.84, **compute cap 12.0 (sm_120, Blackwell)** | Workable; needs CUDA ≥ 12.8 / torch ≥ 2.7-cu128 |
| CPU | 24 cores | Fine |
| **RAM** | 16 GB fitted / **15 GiB usable, ~9.3 GB held by desktop apps** | ⚠ Tight, but **recoverable** — see §2.3 |
| Disk | 776 GB free | Fine for weights; **not** enough for ColabFold's ~2.2 TB local MSA DBs |
| Package mgr | `uv` 0.10.9, Python 3.12.3, no conda | Fine; a few tools assume conda |
| Docker | present | Important — the escape hatch for RFantibody/RFdiffusion |
| Network | RCSB ✓, GitHub ✓, ColabFold MSA API ✓ (live, rejects GET as expected) | Fine |

**Availability confirmed on PyPI:** `DockQ` 2.1.3, `prodigy-prot` 2.4.0, `freesasa` 2.2.1,
`anarci` 2026.2.13.2, `boltz` 2.2.1, `chai_lab` 0.6.1, `ImmuneBuilder` 1.2, `igfold` 1.0.1,
`biotite`, `biopython`. **Repos reachable:** ipSAE (DunbrackLab), RFantibody, RFdiffusion,
ProteinMPNN, LigandMPNN, LocalColabFold, ANARCII, NetSolP-1.0 (DTU + GitHub mirror).

### 2.1 Complex size and runtime budget

Fab submission (their example FASTA is Fab-length with a His-tag): H ~220 + L ~214 +
PD-1 ECD ~120 ≈ **554 residues**. Fv-only: ≈ **350 residues**. Both fit comfortably in
12 GB. Estimated AF2-Multimer wall-clock on this GPU: **~5–12 min per complex** at Fab
size, roughly half that at Fv size. So an overnight batch buys **~100–200 complexes**.
That number sets the width of the funnel, and it is the first thing Phase 1 measures for
real rather than estimating.

### 2.3 The RAM situation, diagnosed

Not a mystery and not a hardware bottleneck — the machine has **16 GB fitted (15 GiB usable** after
firmware/iGPU reservation), and the shortfall is simply what is running:

| Process group | RSS |
|---|---|
| Brave | 5.2 GB |
| Zoom (+ webview host) | 2.2 GB |
| Claude | 1.4 GB |
| Slack | 1.4 GB |
| Discord | 1.3 GB |
| GNOME Shell / Xorg / nautilus | 1.5 GB |

That is **~9.3 GB of chat apps and browser**, leaving 6 GB available. Closing Zoom, Slack, Discord
and most Brave tabs during batch runs recovers **~8 GB** — which takes us from "marginal" to
"comfortable" for a 350–550 residue complex prediction.

Swap already exists: an **8 GB swapfile at `/swap.img`, currently ~0 used**. My earlier note about
"adding a 32 GB swapfile" was wrong on the premise; the correction is to **grow the existing one**
to ~24–32 GB (disk is not scarce at 776 GB free) and set `vm.swappiness=10`. Swap here is not for
performance — it is **insurance against the OOM killer terminating a six-hour overnight batch**.
Thrashing into swap is slow; being killed at 04:00 costs the whole night.

Operating rule for Phase 2/3 batch nights: **close the chat apps, run from a TTY, grow swap.** The
GPU's 12 GB VRAM, not system RAM, then becomes the binding constraint.

### 2.2 Environment rule for this machine

Per existing vault practice: **the venv lives outside the vault** —
`export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/locksmith"` before any `uv` command.
`pyproject.toml` / `uv.lock` stay in the project (portable, worth syncing); thousands of
platform-specific binary files do not. Torch pinned to the cu128 index explicitly; verify
with `torch.cuda.get_arch_list()` containing `sm_120` **plus a real matmul**, not just
`is_available()`.

---

## 3. Phase 0 — Scoring harness and ground-truth calibration (Day 1, Tue)

**Build the judge before building the contestant.** We cannot choose between designs
without reproducing the scoring pipeline locally, and we cannot trust our reproduction
until it has been run on structures whose answers we already know.

### 3.1 Work

1. `uv` project; torch cu128; verify sm_120 with a real matmul.
2. Install the four pipeline tools — **ipSAE** (vendored script), **DockQ**,
   **PRODIGY** (`prodigy-prot`), **NetSolP** — plus `ANARCI`/`ANARCII` for IMGT
   numbering and `freesasa` for SASA.
3. Fetch reference structures: **5GGS** (Keytruda Fab + PD-1, primary), **5DK3**
   (Keytruda Fab alone), **5IUS** (PD-1/PD-L1 — defines the epitope we must block),
   **5WT9** (nivolumab + PD-1, an independent real solution).
4. Write `scripts/score_design.py` → emits all 8 raw metrics, their 0–10 band scores,
   category scores, final 0–100 score, and a **per-gate margin table**. One JSON per
   design. This file is the project's spine.
5. Write `scripts/validate_submission.py` → checks every format invariant from the
   handbook (folder names, prefix matching, the three exact FASTA headers, chain
   A/B/C assignment, one design per challenge).

### 3.2 The calibration experiment

Run the harness on four things and tabulate:

| Subject | What it tells us |
|---|---|
| **5GGS crystal** (native Keytruda–PD-1) | What a *real, clinically validated* complex scores. Our ceiling reference. |
| **5WT9 crystal** (nivolumab–PD-1) | A second real answer — is the harness consistent across genuine binders? |
| **5GGS re-predicted from sequence** | **The most informative number in the project.** The gap between crystal-scored and predicted-scored *is* our predictor's optimism bias. |
| **A deliberate decoy** (antibody docked to the wrong face of PD-1) | Does the harness actually discriminate? If a decoy passes the gates, the gates are not measuring what we think. |

### 3.3 Ambiguities this phase resolves empirically

Four things the handbook leaves undefined, each of which changes the designs:

- **CDR SASA: bound or unbound?** Bands say >600 Å² good, >250 required. Computing both
  on 5GGS tells us which convention lands in a sane band. This matters because the two
  readings *conflict in sign* with the contacts metric — a well-buried interface lowers
  bound-state CDR SASA.
- **Fab or Fv?** Their example FASTA is Fab-length with `…HHHHHH`, but NetSolP is
  documented as running on Fv. Score 5GGS both ways.
- **ipSAE chain-pair handling** — the spec says rows with `Type = max`, best over
  antibody-vs-antigen pairs. Confirm against the vendored script's actual output.
- **DockQ chain mapping** if we submit Fv against a Fab reference.

### 3.4 ✅ Gate 0 — verifiable, binary

- [ ] `torch.cuda.get_arch_list()` contains `sm_120` **and** a 4096² GPU matmul returns correct values
- [ ] `score_design.py` runs end-to-end on 5GGS and emits all 8 metrics
- [ ] **`DockQ(5GGS, 5GGS) == 1.000`** — a self-comparison that is not exactly 1.0 means the harness is wrong
- [ ] **CDR-H3 identity(5GGS heavy vs Keytruda) == 100%** — same logic, for the novelty path
- [ ] Native 5GGS is **viable** (clears all 8 gates). *If the real drug fails our harness, the harness is broken — not the drug.*
- [ ] Decoy complex is **non-viable**
- [ ] Calibration table committed to `docs/`

> **This gate is the project's foundation. We do not proceed to design work until the
> harness scores pembrolizumab correctly.**

---

## 4. Phase 1 — Folding stack (Day 1–2, Tue–Wed)

We need a predictor that emits AlphaFold-style PAE JSON. Two candidates, deliberately
kept in parallel because one carries a platform risk:

- **Track A — LocalColabFold (AF2-Multimer).** The canonical choice; the metric bands
  were plainly calibrated against it. **Risk: JAX on Blackwell `sm_120` is unproven
  here.** Test on day 1, not day 5.
- **Track B — Boltz-2** (and/or **Chai-1**). PyTorch-native, so cu128 works cleanly;
  AF3-class architecture; emits PAE. Lower platform risk, different numeric behaviour.

MSAs come from the **ColabFold public MMseqs2 API** — local databases are ~2.2 TB and we
have 776 GB, so local is off the table. Note that paired MSAs are meaningless for
antibody–antigen (no co-evolutionary signal between a drug and its target), so the
sensible protocol is **real MSA for PD-1, single-sequence or germline-shallow for the
antibody chains**. That is a tuning knob worth one experiment.

**The validation that decides the track:** re-predict the 5GGS complex *from sequence
alone* and DockQ it against the crystal. A predictor that cannot recover a known
antibody–antigen pose cannot be trusted on a design.

### 4.1 ✅ Gate 1

- [ ] At least one track runs on GPU end-to-end producing `.pdb` + PAE JSON
- [ ] **Re-predicted 5GGS scores DockQ ≥ 0.49 vs crystal** (CAPRI Medium or better)
- [ ] Re-predicted 5GGS is viable on all 8 gates
- [ ] **Measured** wall-clock per complex recorded → funnel width fixed by arithmetic, not guesswork
- [ ] Cross-predictor ipSAE/ΔG spread on the same structure measured → **this becomes σ, the margin unit in §5.4**

---

## 5. Phase 2 — Challenge 1, "Remix Keytruda" (Day 2–4, Wed–Fri)

### 5.1 The real difficulty

Novelty wants CDR-H3 rewritten (<70% identity for full marks); DockQ wants the binding
pose preserved (≥0.80 for full marks); and CDR-H3 supplies **30–50% of the paratope**.
These pull against each other by construction — that tension *is* Challenge 1.

Pembrolizumab's CDR-H3 appears to be ~11 residues (`RDYRFDMGFDY`, to be confirmed by
ANARCI in Phase 0). At 11 residues, <70% identity needs **≥4 substitutions**; <95% needs
just 1. So the novelty gate is trivial and the novelty *band* is very reachable — the
question is only whether the pose survives.

Run the arithmetic before choosing: trading 3 DockQ sub-score points for 4 novelty points
is worth `−3.0 + 8.0 = +5.0` final points. We will **tabulate this frontier explicitly**
rather than assuming, and pick from the measured Pareto front.

### 5.2 The funnel — cheap reject before expensive confirm

| Stage | Method | Cost | Survivors |
|---|---|---|---|
| **S0** Generate | ProteinMPNN / **LigandMPNN** (interface-aware, antigen as context) redesigning only IMGT CDR-H1/H2/H3, framework fixed; sample across temperature 0.1–0.5 to trace the novelty/quality frontier | minutes | ~10,000 |
| **S1** Sequence rules | CDR-H3 identity band; liability motifs (N-X-S/T sequon, NG/NS/NT/NH/ND deamidation, DG/DS/DT/DD/DH isomerisation, exposed Met/Trp/Cys); no new unpaired cysteines; predicted pI 6–9 | ms | ~2,000 |
| **S2** Solubility | NetSolP, keep **≥0.70** (the *good* band, not the 0.50 gate) | seconds/batch | ~500 |
| **S3** Cheap structure | ABodyBuilder2 / IgFold Fv model; CDR-H3 loop RMSD to parent as a pose-preservation proxy; clash check | ~1 s each | ~200 |
| **S4** Expensive fold | AF2-Multimer / Boltz-2 complex + PAE — **overnight batch** | 5–12 min each | ~100–200 |
| **S5** Full scoring | `score_design.py`; rank by risk-adjusted rule (§5.4) | instant | ~20 |
| **S6** Dossier | Orthogonal validation battery (§6) | hours | **1 submitted** |

Overnight runs use the established pattern:
`nohup setsid systemd-inhibit --what=sleep:idle:handle-lid-switch --why="…" <cmd> > job.log 2>&1 &`
and must be **resumable** — count completed designs on disk and skip them, so an
interrupt costs nothing. Also: **never edit a script a running batch shells out to.**

### 5.3 Data hygiene (learned the hard way, previously, on this machine)

- **Stamp provenance into every row at creation time** — MPNN seed, temperature, parent
  backbone, predictor, model index. Cannot be reconstructed after aggregation.
- **Validate against physics, not against the label.** A design claiming ΔG −14 with 8
  interface contacts is not a good design, it is a broken measurement. Assert
  cross-metric consistency (contacts vs buried surface vs ΔG) and quarantine rows that
  violate it.
- **Delete, don't keep, any design whose prediction job exited non-zero.** A half-written
  PDB that still parses is the worst kind of bad data.

### 5.4 Selection rule — risk-adjusted, not score-maximal

Using σ from Gate 1 (cross-predictor spread per metric):

1. **Require margin ≥ 2σ on every one of the 8 gates.** Non-negotiable; a design at
   ipSAE 0.61 is one prediction-noise event from scoring zero.
2. Among survivors, maximise the **minimum binding sub-score** (the mean is dragged by
   its worst member).
3. Break ties on novelty, which is the cheapest remaining point.

### 5.4a The winner's curse — re-score the winner on fresh seeds

Selection *is* optimisation. Screening ~10,000 candidates and submitting the argmax is a
hill-climb executed in one parallel step, and it does not require us to intend anything. If each
observed score is `true + noise`, the maximum over N samples is disproportionately a design whose
*noise* was favourable, and the inflation grows with N.

So the selection-time score of our chosen design is **biased upward by construction**.

**Mitigation, mandatory before locking either challenge:** re-predict the selected design with
**fresh seeds** and re-score it. That estimate is unbiased because the design was not chosen using
it. If the score drops materially, the gap *is* the curse, and the runner-up may be the better bet.
Record both numbers — the selection score and the clean re-score — in the margin table, and quote
the **clean** one in the pitch.

This is the self-interested reason for the §7 dossier, distinct from the integrity reason: a
different predictor has different blind spots, so cross-model agreement is evidence that survived
selection rather than evidence manufactured by it.

### 5.5 ✅ Gate 2

- [ ] ≥20 candidates clear all 8 cutoffs at ≥2σ margin
- [ ] Novelty/DockQ Pareto frontier plotted from real data
- [ ] One design locked, with a written margin table and a stated reason for choosing it
- [ ] Locked design reproduces on a **re-run from its own FASTA** (determinism check)
- [ ] **Fresh-seed re-score recorded** and within tolerance of the selection score (§5.4a)

---

## 6. Phase 3 — Challenge 2, "Invent the Future" (Day 3–5, Thu–Sat)

No DockQ safety net: ipSAE, ΔG and interface pLDDT carry everything. De novo binders
routinely fail exactly these confidence metrics, so this is where the project is most
likely to fail. **Two tracks, with a hard go/no-go on Thursday.**

- **Track A (upside) — RFantibody**, the Baker-lab antibody-specific RFdiffusion:
  target-conditioned CDR loop diffusion onto a framework → ProteinMPNN → RF2 filtering.
  Best scientific story by a distance. **Risk: high** — RFdiffusion's SE3-transformer/DGL
  stack is old and Blackwell is new. Docker is the mitigation, and it is installed. Must
  be *attempted on Day 2–3*, never later.
- **Track B (guaranteed) — germline framework + de novo CDR design.** Build an Fv on a
  preferred human germline framework (the handbook names IGHV3-23, IGKV1-39 among
  others), define the epitope from the **PD-L1 footprint on PD-1 in 5IUS**, place the Fv
  against that epitope using the 5GGS binding geometry as a *prior on plausible approach
  angle*, then design all six CDRs de novo with LigandMPNN in the antigen's presence.
  Torch-only, so it cannot fail for platform reasons.

Track B is legitimately de novo at the level that matters — every CDR sequence is
designed from scratch against the target — while using a germline framework, which is
what real therapeutic antibodies do anyway and which the handbook explicitly encourages
for developability. **We will say exactly this in the pitch rather than implying more
novelty than we delivered.** Novelty is scored against *germline* CDR-H3 here, which any
designed loop clears easily; the framework choice costs us nothing on the rubric and buys
a large developability advantage.

Note an unexploited loophole we are deliberately **not** taking: nothing in the rubric
rewards blocking PD-L1 specifically — ΔG and ipSAE do not know what a checkpoint is, so a
design binding the back of PD-1 scores identically. We target the PD-L1-competitive
epitope anyway, because a checkpoint inhibitor that doesn't inhibit the checkpoint is not
a drug, and §6.4 measures whether we succeeded.

### 6.1 ✅ Gate 3

- [ ] Track A/B go/no-go decision made and recorded by end of Day 3
- [ ] ≥5 candidates viable on all applicable gates at ≥2σ margin
- [ ] One design locked with margin table, **including fresh-seed re-score** (§5.4a)
- [ ] Epitope-overlap check (§6.4 below) passes — the design actually competes with PD-L1

---

## 7. Phase 4 — The orthogonal-evidence dossier (Day 5–6, Sat–Sun)

The anti-Goodhart work, and the part I think actually wins the audition. Each design gets
all six:

1. **Cross-predictor consensus.** Independently predict with AF2-Multimer, Boltz-2 and
   Chai-1. Report pairwise pose RMSD and the ipSAE spread. A design survives only if ≥2
   predictors agree on the binding mode. *Rationale: a confidently-wrong pose is usually
   confidently wrong in only one model's idiom.*
2. **Specificity / decoy controls.** Predict the designed antibody against unrelated
   antigens (e.g. lysozyme, and PD-L1 itself). ipSAE should **collapse**. A binder that
   "binds" everything has learnt the predictor, not the target.
3. **Self-consistency (scRMSD).** Refold the designed sequence alone and compare to the
   designed backbone; < 2 Å is the field's conventional bar. Tests whether the sequence
   actually encodes the structure we designed.
4. **Epitope-overlap quantification.** Fraction of PD-L1's contact residues on PD-1
   (extracted from 5IUS) that our antibody buries. This is the only check in the whole
   project that asks whether the molecule would *work as a checkpoint inhibitor*, which
   the rubric never asks.
5. **Hotspot ablation.** Mutate the 2–3 largest-contribution interface residues to Ala;
   ΔG should degrade substantially. If it doesn't, the interface is not real — it is
   distributed noise that PRODIGY happens to like.
6. **Full developability panel beyond the scored metric.** The handbook's six pillars:
   aggregation (TANGO/Aggrescan), immunogenicity (MHC-II epitope scan), chemical
   liability motifs, humanisation/T20 score, predicted pI and Tm. NetSolP is 20% of the
   score; the other five pillars are 0% of the score and ~100% of why real candidates
   die in CMC.

### 7.1 ✅ Gate 4

- [ ] All six validations run on both locked designs
- [ ] Results written up **including the failures** — where our designs are weak, stated plainly
- [ ] Any design failing consensus or specificity is **replaced**, not explained away

---

## 8. Phase 5 — Package and pitch (Day 6, Sun)

1. `build_submission.py` assembles the exact tree; `validate_submission.py` proves it.
2. **Re-run ipSAE and NetSolP on the final zipped files**, exactly as the handbook's
   final checklist instructs — not on the working copies. Format bugs are the one failure
   mode that is entirely preventable and entirely fatal.
3. 3-minute deck (handbook contradicts itself: §4.4 and §11.4 say 3 min, the §4.5
   checklist says 5 — **build for 3, keep 2 minutes of spare material**).

Deck spine, 3 minutes:
- The problem is not binding, it is the other 90% of attrition — and the rubric knows it
- Our pipeline in one diagram
- **We built the judge before the contestant** — the calibration table, with pembrolizumab
  scored by our own harness as the reference point
- The two designs, with margin tables
- **The dossier**: why we believe these are real and not predictor artefacts
- What we would do with another week (honest limitations)

### 8.1 ✅ Gate 5

- [ ] `validate_submission.py` passes on the final zip
- [ ] Metrics re-computed from the zipped files match the recorded values exactly
- [ ] Deck timed under 3:00 aloud

---

## 9. Risk register

| # | Risk | Severity | Mitigation | Decide by |
|---|---|---|---|---|
| 1 | **15 GiB RAM, ~9.3 GB held by Brave/Zoom/Slack/Discord.** | Medium (was High) | Close chat apps during batches (~8 GB recovered); **grow** the existing 8 GB `/swap.img` to 24–32 GB as OOM insurance; `vm.swappiness=10`; prefer Fv-size complexes. See §2.3 | Day 1 |
| 2 | **JAX on Blackwell sm_120** — ColabFold may not run | High | Track B (Boltz-2/Chai-1, torch cu128) developed in parallel from the start | Day 1 |
| 3 | **RFantibody/RFdiffusion on Blackwell** (old DGL/SE3 stack) | High | Docker container; hard go/no-go with Track B as guaranteed fallback | Day 3 |
| 4 | ColabFold MSA API rate-limits or goes down | Medium | Cache every MSA to disk on first fetch; single-sequence mode for antibody chains is defensible anyway | Day 2 |
| 5 | 12 GB VRAM insufficient for AF3-class at Fab size | Medium | Fv-size submission; reduced recycles/samples; chunked attention | Day 2 |
| 6 | NetSolP download/licensing friction | Medium | DTU service + GitHub mirror both confirmed reachable; ESM-based reimplementation as backstop | Day 1 |
| 7 | **Our metrics ≠ organisers' metrics** | **High** | The entire ≥2σ margin rule exists for this; quantified in Gate 1 | Day 2 |
| 8 | Timeline ambiguity (handbook says Dec 2025) | Low | Ajitesh confirming separately; we build to Sunday regardless | — |
| 9 | Overnight job dies silently, burning a night | Medium | Resumable batches; heartbeat logging; check at wake | Day 3 |

---

## 10. Vault knowledge notes — ✅ first three written

Requested: read the shared links and add tagged knowledge to the vault. **Constraint:**
`3- Tags/` is outside the write zone, and the vault has **no existing biology tags** (83
tags, nearest are `[[AI, ML]]`, `[[Learning]]`, `[[Resource]]`, `[[Idea]]`,
`[[Job Search]]`). Vault convention is `Tags:[[tag]]` wikilinks at the top of the note,
not YAML frontmatter.

Written into `knowledge/` (2026-09-14), tagged with existing hubs plus new ones
(`[[Protein Design]]`, `[[Nanopore]]`, `[[Locksmith Bio]]`, `[[IDP]]`,
`[[Structural Biology]]`) that render as unresolved until the hub notes exist in `3- Tags/` —
**your call, since I can't write there.**

| Note | Source | Why it matters here |
|---|---|---|
| ✅ **Intrinsically Disordered Proteins** | Uversky 2019 (full text), Kulkarni 2022 (abstract only — AIP 403), Chen & Kriwacki 2018 (full text) | Anfinsen's dogma and its limit; why ensemble-averaging is a category error for IDPs |
| ✅ **Nanopore Sensing of Disordered Proteins** | Shaji 2026 *Nat Nanotech* (full 24-page PDF), Peng 2025 *ACS Nano* (abstract only — ACS 403) | Single-molecule measurement; and Peng is itself a *de novo design* paper |
| ✅ **Locksmith Bio — Company Context** | Handbook + inference | What they likely do, the lock-and-key naming, how to pitch |
| ⬜ PD-1/PD-L1 structural basis | Tan 2017, Na 2017, PDB 5GGS/5IUS/5WT9 | The epitope definition for both challenges |
| ⬜ ProteinMPNN & RFdiffusion mechanics | Dauparas 2022, Watson 2023 | Our generative engines; sampling temperature controls the novelty frontier |
| ⬜ Antibody developability guidelines | Raybould 2019, Jain 2017 | The 40% of the score that is not binding |

### 10.1 The bridge worth building — and possibly the best idea in this plan

Locksmith's science is **intrinsically disordered proteins**: molecules with no single
native structure, described properly by a conformational *ensemble* rather than one set
of coordinates. The hackathon is about antibodies, which are well-folded — so at first
glance the background reading is unrelated context.

It isn't. **CDR-H3 is the most conformationally heterogeneous loop in the antibody
repertoire** — that is precisely why it is the specificity determinant and why it is hard
to design. Representing it with a single static PDB plus a scalar confidence is *exactly*
the modelling failure the IDP field exists to correct.

So: for our submitted designs, characterise CDR-H3 as an **ensemble** — sample multiple
predictions across seeds and predictors, report the conformational spread, and show
whether the interface is supported by a converged loop or by one lucky sample. It costs
little on top of the consensus work in §7.1, it is a *stronger* form of the confidence
argument than ipSAE, and it frames our result in the vocabulary of the company we are
pitching to.

That is the slide I would build the pitch around. Not "we hit the thresholds" — **"we
treated the hardest loop in the molecule the way your lab treats disorder, and here is
what that revealed."**

---

## 11. Timeline

| Day | Focus | Gate |
|---|---|---|
| **Tue 15** | Env, scoring harness, ground-truth calibration | **Gate 0** |
| **Wed 16** | Folding stack decision; refold-5GGS validation; RFantibody attempt | **Gate 1** |
| **Thu 17** | Ch1 generation + funnel S0–S3; overnight S4 batch; Ch2 track decision | — |
| **Fri 18** | Ch1 selection locked; Ch2 build; overnight Ch2 batch | **Gate 2** |
| **Sat 19** | Ch2 selection; full validation dossier | **Gate 3, 4** |
| **Sun 20** | Package, validate, deck, submit | **Gate 5** |

Challenge 1 is deliberately finished first — it is the one with a safety net. If
everything slips, we submit one excellent design rather than two rushed ones.

---

## 12. Open questions for you

1. **Team name** — needed for the folder/zip structure, and it is baked into every path.
2. **Ask Ajitesh three things?** (a) live deadline; (b) **Fab or Fv** for submission;
   (c) **CDR SASA bound or unbound**. These are legitimate clarifications, not hints —
   but if you'd rather not ask, Phase 0 resolves (b) and (c) empirically.
3. **Tag hubs** — do you want `[[Protein Design]]`, `[[Antibody]]`, `[[IDP]]`,
   `[[Locksmith Bio]]` created in `3- Tags/`? I can't write there; you'd add them.
4. **Is this solo, or is there a team?** Changes how much of the pipeline needs to be
   hand-offable versus just reproducible.

---

## 13. Performance and architecture — making the compute budget count

**~95% of this project's compute is one operation: complex structure prediction.** MPNN
generation, sequence filters, PRODIGY, DockQ, SASA and NetSolP together are a rounding error.
So: optimise folding for throughput, and optimise everything else for *re-runnability*.

### 13.1 The budget, in the only currency that matters

Realistically **~45 GPU-hours** (5 batch nights Tue–Sat × ~9 h), plus partial days. What that buys
depends entirely on configuration:

| Configuration | Est. per complex | Complexes in 45 h |
|---|---|---|
| Naïve: Fab (554 res), 5 models, 3 recycles, fresh MSA each run | ~12 min | **~225** |
| Tuned: Fv (350 res), 1 model, 3 recycles, cached antigen MSA, single-seq antibody | ~1.5–2 min | **~1,400–1,800** |

A **6–8× swing in candidates evaluated** for identical wall-clock, entirely from configuration.
These are estimates; Gate 1 measures them for real, and the funnel width in §5.2 should be set from
the measurement, not from this table.

### 13.2 Architecture decisions (do these first — they are free and they compound)

**1. Separate expensive artefacts from derived metrics. Highest-leverage decision in the project.**
Store the *structure*, the *PAE*, and the *MSA*. Never bake a metric convention into a stored
result. Four conventions are still unresolved (CDR SASA bound vs unbound, Fab vs Fv, ipSAE chain
pairing, DockQ chain mapping — §3.3). If a convention is baked in and turns out wrong, we re-fold
everything and lose a day. If metrics are *derived on demand* from stored artefacts, the same
discovery costs a 10-second re-run of `score_design.py` over the whole corpus. Disk is 776 GB and
free; GPU-hours are not.

**2. Content-hash memoisation.** Key every expensive call by `hash(sequence, predictor, params)`.
Skip anything already on disk. This makes the pipeline **resumable by construction** rather than by
bolted-on checkpointing, so a crashed or interrupted overnight batch costs only the in-flight job.

**3. Two-tier prediction, where tier B is also the science.**

| Tier | Config | Cost | Applied to |
|---|---|---|---|
| **A — screen** | 1 model, 1–3 recycles, Fv, cached antigen MSA, single-seq antibody | ~1–2 min | everything reaching S4 |
| **B — confirm** | 5 models × 3 seeds, 20 recycles w/ early stop, + Boltz-2 / Chai-1 | ~10–15 min | top ~5% only |

The elegant part: **tier B's multi-model, multi-seed output *is* the CDR-H3 conformational ensemble**
that §10.1 identifies as the pitch differentiator. The scientifically distinctive deliverable falls
out of the compute-efficient design at zero extra cost.

**4. Pipeline CPU behind GPU.** 24 cores sit idle while the GPU folds. Run scoring (PRODIGY,
DockQ, freesasa, ANARCI) as a consumer process on a queue so the GPU never blocks on CPU work.
Worth ~10% and it costs one `multiprocessing.Queue`.

### 13.3 The big folding levers

**MSA caching — the single largest free win.** In Challenge 1 the antigen is *always* PD-1 and the
framework is *always* pembrolizumab's. The PD-1 MSA is identical across every candidate. Fetch it
once, cache the `.a3m`, reuse forever. Re-fetching per prediction wastes minutes each and hammers
the ColabFold public API for no information gain.

**Single-sequence mode for the antibody chains — faster *and* more correct.** Paired MSAs encode
co-evolutionary signal between interacting partners. **A drug and its target do not co-evolve** —
there is no evolutionary record of pembrolizumab binding PD-1. So a paired antibody–antigen MSA
contributes noise, not signal. The right protocol is a real MSA for PD-1 and single-sequence (or
germline-shallow) for VH/VL. This is also exactly why IgFold and ABodyBuilder2 work from single
sequences. Speed here is a side effect of doing the correct thing.

**Fv instead of Fab.** 350 vs 554 residues, and Evoformer cost grows worse than linearly in
sequence length — roughly a **2.5×** saving. Blocked on the Fab/Fv question in §12.

**Templates for Challenge 1.** We *have* the answer structure (5GGS). Supplying it as a template
speeds convergence and permits fewer recycles. Entirely legitimate — Challenge 1 is explicitly a
redesign of that scaffold.

**Recycles and model count are the throttle.** Runtime is roughly linear in both. Screening at 1
model / few recycles and confirming at 5 models / 20 recycles is where the 6–8× comes from.

**bf16.** Blackwell has strong bfloat16 throughput; both JAX and Boltz support it. Measure accuracy
impact on the 5GGS refold before trusting it.

### 13.4 The genuinely *smart* part: stop filtering, start choosing

A static threshold funnel processes candidates in arbitrary order. With ~1,500 fold-slots against
~10,000 candidates, **the order we fold in matters more than the speed we fold at.**

**Surrogate-guided selection.** After the first ~150–200 tier-A folds we hold
`(cheap features) → (ipSAE, ΔG, interface pLDDT)` pairs. Fit a gradient-boosted ranker on them and
use it to prioritise the remaining candidates. Cheap features available *before* folding:

- **ProteinMPNN sequence log-likelihood** given the fixed backbone — free, emitted at generation
- **Fast-fold self-consistency**: ABodyBuilder2/IgFold the designed Fv (~1 s) and measure CDR-loop
  RMSD to the parent backbone. In the de novo design literature this is among the strongest cheap
  predictors of downstream AF success
- NetSolP, CDR-H3 identity, liability-motif counts, loop length, net charge, hydrophobic fraction

This converts the funnel from a filter into an **active-learning loop** — which is the honest
framing of the whole exercise as a multi-objective ML design problem, and is itself pitch material.

**Batch diversity.** Do not spend 200 fold-slots on 200 near-identical sequences. Cluster
candidates by CDR sequence identity and sample *across* clusters. Standard batch-Bayesian-
optimisation reasoning: maximise information per GPU-hour, not predicted score per candidate.

**Calibrate the filters, don't trust them.** A filter is only useful if it discards candidates that
would have scored badly. Track the **survival rate of the final objective through each stage** — if
hard-filtering NetSolP ≥ 0.70 at S2 is systematically removing the most novel CDR-H3s (charged and
hydrophobic loops score worse on solubility), the filter is eating the Pareto front. Measure this
explicitly; it is the failure mode that a funnel cannot detect from inside.

### 13.5 Free external compute

**AlphaFold Server (AF3)** is free with a daily job cap and is on the handbook's recommended list.
Correct use: spend the local 45 GPU-hours on *screening*, and the free AF3 allocation on the
**final handful of designs** where quality matters most — best available model, zero local compute,
and a genuinely independent third predictor for the consensus check in §7.1. Verify early that its
PAE output is ipSAE-compatible, and check its terms of use for a competition context.

### 13.6 An exploit we are explicitly declining

Challenge 1 is fixed-backbone redesign on 5GGS, so one could submit the **crystal coordinates**
with the new sequence attached and score DockQ ≈ 1.0 by construction. We are not doing that, for
two reasons: the PAE file would not correspond to the submitted coordinates (ipSAE reads both, so
the submission would be internally inconsistent), and those coordinates would not be a *prediction
of our molecule* — they are a measurement of someone else's. Recorded here so the temptation is
documented rather than rediscovered at 2 a.m. on Saturday.

### 13.7 What not to optimise

Micro-optimising CPU scoring, MPNN sampling throughput, or file I/O. They are <5% of the budget
combined; time spent there is time not spent on fold-ordering, which is where the real leverage is.

---

## 14. Plan review — what is wrong with the plan above

Written 2026-09-14 after a pass over §1–13 looking for errors rather than confirmation. Ordered
by how much damage each would do if left alone.

### C1. The margin rule was justified by the wrong mechanism — corrected

§1.1 and §5.4 argue for a "≥2σ margin on every gate" because "our local metric estimates will not
agree with the organisers' pipeline run". **That reasoning is wrong.** The organisers do not
re-fold our designs — they run *their* tools on *our* files. Given the same PDB and PAE, ipSAE,
DockQ, PRODIGY and SASA are **deterministic**. There is no prediction noise between our run and
theirs.

What actually varies is **implementation**: tool version, IMGT numbering scheme, SASA probe radius,
whether CDR SASA is bound or unbound, how chains are paired. That is a much smaller uncertainty —
and a different *kind*, because it is reducible by pinning versions rather than by adding margin.

**Corrected approach:**

1. **Vendor the exact ipSAE script** from the DunbrackLab repo at a pinned commit; pin
   `DockQ`, `prodigy-prot`, `freesasa`, `anarci` to exact versions and record them in the
   submission's `metrics/` folder. Eliminates most of the variance at the root.
2. **Margin sized for residual convention risk**, not prediction noise: clear every gate by
   **≥20% of the distance from the cutoff to the next band edge**. Cheap, achievable, and it
   protects against a convention surprise without demanding the Good band everywhere.
3. **The 2σ rule as written may have been unsatisfiable anyway.** Cross-predictor σ on ipSAE is
   plausibly 0.10–0.20; 2σ above the 0.60 gate demands 0.80–1.00, i.e. the Good band on every
   metric simultaneously. A constraint that nothing satisfies is not a constraint, it is a bug.
4. **Cross-predictor spread still matters enormously — but for truth, not margin.** It belongs in
   the §7 dossier as evidence the pose is real. Moving it there is the right home for it.

Selection rule, restated: *filter to designs clearing every gate by ≥20% of band width; among
those, maximise the minimum binding sub-score; break ties on novelty.*

### C2. AlphaFold-Multimer is known to be weak at antibody–antigen complexes

This is the deepest risk in the project and §4 treats it too lightly. De novo antibody–antigen
complex prediction is the documented weak spot of AF2-Multimer — far below its performance on
general protein–protein complexes. The entire rubric rests on a predictor that is worst at exactly
this problem class.

Consequences:

- **Challenge 1 is largely protected** — we have the 5GGS template, and templated fixed-backbone
  redesign is a much easier prediction problem than blind docking.
- **Challenge 2 is exposed.** No template, no DockQ safety net, and ipSAE ≥ 0.60 is a real gate.
  This is where the project most plausibly fails.

**Gate 1 must therefore test the honest case: refold 5GGS with templates DISABLED.** Templated
success proves nothing about Challenge 2. If the untemplated refold fails, we learn on Day 2 that
Challenge 2 needs a fundamentally different approach — AF3-class models (Boltz-2, Chai-1, which
handle antibodies better), or an initial-guess/template-prior protocol — rather than discovering
it on Saturday.

Add to the risk register as the highest-severity scientific risk, distinct from the platform risks.

### C3. `prodigy-prot` and `DockQ` have incompatible NumPy pins

Verified on PyPI: `prodigy-prot` 2.4.0 requires `numpy>=2`; `DockQ` 2.1.3 requires `numpy<2.0`.
**They cannot share an environment.** Resolution is isolated tool environments with a subprocess
boundary (see `BUILD.md` §3) — not a single venv. Would have cost an hour of confusion on Day 1.

Also unpinned-but-needed: **ANARCI requires HMMER**, an external binary not declared in its
metadata. `freesasa` publishes classifiers only through 3.11 and may need to build from source on
3.12.

### C4. Phase 0 is over-packed

Day 1 as written is: uv project + torch cu128 + six tool installs (two with environment conflicts,
one needing HMMER, one needing ESM weights) + four PDB fetches + `score_design.py` +
`validate_submission.py` + a four-way calibration study. That is **1.5–2 days**, not one.

Rather than compress it, accept it and take the time out of Challenge 2's slack — Phase 0 is the
foundation and rushing it poisons everything downstream. Revised: Gate 0 lands **Wednesday
midday**, Challenge 1 generation starts Wednesday evening.

### C5. The presentation is under-scoped by a factor of about five

50 points of 250 is **20% of the total** — the same weight as novelty and developability combined
across *both* challenges. §8 gives it one bullet list. A design scoring 85 with a poor pitch loses
to a design scoring 70 with a great one.

Treat it as a first-class deliverable with its own build time (Saturday evening, not Sunday
morning), and note that the judges are humans who will respond to the §7 dossier and the ensemble
framing far more than to a metrics table.

### C6. Challenge 2 Track B is hand-waved at the hardest step

§6 says "place the Fv against that epitope using the 5GGS binding geometry as a prior". That
sentence is doing an enormous amount of work. Concretely it means: **framework-align a germline
VH/VL pair onto pembrolizumab's VH/VL in the 5GGS complex** (superpose on framework Cα, which is
structurally conserved across antibodies), transplant so the germline Fv inherits the approach
angle and epitope, then design all six CDRs with LigandMPNN in the antigen's presence. Stated that
way it is a concrete, implementable procedure. Stated the old way it is a wish.

### C7. The format dry-run is scheduled six days too late

Building and validating the submission zip is scheduled for Sunday. It should happen **Wednesday,
with dummy files** — a two-hour task that de-risks the one failure mode guaranteed to be fatal and
guaranteed to be preventable. Fail fast on format.

### C8. Documentation time is not in the timeline

Per the workspace standard, every substantive session gets its own teaching doc, and three
knowledge notes from the handbook's reference list are still unwritten. That is roughly **an hour a
day** which the schedule currently pretends is free. Budget it, or it silently eats the evenings
that were supposed to hold slack.

### What survives review unchanged

The funnel shape, the cheap-before-expensive ordering, the artefact/metric separation, the two-tier
prediction design, the surrogate-guided ordering, the calibration-first principle, and the dossier.
Those are the load-bearing ideas and I would not change them.

---

# 15. Revised plan: milestones, not calendar

Supersedes §3–§11. Written 2026-09-15 after review, following the framing change.

## 15.1 What the framing change actually removes

Not submitting removes the *artificial* constraints. It does not remove the real one.

| Dropped | Why it existed | Kept |
|---|---|---|
| One design per challenge | Submission rule | **The eight gates.** They define "a design that would have counted" — the evidence a lab cares about |
| Strict folder/FASTA packaging as a gate | Auto-validation | Canonical layout as the *output format*; drives nothing |
| The Sunday deadline | Submission | Milestone ordering; no invented time estimates |
| Risk-adjusted single-shot selection | One shot | **Margin as robustness of claim** (§14-C1), not as insurance |
| Team name | Folder naming | Placeholder `RYAN_BINNY`. Not raised again. |

**The winner's curse survives, reframed.** §5.4a justified it partly through one-shot pressure.
That was the weaker argument. Taking the argmax over noisy measurements inflates the winner's
score *whether we pick one design or ten* — it is a statistical fact about selection, not about
submission rules. The fresh-seed re-score of any design we call "best" stays mandatory.

## 15.2 Settled decisions

**~~Fv screen → Fab confirm~~ — SUPERSEDED 2026-09-17, see G1c. The protocol is now Fab-only.**

The original reasoning was: screen wide on bare VH+VL (~350 residues, ~2.5× cheaper), re-fold the
shortlist as full Fab for reported numbers, because the constant domains clamp the VH/VL elbow and
a bare Fv leaves it under-constrained.

The elbow argument was right and it killed the screen rather than scoping it. Measured: Fv ipSAE
seed-to-seed reliability is **0.607**, Fab's is **0.965** — the unclamped elbow shows up directly as
measurement noise (`v04_h3_4` Fv sd 0.122, spread 0.215 over 3 seeds). Averaging seeds to recover
precision costs more than the Fab it was meant to save: ≥4 Fv seeds to approach Fab reliability =
2.9× the Fab's wall clock. The 2.5× residue saving does not survive the fixed ~60 s per-invocation
overhead. Rank correlation was the secondary evidence (restricted-range ρ = 0.469, CI spanning
zero); the cost inversion is the decisive part.

**This protocol has a hidden assumption and it must be tested, not assumed:** that Fv *ranking*
predicts Fab *ranking*. If it does not, the cheap screen is worthless and we would never notice,
because we would only ever see Fab numbers for designs the Fv screen already liked. Hence
**Gate 1c**. If Spearman ρ < 0.6, abandon the Fv screen and accept 2.5× fewer folds.

**ipSAE cutoffs 10 / 15** — already in `config/metrics.yaml` since it was written. Now marked
settled rather than unresolved.

**Boltz-2 is the primary predictor**; ColabFold/AF2 and Chai-1 become consensus predictors rather
than the critical path. Justification: torch-cu128 is verified working on this GPU while
JAX-on-Blackwell is unproven, and the compatibility objection does not apply — `ipsae.py`
explicitly supports Boltz PAE `.npz` (changelog: "January 3, 2026: Fixed Boltz2 issues").

**But ipSAE values from Boltz are PROVISIONAL until cross-calibrated.** The rubric's bands
(≥0.60 cutoff, ≥0.80 good) come from a metric developed on AlphaFold PAE. Boltz-2's PAE comes
from a different confidence head and is not guaranteed to be on the same numeric scale. Applying
AF2-calibrated thresholds to Boltz output is an unchecked assumption sitting under every
viability decision — the same class of error as reading a crystal B-factor as pLDDT. Resolved by
folding the same 5GGS complex with both and comparing (Gate 1d).

Second consequence: Boltz-2 is a **diffusion model**, so different seeds produce genuinely
different structures, not merely different confidence scores. "The prediction" is a distribution.
This makes the multi-seed ensemble treatment natural rather than bolted on.

## 15.3 Milestones

### M0 — Scoring harness ✅ COMPLETE
Gate 0 green. Five of eight metrics validated against ground truth; see
[the calibration table](results/calibration.md). ipSAE, interface pLDDT and NetSolP untested.

### M1 — Predictor qualification ← *everything waits on this*

Nothing precedes it. Three things run **concurrently** because they do not contend for the GPU
queue and each blocks later work: **NetSolP install** (the last unknown metric — `viable` can
never be `True` without it), the **DockQ sequence-divergence test**, and the
**5IUS epitope extraction**.

1. Install Boltz-2; fold 5GGS **with templates** → first real exercise of ipSAE and interface
   pLDDT, and the harness's first end-to-end run on a prediction.
2. Fold 5GGS **without templates** → the scientific question: can an AF-class model recover a
   known antibody–antigen pose *without being shown the answer*? Challenge 1 is template-
   protected; Challenge 2 is not.
3. Fold Fv-only and Fab for the same complex → the Gate 1c correlation baseline.
4. Install ColabFold; fold 5GGS once → the ipSAE cross-calibration.

### M2 — End-to-end smoke test and baselines

The refold already exercises fold → score. Extend it to design:

1. **One hand-mutated design** (4 substitutions in CDR-H3, which by §5.2 arithmetic lands at
   69.2% identity = the Good novelty band) through the full pipeline. Integration bugs surface
   here, not in unit tests.
2. **Baseline 0 — pembrolizumab itself.** Already measured: ΔG −14.3, 102 contacts, DockQ 1.000,
   novelty 100% (fails by construction). The binding upper bound.
3. **Baseline 1 — plain ProteinMPNN at defaults**, ~20 designs, no filtering, scored.

Baselines are the control the funnel must beat. Without them "our pipeline scored 84" is a number
with no referent. With them the claim becomes: *the funnel beats naive MPNN on hit-rate and
composite score, approaches pembrolizumab on binding, and beats it on novelty.* That is a
defensible claim; the other is not.

### M3 — Challenge 1 campaign  ✅ **COMPLETE 2026-09-19**

> **Deliverable: `mpnn_T0.5_s104_036`** — CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to
> pembrolizumab, arm T=0.5. Discounted surrogate **94.963**, rubric `final` **87.5**, viable, *(the 87.5 is convention-dependent and superseded: under the handbook-conformant `band_value: top` + `dockq_interface_agg: global` it is **94.0**; the same design scores **81.0 / 87.5 / 94.0** across the three readings the handbook permits — see `results/handbook_conformance.md`)* *(corrected 2026-09-25: this line previously read 96.0 and 84.0/90.0/96.0, computed when `dockq.compute` parsed DockQ's printed 3-dp summary. True `GlobalDockQ = 0.79958` bands `medium`, not `good`; the printed `0.800` banded `good`. Recomputed above from the unrounded value.)*
> fresh-seed DockQ **0.749**, CDR-H3 ensemble RMSD 0.52 Å over 7 seeds.
> See [the winner report](results/m3_winner.md).
>
> **As run:** 239 designs over T = 0.1/0.2/0.3/0.5 (CDR-H3 length fixed at 13) → **all 239
> folded unfiltered** at 1 seed, 6.0 h, zero failures → scored → shortlist 20 → **7 seeds
> each** → ranked on the continuous surrogate → winner shrinkage-discounted and fresh-seeded.
>
> **Four things the run changed about the plan, each measured:**
>
> 1. **Folded everything rather than filtering.** Using the aromatic filter and evaluating it
>    in the same run is circular. Folding all 239 costs ~30 extra folds and makes every filter,
>    threshold and null model evaluable offline on complete data, for ever.
> 2. **7 seeds on 20 designs, not 3 on 30.** Simulating the full procedure (shortlist →
>    re-seed → argmax) shows expected pick quality plateaus at k≈20, and that depth beats
>    breadth **once the budget is large enough** (at 120 folds: 60×3 → +1.388, 20×7 → **+1.466**).
>    ⚠ **The stronger claim "3 seeds is the worst allocation at every budget tested" is FALSE**
>    and was corrected on 2026-09-20: at a 40-fold budget 20×3 (+1.4024) beats 4×10 (+1.3847)
>    and 2×15 (+1.2992). The refuted wording survived here until 2026-09-21.
>    See [the sizing](results/m3_shortlist_depth.md).
> 3. **Ranked on a continuous surrogate, reported `final`.** `final` takes 3 distinct values
>    over 40 designs and flips band on seed noise; `src/locksmith/select/surrogate.py` keeps the
>    rubric's pricing and anchors but interpolates between them (single-seed reliability
>    **0.689** vs **0.602**). ⚠ **Two corrections, 2026-09-21.** (i) The 0.689 is biased — it
>    divides by the variance of 3-seed means, which already contains σ²_w/3; the correct value
>    on the same data is **0.653**, and the tell is free: Spearman-Brown reproduces the printed
>    rel3=0.849 from 0.653 and not from 0.689. (ii) **The surrogate no longer agrees with
>    `final`**: `surrogate.py:46` hardcodes midpoint anchors (2.5/7.0/9.5) while
>    `config/metrics.yaml:7` is `band_value: top`, and the surrogate never reads the config.
>    An all-medium design gives final=80.0, surrogate=70.0. **The submitted winner was selected
>    on this surrogate.** Needs a test, not a note.
> 4. **The winner's-curse discount was validated, not just applied.** Shrinkage predicted
>    94.963; the uncontaminated fresh seed measured **94.962**. The raw selection mean was 0.155
>    too high — **7× the 0.022 gap between first and second place**.
>
> **Known limits of the deliverable.** The top two are separated by **0.1 standard errors**, so
> the ordering is unresolved — this is *a* best design, not *the* best. Shortlist reliability is
> **0.629**, lower than simulated, because shortlisting restricts range (the noise behaved: 7-seed
> within-design sd 0.467 vs 0.529 predicted). The campaign **measured** the aromatic filter
> rather than using it, so G3's 194-fold saving is simulated, not demonstrated. And the named
> winner has aromatic count 2, so the filter at its own threshold would have discarded it.

<details><summary>Superseded: the 2026-09-18 re-scoping that this replaces</summary>

#### M3 — Challenge 1 campaign  ⚠ **re-scoped 2026-09-18 — shape now settled**

> **Rank on 3-seed mean composite; filter on CDR-H3 aromatic fraction BEFORE folding.**
>
> The ensemble-axis branch is closed. Tested at n=40: CDR-H3 ensemble RMSD correlates with
> 3-seed mean DockQ at rho −0.387, but **aromatic fraction fully explains it** — the partial
> correlation controlling for aromatics is −0.081 (p=0.62), while aromatics survive controlling
> for ensemble (−0.410, p=0.009). Aromatic fraction predicts DockQ **better** (−0.536) at **zero
> folds** versus three. See [the validation](results/ensemble_validation.md).
>
> This gives the funnel its first genuinely cheap stage: over-generate with MPNN, prune on
> aromatic fraction before any GPU time, then fold the survivors. Multi-seeding of the shortlist
> stays regardless — reliability 0.727 means single-seed ordering resolves tiers, not neighbours.
>
> **Sizing decided 2026-09-18: WIDE, run overnight.** 500 generated → aromatic-filter to 200 →
> fold 200 at 1 seed → shortlist 40 → 3-seed → fresh-seed the winner. ~282 folds ≈ 6.7 h at the
> measured 85 s/fold quiet, 10.4 h contended. **Do fold batching first** (~1.8×, cuts this to
> ~3.7 h): the condition for un-deferring it — a known, stable funnel pattern — is now met.
>
> Still missing: a genuine **wide** generation pass. The 40 designs on hand are one generator at
> one temperature with CDR-H3 length fixed at 13, which is also the limit of the aromatic result.

> Baseline 1 clears **every gate at a 100% rate**, so the funnel has **no hit-rate headroom** to
> demonstrate against it. ProteinMPNN redesigns onto the native backbone in complex, so the binding
> geometry — and therefore DockQ — is near-guaranteed by construction. A campaign that reports
> "our designs are viable" would say nothing the control does not.
>
> Discriminators that would actually bite, cheapest first: **(1) robustness under re-seeding**
> (the §5.4a winner's-curse re-score — these are single-seed numbers and the baseline has no such
> measure); **(2) larger backbone perturbation**, e.g. varying CDR-H3 length, which breaks the
> geometric guarantee; **(3)** the Challenge 2 regime, where the gates demonstrably do bite.
>
> Selection is settled: rank on `final`, tiebreak on DockQ (`selection_key` in config). Note the
> composite takes only **3 distinct values across 20 designs**, so the tiebreaker does the fine
> ordering and is load-bearing.

Funnel per §5.2, surrogate-ordered per §13.4, carrying a **shortlist of 5–10** rather than one.
Fresh-seed re-score on whichever we name best.

</details>

### M4 — Challenge 2 campaign  ◐ **PILOT RUN 2026-09-21 — nothing submittable**

> **Hardware block resolved by renting.** RFantibody's own pins (torch 2.3.1+cu118, dgl
> 2.4.0+cu118) install and run unmodified on a pre-Blackwell GPU. Rented RTX 3090 (`sm_86`),
> 5.5 h, **$2.82**. Throughput **2.5–2.7 min/backbone**, MPNN 41 s for 30 sequences, RF2 ~35 s
> per design, peak VRAM 3.4 GB of 24 — the card was never stretched.
>
> **Produced:** 18 conditioned + 18 unconditioned backbones, 30 MPNN sequences, 30 RF2
> predictions, **zero failures**, all carrying the corrected 113-residue PD-1 from crystal
> chain **Z**.
>
> **Three results.** (1) **Hotspot conditioning works**: `frac_iface_on_epitope` 0.712 vs
> 0.501, d=1.47, p=0.0016 — but this is **optional stopping** (interim look at n=10v5, then
> extended), CI **[0.73, 2.22]**, and the null arm tests conditioning-vs-none rather than
> this-epitope-vs-another. The decoy-patch control that could have failed was never run.
> (2) **`interaction_pae` cannot rank docks** — ICC **0.000**, F=0.70, against a
> pre-registered detectable floor of 0.32. The prereg fallback (hotspot contact count) stands.
> (3) **RF2 sits 24.87 Å from the designed poses** — though the parsimonious reading is that
> unfiltered designs failed the standard filter, not that RF2 is unreliable.
>
> **⛔ Blocking everything downstream: the pod was stopped without retrieving the data.** All
> 36 backbones, 30 sequences and 30 RF2 structures (443 MB) sit on a stopped RunPod volume.
> **None of the seven Challenge 2 metrics has a value**; there is no PDB, no PAE, no FASTA.
> Retrieval is a ~20 min file copy requiring a paid pod restart. See
> [the gap analysis](results/challenge2_remaining_work.md) — ~7 h of work remains, all local
> except that retrieval.

<details><summary>Previous status (2026-09-20) — blocked on hardware</summary>

### M4 — Challenge 2 campaign  ⛔ **BLOCKED ON HARDWARE 2026-09-20 — not attempted**

> **Status 2026-09-20.** Route chosen: **A, RFantibody** (target-conditioned CDR backbone
> diffusion), because §3.2 asks for "blank canvas … de novo" and the cheaper germline-framework
> route is Challenge 1's method relabelled. **Gate 0 failed in 25 minutes, measured:** RFantibody
> pins `torch==2.3.*`/cu118 and this GPU is `sm_120`; both cuBLAS and a plain ReLU fail with
> `no kernel image`, `get_arch_list()` shows **no PTX**, official DGL stops at cu124
> (cu126/cu128 both 403), and DGL's exact `torch==2.4.0` pin closes the bring-your-own-torch
> workaround. Docker cannot help — it isolates userspace, not the instruction set — and this box
> has no GPU runtime anyway.
>
> **The route is off-machine**, not abandoned: RFantibody's stack runs untouched on any
> T4/L4/A10. See [the risk scope](results/rfantibody_risk_scope.md) (9 risks, kill criteria,
> staged gates) and [the plan](results/challenge2_colab_plan.md) (RunPod/Kaggle over free Colab;
> hotspots = the 26-residue PD-L1 footprint already mapped to 5GGS; framework = RFantibody's own
> `hu-4D5-8_Fv.pdb`; RF2 as filter, Boltz-2 as the scoring fold so both challenges share one
> predictor).
>
> **Independently blocking:** the **germline CDR-H3 novelty metric does not exist**
> (`metrics/novelty.py` knows only pembrolizumab; `data/germline/` is empty). §6.3.1 scores
> Challenge 2 novelty against human germline, and CDR-H3 has no single germline template — it
> needs a best-match search over IGHV/IGHD/IGHJ. ~half a day, required for any route.
>
> **And the standing reason to be sceptical of whatever it produces:** Challenge 2 has no DockQ,
> so nothing in its rubric can detect a wrong pose; Boltz-2's median DockQ on post-cutoff
> complexes is 0.291; and SKEMPI showed no metric in the stack tracks measured affinity.

<details><summary>Original M4 framing (2026-09-17) — kept for the reasoning trail</summary>

</details>

### M4 — Challenge 2 campaign  ⚠ **HIGH RISK — revised 2026-09-17, no longer suspended**

> The post-cutoff test (G1f) measures what M4 depends on. After input validation the numbers are:
> median Fab DockQ **0.291** on 5 unseen complexes against **0.818** on the memorised 5GGS, with
> 1/5 clearing the 0.49 bar and 2/5 failing completely and seed-stably. Placement of novel
> antibodies is therefore unreliable but not uniformly broken.
>
> **An earlier reading of this test suspended M4 outright.** That reading was wrong: it rested on
> median 0.157 and on two 'confident but completely wrong' predictions, and 4 of 5 targets had
> been folded from sequences with internal loops silently deleted. Corrected, ipSAE's ranking is
> intact (Spearman +0.900) and *conservative* rather than inflated. The suspension is lifted.
>
> What remains true: this is the project's largest technical risk, a characterised failure is an
> admissible M4 outcome, and any M4 design's evidence should not rest on ipSAE level alone.

</details>

### M5 — Dossier  ✅ **SUPERSEDED AND EXCEEDED 2026-09-20**
The planned six-part dossier was replaced by something stronger: three pre-registered
*validity* controls (epitope knockout, composition-matched scramble null, SKEMPI ΔΔG
retrospective) plus an ICC/variance decomposition of the metric stack. Results in
`results/validity.md`, `results/skempi_validity.md`, `results/metric_validity.md`. The
original plan is below.

**Capped deliberately.** Full scoring on the 5–10 shortlist; full six-part dossier on **two**
designs per challenge: the best, plus one deliberately *different* one (different CDR-H3 length,
or different epitope approach). Contrast is worth more than a second near-copy, and it keeps
6 validations × N from exploding.

Gates first, dossier second. A beautiful dossier on a non-viable design is worth nothing.

### M6 — Writeup  ◐ **PARTIAL 2026-09-20**
Challenge 1 is packaged (`submission/RYAN_BINNY.zip`) with `docs/methods_and_limitations.md`
leading on the caveats, and validated by an artifact-only validator. The 3-minute pitch exists
as five slides of correct argument with no design work. Per-session docs are complete.

Per-session docs already exist. M6 is the synthesis: what was built, what was learned, what
failed, what we would do next.

## 15.4 Challenge 2: design toward the epitope, do not filter afterwards

Previously 5IUS was used only for *post-hoc* epitope-overlap checking — discovering at the end
whether a confident binder had hit the right face of PD-1. That is backwards.

**Extract the PD-L1 competitive footprint on PD-1 from 5IUS early** and pass it as explicit target
hotspots. Practical with both tools: RFdiffusion exposes `ppi.hotspot_res`, and RFantibody is
built specifically for epitope-targeted antibody design.

Note that **Track B gets this for free.** Grafting a germline framework onto pembrolizumab's
binding geometry inherits the PD-L1-competitive epitope by construction — which makes the
fallback stronger than §6 credited it.

The footprint is needed in both branches (hotspots for A, overlap validation for both), so it
moves early and is cheap with the existing `metrics/interface.py`.

## 15.5 Two corrections to the record

**PRODIGY ΔG is ordinal, not cardinal.** `results/calibration.md` presented the predicted 34 pM
vs measured 29 pM for pembrolizumab as validation of accuracy. That overstates it. PRODIGY is a
linear regression on contact counts and non-interacting-surface composition with reported RMSE
around 1.5–2 kcal/mol; since ~1.4 kcal/mol is a **10× change in Kd**, a 0.1 kcal/mol agreement is
well inside its noise. It is a coincidence, not precision.

What that run *did* validate is plumbing: the tool ran on the correct interface with the correct
chain selection. Keep it, labelled correctly. Use ΔG for **ranking** and for the ≤ −6 gate; do
not quote absolute Kd as meaningful. For fine discrimination between close designs, lean on
cross-predictor consensus instead. Note also that PRODIGY's ΔG is essentially a function of its
own contact count, so **ΔG and contacts are not independent evidence** despite occupying two of
six binding slots.

**DockQ 0.867 is a scale, not a ceiling.** Earlier wording implied a design could not meaningfully
exceed it. Wrong. The 0.867 between 5GGS's two copies measures how much *genuinely identical*
molecules differ when independently refined under different crystal packing — it sets the scale
**below which** "different pose" and "same pose, different packing" are indistinguishable. A
prediction that reproduces copy 1's specific conformation can legitimately score higher.

## 15.6 Revised gate list

| Gate | Test | Blocks |
|---|---|---|
| **G0** ✅ | Harness reproduces ground truth; pembrolizumab passes every binding gate and fails novelty; decoy rejected | — |
| **G1a** | Predicted 5GGS (**templated**) scores viable on all 8 metrics | Everything — proves the harness works on a prediction |
| **G1b** | Predicted 5GGS (**untemplated**) DockQ ≥ 0.49 vs crystal | **Hard go/no-go for Challenge 2 only.** Ch1 is template-protected and unaffected |
| **G1c** ❌ | **FAILED 2026-09-17.** Restricted-range ρ = 0.469, 95% CI [−0.14, +0.82], n=12. Separately and more decisively: Fv ipSAE reliability 0.61 vs Fab 0.96 (under-constrained elbow), so matching Fab precision needs ≥4 Fv seeds = 2.9× the Fab's cost. **Fab-only adopted.** See [the panel results](results/panel_g1c_g1d.md) | Resolved — funnel screens on Fab |
| **G1d** ◐ | **PARTIAL 2026-09-17.** Against a 14-point Boltz ipSAE↔DockQ curve, the AF2 point sits 3.1 residual sd low → **scale offset ≈ 0.13** (raw gap 0.187; the rest is deserved). n=1 for AF2. **Blocked for designs:** AF2 cannot fold without MSAs (single-sequence gives pLDDT 37, interpenetrating chains) and designs must not reach the public MMseqs2 server. Needs a local DB, or drop AF2 for Chai-1 | Treat Boltz ipSAE as ~0.13 optimistic |
| **G1e** ½ | DockQ ✅ tolerates ≥8 substitutions and indels once `--allowed_mismatches 40` + `--mapping ABC:ABC` are passed (defaults refuse **every** mutated design). NetSolP ⬜ downloaded, not installed | `viable` can return `True` |
| **G1f** ◐ | **POST-CUTOFF TEST — MARGINAL (revised 2026-09-17 after input validation).** 5 complexes released clear of Boltz-2's verified 2023-06-01 cutoff, CDR-H3 novelty 21–44%: **median Fab DockQ 0.291** vs 5GGS's 0.818; 1/5 clears 0.49; 2/5 fail completely and stably. ipSAE rank correlation on novel complexes is **intact** (Spearman +0.900) but sits ~0.19–0.28 BELOW the panel curve, i.e. conservative. **An earlier FAIL verdict (median 0.157, inverted confidence) was withdrawn** — 4/5 targets had been folded from coordinate-derived sequences with internal loops spliced out. See [the result and its validation](results/postcutoff_result.md) | Challenge 2 high-risk, not excluded |
| **G2** ✅ | **CLOSED 2026-09-18.** Baseline 1 (plain ProteinMPNN, 20 designs, defaults) run end to end: design → validate → fold → score → gate → rank, 20/20 folds, `designs.parquet` written. **20/20 clear all eight gates**; pembrolizumab itself scores 76.0 and is NON-VIABLE (novelty gate). See [the baseline report](results/baseline_mpnn.md) | The control exists — but shows the gates do not discriminate on fixed-backbone redesign |
| **G3** ❌ **REFUTED AS A DESIGN RULE 2026-09-22** (test: [g3_outcome_variable](results/g3_outcome_variable.md)) — re-ran G3's own equal-budget random-subset test with EACH scored metric as the outcome, n=239, 10,000 resamples. The filter beats its null on **2 of 6**: `dockq` (+0.0237, p=0.0001) and `iface_plddt` (+1.12, p=0.0001). **Both are properties of the PREDICTOR, not the interface** — DockQ here is pose retention against the parent crystal, and interface pLDDT is Boltz's own confidence. Every quantity about the interface itself is null or against it: `dg` p=0.064, `cdr_sasa` p=0.547, and **`contacts` runs the WRONG WAY** (filtered designs make 1.80 FEWER contacts; one-sided p for 'more contacts' = 0.988). That is what the chemistry predicts, since Tyr/Trp are large and contact-rich. So the filter selects for designs Boltz finds easy to place confidently, which is a metric gaming its own scorer, and neither surviving quantity even EXISTS for a de novo target. Original PASS statistics were sound; the outcome variable did not support the conclusion. Superseded status below. |
| **G4** | Ch2: ≥1 gate-clearing design **or** a characterised failure with evidence | Dossier |
| **G5** | Dossier complete on 2 designs per challenge (best + contrast) | Writeup |
| **G6** | Synthesis written | — |
