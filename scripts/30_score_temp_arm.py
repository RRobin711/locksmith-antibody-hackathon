#!/usr/bin/env python3
"""Score the M3 primary arm. Sequence metrics serially, structure metrics on 6 workers.

Split by what varies. NetSolP and CDR-H3 identity are functions of the SEQUENCE, so
they are computed once per design; the structure metrics are functions of one PDB+PAE
and are computed per fold. Mixing the two recomputes a ~11 s/seq NetSolP call for
every seed of every design.

WHY 6 WORKERS, NOT 24. Each worker spawns DockQ and PRODIGY subprocesses in their own
venvs (the numpy 2.0 split makes shared environments impossible), a few hundred MB
each. This machine has 15 GiB usable and has hit memory pressure before. 6 keeps the
footprint near 2-3 GB. Parallelising is only safe at all because ipsae.py writes its
table NEXT TO the input PDB and every fold owns its own directory -- shared output
directories would be a silent race.

Resumable: keys already present in the output files are skipped.
Writes runs/designs_temp/{seq_scores,fold_scores}.jsonl.
"""
from __future__ import annotations
import json, multiprocessing, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

WORKERS = 6
POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/designs_temp")
INDEX = OUT / "index.jsonl"
FOLDSC = OUT / "fold_scores.jsonl"
SEQSC = OUT / "seq_scores.jsonl"


def score_one(rec: dict) -> dict:
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


def done_keys(path: Path, key: str, *, require: str | None = None) -> set:
    """Keys already recorded. With `require`, only rows that actually carry that field.

    A row recording a FAILURE is not a completed unit of work. Treating it as one is how
    a batch marks every failure complete and skips it forever -- the same class of error
    as keying a batch on a process exit status. `require` makes the resume condition the
    presence of the artefact, not the presence of a row.
    """
    if not path.exists():
        return set()
    out = set()
    for l in path.read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if require is not None and require not in r:
            continue
        out.add(r[key])
    return out


def main() -> int:
    from locksmith.metrics import netsolp, novelty
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- per-design sequence metrics (once each) ----
    have_seq = done_keys(SEQSC, "design_id", require="netsolp")
    todo_seq = [did for did in pool if did not in have_seq]
    print(f"sequence metrics: {len(have_seq)} done, {len(todo_seq)} to run", flush=True)
    for i, did in enumerate(todo_seq, 1):
        d = pool[did]
        rec = {"design_id": did, "cdrh3_identity": novelty.compute(d["heavy"]).value}
        try:
            rec["netsolp"] = netsolp.compute(d["heavy"], d["light"])["netsolp"].value
        except Exception as e:                                    # noqa: BLE001
            rec["error"] = f"{type(e).__name__}: {e}"[:300]
            print(f"  [{i}/{len(todo_seq)}] seq {did}: ERROR {rec['error']}",
                  file=sys.stderr, flush=True)
        else:
            print(f"  [{i}/{len(todo_seq)}] seq {did}: netsolp={rec['netsolp']:.4f}", flush=True)
        with SEQSC.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    # ---- per-fold structure metrics ----
    have = {}
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ok") and r["design_id"] in pool:
                have[(r["design_id"], r["seed"])] = r
    scored = done_keys(FOLDSC, "key", require="dockq")
    todo = [{"key": f"{did}|{seed}", "design_id": did, "seed": seed,
             "pdb": r["pdb"], "pae": r["pae"]}
            for (did, seed), r in sorted(have.items()) if f"{did}|{seed}" not in scored]
    print(f"structure metrics: {len(have)} folds available, {len(scored)} scored, "
          f"{len(todo)} to score on {WORKERS} workers", flush=True)
    n_err = 0
    if todo:
        # SPAWN, NOT FORK. The sequence stage above runs NetSolP in THIS process, which
        # initialises CUDA. ProcessPoolExecutor defaults to fork on Linux, and a forked
        # child inherits a CUDA context it cannot re-initialise -- every worker then dies
        # with "Cannot re-initialize CUDA in forked subprocess". Spawn starts each worker
        # from a clean interpreter. This cost 239/239 scoring failures on 2026-09-19;
        # the original design avoided it only by keeping the two stages in separate
        # scripts, so merging them silently created the coupling.
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=ctx) as ex:
            futs = {ex.submit(score_one, t): t["key"] for t in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                res = fut.result()
                if "error" in res:
                    n_err += 1
                    print(f"  [{i}/{len(todo)}] ERROR {res['key']}: {res['error']}",
                          file=sys.stderr, flush=True)
                else:
                    print(f"  [{i}/{len(todo)}] {res['key']}: dockq={res.get('dockq')} "
                          f"ipsae={res.get('ipsae')}", flush=True)
                with FOLDSC.open("a") as f:
                    f.write(json.dumps(res) + "\n")
    ok_f = len(done_keys(FOLDSC, "key", require="dockq"))
    ok_s = len(done_keys(SEQSC, "design_id", require="netsolp"))
    print(f"\nscored folds: {ok_f}  designs: {ok_s}  errors this run: {n_err}", flush=True)
    # bug 3: a stage that failed for every unit must not report success. The overnight
    # run printed "stage 2 exit=0" after 239/239 failures.
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
