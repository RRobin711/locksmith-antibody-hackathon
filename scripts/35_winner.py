#!/usr/bin/env python3
"""Score the 7-seed shortlist, name a winner, discount it, characterise its ensemble.

FOUR THINGS HAPPEN HERE AND THEY ARE DELIBERATELY IN THIS ORDER.

1. SCORE the 120 reseed folds and combine them with the seed-1 fold each design
   already has, giving 7 seeds per shortlisted design.

2. TEST THE ASSUMPTION THE SHORTLIST WAS SIZED ON. `scripts/31` chose 20 designs at
   7 seeds over 60 at 3 by simulating i.i.d. seed noise shrinking as 1/sqrt(s). With
   only 3 seeds on the old pool that was unverifiable past s=3. Seven seeds tests it:
   if the within-design sd over 7 seeds is much larger than the 0.529 surrogate pts
   measured over 3, the noise has a systematic component and averaging stopped paying
   -- which would mean the shortlist was sized on a false premise. Reported either way.

3. NAME a winner on the 7-seed mean surrogate, then apply the WINNER'S CURSE discount.
   Selection takes an argmax over scores that are truth plus noise, so the winner is
   disproportionately a design whose noise landed high. The estimator is empirical-Bayes
   shrinkage toward the pool mean by the measured reliability:

       corrected = pool_mean + reliability x (observed - pool_mean)

   A LARGER pool makes this correction larger, not smaller, because the argmax is taken
   over more draws. The discounted number is the headline; the raw one is a by-product.

4. FRESH-SEED the winner on a seed used nowhere in selection. This is the only
   unbiased estimate available: every seed that took part in choosing the winner is
   contaminated by having been selected on.

Writes results/m3_winner.md.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import multiprocessing

import numpy as np

from locksmith.config import load
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.score import evaluate
from locksmith.select import surrogate

POOL = Path("designs/wide_temp/designs.json")
BASE = Path("runs/designs_temp")
RS = Path("runs/designs_reseed7")
FOLDSC = RS / "fold_scores.jsonl"
REPORT = Path("results/m3_winner.md")
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
FRESH_SEED = 23
METRICS = ("ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa")
WORKERS = 6
CDRH3 = range(95, 108)


def score_one(rec):
    from locksmith.config import load as _load
    from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
    from locksmith.types import Provenance, Structure
    cfg = _load(); conv = cfg.conventions
    native = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                       provenance=Provenance.EXPERIMENT, label="5GGS")
    st = Structure(pdb=Path(rec["pdb"]), provenance=Provenance.PREDICTION,
                   pae=Path(rec["pae"]), label=rec["key"], predictor="boltz2")
    out = {"key": rec["key"], "design_id": rec["design_id"], "seed": rec["seed"],
           "pdb": rec["pdb"]}
    try:
        out.update({k: v.value for k, v in prodigy.compute(st).items()})
        out["ipsae"] = ipsae.compute(st, pae_cutoff=conv["ipsae_pae_cutoff"],
                                     dist_cutoff=conv["ipsae_dist_cutoff"])["ipsae"].value
        out["iface_plddt"] = plddt.compute(st, cutoff=conv["interface_dist_cutoff"]).value
        out["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{conv['cdr_sasa_state']}"].value
        out["dockq"] = dockq.compute(st, native,
                                     allowed_mismatches=conv["dockq_allowed_mismatches"])["dockq"].value
    except Exception as e:                                      # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"[:300]
    return out


def done(path, key, require):
    if not path.exists():
        return set()
    return {json.loads(l)[key] for l in path.read_text().splitlines()
            if l.strip() and require in json.loads(l)}


def ca(pdb, chain="A"):
    import gemmi
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    c = [x for x in st[0] if x.name == chain][0]
    return np.array([[a.pos.x, a.pos.y, a.pos.z] for r in c
                     for a in [r.find_atom("CA", "*")] if a])


def superpose_on_framework(ref, mob, loop):
    mask = np.array([i not in set(loop) for i in range(len(ref))])
    P, Q = ref[mask], mob[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return (mob - Q.mean(0)) @ R + P.mean(0)


def main() -> int:
    cfg = load()
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in (BASE / "seq_scores.jsonl").read_text().splitlines() if l.strip()}
    short = [r["design_id"] for r in json.loads((RS / "shortlist.json").read_text())]

    # ---- 1. score the reseed folds ----
    have = {}
    for l in (RS / "index.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("ok"):
                have[(r["design_id"], r["seed"])] = r
    scored = done(FOLDSC, "key", "dockq")
    todo = [{"key": f"{d}|{s}", "design_id": d, "seed": s, "pdb": r["pdb"], "pae": r["pae"]}
            for (d, s), r in sorted(have.items()) if f"{d}|{s}" not in scored]
    print(f"scoring {len(todo)} reseed folds on {WORKERS} workers", flush=True)
    if todo:
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=ctx) as ex:
            futs = [ex.submit(score_one, t) for t in todo]
            for i, f in enumerate(as_completed(futs), 1):
                res = f.result()
                if "error" in res:
                    print(f"  [{i}/{len(todo)}] ERROR {res['key']}: {res['error']}",
                          file=sys.stderr, flush=True)
                else:
                    print(f"  [{i}/{len(todo)}] {res['key']}: dockq={res.get('dockq')}",
                          flush=True)
                with FOLDSC.open("a") as fh:
                    fh.write(json.dumps(res) + "\n")

    # ---- gather all seeds per shortlisted design ----
    per = defaultdict(dict)
    for src in (BASE / "fold_scores.jsonl", FOLDSC):
        for l in src.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if "dockq" in r and r["design_id"] in short:
                per[r["design_id"]][r["seed"]] = r

    def surr_of(rec, did):
        raw = {m: rec.get(m) for m in METRICS}
        raw["netsolp"] = seq[did]["netsolp"]
        raw["cdrh3_identity"] = seq[did]["cdrh3_identity"]
        return surrogate.compute(raw, 1, cfg).value

    rows = []
    for did in short:
        seeds = sorted(per[did])
        if len(seeds) < 2:
            continue
        vals = np.array([surr_of(per[did][s], did) for s in seeds])
        dqs = np.array([per[did][s]["dockq"] for s in seeds])
        rows.append({"design_id": did, "n_seeds": len(seeds), "seeds": seeds,
                     "surr_mean": float(vals.mean()), "surr_sd": float(vals.std(ddof=1)),
                     "dockq_mean": float(dqs.mean()), "dockq_sd": float(dqs.std(ddof=1)),
                     "vals": vals.tolist()})
    rows.sort(key=lambda r: -r["surr_mean"])

    L, w = [], None
    L = []; w = L.append
    w("# M3 — the winner")
    w("")
    w(f"`scripts/35_winner.py`. {len(rows)} shortlisted designs, "
      f"{sorted({r['n_seeds'] for r in rows})} Boltz seeds each.")
    w("")

    # ---- 2. the 1/sqrt(s) assumption ----
    within7 = float(np.sqrt(np.mean([r["surr_sd"] ** 2 for r in rows])))
    w("## 1. Does the noise actually average down?")
    w("")
    w("The shortlist was sized (20 designs x 7 seeds, over 60 x 3) by assuming seed noise is "
      "i.i.d. and shrinks as 1/sqrt(s). That was measured on three seeds and extrapolated. "
      "Seven seeds test it.")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| within-design sd over 3 seeds (40-pool, surrogate pts) | 0.529 |")
    w(f"| within-design sd over {rows[0]['n_seeds']} seeds (this shortlist) | **{within7:.3f}** |")
    w(f"| ratio | **{within7/0.529:.2f}x** |")
    w("")
    if within7 <= 0.529 * 1.25:
        w("The two agree, so the i.i.d. assumption holds well enough at s=7 and the shortlist "
          "sizing rested on a sound premise.")
    else:
        w(f"**The 7-seed spread is materially LARGER than the 3-seed estimate.** Seed noise is "
          f"therefore not i.i.d. — more seeds are revealing structure (multiple conformational "
          f"basins) that three seeds could not see. Averaging shrinks it more slowly than "
          f"1/sqrt(s), so the sizing in `scripts/31` was optimistic and the true reliability "
          f"below is lower than simulated. Reported rather than tuned away.")
    w("")
    # reliability at s seeds, measured
    between = float(np.std([r["surr_mean"] for r in rows], ddof=1))
    s_used = rows[0]["n_seeds"]
    var_noise = within7 ** 2 / s_used
    rel = max(0.0, 1 - var_noise / (between ** 2)) if between > 0 else float("nan")
    w(f"Between-design sd of the {s_used}-seed means: **{between:.3f}**; noise sd of a "
      f"{s_used}-seed mean: {np.sqrt(var_noise):.3f}; **reliability = {rel:.3f}**.")
    w("")

    # ---- 3. ranking + winner's curse ----
    w("## 2. The ranking")
    w("")
    w("| rank | design | arm T | arom | surrogate (mean ± sd) | DockQ (mean ± sd) |")
    w("|---|---|---|---|---|---|")
    for i, r in enumerate(rows[:10], 1):
        d = pool[r["design_id"]]
        w(f"| {i} | `{r['design_id']}` | {d['arm_temperature']} | {d['arom_count']} | "
          f"{r['surr_mean']:.3f} ± {r['surr_sd']:.3f} | "
          f"{r['dockq_mean']:.3f} ± {r['dockq_sd']:.3f} |")
    w("")
    win = rows[0]
    pool_mean = float(np.mean([r["surr_mean"] for r in rows]))
    corrected = pool_mean + rel * (win["surr_mean"] - pool_mean)
    discount = win["surr_mean"] - corrected
    gap = win["surr_mean"] - rows[1]["surr_mean"]
    w("## 3. The winner, discounted")
    w("")
    w(f"**`{win['design_id']}`** — arm T={pool[win['design_id']]['arm_temperature']}, "
      f"aromatic count {pool[win['design_id']]['arom_count']}, "
      f"CDR-H3 `{pool[win['design_id']]['cdrh3']}`, "
      f"identity {seq[win['design_id']]['cdrh3_identity']:.1f}%.")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| raw {s_used}-seed mean surrogate | {win['surr_mean']:.3f} |")
    w(f"| shortlist mean | {pool_mean:.3f} |")
    w(f"| reliability used for shrinkage | {rel:.3f} |")
    w(f"| **winner's-curse discount** | **−{discount:.3f}** |")
    w(f"| **HEADLINE: discounted surrogate** | **{corrected:.3f}** |")
    w(f"| margin over 2nd place | {gap:.3f} ({gap/(within7/np.sqrt(s_used)):.1f} noise sd) |")
    w("")
    if gap < within7 / np.sqrt(s_used):
        w(f"> The gap to second place is **smaller than one standard error of the "
          f"{s_used}-seed mean**. The ordering at the top is not resolved: this is *a* best "
          f"design, not *the* best, and a different seed set could reorder the top two.")
        w("")

    # ---- 4. fresh seed ----
    w("## 4. Fresh-seed re-score")
    w("")
    d = pool[win["design_id"]]
    lab = f"{win['design_id'].replace('.','p')}__fresh{FRESH_SEED}"
    try:
        res = drv.fold(lab, d["heavy"], d["light"], d["antigen"], out_root=RS,
                       construct="fab", seed=FRESH_SEED, antigen_msa=PD1_MSA)
        fr = score_one({"key": lab, "design_id": win["design_id"],
                        "seed": FRESH_SEED, "pdb": str(res.pdb), "pae": str(res.pae)})
        if "error" in fr:
            w(f"Fresh-seed fold scored with an error: `{fr['error']}`")
        else:
            fs = surr_of(fr, win["design_id"])
            w(f"Seed {FRESH_SEED}, used nowhere in selection — the only estimate not "
              f"contaminated by having been selected on.")
            w("")
            w("| quantity | value |")
            w("|---|---|")
            w(f"| surrogate, selection seeds (mean of {s_used}) | {win['surr_mean']:.3f} |")
            w(f"| surrogate, fresh seed {FRESH_SEED} | **{fs:.3f}** |")
            w(f"| shrinkage-predicted value | {corrected:.3f} |")
            w(f"| fresh-seed DockQ | {fr['dockq']:.3f} |")
            w("")
            w(f"The fresh seed came in {fs - win['surr_mean']:+.3f} against the selection mean "
              f"and {fs - corrected:+.3f} against the shrinkage prediction, so the discount "
              f"was {'well calibrated' if abs(fs-corrected) < abs(fs-win['surr_mean']) else 'in the right direction but overshot'}.")
            with FOLDSC.open("a") as fh:
                fh.write(json.dumps(fr) + "\n")
    except FoldFailed as e:
        w(f"Fresh-seed fold FAILED: `{e}`")
    w("")

    # ---- 5. ensemble ----
    w("## 5. The winner's CDR-H3 ensemble")
    w("")
    paths = [Path(per[win["design_id"]][s]["pdb"]) for s in sorted(per[win["design_id"]])]
    cas = [ca(p) for p in paths]
    n = min(len(c) for c in cas)
    cas = [c[:n] for c in cas]
    loop = [i for i in CDRH3 if i < n]
    devs = []
    for i in range(len(cas)):
        for j in range(i + 1, len(cas)):
            mv = superpose_on_framework(cas[i], cas[j], loop)
            devs.append(np.sqrt(((mv[loop] - cas[i][loop]) ** 2).sum(1)))
    dall = np.concatenate(devs)
    rms, mx = float(np.sqrt((dall ** 2).mean())), float(dall.max())
    w(f"Pairwise CA deviation over CDR-H3 (positions 96–108) after superposing on the "
      f"**framework**, across {len(cas)} seeds:")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| ensemble RMSD | **{rms:.2f} Å** |")
    w(f"| max pairwise deviation | {mx:.2f} Å |")
    w("")
    w(f"For context the 40-design discovery pool spanned 0.28–2.23 Å, median 0.71 Å, so this "
      f"winner is {'tighter than' if rms < 0.71 else 'looser than'} the median design there. "
      f"Ensemble spread is reported as characterisation only — it was dropped from selection "
      f"on 2026-09-18 because CDR-H3 aromatic content explains it away entirely.")
    w("")
    # rubric score, reported
    best = per[win["design_id"]][sorted(per[win["design_id"]])[0]]
    raw = {m: float(np.mean([per[win["design_id"]][s][m]
                             for s in sorted(per[win["design_id"]])])) for m in METRICS}
    raw["netsolp"] = seq[win["design_id"]]["netsolp"]
    raw["cdrh3_identity"] = seq[win["design_id"]]["cdrh3_identity"]
    sc = evaluate(raw, 1, cfg)
    w("## 6. The reported rubric score")
    w("")
    w("Ranking used the continuous surrogate; the rubric composite is what the organisers "
      "would recompute, so it is what gets reported.")
    w("")
    w("```")
    w(sc.table())
    w("```")
    w("")
    w(f"`final` = **{sc.final}**, viable = **{sc.viable}**"
      + (f", failing: {sc.failing}" if sc.failing else "")
      + (f", thin margin on: {sc.thin_margin}" if sc.thin_margin else "") + ".")
    w("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n")
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
