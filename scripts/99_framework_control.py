#!/usr/bin/env python3
"""The control that decides whether `fix91`'s collapse is residue-specific or margin.

THE QUESTION. `fix91` mutated light 91 -- a residue with ZERO antigen contacts in all five
diffusion samples -- and the design collapsed 0.637 -> 0.128, 3/5 viable -> 0/5. Two
explanations fit and the data in hand does not separate them:

  (a) RESIDUE-SPECIFIC. Light 91 is load-bearing in a way contacts do not capture, so the
      contact rule is refuted as a predictor.
  (b) MARGIN. A design sitting 0.037 above the viability cutoff cannot absorb ANY
      single-residue change, so the contact rule is untested here rather than refuted.

(b) is supported by all three arms landing in the same place (0.128 / 0.140 / 0.034)
rather than the double mutant being twice as bad, which is what independent per-residue
damage would look like.

THE CONTROL. Mutate a residue that (a) predicts nothing about and (b) predicts will kill:
**the same substitution, the same zero contact count, in FRAMEWORK instead of a CDR.**

  heavy N77Q   framework, contacts [0,0,0,0,0]
  heavy N84Q   framework, contacts [0,0,0,0,0]

Both are N->Q, exactly as `fix91` was, so substitution chemistry is held fixed and the only
variable is where it sits. Two arms rather than one because a single control on which a
refutation turns is too thin; if they disagree, that is itself informative.

(Both are also MODERATE deamidation motifs -- `NT` at 77, `NS` at 84 -- so each arm removes
a real liability as a side effect. That is incidental to the control.)

READING IT, fixed before folding:
  * Both survive (>=3/5 viable, median near 0.637) -> the design CAN absorb a zero-contact
    N->Q. `fix91`'s collapse is then residue-specific, explanation (a), and the contact
    rule is refuted as a predictor.
  * Both collapse -> ANY single-residue change kills this design. Explanation (b), and the
    contact rule is UNTESTED here. Nothing about it should be written as refuted.
  * They disagree -> position matters in a way neither explanation captures; report as
    open and do not generalise from n=2.
"""
from __future__ import annotations

import json, time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold

OUT = Path("runs/framework_control")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
RECYCLING, SAMPLES, SEED = 10, 5, 1


def mutate(seq: str, pos1: int, frm: str, to: str) -> str:
    assert seq[pos1 - 1] == frm, f"expected {frm} at {pos1}, found {seq[pos1-1]}"
    return seq[:pos1 - 1] + to + seq[pos1:]


def main() -> int:
    D = {x["design_id"]: x for x in json.loads(
        Path("runs/challenge2_fold_r10/designs.json").read_text())}
    d = D["bb_1_0_dldesign_0"]
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]

    arms = [("ctrl_N77Q", mutate(d["heavy"], 77, "N", "Q"), d["light"], "heavy N77Q"),
            ("ctrl_N84Q", mutate(d["heavy"], 84, "N", "Q"), d["light"], "heavy N84Q")]

    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    for label, h, l, what in arms:
        pred = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(pred, label, n_models=SAMPLES):
            print(f"{label:<12} already folded", flush=True)
            continue
        print(f"{label:<12} {what:<14} (framework, 0 contacts) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, h, l, ag, out_root=OUT, antigen_msa=MSA, seed=SEED,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1), "change": what}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                                   # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300], "change": what}
            print(f"FAILED: {str(e)[:170]}", flush=True)
        (OUT / "fold_log.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
