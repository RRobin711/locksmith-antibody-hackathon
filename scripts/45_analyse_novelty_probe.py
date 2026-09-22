#!/usr/bin/env python3
"""Analyse the novelty probe. Writes results/novelty_probe.md."""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.types import Provenance, Structure

OUT = Path("results/novelty_probe.md")
INDEX = Path("runs/novelty_probe/index.jsonl")
CACHE = Path("runs/novelty_probe/scores.jsonl")
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")
POOL_MEAN, POOL_MAX, SELF_REFOLD = 0.705, 0.777, 0.818
ARMS = [("A_k4_nocontact", "A — 4 zero-contact positions", 69.2, 0),
        ("B_k6_nocontact", "B — 6 zero-contact positions", 53.8, 0),
        ("C_k6_paratope",  "C — 6 paratope positions",     53.8, 227)]


def rows(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def boot_ci(v, n=10000):
    v = np.asarray(v, float)
    if len(v) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(0)
    m = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return tuple(np.percentile(m, [2.5, 97.5]))


def main() -> int:
    idx = [r for r in rows(INDEX) if r.get("ok")]
    if not idx:
        print("novelty probe: nothing on disk, skipping"); return 0
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
            rec["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
            rec["dockq"] = dockq.compute(
                st, NATIVE, allowed_mismatches=c["dockq_allowed_mismatches"])["dockq"].value
        except Exception as e:                                        # noqa: BLE001
            rec["error"] = str(e)[:300]
        with CACHE.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        have[r["label"]] = rec
        print(f"  scored {r['label']}: dockq={rec.get('dockq')}", flush=True)

    by = defaultdict(list)
    for r in idx:
        s = have.get(r["label"], {})
        if "dockq" in s:
            by[r["arm"]].append(s)

    L, w = [], lambda s="": L.append(s)
    w("# What does the rubric's novelty metric actually measure?")
    w("")
    w("`scripts/43_novelty_probe_generate.py` → `44_novelty_probe_fold.py` → this. "
      "Pre-registered in [[prereg_2026-09-20_novelty_probe|the novelty-probe "
      "pre-registration]] before any fold ran.")
    w("")
    w("Only the listed CDR-H3 positions are redesigned; H1, H2, the light chain and the "
      "antigen are native, so the **paratope is the only thing that varies between arms**. "
      "The native residue is forbidden at each designed position, so identity is exact.")
    w("")
    w("| arm | positions | antigen contacts touched | CDR-H3 identity | novelty band | n | DockQ mean | 95% CI | ipSAE | ΔG |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    stat = {}
    for key, lab, ident, con in ARMS:
        g = by.get(key, [])
        if not g:
            continue
        dq = [x["dockq"] for x in g]
        lo, hi = boot_ci(dq)
        stat[key] = dq
        w(f"| **{lab}** | {len(g)} designs | **{con}** | **{ident}%** | Good | {len(g)} "
          f"| **{np.mean(dq):.3f}** | [{lo:.3f}, {hi:.3f}] "
          f"| {np.mean([x['ipsae'] for x in g]):.3f} "
          f"| {np.mean([x['dg'] for x in g]):+.1f} |")
    w("")
    w(f"Reference points: 239-design pool mean DockQ **{POOL_MEAN:.3f}**, pool max "
      f"**{POOL_MAX:.3f}**, pembrolizumab self-refold **{SELF_REFOLD:.3f}**.")
    w("")

    if "B_k6_nocontact" in stat and "C_k6_paratope" in stat:
        b, cc = stat["B_k6_nocontact"], stat["C_k6_paratope"]
        u = stats.mannwhitneyu(b, cc, alternative="two-sided")
        diff = float(np.mean(b) - np.mean(cc))
        w("## The comparison the whole arm exists for")
        w("")
        w("Arms B and C carry **identical** `cdrh3_identity` of 53.8%, the same Good band, "
          "the same novelty sub-score and the same contribution to `final`. They differ "
          "only in *which* CDR-H3 positions were allowed to change.")
        w("")
        w("| | B (paratope intact) | C (paratope redesigned) | difference |")
        w("|---|---|---|---|")
        w(f"| DockQ mean | **{np.mean(b):.3f}** | **{np.mean(cc):.3f}** | **{diff:+.3f}** |")
        w(f"| ipSAE mean | {np.mean([x['ipsae'] for x in by['B_k6_nocontact']]):.3f} "
          f"| {np.mean([x['ipsae'] for x in by['C_k6_paratope']]):.3f} | |")
        w(f"| `cdrh3_identity` | 53.8% | 53.8% | **0.0 — the rubric sees nothing** |")
        w(f"| Mann–Whitney U | | | U={u.statistic:.0f}, p={u.pvalue:.2g} |")
        w("")
        if diff >= 0.10 and u.pvalue < 0.05:
            w(f"**H2 confirmed.** A DockQ gap of **{diff:.3f}** — "
              f"{diff/0.018:.0f} times the seed noise sd of 0.018 — is completely invisible "
              "to the scored novelty metric. The rubric's novelty axis measures **sequence "
              "distance, not interface novelty**: a design can take the full novelty band "
              "while leaving the entire paratope untouched, and the metric cannot "
              "distinguish it from one that destroys the paratope.")
        elif diff < 0.10:
            w(f"**H2 not confirmed** — the gap is only {diff:+.3f}. Either the predictor is "
              "insensitive to paratope identity on this complex (a finding about Boltz that "
              "would undercut DockQ as evidence here), or CDR-H3 contributes less to this "
              "interface than the contact counts imply. Report as a null, not as support.")
        w("")

    best = max(((k, max(v)) for k, v in stat.items()), key=lambda kv: kv[1], default=None)
    if best:
        w("## H3 — does this reach the Good DockQ band?")
        w("")
        w(f"Best single design: **{best[1]:.3f}** ({best[0]}). Good needs ≥ 0.80.")
        w("")
        if best[1] >= 0.80:
            w("**Reached.** `dockq` moves Medium → Good, worth **+2.50** on `final` "
              "(87.5 → 90.0). Given NetSolP is pinned at Medium for any "
              "pembrolizumab-framework Fab ([[rubric_headroom|headroom audit]]), 90.0 is "
              "the practical ceiling on this scaffold and this is how it is reached.")
        else:
            w(f"**Not reached** — {0.80-best[1]:.3f} short. The extrapolation in the headroom "
              "audit predicted identity in this band would get there; it did not, so that "
              "extrapolation is **withdrawn as a prediction** and the observed relationship "
              "is reported instead.")
        w("")
    w("## Declaration")
    w("")
    w("**These are rubric probes, not design candidates.** An arm-A molecule is a near-copy "
      "of pembrolizumab with four substitutions at positions that touch nothing. Proposing "
      "one because it scores well would be gaming a metric this experiment exists to show "
      "is gameable. M3 is closed and `mpnn_T0.5_s104_036` remains the named design "
      "whatever the numbers above say.")
    w("")
    w("**Note for Challenge 2:** its binding mean has no DockQ — no metric compares against "
      "a reference structure. Nothing in the Challenge 2 rubric could have detected the "
      "B-versus-C difference at all.")
    w("")
    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
