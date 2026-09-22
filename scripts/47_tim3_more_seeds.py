#!/usr/bin/env python3
"""Settle the TIM-3 comparison. 3 vs 3 cannot do it; this adds 5 seeds each side.

WHY. The reference panel gave our design 0.624/0.612/0.469 against TIM-3 and
pembrolizumab 0.322/0.189/0.458. The ranges do not overlap, which looks decisive and
is not: with 3 observations per group the SMALLEST two-sided Mann-Whitney p that can
be attained is exactly 0.100, and that is what we got. The result is therefore at the
ceiling of what the design could show -- suggestive, not established -- and the earlier
write-up stated it more strongly than the arithmetic supports.

Pembrolizumab's spread is also the problem: 0.189 to 0.458 across three seeds, a range
of 0.269, which is an order of magnitude wider than the ~0.02 single-seed ipSAE sd seen
on the PD-1 complex. Against a non-cognate antigen the predictor is far less stable, so
the mean is poorly determined at n=3 either way.

Five more seeds each (54-58) takes both groups to n=8. At n=8 vs 8 the attainable
two-sided p floor is 1.6e-4, so the test can actually reject. Both antibodies are folded
in the SAME script against the SAME cached TIM-3 MSA with the same construct, so the
comparison stays like-for-like; the seeds are fresh and shared across both arms.

This is a power fix to an existing comparison, not a new hypothesis. The pre-registered
specificity thresholds are unchanged; what changes is whether we can speak to them.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.io.pdb import seq_for_folding

OUT = Path("runs/specificity_ref")
INDEX = OUT / "index.jsonl"
TIM3_MSA = Path("data/msa_cache/v2/8tbb_antigen.csv")
MANIFEST = Path("data/refs/postcutoff/prepared/manifest_seqres.json")
PARENT = Path("data/refs/prepared/5ggs_ABZ.pdb")
POOL = Path("designs/wide_temp/designs.json")
WINNER = "mpnn_T0.5_s104_036"
SEEDS = (54, 55, 56, 57, 58)


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    man = json.loads(MANIFEST.read_text())["8TBB"]
    tim3 = man["antigen"]
    w = {d["design_id"]: d for d in json.loads(POOL.read_text())}[WINNER]
    panel = [
        ("ours", "the named design (was: spec_tim3 seeds 31-33)", w["heavy"], w["light"]),
        ("pembro", "pembrolizumab (negative reference)",
         seq_for_folding(PARENT, "A"), seq_for_folding(PARENT, "B")),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    have = done()
    t0, ok, bad = time.time(), 0, 0
    for key, desc, heavy, light in panel:
        for seed in SEEDS:
            label = f"ref_{key}_tim3__s{seed}"
            if label in have:
                print(f"skip {label}", flush=True); continue
            try:
                r = drv.fold(label, heavy, light, tim3, out_root=OUT,
                             construct="fab", seed=seed, antigen_msa=TIM3_MSA)
            except FoldFailed as e:
                bad += 1
                print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
                rec = {"label": label, "antibody": key, "desc": desc, "seed": seed,
                       "ok": False, "error": str(e)[:400]}
            else:
                ok += 1
                print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
                rec = {"label": label, "antibody": key, "desc": desc, "seed": seed,
                       "ok": True, "pdb": str(r.pdb), "pae": str(r.pae),
                       "plddt": str(r.plddt), "seconds": r.seconds}
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"\ntim3 extra seeds: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
