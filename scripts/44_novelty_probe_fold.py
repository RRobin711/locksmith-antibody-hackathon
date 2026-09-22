#!/usr/bin/env python3
"""Fold the novelty-probe arms. One seed each; the contrast is between arms.

Arms A/B change only zero-contact CDR-H3 positions, arm C only paratope positions,
and B and C are matched at 53.8% CDR-H3 identity -- identical on the rubric's novelty
axis. See scripts/43_novelty_probe_generate.py and the pre-registration.

ONE SEED PER DESIGN is the right allocation here and it is worth saying why, because
the project has just spent two days on the opposite conclusion. M3 needed many seeds
because it was RANKING designs whose true differences were smaller than the seed
noise. This arm is comparing ARM MEANS, with ~13 designs per arm, and the predicted
between-arm difference is large (a paratope destroyed versus untouched). The standard
error of an arm mean over 13 designs at DockQ seed sd 0.018 is 0.005; the effect being
looked for is of order 0.1. Seeds would buy precision that is already 20x more than
the comparison needs, and breadth within an arm is what guards against one odd design
carrying the result.
"""
from __future__ import annotations
import json, sys, time
from collections import Counter
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold.batch import BatchItem, fold_batch

POOL = Path("designs/novelty_probe/designs.json")
OUT = Path("runs/novelty_probe")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEED = 1
BATCH = 12


def have() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["design_id"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    if not POOL.exists():
        print(f"{POOL} missing -- generation did not run", file=sys.stderr)
        return 1
    pool = json.loads(POOL.read_text())
    done = have()
    todo = [d for d in pool if d["design_id"] not in done]
    print(f"{len(pool)} probe designs, {len(done)} done, {len(todo)} to fold", flush=True)
    print(f"by arm: {dict(sorted(Counter(d['arm'] for d in todo).items()))}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)

    t0, ok, bad = time.time(), 0, 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = [BatchItem(label=f"{d['design_id']}__n{SEED}", heavy=d["heavy"],
                           light=d["light"], antigen=d["antigen"]) for d in chunk]
        by = {it.label: d for it, d in zip(items, chunk)}
        t1 = time.time()
        out = fold_batch(items, out_root=OUT, seed=SEED, construct="fab",
                         antigen_msa=PD1_MSA)
        rows = []
        for label, res in out.results.items():
            d = by[label]
            rows.append({"design_id": d["design_id"], "arm": d["arm"], "label": label,
                         "seed": SEED, "ok": True, "cdrh3": d["cdrh3"],
                         "cdrh3_identity": d["cdrh3_identity"],
                         "pdb": str(res.pdb), "pae": str(res.pae),
                         "plddt": str(res.plddt), "seconds": res.seconds})
        for label, err in out.failures.items():
            d = by[label]
            rows.append({"design_id": d["design_id"], "arm": d["arm"], "label": label,
                         "seed": SEED, "ok": False, "error": err[:400]})
        with INDEX.open("a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        ok += len(out.results); bad += len(out.failures)
        print(f"  batch {i//BATCH+1}: {len(out.results)} ok, {len(out.failures)} failed, "
              f"{time.time()-t1:.0f}s", flush=True)
    print(f"\nnovelty probe: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
