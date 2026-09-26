#!/usr/bin/env python3
"""Parallel per-fold scoring for the 40x3 pool.

WHY THIS IS SAFE TO PARALLELISE. Each metric is a pure function of one PDB + PAE,
and -- the part that actually matters -- `ipsae.py` writes its results table NEXT
TO the input PDB (`<stem>_10_15.txt`). That would be a race if folds shared a
directory. They do not: every fold has its own
`runs/.../<label>/boltz_results_<label>/predictions/<label>/`. Verified before
enabling this.

WHY 6 WORKERS AND NOT 24. Each worker spawns DockQ and PRODIGY subprocesses in
their own venvs, a few hundred MB each. This machine hit memory pressure earlier
in the session. 6 keeps the footprint near 2-3 GB.

NetSolP is deliberately NOT parallelised: predict.py sets
intra_op_num_threads = os.cpu_count(), so one call already uses all 24 cores and
running several would oversubscribe. It stays in scripts/25 (serial).
"""
from __future__ import annotations
import json, os, sys
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

WORKERS = 6
OUT = Path("runs/designs_wide")
FOLDSC = OUT / "fold_scores.jsonl"
POOL = Path("designs/wide_mpnn/designs.json")
PRIOR = [Path("runs/designs_baseline/index.jsonl"),
         Path("runs/designs_reseed/index.jsonl"), OUT / "index.jsonl"]


def score_one(rec: dict) -> dict:
    # imports inside the worker so each process initialises its own state
    from locksmith.config import load
    from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
    from locksmith.types import Provenance, Structure
    cfg = load(); conv = cfg.conventions
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
        out["dockq"] = dockq.compute(
            st, native, allowed_mismatches=conv["dockq_allowed_mismatches"])["dockq"].value
    except Exception as e:                                        # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"[:300]
    return out


def main() -> int:
    pool = {d["design_id"] for d in json.loads(POOL.read_text())}
    have = {}
    for p in PRIOR:
        if not p.exists():
            continue
        for l in p.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ok") and r["design_id"] in pool:
                have[(r["design_id"], r.get("seed", 1))] = r
    done = set()
    if FOLDSC.exists():
        done = {json.loads(l)["key"] for l in FOLDSC.read_text().splitlines() if l.strip()}

    todo = []
    for (did, seed), r in sorted(have.items()):
        key = f"{did}|{seed}"
        if key in done:
            continue
        todo.append({"key": key, "design_id": did, "seed": seed,
                     "pdb": r["pdb"], "pae": r["pae"]})
    print(f"{len(have)} folds available, {len(done)} already scored, {len(todo)} to score "
          f"on {WORKERS} workers")
    FOLDSC.parent.mkdir(parents=True, exist_ok=True)
    n_err = 0
    # `fork` (the Linux default) cannot re-initialise CUDA in the child. Today this
    # parent never touches CUDA -- the metric imports live inside `score_one` -- so
    # fork happens to work. One CUDA-touching line added above this point would kill
    # every worker with `Cannot re-initialize CUDA in forked subprocess`; that cost
    # 239/239 workers once already. Pinned by
    # tests/test_invariants.py::test_every_process_pool_uses_spawn_not_fork.
    _ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=_ctx) as ex:
        futs = {ex.submit(score_one, t): t["key"] for t in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            if "error" in res:
                n_err += 1
                print(f"  [{i}/{len(todo)}] ERROR {res['key']}: {res['error']}", file=sys.stderr)
            else:
                print(f"  [{i}/{len(todo)}] {res['key']}: dockq={res.get('dockq')} "
                      f"ipsae={res.get('ipsae')}", flush=True)
            with FOLDSC.open("a") as f:
                f.write(json.dumps(res) + "\n")
    print(f"\nscored {len(todo)} folds, {n_err} errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
