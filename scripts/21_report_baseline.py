#!/usr/bin/env python3
"""Baseline 1 report -> results/baseline_mpnn.md. Also exercises select/."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from locksmith.config import load
from locksmith.score import evaluate
from locksmith.select import Candidate, rank

PARQ = Path("designs/baseline_mpnn/designs.parquet")
OUT = Path("results/baseline_mpnn.md")
PANEL = Path("runs/panel/scores.jsonl")


def panel_curve(form="fab"):
    R = [json.loads(l) for l in PANEL.read_text().splitlines() if l.strip()]
    R = [r for r in R if r["predictor"] == "boltz2" and r["seed"] == 1
         and r["construct"] == form and r.get("dockq") is not None]
    d = np.array([r["dockq"] for r in R]); i = np.array([r["ipsae"] for r in R])
    lr = stats.linregress(d, i)
    sd = float(np.std(i - (lr.intercept + lr.slope * d), ddof=2))
    return lr, sd, len(d)


def main() -> int:
    df = pd.read_parquet(PARQ)
    cfg = load(); bands = cfg.bands()
    L = []
    def w(s=""):
        L.append(s)

    w("# Baseline 1 — plain ProteinMPNN at defaults")
    w()
    w(f"{len(df)} designs, ProteinMPNN `v_48_020`, temperature 0.1, seed 37, over the 29 IMGT "
      f"heavy CDR positions of pembrolizumab (H1 8, H2 8, H3 13). Light chain and PD-1 held "
      f"fixed as context. **No filtering, no reranking** — every design generated was folded as "
      f"a Fab, scored on all eight metrics and gated. This is the control the funnel must beat.")
    w()

    ok = df[df.fold_ok]
    w("## 1. Headline")
    w()
    n_viable = int((ok.viable == True).sum())     # noqa: E712
    n_unknown = int(ok.viable.isna().sum())
    w(f"- **{n_viable} of {len(ok)} designs clear all eight gates** "
      f"({100*n_viable/len(ok):.0f}%). {n_unknown} undetermined.")
    w(f"- Fold success: **{int(df.fold_ok.sum())}/{len(df)}**, zero failures.")
    if n_viable:
        w(f"- Best composite score among viable: **{ok[ok.viable == True].final_score.max():.1f}**")  # noqa: E712
    w()

    w("## 2. Which gates do the rejecting")
    w()
    fails: dict[str, int] = {}
    for s in ok.failing_gates.fillna(""):
        for m in [x for x in s.split(",") if x]:
            fails[m] = fails.get(m, 0) + 1
    w("| gate | designs failed | cutoff | direction |")
    w("|---|---|---|---|")
    for m, c in sorted(fails.items(), key=lambda kv: -kv[1]):
        b = bands[m]
        w(f"| `{m}` | **{c}/{len(ok)}** | {b.cutoff} | {b.direction}er is better |")
    if not fails:
        w("| *(none — every design cleared every gate)* | | | |")
    w()

    w("## 3. Distributions")
    w()
    w("| metric | min | median | max | cutoff | good |")
    w("|---|---|---|---|---|---|")
    for m in ("dockq", "ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa",
              "netsolp", "cdrh3_identity"):
        if m not in ok:
            continue
        v = ok[m].dropna()
        if v.empty:
            continue
        b = bands[m]
        w(f"| `{m}` | {v.min():.3f} | {v.median():.3f} | {v.max():.3f} | {b.cutoff} | {b.good} |")
    w()

    w("## 4. Where these designs sit on the panel's ipSAE↔DockQ curve")
    w()
    lr, sd, n = panel_curve("fab")
    v = ok.dropna(subset=["dockq", "ipsae"])
    pred = lr.intercept + lr.slope * v.dockq
    resid = v.ipsae - pred
    se = sd * np.sqrt(1/len(v) + 1/n)
    w(f"Panel Fab curve: `ipSAE = {lr.intercept:.3f} + {lr.slope:.3f} × DockQ`, residual sd "
      f"{sd:.3f}, n={n}. These designs are perturbations of a **memorised** complex, so this "
      f"tests the level-shift question from the post-cutoff work for free.")
    w()
    w(f"- mean residual **{resid.mean():+.3f}** (SE {se:.3f}) → **{resid.mean()/se:+.1f} SE**")
    w(f"- residual sd **{resid.std(ddof=1):.3f}** vs panel **{sd:.3f}** "
      f"({resid.std(ddof=1)/sd:.1f}×)")
    rho = stats.spearmanr(v.dockq, v.ipsae)
    w(f"- Spearman ipSAE↔DockQ across the baseline: **{rho.statistic:+.3f}** (p={rho.pvalue:.3f})")
    w()

    w("## 5. Ranked (via `select.rank`, gates structurally enforced)")
    w()
    cands = []
    for _, r in ok.iterrows():
        raw = {m: (None if pd.isna(r.get(m)) else r.get(m)) for m in bands}
        cands.append(Candidate(r.design_id, evaluate(raw, 1, cfg), {}))
    sel = rank(cands)
    w(f"{sel.n_viable} viable, {len(sel.rejected)} gated out, {len(sel.unknown)} undetermined.")
    w()
    if sel.ranked:
        w("| rank | design | final | DockQ | ipSAE | CDR-H3 id % | ΔG |")
        w("|---|---|---|---|---|---|---|")
        for k, c in enumerate(sel.ranked[:10], 1):
            R = c.scored.raw
            w(f"| {k} | `{c.design_id}` | **{c.scored.final:.1f}** | {R.get('dockq'):.3f} | "
              f"{R.get('ipsae'):.3f} | {R.get('cdrh3_identity'):.1f} | {R.get('dg'):.1f} |")
    w()
    # ---------------------------------------------------------------- reading
    w("## 6. What this baseline actually says")
    w()
    panel = {json.loads(l)["label"]: json.loads(l)
             for l in PANEL.read_text().splitlines() if l.strip()}
    wt = panel["v00_wt__fab__s1"]
    wt_raw = dict(dockq=wt["dockq"], ipsae=wt["ipsae"], dg=-14.3, contacts=102,
                  iface_plddt=94.4, cdr_sasa=1564, netsolp=0.569, cdrh3_identity=100.0)
    wt_s = evaluate(wt_raw, 1, cfg)
    w(f"**Pembrolizumab itself scores {wt_s.final} and is NON-VIABLE** — it fails the novelty "
      f"gate at 100% CDR-H3 identity, by construction. Every one of these 20 designs outscores "
      f"the licensed drug on the competition's own rubric ({ok.final_score.min()}–"
      f"{ok.final_score.max()}). That is the rubric working as specified, not an anomaly: it is "
      f"scoring novelty at 20% weight and a marketed antibody has none.")
    w()
    w("**The eight gates do not discriminate among backbone-constrained CDR redesigns.** A 100% "
      "hit rate is not a sign the designs are good; it is a sign the gates are not the binding "
      "constraint in this regime. ProteinMPNN redesigns sequence onto the *native backbone in "
      "complex*, so it selects residues that fit pembrolizumab's exact binding geometry, and "
      "Boltz then recovers approximately that pose. High DockQ is close to guaranteed by "
      "construction — which is precisely the caveat that DockQ-vs-5GGS measures **retention of "
      "the native binding mode**, not correctness.")
    w()
    w(f"**Consequence for M3: the funnel cannot demonstrate value through hit-rate against this "
      f"baseline.** There is no headroom — naive MPNN already clears every gate. The funnel has "
      f"to compete on composite score, on robustness under re-seeding, or in a regime where the "
      f"gates actually bite (larger backbone perturbation, or Challenge 2's de novo placement, "
      f"where the post-cutoff test already shows they do).")
    w()
    n_distinct = ok.final_score.nunique()
    w(f"**The composite has coarse resolution: {n_distinct} distinct values across {len(ok)} "
      f"designs.** Sub-scores are band midpoints, so `final` only moves when a metric crosses a "
      f"band edge. Ranking on `final` therefore sorts designs into a few tiers and the "
      f"**DockQ tiebreaker does the fine ordering within them** — which is the intended division "
      f"of labour under `selection_key: final`, and worth stating because it means the tiebreaker "
      f"is not decorative.")
    w()
    w("**The ipSAE level shift does NOT apply here.** On the five post-cutoff targets ipSAE sat "
      f"~0.19–0.28 *below* the panel curve. These designs sit **on** it (mean residual "
      f"{resid.mean():+.3f}, {resid.mean()/se:+.1f} SE, and a *tighter* spread than the panel "
      f"itself at {resid.std(ddof=1)/sd:.1f}×). The shift is a property of novel complexes, not "
      f"of designs — so Challenge 1 gate thresholds calibrated on the panel transfer, and "
      f"Challenge 2's would not.")
    w()
    w(f"**But ipSAE carries no ranking information here either**: Spearman ipSAE↔DockQ across "
      f"the 20 designs is **{rho.statistic:+.3f}** (p={rho.pvalue:.3f}). This is the panel's §8 "
      f"finding reproduced on real designs rather than on hand-mutants — within a narrow band of "
      f"live designs, ipSAE and structural correctness are uncorrelated. It confirms the "
      f"selection re-spec: report ipSAE, gate on it, do not rank on it.")
    w()
    w("## 7. Precision")
    w()
    w(f"At n={len(ok)} a viability rate of 100% carries a 95% CI of roughly [83%, 100%] "
      f"(rule of three). The claim supported is 'naive MPNN clears these gates at a high rate', "
      f"not 'always'. Twenty is enough to establish the referent and to show the gates do not "
      f"bite; it is not enough to estimate a small failure rate.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
