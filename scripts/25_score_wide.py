#!/usr/bin/env python3
"""Score every fold in the 40x3 pool. Cached and resumable.

Split by what varies: structure metrics are computed PER FOLD (they differ by
seed); sequence metrics -- NetSolP and CDR-H3 identity -- are computed PER DESIGN,
because the sequence is identical across a design's seeds and NetSolP costs ~22 s
a call. Recomputing it per fold would triple the cost for identical numbers.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.types import Provenance, Structure

POOL = Path("designs/wide_mpnn/designs.json")
OUT = Path("runs/designs_wide")
FOLDSC = OUT / "fold_scores.jsonl"
SEQSC = OUT / "seq_scores.jsonl"
PRIOR = [Path("runs/designs_baseline/index.jsonl"), Path("runs/designs_reseed/index.jsonl"),
         OUT / "index.jsonl"]
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")


def all_folds() -> dict[tuple[str, int], dict]:
    have = {}
    for p in PRIOR:
        if not p.exists():
            continue
        for l in p.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ok"):
                have[(r["design_id"], r.get("seed", 1))] = r
    return have


def done(path: Path, key: str) -> set:
    if not path.exists():
        return set()
    return {json.loads(l)[key] for l in path.read_text().splitlines() if l.strip()}


def main() -> int:
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    cfg = load(); conv = cfg.conventions
    folds = all_folds()

    # ---- per-design sequence metrics (once each) ----
    have_seq = done(SEQSC, "design_id")
    for did, d in pool.items():
        if did in have_seq:
            continue
        rec = {"design_id": did,
               "cdrh3_identity": novelty.compute(d["heavy"]).value}
        ns = netsolp.compute(d["heavy"], d["light"])["netsolp"]
        rec["netsolp"] = ns.value
        with SEQSC.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"  seq {did}: netsolp={rec['netsolp']}")

    # ---- per-fold structure metrics ----
    have_f = done(FOLDSC, "key")
    for (did, seed), r in sorted(folds.items()):
        if did not in pool:
            continue
        key = f"{did}|{seed}"
        if key in have_f:
            continue
        st = Structure(pdb=Path(r["pdb"]), provenance=Provenance.PREDICTION,
                       pae=Path(r["pae"]), label=key, predictor="boltz2")
        rec = {"key": key, "design_id": did, "seed": seed, "pdb": r["pdb"]}
        try:
            rec.update({k: v.value for k, v in prodigy.compute(st).items()})
            rec["ipsae"] = ipsae.compute(st, pae_cutoff=conv["ipsae_pae_cutoff"],
                                         dist_cutoff=conv["ipsae_dist_cutoff"])["ipsae"].value
            rec["iface_plddt"] = plddt.compute(st, cutoff=conv["interface_dist_cutoff"]).value
            rec["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{conv['cdr_sasa_state']}"].value
            rec["dockq"] = dockq.compute(
                st, NATIVE, allowed_mismatches=conv["dockq_allowed_mismatches"])["dockq"].value
        except Exception as e:                                    # noqa: BLE001
            rec["error"] = str(e)[:300]
        with FOLDSC.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"  {key}: dockq={rec.get('dockq')} ipsae={rec.get('ipsae')}")
    print(f"\nfolds scored: {len(done(FOLDSC,'key'))}  designs scored: {len(done(SEQSC,'design_id'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
