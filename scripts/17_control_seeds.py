#!/usr/bin/env python3
"""Control 3: seed variance on the worst target, Fab, two extra seeds."""
from __future__ import annotations
import json, sys
from pathlib import Path
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

TARGET = sys.argv[1] if len(sys.argv) > 1 else "9W43"
MAN = Path("data/refs/postcutoff/prepared/manifest_seqres.json")
OUT = Path("runs/postcutoff_v2")
INDEX = OUT / "index.jsonl"
CACHE = Path("data/msa_cache/v2")

m = json.loads(MAN.read_text())[TARGET]
done = {json.loads(l)["label"] for l in INDEX.read_text().splitlines() if l.strip()}
for seed in (2, 3):
    label = f"{TARGET.lower()}__fab__v2s{seed}"
    if label in done:
        print(f"skip {label}"); continue
    try:
        r = drv.fold(label, m["heavy_full"], m["light_full"], m["antigen"],
                     out_root=OUT / "fab", construct="fab", seed=seed,
                     antigen_msa=CACHE / f"{TARGET.lower()}_antigen.csv")
    except FoldFailed as e:
        print(f"FAILED {label}: {e}", file=sys.stderr); continue
    print(f"  {label}: {r.seconds:.0f}s")
    with INDEX.open("a") as f:
        f.write(json.dumps({"label": label, "target": TARGET, "construct": "fab",
                            "seed": seed, "predictor": "boltz2", "ok": True,
                            "pdb": str(r.pdb), "pae": str(r.pae), "plddt": str(r.plddt),
                            "seconds": r.seconds, "n_residues": r.n_residues,
                            "chain_lengths": list(r.chain_lengths)}) + "\n")
