# Project state — 2026-09-26

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

Working tree is **clean**, 34/34 tests pass, and the 2026-09-25 session is committed
(7 commits, `4241bb6..d5cf334`).

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
- 34 invariant tests, several mutation-verified.
- The harness scores pembrolizumab itself correctly (the standing canary).

**Taken on trust.**

- **Boltz-2's confidence as a proxy for binding.** Six of the eight scored metrics are
  computed from files we generated; a confidently wrong pose scores exactly like a right
  one. This is stated in both shipped `methods_and_limitations.md` files rather than
  buried.
- **The negative-control result cuts against the rubric, not for us.** HyHEL-10, raised
  against hen egg lysozyme, clears **all five** §7.2 hard cutoffs **on `model_0`** — the
  argmax of five diffusion draws, and what the tool's default hands a grader. **On the
  median of those five it fails** (ipSAE 0.219 vs 0.609). Separately, and measured **on the
  median**, four of the five gates reject **0 of 6** wrong antibodies, so §7.2 rests on
  ipSAE alone. *Those two figures come from different estimators and are labelled here
  because an unlabelled pair is how this project got the false-positive rates wrong — see*
  [the register, §C1 and §C8](results/retractions.md). See
  [the negative control](results/negative_control.md).
- **Nothing here is wet-lab evidence.** No claim in the package says otherwise.

---

## 5. Test suite and repository

- `tests/test_invariants.py` — **34 tests**, all passing (`uv run pytest`, ~24 s).
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
| **Shape-matching the patch null** to the real epitope's spread | nothing — it is cheap | the drawn patches are more compact (7.73 Å RMS vs the epitope's 10.08 Å), making the test anti-conservative by an unquantified amount |
| **The reliability figure 0.629** | the original script | does not reproduce; plug-in gives 0.276 `midpoint` / 0.296 `top`. Flagged, not guessed at |

---

## 7. What is left

In order of what unblocks what.

1. **Mutation-test the inert tests.** Several assert over *source text* rather than
   behaviour. The MSA guard first, since it guards §3's defect. This project has already
   shipped a guard that matched `Number of failed examples` — a string Boltz prints
   **unconditionally**, including as `: 0` — so it failed every healthy fold it saw. A
   check written from a LEARNINGS sentence rather than from the tool's real output has not
   been tested against the tool.
2. **`results/rubric_headroom.md`** — regenerate under `band_value=top` or retract
   explicitly. It uses midpoint bands (max 95.0) against a `top` config and quotes a design
   at `dockq 0.747`. It does not ship, which is why it has survived.
3. **Split the NetSolP entry in `LEARNINGS.md`, then promote half of it.** The entry has
   absorbed a second, unrelated lesson (an error rate is a property of a threshold), so
   promoting the `ESM1b` half would strand the other. Split first; the test is then ~10
   lines (`netsolp.MODEL_TYPE == "ESM1b"`, plus pembrolizumab Fv VH **0.733** / VL
   **0.569** passing where `ESM12` 0.35/0.31 and `Distilled` 0.49/0.45 fail on Fab).
4. **The GPU-blocked controls in §6**, if a card is ever available. Note the depth sweep
   already decided *against* renting for design purposes; these are validity controls, a
   different justification.

**Done 2026-09-26 and no longer on this list:** per-interface DockQ verification in the
documentation guard (`check_docs_against_scores` now compares element-wise; mutation-tested
by restoring `A,B DockQ 0.931`), the `ProcessPoolExecutor` spawn fix and its test, and
[the retraction register](results/retractions.md), which is what had been blocking a clean
version of this file.

---

## 8. Reading order for a cold reader

1. This file.
2. [The retraction register](results/retractions.md) — everything the project withdrew, and
   the four figures flagged as not reproducing. Read before trusting a number found
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
