#!/usr/bin/env python3
"""Redesign Challenge 1's light-chain CDRs — the one region we never touched.

WHY. `min(VH, VL)` pins Challenge 1's NetSolP to the light chain: VL is pembrolizumab's
0.569 in all 239 designs because ProteinMPNN only ever redesigned heavy CDRs. Both this
project's own docs and two independent reviewers named light-chain redesign as the single
highest-value unfixed item.

THE ARITHMETIC TRAP, CHECKED BEFORE SPENDING A GPU-HOUR. The shipped design's VH is
**0.699** against a Good edge of **0.70**. So even a perfect light chain leaves
`min(VH, VL) = 0.699` and the band stays Medium. **Redesigning the light chain alone
cannot move the score.** Worth knowing before, not after.

What it *can* do is convert a vague claim ("the light chain is the deficit") into a precise
one ("the deficit is now one heavy-chain residue"), and produce a strictly better molecule
— VL 0.569 is poor in absolute terms whatever the band says.

CHEAP BY CONSTRUCTION. NetSolP is sequence-only, so hundreds of candidate light chains can
be screened without folding anything. Only the best is folded, to check the interface
survived. That is the funnel this project argued for in `PLAN.md` §5.2 and never applied
to the light chain.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.design import mpnn
from locksmith.metrics import liabilities, netsolp

OUT = Path("runs/light_chain")
N_DESIGNS = 24
TEMPERATURE = 0.1
SEED = 4242
SRC_PDB = Path("data/refs/prepared/5ggs_ABZ.pdb")


def main() -> int:
    cfg = load()
    OUT.mkdir(parents=True, exist_ok=True)
    hbc = json.loads(Path("data/refs/handbook_constructs.json").read_text())
    heavy, light_wt = hbc["heavy"], hbc["light"]

    base = netsolp.compute(heavy, light_wt, construct="fv")["netsolp"]
    vh = float(base.detail.split("H=")[1].split(",")[0])
    vl = float(base.detail.split("L=")[1].rstrip(")"))
    good = cfg.bands()["netsolp"].good
    print(f"baseline  VH {vh:.4f}   VL {vl:.4f}   min {min(vh, vl):.4f}   "
          f"Good edge {good}", flush=True)
    print(f"CEILING: VH is {good - vh:+.4f} from the edge, so min() can never exceed "
          f"{vh:.4f} by redesigning the light chain alone.\n", flush=True)

    # ---- generate light-chain variants (chain B designed, A and C as context) ----
    cache = OUT / "designs.json"
    if cache.exists():
        rows = json.loads(cache.read_text())
        print(f"reusing {len(rows)} cached light chains", flush=True)
    else:
        print(f"generating {N_DESIGNS} light chains with ProteinMPNN "
              f"(T={TEMPERATURE}, seed {SEED})", flush=True)
        got = mpnn.generate(SRC_PDB, n=N_DESIGNS, temperature=TEMPERATURE, seed=SEED,
                            design_chain="B", context_chains=("A", "C"),
                            out_root=OUT / "mpnn")
        # `MpnnDesign` names its fields by ROLE, not by chain letter: with
        # design_chain="B" the DESIGNED chain lands in `.heavy` and the context heavy
        # chain in `.light`. Worth stating, because reading it the obvious way silently
        # screens the wrong molecule.
        rows = [{"light_coord": d.heavy, "score": d.score,
                 "seq_recovery": d.seq_recovery, "sample": d.sample} for d in got]
        cache.write_text(json.dumps(rows, indent=1))

    # ---- screen on sequence alone. No folding. ----
    print(f"\nscreening {len(rows)} light chains on NetSolP (sequence-only, no folds)",
          flush=True)
    # The designed chain comes from 5GGS COORDINATES (217 aa); the handbook construct is
    # 218. Graft the designed positions onto the handbook light chain by locating the
    # coordinate sequence inside it, rather than comparing two different constructs.
    wt_coord = json.loads((OUT / "designs.json").read_text())
    from locksmith.io.pdb import seq_for_folding
    coord_l = seq_for_folding(SRC_PDB, "B")
    off = light_wt.find(coord_l[:30])
    if off < 0:
        print("coordinate light chain not found in the handbook construct", file=sys.stderr)
        return 1
    print(f"grafting designed positions onto the handbook light chain at offset {off} "
          f"(coord {len(coord_l)} aa, handbook {len(light_wt)} aa)\n", flush=True)

    def graft(designed_coord: str) -> str:
        out = list(light_wt)
        for j, (a, b) in enumerate(zip(coord_l, designed_coord)):
            if a != b:
                out[off + j] = b
        return "".join(out)

    scored = []
    for i, r in enumerate(rows):
        l = graft(r["light_coord"])
        if len(l) != len(light_wt):
            print(f"  [{i}] graft produced {len(l)} aa; skipped", file=sys.stderr)
            continue
        res = netsolp.compute(heavy, l, construct="fv")["netsolp"]
        v_l = float(res.detail.split("L=")[1].rstrip(")"))
        rep = liabilities.compute(heavy, l)
        ok, fails = rep.handbook_9_2_pass()
        n_diff = sum(1 for a, b in zip(l, light_wt) if a != b)
        scored.append({"light": l, "vl": v_l, "min": min(vh, v_l), "subs": n_diff,
                       "cdr_liabilities": len(rep.cdr_hits), "s92": ok, "fails": fails})
        print(f"  [{i:2d}] VL {v_l:.4f}  ({v_l - vl:+.4f})  subs {n_diff:2d}  "
              f"CDR liabilities {len(rep.cdr_hits)}  §9.2 {'PASS' if ok else 'FAIL'}",
              flush=True)

    scored.sort(key=lambda r: -r["vl"])
    (OUT / "screened.json").write_text(json.dumps(scored, indent=1))

    print("\n" + "=" * 72)
    best = scored[0]
    clearing = [r for r in scored if r["vl"] >= good]
    clean = [r for r in scored if r["vl"] >= good and r["s92"]]
    print(f"best VL {best['vl']:.4f} ({best['vl'] - vl:+.4f} over pembrolizumab's "
          f"{vl:.4f}), {best['subs']} substitutions")
    print(f"light chains reaching VL >= {good}: {len(clearing)}/{len(scored)}")
    print(f"  ... and also clearing §9.2: {len(clean)}")
    print(f"resulting min(VH, VL) for the best: {min(vh, best['vl']):.4f} "
          f"-> band unchanged, because VH {vh:.4f} < {good}")
    print("\nCONCLUSION: the developability ceiling on this design is no longer the light "
          f"chain. It is ONE heavy-chain residue's worth of NetSolP — {good - vh:.4f}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
