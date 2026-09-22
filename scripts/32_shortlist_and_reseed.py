#!/usr/bin/env python3
"""Shortlist on the continuous surrogate, then re-seed -- at 7 seeds, not 3.

WHY 7 SEEDS ON 20 DESIGNS AND NOT 3 SEEDS ON 60. Simulated at the measured noise
structure (true between-design sd 0.562 surrogate pts, single-seed noise sd 0.529),
holding the fold budget fixed at ~120 extra folds:

    k=60, s=3  ->  E[true score of the design finally picked] = +1.394
    k=40, s=4  ->  +1.431
    k=30, s=5  ->  +1.458
    k=20, s=7  ->  +1.470     <- chosen
    k=13, s=10 ->  +1.473

Three seeds is the WORST allocation at every budget tested. The reason is that the
quality of the final pick is limited by the reliability of the measurement used to
choose it, not by how many candidates are on the list: deepening the shortlist adds
candidates whose scores are just as noisy, so a noisy-high mediocre design is promoted
about as often as the true best is found. Going from k=20 to k=239 at 3 seeds buys
NOTHING measurable (+1.395 -> +1.389, inside Monte-Carlo error) for 8x the folds.

This overturns the "retain the true top 5 at 95%" sizing, which demanded k=119.
Retaining the best design in the shortlist is not the same as PICKING it, and only the
second one ships.

ASSUMPTION, AND HOW THIS RUN TESTS IT. The simulation assumes seed noise is i.i.d. and
that s seeds reduce it by sqrt(s). The 40-pool has only 3 seeds, so that cannot be
checked beyond 3. Seven seeds on twenty designs tests it directly: if the within-design
sd across 7 seeds is much larger than the 3-seed estimate, the noise has a systematic
component (a design with two genuine conformational basins, say) and averaging will
have stopped helping. That check is part of the deliverable, not an afterthought.

Seeds 2..7 for the shortlist; seed 1 already exists for all 239. Resumable.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

import numpy as np

from locksmith.config import load
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.select import surrogate

POOL = Path("designs/wide_temp/designs.json")
SRC = Path("runs/designs_temp")
OUT = Path("runs/designs_reseed7")
INDEX = OUT / "index.jsonl"
SHORTLIST = OUT / "shortlist.json"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
K, SEEDS = 20, (2, 3, 4, 5, 6, 7)
METRICS = ("ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa")


def main() -> int:
    cfg = load()
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in (SRC / "seq_scores.jsonl").read_text().splitlines() if l.strip()}
    rows = []
    for l in (SRC / "fold_scores.jsonl").read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if "dockq" not in r or r["design_id"] not in seq:
            continue
        raw = {m: r.get(m) for m in METRICS}
        raw["netsolp"] = seq[r["design_id"]]["netsolp"]
        raw["cdrh3_identity"] = seq[r["design_id"]]["cdrh3_identity"]
        g = surrogate.compute(raw, 1, cfg)
        rows.append({"design_id": r["design_id"], "surrogate": g.value,
                     "band_margin": g.band_margin, "limiting": g.limiting,
                     "dockq_s1": r["dockq"],
                     "arom": pool[r["design_id"]]["arom_count"],
                     "temperature": pool[r["design_id"]]["arm_temperature"]})
    rows.sort(key=lambda x: -x["surrogate"])
    short = rows[:K]
    OUT.mkdir(parents=True, exist_ok=True)
    SHORTLIST.write_text(json.dumps(short, indent=2))
    s = np.array([r["surrogate"] for r in rows])
    print(f"ranked {len(rows)} designs on the continuous surrogate: "
          f"{s.min():.2f}-{s.max():.2f}, sd {s.std(ddof=1):.3f}")
    print(f"shortlist k={K}: surrogate {short[-1]['surrogate']:.2f}-{short[0]['surrogate']:.2f}")
    print(f"  by arm: ", {t: sum(1 for r in short if r['temperature'] == t)
                          for t in sorted({r['temperature'] for r in short})})
    print(f"  by aromatic count: ", {a: sum(1 for r in short if r['arom'] == a)
                                     for a in sorted({r['arom'] for r in short})})

    have = set()
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("ok"):
                    have.add((r["design_id"], r["seed"]))
    todo = [(r["design_id"], sd) for r in short for sd in SEEDS
            if (r["design_id"], sd) not in have]
    print(f"\n{K} designs x {len(SEEDS)} new seeds = {K*len(SEEDS)} folds; "
          f"{len(have)} on disk; {len(todo)} to run", flush=True)

    t0, done, failed = time.time(), 0, 0
    for did, sd in todo:
        d = pool[did]
        label = f"{did.replace('.', 'p')}__r{sd}"
        try:
            res = drv.fold(label, d["heavy"], d["light"], d["antigen"],
                           out_root=OUT, construct="fab", seed=sd, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            failed += 1
            print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
            rec = {"design_id": did, "label": label, "seed": sd, "ok": False,
                   "error": str(e)[:400]}
        else:
            done += 1
            rate = (time.time() - t0) / done
            print(f"  [{done}/{len(todo)}] {label}: {res.seconds:.0f}s "
                  f"(eta {(len(todo)-done)*rate/3600:.1f}h)", flush=True)
            rec = {"design_id": did, "label": label, "seed": sd, "ok": True,
                   "pdb": str(res.pdb), "pae": str(res.pae), "plddt": str(res.plddt),
                   "seconds": res.seconds}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"\nfolded {done}, failed {failed}, elapsed {(time.time()-t0)/3600:.2f}h", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
