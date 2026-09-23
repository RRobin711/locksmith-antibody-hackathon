#!/usr/bin/env python3
"""Three §9.2 fix arms for bb_1_0_dldesign_0, chosen from contacts rather than handbook order.

THE CONTACT TABLE THAT CHOSE THE SUBSTITUTIONS (median over 5 diffusion samples,
heavy-atom <=4.5 A to PD-1):

    L91 ASN  glycosylation acceptor        0     <- free
    L92 LYS  X of N-X-S                   13
    L93 SER  sequon third position        19     <- most contacted residue in either motif
    L31 ASN  deamidation acceptor         13
    L32 GLY  n+1, sets the deamidation rate 4    <- cheaper than the acceptor

`fix91` = **N91Q**. On the PREVIOUS Challenge 2 design the Asn carried 10 and 19 contacts
and the Ser carried zero, so `S->A` was the correct fix and `N->Q` collapsed ipSAE
0.864 -> 0.014. Here the roles are exactly reversed. Same rule, opposite answer -- which is
the whole content of the rule. `N->Q` also eliminates the glycosylation acceptor outright
rather than removing the motif's third position.

`fix31` = **G32A**, not N31Q. Deamidation happens AT the Asn but its RATE is set by the
n+1 residue; glycine is the fastest because it most readily permits the succinimide
intermediate. `G->A` therefore clears the `NG` motif at 4 contacts instead of 13. Stated
plainly: this SLOWS the chemistry where `N->Q` would eliminate the acceptor, and glycine
lacks a C-beta so removing it can change loop conformation -- on Challenge 1 `G56A` cost 2
composite points and DOUBLED the diffusion spread (0.089 vs 0.044).

`fix31` would never be shipped on its own -- 91 would still fail 9.2 -- but it is folded
because `fix_both` alone cannot say WHICH mutation caused any damage.

Everything else is identical to the re-screen: `pd1_123_handbook.csv`, recycling 10,
5 diffusion samples, seed 1, same driver. The unfixed design stays on disk as the fallback,
so no arm here can cost anything.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.metrics import liabilities
from locksmith.fold.boltz import fold

OUT = Path("runs/liability_fix")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
RECYCLING, SAMPLES, SEED = 10, 5, 1


def mutate(seq: str, pos1: int, frm: str, to: str) -> str:
    assert seq[pos1 - 1] == frm, f"expected {frm} at {pos1}, found {seq[pos1-1]}"
    return seq[:pos1 - 1] + to + seq[pos1:]


def main() -> int:
    D = {x["design_id"]: x for x in json.loads(
        Path("runs/challenge2_fold_r10/designs.json").read_text())}
    d = D["bb_1_0_dldesign_0"]
    heavy, light = d["heavy"], d["light"]
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]

    l91 = mutate(light, 91, "N", "Q")                  # glycosylation acceptor, 0 contacts
    l32 = mutate(light, 32, "G", "A")                  # deamidation n+1, 4 contacts
    both = mutate(mutate(light, 91, "N", "Q"), 32, "G", "A")

    arms = [("fix91", heavy, l91, "N91Q"),
            ("fix31", heavy, l32, "G32A"),
            ("fix_both", heavy, both, "N91Q + G32A")]

    print("§9.2 scan per arm (sequence-only, before any fold):", flush=True)
    for label, h, l, what in [("unfixed", heavy, light, "-")] + arms:
        rep = liabilities.compute(h, l)
        ok, fails = rep.handbook_9_2_pass()
        highs = [x for x in rep.liabilities if getattr(x, "severity", "") == "HIGH"]
        print(f"  {label:<10} {what:<14} §9.2 pass={ok!s:<6} HIGH liabilities={len(highs)}"
              + ("  " + "; ".join(f"{x.kind} {x.motif} {x.chain}{x.position}"
                                  for x in highs) if highs else ""), flush=True)
    print(flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    for label, h, l, what in arms:
        pred = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(pred, label, n_models=SAMPLES):
            print(f"{label:<10} already folded", flush=True)
            continue
        print(f"{label:<10} {what:<14} ...", end=" ", flush=True)
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
