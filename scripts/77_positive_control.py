#!/usr/bin/env python3
"""Positive control for the Challenge 2 fold configuration.

Folds WILD-TYPE pembrolizumab + PD-1 through the EXACT call used by
`scripts/72_challenge2_fold.py`, in two arms:

    A  Fab (219 + 217 + 123)   -- isolates the pipeline: MSA, antigen, settings
    B  Fv  (119 + 111 + 123)   -- isolates the construct, matching the designs' 119/107

This is a cognate, crystallographically-solved, pre-cutoff pair (5GGS). Boltz-2 has
memorised it. If it cannot place this complex confidently, the `0/30` Challenge 2 result
says nothing about the designs.

Predictions and the decision rule are fixed in
`results/prereg_2026-09-22_positive_control.md`, written before this ran.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.metrics import ipsae
from locksmith.types import Provenance, Structure

SRC = Path("/tmp/poscontrol.json")
OUT = Path("runs/challenge2_poscontrol")
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")


def main() -> int:
    cfg = load()
    c = cfg.conventions
    d = json.loads(SRC.read_text())

    arms = [
        ("posctrl_fab", d["fab_heavy"], d["fab_light"], "A - Fab, isolates the pipeline"),
        ("posctrl_fv", d["fv_heavy"], d["fv_light"], "B - Fv, isolates the construct"),
    ]
    results = {}
    for label, heavy, light, what in arms:
        print(f"\n=== {label}: {what} ===", flush=True)
        print(f"    heavy {len(heavy)}  light {len(light)}  antigen {len(d['antigen'])}",
              flush=True)
        try:
            res = drv.fold(label, heavy, light, d["antigen"], out_root=OUT,
                           construct="fab" if "fab" in label else "fv",
                           seed=1, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            print(f"    FAILED: {e}", file=sys.stderr, flush=True)
            results[label] = None
            continue
        st = Structure(pdb=res.pdb, provenance=Provenance.PREDICTION, pae=res.pae,
                       label=label)
        out = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                            dist_cutoff=c["ipsae_dist_cutoff"])
        v = out["ipsae"].value
        results[label] = v
        print(f"    ipSAE = {v}   ({out['ipsae'].detail})", flush=True)
        print(f"    {res.n_residues} residues, {res.seconds:.0f}s", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(results, indent=1))

    a, b = results.get("posctrl_fab"), results.get("posctrl_fv")
    print("\n" + "=" * 62)
    print(f"ARM A  Fab : ipSAE {a}   (predicted >= 0.75)")
    print(f"ARM B  Fv  : ipSAE {b}   (predicted >= 0.60)")
    print("=" * 62)
    if a is None or b is None:
        print("VERDICT: a fold failed; nothing can be concluded.")
        return 1
    if b >= 0.60:
        print("VERDICT: the Fv construct is sound. 0/30 is a real property of the "
              "designs and Challenge 2's end state STANDS.")
        if a - b > 0.15:
            print(f"         NOTE: the construct still costs {a-b:.3f} ipSAE; report "
                  f"0/30 WITH that penalty quantified.")
    elif a >= 0.75:
        print("VERDICT: THE CONSTRUCT IS THE CONFOUND. 0/30 is NOT interpretable as a "
              "statement about the designs. Withdraw the Challenge 2 result and rewrite "
              "STATE.md.")
    else:
        print("VERDICT: the shared configuration is broken. Both the control and 0/30 "
              "are uninterpretable; debug before any claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
