#!/usr/bin/env python3
"""The control nobody ran: destroy the EPITOPE, keep the antigen.

WHY THIS AND NOT THE DECOY PANEL. The specificity panel varied the antigen while
holding the antibody fixed. That confounds two things: whether the antibody is
selective for PD-1's binding SITE, and whether the predictor responds to antigen
identity at all. Holding PD-1 fixed and removing only its binding face separates
them. If ipSAE / dG / contacts do not move when the epitope is gone, then those
metrics are not reporting the interface -- they are reporting that two chains are
adjacent -- and every binding number in this project is uninterpretable.

The prediction, from what is already measured, is that they will NOT move much:
Boltz reproduces pembrolizumab's CDR-H3 pose to 1.12 A mean across 239 designs
whose loops differ by 7-11 of 13 residues, and the alanine ablation removed 158
antibody-side contacts for 0.030 DockQ. This experiment puts that on the antigen
side, where there is no training-set pose to recall for a mutated PD-1.

ARMS (antigen chain C mutated; antibody and light chain untouched):

  ko6    the 6 largest epitope contributors -> Ala        305 of 720 contacts
  ko12   the 12 largest -> Ala                            527 of 720 contacts
  ctrl6  6 NON-contacting surface residues -> Ala         0 contacts

`ctrl6` is the necessary control and is chosen to match `ko6` in count and, as far
as possible, in residue type, so the comparison is "same number of alanines, on or
off the interface". Without it a drop in either arm is uninterpretable, which is
exactly the hole the 2026-09-20 ablation fell into.

3 seeds per arm plus 3 fresh seeds of the unmutated complex as the internal
positive control, so every number here is like-for-like against a reference folded
in the same script with the same MSA.

MSA NOTE, and it is load-bearing. The cached PD-1 alignment
(data/msa_cache/pd1_5ggs.csv) is keyed to the WILD-TYPE PD-1 sequence. Handing a
mutated antigen a wild-type MSA leaks the native residue identity back into the
prediction through the alignment, which would mask exactly the effect being
measured. Each mutated antigen therefore gets `antigen_msa=None`, i.e. a fresh
server alignment for the mutant sequence. The wild-type control uses the cache.
This asymmetry is deliberate and is reported.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.io.pdb import seq_for_folding

WINNER = "mpnn_T0.5_s104_036"
POOL = Path("designs/wide_temp/designs.json")
PARENT = Path("data/refs/prepared/5ggs_ABZ.pdb")
OUT = Path("runs/epitope_ko")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEEDS = (61, 62, 63)

# 0-based indices into the 113-aa PD-1 chain, ranked by heavy-atom contacts <5 A
EPITOPE_12 = [58, 100, 97, 55, 56, 52, 47, 57, 54, 28, 33, 31]
CONTACTS = {58: 105, 100: 68, 97: 45, 55: 44, 56: 44, 52: 43,
            47: 38, 57: 35, 54: 31, 28: 25, 33: 25, 31: 24}


def pick_controls(seq: str, epitope: set[int], want: int) -> list[int]:
    """Non-contacting positions, matched as far as possible to ko6's residue types."""
    target = [seq[i] for i in EPITOPE_12[:want]]
    free = [i for i in range(len(seq)) if i not in epitope and seq[i] not in "GPC"]
    chosen: list[int] = []
    for aa in target:
        cand = [i for i in free if seq[i] == aa and i not in chosen]
        if not cand:                      # fall back to any unused non-epitope residue
            cand = [i for i in free if i not in chosen]
        chosen.append(cand[len(cand) // 2])
    return sorted(chosen)


def to_ala(seq: str, idx: list[int]) -> str:
    s = list(seq)
    for i in idx:
        s[i] = "A"
    return "".join(s)


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    w = {d["design_id"]: d for d in json.loads(POOL.read_text())}[WINNER]
    pd1 = seq_for_folding(PARENT, "C")
    if pd1 != w["antigen"]:
        print("WARNING: parent PD-1 differs from the design's antigen field", file=sys.stderr)
    epi = set(json.loads(Path("runs/pd1_epitope_contacts.json").read_text()).keys())
    epi = {int(i) for i in epi}
    ctrl = pick_controls(pd1, epi, 6)

    arms = [
        ("wt", "unmutated PD-1 (internal positive control)", pd1, PD1_MSA, 0),
        ("ko6", "6 largest epitope contributors -> Ala",
         to_ala(pd1, EPITOPE_12[:6]), None, sum(CONTACTS[i] for i in EPITOPE_12[:6])),
        ("ko12", "12 largest epitope contributors -> Ala",
         to_ala(pd1, EPITOPE_12), None, sum(CONTACTS.values())),
        ("ctrl6", "6 NON-contacting surface residues -> Ala",
         to_ala(pd1, ctrl), None, 0),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"design {WINNER}; PD-1 {len(pd1)} aa; total epitope contacts 720", flush=True)
    print(f"control positions (non-contacting): {ctrl} -> "
          f"{''.join(pd1[i] for i in ctrl)}", flush=True)
    for k, d, s, msa, n in arms:
        print(f"  {k:6s} contacts_removed={n:4d} msa={'cached' if msa else 'server'}  {d}",
              flush=True)

    have = done()
    t0, ok, bad = time.time(), 0, 0
    for key, desc, ag, msa, ncon in arms:
        for seed in SEEDS:
            label = f"ko_{key}__s{seed}"
            if label in have:
                print(f"skip {label}", flush=True); continue
            try:
                r = drv.fold(label, w["heavy"], w["light"], ag, out_root=OUT,
                             construct="fab", seed=seed, antigen_msa=msa)
            except FoldFailed as e:
                bad += 1
                print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
                rec = {"label": label, "arm": key, "desc": desc, "seed": seed,
                       "contacts_removed": ncon, "ok": False, "error": str(e)[:400]}
            else:
                ok += 1
                print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
                rec = {"label": label, "arm": key, "desc": desc, "seed": seed,
                       "contacts_removed": ncon, "ok": True, "pdb": str(r.pdb),
                       "pae": str(r.pae), "plddt": str(r.plddt), "seconds": r.seconds}
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"\nepitope knockout: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
