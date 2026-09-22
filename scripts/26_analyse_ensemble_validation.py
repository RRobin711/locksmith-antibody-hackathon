#!/usr/bin/env python3
"""Does ensemble tightness earn a place in selection? Analysis per the pre-registration.

Writes results/ensemble_validation.md.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import gemmi
import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.score import evaluate

POOL = Path("designs/wide_mpnn/designs.json")
OUT = Path("runs/designs_wide")
FOLDSC = OUT / "fold_scores.jsonl"
SEQSC = OUT / "seq_scores.jsonl"
REPORT = Path("results/ensemble_validation.md")
CDRH3 = range(95, 108)
HYDROPHOBIC = set("AVILMFWCY")
AROMATIC = set("FWY")
POS, NEG = set("KR"), set("DE")


def ca_of_chain(pdb: Path, chain="A"):
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    ch = [c for c in st[0] if c.name == chain][0]
    ca, res = [], []
    for r in ch:
        a = r.find_atom("CA", "*")
        if a:
            ca.append([a.pos.x, a.pos.y, a.pos.z]); res.append(r)
    return np.array(ca), res


def superpose_on_framework(ref, mob, loop):
    mask = np.array([i not in set(loop) for i in range(len(ref))])
    P, Q = ref[mask], mob[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return (mob - Q.mean(0)) @ R + P.mean(0)


def ensemble_rmsd(paths: list[Path]) -> tuple[float, float]:
    """Pairwise CDR-H3 CA deviation after framework superposition."""
    cas = [ca_of_chain(p)[0] for p in paths]
    n = min(len(c) for c in cas)
    cas = [c[:n] for c in cas]
    loop = [i for i in CDRH3 if i < n]
    devs = []
    for i in range(len(cas)):
        for j in range(i + 1, len(cas)):
            moved = superpose_on_framework(cas[i], cas[j], loop)
            devs.append(np.sqrt(((moved[loop] - cas[i][loop]) ** 2).sum(1)))
    d = np.concatenate(devs)
    return float(np.sqrt((d ** 2).mean())), float(d.max())


def features(heavy: str, mpnn_score: float) -> dict:
    h3 = heavy[95:108]
    n = len(h3)
    return {"mpnn_score": mpnn_score,
            "cdrh3_len": n,
            "net_charge": sum(c in POS for c in h3) - sum(c in NEG for c in h3),
            "hydrophobic_frac": sum(c in HYDROPHOBIC for c in h3) / n,
            "aromatic_frac": sum(c in AROMATIC for c in h3) / n,
            "gly_frac": h3.count("G") / n}


def main() -> int:
    cfg = load()
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in SEQSC.read_text().splitlines() if l.strip()}
    per = defaultdict(dict)
    for l in FOLDSC.read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if "error" not in r:
            per[r["design_id"]][r["seed"]] = r

    rows = []
    for did, d in pool.items():
        seeds = per[did]
        if len(seeds) < 3 or did not in seq:
            continue
        paths = [Path(seeds[s]["pdb"]) for s in sorted(seeds)]
        rms, mx = ensemble_rmsd(paths)
        rec = {"design_id": did, "cdrh3_rmsd": rms, "cdrh3_max_dev": mx,
               **features(d["heavy"], d["score"])}
        for m in ("dockq", "ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa"):
            v = [seeds[s][m] for s in sorted(seeds) if seeds[s].get(m) is not None]
            rec[m] = float(np.mean(v)) if v else None
            rec[f"{m}_sd"] = float(np.std(v, ddof=1)) if len(v) > 1 else None
        rec["netsolp"] = seq[did]["netsolp"]
        rec["cdrh3_identity"] = seq[did]["cdrh3_identity"]
        raw = {k: rec.get(k) for k in cfg.bands()}
        s = evaluate(raw, 1, cfg)
        rec["final"] = s.final; rec["viable"] = s.viable
        rows.append(rec)

    n = len(rows)
    L = []
    def w(x=""):
        L.append(x)

    def rho(a, b):
        x = [r[a] for r in rows if r.get(a) is not None and r.get(b) is not None]
        y = [r[b] for r in rows if r.get(a) is not None and r.get(b) is not None]
        if len(x) < 5:
            return None
        return stats.spearmanr(x, y)

    w("# Does ensemble tightness earn a place in selection?")
    w()
    w(f"Analysis exactly as fixed in [[prereg_ensemble_validation|the pre-registration]], written "
      f"before these designs were generated. **{n} designs**, ProteinMPNN `v_48_020` at "
      f"temperature 0.1, each folded as a Fab on **3 Boltz seeds**. No gating and no shortlisting "
      f"before the correlation was measured.")
    w()
    w(f"CDR-H3 ensemble RMSD is the pairwise CA deviation of positions 96–108 after superposing "
      f"on the **framework** — never on the loop, which would hide what is being measured.")
    w()

    w("## 1. The pool")
    w()
    er = np.array([r["cdrh3_rmsd"] for r in rows])
    dq = np.array([r["dockq"] for r in rows])
    w(f"| quantity | min | median | max |")
    w(f"|---|---|---|---|")
    w(f"| CDR-H3 ensemble RMSD | {er.min():.2f} Å | {np.median(er):.2f} Å | {er.max():.2f} Å |")
    w(f"| 3-seed mean DockQ | {dq.min():.3f} | {np.median(dq):.3f} | {dq.max():.3f} |")
    w(f"| `final` (3-seed mean inputs) | {min(r['final'] for r in rows):.1f} | "
      f"{np.median([r['final'] for r in rows]):.1f} | {max(r['final'] for r in rows):.1f} |")
    w(f"| viable | {sum(1 for r in rows if r['viable'])}/{n} | | |")
    w()
    w(f"Ensemble spread varies **{er.max()/er.min():.1f}×** across the pool.")
    w()

    w("## 2. PRIMARY — ensemble RMSD vs 3-seed mean DockQ")
    w()
    r = rho("cdrh3_rmsd", "dockq")
    z = np.arctanh(np.clip(r.statistic, -0.999, 0.999)); se = 1/np.sqrt(n-3)
    lo, hi = np.tanh(z-1.96*se), np.tanh(z+1.96*se)
    w(f"> **Spearman rho = {r.statistic:+.3f}**, 95% CI [{lo:+.2f}, {hi:+.2f}], "
      f"p = {r.pvalue:.3f}, n = {n}")
    w()
    if abs(r.statistic) >= 0.50 and r.pvalue < 0.05:
        verdict = "**WORTH SELECTING ON**"
    elif abs(r.statistic) < 0.30 and r.pvalue >= 0.05:
        verdict = "**DROP FROM SELECTION**"
    else:
        verdict = "**WORTH REPORTING ONLY**"
    w(f"Pre-registered verdict: {verdict}")
    w()

    w("## 3. Ensemble RMSD vs every rubric metric")
    w()
    w("| metric | Spearman | p |")
    w("|---|---|---|")
    for m in ("dockq", "ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa",
              "netsolp", "cdrh3_identity", "final"):
        rr = rho("cdrh3_rmsd", m)
        if rr:
            w(f"| `{m}` | {rr.statistic:+.3f} | {rr.pvalue:.3f} |")
    w()

    w("## 4. SECONDARY — can a cheap PRE-FOLD feature predict ensemble spread?")
    w()
    w("A feature reaching |rho| >= 0.50 at Bonferroni alpha = 0.0083 (6 tests) would be a screen "
      "for conformational stability costing **zero folds** — worth more than the primary result.")
    w()
    w("| pre-fold feature | Spearman | p | passes Bonferroni? |")
    w("|---|---|---|---|")
    hits = []
    for f in ("mpnn_score", "cdrh3_len", "net_charge", "hydrophobic_frac",
              "aromatic_frac", "gly_frac"):
        rr = rho(f, "cdrh3_rmsd")
        if not rr:
            continue
        ok = abs(rr.statistic) >= 0.50 and rr.pvalue < 0.0083
        if ok:
            hits.append(f)
        w(f"| `{f}` | {rr.statistic:+.3f} | {rr.pvalue:.3f} | {'**yes**' if ok else 'no'} |")
    w()
    w(f"Screens found: **{hits if hits else 'none'}**")
    w()

    w("## 5. Co-measurement check (already known, not the question)")
    w()
    rr = rho("cdrh3_rmsd", "dockq_sd")
    w(f"- ensemble RMSD vs DockQ sd across seeds: **{rr.statistic:+.3f}** (p={rr.pvalue:.3f})")
    w("  Both are computed from the same three structures, so this is partly mechanical, and it "
      "cannot drive selection: knowing the ensemble spread requires the 3 folds that would give "
      "the score variance directly.")
    w()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n")
    (OUT / "ensemble_table.json").write_text(json.dumps(rows, indent=2))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
