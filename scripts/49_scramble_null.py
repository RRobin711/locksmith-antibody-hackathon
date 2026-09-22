#!/usr/bin/env python3
"""The proper null: shuffle CDR-H3 residue ORDER, hold composition exactly.

WHAT THIS TESTS. The 239-design pool spans DockQ 0.596-0.777 and the project spent
six days ranking within that band. The question nobody asked is whether that band
is DESIGN QUALITY or just LOOP-PERTURBATION MAGNITUDE. A scramble answers it: take
a real design's CDR-H3 and permute the residue order. The result has

    identical length, identical amino-acid composition, identical aromatic count,
    identical net charge, identical hydrophobic fraction, identical NetSolP inputs
    at the composition level -- and no design rationale whatsoever.

Every cheap sequence feature this project has used as a predictor is held constant
by construction. If the scramble distribution overlaps the pool distribution, then
the pool's DockQ spread is not measuring design quality, and the ranking apparatus
built on top of it was ranking noise plus loop-perturbation size.

WHY THIS IS A BETTER NULL THAN THE NOVELTY PROBE. Arm C of the novelty probe
redesigned paratope positions with ProteinMPNN, so its sequences are still
structurally plausible ones the model likes -- it is a weak null. A permutation is
a strong null: same residues, no plausibility.

Note it is not a *perfect* null. Shuffling changes CDR-H3 identity to the parent
(a scramble usually lands below its source design's identity), so a scramble is
slightly more diverged than its source. That biases AGAINST overlap, i.e. against
the null hypothesis, so overlap is the conservative finding. The per-design pairing
below controls for it as far as anything can: each scramble is matched to the
design it came from, and the comparison is the paired difference.

DESIGN: 30 source designs sampled across the whole DockQ range (deciles, so the
comparison is not made only at the top), one scramble each, one seed each. The
statistic is the paired difference source - scramble, tested with Wilcoxon signed
rank, plus overlap of the two distributions. Seeds: DockQ within-design sd is
0.014, and the effect that would matter is of order 0.1, so one seed per design
with n=30 pairs gives SE ~0.003 on the mean difference. Depth is not the binding
constraint; breadth across the range is.
"""
from __future__ import annotations
import json, random, sys, time
from pathlib import Path

from locksmith.design.mpnn import cdr_positions
from locksmith.fold.batch import BatchItem, fold_batch

POOL = Path("designs/wide_temp/designs.json")
SCORES = Path("runs/designs_temp/fold_scores.jsonl")
OUT = Path("runs/scramble_null")
INDEX = OUT / "index.jsonl"
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
SEED, BATCH, N_SOURCES = 1, 12, 30
RNG = random.Random(4242)


def scramble(h3: str, rng: random.Random, tries: int = 200) -> str:
    """A permutation that is not the identity and not a trivial near-identity."""
    best = None
    for _ in range(tries):
        c = list(h3); rng.shuffle(c); s = "".join(c)
        if s == h3:
            continue
        moved = sum(1 for a, b in zip(s, h3) if a != b)
        if moved >= max(2, int(0.6 * len(h3))):      # most positions actually move
            return s
        best = best or s
    if best is None:
        raise SystemExit(f"could not scramble {h3}")
    return best


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["design_id"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    pool = {d["design_id"]: d for d in json.loads(POOL.read_text())}
    scored = [json.loads(l) for l in SCORES.read_text().splitlines()
              if l.strip() and "dockq" in json.loads(l)]
    scored.sort(key=lambda r: r["dockq"])
    # stratified across the DockQ range: N_SOURCES evenly spaced ranks
    step = len(scored) / N_SOURCES
    picks = [scored[min(len(scored) - 1, int(i * step + step / 2))] for i in range(N_SOURCES)]

    OUT.mkdir(parents=True, exist_ok=True)
    have = done()
    items, meta = [], {}
    for p in picks:
        d = pool[p["design_id"]]
        h = d["heavy"]
        loop = cdr_positions(h)["cdr3"]
        h3 = "".join(h[i] for i in loop)
        sc = scramble(h3, RNG)
        mut = list(h)
        for i, aa in zip(loop, sc):
            mut[i] = aa
        mut = "".join(mut)
        sid = f"scr_{d['design_id'].replace('.', 'p')}"
        if sid in have:
            continue
        items.append(BatchItem(label=sid, heavy=mut, light=d["light"], antigen=d["antigen"]))
        meta[sid] = {"design_id": sid, "source_id": d["design_id"],
                     "source_dockq": p["dockq"], "source_cdrh3": h3, "scrambled_cdrh3": sc,
                     "n_moved": sum(1 for a, b in zip(sc, h3) if a != b)}
    print(f"{len(picks)} sources spanning DockQ "
          f"{picks[0]['dockq']:.3f}-{picks[-1]['dockq']:.3f}; {len(items)} to fold", flush=True)
    for sid in list(meta)[:3]:
        m = meta[sid]
        print(f"  {m['source_id']}: {m['source_cdrh3']} -> {m['scrambled_cdrh3']} "
              f"({m['n_moved']}/13 moved)", flush=True)

    t0, ok, bad = time.time(), 0, 0
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        out = fold_batch(chunk, out_root=OUT, seed=SEED, construct="fab",
                         antigen_msa=PD1_MSA)
        rows = []
        for label, res in out.results.items():
            rows.append({**meta[label], "label": label, "seed": SEED, "ok": True,
                         "pdb": str(res.pdb), "pae": str(res.pae),
                         "plddt": str(res.plddt), "seconds": res.seconds})
        for label, err in out.failures.items():
            rows.append({**meta[label], "label": label, "seed": SEED, "ok": False,
                         "error": err[:400]})
        with INDEX.open("a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        ok += len(out.results); bad += len(out.failures)
        print(f"  batch {i//BATCH+1}: {len(out.results)} ok, {len(out.failures)} failed, "
              f"{out.seconds:.0f}s", flush=True)
    print(f"\nscramble null: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
