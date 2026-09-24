#!/usr/bin/env python3
"""Batching vs staggering, measured side by side and verified byte-for-byte.

THE TWO-PHASE PROFILE THAT MOTIVATES BOTH. A serial fold measured 171 s, of which the
first **78 s hold ZERO GPU memory at 0-5% utilisation** -- CPU-side model loading and
featurisation -- followed by 93 s at 5.4 GiB and 98-100%. So 46% of every fold does not
touch the GPU at all.

  * **Batching** amortises the 78 s across a directory of inputs: the model loads once.
  * **Staggering** overlaps one fold's CPU phase with another's GPU phase, offsetting two
    workers by ~80 s so their GPU phases never coincide.

Both should approach 171/93 = **1.84x** asymptotically. At N=4 the batched arm still pays
one 78 s load, so its measured speedup understates the asymptote; both are reported.

VERIFICATION IS BYTE-FOR-BYTE, not timing. Serial folds are bit-identical
(`runs/determinism/comparison.json`), so this is a straight diff of ATOM records and PAE
arrays against stored outputs. Batching may pad to the longest sequence in a batch, which
can change numerics; staggering should change nothing, but contention has surprised this
project before. If bytes differ, the max atomic displacement is reported before anything
is called a failure -- 1e-4 A and 0.5 A are different problems.
"""
from __future__ import annotations

import json, shutil, subprocess, sys, time
from pathlib import Path

import numpy as np

ROOT = Path("runs/throughput")
REF = Path("runs/constrained_fold")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
BOLTZ = str(Path.home() / ".local/bin/boltz")
DESIGNS = ["bb_1_0", "bb_2_0", "bb_3_0", "bb_4_0"]
SERIAL_S = 171.0
RECYCLING, SAMPLES, SEED = 10, 5, 1

SAMPLER = r"""
while true; do
  C=$(nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits 2>/dev/null | paste -sd+ | bc 2>/dev/null)
  N=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
  R=$(ps -eo rss= --sort=-rss | head -60 | awk '{s+=$1} END{print s}')
  echo "$(date +%s)|${C:-0}|$N|$R"
  sleep 1
done
"""


def write_fasta(path: Path, heavy: str, light: str, antigen: str, msa: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f">A|protein|empty\n{heavy}\n>B|protein|empty\n{light}\n"
                    f">C|protein|{msa}\n{antigen}\n")


def cmd(data: Path, out: Path) -> list[str]:
    return [BOLTZ, "predict", str(data), "--out_dir", str(out),
            "--output_format", "pdb", "--write_full_pae",
            "--diffusion_samples", str(SAMPLES), "--recycling_steps", str(RECYCLING),
            "--seed", str(SEED), "--accelerator", "gpu", "--num_workers", "0",
            "--no_kernels", "--max_msa_seqs", "1024"]


def sample(fn):
    log = ROOT / "samples.txt"
    p = subprocess.Popen(["bash", "-c", SAMPLER], stdout=log.open("w"),
                         stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        fn()
    finally:
        el = time.time() - t0
        p.terminate(); p.wait(timeout=10)
    mem, nproc, rss = [], [], []
    for line in log.read_text().splitlines():
        a = line.split("|")
        if len(a) < 4:
            continue
        try:
            mem.append(int(a[1] or 0)); nproc.append(int(a[2] or 0)); rss.append(int(a[3])//1024)
        except ValueError:
            pass
    return {"seconds": round(el, 1),
            "gpu_mem_peak_MiB": max(mem) if mem else 0,
            "max_concurrent_cuda_procs": max(nproc) if nproc else 0,
            "samples_with_2_procs": sum(1 for n in nproc if n >= 2),
            "rss_peak_MB": max(rss) if rss else 0}


def verify(label: str, pred: Path) -> dict:
    ref = REF / f"cf_{label}" / f"boltz_results_cf_{label}" / "predictions" / f"cf_{label}"
    out = {"label": label, "models": 0, "bytes_same": True, "pae_same": True, "max_dxyz": 0.0}
    for i in range(SAMPLES):
        a = ref / f"cf_{label}_model_{i}.pdb"
        b = pred / f"{pred.name}_model_{i}.pdb"
        if not (a.exists() and b.exists()):
            out["bytes_same"] = False; out["missing"] = str(b); return out
        la = [l for l in a.read_text().splitlines() if l.startswith("ATOM")]
        lb = [l for l in b.read_text().splitlines() if l.startswith("ATOM")]
        if la != lb:
            out["bytes_same"] = False
            import gemmi
            sa, sb = gemmi.read_structure(str(a)), gemmi.read_structure(str(b))
            d = max(x.pos.dist(y.pos) for ca, cb in zip(sa[0], sb[0])
                    for ra, rb in zip(ca, cb) for x, y in zip(ra, rb))
            out["max_dxyz"] = max(out["max_dxyz"], round(d, 6))
        with np.load(ref / f"pae_cf_{label}_model_{i}.npz") as za, \
             np.load(pred / f"pae_{pred.name}_model_{i}.npz") as zb:
            if not np.array_equal(za[list(za.keys())[0]], zb[list(zb.keys())[0]]):
                out["pae_same"] = False
        out["models"] += 1
    return out


def main() -> int:
    y = {r["backbone"]: r for r in json.loads(
        Path("runs/redesign_yield/yield.json").read_text()) if r["clean"]}
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    msa_abs = MSA.resolve()
    if " " in str(msa_abs):
        from locksmith.fold.boltz import _stage
        msa_abs = _stage(MSA)
    ROOT.mkdir(parents=True, exist_ok=True)
    res = {}

    # ---------------- ARM 1: BATCHING ----------------
    print("=== ARM 1: batching -- one invocation over a directory of 4 ===", flush=True)
    bdir = ROOT / "batch_in"; bout = ROOT / "batch_out"
    shutil.rmtree(bdir, ignore_errors=True); shutil.rmtree(bout, ignore_errors=True)
    for name in DESIGNS:
        write_fasta(bdir / f"{name}.fasta", y[name]["heavy"], y[name]["light"], ag, msa_abs)
    res["batch"] = sample(lambda: subprocess.run(cmd(bdir, bout), capture_output=True,
                                                 text=True, timeout=7200))
    res["batch"]["per_fold_s"] = round(res["batch"]["seconds"] / len(DESIGNS), 1)
    res["batch"]["speedup"] = round(SERIAL_S / res["batch"]["per_fold_s"], 2)
    res["batch"]["verify"] = [verify(n, bout / f"boltz_results_{n}" / "predictions" / n)
                              for n in DESIGNS]
    b = res["batch"]
    print(f"  {b['seconds']}s total | {b['per_fold_s']}s/fold | speedup {b['speedup']}x")
    print(f"  GPU peak {b['gpu_mem_peak_MiB']} MiB | max concurrent CUDA procs "
          f"{b['max_concurrent_cuda_procs']} | RSS peak {b['rss_peak_MB']} MB", flush=True)

    # ---------------- ARM 2: STAGGERING ----------------
    print("\n=== ARM 2: staggering -- 2 workers, 80 s offset ===", flush=True)
    sout = ROOT / "stag_out"; shutil.rmtree(sout, ignore_errors=True)
    sdir = ROOT / "stag_in"; shutil.rmtree(sdir, ignore_errors=True)
    for name in DESIGNS:
        write_fasta(sdir / f"{name}.fasta", y[name]["heavy"], y[name]["light"], ag, msa_abs)
    groups = [DESIGNS[:2], DESIGNS[2:]]

    def run_staggered():
        procs = []
        for gi, grp in enumerate(groups):
            if gi:
                time.sleep(80)
            sh = " && ".join(
                " ".join(f'"{c}"' for c in cmd(sdir / f"{n}.fasta", sout)) for n in grp)
            procs.append(subprocess.Popen(["bash", "-c", sh],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        for p in procs:
            p.wait()

    res["stagger"] = sample(run_staggered)
    res["stagger"]["per_fold_s"] = round(res["stagger"]["seconds"] / len(DESIGNS), 1)
    res["stagger"]["speedup"] = round(SERIAL_S / res["stagger"]["per_fold_s"], 2)
    res["stagger"]["verify"] = [verify(n, sout / f"boltz_results_{n}" / "predictions" / n)
                                for n in DESIGNS]
    s = res["stagger"]
    print(f"  {s['seconds']}s total | {s['per_fold_s']}s/fold | speedup {s['speedup']}x")
    print(f"  GPU peak {s['gpu_mem_peak_MiB']} MiB | max concurrent CUDA procs "
          f"{s['max_concurrent_cuda_procs']} | {s['samples_with_2_procs']} samples with "
          f"2 procs on the GPU | RSS peak {s['rss_peak_MB']} MB", flush=True)

    print("\n=== byte verification ===")
    for arm in ("batch", "stagger"):
        for v in res[arm]["verify"]:
            ok = v["bytes_same"] and v["pae_same"]
            print(f"  {arm:<9}{v['label']:<10}{v['models']}/5 models  "
                  f"bytes={v['bytes_same']}  pae={v['pae_same']}  "
                  f"max_dxyz={v['max_dxyz']} A  {'OK' if ok else '*** DIFFERS ***'}")
    (ROOT / "results.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
