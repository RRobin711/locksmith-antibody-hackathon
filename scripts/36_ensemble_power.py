#!/usr/bin/env python3
"""How many seeds does a CDR-H3 SPREAD estimate need? (zero new folds)

M3 established that for estimating a design's MEAN score, depth is cheap and
three seeds is the worst allocation: the noise of a k-seed mean falls as
1/sqrt(k), so folds are better spent on more seeds than more designs only up to
a point.  **Spread is a different quantity and obeys a different law.**  The
relative sampling error of a standard-deviation-like statistic from k draws is
~1/sqrt(2(k-1)) -- 50% at k=3, 35% at k=5, 29% at k=7 -- so a spread estimate is
far more seed-hungry than a mean.  Tonight's ensemble run is a correlation
against spread, so its attenuation is governed by that law, not by the M3 one.

This script measures the law on real data instead of assuming it, using the 20
designs x 7 seeds already on disk (M3 shortlist).  It reports, for each k:

    reliability_k = var_between_designs(true spread)
                    / (var_between_designs + E[sampling var of a k-seed spread])

and the attenuation sqrt(reliability_k) that any correlation against a k-seed
spread suffers.  Then it optimises (n designs, k seeds) at a fixed fold budget.

ESTIMATOR NOTE -- this is a deliberate change from 23_ensemble_cdrh3.py.
That script measured every seed against seed[0], so the number depended on which
seed happened to be first and inflated by ~sqrt(2) relative to spread about the
ensemble centre.  Here the estimator is the ROOT MEAN SQUARE DEVIATION OVER ALL
C(k,2) SEED PAIRS, which is reference-free and uses every pair.  Values are
therefore not directly comparable to the 0.33-1.45 A quoted on 2026-09-18.

CAVEAT the output must carry: the 20 designs here are the M3 shortlist, i.e. the
top of a 239 pool.  Range restriction inflates nothing about the WITHIN-design
sampling variance (that is what we use) but the BETWEEN-design variance of the
spread is measured on a selected set, so reliability computed here is a
LOWER bound if the full pool spreads wider on this axis, and an upper bound if
selection happened to pick unusually heterogeneous designs.
"""
from __future__ import annotations
import itertools, json, sys
from collections import defaultdict
from pathlib import Path

import gemmi
import numpy as np

CDRH3 = range(95, 108)                      # 0-based, heavy chain, 13 residues
OUT = Path("results/ensemble_power.md")


def ca_of_chain(pdb: Path, chain="A"):
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    ch = [c for c in st[0] if c.name == chain][0]
    ca, b = [], []
    for r in ch:
        a = r.find_atom("CA", "*")
        if a:
            ca.append([a.pos.x, a.pos.y, a.pos.z]); b.append(a.b_iso)
    return np.array(ca), np.array(b)


def superpose_on_framework(ref_ca, mob_ca, loop_idx):
    mask = np.array([i not in set(loop_idx) for i in range(len(ref_ca))])
    P, Q = ref_ca[mask], mob_ca[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return (mob_ca - Q.mean(0)) @ R + P.mean(0)


def pair_dev(ca_a, ca_b, loop):
    """RMS CA deviation over the loop, after superposing b onto a on framework."""
    n = min(len(ca_a), len(ca_b))
    moved = superpose_on_framework(ca_a[:n], ca_b[:n], loop)
    d = np.sqrt(((moved[loop] - ca_a[loop]) ** 2).sum(1))
    return float(np.sqrt((d ** 2).mean()))


def main() -> int:
    paths = defaultdict(dict)
    for line in open("runs/designs_reseed7/index.jsonl"):
        r = json.loads(line)
        if r["ok"]:
            paths[r["design_id"]][r["seed"]] = Path(r["pdb"])
    for line in open("runs/designs_temp/index.jsonl"):
        r = json.loads(line)
        if r.get("ok") and r["design_id"] in paths:
            paths[r["design_id"]][1] = Path(r["pdb"])

    designs = sorted(d for d in paths if len(paths[d]) >= 7)
    print(f"{len(designs)} designs with >=7 seeds", file=sys.stderr)

    # pairwise deviation matrix per design
    pw, plddt_loop, plddt_iface = {}, {}, {}
    for d in designs:
        seeds = sorted(paths[d])[:7]
        cas = {}
        for s in seeds:
            ca, b = ca_of_chain(paths[d][s])
            cas[s] = ca
            plddt_loop.setdefault(d, []).append(
                float(np.mean([b[i] for i in CDRH3 if i < len(b)])))
        loop = [i for i in CDRH3 if i < len(cas[seeds[0]])]
        m = {}
        for a, b_ in itertools.combinations(seeds, 2):
            m[(a, b_)] = pair_dev(cas[a], cas[b_], loop)
        pw[d] = (seeds, m)
        print(f"  {d}: {len(m)} pairs, rms {np.sqrt(np.mean([v**2 for v in m.values()])):.3f} A",
              file=sys.stderr)

    def spread(d, subset):
        seeds, m = pw[d]
        vals = [m[(a, b)] for a, b in itertools.combinations(sorted(subset), 2)]
        return float(np.sqrt(np.mean([v ** 2 for v in vals])))

    truth = {d: spread(d, sorted(pw[d][0])) for d in designs}
    var_between = float(np.var(list(truth.values()), ddof=1))

    rows = []
    for k in (2, 3, 4, 5, 6, 7):
        within = []
        for d in designs:
            seeds = pw[d][0]
            est = [spread(d, c) for c in itertools.combinations(seeds, k)]
            within.append(np.var(est, ddof=1) if len(est) > 1 else 0.0)
        v_within = float(np.mean(within))
        rel = var_between / (var_between + v_within) if var_between > 0 else float("nan")
        rows.append((k, v_within, rel, np.sqrt(max(rel, 0.0))))

    lines = []
    w = lines.append
    w("# How many seeds does a CDR-H3 spread estimate need?")
    w("")
    w("`scripts/36_ensemble_power.py` — **zero new folds**; computed from the 20 M3-shortlist")
    w("designs already folded at 7 seeds each. Run before committing GPU time to the ensemble")
    w("widening, because the answer decides the (designs x seeds) split.")
    w("")
    w("Estimator: RMS CA deviation over CDR-H3 (heavy 96–108) across **all C(k,2) seed pairs**,")
    w("each pair superposed on the framework. Reference-free, unlike the 2026-09-18 estimator")
    w("which measured everything against seed[0]; numbers here are not comparable to that one.")
    w("")
    w(f"Between-design variance of the 7-seed spread: **{var_between:.5f} Å²** "
      f"(sd {np.sqrt(var_between):.3f} Å over {len(designs)} designs).")
    w("")
    w("| seeds k | sampling var of a k-seed spread | reliability | attenuation √r | folds per design |")
    w("|---|---|---|---|---|")
    for k, v, rel, att in rows:
        w(f"| {k} | {v:.5f} Å² | **{rel:.3f}** | {att:.3f} | {k-1} new |")
    w("")
    w("`reliability = var_between / (var_between + sampling var)`. A correlation measured")
    w("against a k-seed spread is attenuated by √reliability, so a true ρ of 0.50 presents as")
    w("`0.50 × √r`.")
    w("")

    # budget optimisation: n designs x k seeds, seed 1 already exists for all 239
    w("## Allocation at a fixed fold budget")
    w("")
    w("Seed 1 exists for all 239 pool designs, so `n` designs at `k` seeds costs `n(k-1)` new")
    w("folds. Power for a correlation is driven by the attenuated ρ and by n. Using Fisher-z,")
    w("`SE = 1/√(n-3)`, the detectable effect at 80% power / α=0.05 two-sided is")
    w("`z = 2.80/√(n-3)`, and we compare it against the attenuated true effect.")
    w("")
    w("| budget (folds) | k | n | attenuation | ρ_true detectable at 80% power |")
    w("|---|---|---|---|---|")
    best = {}
    for budget in (120, 200, 280, 360):
        cand = []
        for k, v, rel, att in rows:
            if k < 2:
                continue
            n = budget // (k - 1)
            n = min(n, 239)
            if n < 8:
                continue
            z = 2.80 / np.sqrt(n - 3)
            rho_obs = np.tanh(z)
            rho_true = min(rho_obs / att, 1.0) if att > 0 else 1.0
            cand.append((rho_true, k, n, att))
        cand.sort()
        best[budget] = cand[0]
        for rho_true, k, n, att in cand:
            mark = " **←**" if (rho_true, k, n, att) == cand[0] else ""
            w(f"| {budget} | {k} | {n} | {att:.3f} | {rho_true:.3f}{mark} |")
    w("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}", file=sys.stderr)
    for b, (rt, k, n, att) in best.items():
        print(f"budget {b:>4} folds -> best n={n} designs x k={k} seeds, "
              f"attenuation {att:.3f}, detects rho_true>={rt:.3f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
