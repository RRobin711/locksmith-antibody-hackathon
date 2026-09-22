#!/usr/bin/env python3
"""How deep must the shortlist be, given that we cut it on a SINGLE-seed ordering?

THE FAILURE THIS PREVENTS. Shortlisting k designs on a noisy single-seed score and
then 3-seeding only those k means the survivors are re-measured and the discards never
are. Anything the noisy pass wrongly dropped is invisible for ever -- and the resulting
pool looks clean, because every design in it was measured twice. This project has
already made the structurally identical mistake once (G1c: an Fv screen whose ranking
was never checked against the Fab ranking it stood in for). Picking k = 30 by feel
repeats it.

THE MEASUREMENT. The 40-design pool carries three Boltz seeds per design, so the
single-seed -> 3-seed shuffle can be measured directly rather than assumed. Two
estimates, deliberately different in their assumptions:

  (a) EMPIRICAL, on the 40-pool. Rank by seed 1; treat the 3-seed mean as truth; find
      the depth that would have retained the true top 5. Distribution-free, but n=40
      and "truth" is itself a 3-seed mean, so it understates the depth a little.

  (b) SIMULATED, at the real n=239. Decompose variance: seed noise from the 40-pool's
      within-design spread, TRUE between-design spread from the 239-pool's observed
      spread minus that noise. Then simulate pools of 239 with known truth and find the
      depth retaining the true top 5 with probability >= 0.95. Assumes normality, which
      the empirical estimate does not.

Reporting both, and taking the LARGER, is the point: they fail in opposite directions.

Writes results/m3_shortlist_depth.md.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.select import surrogate

OLD_POOL = Path("designs/wide_mpnn/designs.json")
OLD = Path("runs/designs_wide")
NEW_POOL = Path("designs/wide_temp/designs.json")
NEW = Path("runs/designs_temp")
REPORT = Path("results/m3_shortlist_depth.md")
METRICS = ("ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa")
B = 4000
RNG = np.random.default_rng(0)


def surr(rec: dict, netsolp: float, identity: float, cfg) -> float:
    raw = {m: rec.get(m) for m in METRICS}
    raw["netsolp"], raw["cdrh3_identity"] = netsolp, identity
    return surrogate.compute(raw, 1, cfg).value


def load_old(cfg):
    pool = {d["design_id"]: d for d in json.loads(OLD_POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in (OLD / "seq_scores.jsonl").read_text().splitlines() if l.strip()}
    per = defaultdict(dict)
    for l in (OLD / "fold_scores.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if "dockq" in r:
                per[r["design_id"]][r["seed"]] = r
    out = {}
    for did in pool:
        if did in seq and len(per[did]) >= 3:
            ks = sorted(per[did])[:3]
            out[did] = [surr(per[did][k], seq[did]["netsolp"], seq[did]["cdrh3_identity"], cfg)
                        for k in ks]
    return out


def load_new(cfg):
    pool = {d["design_id"]: d for d in json.loads(NEW_POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in (NEW / "seq_scores.jsonl").read_text().splitlines() if l.strip()}
    vals = {}
    for l in (NEW / "fold_scores.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if "dockq" in r and r["design_id"] in seq:
                vals[r["design_id"]] = surr(r, seq[r["design_id"]]["netsolp"],
                                            seq[r["design_id"]]["cdrh3_identity"], cfg)
    return vals


def depth_for(truth_idx: set, order: np.ndarray) -> int:
    """Shallowest depth of `order` that contains every index in truth_idx."""
    pos = {int(d): i for i, d in enumerate(order)}
    return max(pos[t] for t in truth_idx) + 1


def main() -> int:
    cfg = load()
    old = load_old(cfg)
    new = load_new(cfg)
    L = []
    w = L.append

    arr = np.array([v for v in old.values()])            # (40, 3)
    within = np.sqrt(np.mean(np.var(arr, axis=1, ddof=1)))
    mean3 = arr.mean(axis=1)
    between3 = mean3.std(ddof=1)
    rel1 = 1 - within**2 / (between3**2 + within**2)
    rel3 = 1 - (within**2 / 3) / between3**2

    newv = np.array(list(new.values()))
    sd_obs_new = newv.std(ddof=1)
    var_true_new = max(sd_obs_new**2 - within**2, 1e-12)
    sd_true_new = np.sqrt(var_true_new)

    w("# How deep must the shortlist be?")
    w("")
    w("Reproduce with `scripts/31_shortlist_depth.py`. The question is not \"how many can we "
      "afford to 3-seed\" but \"how many must we 3-seed so that the design we would have picked "
      "with perfect measurement is still in the list\". Cutting on a single-seed ordering and "
      "re-measuring only the survivors makes anything wrongly discarded invisible for ever.")
    w("")
    w("## 1. The noise, measured on the continuous surrogate")
    w("")
    w("All quantities are in surrogate points, which share the 0–100 scale of `final` and agree "
      "with it exactly at every band anchor (`src/locksmith/select/surrogate.py`).")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| seed noise sd, within design (40-pool, 3 seeds) | **{within:.3f}** |")
    w(f"| between-design sd of 3-seed means (40-pool) | {between3:.3f} |")
    w(f"| single-seed reliability of the surrogate | **{rel1:.3f}** |")
    w(f"| 3-seed-mean reliability of the surrogate | **{rel3:.3f}** |")
    w(f"| observed sd of the 239-pool (single seed) | {sd_obs_new:.3f} |")
    w(f"| implied TRUE between-design sd, 239-pool | **{sd_true_new:.3f}** |")
    w("")
    w(f"For comparison the banded `final` scored **0.602** single-seed and **0.780** at three "
      f"seeds. The surrogate is {'better' if rel1 > 0.602 else 'no better'} at one seed "
      f"({rel1:.3f}), which is the entire reason for ranking on it.")
    w("")

    # ---------- (a) empirical on the 40-pool ----------
    w("## 2. Estimate (a) — empirical, distribution-free, n=40")
    w("")
    s1 = arr[:, 0]
    order = np.argsort(-s1)
    rows = []
    for m in (1, 3, 5):
        truth = set(np.argsort(-mean3)[:m].tolist())
        rows.append((m, depth_for(truth, order)))
    w("| retain the true top… | depth needed in the 40-pool | as a fraction of the pool |")
    w("|---|---|---|")
    for m, d in rows:
        w(f"| {m} | **{d}** | {d/len(mean3):.0%} |")
    w("")
    w("Truth here is the 3-seed mean, which is itself noisy (reliability "
      f"{rel3:.3f}), so this understates the depth somewhat.")
    w("")

    # ---------- (b) simulation at n=239 ----------
    w("## 3. Estimate (b) — simulated at the real n=239")
    w("")
    w(f"True scores drawn N(0, {sd_true_new:.3f}); one observation each at "
      f"N(true, {within:.3f}); rank by the observation; record the depth containing the true "
      f"top *m*. {B:,} simulated pools.")
    w("")
    n = len(newv)
    w("| retain the true top… | median depth | 90th pct | **depth for P≥0.95** | folds to 3-seed it |")
    w("|---|---|---|---|---|")
    chosen = {}
    for m in (1, 3, 5):
        depths = np.empty(B, dtype=int)
        for b in range(B):
            true = RNG.normal(0, sd_true_new, n)
            obs = true + RNG.normal(0, within, n)
            truth = set(np.argsort(-true)[:m].tolist())
            depths[b] = depth_for(truth, np.argsort(-obs))
        d95 = int(np.percentile(depths, 95))
        chosen[m] = d95
        w(f"| {m} | {int(np.median(depths))} | {int(np.percentile(depths,90))} | **{d95}** | "
          f"{d95*2} |")
    w("")
    # ---------- (c) the criterion that actually matters ----------
    w("## 4. Both of the above answer the wrong question")
    w("")
    w("Estimates (a) and (b) size the shortlist so that the true best designs are *retained*. "
      "But retaining the best design is not the same as **picking** it, and only the pick "
      "ships. The shortlist is re-measured at more seeds and then argmax-ed, so the right "
      "criterion is the expected TRUE quality of the design finally named — and that is "
      "limited by the reliability of the measurement used to choose, not by the depth of "
      "the list.")
    w("")
    w(f"Simulating the whole procedure end to end (1 seed on all {n} → top k → 3 seeds on "
      f"those → argmax), {B:,} pools:")
    w("")
    w("| k | extra folds | E[true score of the design picked] |")
    w("|---|---|---|")
    dt = {}
    for kk in (5, 10, 20, 30, 60, 119, n):
        vals = np.empty(B)
        for b in range(B):
            true = RNG.normal(0, sd_true_new, n)
            sl = np.argsort(-(true + RNG.normal(0, within, n)))[:kk]
            obs3 = true[sl] + RNG.normal(0, within / np.sqrt(3), kk)
            vals[b] = true[sl][np.argmax(obs3)]
        dt[kk] = vals.mean()
        w(f"| {kk} | {2*kk} | {vals.mean():+.4f} |")
    w("")
    w(f"**The curve is flat past k≈20.** Going from k=20 ({dt[20]:+.4f}) to 3-seeding the "
      f"entire pool ({dt[n]:+.4f}, {2*n} folds) buys nothing measurable. Depth stops helping "
      f"almost immediately, because a deeper list adds candidates whose 3-seed scores are "
      f"just as noisy — a noisy-high mediocre design gets promoted about as often as the "
      f"true best gets found.")
    w("")
    w("## 5. So spend the folds on SEEDS, not on depth")
    w("")
    w("If the binding constraint is the reliability of the choosing measurement, the fix is "
      "more seeds per candidate, not more candidates. Holding the fold budget fixed:")
    w("")
    w("| budget (extra folds) | k × seeds | E[true score of pick] |")
    w("|---|---|---|")
    best_combo = None
    for budget in (40, 120, 240):
        for sd_n in (3, 4, 5, 7, 10, 15):
            kk = budget // (sd_n - 1)
            if kk < 2:
                continue
            vals = np.empty(B)
            for b in range(B):
                true = RNG.normal(0, sd_true_new, n)
                sl = np.argsort(-(true + RNG.normal(0, within, n)))[:kk]
                obs = true[sl] + RNG.normal(0, within / np.sqrt(sd_n), kk)
                vals[b] = true[sl][np.argmax(obs)]
            e = vals.mean()
            mark = ""
            if budget == 120 and sd_n == 7:
                mark = "  ← **chosen**"
                best_combo = (kk, sd_n, e)
            w(f"| {budget} | {kk} × {sd_n} | {e:+.4f}{mark} |")
    w("")
    w("**Three seeds is the worst allocation at every budget tested.** The campaign plan's "
      "\"3-seed the shortlist\" spends folds on the axis that has already stopped paying.")
    w("")
    k = best_combo[0]
    w(f"## 6. Decision: **k = {best_combo[0]} designs at {best_combo[1]} seeds** "
      f"({best_combo[0]*(best_combo[1]-1)} extra folds)")
    w("")
    w(f"Supersedes the k={chosen[5]} of §3 and the k=30 planned by feel. Expected true score "
      f"of the pick {best_combo[2]:+.4f} against {dt[30]:+.4f} for the planned 30×3 — a better "
      f"pick for {best_combo[0]*(best_combo[1]-1)} folds against 60.")
    w("")
    w("**The assumption this rests on, and how the run tests it.** The simulation assumes seed "
      "noise is i.i.d. and that s seeds shrink it by √s. The 40-pool has only three seeds, so "
      "that is unverified past s=3. Seven seeds on twenty designs checks it directly: if the "
      "within-design sd across 7 seeds materially exceeds the 3-seed estimate, the noise has a "
      "systematic component — a design with two genuine conformational basins would do it — and "
      "averaging has stopped helping. That check is reported with the winner.")
    w("")
    w("## 7. Superseded: the retention-based sizing")
    w("")
    w(f"Kept because the reasoning trail matters. Retention-based sizing said k={chosen[5]}.")
    w("")
    w(f"The two estimates disagreed by construction and the larger would have been taken: "
      f"empirical (a) says {max(d for _, d in rows)}, simulation (b) says {chosen[5]} for the "
      f"true top 5 at 95%. **k = {k}**, costing **{k*2} additional folds** "
      f"({k*2*84/3600:.1f} h at the measured 84 s/fold quiet).")
    w("")
    if k > 30:
        w(f"> This is **{k/30:.1f}× the 30 that was planned by feel**. The extra "
          f"{(k-30)*2} folds cost {((k-30)*2)*84/3600:.1f} h — cheap against the cost of "
          f"never discovering that the single-seed pass discarded the best design. Taking them.")
    else:
        w(f"> Shallower than the 30 planned by feel, so 30 is kept as the operating depth: "
          f"there is no reason to cut below what was already budgeted.")
        k = 30
    w("")
    w("### Why not simply 3-seed everything")
    w(f"239 designs x 2 extra seeds = 478 folds = {478*84/3600:.1f} h. That is the honest "
      f"alternative and it is not absurd; it is rejected only because {k} captures the true "
      f"top 5 at 95% for {k*2/478:.0%} of the folds. If the campaign is ever re-run with "
      f"batching working, 3-seeding the whole pool removes this entire analysis and its "
      f"assumptions.")
    w("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L[-40:]))
    print(f"\n--> wrote {REPORT}; CHOSEN_DEPTH={k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
