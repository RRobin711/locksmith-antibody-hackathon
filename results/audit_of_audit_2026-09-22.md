# Auditing tonight's own work

**2026-09-22.** Every headline number in `results/audit_response_2026-09-22.md` re-derived
from the files by `scripts/76_audit_tonight.py`, plus a check that
`scripts/70_epitope_patch_null.py` does what its docstring claims.

## Result

```
PASS 46   FAIL 0   UNVERIFIABLE 0
```

Machine-readable: `results/audit_of_audit_2026-09-22.json`.

Covered: the DockQ refusal and its reproduction (0.816, A–C 0.723, A–B 0.931), the
checksum pass, the conditioning statistics (0.7119 / 0.5005 / d=1.4747 / CI
[0.733, 2.216]), the whole B0 winner-change analysis, the patch null, the four RF2 ICCs
and the detectable floor, the B3 filter result, and every sequence claim (15 subs, 93.5%,
CDR-H2 by one, charge +2 vs 0, aromatics 2 vs 4, VH 0.699 / VL 0.569).

## Three things the audit found

**1. One figure in the audit response was imprecise and is corrected.** Shortlist
single-seed reliability was written as **0.28**; recomputed under the `top` convention it
is **0.296**. 0.28 is the value under `midpoint`, quoted in a `top` context — the same
convention-mixing error the document was reporting elsewhere, made while reporting it.
Corrected in place.

**2. The audit script itself carried the night's characteristic bug.** Its summary tested
`ok is True`, but numpy comparisons return `np.bool_`, and `np.True_ is True` is `False`.
So seven genuine passes were printed as PASS and simultaneously listed as UNVERIFIABLE,
and `json.dumps` refused to serialise them. **The script that exists to catch "the newest
claim carries the error" carried the error on its first run.** Fixed by coercing with
`bool()`; the comment at `check()` records why.

**3. A limitation of the patch null, found by checking the docstring against behaviour.**
The contiguous surface patches are **more compact than the real epitope**: mean RMS spread
**7.73 Å** for a drawn patch against **10.08 Å** for the PD-L1 footprint itself (uniform
draws: 13.21 Å). So the null objects are the right *family* — clearly compact rather than
scattered — but they are not size-and-shape matched to the epitope. A more compact patch
covers a smaller area of surface, which plausibly makes it *easier* to miss a spread-out
interface and therefore makes the test **anti-conservative** by an unquantified amount.

This does not overturn the result — 17/18 backbones beat their null and the effect is
large (0.712 vs 0.154) — but the honest statement of the null is *"a compact 26-residue
patch elsewhere on the same chain"*, not *"an epitope-like patch elsewhere"*. Matching the
null's spread to the real epitope's is a straightforward improvement and has not been done.

## What this does not cover

The Challenge 2 gate results (produced after this audit ran), the deck, and anything in
`PLAN.md` older than 2026-09-21. It audits last night's corrections, not the whole project.
