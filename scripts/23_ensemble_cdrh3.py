#!/usr/bin/env python3
"""Rank stability, the winner's curse, and the CDR-H3 conformational ensemble.

All three come out of the same folds, because re-seeding a diffusion model IS
sampling conformations. Writes results/reseed_ensemble.md.

THE ENSEMBLE READOUT, AND WHY CDR-H3
------------------------------------
CDR-H3 is the most conformationally heterogeneous part of an antibody: longest
loop, no germline template, and the dominant antigen-contact region. Reporting a
single predicted structure plus one confidence number for it is exactly the
representation Locksmith argues is wrong. Given the seeds are being folded
anyway, the spread across them is free.

Superposition is on the FRAMEWORK, not on the loop. Superposing on the loop would
hide the thing being measured -- whether the loop sits in the same place relative
to the rest of the molecule.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import gemmi
import numpy as np
import pandas as pd
from scipy import stats

from locksmith.config import load
from locksmith.metrics import dockq, ipsae
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

BASE = Path("designs/baseline_mpnn/designs.parquet")
DESIGNS = Path("designs/baseline_mpnn/designs.json")
RESEED = Path("runs/designs_reseed/index.jsonl")
BASEIDX = Path("runs/designs_baseline/index.jsonl")
OUT = Path("results/reseed_ensemble.md")
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")
CDRH3 = range(95, 108)          # 0-based indices into the heavy chain
SCORECACHE = Path("runs/designs_reseed/scores.jsonl")


def score_one(pdb: Path, pae: Path, label: str, cfg) -> dict:
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae,
                   label=label, predictor="boltz2")
    conv = cfg.conventions
    out = {}
    ip = ipsae.compute(st, pae_cutoff=conv["ipsae_pae_cutoff"],
                       dist_cutoff=conv["ipsae_dist_cutoff"])["ipsae"]
    dq = dockq.compute(st, NATIVE,
                       allowed_mismatches=conv["dockq_allowed_mismatches"])["dockq"]
    out["ipsae"], out["dockq"] = ip.value, dq.value
    return out


def ca_of_chain(pdb: Path, chain="A"):
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    ch = [c for c in st[0] if c.name == chain][0]
    ca, res = [], []
    for r in ch:
        a = r.find_atom("CA", "*")
        if a:
            ca.append([a.pos.x, a.pos.y, a.pos.z]); res.append(r)
    return np.array(ca), res


def superpose_on_framework(ref_ca, mob_ca, loop_idx):
    """Kabsch on framework CAs only, then apply to everything."""
    mask = np.array([i not in set(loop_idx) for i in range(len(ref_ca))])
    P, Q = ref_ca[mask], mob_ca[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    moved = (mob_ca - Q.mean(0)) @ R + P.mean(0)
    fw_rmsd = float(np.sqrt(((moved[mask] - ref_ca[mask]) ** 2).sum(1).mean()))
    return moved, fw_rmsd


def main() -> int:
    cfg = load()
    base = pd.read_parquet(BASE)
    baseidx = {json.loads(l)["design_id"]: json.loads(l)
               for l in BASEIDX.read_text().splitlines() if l.strip()}
    rows = [json.loads(l) for l in RESEED.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r.get("ok")]

    cached = {}
    if SCORECACHE.exists():
        cached = {json.loads(l)["label"]: json.loads(l)
                  for l in SCORECACHE.read_text().splitlines() if l.strip()}

    per = defaultdict(dict)          # design -> seed -> metrics
    paths = defaultdict(dict)
    for did, r in baseidx.items():
        if r.get("ok"):
            b = base[base.design_id == did]
            if not b.empty:
                per[did][1] = {"dockq": float(b.dockq.iloc[0]),
                               "ipsae": float(b.ipsae.iloc[0]),
                               "final": float(b.final_score.iloc[0])}
                paths[did][1] = Path(r["pdb"])
    for r in rows:
        did, seed = r["design_id"], r["seed"]
        if r["label"] in cached:
            m = cached[r["label"]]
        else:
            m = score_one(Path(r["pdb"]), Path(r["pae"]), r["label"], cfg)
            m["label"] = r["label"]
            with SCORECACHE.open("a") as f:
                f.write(json.dumps(m) + "\n")
        b = base[base.design_id == did].iloc[0]
        raw = {k: (None if pd.isna(b.get(k)) else b.get(k)) for k in cfg.bands()}
        raw["dockq"], raw["ipsae"] = m["dockq"], m["ipsae"]
        s = evaluate(raw, 1, cfg)
        per[did][seed] = {"dockq": m["dockq"], "ipsae": m["ipsae"], "final": s.final}
        paths[did][seed] = Path(r["pdb"])

    shortlist = [d for d in json.loads(
        Path("designs/baseline_mpnn/reseed_shortlist.json").read_text()) if len(per[d]) >= 2]

    L = []
    def w(s=""):
        L.append(s)
    w("# Re-seeding the baseline shortlist — stability, winner's curse, CDR-H3 ensemble")
    w()
    w(f"Top tier of the baseline: {len(shortlist)} designs all at `final` 87.5, so the DockQ "
      f"tiebreaker alone orders them. Re-folded as Fab on seeds 2 and 3 with the same driver, "
      f"MSA and scoring path. **Prediction going in:** median adjacent DockQ gap 0.011 against a "
      f"panel-measured Fab seed sd of 0.018 → this ordering should be substantially noise.")
    w()

    # ---------------------------------------------------------------- spread
    w("## 1. Per-design spread across seeds")
    w()
    w("| design | DockQ mean | DockQ sd | DockQ range | ipSAE mean | ipSAE sd | final values |")
    w("|---|---|---|---|---|---|---|")
    within = []
    for d in shortlist:
        seeds = per[d]
        dq = np.array([seeds[s]["dockq"] for s in sorted(seeds)])
        ip = np.array([seeds[s]["ipsae"] for s in sorted(seeds)])
        fin = sorted({seeds[s]["final"] for s in sorted(seeds)})
        within.append(dq.var(ddof=1))
        w(f"| `{d}` | {dq.mean():.3f} | **{dq.std(ddof=1):.4f}** | "
          f"{dq.min():.3f}–{dq.max():.3f} | {ip.mean():.3f} | {ip.std(ddof=1):.4f} | "
          f"{', '.join(f'{x:.1f}' for x in fin)} |")
    s2w = float(np.mean(within)); sw = s2w ** 0.5
    means = np.array([np.mean([per[d][s]["dockq"] for s in per[d]]) for d in shortlist])
    s2o = float(base[base.design_id.isin(shortlist)].dockq.var(ddof=1))
    rel = max(0.0, 1 - s2w / s2o) if s2o else float("nan")
    w()
    w(f"- pooled seed sd (designs) = **{sw:.4f}**  (panel, on mutants: 0.0181)")
    w(f"- between-design sd in the top tier = {s2o**0.5:.4f}")
    w(f"- **implied reliability of the DockQ ordering = {rel:.3f}**  "
      f"(attenuation ceiling √r = {rel**0.5:.3f})")
    w()

    # ---------------------------------------------------------------- stability
    w("## 2. Does the ranking survive re-seeding?")
    w()
    seed_ranks = {}
    for s in (1, 2, 3):
        avail = [d for d in shortlist if s in per[d]]
        if len(avail) >= 4:
            seed_ranks[s] = {d: per[d][s]["dockq"] for d in avail}
    ss = sorted(seed_ranks)
    w("| seed pair | Spearman rank correlation | top-1 agrees? |")
    w("|---|---|---|")
    for a in range(len(ss)):
        for b2 in range(a + 1, len(ss)):
            sa, sb = ss[a], ss[b2]
            common = [d for d in shortlist if d in seed_ranks[sa] and d in seed_ranks[sb]]
            r = stats.spearmanr([seed_ranks[sa][d] for d in common],
                                [seed_ranks[sb][d] for d in common])
            wa = max(common, key=lambda d: seed_ranks[sa][d])
            wb = max(common, key=lambda d: seed_ranks[sb][d])
            w(f"| seed {sa} vs {sb} | **{r.statistic:+.3f}** (p={r.pvalue:.3f}) | "
              f"{'yes' if wa == wb else f'no — {wa.split(chr(95))[-1]} vs {wb.split(chr(95))[-1]}'} |")
    w()
    winners = {s: max(seed_ranks[s], key=lambda d: seed_ranks[s][d]) for s in ss}
    w(f"- per-seed DockQ winner: " + ", ".join(f"seed {s} → `{winners[s]}`" for s in ss))
    mean_rank = sorted(shortlist, key=lambda d: -np.mean([per[d][s]["dockq"] for s in per[d]]))
    w(f"- winner by **3-seed mean**: `{mean_rank[0]}`")
    w()

    # ---------------------------------------------------------------- winner's curse
    w("## 3. The winner's curse, quantified")
    w()
    s1 = {d: per[d][1]["dockq"] for d in shortlist if 1 in per[d]}
    top1 = max(s1, key=lambda d: s1[d])
    regress = {d: np.mean([per[d][s]["dockq"] for s in per[d]]) - s1[d] for d in shortlist}
    mean_reg = float(np.mean(list(regress.values())))
    w(f"- seed-1 top design: `{top1}` at DockQ **{s1[top1]:.3f}**")
    w(f"- its 3-seed mean: **{np.mean([per[top1][s]['dockq'] for s in per[top1]]):.3f}** "
      f"→ regression **{regress[top1]:+.4f}**")
    w(f"- mean regression across all {len(shortlist)} re-seeded designs: **{mean_reg:+.4f}**")
    w(f"- **winner's-curse excess = {regress[top1] - mean_reg:+.4f} DockQ**")
    w()
    w("That excess is the selection bias: the amount by which picking the argmax of a noisy "
      "measurement overstates it, over and above any drift shared by every design. Any future "
      "\"our best design scored X\" has to be discounted by it.")
    w()

    # ---------------------------------------------------------------- ensemble
    w("## 4. The CDR-H3 conformational ensemble")
    w()
    w("Superposition is on the **framework** CAs, never on the loop: superposing on the loop "
      "would hide exactly what is being measured — whether CDR-H3 sits in the same place "
      "relative to the rest of the molecule. Loop = heavy-chain positions 96–108 (13 residues).")
    w()
    w("| design | framework RMSD | **CDR-H3 RMSD** | CDR-H3 max dev | mean loop pLDDT | pLDDT sd | DockQ mean |")
    w("|---|---|---|---|---|---|---|")
    ens = {}
    for d in shortlist:
        seeds = sorted(paths[d])
        if len(seeds) < 2:
            continue
        ref_ca, ref_res = ca_of_chain(paths[d][seeds[0]])
        loop = [i for i in CDRH3 if i < len(ref_ca)]
        devs, fws, plddts = [], [], []
        for s in seeds[1:]:
            mob_ca, _ = ca_of_chain(paths[d][s])
            n = min(len(ref_ca), len(mob_ca))
            moved, fw = superpose_on_framework(ref_ca[:n], mob_ca[:n], loop)
            dev = np.sqrt(((moved[loop] - ref_ca[loop]) ** 2).sum(1))
            devs.append(dev); fws.append(fw)
        for s in seeds:
            _, res = ca_of_chain(paths[d][s])
            plddts.append([res[i].find_atom("CA", "*").b_iso for i in loop])
        dev = np.concatenate(devs)
        pl = np.array(plddts)
        dqm = float(np.mean([per[d][s]["dockq"] for s in per[d]]))
        ens[d] = {"cdrh3_rmsd": float(np.sqrt((dev ** 2).mean())),
                  "max_dev": float(dev.max()),
                  "plddt": float(pl.mean()), "plddt_sd": float(pl.mean(0).std()),
                  "dockq": dqm}
        w(f"| `{d}` | {np.mean(fws):.2f} Å | **{ens[d]['cdrh3_rmsd']:.2f} Å** | "
          f"{ens[d]['max_dev']:.2f} Å | {ens[d]['plddt']:.1f} | {ens[d]['plddt_sd']:.1f} | "
          f"{dqm:.3f} |")
    w()
    if len(ens) >= 4:
        k = list(ens)
        r1 = stats.spearmanr([ens[d]["cdrh3_rmsd"] for d in k], [ens[d]["dockq"] for d in k])
        r2 = stats.spearmanr([ens[d]["cdrh3_rmsd"] for d in k], [ens[d]["plddt"] for d in k])
        w(f"- Does a tight CDR-H3 ensemble track a better score? "
          f"Spearman(CDR-H3 RMSD, DockQ) = **{r1.statistic:+.3f}** (p={r1.pvalue:.3f})")
        w(f"- Does pLDDT know the loop is heterogeneous? "
          f"Spearman(CDR-H3 RMSD, loop pLDDT) = **{r2.statistic:+.3f}** (p={r2.pvalue:.3f})")
        w()
        tight = min(ens, key=lambda d: ens[d]["cdrh3_rmsd"])
        loose = max(ens, key=lambda d: ens[d]["cdrh3_rmsd"])
        w(f"- tightest ensemble: `{tight}` at {ens[tight]['cdrh3_rmsd']:.2f} Å; "
          f"most heterogeneous: `{loose}` at {ens[loose]['cdrh3_rmsd']:.2f} Å — a "
          f"{ens[loose]['cdrh3_rmsd']/max(ens[tight]['cdrh3_rmsd'],1e-9):.1f}× spread across "
          f"designs that are indistinguishable on the rubric.")
    w()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
