#!/usr/bin/env python3
"""Control 2: fold each antigen ALONE and compare to its crystal chain.

If an antigen does not fold well on its own, a wrong epitope in the complex is
downstream of a bad antigen, and means something different from "the model
cannot place antibodies". MSA depth is reported alongside, because PcrV, DbpA
and ULBP6 are not well-populated targets and a thin alignment is the most likely
cause of a bad monomer.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import gemmi

MAN = Path("data/refs/postcutoff/prepared/manifest_seqres.json")
PREP = Path("data/refs/postcutoff/prepared")
OUT = Path("runs/postcutoff_antigen")
BOLTZ = "/home/rrobin711/.local/bin/boltz"
CACHE = Path("data/msa_cache/v2")


def msa_depth(p: Path) -> int | None:
    if not p.exists():
        return None
    return sum(1 for _ in p.open()) - 1


def main() -> int:
    man = json.loads(MAN.read_text())
    rows = []
    for t, m in man.items():
        label = f"{t.lower()}__antigen_only"
        d = OUT / label
        pdb = d / f"boltz_results_{label}" / "predictions" / label / f"{label}_model_0.pdb"
        ag_msa = CACHE / f"{t.lower()}_antigen.csv"
        if not pdb.exists():
            d.mkdir(parents=True, exist_ok=True)
            fa = d / f"{label}.fasta"
            msa_field = ""
            if ag_msa.exists():
                staged = Path.home() / ".cache/locksmith/msa" / ag_msa.name
                staged.parent.mkdir(parents=True, exist_ok=True)
                staged.write_bytes(ag_msa.read_bytes())
                msa_field = str(staged)
            fa.write_text(f">A|protein|{msa_field}\n{m['antigen']}\n")
            cmd = [BOLTZ, "predict", str(fa), "--out_dir", str(d),
                   "--output_format", "pdb", "--write_full_pae",
                   "--diffusion_samples", "1", "--recycling_steps", "3", "--seed", "1",
                   "--accelerator", "gpu", "--num_workers", "0", "--no_kernels",
                   "--max_msa_seqs", "1024"]
            if not msa_field:
                cmd.append("--use_msa_server")
            t0 = time.time()
            subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if not pdb.exists():
                print(f"{t}: antigen-only fold FAILED", file=sys.stderr)
                rows.append({"target": t, "ok": False})
                continue
            print(f"  {label}: {time.time()-t0:.0f}s")

        # superpose against chain C of the crystal
        pred = gemmi.read_structure(str(pdb)); pred.setup_entities()
        nat = gemmi.read_structure(str(PREP / f"{t.lower()}_ABC.pdb")); nat.setup_entities()
        pc = pred[0][0]
        nc = [c for c in nat[0] if c.name == "C"][0]
        ptype = gemmi.PolymerType.PeptideL
        sup = gemmi.calculate_superposition(nc.get_polymer(), pc.get_polymer(), ptype,
                                            gemmi.SupSelect.CaP)
        plddt = [a.b_iso for r in pc for a in r if a.name == "CA"]
        rows.append({"target": t, "ok": True, "rmsd": round(sup.rmsd, 2),
                     "aligned": sup.count, "n_native": sum(1 for _ in nc),
                     "mean_plddt": round(sum(plddt)/len(plddt), 1) if plddt else None,
                     "msa_depth": msa_depth(ag_msa)})

    print()
    print(f"{'target':<8}{'CA RMSD':>9}{'aligned':>9}{'mean pLDDT':>12}{'MSA depth':>11}")
    for r in rows:
        if not r.get("ok"):
            print(f"{r['target']:<8}   FOLD FAILED"); continue
        print(f"{r['target']:<8}{r['rmsd']:>9.2f}{r['aligned']:>9}{r['mean_plddt']:>12}"
              f"{str(r['msa_depth']):>11}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "antigen_control.json").write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
