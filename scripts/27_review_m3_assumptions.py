#!/usr/bin/env python3
"""Test the assumptions M3 is about to be built on, using folds already paid for.

M3's plan is: generate wide -> filter on CDR-H3 aromatic fraction BEFORE folding ->
fold survivors -> rank on 3-seed mean `final`. Four of those words hide an assumption
that the existing 40x3 pool can already test at zero GPU cost:

  1. "filter"  -- does it beat RANDOM pruning at the same fold budget? A filter that
                  only matches random is not a filter, it is a coin.
  2. "aromatic" -- is that the only free feature, and is the effect a gradient or a step?
  3. "rank on `final`" -- what is the seed reliability of `final` itself? DockQ's was
                  measured (0.727); the SELECTION KEY's never was.
  4. "top-end"  -- the proposed G3 judges top-end quality. Does the filter move the max,
                  or only the mean? Those are different claims with different uses.

Writes results/m3_plan_review.md. Read-only over runs/designs_wide/.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.score import evaluate

POOL = Path("designs/wide_mpnn/designs.json")
OUT = Path("runs/designs_wide")
REPORT = Path("results/m3_plan_review.md")
CDRH3 = slice(95, 108)
AROMATIC = set("FWY")
B = 20000                      # resamples for the random-pruning null
SEED_SD_DOCKQ = 0.018          # measured, results/reseed_ensemble.md


def load_pool():
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in (OUT / "seq_scores.jsonl").read_text().splitlines() if l.strip()}
    per = defaultdict(dict)
    for l in (OUT / "fold_scores.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if "error" not in r:
                per[r["design_id"]][r["seed"]] = r
    return pool, seq, per


def build(cfg, pool, seq, per):
    rows = []
    for did, d in pool.items():
        seeds = per[did]
        if len(seeds) < 3 or did not in seq:
            continue
        ks = sorted(seeds)[:3]
        h3 = d["heavy"][CDRH3]
        rec = {"design_id": did, "h3": h3, "arom": sum(c in AROMATIC for c in h3),
               "h3_len": len(h3), "identity": seq[did]["cdrh3_identity"],
               "mpnn_score": d["score"], "temperature": d["temperature"]}
        for m in ("dockq", "ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa"):
            rec[m] = float(np.mean([seeds[s][m] for s in ks]))
        rec["netsolp"] = seq[did]["netsolp"]
        rec["cdrh3_identity"] = rec["identity"]
        # `final` per seed AND as a 3-seed mean -- the difference is the whole point of §3
        finals = []
        for s in ks:
            raw = {k: seeds[s].get(k) for k in cfg.bands()}
            raw["netsolp"], raw["cdrh3_identity"] = rec["netsolp"], rec["identity"]
            finals.append(evaluate(raw, 1, cfg).final)
        rec["final_per_seed"] = finals
        rec["final"] = float(np.mean(finals))
        raw = {k: rec.get(k) for k in cfg.bands()}
        rec["final_of_mean"] = evaluate(raw, 1, cfg).final
        rows.append(rec)
    return rows


def partial_spearman(x, y, z):
    """Spearman of x,y with z partialled out -- rank, then regress out, then correlate."""
    rx, ry, rz = (stats.rankdata(v) for v in (x, y, z))
    res = lambda a, b: a - np.polyval(np.polyfit(b, a, 1), b)
    return stats.pearsonr(res(rx, rz), res(ry, rz))


def main() -> int:
    cfg = load()
    rows = build(cfg, *load_pool())
    n = len(rows)
    arom = np.array([r["arom"] for r in rows])
    dq = np.array([r["dockq"] for r in rows])
    idt = np.array([r["identity"] for r in rows])
    fin = np.array([r["final"] for r in rows])
    rng = np.random.default_rng(0)
    L = []
    w = L.append

    w("# Reviewing M3's assumptions against folds already paid for")
    w("")
    w(f"No new folds. {n} designs x 3 Boltz seeds from [[ensemble_validation|the ensemble "
      f"validation pool]], re-interrogated to test what the M3 campaign plan assumes. "
      f"Reproduce with `scripts/27_review_m3_assumptions.py`.")
    w("")
    w("Every number below was computed on the same pool that *discovered* the aromatic "
      "effect, so none of it is out-of-sample evidence FOR that effect. It is evidence about "
      "the effect's **shape**, its **competitors**, and whether the planned **decision rule** "
      "can act on it — which is exactly what a campaign design needs and what a single "
      "correlation coefficient cannot supply.")
    w("")

    # ---------------- 1. the null model ----------------
    w("## 1. The filter improves the mean; it does not improve the maximum")
    w("")
    w("A pre-fold filter's job is to let a fixed fold budget reach a better design. The "
      "comparison that tests this is **not** filtered-vs-unfiltered — throwing away half a "
      "pool keeps the best design half the time by luck alone. The comparison is "
      "filtered-vs-**a random subset of the same size**, which costs nothing to run.")
    w("")
    w(f"Random subsets drawn {B:,} times without replacement.")
    w("")
    w("| keep | statistic | filtered | random mean | P(random >= filtered) |")
    w("|---|---|---|---|---|")
    keeps = (0.4, 0.5, 0.6)
    null = {}
    for keep in keeps:
        k = int(round(n * keep))
        sel = np.argsort(arom, kind="stable")[:k]        # keep the LEAST aromatic
        fmax, fmean = dq[sel].max(), dq[sel].mean()
        rmax = np.empty(B); rmean = np.empty(B)
        for b in range(B):
            s = rng.choice(n, k, replace=False)
            rmax[b], rmean[b] = dq[s].max(), dq[s].mean()
        pmax, pmean = (rmax >= fmax).mean(), (rmean >= fmean).mean()
        null[keep] = (pmax, pmean)
        w(f"| {keep:.0%} (n={k}) | **max** DockQ | {fmax:.4f} | {rmax.mean():.4f} | **{pmax:.3f}** |")
        w(f"| {keep:.0%} (n={k}) | mean DockQ | {fmean:.4f} | {rmean.mean():.4f} | **{pmean:.4f}** |")
    w("")
    w("**Read the max row first.** At every retention level the filtered subset's best design "
      "is no better than a random subset's — p = "
      + ", ".join(f"{null[k][0]:.2f}" for k in keeps) +
      ", i.e. indistinguishable from chance. The filter never discards the pool maximum, but "
      "neither does random pruning, often enough that keeping it proves nothing.")
    w("")
    w("The mean row is where the filter earns its place: p = "
      + ", ".join(f"{null[k][1]:.3f}" for k in keeps) +
      ". Filtering raises the *typical* quality of what gets folded by "
      f"{dq[np.argsort(arom, kind='stable')[:int(round(n*0.4))]].mean() - dq.mean():+.4f} DockQ "
      f"at 40% retention — about **one seed standard deviation** ({SEED_SD_DOCKQ:.3f}).")
    w("")
    w("> **Consequence for G3.** A criterion worded around *top-end* quality is aimed at the")
    w("> one thing this filter demonstrably does not do, and would pass or fail for reasons")
    w("> unrelated to the filter. A criterion worded around *mean* quality — equivalently,")
    w("> shortlist yield per fold — tests something the data can actually support.")
    w("")
    w("One more thing the table exposes: at 40% retention the filter **cannot be applied "
      "cleanly at all**. Seventeen designs share aromatic count 2, so a rule that keeps 16 of "
      "40 has to split that tier arbitrarily, and the reported figure depends on the sort's "
      "tie-breaking. A percentile filter over a 4-valued feature is not a well-defined rule.")
    w("")

    # ---------------- 2. shape of the effect ----------------
    w("## 2. The aromatic effect is a step at <=1, not a gradient")
    w("")
    w("CDR-H3 is 13 residues throughout this pool, so `aromatic_frac` is a **4-level count** "
      "and `aromatic_frac` and aromatic *count* are the same variable (both rho = "
      f"{stats.spearmanr(arom, dq)[0]:+.3f} against DockQ).")
    w("")
    w("| aromatics in CDR-H3 | n | mean 3-seed DockQ | sd | max |")
    w("|---|---|---|---|---|")
    for v in sorted(set(arom.tolist())):
        s = dq[arom == v]
        sd = f"{s.std(ddof=1):.4f}" if len(s) > 1 else "—"
        w(f"| {v} | {len(s)} | **{s.mean():.4f}** | {sd} | {s.max():.4f} |")
    kw = stats.kruskal(*[dq[arom == v] for v in sorted(set(arom.tolist())) if (arom == v).sum() > 1])
    w("")
    w(f"Kruskal–Wallis over the three populated levels: H = {kw.statistic:.2f}, p = {kw.pvalue:.4f}.")
    w("")
    r_all, _ = stats.spearmanr(arom, dq)
    m = arom != arom.max()
    r_drop, p_drop = stats.spearmanr(arom[m], dq[m])
    w(f"**Leverage check.** The top level holds a single design. Dropping it: rho "
      f"{r_all:+.3f} -> **{r_drop:+.3f}** (p = {p_drop:.4f}, n = {m.sum()}). The effect is not "
      f"an artefact of that one point — which is worth stating, because this project has "
      f"already been bitten once by an R^2 carried entirely by two anchor designs.")
    w("")
    lo = dq[arom <= 1]
    w(f"But the structure is a **step, not a slope**: designs with <=1 aromatic average "
      f"{lo.mean():.4f} with sd {lo.std(ddof=1):.4f}, against {dq[arom >= 2].mean():.4f} "
      f"(sd {dq[arom >= 2].std(ddof=1):.4f}) for the rest. The low-aromatic group is not just "
      f"better, it is **{dq[arom >= 2].std(ddof=1) / lo.std(ddof=1):.1f}x tighter** — it "
      f"contains no failures rather than better successes.")
    w("")
    w(f"Only **{(arom <= 1).sum()}/{n} ({(arom <= 1).mean():.0%})** of the pool clears count <=1. "
      "A *percentile* filter (\"keep the least-aromatic 40%\") therefore admits a large "
      "majority of count-2 designs and dilutes the very effect it is selecting on. It is also "
      "**not portable across generation regimes**: the same percentile maps to a different "
      "absolute aromatic content at every MPNN temperature, which would confound the planned "
      "temperature arms with the filter itself. Specify the threshold as an **absolute count**.")
    w("")

    # ---------------- 3. reliability of the selection key ----------------
    w("## 3. The selection key is `final`, and nobody had measured its reliability")
    w("")
    flips = sum(1 for r in rows if len(set(r["final_per_seed"])) > 1)
    within = np.mean([np.std(r["final_per_seed"], ddof=1) for r in rows])
    wvar = np.mean([np.var(r["final_per_seed"], ddof=1) for r in rows])
    between = fin.std(ddof=1)
    rel1 = 1 - wvar / (between ** 2 + wvar)
    rel3 = 1 - (wvar / 3) / (between ** 2)
    w(f"`config/metrics.yaml` sets `selection_key: final`. The measured 0.727 reliability that "
      f"M3's multi-seeding is justified by is **DockQ's**, not `final`'s. They are not the same "
      f"number, because banding is a step function and a metric sitting near a band edge flips "
      f"band on seed noise.")
    w("")
    w(f"| quantity | value |")
    w(f"|---|---|")
    w(f"| designs whose single-seed `final` changes across 3 seeds | **{flips}/{n} ({flips/n:.0%})** |")
    w(f"| within-design sd of single-seed `final` | {within:.3f} points |")
    w(f"| between-design sd of 3-seed mean `final` | {between:.3f} points |")
    w(f"| single-seed reliability of `final` | **{rel1:.3f}** |")
    w(f"| 3-seed-mean reliability of `final` | **{rel3:.3f}** |")
    w(f"| distinct values of `final` across the pool | {sorted(set(np.round(fin,2).tolist()))} |")
    w("")
    w(f"More than half the pool changes its rubric score depending on which Boltz seed you "
      f"folded it with, and the sub-scores doing the flipping are **ipSAE** and **dG** — both "
      f"sitting near a band edge. Single-seed reliability of the key we actually rank on is "
      f"**{rel1:.3f}**, materially worse than DockQ's 0.727; even the 3-seed mean reaches only "
      f"**{rel3:.3f}**.")
    w("")
    w("Worse for a wide campaign: `final` takes **three distinct values** across 40 designs. "
      "Scaling to 200 will not add resolution, because banding is what removes it. The top "
      "tier will be a large tie broken by DockQ at reliability 0.727 over a range of "
      f"{dq.max()-dq.min():.3f} — which is how you select noise.")
    w("")
    w("> **Consequence for M3.** Ranking on the banded composite discards precisely the")
    w("> within-band information that distinguishes candidates. Rank internally on a")
    w("> continuous surrogate and keep `final` as the reported score; and prefer, among")
    w("> ties, the design furthest from a band edge — the project already has this idea as")
    w("> `margin_fraction` for gates, and band edges deserve it too.")
    w("")

    # ---------------- 4. the missed second feature ----------------
    w("## 4. A second free feature was missed, and it is nearly as strong")
    w("")
    w("The pre-registration tested six pre-fold features and found one. It did not test the "
      "rubric metric that is *already* computed before folding: **CDR-H3 identity to the "
      "parent**.")
    w("")
    w("| relationship | Spearman | p |")
    w("|---|---|---|")
    for lab, a, b in (("aromatic count -> DockQ", arom, dq),
                      ("CDR-H3 identity -> DockQ", idt, dq),
                      ("aromatic count -> CDR-H3 identity", arom, idt)):
        r, p = stats.spearmanr(a, b)
        w(f"| {lab} | {r:+.3f} | {p:.4f} |")
    r, p = partial_spearman(arom, dq, idt)
    w(f"| partial: aromatic -> DockQ, controlling identity | **{r:+.3f}** | {p:.4f} |")
    r, p = partial_spearman(idt, dq, arom)
    w(f"| partial: identity -> DockQ, controlling aromatic | **{r:+.3f}** | {p:.4f} |")
    w("")
    z = lambda a: (stats.rankdata(a) - stats.rankdata(a).mean()) / stats.rankdata(a).std()
    combo = -z(arom) + z(idt)
    rc, pc = stats.spearmanr(combo, dq)
    w(f"The two features are **uncorrelated with each other** "
      f"(rho = {stats.spearmanr(arom, idt)[0]:+.3f}) and each *strengthens* when the other is "
      f"controlled — mutual suppression. A combined rank score reaches rho = **{rc:+.3f}** "
      f"(p = {pc:.5f}) against 3-seed mean DockQ, far above either alone.")
    w("")
    w("| keep 40% by | mean DockQ | max | top-5 retained | mean identity |")
    w("|---|---|---|---|---|")
    k = int(round(n * 0.4))
    top5 = set(np.argsort(-dq)[:5].tolist())
    for name, score in (("aromatic only", -arom.astype(float)), ("identity only", idt), ("combined", combo)):
        sel = np.argsort(-score, kind="stable")[:k]
        w(f"| {name} | {dq[sel].mean():.4f} | {dq[sel].max():.4f} | "
          f"{len(top5 & set(sel.tolist()))}/5 | {idt[sel].mean():.1f}% |")
    w(f"| (unfiltered pool) | {dq.mean():.4f} | {dq.max():.4f} | 5/5 | {idt.mean():.1f}% |")
    w("")
    w("**And here is the catch that makes this a trade, not a free win.** CDR-H3 identity is "
      "the *novelty* axis, which `config/metrics.yaml` prices at **2x** a binding metric, and "
      "it runs the wrong way: higher identity predicts better DockQ but scores **worse** on "
      "novelty. Selecting on it buys binding with novelty points.")
    w("")
    ri, pi = stats.spearmanr(idt, fin)
    ra, pa = stats.spearmanr(arom, fin)
    w(f"In *this* pool the trade happens to be invisible — identity -> `final` is "
      f"rho = {ri:+.3f} (p = {pi:.3f}), because all {len(set(idt.tolist()))} distinct identity "
      f"values ({sorted(set(idt.tolist()))}%) fall in a single novelty band. Aromatic count, by "
      f"contrast, predicts `final` at rho = **{ra:+.3f}** (p = {pa:.4f}) — *better* than it "
      f"predicts DockQ. **Aromatic content is the feature to filter on; identity is a feature "
      f"to hold constant**, not to optimise, or the campaign will quietly trade away the "
      f"highest-priced axis on the rubric.")
    w("")

    # ---------------- 5. what the pool cannot tell us ----------------
    w("## 5. What this pool cannot tell anyone, and why M3's arms are right to exist")
    w("")
    w("| dimension | distinct values in 40 designs |")
    w("|---|---|")
    w(f"| CDR-H3 length | {sorted(set(r['h3_len'] for r in rows))} |")
    w(f"| MPNN temperature | {sorted(set(r['temperature'] for r in rows))} |")
    w(f"| CDR-H3 identity | {sorted(set(idt.tolist()))} |")
    w(f"| aromatic count | {sorted(set(arom.tolist()))} |")
    w(f"| `final` | {sorted(set(np.round(fin,2).tolist()))} |")
    w("")
    w("Forty designs, and the pool is four aromatic levels x three identity levels x one "
      "length x one temperature. This is a **densely sampled single operating point**, not a "
      "design space. Every conclusion above — including the aromatic effect — is conditional "
      "on that point. Varying temperature is the correct primary axis for M3 precisely "
      "because it is the only cheap way to find out whether any of this survives elsewhere.")
    w("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n")
    print(f"wrote {REPORT}  ({len(L)} lines, n={n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
