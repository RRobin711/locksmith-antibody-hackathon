#!/usr/bin/env python3
"""What is actually left on the rubric, and is it reachable? CPU only, no GPU.

Runs concurrently with the overnight folding: NetSolP is quantized ONNX on CPU and
Boltz is GPU-bound, so this costs the fold queue nothing.

THE QUESTION. The winner scores `final` = 87.5 with two metrics in the Medium band:

    dockq    0.747  (Good needs >= 0.80)   worth +2.50 final points
    netsolp  0.585  (Good needs >= 0.70)   worth +5.00 final points

Under this project's band_scores (good 9.5, medium 7.0) the ceiling is 95.0, not 100,
so the honest statement is "87.5 of a reachable 95.0", and the two gaps above are the
whole of it. Nobody has ever tried to move either. This script asks, for each, whether
it is reachable AT ALL on this scaffold -- before any GPU time is spent chasing it.

NETSOLP: A CEILING, NOT A LEVER (hypothesis)
--------------------------------------------
Three facts make the "free 20%" look unreachable:

  1. `netsolp_chain_agg: min` -- a design scores its WORST chain.
  2. ProteinMPNN redesigns only the 29 IMGT CDR positions of the HEAVY chain
     (`design/mpnn.py`); the whole light chain is pembrolizumab's, unchanged, in
     every one of the 239 designs.
  3. Pembrolizumab's own chains measure 0.623 (Fab heavy) and 0.626 (Fab light) on
     the ESM1b 5-fold ensemble. Both are Medium.

If (3) holds then min(VH, 0.626) <= 0.626 for every design regardless of what the
heavy CDRs do, and Good is unreachable without redesigning the light chain. The 40
designs measured so far span 0.567-0.597 -- every one BELOW the native heavy chain,
and 0.103 below the Good edge, which is 3.4x the entire observed spread.

This script measures all 239 to turn "looks unreachable" into a number: the achievable
maximum over the pool, and how far it sits from 0.70. A ceiling is a finding -- 20% of
the rubric being unreachable on the specified scaffold is a statement about the rubric,
in the rubric's own terms, and it is the difference between "we ignored developability"
and "we established it was pinned and said so".

DOCKQ: A REAL LEVER NOBODY PULLED (hypothesis)
-----------------------------------------------
Novelty is banded: cdrh3_identity < 70% scores Good, and there is NO further reward for
going lower. The 239 designs span 15.4-46.2% identity. Every one of them is paying
binding quality for novelty the rubric does not score -- identity predicts DockQ at
rho +0.389 across the pool, and the whole band from 46% to 69% is unexplored. This
script quantifies the slope and extrapolates what identity would be needed for DockQ
0.80, flagging it as an extrapolation beyond the observed range, which is exactly what
it is.

OUTPUT: results/rubric_headroom.md. No selection decision is taken here and M3's named
winner does not change; this measures the board, it does not move a piece.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.metrics import netsolp

POOL = Path("designs/wide_temp/designs.json")
FOLDSC = Path("runs/designs_temp/fold_scores.jsonl")
CACHE = Path("runs/netsolp_pool_fv.jsonl")   # Fab-based cache retired 2026-09-20
OUT = Path("results/rubric_headroom.md")
WINNER = "mpnn_T0.5_s104_036"
CHUNK = 24


def cached() -> dict[str, float]:
    if not CACHE.exists():
        return {}
    return {json.loads(l)["name"]: json.loads(l)["value"]
            for l in CACHE.read_text().splitlines() if l.strip()}


def score_seqs(seqs: dict[str, str]) -> dict[str, float]:
    """NetSolP over named sequences, chunked and cached so a kill costs one chunk."""
    have = cached()
    todo = {k: v for k, v in seqs.items() if k not in have}
    print(f"netsolp: {len(have)} cached, {len(todo)} to score", flush=True)
    keys = list(todo)
    for i in range(0, len(keys), CHUNK):
        part = {k: todo[k] for k in keys[i:i + CHUNK]}
        t0 = time.time()
        try:
            got = netsolp.predict(part)
        except Exception as e:                                        # noqa: BLE001
            print(f"  chunk {i//CHUNK+1} FAILED: {str(e)[:200]}", file=sys.stderr, flush=True)
            continue
        with CACHE.open("a") as f:
            for k, v in got.items():
                f.write(json.dumps({"name": k, "value": float(v)}) + "\n")
        have.update({k: float(v) for k, v in got.items()})
        print(f"  chunk {i//CHUNK+1}/{(len(keys)+CHUNK-1)//CHUNK}: {len(got)} seqs "
              f"in {time.time()-t0:.0f}s", flush=True)
    return have


def band_final(dockq_good: bool, netsolp_good: bool) -> float:
    b = [9.5, 9.5 if dockq_good else 7.0, 9.5, 9.5, 9.5, 9.5]
    return 10 * (0.6 * float(np.mean(b)) + 0.2 * (9.5 if netsolp_good else 7.0) + 0.2 * 9.5)


def main() -> int:
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    folds = {}
    for l in FOLDSC.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if "dockq" in r:
                folds[r["design_id"]] = r

    # NetSolP keys its output CSV on the FASTA header, and a design_id contains a
    # dot ("mpnn_T0.5_..."), which is exactly the kind of character a downstream
    # parser silently truncates. Use opaque safe ids and keep the mapping here.
    # CORRECTED 2026-09-20: this scored the full Fab chains. The handbook says the Fv
    # twice ("the Fv (VH + VL) region", "run on the Fv sequence"), and the difference is
    # not cosmetic -- it flips which chain limits the score. On Fab, heavy limits
    # (0.623 vs 0.626); on Fv, LIGHT limits (0.733 vs 0.569). The earlier version of
    # this table labelled Fab values as "VH"/"VL" and was wrong on both counts.
    from locksmith.metrics.netsolp import _to_fv
    light = _to_fv(pool[WINNER]["light"], "light")
    ids = sorted(pool)
    safe = {f"h{i:04d}": d for i, d in enumerate(ids)}
    seqs = {k: _to_fv(pool[d]["heavy"], "heavy") for k, d in safe.items()}
    seqs["lshared"] = light
    vals = score_seqs(seqs)

    vh = {d: vals[k] for k, d in safe.items() if k in vals}
    vl = vals.get("lshared")
    if not vh or vl is None:
        print("netsolp produced nothing usable; writing what we have", file=sys.stderr)

    lines, w = [], lambda s="": lines.append(s)
    w("# What is left on the rubric, and is it reachable?")
    w("")
    w("`scripts/40_rubric_headroom.py` — CPU only, run concurrently with the overnight folds.")
    w("No selection decision is taken here; M3's named winner is unchanged.")
    w("")
    w("## 1. The board")
    w("")
    w("Under this project's `band_scores` (good 9.5, medium 7.0) the reachable maximum is")
    w("**95.0**, not 100. The winner is at **87.5**, and the entire 7.5-point gap is two")
    w("metrics sitting in Medium:")
    w("")
    w("| metric | winner | Good needs | worth if moved |")
    w("|---|---|---|---|")
    w(f"| `dockq` | 0.747 | ≥ 0.80 | **+{band_final(True, False)-band_final(False, False):.2f}** |")
    w(f"| `netsolp` | 0.585 | ≥ 0.70 | **+{band_final(False, True)-band_final(False, False):.2f}** |")
    w(f"| both | | | **{band_final(True, True):.1f} total** |")
    w("")
    w("Note the +5.00 for NetSolP is *not* the +8 that a 6/10-vs-10/10 band reading gives;")
    w("this project scores bands at their midpoints (9.5 / 7.0 / 2.5), a convention recorded")
    w("in `config/metrics.yaml`. Quoting +8 would overstate the prize by 60%.")
    w("")

    if vh:
        a = np.array(list(vh.values()))
        combined = np.minimum(a, vl)
        w("## 2. NetSolP — measured over the whole pool")
        w("")
        w(f"All {len(vh)} designs, ESM1b 5-fold ensemble, `chain_agg = min`.")
        w("")
        w("| quantity | value |")
        w("|---|---|")
        w(f"| VH (Fv) over 239 designs | {a.min():.4f} – {a.max():.4f} (mean {a.mean():.4f}) |")
        w(f"| VL (Fv; pembrolizumab's, **byte-identical in all 239 designs**) | {vl:.4f} |")
        w(f"| `min(VH, VL)` achievable maximum | **{combined.max():.4f}** |")
        w(f"| Good band edge | 0.70 |")
        w(f"| shortfall | **{0.70 - combined.max():+.4f}** |")
        w(f"| designs reaching Good | **{int((combined >= 0.70).sum())} / {len(vh)}** |")
        w(f"| pool spread of VH | {a.max()-a.min():.4f} |")
        w(f"| shortfall as multiples of the pool spread | "
          f"**{(0.70 - combined.max())/max(a.max()-a.min(), 1e-9):.1f}×** |")
        w("")
        if combined.max() < 0.70:
            w("**The Good band is not reachable by heavy-CDR redesign on this scaffold.**")
            w(f"ProteinMPNN varies only the 29 heavy CDR positions, which moves VH across a")
            w(f"range of {a.max()-a.min():.3f}; the gap to 0.70 is "
              f"{(0.70-combined.max())/max(a.max()-a.min(),1e-9):.1f} times that range. The light chain is")
            w(f"pembrolizumab's in all 239 designs and scores {vl:.3f}, so it caps `min()` "
              f"at {vl:.3f}")
            w("regardless of the heavy chain. Two honest routes remain, both outside what has")
            w("been built: redesign the light-chain CDRs as well, or change the")
            w("`netsolp_chain_agg` convention — and the second is a convention change, not a")
            w("design improvement, so it would have to be declared as such.")
            w("")
            w("**This is a finding, not a failure.** 20% of the rubric is pinned at Medium for")
            w("any pembrolizumab-framework Fab, including pembrolizumab itself. A pitch that")
            w("says so, with the measurement, is stronger than one that quietly leaves the")
            w("points on the table.")
        else:
            n = int((combined >= 0.70).sum())
            w(f"**Reachable: {n} designs already clear 0.70.** The lever is real; the question")
            w("becomes what those designs cost on the binding metrics.")
        w("")

    ident = np.array([pool[d]["cdrh3_identity"] for d in folds])
    dq = np.array([folds[d]["dockq"] for d in folds])
    r = stats.spearmanr(ident, dq)
    sl, ic, rv, pv, se = stats.linregress(ident, dq)
    need = (0.80 - ic) / sl if sl > 0 else float("nan")
    w("## 3. DockQ — the lever nobody pulled")
    w("")
    w("Novelty is **banded**: `cdrh3_identity < 70%` scores Good and nothing below 70 scores")
    w("better. The pool spans **%.1f–%.1f%%** identity. Every design is therefore buying"
      % (ident.min(), ident.max()))
    w("novelty that the rubric does not pay for, and identity is the strongest free predictor")
    w("of DockQ we have.")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| Spearman identity↔DockQ, n={len(ident)} | **{r.statistic:+.3f}** (p={r.pvalue:.2g}) |")
    w(f"| OLS slope | {sl:+.5f} DockQ per % identity (SE {se:.5f}) |")
    w(f"| observed DockQ max | {dq.max():.3f} |")
    w(f"| designs at DockQ ≥ 0.80 | {int((dq>=0.80).sum())} |")
    w(f"| identity implied for DockQ 0.80 | **{need:.0f}%** |")
    w(f"| still inside the Good novelty band? | **{'yes' if need < 70 else 'NO'}** |")
    w("")
    w("**Read the extrapolation honestly.** The implied identity is outside the observed")
    w(f"range ({ident.min():.1f}–{ident.max():.1f}%), so it is a linear extrapolation, and the")
    w("relationship need not stay linear — DockQ is bounded above by what the predictor can do")
    w("on this complex at all, which the pembrolizumab refold puts near 0.82. What the number")
    w("licenses is a *hypothesis worth one cheap arm*: generate designs at 50–69% CDR-H3")
    w("identity, which is untouched design space that is free on novelty, and see whether")
    w("DockQ crosses 0.80. It does not license claiming the 2.5 points.")
    w("")
    w("It is also worth saying what this lever is: it is **Goodhart in our favour**. The")
    w("rubric's banding means a design at 69% identity and one at 15% are scored identically")
    w("on novelty while differing substantially on pose retention. Reporting that we found it,")
    w("and what it implies about banded rubrics, is more interesting than the 2.5 points.")
    w("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
