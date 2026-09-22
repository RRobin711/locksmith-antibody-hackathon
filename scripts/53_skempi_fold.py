#!/usr/bin/env python3
"""The validity experiment: do these metrics track MEASURED binding affinity?

EVERYTHING ELSE IN THIS PROJECT MEASURES RELIABILITY. This measures validity.

Seven days produced reliability coefficients, disattenuation, pre-registration,
winner's-curse shrinkage and a power analysis -- all of which quantify how
*precisely* a design can be ranked, and none of which says whether the ranked
quantity corresponds to anything a laboratory could measure. Every binding number
in the project is a deterministic function of one Boltz sample of one complex whose
pose the model has memorised. Nothing has ever been compared to an experiment.

THE TEST. SKEMPI 2.0 records experimental binding affinities for point mutants of
protein complexes. 3HFM (HyHEL-10 Fab vs hen egg-white lysozyme) carries 71 mappable
single mutants with measured dG_wt and dG_mut. Fold the wild type and 45 mutants,
score each with the project's own metric stack, and correlate each metric against
the measured ddG.

    ddG = RT ln(Kd_mut / Kd_wt)   -- positive means the mutation WEAKENS binding

CHOICE OF TARGET, AND ITS ONE WEAKNESS. 3HFM is pre-2023 and therefore inside
Boltz-2's training set. For a *ddG ranking* test that is acceptable and is stated
plainly: we are not asking the model to find the pose, we are asking whether the
scores it produces move correctly when a residue that experimentally matters is
removed. A model that has memorised the wild-type pose can still, in principle,
respond to mutations. If it cannot, that is precisely the finding. Size also
matters: 215+214+129 = 558 residues, the same regime as this project's Fabs, so the
result transfers.

THE CENSORING, HANDLED HONESTLY. 18 of the 45 carry ddG above +6 kcal/mol, which for
this assay means "no binding detected" rather than a measured number -- the values
pile at a detection limit. They are kept because Spearman is rank-based and a
non-binder genuinely belongs at the weak end of the order, and the analysis reports
the correlation BOTH over all 45 and over the 27 with |ddG| <= 6. Anything that
depends on which set is used is not a result.

THE NOISE FLOOR. The wild type is folded at 3 seeds, so every metric's seed sd is
measured on this complex rather than assumed from the PD-1 one. A null is then
reportable as "no effect larger than x" instead of as an absence.

PREDICTION, RECORDED BEFORE THE FOLDS RUN: near-zero correlation for ipSAE, DockQ
and interface pLDDT, because they describe a pose the model recalls rather than an
interaction energy. PRODIGY dG is the fairest of the set -- it was built to estimate
binding affinity -- and is the one with a real chance. On this project's own evidence
even that is doubtful: PRODIGY scored the named design better against TIM-3 (-14.1)
than against its actual target PD-1 (-12.5).
"""
from __future__ import annotations
import json, shutil, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.io.pdb import seq_for_folding

NAT = Path("data/refs/skempi/3hfm.pdb")
MUTS = Path("data/refs/skempi/3hfm_mutants.json")
OUT = Path("runs/skempi_3hfm")
INDEX = OUT / "index.jsonl"
MSA = Path("data/msa_cache/lysozyme_3hfm.csv")
WT_SEEDS = (1, 2, 3)
CHAINMAP = {"H": 0, "L": 1, "Y": 2}          # -> heavy, light, antigen (folded as A/B/C)


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    chains = [seq_for_folding(NAT, c) for c in ("H", "L", "Y")]
    muts = json.loads(MUTS.read_text())
    print(f"3HFM  H={len(chains[0])} L={len(chains[1])} Y={len(chains[2])}; "
          f"{len(muts)} mutants + {len(WT_SEEDS)} WT seeds", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    have = done()

    jobs = [(f"skempi_wt__s{s}", "WT", 0.0, chains, s, False) for s in WT_SEEDS]
    for m in muts:
        c = list(chains)
        k = CHAINMAP[m["chain"]]
        s = list(c[k])
        if s[m["idx"]] != m["wt"]:
            raise SystemExit(f"{m['mut']}: chain {m['chain']} index {m['idx']} is "
                             f"{s[m['idx']]}, expected {m['wt']}")
        s[m["idx"]] = m["to"]
        c[k] = "".join(s)
        jobs.append((f"skempi_{m['mut']}__s1", m["mut"], m["ddg"], c, 1, m["censored"]))

    t0, ok, bad = time.time(), 0, 0
    for label, name, ddg, (h, l, a), seed, cens in jobs:
        if label in have:
            continue
        msa = MSA if MSA.exists() else None
        try:
            r = drv.fold(label, h, l, a, out_root=OUT, construct="fab",
                         seed=seed, antigen_msa=msa)
        except FoldFailed as e:
            bad += 1
            print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
            rec = {"label": label, "mut": name, "ddg": ddg, "seed": seed,
                   "censored": cens, "ok": False, "error": str(e)[:400]}
        else:
            ok += 1
            if msa is None:      # cache the lysozyme alignment from the first fold
                src = OUT / label / f"boltz_results_{label}" / "msa" / f"{label}_2.csv"
                if src.exists():
                    MSA.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, MSA)
                    print(f"  cached {MSA.name}", flush=True)
            el = time.time() - t0
            print(f"  [{ok}/{len(jobs)}] {label}: {r.seconds:.0f}s "
                  f"(eta {(len(jobs)-ok)*el/ok/3600:.1f}h)", flush=True)
            rec = {"label": label, "mut": name, "ddg": ddg, "seed": seed,
                   "censored": cens, "ok": True, "pdb": str(r.pdb),
                   "pae": str(r.pae), "plddt": str(r.plddt), "seconds": r.seconds}
        with INDEX.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"\nskempi: {ok} folded, {bad} failed, {(time.time()-t0)/3600:.2f}h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
