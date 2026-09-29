# Project state — 2026-09-28

**For a cold reader.** This is the single place to find out where the project is: what is
**verified**, what is **taken on trust**, what is **blocked**, and what is left. Every
number here was read from a file on this machine while writing it. Where a number has a
history, the history is in
[the retraction register](results/retractions.md) rather than inlined, because this file
kept accreting corrections until it contradicted itself in three places.

There is **no deadline and this is not being submitted** to the live event — see
[§15 of the plan](PLAN.md). What the project is now is a worked example of measuring a design
pipeline honestly, and the deliverable is the whole record, not the score.

---

## 0. Publication status — read this first

**There is no remote.** The repository was created on GitHub (private) on 2026-09-26,
found to be serving pre-scrub history, and **deleted**. Nothing is public and nothing has
ever been public.

**Why it was deleted rather than force-pushed.** `git filter-repo` scrubbed a copyrighted
handbook and three organisers' email addresses from local history, and the force-push made
the old commits unreachable — but GitHub retains unreachable objects and serves them by
SHA. Three organiser emails and a 727 KB PDF were retrievable from the remote for ~3 hours
*after* a fresh-clone verification reported five zeros. A clone performs a reachability
walk, so it structurally cannot distinguish "deleted" from "orphaned".

**Before any future push, verify against the remote, not a clone:**

```bash
gh api repos/<owner>/<repo>/commits/<old-sha>       # 200 = still retained
gh api repos/<owner>/<repo>/commits/<never-pushed>  # 422 = control works
```

Old SHAs come from `.git/filter-repo/commit-map`. After the deletion both probes return
404. Local history is clean: 0 handbook blobs, 0 full email addresses, all commits authored
`Ryan Robin <79134609+RRobin711@users.noreply.github.com>`.

**Do not push this repository with `--mirror` or `--all`** without re-checking
`refs/original/*` first — that namespace held all 34 work-email commits after an earlier
rewrite.

---

## 1. Headline

| | design | composite | viable | packaged |
|---|---|---|---|---|
| **Challenge 1** | `mpnn_T0.5_s104_036` **N55Q** | **94.0** | ✅ | ✅ |
| **Challenge 2** | **`bb_8_0`** | **93.6** | ✅ | ✅ |

`submission/RYAN_BINNY.zip` was rebuilt 2026-09-25 11:47 and **passes validation from
its own files** — `scripts/58_validate_submission.py` imports nothing from `runs/`, reads
no cached score, and re-derives every metric from the three files per design. Timestamps
inside the tree are within seconds of each other, which is the healthy signature; a day's
gap is the orphan tell that caught a stale document here once.

Working tree is **clean**, **42/42** tests pass, and the 2026-09-28 session is committed
(9 commits). *Commit SHAs are deliberately not quoted here: the history was rewritten on 2026-09-26 to scrub a copyrighted PDF and third-party emails, which re-hashed every commit. An earlier version of this line cited `4241bb6..d5cf334`, neither of which resolves.*

---

## 2. Challenge 1 — remix Keytruda

`mpnn_T0.5_s104_036` with the `N55Q` deamidation fix. CDR-H3 `ALRPRDVDRGFYK`, **38.5%**
identity to pembrolizumab, from the T=0.5 arm.

| metric | value | band | sub-score |
|---|---|---|---|
| `dockq` | **0.799579** | medium | 8.0 |
| `ipsae` | 0.821 | good | 10.0 |
| `dg` | −13.3 kcal/mol | good | 10.0 |
| `contacts` | 97 | good | 10.0 |
| `iface_plddt` | 88.630 | good | 10.0 |
| `cdr_sasa` | 1596.5 Å² | good | 10.0 |
| `cdrh3_identity` | 38.5% | good | 10.0 |
| `netsolp` | 0.569 | medium | 8.0 |

**→ final 94.0 / 100, viable.**

**Read the DockQ value carefully — it is the project's sharpest self-inflicted wound.** It
is printed to 6 dp deliberately. The true `GlobalDockQ` is **0.7995794972281312**, which is
**0.00042 below** the 0.80 Good edge and therefore `medium`. For nine days this scored
**96.0**, because `dockq.compute` parsed DockQ's *printed* summary, which rounds to 3 dp,
and `0.800` bands `good`. A project whose central argument is that the rubric is gameable
cannot keep two points won by a printf. Mechanism: the module now reads `--json`, and
`score.evaluate` flags any value within ±0.5 ulp of a band edge into
`Scored.rounding_risk`.

**Not affected by the MSA defect** in §3: its folds used a server MSA matched to its own
antigen. The discard warning appears once in `runs/diffusion_samples.log`, for the
Challenge 2 arm only.

**Known limit.** The top two designs in the shortlist were separated by **0.1 standard
errors**, so this is *a* best design, not *the* best. The winner-change analysis is in
[§B0 of the audit response](results/audit_response_2026-09-22.md); swapping for
`mpnn_T0.2_s102_032` was left as the user's call and has not been made.

---

## 3. Challenge 2 — invent the future

`bb_8_0`, from the constrained re-design campaign. Seven metrics, not eight: §5.2 applies
DockQ to Challenge 1 only, because a de novo design has no reference structure.

| metric | `model_0` | median of 5 | band | sub-score |
|---|---|---|---|---|
| `ipsae` | **0.904** | 0.859 | good | 10.0 |
| `dg` | −10.9 kcal/mol | −10.9 | medium | 8.0 |
| `contacts` | 99 | 98 | good | 10.0 |
| `iface_plddt` | 88.620 | 88.620 | good | 10.0 |
| `cdr_sasa` | 1110.5 Å² | 1159.6 | good | 10.0 |
| `cdrh3_identity` | 18.2% (germline) | 18.2 | good | 10.0 |
| `netsolp` | 0.555 | 0.555 | medium | 8.0 |

**→ final 93.6 / 100, viable on 5 of 5 diffusion samples.**

**Every Challenge 2 number produced before 2026-09-23 is withdrawn.** Boltz compares the
MSA's query length against the input chain and, on mismatch, **discards the alignment and
folds single-sequence**, announcing it only on stdout — which the harness captured and
threw away. Every fold paired a 123-residue antigen with a 113-residue cached alignment.
The 2×2 that isolates it is in
[the alignment-discard measurement](results/msa_silently_discarded.md): with a correct
alignment **0.012** both pre- and post-fix, without it **0.773 / 0.686**.

The consequence was not noise but **near-inversion of the ranking** — re-screening all 30
designs promoted one that had ranked **29th of 30** while the packaged design fell
**0.864 → 0.013** from 1st. `model_0` fold now asserts the alignment was used (processed
MSA width 123 = antigen length 123), pinned by tests.

**The ceiling is measured, and it is the generator's.** 144 folds over 18 backbones × 8
constrained sequences: viability arrives at a **constant ~8% per sequence** with no
backbone heterogeneity (χ² = 22.91 on 17 df, p = 0.152; beta-binomial LRT p = 0.202), and
eight times the sequences produced **nothing better than the first pass found** — best
0.859 at depth 1, 0.854 at depth 8. So more backbones and more sequences are the same
experiment at different prices, and **renting a GPU is not justified**. Reaching past ~0.86
needs a different generator, not more samples from this one. See
[the depth sweep](results/depth_sweep.md).

**What the 0.904 does and does not mean.** It is Boltz's confidence, not an affinity
measurement. What the 40-crystal calibration panel buys is that this confidence tracks pose
accuracy at **ρ = +0.702**. Its error rates must be quoted at a stated DockQ threshold —
0% FP / 58.3% FN at Acceptable+, 12.5% FP / 25.0% FN at Medium+ — and never as the
flattering half of each; see [§C1 of the register](results/retractions.md).

---

## 4. What is verified, and what is taken on trust

**Verified on this machine.**

- The package re-derives its own scores from its own files (`scripts/58`, exits non-zero on
  any structural problem or failed cutoff).
- 258/258 retrieved pod artefacts sha256-match the server —
  [the checksum pass](results/checksum_pass_2026-09-22.md).
- 42 invariant tests, most mutation-verified.
- The harness scores pembrolizumab itself correctly (the standing canary).
- **Hotspot conditioning actually steers RFdiffusion** — the decoy-patch control, the only
  experiment that could have falsified it, run 2026-09-28 and **passed**. Conditioned onto
  a patch 165.9° away, 15 of 16 backbones follow it (mean **0.803** of their interface) and
  **all 16 read 0.000** on the PD-L1 epitope, against an unconditioned baseline on that face
  of **0 / 18**. [The control](results/decoy_patch_control.md). *Targeting only — it says
  nothing about binding, and 2 of 18 docked nowhere at all.*

**Taken on trust.**

- **Boltz-2's confidence as a proxy for binding.** Six of the eight scored metrics are
  computed from files we generated; a confidently wrong pose scores exactly like a right
  one. This is stated in both shipped `methods_and_limitations.md` files rather than
  buried.
- **The negative-control result cuts against the rubric, not for us — but it is narrower
  than this entry used to claim.** HyHEL-10, raised against hen egg lysozyme, clears
  **all five** §7.2 hard cutoffs **on `model_0`** (the argmax of five diffusion draws, and
  what the tool's default hands a grader) **on the truncated 113-residue antigen**. Three
  qualifiers, not one, and each was added only after the previous fix was assumed to have
  finished the job: **on the median** of those five it fails (ipSAE 0.219 vs 0.609), and on
  the **repaired 119-residue** antigen its best of five is **0.409** and it clears nothing.
  The 113-mer was missing 6 of nivolumab's 14 epitope residues, so that panel's own positive
  control failed and it was pre-registered **INCONCLUSIVE**; the flattering result and the
  broken control had the same cause.
  **What survives on both constructs:** four of the five gates reject **0 of 6** wrong
  antibodies (measured on the median), so §7.2 rests on ipSAE alone. **What does not:**
  "the rubric accepts an antibody that cannot bind" — it accepts one only on a construct
  whose own positive control it also fails. *A rate is a property of every parameter it was
  computed under — threshold (§C1), estimator (§C8), construct (§C9) — and each time this
  project fixed one axis it assumed it had found them all; see*
  [the register](results/retractions.md). See
  [the negative control](results/negative_control.md).
- **Nothing here is wet-lab evidence.** No claim in the package says otherwise.

---

## 5. Test suite and repository

- `tests/test_invariants.py` — **42 tests**, all passing (`uv run pytest`, ~7 s), and
  `.github/workflows/ci.yml` runs them on a clean clone.
- Git: `master`, no remote, linear history, one commit per unit of work.
- `pytest` and `python-pptx` are now declared in `pyproject.toml`. Both had been
  undeclared; the suite could not be run at all, and `scripts/57` crashed at the deck step
  *after* writing the package files, so a failed build looked like a successful one.

---

## 6. What is blocked, and on what

| item | blocked on | cost |
|---|---|---|
| **The decoy-patch control** — hotspots on the opposite face of PD-1 | a GPU run | still the only control that could falsify the conditioning result |
| **Sequencing the 18 unconditioned backbones** | a GPU run | ~2–4 GPU-hours (~$1–2); separates range restriction from a dead `interaction_pae` |
| ~~**Shape-matching the patch null**~~ | ~~nothing — it is cheap~~ | **DONE 2026-09-28** (`scripts/94_shape_matched_patch_null.py`). Worth **+0.019** on the null mean (0.153 → 0.172) against a real 0.712; conditioning result goes **17/18 → 18/18**. [Register §D4](results/retractions.md) |
| ~~**The reliability figure 0.629**~~ | ~~the original script~~ | **RESOLVED 2026-09-28** — it reproduces as a *7-seed-mean* reliability (1 − 0.176²/0.290² = 0.6317), and `scripts/35_winner.py:202-206` was tracked all along. See [register §D2](results/retractions.md) |

---

## 7. What is left

**Items 1–7 were cleared on 2026-09-28** (9 commits); what they turned into is recorded in
[that session's doc](docs/sessions/2026-09-28-clearing-the-backlog-and-three-guards-that-could-not-see.md).
Two remain and **both need a decision rather than an hour**:

1. ~~**The two validity controls.**~~ **The decoy-patch control is DONE — 2026-09-28,
   and it PASSED.** Run locally on CPU in ~6 h for **$0**, not on a rented GPU: RFantibody's
   CPU route already existed here (`~/.venvs/rfab-cpu`, validated 2026-09-21 at Gate 0b) and
   the decoy control needs RFdiffusion only, so renting was never required for this block.
   - **Result: pre-registered ROW 1.** Decoy-conditioned backbones land at **0.803** on the
     decoy face and **0.000** on the PD-L1 epitope; the unconditioned arm touches the decoy
     face **0 / 18** times. So `frac_iface_on_epitope = 0.712` is a property of our
     conditioning, not of RFdiffusion's prior — the live alternative explanation is
     excluded. [The control](results/decoy_patch_control.md).
   - **Caveats, in the data rather than the footnotes:** 2 of 18 produced no antigen contact
     at all and are excluded (n=16, named); interfaces are smaller than the conditioned
     arm's (median 6 vs 9); one arm, one seed set, 95% CI ±0.133; and this is **targeting,
     not binding**.
   - **Still open: sequencing the 18 unconditioned backbones.** Needs ProteinMPNN, which is
     the one step that does need a rented card (RFantibody pins `torch==2.3.*`, no PTX, so
     nothing reaches `sm_120`). Folding and scoring afterwards run locally and free. This
     separates range restriction from a dead `interaction_pae`; it does not bear on the
     conditioning result above.
2. **Republish.** Recreate the repo private, push, verify old SHAs 404 **against the
   remote** (a fresh clone structurally cannot answer this — see §0), read the rendered
   README / PROJECT-STORY / retractions, then flip public. `.github/workflows/ci.yml` now
   exists and its first push is also its first real test.

### Cleared 2026-09-28

1. ~~No CI.~~ `.github/workflows/ci.yml` — clean-clone install plus the suite, with
   `uv lock --check` first. Mutation-tested: a stale lock and `pytest`-as-an-extra each
   turn it red. Full torch is required (anarcii imports it at call time), CPU-only is fine.
2. ~~`00_doctor.py` cannot fail.~~ Now `--scope {fold,validate,all}` with the required set
   declared per scope. The set was **backwards**: validation needs the five tools and no
   GPU, the preflight demanded a GPU and none of the tools, and never checked NetSolP at
   all. Five tests, all mutation-verified.
3. ~~~18 stale `96.0` derivations.~~ §3.3's worked arithmetic **recomputed** (it printed
   `dockq 0.800 | good | 10.0`, i.e. the rounding defect presented as correct working);
   everything else indexed. [C3](docs/lecture/CORRECTIONS.md)'s index went from **4 rows to
   32**, grouped by kind, and ships the command that regenerates it.
4. ~~The 5,448-word session index.~~ Now 926 words, one line per session. Checked first
   that the long cells were derivative: 93.4% of their distinctive tokens already appear in
   the doc each row links to. Also fixed **66 broken cross-references** — a heading with an
   em dash slugs to a *double* hyphen on GitHub and every link used one; they resolved in
   Obsidian, so the whole set was broken only in the renderer we publish to.
5. ~~The regeneration plan's retracted rates.~~ Corrected per threshold, "validated" →
   "characterised", stale 96.0 → 94.0, and the document marked **superseded**: the depth
   sweep already answered its central question with "do not spend the money".
6. ~~The withdrawn NetSolP triple.~~ Indexed as course correction
   [C5](docs/lecture/CORRECTIONS.md) with the correct per-chain table; banner updated
   across 11 files.
7. ~~§D2 (`0.629`).~~ **The flag was wrong and so was its blocker.** It reproduces as a
   *7-seed-mean* reliability (1 − 0.176²/0.290² = 0.6317), and `scripts/35_winner.py` —
   "the original script" said to be needed — has been tracked since the initial commit with
   the estimator at lines 202–206. Recomputed from raw folds: 0.660. What survives is
   narrower: the recorded single-seed **0.296** is the outlier (components imply ≈0.20),
   and **no script produces 0.276 or 0.296** — they were computed in prose.

Also cleared, from §6 rather than this list: **shape-matching the patch null**
(`scripts/94_shape_matched_patch_null.py`), worth **+0.019** on the null mean against a
real 0.712, taking the conditioning result 17/18 → **18/18**.

**Done 2026-09-26 and off this list:** the remote leak; the shipped §9.2 section describing
the pre-fix molecule; the novelty table (now computed); the convention triple
`84.0/90.0/96.0` → `81.0/87.5/94.0` in all three shipped documents; the HyHEL-10 construct
correction (§C9); the batch-padding mechanism withdrawal (§B10); the validator polluting
the package; `pytest`/`uv.lock`/`gemmi`/prerequisites; case-duplicate PDBs; the private
company-context note; `config/metrics.yaml`'s withdrawn values and refuted ranking claim.

## 8. Reading order for a cold reader

1. This file.
2. [The retraction register](results/retractions.md) — everything the project withdrew, and
   the five figures flagged as not reproducing. Read before trusting a number found
   anywhere else in the repo.
3. [The session index](docs/sessions/README.md) — one line per working session; the teaching
   lives in the per-session docs.
4. [The lecture course](docs/lecture/README.md), with
   [its own corrections file](docs/lecture/CORRECTIONS.md) read first.
5. [The repo README](README.md) for the organising idea, and [PLAN §15](PLAN.md) for how the
   milestones were re-scoped.

**One warning about this repo's prose.** Its errors cluster in sentences, not in code — the
documentation guard found a shipped file asserting seven metrics of a design that was no
longer in the package, and a mixed-threshold error rate survived four independent audits.
Where a results file and a generated artefact disagree, the artefact is right, because the
artefact was recomputed and the sentence was copied.
