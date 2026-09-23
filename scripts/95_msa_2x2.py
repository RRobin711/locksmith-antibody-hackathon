#!/usr/bin/env python3
"""Completes the 2x2: {baseline, S->A} x {antigen MSA present, absent}.

WHY. `scripts/94` found that the shipped Challenge 2 design scores ipSAE 0.686 when the
antigen alignment is absent (the condition it was actually folded under, because Boltz
silently discarded a length-mismatched MSA) and **0.012 when the alignment is present**.
That inverts the expected direction: the design does not merely survive the missing MSA,
its viability appears to DEPEND on it.

Two cells are missing before that can be believed. The r10 run scored the pre-fix baseline
at ipSAE 0.864 on the 113-mer with the cached alignment, which would complete the picture
-- but it is a different run, a different script, and was not folded beside these. Reusing
it would mean comparing across invocations when the whole point is to compare within one.

So both baseline cells are folded here, under the identical driver, seed, sampling depth
and flags as the two S->A cells already measured:

           |  antigen MSA PRESENT        |  antigen MSA ABSENT
  ---------+-----------------------------+---------------------------
  baseline |  base_msa   (113 + cached)  |  base_nomsa (123 + cached->discarded)
  S->A     |  matched_113  [= 0.012]     |  as_shipped   [= 0.686]

READING IT, fixed before the folds:
  * If `base_msa` is high (~0.8) and `base_nomsa` is also high, then the MSA is not what
    carries the baseline, and S->A specifically requires its absence -- meaning the
    sequon fix is far more damaging than the 4.8 points recorded, and was rescued only by
    an accident.
  * If BOTH baseline cells collapse with the MSA present, the effect is not about S->A at
    all: an antigen alignment suppresses this whole de novo interface, and every viable
    number this project has for Challenge 2 came from folds without one.
  * If `base_msa` is high and `base_nomsa` is low, the direction reverses again and the
    no-MSA condition is what flatters S->A only.

Any of the three is a substantial finding. The one outcome that would make the earlier
work safe -- all four cells agreeing -- is already excluded by the two measured cells.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold, PD1_MSA

OUT = Path("runs/msa_2x2")
RECYCLING = 10
SAMPLES = 5
CORE113 = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRD"
           "FHMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    designs = json.loads(Path("runs/challenge2_fold_r10/designs.json").read_text())
    win = [x for x in designs if x["design_id"] == "bb_2_0_dldesign_1"][0]
    heavy, light = win["heavy"], win["light"]          # the PRE-FIX baseline sequences
    ag123 = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    assert "S" == heavy[53], f"expected S at heavy[53], found {heavy[53]!r} -- this is " \
                             f"supposed to be the UNFIXED sequence"
    print(f"baseline heavy {len(heavy)} light {len(light)}; "
          f"113-mer and {len(ag123)}-mer antigens\n", flush=True)

    arms = [
        ("base_msa",   CORE113, PD1_MSA, False, "baseline + 113-mer + cached MSA (USED)"),
        ("base_nomsa", ag123,   PD1_MSA, True,  "baseline + 123-mer + cached MSA (DISCARDED)"),
    ]
    log = {}
    for label, antigen, msa, allow, what in arms:
        d = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(d, label, n_models=SAMPLES):
            print(f"{label:<12} already folded", flush=True)
            continue
        print(f"{label:<12} {what} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, heavy, light, antigen, out_root=OUT, antigen_msa=msa, seed=1,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400,
                 allow_msa_mismatch=allow)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300]}
            print(f"FAILED: {str(e)[:180]}", flush=True)
        (OUT / "fold_log.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
