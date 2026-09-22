#!/usr/bin/env python3
"""Score every folded design on all eight metrics -> designs.parquet.

A queryable table, not a log: one row per design, raw values plus band, plus the
gate verdict per metric, plus viability. `score.evaluate()` is a pure function of
(raw values, config), so changing a convention and re-running this costs seconds
and no GPU time -- which is why the raw values are persisted rather than only the
verdicts.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

import pandas as pd

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

DESIGNS = Path("designs/baseline_mpnn/designs.json")
INDEX = Path("runs/designs_baseline/index.jsonl")
OUT = Path("designs/baseline_mpnn/designs.parquet")
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS crystal")


def main() -> int:
    meta = {r["design_id"]: r for r in json.loads(DESIGNS.read_text())}
    folds = [json.loads(l) for l in INDEX.read_text().splitlines() if l.strip()]
    cfg = load(); conv = cfg.conventions
    rows = []
    for f in folds:
        did = f["design_id"]
        m = meta[did]
        if not f.get("ok"):
            rows.append({"design_id": did, "fold_ok": False, "viable": None,
                         **{k: m[k] for k in ("cdrh3_identity", "score", "seq_recovery")}})
            continue
        st = Structure(pdb=Path(f["pdb"]), provenance=Provenance.PREDICTION,
                       pae=Path(f["pae"]), label=did, predictor="boltz2")
        raw: dict = {}
        raw.update(prodigy.compute(st))
        raw.update(ipsae.compute(st, pae_cutoff=conv["ipsae_pae_cutoff"],
                                 dist_cutoff=conv["ipsae_dist_cutoff"]))
        raw["iface_plddt"] = plddt.compute(st, cutoff=conv["interface_dist_cutoff"])
        sa = sasa.compute(st)
        raw["cdr_sasa"] = sa[f"cdr_sasa_{conv['cdr_sasa_state']}"]
        # Novelty and solubility come from the DESIGNED sequence, not from the
        # predicted structure's coordinates -- the design is the ground truth for
        # its own sequence, and reading it back off a predicted PDB would add a
        # round-trip that can only lose information.
        raw["cdrh3_identity"] = novelty.compute(m["heavy"])
        raw.update(netsolp.compute(m["heavy"], m["light"]))
        raw.update(dockq.compute(st, NATIVE,
                                 allowed_mismatches=conv["dockq_allowed_mismatches"]))
        s = evaluate(raw, challenge=1, cfg=cfg)
        row = {"design_id": did, "fold_ok": True, "generator": m["generator"],
               "parent": m["parent"], "temperature": m["temperature"],
               "seed": m["seed"], "mpnn_score": m["score"],
               "seq_recovery": m["seq_recovery"], "runtime_s": f.get("seconds"),
               "cdr_h3": m["heavy"][95:108],
               "final_score": s.final, "viable": s.viable,
               "failing_gates": ",".join(s.failing), "unknown": ",".join(s.unknown)}
        for k, v in s.raw.items():
            if not k.startswith("_"):
                row[k] = v
        for k, b in s.bands.items():
            row[f"band_{k}"] = b
        for k, v in s.categories.items():
            row[f"cat_{k}"] = v
        rows.append(row)
        print(f"  {did}: final={s.final} viable={s.viable} "
              f"dockq={s.raw.get('dockq')} ipsae={s.raw.get('ipsae')} "
              f"fail={s.failing or '-'}")
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows x {len(df.columns)} cols)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
