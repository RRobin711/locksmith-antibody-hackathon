#!/usr/bin/env python3
"""Tier 0: is a Boltz fold reproducible at all? Plus the serial resource baseline.

WHY THIS COMES FIRST. Every comparison in this project assumes that re-folding the same
input means something: the MSA 2x2, the three fix arms, the framework controls, the paired
constrained fold, the matched positive control. If a fold is not reproducible, that
assumption is load-bearing and unmeasured, and a noise floor would have to be stated
alongside every one of those results.

It also decides how a concurrency test gets BUILT, not merely how it is read:
  * bit-identical -> a concurrency test is a diff against a serial reference. Cheap.
  * not identical -> an exact diff is meaningless. You would need several serial re-folds
    to establish a noise floor first, then compare against that with a threshold fixed in
    advance. A different, larger experiment.

This project already has the rule: a reproducibility test needs a control proving
reproducibility is achievable at all, because cuDNN/cuBLAS select kernels by tensor shape
and the tool may simply not be bitwise deterministic.

SUBJECT. `cf_bb_8_0` -- the design now in the submission. Same sequence, same 123-residue
antigen, same `pd1_123_handbook.csv`, same seed 1, recycling 10, 5 diffusion samples.
Re-folded into a separate directory and compared against the stored artefacts.

COMPARISON, in increasing strictness:
  1. per-sample ipSAE, all five models
  2. PAE matrices, exact array equality
  3. coordinates: byte-identity of the PDB, then max atomic displacement if bytes differ

BASELINE CAPTURED IN THE SAME RUN, since it costs nothing extra: wall-clock, peak RSS,
peak GPU memory, and GPU utilisation sampled at 1 Hz.
"""
from __future__ import annotations

import json, subprocess, sys, time
from pathlib import Path

OUT = Path("runs/determinism")
REF = Path("runs/constrained_fold/cf_bb_8_0/boltz_results_cf_bb_8_0/predictions/cf_bb_8_0")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
LABEL = "det_bb_8_0"
RECYCLING, SAMPLES, SEED = 10, 5, 1


def main() -> int:
    from locksmith.fold import fold_is_complete
    from locksmith.fold.boltz import fold

    d = {r["backbone"]: r for r in json.loads(
        Path("runs/redesign_yield/yield.json").read_text()) if r["clean"]}["bb_8_0"]
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    OUT.mkdir(parents=True, exist_ok=True)
    pred = OUT / LABEL / f"boltz_results_{LABEL}" / "predictions" / LABEL

    if not fold_is_complete(pred, LABEL, n_models=SAMPLES):
        # 1 Hz GPU sampler alongside the fold -- NVML refreshes at ~2 Hz internally, so
        # sampling faster returns duplicates and buys nothing.
        smp = OUT / "gpu_samples.csv"
        sampler = subprocess.Popen(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
             "--format=csv,noheader,nounits", "-l", "1"],
            stdout=smp.open("w"), stderr=subprocess.DEVNULL)
        t0 = time.time()
        try:
            fold(LABEL, d["heavy"], d["light"], ag, out_root=OUT, antigen_msa=MSA,
                 seed=SEED, diffusion_samples=SAMPLES, recycling_steps=RECYCLING,
                 timeout=5400)
        finally:
            elapsed = time.time() - t0
            sampler.terminate(); sampler.wait(timeout=10)
        rows = [r.split(",") for r in smp.read_text().splitlines() if "," in r]
        util = [int(a) for a, _ in rows]; mem = [int(b) for _, b in rows]
        base = {"seconds": round(elapsed, 1), "n_samples": len(rows),
                "gpu_util_mean": round(sum(util) / max(len(util), 1), 1),
                "gpu_util_max": max(util) if util else None,
                "gpu_mem_peak_MiB": max(mem) if mem else None,
                "gpu_mem_mean_MiB": round(sum(mem) / max(len(mem), 1)) if mem else None}
        (OUT / "baseline.json").write_text(json.dumps(base, indent=1))
        print(f"wall-clock {base['seconds']}s | GPU util mean {base['gpu_util_mean']}% "
              f"max {base['gpu_util_max']}% | GPU mem peak {base['gpu_mem_peak_MiB']} MiB\n",
              flush=True)
    else:
        print("re-fold already present; comparing\n", flush=True)

    # ---------------- comparison ----------------
    import numpy as np
    from locksmith.config import load
    from locksmith.metrics import ipsae
    from locksmith.types import Provenance, Structure
    c = load().conventions

    print(f"{'model':<8}{'stored ipSAE':>14}{'refold ipSAE':>14}{'delta':>10}"
          f"{'PDB bytes':>12}{'PAE array':>12}{'max dxyz A':>12}")
    allsame = True
    out = []
    for i in range(SAMPLES):
        a = REF / f"cf_bb_8_0_model_{i}.pdb"
        b = pred / f"{LABEL}_model_{i}.pdb"
        if not (a.exists() and b.exists()):
            print(f"model_{i}: missing"); allsame = False; continue
        pa, pb = REF / f"pae_cf_bb_8_0_model_{i}.npz", pred / f"pae_{LABEL}_model_{i}.npz"
        va = ipsae.compute(Structure(pdb=a, provenance=Provenance.PREDICTION, pae=pa,
                                     label="a"), pae_cutoff=c["ipsae_pae_cutoff"],
                           dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
        vb = ipsae.compute(Structure(pdb=b, provenance=Provenance.PREDICTION, pae=pb,
                                     label="b"), pae_cutoff=c["ipsae_pae_cutoff"],
                           dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
        # PDB bytes: ATOM records only, so a timestamp or path in a REMARK cannot mask it
        la = [l for l in a.read_text().splitlines() if l.startswith("ATOM")]
        lb = [l for l in b.read_text().splitlines() if l.startswith("ATOM")]
        same_bytes = la == lb
        with np.load(pa) as za, np.load(pb) as zb:
            ka, kb = list(za.keys())[0], list(zb.keys())[0]
            same_pae = np.array_equal(za[ka], zb[kb])
        if same_bytes:
            dmax = 0.0
        else:
            import gemmi
            sa, sb = gemmi.read_structure(str(a)), gemmi.read_structure(str(b))
            dmax = max(x.pos.dist(y.pos)
                       for ca, cb in zip(sa[0], sb[0])
                       for ra, rb in zip(ca, cb)
                       for x, y in zip(ra, rb))
        allsame &= same_bytes and same_pae and (va == vb)
        out.append({"model": i, "stored": va, "refold": vb, "bytes": same_bytes,
                    "pae": same_pae, "max_dxyz": round(dmax, 4)})
        print(f"model_{i:<2}{va:>14.4f}{vb:>14.4f}{vb-va:>+10.4f}"
              f"{str(same_bytes):>12}{str(same_pae):>12}{dmax:>12.4f}")

    print()
    print("VERDICT: " + ("BIT-IDENTICAL — a concurrency test can be an exact diff"
                         if allsame else
                         "NOT reproducible — an exact diff is meaningless; a noise floor "
                         "must be measured from several serial re-folds first"))
    (OUT / "comparison.json").write_text(json.dumps(
        {"bit_identical": bool(allsame), "models": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
