# Project state — 2026-09-22 (overnight run)

**For a cold reader.** This file is the single place to find out where the project is.
It records what is **verified**, what is **taken on trust**, what is **blocked**, and the
shortest path to a complete submission. Every number below was recomputed from files on
this machine during this session unless it says otherwise.

> ## ✅ HEADLINE: **Both challenges are packaged, viable and validated.**
>
> | | design | score | viable |
> |---|---|---|---|
> | **Challenge 1** | `mpnn_T0.5_s104_036` | **96.0** | ✅ |
> | **Challenge 2** | `bb_2_0_dldesign_1` | **96.0** | ✅ |
>
> `submission/LOCKSMITH_DEV.zip` (0.9 MB) contains both. `VALIDATION PASSED` from the
> packaged files alone, re-deriving every metric with no run directory and no cached score.
>
> **Challenge 2 is 1 of 30**, and the earlier `0/30` from the same night is **withdrawn**:
> it was an artefact of folding at `recycling_steps=3`. Re-folded at recycling 10, the
> winner scores ipSAE **0.864** — higher than the positive control's 0.842 on a real
> crystallised pair — while all 29 others sit at **≤0.331**. Nothing in between.
>
> **Neither 96.0 is evidence of binding.** Both are self-consistency scores. This project's
> own SKEMPI work shows the stack does not track measured affinity in either direction.

---

## 1. What was done tonight, in order

| # | Task | Status |
|---|---|---|
| 1 | Finish the sha256 pass on the retrieved pod artefacts | ✅ **DONE** — 258/258 verified, 0 mismatches |
| 2 | Challenge 2 end to end | ✅ **DONE** — 30/30 folded, **0/30 clear the gates** (all fail `ipsae`) |
| 3 | Select and package Challenge 2 | ⛔ **CORRECTLY NOT RUN** — no design clears; packager refused, exit 2 |
| 4 | Audit tonight's own work | ✅ **DONE** — 46 checks, 0 failures, 3 findings |
| 5 | Resolve the G3 aromatic filter | ✅ **DONE** — refuted as a design rule, propagated |

---

## 2. Challenge 2 — **1 of 30 viable, packaged, validated**

| step | status |
|---|---|
| Germline novelty wired for Ch2 (§6.3.1) | ✅ scored 30.0% on the winner; pinned by 3 tests |
| `challenge=1` un-hardcoded in 57 and 58 | ✅ |
| Fold all 30 (recycling 10) | ✅ 30/30, zero failures |
| PAE → submission format | ✅ |
| Seven metrics + §7.2 gates | ✅ **1 of 30 clears** |
| Positive control | ✅ Fab 0.776 / **Fv 0.842** |
| **Step 3 — select and package** | ✅ **RUN** — pre-registered rule, §4.3 tree, validated |

**The winner, re-derived by the validator from the package alone:**

`ipsae` **0.864** · `dg` −12.400 · `contacts` 98 · `iface_plddt` 83.580 ·
`cdr_sasa` 1066.900 · `cdrh3_identity` 30.000 (germline) · `netsolp` 0.562 (medium)
→ binding 10.0, developability 8.0, novelty 10.0 → **final 96.0, viable**.

**The 29 others** all fail on `ipsae` alone, range 0.000–0.331.

### The withdrawn `0/30`, and what it cost

`recycling_steps=3` was inherited from Challenge 1 and never re-examined. At that setting
15 of 30 designs scored exactly 0.000 and the best was 0.372 — a pool piled up at the
floor, which is a convergence diagnosis, not a result. The ranking was actively
misleading: **the design that clears ranked 2nd; the one ranked 1st still fails.**

The positive control I built to test this **passed and was blind to it**, because it ran
at recycling 3 too. It correctly exonerated the Fv construct and printed a verdict about
Challenge 2 that was wrong within the hour. *A control eliminates the confound you thought
of and is silent on the one you did not.*

A signal was also available and dropped: my own PAE diagnostic flagged
`bb_2_0_dldesign_1` at **81.4%** of cross-chain pairs under PAE 10 Å, by far the highest
of the nine checked. It was noted, then not followed up before `0/30` was written up.

---|---|
| Germline novelty wired for Ch2 (§6.3.1) | ✅ pinned by 3 tests |
| `challenge=1` un-hardcoded in 57 and 58 | ✅ |
| Fold + score + gate machinery | ✅ runs end to end; the packager's refusal guard fires correctly |
| Positive control | ✅ **Fab 0.776, Fv 0.842** — the pipeline places a real cognate pair well above the gate |
| **Gate pass rate** | ⏳ **UNKNOWN** — the recycling-3 answer (`0/30`) is withdrawn |

**What went wrong.** The first pass used `recycling_steps=3`, inherited from Challenge 1's
fold settings without re-examination — the same class of error as inheriting the Fv/Fab
decision, which is what the positive control was built to check. Recycling depth turns out
to matter enormously for these complexes:

| design | recycling 3, seed 1 | recycling 10, seeds 1/2/3 |
|---|---|---|
| `bb_2_0_dldesign_1` | 0.263 | **0.864 / 0.842 / 0.856** |
| `bb_4_0_dldesign_2` | 0.372 | 0.331 / 0.416 / 0.361 |
| `bb_6_0_dldesign_2` | 0.242 | 0.011 / 0.267 / 0.105 |
| `bb_4_0_dldesign_0` | 0.235 | 0.000 / 0.000 / 0.000 |
| `bb_7_0_dldesign_1` | 0.234 | 0.161 / 0.169 / 0.000 |

**Note it is not a uniform lift.** Four of the five got no better or worse; one moved
decisively and reproducibly. Extra recycling does not rescue bad designs — it **resolves**
which are which, and at recycling 3 the pool was too noisy to tell them apart. The
single-seed ranking at recycling 3 was near-worthless: the design that clears was ranked
**2nd**, and the one ranked 1st does not clear.

**A signal I had and under-weighted.** My own PAE diagnostic, run hours earlier, flagged
`bb_2_0_dldesign_1` as having **81.4%** of cross-chain residue pairs under PAE 10 Å — by
far the highest of the nine I checked. I noted it, said the gate outcome was "genuinely
open", and then reported `0/30` without going back to it.

---|---|
| Germline novelty wired for Ch2 (§6.3.1) | ✅ `novelty.compute(..., challenge=2)` routes to `metrics/germline.py`; pinned by 3 tests |
| `challenge=1` un-hardcoded in 57 and 58 | ✅ 57 uses a `CHALLENGE` constant; 58 passes `challenge=` to novelty and reads DockQ applicability from config instead of `if challenge == 1` |
| Fold the 30 designs | ✅ **30/30, zero failures**, Boltz-2, seed 1, handbook §4.2.2 antigen |
| PAE → submission format | ✅ `submit/pae.py` path exercised by the packager (which then refused) |
| Seven Ch2 metrics + §7.2 gates | ✅ **0 of 30 clear** |

**Which metric failed, by how much, on how many designs:**

| metric | cutoff | min | median | max | failed on |
|---|---|---|---|---|---|
| `cdr_sasa` | ≥ 250 Å² | 929.1 | 1344.6 | 2209.5 | 0/30 |
| `cdrh3_identity` (germline) | < 95 % | 16.7 | 32.1 | 44.4 | 0/30 |
| `contacts` | ≥ 10 | 44 | 77.5 | 114 | 0/30 |
| `dg` | ≤ −6 | −14.0 | −10.95 | −8.0 | 0/30 |
| `iface_plddt` | ≥ 65 | 65.91 | 73.74 | 94.29 | 0/30 |
| `netsolp` | ≥ 0.50 | 0.552 | 0.586 | 0.629 | 0/30 |
| **`ipsae`** | **≥ 0.60** | **0.000** | **0.006** | **0.372** | **30/30** |

**The shortfall is not marginal.** Best design 0.372 vs 0.60 needed — **0.228 short,
1.6×**. Median 0.006. Exactly zero on 15 of 30. Only one design reaches 0.3.

**Why, mechanically.** `ipsae` is the only metric computed from the **PAE** — the model's
uncertainty about where the chains sit relative to each other. The other six read
coordinates or sequence. On `bb_10_0_dldesign_0`: 61 heavy-atom contacts, ΔG −9.6,
interface pLDDT 75.7, **ipSAE 0.000**, because not one cross-chain residue pair has PAE
below 10 Å (minimum 18.40 Å). Verified this is genuine and not the known empty-table
failure: ipsae wrote a full 14-line table and scored the heavy–light interface at 0.876.

**This confirms a prediction rather than discovering a surprise.**
`results/challenge2_scope.md` declined Challenge 2 in part because Boltz-2's median Fab
DockQ on post-cutoff complexes is **0.291**, and these designs are more novel than that
test set.

**Does NOT establish that the designs fail to bind** — ipSAE is a statement about the
predictor's uncertainty, and `results/skempi_validity.md` shows this stack does not track
affinity in either direction. **Does NOT establish that conditioning failed** — it
demonstrably worked (17/18 backbones beat a contiguous-patch null).

### Step 3 — not run, deliberately

No selection was made, no folder built, no zip changed. The packager refused with exit 2
and printed its reason. The pre-registered selection rule (hotspot contacts, tie-broken on
`frac_iface_on_epitope`) is implemented in `scripts/75_challenge2_package.py` and ready
should a future run produce a viable design; it was **not** applied to a non-viable pool.

---

## 3. Step 1 — the checksum pass ✅

**Verified:** 258 of 258 files match a **sha256 computed on the server**, 0 mismatched,
0 unreachable. Manifest `runs/challenge2_pod/CHECKSUMS.jsonl`, summary
`CHECKSUM_SUMMARY.json`, sentinel `CHECKSUMS.DONE`. 258 rather than 256 because the
earlier pull had skipped two `workspace/lock/` files.

**Budget:** ~20 minutes of the 90-minute ceiling, 1 of 3 restart cycles. Pod stopped.

**What failed on the way, and what I did about it:**

| attempt | configuration | outcome |
|---|---|---|
| 1 | "Automatically migrate your Pod data" (the only path to a real machine) | **failed — "There are no instances currently available"** |
| 2 | "Start Pod using CPUs" | pass completed |

**The pre-transfer allocation check FAILED and I proceeded anyway — on purpose.** With
the pod running, the console reported **vCPU 0, Memory 0 GB**, the identical configuration
that OOM-killed Jupyter previously. Migration was unavailable, so there was no
real-RAM option. I ran it because the pass checkpoints every hash to disk immediately, so
the downside of a mid-run death was a partial manifest a later attempt resumes from —
which is what the instruction itself asked for. Jupyter survived the whole pass.

**Taken on trust:** whether "vCPU 0 / Memory 0 GB" is a genuine allocation or a console
display artefact for a GPU pod started on CPU. I cannot establish which. The pod plainly
had *some* memory (it served 258 hash requests and 427 MB of files, showing 16–18% memory
utilisation), but I did not verify the number from inside the pod.

**Deviation from the instruction, stated plainly:** the script does **not** stop the pod
itself. That needs a RunPod API key, which does not exist on this machine, and I was not
willing to create an account credential unasked. I polled the artefact instead (not the
process table) and stopped the pod manually within a minute of the sentinel appearing.

Full write-up: [[results/checksum_pass_2026-09-22|the checksum pass]].

---

## 4. Step 4 — auditing tonight's own work ✅

`scripts/76_audit_tonight.py` re-derives every headline number in
`results/audit_response_2026-09-22.md` from the files, and checks
`scripts/70_epitope_patch_null.py` against its own docstring.

**Result: PASS 46, FAIL 0, UNVERIFIABLE 0.** Machine-readable in
`results/audit_of_audit_2026-09-22.json`.

**Verified to reproduce exactly:** DockQ exits 1 at defaults and gives 0.816 with the
flags (A–C 0.723, A–B 0.931); conditioned 0.7119 vs unconditioned 0.5005, d = 1.4747,
CI [0.733, 2.216]; the whole winner-change analysis (old winner `mpnn_T0.5_s104_036`,
new winner `mpnn_T0.2_s102_032`, shipped design falls to 4th, 18/20 ranks change,
Spearman 0.755, gap 0.1908, within-sd 0.2263); patch null 0.712 vs 0.154, 17/18; all four
RF2 ICCs and the 0.317 floor; B3's 1-of-30 at 32.86 Å and Spearman +0.415; and every
sequence claim (15 subs, 93.53%, CDR-H2 by one, charge +2 vs 0, aromatics 2 vs 4,
VH 0.699, VL 0.569).

**Three findings:**

1. **One figure was wrong and is corrected.** Shortlist reliability was written as 0.28;
   that is the `midpoint` value quoted in a `top` context. It is **0.296**.
   Convention-mixing, committed in the document that reports convention-mixing.
2. **The audit script carried the night's characteristic bug on its first run.** Its
   summary tested `ok is True`, but numpy returns `np.bool_` and `np.True_ is True` is
   `False`, so seven genuine passes printed PASS *and* were listed UNVERIFIABLE, and
   `json.dumps` refused them.
3. **A limitation of the patch null.** Its contiguous patches are **more compact than the
   real epitope** (7.73 Å RMS spread vs 10.08 Å; uniform draws 13.21 Å). The null is the
   right *family* but is not shape-matched, which plausibly makes the test
   **anti-conservative** by an unquantified amount. The result stands (17/18, 0.712 vs
   0.154); the honest phrasing of the null is "a compact 26-residue patch elsewhere",
   not "an epitope-like patch elsewhere".

**Also verified: the new test suite genuinely fails when the bugs are reintroduced.**
Five mutations, five localised failures, suite restored to green after each — see
`results/mutation_test_2026-09-22.md`.

---

## 5. Step 5 — the G3 aromatic filter: REFUTED ✅

`scripts/74_g3_outcome_variable.py` re-runs G3's own equal-budget random-subset test with
**each** scored metric as the outcome (n=239, 10,000 resamples).

| outcome | filtered | random | margin | one-sided p |
|---|---|---|---|---|
| `dockq` | 0.7287 | 0.7050 | +0.0237 | **0.0001** ✅ |
| `iface_plddt` | 91.52 | 90.40 | +1.12 | **0.0001** ✅ |
| `dg` | −12.355 | −12.196 | +0.159 | 0.064 |
| `ipsae` | 0.7981 | 0.7947 | +0.0034 | 0.241 |
| `cdr_sasa` | 1519.06 | 1519.85 | −0.79 | 0.547 |
| `contacts` | 99.82 | 101.62 | **−1.80** | 0.988 |

**It wins on 2 of 6, and both are properties of the PREDICTOR rather than the interface** —
DockQ here is pose retention against the parent crystal, and interface pLDDT is Boltz's own
confidence. Every quantity about the interface itself is null or against it, and
**`contacts` runs the wrong way**: filtered designs make 1.80 *fewer* heavy-atom contacts,
exactly as the chemistry predicts when you select against large aromatics.

So the filter selects for designs the scorer finds easy to place confidently — a metric
gaming its own scorer — and **neither surviving quantity even exists for a de novo
target**. The original statistics were sound; the outcome variable never supported the
conclusion.

**Propagated in the same pass:** `PLAN.md` (G3 ✅→❌), `README.md`,
`results/pitch_outline.md`, `results/m3_g3_verdict.md` (SUPERSEDED banner),
`LEARNINGS.md`.

**Downstream checked, not assumed:** `scripts/32_shortlist_and_reseed.py:76` sorts on
`-x["surrogate"]`; aromatic count appears only in a reporting line. **The filter was never
a selection step, so refuting it does not disturb the Challenge 1 selection.**

**Bonus defect found while propagating:** the shipped `methods_and_limitations.md`
contained a reference to `results/g3_verdict_reexamined.md`, **a file that never existed** —
written into the submission during last session's pass. Replaced with the result inline.

---

## 6. Challenge 1 — unchanged and still valid

Rebuilt and re-validated tonight after the doc edits: **final 96.0, viable True**,
validator passes from the package's own files, `structures/` contains exactly the two
files §4.2.1 lists.

**Left alone deliberately, as instructed:** the deck, and any decision about swapping the
submitted design for `mpnn_T0.2_s102_032`. The winner-change finding is documented in
`results/audit_response_2026-09-22.md` §B0; the decision is the user's.

---

## 7. Test suite and version control

- `tests/test_invariants.py` — **20 tests**, all passing.
- Repo under git; this session added a commit per unit of work.

---

## 8. What is blocked, and on what

| item | blocked on |
|---|---|
| **The decoy-patch control** (hotspots on the opposite face of PD-1) | a GPU run. Still the only control that could falsify the conditioning result. |
| **Sequencing the 18 unconditioned backbones** | ~2–4 GPU-hours (~$1–2). Separates range restriction from a dead `interaction_pae`. |
| **Shape-matching the patch null** to the real epitope's spread | nothing — it is cheap, and §4 finding 3 says why it matters. |
| **The reliability figure 0.629** in the record | the original script. Does not reproduce (plug-in gives 0.276 `midpoint` / 0.296 `top`). Flagged, not corrected. |
| **Promoting the last LEARNINGS entry over cap** | `assert_artefacts()` fixtures. 41 bullets against a 40 cap. |

---

## 9. Shortest path to a complete submission from here

**Challenge 1 is complete and viable** (96.0, validates from its own files). Nothing on
this list is required for it.

**Challenge 2 needs a design its own predictor will place.** In rough order of
cost-effectiveness:

1. **Re-fold the existing 30 with more seeds and more recycling.** Cheapest possible test
   of whether ipSAE ~0 is stable or sampling noise. We ran **one seed, 3 recycling steps**.
   If the best design moves 0.372 → 0.6 on a better sample, everything downstream unblocks.
   ~1 GPU-hour. **Do this first — it is the only step that could change the verdict without
   new designs.**
2. **Give the antibody chains an MSA.** Ours were folded with an antigen MSA only, which is
   this project's standing convention for *redesigns of a known antibody*. A de novo VH/VL
   is a different case and the convention was inherited without re-examination.
3. **Generate more backbones.** 10 backbones × 3 sequences is a thin pool; the pilot was
   sized as a tooling demonstration, not a campaign.
4. **Run the decoy-patch control** before any Challenge 2 claim goes in the deck.

**If none of that lifts ipSAE, the honest submission is no Challenge 2 folder plus the
measurement** — which is what exists now, and is a stronger artefact than a packaged
design that fails a hard cutoff.
