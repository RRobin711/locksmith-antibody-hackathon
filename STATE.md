# Project state — 2026-10-03

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

**It is public.** <https://github.com/RRobin711/locksmith-antibody-hackathon> — public
since 2026-09-29, 107 commits, CI green. Owned by `RRobin711`, which is the account that
authored every commit (`79134609+RRobin711@users.noreply.github.com`) and the one holding
the `workflow` scope GitHub requires to push `.github/workflows/`.

**The September attempt was deleted, and this is a different repository.** The first repo
(2026-09-26, private) was found serving pre-scrub history and destroyed. `git filter-repo`
had scrubbed a copyrighted handbook and three organisers' email addresses from local
history, and the force-push made the old commits unreachable — but **GitHub retains
unreachable objects and serves them by SHA**. Three emails and a 727 KB PDF were
retrievable for ~3 hours *after* a fresh-clone verification reported five zeros, because a
clone performs a **reachability walk** and so structurally cannot distinguish "deleted"
from "orphaned".

**What was verified before this push, with controls in both directions:**

```bash
gh api repos/<owner>/<repo>/commits/<old-sha>        # 200 = still retained
gh api repos/<owner>/<repo>/commits/<never-pushed>   # 404 = NEGATIVE control works
gh api repos/<owner>/<repo>/commits/<known-present>  # 200 = POSITIVE control works
```

The positive control was added on 2026-09-29 and September had only the negative one. Two
404s prove nothing unless the probe can be shown to return 200 for something — otherwise
"nothing retained" and "the probe is broken" are the same observation.

| check | result |
|---|---|
| handbook blobs / full email addresses in history | **0** — only `@users.noreply.github.com` survives |
| commit identity, all 107 | single author, as above |
| `scripts/59_prepublish_audit.py` | clean (history paths, all blobs incl. unreachable, case collisions, authors) |
| run artefacts (`outputs/`, `cached_schedules/`, a 7.8 MB `.pkl`) | removed from **history** before the first push; 0 additions in any commit |
| anonymous fetch of README / PROJECT-STORY / retractions | HTTP 200 |

A full-history bundle was taken and verified restorable before that rewrite.

**Two standing cautions.** Do not push with `--mirror` or `--all` without re-checking
`refs/original/*` — that namespace held all 34 work-email commits after an earlier rewrite.
And `gh`'s active account flips between the two configured logins; the remote is pinned to
`https://RRobin711@github.com/...` so the credential helper cannot silently authenticate as
the wrong one.

**Still open:** an empty stray repo at `RyanB-raekis/locksmith-antibody-hackathon` from a
push rejected for missing the `workflow` scope. Probed with both controls: `isEmpty: true`,
no retained objects — the pre-receive hook rejected before anything was kept. Deleting it
needs `gh auth refresh -h github.com -s delete_repo`, which only the user can grant. It is
tidiness, not exposure.

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

Working tree is **clean**, **42/42** tests pass, CI is green on the public remote, and the
2026-09-29 session is committed (**107 commits** total).

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
**no *detectable*** backbone heterogeneity (χ² = 22.91 on 17 df, p = 0.152; beta-binomial
LRT p = 0.202), and eight times the sequences produced **nothing better than the first pass
found** — best 0.859 at depth 1, 0.854 at depth 8. See
[the depth sweep](results/depth_sweep.md).

**Read the heterogeneity null with its power attached — it is weak.** That test had **23%
power against the effect it itself fitted**, and 80% power only at ρ ≈ 0.24, five times
larger. A pool in which three of the eighteen backbones were five times better than the
rest would have been missed **three times in five**. So the supportable claim is *no
backbone is detectably more than about four times the pool rate* — **not** that the
backbones are exchangeable, which is how it was written and how it carried the decision not
to spend. The "more backbones and more sequences are the same experiment" conclusion is
therefore **unsupported rather than refuted**: ~0.86 may well be the generator's ceiling,
but this evidence cannot separate that from a pool containing good backbones. The design
that would settle it is the prereg's own stratum C (+144 folds, power 0.802), **declined on
the strength of the null it would have corrected**, and now free — see §6.
[Register §B11](results/retractions.md), [the power analysis](results/heterogeneity_power.md).

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
- Git: `master`, linear history, one commit per unit of work. **Public remote since
  2026-09-29** — `RRobin711/locksmith-antibody-hackathon`, pinned in `origin` as
  `https://RRobin711@github.com/...` so a flipped `gh` account cannot authenticate as the
  wrong user. See §0.
- `pytest` and `python-pptx` are now declared in `pyproject.toml`. Both had been
  undeclared; the suite could not be run at all, and `scripts/57` crashed at the deck step
  *after* writing the package files, so a failed build looked like a successful one.

---

## 6. What is blocked, and on what

| item | blocked on | cost |
|---|---|---|
| ~~**The decoy-patch control**~~ | ~~a GPU run~~ | **DONE 2026-09-28 and it PASSED** — ran locally on CPU for $0, not on a rented card. [The control](results/decoy_patch_control.md) |
| ~~**Sequencing the 18 unconditioned backbones**~~ | ~~a GPU run~~ | **NOT BLOCKED — the blocker was false.** ProteinMPNN runs on this laptop's CPU (verified 2026-10-03; **~2.4 min** for all 144 sequences at the prereg's measured 8 s per 8 draws per backbone, $0). Only the folding costs anything, and that is local. [Register §B12](results/retractions.md) |
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
   - **Still open: sequencing the 18 unconditioned backbones — and it needs no rental.**
     This was listed as rental-blocked from 2026-09-22 to 2026-10-03 on the grounds that
     RFantibody pins `torch==2.3.*` with no PTX, so nothing reaches `sm_120`. The pin is
     real; the conclusion was not. RFantibody's own bundled ProteinMPNN falls back to CPU
     (`proteinmpnn_interface_design.py:85-90`) and generates all 144 sequences in about
     **2.4 minutes** for $0 — 18 backbones at the prereg's measured 8 s per 8 draws, and
     the tool itself verified at 2 sequences in 1 second. (An earlier draft of this line
     said "~10 minutes", which is the prereg's figure for **576** sequences, not 144.) Folding and scoring were already local. The
     whole experiment is free. See [register §B12](results/retractions.md), which also
     records that the project had proved this five days *before* writing down that it was
     impossible. It separates range restriction from a dead `interaction_pae`; it does not
     bear on the conditioning result above.
2. ~~**Republish.**~~ **DONE 2026-09-29 — it is public.** See §0 for the verification and
   its controls. `.github/workflows/ci.yml` ran for the first time on that push and passed
   (3m20s, 42 tests); its header had warned that ~7.1 GB of install against "roughly 14 GB
   free" was tight, and the run reported `/dev/root 72G, 31G avail` — the warning was
   wrong and has been corrected rather than left standing on a false premise.

   **Still open, and it needs you:** deleting the empty stray repo requires
   `gh auth refresh -h github.com -s delete_repo`.

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

0. [The short version](docs/the-short-version.md) if you have five minutes rather than an
   hour — it links back here for everything it compresses.
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
