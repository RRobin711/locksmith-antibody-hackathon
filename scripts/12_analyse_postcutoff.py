#!/usr/bin/env python3
"""The post-cutoff test. Analysis exactly as pre-registered in
results/prereg_post_cutoff_test.md. Writes results/postcutoff_result.md."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

SCORES = Path("runs/postcutoff/scores.jsonl")
PANEL = Path("runs/panel/scores.jsonl")
TARGETS = Path("data/refs/postcutoff/prepared/manifest.json")
OUT = Path("results/postcutoff_result.md")

# Pre-registered panel curves (refit here from the panel data so they cannot drift).
META = {  # release date, antigen, CDR-H3 novelty vs closest pre-cutoff relative
    "9JBQ": ("2024-09-11", "PcrV (P. aeruginosa)", 21.4),
    "9BQW": ("2025-08-06", "DbpA (Borrelia)", 28.6),
    "8TBB": ("2024-08-28", "TIM-3 (human)", 31.2),
    "9W43": ("2026-07-01", "PD-1 (human)", 38.5),
    "8RWB": ("2025-02-12", "ULBP6 (human)", 44.4),
}


def curves():
    R = [json.loads(l) for l in PANEL.read_text().splitlines() if l.strip()]
    R = [r for r in R if r["predictor"] == "boltz2" and r["seed"] == 1
         and r.get("dockq") is not None and r.get("ipsae") is not None]
    out = {}
    for form in ("fv", "fab"):
        d = np.array([r["dockq"] for r in R if r["construct"] == form])
        i = np.array([r["ipsae"] for r in R if r["construct"] == form])
        lr = stats.linregress(d, i)
        sd = float(np.std(i - (lr.intercept + lr.slope * d), ddof=2))
        out[form] = (lr, sd, len(d), float(d.mean()), float(((d - d.mean()) ** 2).sum()))
    return out


def main() -> int:
    S = [json.loads(l) for l in SCORES.read_text().splitlines() if l.strip()]
    C = curves()
    L = []
    def w(s=""):
        L.append(s)

    w("# The post-training-cutoff test — result")
    w()
    w("Analysis exactly as fixed in [[prereg_post_cutoff_test|the pre-registration]], which was "
      "written before target selection and before any fold. Targets and the novelty screen are in "
      "[[postcutoff_targets|the target record]]. Five antibody–antigen complexes released "
      "2024-09 to 2026-07, all ≥7 months clear of Boltz-2's **2023-06-01** release-date cutoff, "
      "each with a closest pre-cutoff CDR-H3 relative ≤44.4% identical.")
    w()
    w("**DockQ here is genuine prediction accuracy** — each target scored against its own released "
      "crystal, same molecule, known answer the model has not seen. That differs from the variant "
      "panel, where mutants were scored against the 5GGS crystal and DockQ measured retention of "
      "the native binding mode.")
    w()

    w("## 1. The numbers")
    w()
    w("| target | released | antigen | CDR-H3 novelty | Fv DockQ | Fv ipSAE | Fab DockQ | Fab ipSAE |")
    w("|---|---|---|---|---|---|---|---|")
    by = {}
    for t in META:
        row = {r["construct"]: r for r in S if r["target"] == t}
        by[t] = row
        rel, ag, nov = META[t]
        def g(f, k):
            return f"{row[f][k]:.3f}" if f in row and row[f].get(k) is not None else "--"
        w(f"| {t} | {rel} | {ag} | {nov}% | {g('fv','dockq')} | {g('fv','ipsae')} | "
          f"{g('fab','dockq')} | {g('fab','ipsae')} |")
    w(f"| *5GGS (memorised, reference)* | *2017* | *PD-1* | *—* | *0.820* | *0.841* | *0.818* | *0.807* |")
    w()

    # ---------------------------------------------------------------- level
    w("## 2. Level — the Challenge 2 go/no-go")
    w()
    for form in ("fab", "fv"):
        dq = sorted(by[t][form]["dockq"] for t in META if form in by[t])
        med = float(np.median(dq))
        n_pass = sum(1 for x in dq if x >= 0.49)
        if med >= 0.49 and n_pass >= 3:
            verdict = "**PASS**"
        elif med >= 0.23:
            verdict = "**MARGINAL**"
        else:
            verdict = "**FAIL**"
        w(f"- **{form.upper()}**: DockQ {', '.join(f'{x:.3f}' for x in dq)} → "
          f"median **{med:.3f}**, {n_pass}/5 ≥ 0.49 → {verdict}")
    w()
    fab = sorted(by[t]["fab"]["dockq"] for t in META)
    w(f"Against 5GGS's 0.818 (Fab), the median novel target scores **{np.median(fab):.3f}** — a drop "
      f"of **{0.818 - np.median(fab):.3f} DockQ**. Four of five fall below 0.23, the CAPRI "
      f"'acceptable' floor, meaning the binding mode is **not recovered at all**. The single "
      f"success (8TBB, Fab 0.676 / Fv 0.852) shows the pipeline is capable — these are model "
      f"failures, not harness failures.")
    w()

    # ---------------------------------------------------------------- relationship
    w("## 3. Relationship — does the ipSAE calibration survive novel structures?")
    w()
    w("Residual against the panel curve for the same construct, in units of the panel's residual sd.")
    w()
    for form in ("fv", "fab"):
        lr, sd, n, dbar, sxx = C[form]
        w(f"**{form.upper()} curve** — `ipSAE = {lr.intercept:.3f} + {lr.slope:.3f} × DockQ`, "
          f"residual sd {sd:.3f}, n={n}")
        w()
        w("| target | DockQ | ipSAE predicted | ipSAE observed | residual | in sd |")
        w("|---|---|---|---|---|---|")
        res = []
        for t in META:
            if form not in by[t]:
                continue
            r = by[t][form]
            pred = lr.intercept + lr.slope * r["dockq"]
            resid = r["ipsae"] - pred
            res.append(resid)
            w(f"| {t} | {r['dockq']:.3f} | {pred:.3f} | {r['ipsae']:.3f} | {resid:+.3f} | "
              f"**{resid/sd:+.1f}** |")
        res = np.array(res)
        se = sd * np.sqrt(1 / len(res) + 1 / n)
        w()
        w(f"- mean residual **{res.mean():+.3f}** (SE {se:.3f}) → **{res.mean()/se:+.1f} SE**")
        w(f"- but the residuals themselves have sd **{res.std(ddof=1):.3f}**, versus the panel's "
          f"**{sd:.3f}** — a **{res.std(ddof=1)/sd:.1f}×** inflation")
        rho = stats.spearmanr([by[t][form]["dockq"] for t in META if form in by[t]],
                              [by[t][form]["ipsae"] for t in META if form in by[t]])
        w(f"- Spearman ipSAE vs DockQ on these five: **rho = {rho.statistic:+.3f}**, p = {rho.pvalue:.3f} "
          f"(panel: +0.815 Fv / +0.754 Fab)")
        w()

    # ---------------------------------------------------------------- false positives
    w("## 4. The failure mode that matters most")
    w()
    w("The pre-registration asked whether ipSAE sits above or below the curve. Neither describes "
      "what happened: **the relationship collapses**, and it collapses in both directions at once.")
    w()
    w("| | ipSAE | DockQ | what it means |")
    w("|---|---|---|---|")
    w("| 9W43 Fv | **0.722** | **0.070** | confident, and completely wrong |")
    w("| 9BQW Fab | **0.707** | **0.064** | confident, and completely wrong |")
    w("| 8TBB Fv | 0.674 | **0.852** | the one correct prediction — and it scores *lower* than both failures |")
    w("| 9JBQ Fv | 0.000 | 0.074 | correctly unconfident |")
    w()
    w("**ipSAE ranks two catastrophically wrong predictions above the only correct one.** Both false "
      "positives clear the rubric's 0.60 ipSAE cutoff comfortably; one clears 0.70. A funnel keyed "
      "on ipSAE would have promoted both and discarded nothing.")
    w()
    # ------------------------------------------------ mechanism + novelty
    w("## 5. Why ipSAE is fooled — the failures are not failures to dock")
    w()
    w("| prediction | Ab–Ag contacts <5 Å | min distance | DockQ |")
    w("|---|---|---|---|")
    import gemmi
    idx = {json.loads(l)["label"]: json.loads(l)
           for l in Path("runs/postcutoff/index.jsonl").read_text().splitlines() if l.strip()}
    for t in META:
        lab = f"{t.lower()}__fab__s1"
        if lab not in idx or not idx[lab].get("ok"):
            continue
        st = gemmi.read_structure(idx[lab]["pdb"]); st.remove_hydrogens()
        ch = {c.name: np.array([[a.pos.x, a.pos.y, a.pos.z] for r in c for a in r])
              for c in st[0]}
        ab = np.vstack([ch["A"], ch["B"]])
        D = np.linalg.norm(ab[:, None, :] - ch["C"][None, :, :], axis=-1)
        w(f"| {t} Fab | {int((D < 5.0).sum())} | {D.min():.1f} Å | {by[t]['fab']['dockq']:.3f} |")
    w()
    w("**Every failed prediction builds a large, well-packed interface.** The model is not failing "
      "to dock; it is docking confidently to the **wrong epitope or the wrong orientation**. That "
      "is the mechanism behind the false positives: ipSAE scores the interface the model built, and "
      "a confidently-built wrong interface is indistinguishable, to ipSAE, from a confidently-built "
      "right one. Nothing in the PAE can see that the epitope is wrong, because the PAE is the "
      "model's opinion of its own output.")
    w()
    w("This also means the failure is **not** about antibody novelty per se:")
    w()
    for form in ("fv", "fab"):
        nov = [META[t][2] for t in META if form in by[t]]
        dq = [by[t][form]["dockq"] for t in META if form in by[t]]
        r = stats.spearmanr(nov, dq)
        w(f"- {form.upper()}: Spearman(CDR-H3 novelty, DockQ) = **{r.statistic:+.3f}**, p = {r.pvalue:.3f}")
    w()
    w("If anything the sign is positive — the *most* novel antibody (9JBQ, 21.4%) and the least "
      "(8RWB, 44.4%) both failed, and the one success sits in the middle. Antibody–antigen docking "
      "is simply hard once the answer is not in the training data.")
    w()

    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
