#!/usr/bin/env python3
"""Fold the 30 Challenge 2 designs with Boltz-2. Resumable; nothing is filtered.

INPUT. The designed heavy/light chains come from the RFantibody pilot's ProteinMPNN
stage, retrieved from the pod volume on 2026-09-22 and read out of the coordinate files
in `runs/challenge2_pod/c2/seq/`. These are *designed* chains, so there is no SEQRES to
prefer -- the coordinates ARE the design, and `seq_for_folding` would be the wrong tool
(it guards against coordinate-derived sequences of EXPERIMENTAL structures with
unresolved loops). We still assert the chains are gap-free by residue numbering.

THE ANTIGEN IS THE HANDBOOK'S, NOT THE POD'S. RFdiffusion was conditioned against a
113-residue PD-1 built from the crystal; the handbook's §4.2.2 antigen is 123 residues
(5GGS SEQRES). Verified: the pod's target is an EXACT SUBSTRING of the handbook antigen
at offset 5 with 5 trailing residues, i.e. pure terminal extension. Terminal truncation
is harmless where an internal deletion would be fatal, so folding against the longer,
submission-correct construct is both safe and the right thing to hand over.

Every design is folded. No pre-filtering, because the gate pass rate is the quantity we
are trying to measure and filtering first would bias it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import gemmi

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

SEQ_DIR = Path("runs/challenge2_pod/c2/seq")
OUT = Path("runs/challenge2_fold")
INDEX = OUT / "index.jsonl"
DESIGNS = OUT / "designs.json"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")


def chains_of(pdb: Path) -> dict[str, str]:
    st = gemmi.read_structure(str(pdb))
    st.setup_entities()
    out = {}
    for ch in st[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        nums = [r.seqid.num for r in res]
        if nums != list(range(nums[0], nums[0] + len(nums))):
            raise ValueError(f"{pdb.name} chain {ch.name}: non-contiguous numbering")
        out[ch.name] = gemmi.one_letter_code([r.name for r in res]).upper()
    return out


def collect() -> list[dict]:
    hbc = json.loads(Path("data/refs/handbook_constructs.json").read_text())
    antigen = hbc["antigen"]
    rows = []
    for pdb in sorted(SEQ_DIR.glob("*_dldesign_*.pdb")):
        c = chains_of(pdb)
        if set(c) != {"H", "L", "T"}:
            raise ValueError(f"{pdb.name}: chains {sorted(c)}")
        if c["T"] not in antigen:
            raise ValueError(f"{pdb.name}: target is not a substring of the handbook "
                             f"antigen -- do not silently fold a different protein")
        rows.append({"design_id": pdb.stem, "heavy": c["H"], "light": c["L"],
                     "antigen": antigen, "source_pdb": str(pdb)})
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = collect()
    DESIGNS.write_text(json.dumps(rows, indent=1))
    print(f"{len(rows)} designs; antigen {len(rows[0]['antigen'])} aa "
          f"(handbook §4.2.2), heavy {len(rows[0]['heavy'])} aa, "
          f"light {len(rows[0]['light'])} aa", flush=True)

    done = set()
    if INDEX.exists():
        # Resume on the ARTEFACT, never on the row existing: a row with an error is not
        # completed work. This project once treated 239 error rows as done and would
        # have skipped them for ever.
        done = {json.loads(l)["design_id"] for l in INDEX.read_text().splitlines()
                if l.strip() and json.loads(l).get("ok")}
    todo = [r for r in rows if r["design_id"] not in done]
    print(f"{len(done)} already folded, {len(todo)} to go", flush=True)

    for i, r in enumerate(todo, 1):
        did = r["design_id"]
        label = did.replace(".", "p")
        try:
            res = drv.fold(label, r["heavy"], r["light"], r["antigen"],
                           out_root=OUT, construct="fv", seed=1, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            print(f"[{i}/{len(todo)}] FAILED {did}: {str(e)[:200]}",
                  file=sys.stderr, flush=True)
            rec = {"design_id": did, "label": label, "ok": False, "error": str(e)[:400]}
        else:
            print(f"[{i}/{len(todo)}] {did}: {res.n_residues} res, {res.seconds:.0f}s",
                  flush=True)
            rec = {"design_id": did, "label": label, "ok": True, "pdb": str(res.pdb),
                   "pae": str(res.pae), "plddt": str(res.plddt),
                   "seconds": res.seconds, "n_residues": res.n_residues}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    ok = sum(1 for l in INDEX.read_text().splitlines()
             if l.strip() and json.loads(l).get("ok"))
    print(f"\nfolded ok: {ok}/{len(rows)}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
