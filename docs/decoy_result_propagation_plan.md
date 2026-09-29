# What to do the moment the decoy control lands

**Written 2026-09-28, while the run is still diffusing and before any decoy number exists.**
Written now precisely *because* it is before: the work each outcome demands differs by an
order of magnitude, and deciding what counts as "the honest write-up" after seeing a
flattering or damning number is how a project talks itself into the reading it prefers.

Run first, and let it name the row:

```bash
uv run python scripts/95_decoy_patch_control.py --analyse runs/challenge2_decoy/bb
```

It prints one of four outcomes against `BAR = 0.500`, the measured unconditioned baseline.
**Do not paraphrase the row it names.** Record the row, then follow the matching section.

---

## The blast radius, measured before the result

A markup- and newline-tolerant sweep for `0.712`, the nulls (`0.154` / `0.172`), `17/18`,
`18/18`, `frac_iface_on_epitope` and conditioning-claim phrasing finds **153 occurrences
across 39 files** (some are false positives; the list is a starting point, not a worklist):

| tier | where | note |
|---|---|---|
| **shipped** | `submission/RYAN_BINNY/RYAN_BINNY_Challenge2/docs/methods_and_limitations.md:106` | **generated** by `scripts/57_build_submission.py` — fix the GENERATOR and rebuild; never hand-edit a packaged file (2026-09-25's lesson) |
| front matter | `README.md`, `PROJECT-STORY.md`, `STATE.md`, `PLAN.md` | read first by anyone |
| results | `challenge2_patch_null.md`, `challenge2_patch_null_shape_matched.md`, `decoy_patch.md`, `challenge2_pilot.md`, `pitch_outline.md`, `audit_*` | the primary record |
| course | `05-experiment-design.md` (14), `07-the-campaign.md`, `08-what-broke.md`, `01-…`, `09-critique.md` | index per policy, do not rewrite |
| sessions | 2026-09-21, -22, -23, -28 docs | **historical — leave alone**, they record what was believed then |

---

## ROW 1 — conditioning works (decoy high, epitope low)

*Smallest job.* The published claim survives its only falsifier.

1. Write `results/decoy_patch_control.md`: both means, per-backbone table, the row that
   fired, and the 4.9 Å shared-edge limitation restated.
2. ~~Add a register entry under **B** (confirmations), not C or D.~~ **Wrong, corrected on
   execution 2026-09-28.** `results/retractions.md` has no confirmations section — A, B, C
   and D are *all* withdrawals, and every B entry is WITHDRAWN or REFUTED. A passing control
   does not belong in a retraction register at all. It goes to
   `results/decoy_patch_control.md`, to `STATE.md` §4 *"Verified on this machine"*, and as a
   forward pointer from the patch-null results. Left visible rather than edited away: a plan
   written in advance is only useful if you can see where it was wrong.
3. Update `STATE.md` §7 item 1: control **passed**, and say what it does and does not buy —
   it establishes *targeting*, never *binding*.
4. One line in `results/challenge2_patch_null_shape_matched.md` pointing forward to it.
5. **Do not upgrade any existing wording.** 0.712 stays 0.712; a passed control does not
   make the number larger or the claim broader.

## ROW 2 — inconclusive (both below the bar)

*Middle job, and the one with the highest risk of being written up dishonestly.*

1. Record it as **INCONCLUSIVE**, using that word, in `results/decoy_patch_control.md`.
2. **Do not write "the interfaces did not move to the decoy, which shows specificity for
   the real epitope."** That is the inversion this row exists to forbid: if the decoy face
   is not dockable, the experiment never tested conditioning at all.
3. Register entry under **D (flagged)**: the conditioning claim remains *unfalsified rather
   than confirmed*, and say which experiment would still settle it (a dockable decoy —
   pick the patch by predicted dockability, not only by geometry).
4. `STATE.md` §7 item 1 stays open, reworded: the control ran and returned no information.
5. The precedent to follow is `results/negative_control.md`, which fired Rule 3 and said so
   rather than harvesting its negative arm. The precedent to avoid is the framework control
   that overrode its own inconclusive branch at reporting time.

## ROW 3 — REFUTED (epitope still ≈ 0.712)

*Largest job. Assume half a day, not an hour.* The conditioning claim is the project's
Challenge 2 headline.

1. `results/decoy_patch_control.md` first, with the full table, then:
2. **Register entry in section C, withdrawing the conditioning claim outright.** State what
   it means: `frac_iface_on_epitope = 0.712` measures where RFdiffusion puts antibodies on
   PD-1, not where we told it to. The 18/18 patch-null result is then *true and irrelevant* —
   it shows the interface is non-randomly placed, which the prior already explains.
3. Work the tiers above **top-down**, and for the shipped file fix
   `scripts/57_build_submission.py` and **rebuild**, then re-run `scripts/58` to confirm the
   package still validates from its own files.
4. Course: index under a new `CORRECTIONS.md` **C7**, add it to the banner line (C1–C7), do
   not rewrite chapters. `05-experiment-design.md` carries 14 occurrences and is the heaviest.
5. Re-run the markup-tolerant sweep afterwards and require **0 unqualified**, the same bar
   the C9 pass used.
6. `STATE.md` §1 headline and §4 "taken on trust" both change. Challenge 2's composite
   (93.6) does **not** change — it never depended on conditioning — and saying so explicitly
   prevents the correction being read as wider than it is.

## ROW 4 — ambiguous (both above the bar)

Not pre-registered; it exists because the world has four outcomes and the pre-registration
had three. Consistent with docks straddling the **4.9 Å** shared edge between the patches.
Report as ambiguous, flag in **D**, and do not pick the flattering half. The follow-up is a
decoy with a larger separation, accepting a worse size or spread match, and saying which
was traded.

---

## Applies to every row

- Record the row **before** interpreting it, in the write-up as well as in the commit.
- `n` is reported with every mean. A mean without its denominator is how a glob matching
  1 of 18 files looked like a working analysis earlier today.
- The session doc gains a section; `LEARNINGS.md` is at its 40-bullet cap, so anything
  promoted there must displace something — do not quietly go to 41.
- Session docs from previous days are **not** edited. They record what was believed then.
