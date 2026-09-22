#!/usr/bin/env python3
"""Specificity controls: does the named design bind things it should not?

THE QUESTION. `mpnn_T0.5_s104_036` scores ipSAE 0.856 / dG -12.7 / 97 contacts
against PD-1. None of those numbers is evidence of *specificity*: a sticky,
well-packed surface scores the same way against whatever it is docked to, and
Boltz will place two chains together whether or not they belong together. The
post-cutoff test already showed this predictor building large, confident, wrongly
placed interfaces. So the control is: fold the SAME antibody against antigens it
must not bind, and require the score to collapse.

THE PANEL, chosen for increasing distance from PD-1:

  PD-1      (5GGS antigen, 113 aa)  POSITIVE CONTROL at fresh seeds 31-33.
                                    Like-for-like: same protocol, same cached MSA,
                                    seeds used nowhere in selection.
  PD-L1     (5IUS chain C, IgV)     THE ONE THAT MATTERS FUNCTIONALLY. PD-1's
                                    ligand, and the molecule our antibody exists to
                                    block. Binding it would be a mechanism failure,
                                    not just a specificity failure. Truncated to the
                                    IgV domain for size parity with PD-1 (the full
                                    ectodomain is 214 aa and would confound interface
                                    size with identity).
  TIM-3     (8TBB antigen)          HARDEST DECOY. A human checkpoint receptor with
                                    the same Ig V-set fold as PD-1. Cross-reactivity
                                    inside the checkpoint family is the realistic
                                    off-target risk for a real drug.
  ULBP6     (8RWB antigen)          Human, MHC-I-like fold. Different fold, same
                                    species, similar size.
  PcrV      (9JBQ antigen)          Bacterial, unrelated. The "does it bind anything
                                    at all" floor.

MSAs: PD-1, TIM-3, ULBP6 and PcrV are already cached (data/msa_cache/). PD-L1 is
not, so its first fold fetches from the ColabFold public server and the alignment is
then cached for the remaining seeds -- same pattern as 14_fold_postcutoff_v2.py.
Published human sequence, so the upload discloses nothing.

WHAT THIS CANNOT SHOW. A decoy that scores low is consistent with specificity but
does not establish it; a predictor that is bad at novel placement (median post-cutoff
DockQ 0.291) will score novel pairings low whether or not they would bind in reality.
The informative direction is asymmetric: a decoy scoring HIGH is strong evidence of a
problem, a decoy scoring LOW is weak evidence of its absence. Said plainly in the
writeup, not buried.

3 seeds per antigen because one seed cannot separate a low score from a bad draw:
the shortlist's single-seed ipSAE sd is ~0.02, but across genuinely different
antigens the spread is much larger and 3 gives a usable interval.
"""
from __future__ import annotations
import csv, json, shutil, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

WINNER = "mpnn_T0.5_s104_036"
POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/specificity")
INDEX = OUT / "index.jsonl"
CACHE = Path("data/msa_cache")
SEEDS = (31, 32, 33)          # used nowhere in M3 selection or validation (1-7, 23)


def query_of(csv_path: Path) -> str:
    """The query sequence of a cached Boltz MSA (the row with key -1)."""
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            if row["key"] == "-1":
                return row["sequence"]
    raise SystemExit(f"no query row in {csv_path}")


def pdl1_igv() -> str:
    """PD-L1 IgV domain from 5IUS chain C, cut at the IgV/IgC boundary."""
    from locksmith.io.pdb import seq_for_folding
    full = seq_for_folding(Path("data/refs/5ius.pdb"), "C")
    i = full.find("NAPYNKIN")           # first residue of the IgC domain
    if i < 0:
        raise SystemExit("PD-L1 IgV/IgC boundary motif not found")
    return full[:i]


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    w = pool[WINNER]
    pdl1 = pdl1_igv()

    panel = [
        ("pd1",   "PD-1 (positive control)",      w["antigen"],
         CACHE / "pd1_5ggs.csv"),
        ("pdl1",  "PD-L1 IgV (functional decoy)", pdl1,
         CACHE / "pdl1_5ius_igv.csv"),
        ("tim3",  "TIM-3 (Ig V-set decoy)",       query_of(CACHE / "v2/8tbb_antigen.csv"),
         CACHE / "v2/8tbb_antigen.csv"),
        ("ulbp6", "ULBP6 (MHC-I-like decoy)",     query_of(CACHE / "v2/8rwb_antigen.csv"),
         CACHE / "v2/8rwb_antigen.csv"),
        ("pcrv",  "PcrV (bacterial decoy)",       query_of(CACHE / "v2/9jbq_antigen.csv"),
         CACHE / "v2/9jbq_antigen.csv"),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    have = done()
    print(f"winner {WINNER}; panel of {len(panel)} antigens x {len(SEEDS)} seeds", flush=True)
    for key, desc, ag, msa in panel:
        print(f"  {key:6s} {len(ag):4d} aa  msa={'cached' if msa.exists() else 'SERVER'}  {desc}",
              flush=True)

    t0, ok, bad = time.time(), 0, 0
    for key, desc, ag, msa in panel:
        for seed in SEEDS:
            label = f"spec_{key}__s{seed}"
            if label in have:
                print(f"skip {label}", flush=True)
                continue
            use = msa if msa.exists() else None
            try:
                r = drv.fold(label, w["heavy"], w["light"], ag, out_root=OUT,
                             construct="fab", seed=seed, antigen_msa=use)
            except FoldFailed as e:
                bad += 1
                print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
                rec = {"label": label, "antigen": key, "desc": desc, "seed": seed,
                       "ok": False, "error": str(e)[:400]}
            else:
                ok += 1
                # Cache the alignment the first time the server supplies one.
                if use is None:
                    src = OUT / label / f"boltz_results_{label}" / "msa" / f"{label}_2.csv"
                    if src.exists():
                        msa.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, msa)
                        print(f"  cached {msa.name} "
                              f"({sum(1 for _ in msa.open())-1} seqs)", flush=True)
                print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
                rec = {"label": label, "antigen": key, "desc": desc, "seed": seed,
                       "antigen_len": len(ag), "ok": True, "pdb": str(r.pdb),
                       "pae": str(r.pae), "plddt": str(r.plddt), "seconds": r.seconds}
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"\nspecificity: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
