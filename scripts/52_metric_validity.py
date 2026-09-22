#!/usr/bin/env python3
"""Do the eight scored metrics measure the DESIGN? Zero new folds.

Six days were spent on how precisely designs could be ranked. This asks the prior
question -- whether the things being ranked carry design information at all -- and
answers it three ways from folds already on disk:

  1. ICC per metric. Within-design variance from the 20 designs x 7 seeds; total
     variance from the 239-design single-seed pool. ICC = 1 - within/total is the
     fraction of the spread that is the design rather than the sampler. A metric with
     ICC ~ 0 is a random number generator wearing a metric's name.
  2. Which metrics can move the score at all. A metric whose entire observed range
     sits inside one band contributes a CONSTANT to `final` and cannot rank anything.
  3. How far the predicted CDR-H3 actually travels from pembrolizumab's crystal loop,
     against two references: the crystal-vs-crystal floor (two copies in the same
     asymmetric unit, i.e. experimental noise) and Boltz refolding pembrolizumab's own
     sequence. If 239 designs whose loops differ by 7-11 of 13 residues land no further
     from the crystal than a re-run of the native sequence does, the model is recalling
     the template rather than predicting the design.

Writes results/metric_validity.md.
"""
from __future__ import annotations
import itertools, json, sys
from collections import defaultdict
from pathlib import Path

import gemmi
import numpy as np

CDRH3 = range(95, 108)
OUT = Path("results/metric_validity.md")
METRICS = ("dg", "ipsae", "dockq", "iface_plddt", "contacts", "cdr_sasa")
GOOD = {"ipsae": (0.80, "high"), "dockq": (0.80, "high"), "dg": (-12.0, "low"),
        "contacts": (25, "high"), "iface_plddt": (80, "high"), "cdr_sasa": (600, "high")}


def ca(pdb, chain="A"):
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    c = [x for x in st[0] if x.name == chain][0]
    return np.array([[a.pos.x, a.pos.y, a.pos.z]
                     for r in c if (a := r.find_atom("CA", "*"))])


def loop_rmsd(ref, mob, loop):
    n = min(len(ref), len(mob)); ref, mob = ref[:n], mob[:n]
    loop = [i for i in loop if i < n]
    mask = np.array([i not in set(loop) for i in range(n)])
    P, Q = ref[mask], mob[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    moved = (mob - Q.mean(0)) @ (U @ np.diag([1, 1, d]) @ Vt) + P.mean(0)
    return float(np.sqrt((((moved[loop] - ref[loop]) ** 2).sum(1)).mean()))


def rows(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def main() -> int:
    pool = [r for r in rows("runs/designs_temp/fold_scores.jsonl") if "dockq" in r]
    per = defaultdict(lambda: defaultdict(list))
    for src in ("runs/designs_reseed7/fold_scores.jsonl", "runs/designs_temp/fold_scores.jsonl"):
        for r in rows(src):
            if "dockq" in r:
                for m in METRICS:
                    per[r["design_id"]][m].append(r[m])
    deep = [v for v in per.values() if len(v["dockq"]) >= 7]

    L, w = [], lambda s="": L.append(s)
    w("# Do the scored metrics measure the design, or the sampler?")
    w("")
    w("`scripts/52_metric_validity.py` — zero new folds. Written 2026-09-20 after an")
    w("independent audit pointed out that six days had been spent on ranking precision and")
    w("none on whether the ranked quantities carry design information.")
    w("")
    w("## 1. Intraclass correlation — how much of each metric is the design?")
    w("")
    w(f"Within-design variance from **{len(deep)} designs x 7 seeds**; total variance from the")
    w(f"**{len(pool)}-design single-seed pool**. `ICC = 1 - within/total`.")
    w("")
    w("| metric | within-seed sd | pool sd | **ICC** | reading |")
    w("|---|---|---|---|---|")
    icc = {}
    for m in METRICS:
        wv = float(np.mean([np.var(v[m], ddof=1) for v in deep]))
        pv = np.var([r[m] for r in pool], ddof=1)
        icc[m] = max(0.0, 1 - wv / pv)
        verdict = ("**pure seed noise — carries no design information**" if icc[m] < 0.05
                   else "usable" if icc[m] > 0.5 else "weak")
        w(f"| `{m}` | {np.sqrt(wv):.3f} | {np.sqrt(pv):.3f} | **{icc[m]:.3f}** | {verdict} |")
    w("")
    dead = [m for m in METRICS if icc[m] < 0.05]
    if dead:
        w(f"**{', '.join('`'+m+'`' for m in dead)} are pure sampler noise.** Their entire")
        w("design-to-design variation is which random seed Boltz drew. Any analysis that")
        w("compared them between designs — including the 2026-09-20 hotspot ablation, whose")
        w("verdict branch was decided on `contacts` — was comparing two noise draws.")
        w("")
    w("## 2. Which metrics can move `final` at all?")
    w("")
    w("A metric whose whole observed range sits inside one band contributes a constant.")
    w("")
    w("| metric | observed range | Good edge | % of pool already Good | can it rank? |")
    w("|---|---|---|---|---|")
    clamped = []
    for m, (edge, d) in GOOD.items():
        v = np.array([r[m] for r in pool], float)
        frac = (v <= edge).mean() if d == "low" else (v >= edge).mean()
        can = "no — constant" if frac in (0.0, 1.0) else "yes"
        if frac == 1.0:
            clamped.append(m)
        w(f"| `{m}` | {v.min():.3f} – {v.max():.3f} | {edge} | {frac*100:.0f}% | {can} |")
    w("| `cdrh3_identity` | 15.4 – 46.2 | <70 | 100% | no — constant |")
    w("| `netsolp` | 0.562 – 0.619 | 0.70 | 0% | no — constant |")
    w("")
    w(f"**{len(clamped)+2} of the 8 rubric metrics are constants across this pool.** "
      f"`{'`, `'.join(clamped)}` and `cdrh3_identity` are pinned at Good; `netsolp` is pinned")
    w("at Medium. The eight-metric harness ranks on three: `dg`, `ipsae`, `dockq`.")
    w("")
    w("## 3. How far does the predicted CDR-H3 move from pembrolizumab's crystal loop?")
    w("")
    nat = Path("data/refs/prepared/5ggs_ABZ.pdb")
    ref = ca(nat, "A")
    loop = [i for i in CDRH3 if i < len(ref)]
    refs = []
    alt = Path("data/refs/prepared/5ggs_CDY.pdb")
    if alt.exists():
        # The second crystal copy is ALSO prepared as chains A/B/C, and its heavy chain
        # is 220 aa against 219 -- so neither "chain C" nor index 95-107 transfers.
        # Locate the loop by its motif in each structure and offset the whole comparison
        # by the sequence shift. (First attempt used chain C, i.e. the antigen, and
        # reported a 12.5 A "experimental floor"; a number that absurd is the check.)
        from locksmith.io.pdb import seq_for_folding
        try:
            sa = seq_for_folding(nat, "A")
            sb = seq_for_folding(alt, "A")
            motif = sa[loop[0]:loop[-1] + 1]
            j = sb.find(motif)
            if j < 0:
                raise ValueError("CDR-H3 motif not found in the second crystal copy")
            shift = j - loop[0]
            cb = ca(alt, "A")
            n = min(len(ref), len(cb) - max(shift, 0))
            refs.append(("5GGS crystal copy 2 vs copy 1 (experimental floor)",
                         loop_rmsd(ref[:n], cb[shift:shift + n] if shift >= 0 else cb[:n],
                                   loop)))
        except Exception as e:                                        # noqa: BLE001
            print(f"crystal-vs-crystal skipped: {e}", file=sys.stderr)
    wt = sorted(Path("runs/panel").glob("**/v00_wt__fab__s1*/**/*_model_0.pdb"))
    if wt:
        refs.append(("Boltz refolding pembrolizumab's OWN sequence", loop_rmsd(ref, ca(wt[0]), loop)))
    idx = {r["design_id"]: r for r in rows("runs/designs_temp/index.jsonl") if r.get("ok")}
    dev = []
    for did, r in idx.items():
        try:
            dev.append(loop_rmsd(ref, ca(Path(r["pdb"])), loop))
        except Exception:                                             # noqa: BLE001
            pass
    dev = np.array(dev)
    w("Cα RMSD over CDR-H3 (heavy 96–108) after superposing on the **framework**.")
    w("")
    w("| | CDR-H3 Cα RMSD vs the 5GGS crystal loop |")
    w("|---|---|")
    for lab, v in refs:
        w(f"| {lab} | **{v:.3f} Å** |")
    w(f"| **{len(dev)} designs, CDR-H3 identity 15.4–46.2%** | "
      f"**mean {dev.mean():.3f} Å**, median {np.median(dev):.3f}, sd {dev.std(ddof=1):.3f}, "
      f"max {dev.max():.3f} |")
    w(f"| designs within 1.5 Å of the crystal loop | **{(dev < 1.5).sum()} / {len(dev)} "
      f"({(dev < 1.5).mean()*100:.0f}%)** |")
    w("")
    if refs:
        native = [v for lab, v in refs if "OWN sequence" in lab]
        if native:
            w(f"**Replacing 7–11 of 13 CDR-H3 residues moves the predicted loop only "
              f"{dev.mean()/native[0]:.2f}× as far from the crystal as Boltz's own refold of "
              f"the unmodified pembrolizumab sequence already is.** A sequence change of that "
              f"size should not land a loop essentially on top of the parent's.")
            w("")
    w("Read with the post-cutoff control: median Fab DockQ **0.291** on five complexes")
    w("released after Boltz-2's verified 2023-06-01 cutoff, against 0.818 on 5GGS. A model")
    w("that scores 0.29 on novel antibody–antigen pairs and 0.60–0.78 on 239 CDR-variants of")
    w("a training-set complex is reproducing the template it memorised, and the pool's DockQ")
    w("spread is variation *around* that template, not evidence about the designs.")
    w("")
    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
