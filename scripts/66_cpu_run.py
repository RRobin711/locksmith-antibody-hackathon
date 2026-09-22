#!/usr/bin/env python3
"""Generic CPU entry point for RFantibody's console commands.

Applies the NVTX null-context shim (see scripts/65_rfdiff_cpu.py for the full
rationale) BEFORE importing rfantibody, then dispatches to one of the click
commands declared in RFantibody's pyproject [project.scripts]:

    rfdiffusion = rfantibody.cli.inference:rfdiffusion
    proteinmpnn = rfantibody.cli.inference:proteinmpnn
    rf2         = rfantibody.cli.inference:rf2

RF2 needs the shim as much as RFdiffusion does: rf2/network/SE3_network.py:3
imports the same vendored SE3Transformer.

Usage:  66_cpu_run.py <rfdiffusion|proteinmpnn|rf2> [args...]
"""
from __future__ import annotations

import contextlib
import sys

import torch

if not torch.cuda.is_available():
    @contextlib.contextmanager
    def _null_range(*_a, **_k):
        yield
    torch.cuda.nvtx.range = _null_range
    torch.cuda.nvtx.range_push = lambda *_a, **_k: None
    torch.cuda.nvtx.range_pop = lambda *_a, **_k: None
    print("[cpu-shim] torch.cuda.nvtx disabled (profiler markers only; no numerics)",
          file=sys.stderr, flush=True)

from rfantibody.cli import inference  # noqa: E402

if __name__ == "__main__":
    entry = sys.argv[1]
    sys.argv = [entry] + sys.argv[2:]
    getattr(inference, entry)()
