> **What this is.** The brief written for an unattended overnight run on 2026-09-21 —
> the machine works alone for hours with no one to ask. Kept in the repository because the
> interesting part is not the task but the structure: a stated objective that is explicitly
> *not* the obvious metric, pre-registered gates that can fail, and a self-verification
> pass the run has to survive before its output is trusted. It is a planning artefact, not
> documentation of the pipeline; see [the session index](sessions/README.md) for what
> actually happened.

# Task: Challenge 2 on CPU, unattended overnight — with self-verification

Ryan is asleep or going to sleep. Nothing here blocks on him. **Runtime does not matter** — a
slow job that finishes is worth more than a fast one that doesn't start.

Route A (RFantibody) was chosen for Challenge 2 and Gate 0 failed on GPU: the pinned CUDA 11.8
stack ships no `sm_120` kernels and no PTX, and DGL drags torch backwards. CPU may sidestep the
*kernel-image* half of that. **It does not sidestep the rest, and that assumption is untested** —
see Gate 0. Cloud was the prior plan; it's off tonight because free notebooks die when the lid
closes and a rented pod needs account setup Ryan isn't awake for.

## The objective, and why it is not backbone count

Tonight's backbones are **worthless the moment a pod is rented** — an A10 generates them at
roughly 50x this rate. What cannot be bought tomorrow is a measured CPU route, verified inputs,
the germline metric, and **one complete pass through all three stages that proves the pipeline
joins up**. That pass de-risks the pod run; 20 backbones with nothing downstream does not.

> **Primary objective: one verified end-to-end pass — backbone -> MPNN -> RF2 -> Boltz -> scored.
> Volume is secondary and strictly optional.**

A night that lands exactly one verified end-to-end design is a **success**, and the report must
say so. Do not treat a low N as failure.

---

## Order of work (changed — read this before starting)

1. **§C germline novelty metric**, in the existing `~/.venvs/locksmith`, BEFORE any install.
2. **Gate 0-CPU** in a fresh isolated venv.
3. **Gate 0b** — per-step timing, RSS, determinism control.
4. **Pre-register**, then run.

§C first is deliberate: it is the only guaranteed deliverable, it blocks Challenge 2 on every
route including the pod, it needs no GPU, and doing it first puts it safely on disk before an
install can break anything.

---

## Gate 0-CPU — verify by execution, never by flag (~20 min + clone + weights)

**Correction to the earlier draft: RFantibody is NOT cloned and `hu-4D5-8_Fv.pdb` is NOT in this
repo.** `vendor/` holds only `ipsae` and `netsolp`. Gate 0 therefore includes a clone plus a
multi-GB weights download. Budget it; do not assume the inputs are on disk.

**Environment isolation is a hard requirement.** Create a NEW venv for this stack. Yesterday DGL
pinned `torch==2.4.0` exactly and *silently replaced* a working torch build. `~/.venvs/locksmith`
carries `torch 2.11.0+cu128` and §D's Boltz run depends on it. After the install completes, run
`uv run scripts/00_doctor.py` against the working env — **that is the gate**. If doctor fails,
stop, restore, and report; the night's GPU half matters more than its CPU half.

Verify by arithmetic and by reading code, not by `is_available()` (which lied twice on 2026-09-20):

- a real `torch` matmul on CPU, checked against a known value
- a real DGL graph message-pass on CPU, >1 node, output values inspected
- an SE3-Transformer forward pass if a minimal one is cheap to construct
- **`grep -rn "\.cuda()\|device=.cuda.\|\.to('cuda')" ` over RFdiffusion/RFantibody inference
  paths.** Hardcoded device calls survive the move to CPU untouched and are an environment
  problem, not a CUDA-version problem. This check exists because the claim "CPU sidesteps that
  entirely" was a mechanism asserted before testing — the same error as yesterday's PTX claim.

**If any fails: stop.** Write `results/gate0_cpu.md` with the measured failure. Do not patch,
rebuild, or source-compile — that is porting, excluded by the standing kill criterion.

**Print the Gate 0 verdict and a one-line recommendation immediately, then proceed to Gate 0b
without waiting for a reply.**

## Gate 0b — size the night in minutes, not hours

**Measure seconds per diffusion step, not per backbone.** RFdiffusion logs per-step progress; on
CPU a single backbone plausibly runs 2-12 h, so waiting for one to finish could consume the whole
night before any decision is possible. Take the step rate after a handful of steps and extrapolate.

Also measure, at this gate and before anything runs concurrently:

- **Peak RSS.** `results/rfantibody_risk_scope.md` R5 records RFantibody's own Docker baseline as
  `--memory 10g` *host* RAM — and that is its GPU configuration. On CPU everything that lived in
  VRAM moves to host RAM, so treat 10 GB as a **floor**. This box has ~11 GB available of 15 GB
  total, and has already had one silent host-RAM kill. **RAM, not DGL, may be the binding
  constraint.** State the ceiling explicitly and decide from it whether Boltz may run concurrently.
- **A determinism control (tier 0).** Run the same seed twice back-to-back and record the
  deviation. Torch CPU reductions are thread-count dependent and may legitimately differ, so
  without this the B3 canary can condemn a perfectly healthy run. The observed deviation IS the
  canary's tolerance.
- **Thread pinning.** Set `OMP_NUM_THREADS` / `MKL_NUM_THREADS` explicitly and reserve cores.
  Timing measured on a quiet box was wrong by **2.3x** on 2026-09-20 once other stages competed.
  Re-measure once contention is live, and size from the contended number.

Inspect the output structure: residue count, loops within the specified ranges, no NaN
coordinates, chain naming as expected. A backbone that "completed" but is geometric garbage is a
failure.

Then **pre-register** in `results/prereg_2026-09-21_challenge2_cpu.md`, before any production run:
N, the cap, what counts as enough to carry into RF2, the detectable effect for B4 (below), and
what outcome would make the run uninformative.

**Budget.** 08:00 checkpoint — write a status summary and keep going; Ryan decides over coffee.
**14-hour hard cap** from launch as a runaway guard (not 24 — a 24 h cap collides with tomorrow's
pod plans and holds the sleep inhibitor all day). Reserve time inside the cap for MPNN and RF2.

**Stop rule (revised).** Stop and report if the *end-to-end pass* cannot complete inside the cap.
Do NOT stop merely because fewer than ~6 backbones fit — the earlier draft's rule would have
discarded a night that achieved the primary objective.

---

## A. The run

```
rfdiffusion  -t <PD-1 target, chain T>  -f hu-4D5-8_Fv.pdb  -n <N>
             -l <CDR loop lengths>  -h <hotspots>
proteinmpnn  -q backbones.qv -n 4 -t 0.2
rf2          -q seqs.qv -r 10
```

**Inputs must be BUILT, not collected. The earlier draft was wrong that these exist:**

- **Hotspots.** The 26-residue PD-L1 competitive footprint exists only as a **prose residue list**
  in `results/epitope.md` (H64 V66 H68 E70 S73 G74 Q75 T76 D77 T78 L79 A80 A81 D85 P89 G90 Q91
  C123 G124 I126 L128 I132 I134 K135 E136 R139), in **5IUS author numbering** mapped to 5GGS by
  explicit alignment (the entries are only 90.1% identical). Regenerate the hotspot string from
  `src/locksmith/design/epitope.py` and **assert it against those 26 names** before use.
  **TRAP:** `runs/pd1_epitope_contacts.json` looks like the right file and is not. It is
  **pembrolizumab's** epitope (it feeds the knockout control at `scripts/48_epitope_knockout.py:95`),
  keyed by **sequence index** over the 123-aa antigen, not author numbering. Wrong epitope AND
  wrong numbering, and both fail silently. Do not read that file.
- **Framework.** `hu-4D5-8_Fv.pdb` ships with the RFantibody repo, which is not cloned. It arrives
  with the Gate 0 clone. Using it rather than pembrolizumab's scaffold is what makes this
  Challenge 2 rather than Challenge 1 relabelled.
- **Target.** **NOT raw `5ggs.pdb` chain C — that is a SECOND PEMBROLIZUMAB HEAVY CHAIN.**
  5GGS holds two Fab copies (A/B and C/D) and two PD-1 copies (**Y/Z**). Every planning
  document in this project, including earlier drafts of this prompt, said "5GGS chain C
  relabelled to T"; that conflates the handbook's *submission* convention (A=heavy,
  B=light, C=antigen, true of complexes WE generate) with the crystal's own chain IDs.
  Use **`data/refs/prepared/5ggs_ABZ.pdb` chain C** (113 aa, already relabelled from Z),
  the same antigen Challenge 1 folds against. `src/locksmith/io/pdb.py`'s module
  docstring documents this hazard; the code is clean, only the prose was wrong.
  **Assert the target is ~113-123 aa and NOT ~219 aa before conditioning on it.**
  Verification that catches it: aligning the 5IUS footprint gives **90.2% identity to
  chain Y / 90.1% to chain Z** and **15.4% to chain C**. Note the mapper reports
  "26/26 residues mapped" in ALL THREE cases — coverage is not the check, identity is.

Run constraints: one chained job, sleep inhibitor held (`systemd-inhibit`), resumable so a kill
doesn't lose completed work, and don't starve §C or §D of CPU. Shuffling backbone order is a
**no-op here** unless several loop-length or hotspot configurations are run — backbones from one
configuration are i.i.d. samples with nothing to balance. Shuffle over configurations if there are
several; otherwise skip it rather than cargo-culting it from the fold chains.

---

## B. Self-verification

**B1. Assert on artefacts, never exit codes.** After every backbone, before counting it: file
exists, non-trivial size, parses as a structure, expected residue count, loops within specified
ranges, no NaN or duplicate coordinates, no chain collapsed to a point. **Plus the conditioning
check:** does this backbone's designed loop make heavy-atom contact with the conditioned hotspot
residues? That is deterministic, usable at n=1, and is the primary instrument for whether
conditioning is working. A backbone failing any check is logged as failed and does not enter the
pool.

**B2. Heartbeat.** Append to `runs/challenge2_cpu/heartbeat.log` every few minutes: timestamp,
completed, failed, current stage, mean time per unit, projected completion. Ryan reads one file in
the morning and knows what happened.

**B3. Canary.** Re-run the Gate 0b backbone at the same seed near the run's midpoint. Compare
against the **tier-0 deviation measured at Gate 0b**, not against byte-identity. Report either way.

**B4. Negative control, with its power stated first.** Generate a few backbones with hotspots
removed and compare epitope proximity against the conditioned arm. **Before running it, state the
effect detectable at the n you will actually have** — this project read four underpowered nulls as
evidence of absence on 2026-09-20 and corrected all four. Note the likely outcome: unconditioned
loops landing on one specific 26-residue face by chance is a near-zero-rate event, so the effect
may be large enough that n=4 is decisive. Compute it; don't assume either way. B1's per-backbone
contact check is the primary instrument, this is the corroborating one.

**B5. Stall and crash detection.** If no unit completes within 3x the measured per-unit time, log
loudly and attempt one clean restart from the resume point; if it stalls again, stop and write the
diagnosis. **Wait on PIDs, never `pgrep -f`** — and note the failure mode that actually bit: the
pattern was in the *launcher's own argv* because a heredoc built the script inside `bash -c`. The
guard belongs on the argv, not the filename. Prefer a sentinel file the previous stage writes on
exit over any process-pattern match.

**B6. Failure budget.** More than 30% of attempted backbones failing artefact checks -> stop and
diagnose rather than accumulate a pool of unknown quality.

**B7. Write results incrementally.** `results/challenge2_cpu_run.md` updated as you go. If the
machine dies at 04:00, what is on disk is still a usable report.

---

## C. Germline novelty metric — FIRST, and needed on every route

Handbook §6.3.1: Challenge 2 novelty is CDR-H3 identity to **human germline**. Verified verbatim,
and verified to be the **only** novelty term — §3.2's success criteria, §6.3.1, §7.1 step 4 and
`config/metrics.yaml:153` (`novelty: [cdrh3_identity]`) all agree. `metrics/novelty.py` is 38 lines
and knows only pembrolizumab; `data/germline/` is empty.

Build it: ANARCI or IgBLAST germline assignment, then percent identity across the CDR-H3 junction.
Hard cutoff <95%. CDR-H3 spans the V-D-J junction and has no single germline template, so this
needs a best-match search over IGHV/IGHD/IGHJ, not a single reference string.

**Validate on cases where the expected number is DERIVABLE.** The obvious fixture — a
germline-framework graft — is not one of them: its CDRs are MPNN-designed, so its CDR-H3 is not
the germline's. That fixture would validate **V-gene framework assignment** and leave **junction
identity**, the thing actually scored, untested. Keep it if cheap, labelled as validating
germline assignment only. The real validation set:

| Case | Expected |
|---|---|
| CDR-H3 copied verbatim from a germline IGHJ segment | ~100% |
| Scrambled / random CDR-H3 of matched length | low — and this is the metric's **noise floor** |
| An antibody with a published germline call | reproduces that call |
| Pembrolizumab's `ARRDYRFDMGFDY` | record whatever it gives — humanised mouse-derived, so a realistic middle case, not a known answer |

Report the noise floor beside every identity number. A <95% cutoff means nothing without knowing
what a random loop of the same length scores.

## D. Scoring stays local and unchanged

RF2 is the orthogonal filter; survivors get re-folded with **Boltz-2** so both challenges share one
predictor. Then the existing harness, cutoffs, packager and validator.

**Correction to the earlier draft: `challenge=2` is not fully wired.** `build_challenge()` in
`src/locksmith/submit/package.py:114` is generic and `score.py`/`config.py` filter bands by
challenge tuple — but `scripts/57_build_submission.py:98` hardcodes `evaluate(raw, challenge=1)`
and `scripts/58_validate_submission.py:70` branches on `if challenge == 1`. Both need a challenge
parameter. Small, but not free, and it is on the critical path to a packaged artifact.

GPU is idle while RFdiffusion runs on CPU — use it for Boltz, **subject to the RAM ceiling
measured at Gate 0b.**

## E. Morning report

Lead with what is and isn't trustworthy, in this order: Gate 0 verdict, canary reproduction,
conditioning check (B1) and negative control (B4) with its stated power, failure rate, doctor
result for the working env, then N completed. **N is the least interesting number on that list**,
and one verified end-to-end design is the success condition.

Deliverables: `results/gate0_cpu.md`, `results/challenge2_cpu_run.md`, the prereg, the tested
germline metric, session doc, index row.

## F. Route B is a test fixture, not a submission

Build one germline-framework graft to validate §C. **Do not put it in the Challenge 2 folder.**

The reason, stated correctly — an earlier version of this argument was wrong and the wrong version
must not reach the write-up:

- Route B (`PLAN.md:333-338`, C6 at `PLAN.md:731-738`) framework-aligns a germline VH/VL onto
  pembrolizumab's Fv in 5GGS and designs all six CDRs with LigandMPNN. **The loop backbone is the
  germline scaffold's own, NOT pembrolizumab's.** Do not write "inherits Keytruda's loop geometry";
  it is false and a reader refutes it in one move.
- The correct objection: **Route B's loop backbones are inherited from an unrelated germline
  scaffold and are never conditioned on PD-1.** Only the sequence is target-aware. Route A diffuses
  loop backbones conditioned on the epitope. New geometry aimed at a target is what §3.2's "blank
  canvas ... de novo" is reaching for; re-sequencing borrowed geometry is not.
- **Do not argue from epitope inheritance.** §3.2 says verbatim: *"You may target the same epitope
  as pembrolizumab, a different epitope, or design multi-epitope approaches."* It is explicitly
  permitted.
- **Do not argue from the transplanted pose.** The scored complex is re-folded by Boltz from
  sequence, so 5GGS's approach angle is design-time scaffolding and never reaches the submission.
  The final pose is unverified — but that is equally true of Route A, so it is not a discriminator.
- **The disqualifying part is that the deviation is undetectable.** Ch2 novelty is CDR-H3 identity
  to germline, which any designed loop clears trivially, and there is no DockQ. The rubric would
  score it viable and nothing would reveal it isn't de novo. A deviation the rubric can't detect is
  one we would have to disclose ourselves, and writing "this is not actually de novo" in the docs
  of a de novo challenge costs more than the points are worth.

If Route A cannot run, the honest output is a **measured refusal plus the scope document**. That is
a defensible thing to show Ajitesh.

## G. Framing that must appear in the write-up

However many backbones land, **this is a pilot, not a campaign** — RFantibody's own docs cite real
campaigns in the 10k range. Say so plainly.

**Hold one claim as provisional.** That RFantibody diffuses CDR loop backbones conditioned on the
epitope is currently sourced from `results/challenge2_colab_plan.md:54`, our own secondary doc,
because the repo isn't cloned. **Confirm it from RFantibody's source at clone time** and mark it
verified or correct it. Yesterday's withdrawals came from exactly this kind of one-level-removed
provenance.

And the caveat no hardware fixes: Challenge 2 has no DockQ, Boltz's post-cutoff median Fab DockQ is
0.291, and SKEMPI showed nothing in the stack tracks measured affinity. If a design survives to
packaging, run the **epitope knockout** on it — the one control that actually discriminated — and
write the limitations doc to say we cannot show it binds.

## H. While the CPU grinds — deck outline

The night is machine-bound, not attention-bound. The deck is 50 of 250 points and does not exist.
Produce a **structured outline with the measured numbers slotted in — not finished slides.** The
argument is Ryan's to make and the deck carries his voice. Spine candidates: the audit is the
asset, not the molecule; four controlled experiments showing a standard in-silico antibody scoring
stack cannot rank binders; SKEMPI checked against real ΔΔG, which almost nobody does.

Note the pitch's old spine (loop pLDDT blind to conformational heterogeneity) was **refuted at
n=239** and must not reappear.

## Standing instruction

Push back in writing on anything here that is wrong. Five claims were corrected on 2026-09-20,
four of them Ryan's, all toward a more interesting finding. **This prompt has already had three
factual errors corrected against disk** (RFantibody not cloned, hotspots not a usable artifact,
`challenge=1` hardcoded) and one argument corrected (the Route B geometry claim). Assume it still
contains one. Check against the handbook and the code before acting, not after.
