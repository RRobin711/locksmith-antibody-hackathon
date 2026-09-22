# Project state — 2026-09-22 (overnight run)

**For a cold reader.** This file is the single place to find out where the project is.
It records what is **verified**, what is **taken on trust**, what is **blocked**, and the
shortest path to a complete submission. Every number below was recomputed from files on
this machine during this session unless it says otherwise.

> ## ⚠ HEADLINE: Challenge 2 — status filled in at the end of this run
>
> *(This section is rewritten when scoring completes. If you are reading this line, the
> run did not finish; see §2 for what was measured and `runs/challenge2_fold/scores.jsonl`
> for whatever landed.)*

---

## 1. What was done tonight, in order

| # | Task | Status |
|---|---|---|
| 1 | Finish the sha256 pass on the retrieved pod artefacts | ✅ **DONE** — 258/258 verified, 0 mismatches |
| 2 | Challenge 2 end to end (wire germline novelty, un-hardcode challenge, fold 30, score 7 metrics, report gate pass rate) | see §2 |
| 3 | Select and package Challenge 2 — **only if ≥1 design clears** | see §2 |
| 4 | Audit tonight's own work | ✅ **DONE** — 46 checks, 0 failures, 3 findings |
| 5 | Resolve the G3 aromatic filter | ✅ **DONE** — refuted as a design rule, propagated |

---

## 2. Challenge 2

*(filled in at the end of the run)*

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
