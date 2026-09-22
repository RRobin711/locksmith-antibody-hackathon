#!/usr/bin/env python3
"""Fold the M3 primary arm: every design, one Boltz seed, NO pre-fold filtering.

WHY UNFILTERED. The campaign's purpose is partly to decide whether the CDR-H3
aromatic filter earns a place in the funnel. Folding only the survivors makes that
question unanswerable -- you can never see what you discarded, so any cost claim is
circular. Folding a *sample* of rejects fixes the circularity but leaves sampling
error. Folding EVERYTHING costs ~30 extra folds (~23 min) and makes the comparison
exact: every filter, threshold and random-subset null can then be evaluated offline
on complete data, as many times as we like, at zero further GPU cost.

See results/m3_plan_review.md §1 for why the null model must be a random subset of
equal size rather than the unfiltered pool.

RESUMABLE. Every completed fold is appended to index.jsonl the moment it lands, and
a restart skips anything already recorded ok. A suspend, an OOM kill or a Ctrl-C
costs at most the fold in flight. This matters because `boltz predict` EXITS 0 AFTER
FATAL ERRORS -- so completion is judged on the artefacts, which locksmith.fold's
assert_artefacts() enforces, never on the exit status.

FOLD ORDER IS SHUFFLED, AND THAT IS LOAD-BEARING. The pool is built arm by arm, so
the natural order folds all of T=0.1, then all of T=0.2, and so on. Any run that does
not reach the end would then yield a pool with the low-temperature arms complete and
the high-temperature arm missing entirely -- which does not merely shrink n, it
destroys the temperature comparison the arm exists to make. Shuffling with a fixed
seed makes ANY prefix of the run a balanced random sample across all four arms, so a
partial night is still analysable and an interrupted run costs precision rather than
the experiment. Same family as randomising collection order against drift: the failure
is a collection artefact masquerading as a result.

The seed is fixed (0) so the order is reproducible across restarts; combined with the
resume logic this means a restart continues the same shuffled sequence rather than
re-randomising into a fresh bias.

Writes runs/designs_temp/. Does NOT touch runs/designs_wide/ or designs/wide_mpnn/.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv

POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/designs_temp")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEED = 1


def existing() -> set[tuple[str, int]]:
    have = set()
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ok"):
                have.add((r["design_id"], r["seed"]))
    return have


def main() -> int:
    pool = json.loads(POOL.read_text())
    have = existing()
    todo = [d for d in pool if (d["design_id"], SEED) not in have]
    # Shuffle BEFORE the resume filter would have mattered: the order is a pure function
    # of the pool and the fixed seed, so restarts follow the same sequence.
    random.Random(0).shuffle(todo)
    by_arm = Counter(d.get("arm_temperature") for d in todo)
    print(f"{len(pool)} designs x 1 seed; {len(have)} already on disk; {len(todo)} to run",
          flush=True)
    print(f"shuffled (seed 0); remaining by arm temperature: {dict(sorted(by_arm.items()))}",
          flush=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    t0, done, failed = time.time(), 0, 0
    for d in todo:
        did = d["design_id"]
        label = f"{did.replace('.', 'p')}__t{SEED}"
        try:
            res = drv.fold(label, d["heavy"], d["light"], d["antigen"],
                           out_root=OUT, construct="fab", seed=SEED, antigen_msa=PD1_MSA)
        except FoldFailed as e:
            failed += 1
            print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
            rec = {"design_id": did, "label": label, "seed": SEED, "ok": False,
                   "error": str(e)[:400]}
        else:
            done += 1
            el = time.time() - t0
            rate = el / done
            print(f"  [{done}/{len(todo)}] {label}: {res.seconds:.0f}s "
                  f"(mean {rate:.0f}s, eta {(len(todo)-done)*rate/3600:.1f}h)", flush=True)
            rec = {"design_id": did, "label": label, "seed": SEED, "ok": True,
                   "pdb": str(res.pdb), "pae": str(res.pae), "plddt": str(res.plddt),
                   "seconds": res.seconds}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"\nfolded {done}, failed {failed}, elapsed {(time.time()-t0)/3600:.2f}h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
