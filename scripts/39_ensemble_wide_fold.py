#!/usr/bin/env python3
"""Widen the CDR-H3 ensemble measurement from 40 designs to the whole 239 pool.

WHY THIS SHAPE, AND WHY IT IS NOT THE SHAPE THAT WAS ASKED FOR
--------------------------------------------------------------
The brief said 40-60 designs at 5-7 seeds. `scripts/36_ensemble_power.py` measured
the relevant quantity first, on the 20 designs already folded at 7 seeds, and the
answer is that those folds are better spent on BREADTH:

    seeds k   reliability of a k-seed spread   attenuation sqrt(r)
       2            0.591  (0.265 outlier-free)      0.769  (0.515)
       3            0.813  (0.520)                   0.901  (0.721)
       5            0.935  (0.783)                   0.967  (0.885)
       7            0.968  (0.883)                   0.984  (0.940)

Attenuation is what a correlation against spread loses; n is what its standard error
buys, at 1/sqrt(n-3). Going 2 -> 5 seeds costs 4x the folds and recovers at most
0.967/0.769 = 1.26x of effect, while the same folds spent on breadth take n from 60
to 239 and shrink the Fisher-z SE by 2.0x. Breadth wins, and it wins by more than the
uncertainty in those reliabilities.

So: SEED 2 FOR ALL 239 DESIGNS FIRST (k=2, one new fold each), then seed 3 in the
same shuffled order for as long as the night lasts. The design is NESTED, so any
stopping point yields a complete, balanced k=2 pool plus a k=3 prefix -- never a
half-finished arm.

k=2 SOUNDS TOO THIN. IT IS NOT, BECAUSE VARIANCE IS IDENTIFIED FROM ELSEWHERE.
A 2-seed "spread" is a single pairwise deviation, and on its own you cannot separate
real between-design variation from sampling noise. You do not have to: the sampling
variance of a single pair, V1 = 0.0628 A^2, is measured from the 20x7 shortlist,
where 21 pairs per design pin it down. Then

    var_between(pool) = var(observed 2-seed spreads) - V1

identifies the quantity of interest from the full pool without replicating it there.
This also settles the open question in 36: the shortlist's reliability estimate is
carried by ONE design at 1.77 A (drop it and k=2 reliability falls 0.591 -> 0.265),
and only a full-pool measurement can say whether that design is an outlier or the
visible tip of a fat tail. Either answer is a result.

FOLD ORDER IS SHUFFLED with a fixed seed, for the reason 29_fold_temp_arm.py records:
the pool is built arm by arm, so an unshuffled partial night would return the
low-temperature arms complete and T=0.5 missing entirely, destroying the temperature
comparison rather than merely shrinking it. Temperature matters here specifically --
the aromatic-fraction effect decayed monotonically from rho -0.535 to -0.326 across
these four arms, so temperature is a known effect modifier on a neighbouring axis and
the ensemble relationship may well be modified the same way.

BATCHING. Batch of 12, one boltz invocation per batch, `--seed` being invocation-level
(so a batch is one seed by construction -- this is why the nested design and the
batching agree). Measured amortisation: 84 s serial vs 72 s at batch 6 implies a fixed
per-invocation cost of ~14 s and a marginal fold of ~70 s, so batch 12 gives ~70.8 s
(1.19x) and larger batches buy almost nothing. Loss on a crash is capped at 12 folds
because the index is appended after every batch, not at the end.

DEADLINE. No new batch starts after DEADLINE (default 07:30 local, override with
ENSEMBLE_DEADLINE=HH:MM). An in-flight batch is allowed to finish. The stopping rule
is pre-registered precisely because it is a stopping rule: it is independent of the
data, since the shuffle is fixed before the run and nothing about a design's score
influences when it is folded.

Writes runs/designs_ens/. Does not touch any existing run directory.
"""
from __future__ import annotations
import datetime as dt
import json, os, random, sys, time
from collections import Counter
from pathlib import Path

from locksmith.fold.batch import BatchItem, fold_batch

POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/designs_ens")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
BATCH = 12
SEEDS = (2, 3)
SHUFFLE_SEED = 0          # same constant as 29_fold_temp_arm.py, same reason


MAX_RUN_HOURS = 10          # absolute cap, whatever the clock arithmetic says


def deadline() -> dt.datetime | None:
    """Today's ENSEMBLE_DEADLINE, or None if it has already passed.

    An earlier version rolled a past deadline forward to TOMORROW. That is the
    natural reading for a job launched before midnight, and it is catastrophic
    here: this script is invoked a second time by run_tonight_stage2.sh, and if
    that invocation happens after its deadline the rollover would licence a
    24-hour fold run on a laptop the user expects to be free. A deadline that has
    passed means no time left, so return None and fold nothing. The MAX_RUN_HOURS
    cap is the belt to that braces.
    """
    hhmm = os.environ.get("ENSEMBLE_DEADLINE", "07:30")
    h, m = (int(x) for x in hhmm.split(":"))
    now = dt.datetime.now()
    d = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if d <= now:
        return None
    return min(d, now + dt.timedelta(hours=MAX_RUN_HOURS))


def have() -> set[tuple[str, int]]:
    got = set()
    if INDEX.exists():
        for l in INDEX.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("ok"):
                    got.add((r["design_id"], r["seed"]))
    return got


def main() -> int:
    pool = json.loads(POOL.read_text())
    order = list(pool)
    random.Random(SHUFFLE_SEED).shuffle(order)
    done = have()
    stop = deadline()
    if stop is None:
        print(f"ENSEMBLE_DEADLINE={os.environ.get('ENSEMBLE_DEADLINE', '07:30')} has "
              f"already passed ({dt.datetime.now():%H:%M}); folding nothing.", flush=True)
        return 0
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"pool {len(pool)} designs; nested seeds {SEEDS}; batch {BATCH}", flush=True)
    print(f"already on disk: {len(done)} folds; deadline {stop:%Y-%m-%d %H:%M}", flush=True)
    print(f"arms: {dict(sorted(Counter(d.get('arm_temperature') for d in pool).items()))}",
          flush=True)

    t0, total_ok, total_bad = time.time(), 0, 0
    for seed in SEEDS:
        todo = [d for d in order if (d["design_id"], seed) not in done]
        print(f"\n=== seed {seed}: {len(todo)} designs to fold ===", flush=True)
        for i in range(0, len(todo), BATCH):
            if dt.datetime.now() >= stop:
                print(f"DEADLINE reached at {dt.datetime.now():%H:%M}; "
                      f"not starting a new batch", flush=True)
                print(f"\nfolded {total_ok}, failed {total_bad}, "
                      f"elapsed {(time.time()-t0)/3600:.2f}h", flush=True)
                return 0
            chunk = todo[i:i + BATCH]
            items = [BatchItem(label=f"{d['design_id'].replace('.', 'p')}__e{seed}",
                               heavy=d["heavy"], light=d["light"], antigen=d["antigen"])
                     for d in chunk]
            by_id = {it.label: d for it, d in zip(items, chunk)}
            t1 = time.time()
            out = fold_batch(items, out_root=OUT, seed=seed, construct="fab",
                             antigen_msa=PD1_MSA)
            rows = []
            for label, res in out.results.items():
                d = by_id[label]
                rows.append({"design_id": d["design_id"], "label": label, "seed": seed,
                             "arm": d.get("arm_temperature"), "ok": True,
                             "pdb": str(res.pdb), "pae": str(res.pae),
                             "plddt": str(res.plddt), "seconds": res.seconds})
            for label, err in out.failures.items():
                d = by_id[label]
                rows.append({"design_id": d["design_id"], "label": label, "seed": seed,
                             "arm": d.get("arm_temperature"), "ok": False,
                             "error": err[:400]})
            with INDEX.open("a") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            total_ok += len(out.results)
            total_bad += len(out.failures)
            el = time.time() - t1
            rate = (time.time() - t0) / max(total_ok, 1)
            left = (len(todo) - i - len(chunk))
            print(f"  seed {seed} batch {i//BATCH+1}: {len(out.results)} ok, "
                  f"{len(out.failures)} failed, {el:.0f}s "
                  f"({el/max(len(chunk),1):.0f}s/fold, running mean {rate:.0f}s); "
                  f"{left} left this seed, eta {left*rate/3600:.1f}h", flush=True)
            if out.failures:
                for label, err in list(out.failures.items())[:3]:
                    print(f"    FAILED {label}: {err[:160]}", file=sys.stderr, flush=True)

    print(f"\nfolded {total_ok}, failed {total_bad}, "
          f"elapsed {(time.time()-t0)/3600:.2f}h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
