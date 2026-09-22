#!/usr/bin/env python3
"""Fold the variant panel. Gates 1c and 1d.

Modes:
  smoke   one Fab fold, with VRAM sampled -- run FIRST; no Fab has ever been
          folded on this machine and 549 residues is ~2.6x the Fv pair tensor
  noise   3 variants x 3 seeds x {fv, fab} -- the reliability floor
  panel   every variant x {fv, fab}, seed 1
  af2     ColabFold subset, single-sequence MSA only

Results append to runs/panel/index.jsonl, one line per fold, so an interrupted
run resumes by skipping labels already present (see LEARNINGS: make long jobs
resumable).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from locksmith.design.variants import Variant, load
from locksmith.fold import FoldFailed
from locksmith.fold import boltz as boltz_drv
from locksmith.fold import colabfold as cf_drv
from locksmith.io.pdb import chains, seq_for_folding
from locksmith.numbering import number

REFS = Path("data/refs/prepared/5GGS_ABZ.pdb")
VARIANTS = Path("designs/variants.json")
OUT = Path("runs/panel")
INDEX = OUT / "index.jsonl"
NOISE_VARIANTS = ["v00_wt", "v04_h3_4", "v08_h3_13"]
NOISE_SEEDS = [1, 2, 3]
AF2_SUBSET = ["v00_wt", "v02_h3_2", "v04_h3_4", "v06_h3_8", "v08_h3_13",
              "v11_h1h2h3_9", "v12_h3_polyG"]


def constructs() -> tuple[dict, str]:
    """Return per-variant construct builders plus the antigen sequence."""
    heavy = seq_for_folding(REFS, "A")
    light = seq_for_folding(REFS, "B")
    antigen = seq_for_folding(REFS, "C")
    nh, nl = number(heavy), number(light)
    h_pre, h_post = heavy[: nh.query_start], heavy[nh.query_end + 1 :]
    l_pre, l_post = light[: nl.query_start], light[nl.query_end + 1 :]

    def build(v: Variant, form: str) -> tuple[str, str, str]:
        if form == "fv":
            return v.heavy_fv, v.light_fv, antigen
        # Fab: the SAME mutated variable domain, grafted back onto the constant
        # domains. Identical V region in both forms is what makes the Fv-vs-Fab
        # comparison paired rather than two unrelated measurements.
        return (h_pre + v.heavy_fv + h_post, l_pre + v.light_fv + l_post, antigen)

    return build, antigen


def done_labels() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(ln)["label"] for ln in INDEX.read_text().splitlines() if ln.strip()}


def record(rec: dict) -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with INDEX.open("a") as f:
        f.write(json.dumps(rec) + "\n")


class VramSampler(threading.Thread):
    """Poll nvidia-smi so a fold that survives can still report how close it came."""

    def __init__(self, interval: float = 1.0):
        super().__init__(daemon=True)
        self.interval, self.peak, self._done = interval, 0, threading.Event()

    def run(self) -> None:
        while not self._done.is_set():
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10).stdout.strip()
                self.peak = max(self.peak, int(out.splitlines()[0]))
            except Exception:                                    # noqa: BLE001
                pass
            self._done.wait(self.interval)

    def stop(self) -> int:
        self._done.set()          # NB: not self._stop -- that is a Thread method
        self.join(timeout=5)
        return self.peak


def run_boltz(v: Variant, form: str, seed: int, build, *, sample_vram=False) -> bool:
    label = f"{v.name}__{form}__s{seed}"
    if label in done_labels():
        print(f"  skip {label} (already done)")
        return True
    h, l, a = build(v, form)
    sampler = VramSampler() if sample_vram else None
    if sampler:
        sampler.start()
    try:
        r = boltz_drv.fold(label, h, l, a, out_root=OUT / form, construct=form, seed=seed)
    except FoldFailed as e:
        peak = sampler.stop() if sampler else None
        print(f"  FAILED {label}: {e}", file=sys.stderr)
        record({"label": label, "variant": v.name, "construct": form, "seed": seed,
                "predictor": "boltz2", "ok": False, "error": str(e)[:500],
                "peak_vram_mib": peak})
        return False
    peak = sampler.stop() if sampler else None
    print(f"  {label}: {r.n_residues} res, {r.seconds:.1f}s"
          + (f", peak VRAM {peak} MiB" if peak else ""))
    record({"label": label, "variant": v.name, "construct": form, "seed": seed,
            "predictor": "boltz2", "ok": True, "pdb": str(r.pdb), "pae": str(r.pae),
            "plddt": str(r.plddt), "seconds": r.seconds, "n_residues": r.n_residues,
            "chain_lengths": list(r.chain_lengths), "peak_vram_mib": peak})
    return True


def run_af2(v: Variant, form: str, build) -> bool:
    label = f"{v.name}__{form}__af2"
    if label in done_labels():
        print(f"  skip {label} (already done)")
        return True
    h, l, a = build(v, form)
    try:
        r = cf_drv.fold(label, h, l, a, out_root=OUT / f"af2_{form}",
                        construct=form, msa_mode="single_sequence")
    except FoldFailed as e:
        print(f"  FAILED {label}: {e}", file=sys.stderr)
        record({"label": label, "variant": v.name, "construct": form, "seed": 1,
                "predictor": "alphafold2_multimer_v3", "ok": False, "error": str(e)[:500]})
        return False
    print(f"  {label}: {r.n_residues} res, {r.seconds:.1f}s")
    record({"label": label, "variant": v.name, "construct": form, "seed": 1,
            "predictor": "alphafold2_multimer_v3", "ok": True, "pdb": str(r.pdb),
            "pae": str(r.pae), "plddt": None, "seconds": r.seconds,
            "n_residues": r.n_residues, "chain_lengths": list(r.chain_lengths)})
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["smoke", "noise", "panel", "af2"])
    args = ap.parse_args()

    panel = load(VARIANTS)
    by_name = {v.name: v for v in panel}
    build, _ = constructs()

    if args.mode == "smoke":
        v = by_name["v00_wt"]
        h, l, a = build(v, "fab")
        print(f"Fab smoke fold: H={len(h)} L={len(l)} Ag={len(a)} "
              f"total={len(h)+len(l)+len(a)} residues")
        ok = run_boltz(v, "fab", 1, build, sample_vram=True)
        if not ok:
            print("\nFab fold FAILED -- stopping. Do not queue the panel.", file=sys.stderr)
            return 1
        return 0

    if args.mode == "noise":
        for name in NOISE_VARIANTS:
            for seed in NOISE_SEEDS:
                for form in ("fv", "fab"):
                    run_boltz(by_name[name], form, seed, build)
        return 0

    if args.mode == "panel":
        for v in panel:
            for form in ("fv", "fab"):
                run_boltz(v, form, 1, build)
        return 0

    if args.mode == "af2":
        for name in AF2_SUBSET:
            run_af2(by_name[name], "fv", build)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
