#!/usr/bin/env python3
"""Correlate this project's metrics against MEASURED ddG. Writes results/skempi_validity.md."""
from __future__ import annotations
import json, sys
from pathlib import Path

import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.types import Provenance, Structure

NATIVE = Structure(pdb=Path("data/refs/skempi/3hfm_ABC.pdb"),
                   provenance=Provenance.EXPERIMENT, label="3HFM")
CACHE = Path("runs/skempi_3hfm/scores.jsonl")
OUT = Path("results/skempi_validity.md")
METRICS = [("dg", "PRODIGY ΔG", "low"), ("ipsae", "ipSAE", "high"),
           ("dockq", "DockQ vs the 3HFM crystal", "high"),
           ("iface_plddt", "interface pLDDT", "high"), ("contacts", "contacts", "high")]


def rows(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def main() -> int:
    idx = [r for r in rows("runs/skempi_3hfm/index.jsonl") if r.get("ok")]
    if len(idx) < 15:
        print(f"only {len(idx)} folds; skipping"); return 0
    cfg = load(); c = cfg.conventions
    have = {r["label"]: r for r in rows(CACHE)}
    for r in idx:
        if r["label"] in have:
            continue
        st = Structure(pdb=Path(r["pdb"]), provenance=Provenance.PREDICTION,
                       pae=Path(r["pae"]), label=r["label"], predictor="boltz2")
        rec = {"label": r["label"]}
        try:
            rec.update({k: v.value for k, v in prodigy.compute(st).items()})
            rec["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                         dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
            rec["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
            rec["dockq"] = dockq.compute(
                st, NATIVE, allowed_mismatches=c["dockq_allowed_mismatches"],
                interface_agg=c.get("dockq_interface_agg", "min"))["dockq"].value
        except Exception as e:                                        # noqa: BLE001
            rec["error"] = str(e)[:300]
        with CACHE.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        have[r["label"]] = rec
        print(f"  scored {r['label']}", flush=True)

    wt = [have[r["label"]] for r in idx if r["mut"] == "WT" and "dg" in have.get(r["label"], {})]
    mut = [(r, have[r["label"]]) for r in idx
           if r["mut"] != "WT" and "dg" in have.get(r["label"], {})]
    if not mut:
        print("no scored mutants"); return 0

    L, w = [], lambda s="": L.append(s)
    w("# Do these metrics track measured binding affinity?")
    w("")
    w("`scripts/53_skempi_fold.py` + this. **The only experiment in this project that "
      "compares a predicted number to a laboratory measurement.** Everything else measures "
      "how precisely the pipeline reproduces itself.")
    w("")
    w("System: **3HFM**, HyHEL-10 Fab vs hen egg-white lysozyme, from SKEMPI 2.0. "
      f"{len(mut)} single mutants folded at one seed, wild type at {len(wt)} seeds. "
      "`ddG = RT ln(Kd_mut/Kd_wt)`; **positive ddG means the mutation weakens binding**, so a "
      "metric that tracks affinity should correlate NEGATIVELY with ddG when higher is better.")
    w("")
    if wt:
        w("## Noise floor, measured on this complex")
        w("")
        w("| metric | WT mean | seed sd (n=%d) |" % len(wt))
        w("|---|---|---|")
        for k, lab, _ in METRICS:
            v = [x[k] for x in wt if k in x]
            if len(v) > 1:
                w(f"| {lab} | {np.mean(v):.3f} | {np.std(v, ddof=1):.3f} |")
        w("")
    ddg = np.array([r["ddg"] for r, _ in mut], float)
    cens = np.array([bool(r["censored"]) for r, _ in mut])
    w("## Correlation with measured ddG")
    w("")
    w(f"All {len(mut)} mutants, and separately the {int((~cens).sum())} with |ddG| <= 6 "
      "kcal/mol (the rest sit at an assay detection limit, so their magnitudes are not real "
      "numbers even though their rank order is).")
    w("")
    w("| metric | ρ (all) | p | ρ (|ddG|≤6) | p | expected sign |")
    w("|---|---|---|---|---|---|")
    for k, lab, direction in METRICS:
        v = np.array([s.get(k, np.nan) for _, s in mut], float)
        ok = ~np.isnan(v)
        if ok.sum() < 10:
            continue
        r1 = stats.spearmanr(ddg[ok], v[ok])
        sub = ok & ~cens
        r2 = stats.spearmanr(ddg[sub], v[sub]) if sub.sum() >= 10 else None
        exp = "negative" if direction == "high" else "positive"
        w(f"| {lab} | **{r1.statistic:+.3f}** | {r1.pvalue:.2g} | "
          f"{r2.statistic:+.3f} | {r2.pvalue:.2g} | {exp} |"
          if r2 else
          f"| {lab} | **{r1.statistic:+.3f}** | {r1.pvalue:.2g} | — | — | {exp} |")
    w("")
    n = len(mut)
    z = 2.80 / np.sqrt(n - 3)
    w(f"**A null is a bound.** At n={n} the smallest effect detectable at 80% power "
      f"(α=0.05) is ρ ≈ **{np.tanh(z):.2f}**, so any metric reported as uncorrelated means "
      f"*no monotone relationship stronger than that*.")
    w("")
    w("## Reading")
    w("")
    w("A metric that ranks designs for binding must, at minimum, rank *known* affinity "
      "changes on a complex of the same kind. This is the weakest possible version of that "
      "test — single point mutations, one seed, a complex the predictor has memorised — and "
      "it is still the only external check the project has. Whatever the numbers above say, "
      "they bound what the whole scoring stack can claim.")
    w("")
    w("Caveat, stated rather than buried: 3HFM predates Boltz-2's 2023-06-01 cutoff, so the "
      "wild-type pose is memorised. That is acceptable for a ddG *ranking* test — the question "
      "is whether the scores move correctly when an experimentally important residue is "
      "removed — but it means a positive result would need re-testing on a post-cutoff complex "
      "before being believed.")
    w("")
    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
