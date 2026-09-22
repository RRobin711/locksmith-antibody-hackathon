#!/usr/bin/env python3
"""CPU launcher for RFantibody's RFdiffusion.

WHY THIS EXISTS -- one shim, disclosed, and nothing else.

NVIDIA's vendored SE3Transformer (include/SE3Transformer/) wraps every layer in
`torch.cuda.nvtx` profiler ranges:

    include/SE3Transformer/se3_transformer/model/basis.py:32
    include/SE3Transformer/se3_transformer/model/layers/convolution.py:34
        from torch.cuda.nvtx import range as nvtx_range

On a CPU-only torch build those raise `RuntimeError: NVTX functions not installed`.
NVTX is NVIDIA Tools Extension: named markers a profiler reads.  It performs no
computation and touches no tensor, so replacing it with a null context manager
cannot change a single number -- it only stops the profiler annotations being
emitted.

This is NOT patching, rebuilding or source-compiling the library: no vendored file
is modified, nothing is recompiled.  The shim is applied here, in our own entry
point, BEFORE rfantibody is imported -- which matters, because the modules above
bind `range` at import time, so a later patch would be too late.
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

# Import only AFTER the shim is in place.
from rfantibody.rfdiffusion.inference import model_runners  # noqa: E402,F401

if __name__ == "__main__":
    sys.argv[0] = "rfdiffusion_inference.py"
    runpy_target = f"{sys.prefix}"
    import runpy
    runpy.run_path(
        "/home/rrobin711/.cache/rfantibody/scripts/rfdiffusion_inference.py",
        run_name="__main__",
    )
