#!/usr/bin/env python3
"""Prepare the 18 UNCONDITIONED backbones for sequencing and scoring.

WHY THIS ARM MATTERS. The conditioned arm has scores for everything — ipSAE, DockQ,
interface pLDDT — and its comparison arm has none. 18 unconditioned backbones were
generated on the pod (`runs/challenge2_pod/c2/unconditioned/un_*.pdb`) and never taken
past the backbone stage. Two live questions cannot be answered without them:

  1. **Range restriction vs a dead selector.** The conditioned pool's viability sits at a
     constant ~8% per sequence with no backbone heterogeneity (χ² = 22.91 on 17 df,
     p = 0.152). That reads as "the generator's ceiling", but it is also what you would
     see if the SELECTION on `interaction_pae` were noise — measured at ICC 0.000 — and
     the pool were simply never sorted. An unconditioned arm carried to the same depth
     separates those: if unconditioned designs score the same, selection did nothing.
  2. **The unconditioned arm's targeting baseline**, which this script computes now, for
     free, and which the 2026-09-21 pilot reported as ≈0.501.

WHAT NEEDS A GPU, AND WHAT DOES NOT. **Nothing here needs renting, and this docstring
asserted otherwise for eleven days.** RFantibody's bundled ProteinMPNN branches on
`torch.cuda.is_available()` and falls back to CPU (`proteinmpnn_interface_design.py:85-90`);
in `~/.venvs/rfab-cpu` (torch 2.2.1+cpu) that is False, and it generated 2 sequences in 1
second on 2026-10-03. The torch/PTX pin cited below is real but says nothing about the CPU
path. The only true obstacle is that the CLI subprocesses a bare `python`
(`cli/inference.py:294`), so the venv's `bin` must be on PATH:

    PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 8 -t 0.2

This is also the TOOL-MATCHED copy -- same entry point as `pod/01_run.sh:69`, same weights
(ProteinMPNN_v48_noise_0.2.pt), same temperature. The arms would differ in device, not in
code, weights or flags; state that on the result. See results/retractions.md B12, which
records that the project proved this on 2026-09-23 and wrote down the opposite on 09-28.

The original (wrong) split follows:

    backbones           DONE — 18 already on disk from the 2026-09-21 pod run
    frac_iface_on_epitope   CPU, runs here, no GPU (this script, no flags)
    sequences           ProteinMPNN → **local CPU, free** (CORRECTED 2026-10-03; this
                        docstring said "rented sm_86" from 2026-09-22 and was wrong)
    fold + score        Boltz-2 → **local, free**; torch 2.11+cu128 runs on sm_120

STUBBED, STATED PLAINLY. This script does NOT drive the fold. That path already exists
and is validated (`scripts/72_challenge2_fold.py`), but its input directory is hardcoded
to the conditioned arm's `seq/`. Writing a second, untested fold driver here to save one
edit would be worse than saying so: when the sequences come back, either parameterise 72's
input directory or copy them into the layout it expects. Nothing below folds anything.

    uv run python scripts/96_sequence_unconditioned.py          # verify + baseline (CPU)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

UNCOND = Path("runs/challenge2_pod/c2/unconditioned")
COND = Path("runs/challenge2_pod/c2/bb")
OUT = Path("results/unconditioned_baseline.md")

_spec = importlib.util.spec_from_file_location(
    "_pn", Path(__file__).resolve().parent / "70_epitope_patch_null.py")
_pn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pn)        # reuse ITS parser and epitope ordinals


def score(path: Path):
    chains, order, loop_abs = _pn.parse(path)
    if not {"H", "L", "T"} <= set(chains) or not loop_abs:
        return None
    tnums = sorted(chains["T"])
    loop_pts = np.array([q for i in loop_abs if 1 <= i <= len(order)
                         for q in chains[order[i - 1][0]][order[i - 1][1]]])
    con = set()
    for n in tnums:
        pts = np.array(chains["T"][n])
        if (((pts[:, None, :] - loop_pts[None, :, :]) ** 2).sum(-1) <= _pn.CUTOFF2).any():
            con.add(n)
    if not con:
        return {"file": path.name, "iface": 0, "frac": None}
    epi = {tnums[i] for i in _pn.EPITOPE if i < len(tnums)}
    return {"file": path.name, "iface": len(con), "frac": len(con & epi) / len(con)}


def main() -> int:
    if not UNCOND.exists():
        print(f"{UNCOND} missing", file=sys.stderr); return 1
    un = [r for r in (score(p) for p in sorted(UNCOND.glob("un_*_0.pdb"))) if r]
    co = [r for r in (score(p) for p in sorted(COND.glob("bb_*_0.pdb"))) if r]
    if not un:
        print("no unconditioned backbones parsed", file=sys.stderr); return 1

    uf = [r["frac"] for r in un if r["frac"] is not None]
    cf = [r["frac"] for r in co if r["frac"] is not None]

    L = []; w = L.append
    w("# The unconditioned arm — what is already on disk, and what is missing")
    w("")
    w(f"`scripts/96_sequence_unconditioned.py`. CPU only. "
      f"{len(un)} unconditioned backbones, {len(co)} conditioned, both from the "
      f"2026-09-21 pod run.")
    w("")
    w("## Targeting baseline, computed here")
    w("")
    w("| arm | n | mean `frac_iface_on_epitope` | sd | min | max |")
    w("|---|---|---|---|---|---|")
    for name, xs in (("conditioned", cf), ("**unconditioned**", uf)):
        if xs:
            w(f"| {name} | {len(xs)} | **{np.mean(xs):.3f}** | {np.std(xs, ddof=1):.3f} | "
              f"{min(xs):.3f} | {max(xs):.3f} |")
    w("")
    w("The unconditioned mean is not zero and should not be: the epitope is 26 of 113 "
      "residues on a small IgV domain, so a patch drawn at random already captures about "
      "a quarter of any interface. That denominator is why the 2026-09-21 two-arm "
      "comparison was replaced by the per-backbone patch null in `scripts/70` — and why "
      "the *decoy* control in `scripts/95` is the one that can actually fail.")
    w("")
    w("| backbone | iface residues | frac on epitope |")
    w("|---|---|---|")
    for r in un:
        f = "—" if r["frac"] is None else f"{r['frac']:.3f}"
        w(f"| `{r['file']}` | {r['iface']} | {f} |")
    w("")
    w("## What is missing, and where it has to run")
    w("")
    w("| step | tool | where | status |")
    w("|---|---|---|---|")
    w("| backbones | RFdiffusion | pod, 2026-09-21 | **done**, 18 on disk |")
    w("| targeting baseline | this script | local CPU | **done**, above |")
    w("| sequences | ProteinMPNN | **local CPU, free** | missing |")
    w("| fold + score | Boltz-2 | **local, free** | missing |")
    w("")
    w("**Nothing here needs renting.** This table said `rented sm_86` for the sequencing "
      "row from 2026-09-22 to 2026-10-03, on reasoning that is true in every clause and "
      "false in its conclusion: RFantibody pins `torch==2.3.*`, DGL ships no matching ABI, "
      "and those wheels carry no PTX, so nothing reaches `sm_120` -- all correct, and the "
      "CPU was never in the comparison. RFantibody's bundled ProteinMPNN branches on "
      "`torch.cuda.is_available()` (`proteinmpnn_interface_design.py:85-90`) and generated "
      "2 sequences in 1 second on `~/.venvs/rfab-cpu` (torch 2.2.1+cpu):")
    w("")
    w("```")
    w('$ PATH="$HOME/.venvs/rfab-cpu/bin:$PATH" proteinmpnn -i bb -o seq -n 8 -t 0.2')
    w("No GPU found, running ProteinMPNN on CPU")
    w("```")
    w("")
    w("The one real obstacle is not a device problem and reads exactly like one: the CLI "
      "subprocesses a bare `python` (`cli/inference.py:294`), so without the venv's `bin` "
      "on PATH it dies `FileNotFoundError: 'python'`. See "
      "[register B12](retractions.md).")
    w("")
    w("**The tool-matching objection goes with it.** The reason to rent rather than use "
      "standalone ProteinMPNN was that the conditioned arm used RFantibody's bundled copy. "
      "This *is* that copy -- same entry point as `pod/01_run.sh:69`, same weights "
      "(`ProteinMPNN_v48_noise_0.2.pt`), same `-t 0.2`. The arms would differ in **device**, "
      "not in code, weights or flags; state that on the result.")
    w("")
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L[:24]))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
