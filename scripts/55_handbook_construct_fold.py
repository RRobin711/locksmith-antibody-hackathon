#!/usr/bin/env python3
"""Re-fold the Challenge 1 finalist on the HANDBOOK's constructs, not 5GGS coordinates.

WHAT WAS FOUND. The handbook's example FASTA (S4.2.2) is not an approximation of what
this project folded -- it is 5GGS's **SEQRES**, verbatim, while every fold here used
5GGS's **coordinates**. Verified against the RCSB entity API: the handbook's 123-aa
antigen is byte-identical to the deposited PD-1 entity sequence.

All three of our chains are exact contiguous SUBSTRINGS of the handbook's:

    heavy    ours 219 aa == handbook[1:220]   of 232   (handbook adds Q- and ...DKTHHHHHH)
    light    ours 217 aa == handbook[0:217]   of 218
    antigen  ours 113 aa == handbook[5:118]   of 123   (adds DSPDR- and -VTERR)

So this is the SAME complex with unresolved terminal residues restored -- not, as was
first suggested, a different complex. The core is identical at every position. That
distinction matters: a terminal extension is the case `seq_for_folding()` deliberately
permits, as opposed to an internal deletion, which it refuses.

WHY RE-FOLD ANYWAY. Two reasons, neither of which is "the old numbers are wrong":

  1. **The shipped PDB and FASTA must correspond.** The organisers recompute six of
     eight metrics from the two files handed over. Shipping the handbook's FASTA while
     the PDB models a 10-residue-shorter antigen would be internally inconsistent -- the
     same defect as the coordinate-substitution exploit this project declined in
     PLAN 13.6.
  2. **It is an empirical question whether the termini matter**, and 3 folds answer it.
     The added residues are far from the epitope and likely disordered, so the
     prediction is that the metrics barely move. That prediction is recorded here
     BEFORE the folds run, and the comparison is reported either way.

Folds the finalist's designed CDRs transplanted into the handbook constructs, 3 seeds,
so the comparison against the existing 8-seed numbers has a noise floor on both sides.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.io.pdb import seq_for_folding

WINNER = "mpnn_T0.5_s104_036"
OUT = Path("runs/handbook_construct")
INDEX = OUT / "index.jsonl"
SEEDS = (71, 72, 73)
HB = Path("data/refs/handbook_constructs.json")

HB_HEAVY = ("QVQLVQSGVEVKKPGASVKVSCKASGYTFTNYYMYWVRQAPGQGLEWMGGINPSNGGTNFNEKFKNRVTLTTDSS"
            "TTTAYMELKSLQFDDTAVYYCARRDYRFDMGFDYWGQGTTVTVSSASTKGPSVFPLAPSSKSTSGGTAALGCLVK"
            "DYFPEPVTVSWNSGALTSGVHTFPAVLQSSGLYSLSSVVTVPSSSLGTQTYICNVNHKPSNTKVDKKVEPKSCDK"
            "THHHHHH")
HB_LIGHT = ("EIVLTQSPATLSLSPGERATLSCRASKGVSTSGYSYLHWYQQKPGQAPRLLIYLASYLESGVPARFSGSGSGTDF"
            "TLTISSLEPEDFAVYYCQHSRDLPLTFGGGTKVEIKRTVAAPSVFIFPPSDEQLKSGTASVVCLLNNFYPREAKV"
            "QWKVDNALQSGNSQESVTEQDSKDSTYSLSSTLTLSKADYEKHKVYACEVTHQGLSSPVTKSFNRGEC")
HB_ANTIGEN = ("DSPDRPWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQL"
              "PNGRDFHMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELRVTERR")


def main() -> int:
    parent_h = seq_for_folding(Path("data/refs/prepared/5ggs_ABZ.pdb"), "A")
    parent_l = seq_for_folding(Path("data/refs/prepared/5ggs_ABZ.pdb"), "B")
    w = {d["design_id"]: d for d in
         json.loads(Path("designs/wide_temp/designs.json").read_text())}[WINNER]

    # Assert the substring relationship rather than trusting the offsets.
    oh, ol = HB_HEAVY.find(parent_h), HB_LIGHT.find(parent_l)
    if oh < 0 or ol < 0:
        raise SystemExit("parent chains are not substrings of the handbook constructs; "
                         "the transplant offsets cannot be trusted")
    if len(w["heavy"]) != len(parent_h) or len(w["light"]) != len(parent_l):
        raise SystemExit("designed chain lengths differ from the parent; MPNN is "
                         "fixed-length and this should be impossible")

    heavy = HB_HEAVY[:oh] + w["heavy"] + HB_HEAVY[oh + len(parent_h):]
    light = HB_LIGHT[:ol] + w["light"] + HB_LIGHT[ol + len(parent_l):]
    antigen = HB_ANTIGEN

    # The transplant must change ONLY the designed positions.
    diff = [i for i in range(len(HB_HEAVY)) if HB_HEAVY[i] != heavy[i]]
    print(f"heavy {len(heavy)} aa (handbook {len(HB_HEAVY)}), light {len(light)}, "
          f"antigen {len(antigen)}", flush=True)
    print(f"positions changed vs the handbook's wild-type heavy: {len(diff)} "
          f"-> {diff[:3]}...{diff[-3:]}", flush=True)
    if len(diff) > 29:
        raise SystemExit(f"{len(diff)} positions differ; at most 29 CDR positions should")
    HB.parent.mkdir(parents=True, exist_ok=True)
    HB.write_text(json.dumps({"design_id": WINNER, "heavy": heavy, "light": light,
                              "antigen": antigen, "heavy_offset": oh,
                              "light_offset": ol, "antigen_offset": 5}, indent=1))
    print(f"wrote {HB}", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    have = set()
    if INDEX.exists():
        have = {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
                if l.strip() and json.loads(l).get("ok")}
    t0, ok, bad = time.time(), 0, 0
    for seed in SEEDS:
        label = f"hb_{WINNER.replace('.', 'p')}__s{seed}"
        if label in have:
            print(f"skip {label}", flush=True); continue
        try:
            # No cached MSA: the antigen is 10 residues longer than the cached PD-1
            # alignment's query, so the cache does not apply and reusing it would
            # silently misalign the extension.
            r = drv.fold(label, heavy, light, antigen, out_root=OUT,
                         construct="fab", seed=seed, antigen_msa=None)
        except FoldFailed as e:
            bad += 1
            print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
            rec = {"label": label, "seed": seed, "ok": False, "error": str(e)[:400]}
        else:
            ok += 1
            print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
            rec = {"label": label, "seed": seed, "ok": True, "pdb": str(r.pdb),
                   "pae": str(r.pae), "plddt": str(r.plddt), "seconds": r.seconds}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"\nhandbook construct: {ok} folded, {bad} failed, "
          f"{(time.time()-t0)/60:.0f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
