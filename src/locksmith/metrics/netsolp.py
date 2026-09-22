"""Sequence-only solubility, via NetSolP-1.0 (DTU).

NetSolP is an ESM-based classifier distributed as *quantized ONNX* models, so
inference needs no GPU and no ESM backbone weights -- only onnxruntime plus
`fair-esm` (the alphabet is a pickled `esm.data.Alphabet`).  It therefore runs on
CPU **concurrently with GPU folding** and never contends for the fold queue.

Two things live outside the vault because they are bulky and platform-specific
(the vault syncs to a machine that cannot use them):

    ~/.local/share/locksmith/netsolp   predict.py, data.py, models/*.onnx
    ~/.venvs/netsolp                   its own env (numpy 2; isolated from DockQ)

Override with NETSOLP_DIR / NETSOLP_PYTHON.

WHY MODEL_TYPE MATTERS MORE THAN IT LOOKS
-----------------------------------------
NetSolP ships three solubility predictors.  On pembrolizumab -- a marketed
antibody, our positive control, which must pass every developability gate -- they
disagree about whether it is soluble at all (measured 2026-09-16, cutoff 0.50):

    convention      ESM1b(5-fold)   ESM1b-distilled   ESM12(5-fold)
    VH                   0.733            0.637            0.379
    VL                   0.569            0.463            0.346
    Fab heavy            0.623            0.491            0.352
    Fab light            0.626            0.448            0.312

Only the full **ESM1b 5-fold ensemble** clears the cutoff everywhere.  The other
two fail a licensed drug -- a false negative that would silently discard good
designs, and it would look exactly like a design problem rather than a
configuration one.  Hence ESM1b is the default and the choice is a recorded
convention, not a constant buried here.

The cost is real: ~11 s/sequence over 24 threads versus ~2 s for ESM12.  Paid on
CPU while the GPU folds, so it is off the critical path.
"""
from __future__ import annotations

import csv
import os
import subprocess
import tempfile
from pathlib import Path

from locksmith.types import MetricResult

NETSOLP_DIR = Path(os.environ.get(
    "NETSOLP_DIR", Path.home() / ".local/share/locksmith/netsolp"))
NETSOLP_PYTHON = Path(os.environ.get(
    "NETSOLP_PYTHON", Path.home() / ".venvs/netsolp/bin/python"))

MODEL_TYPE = "ESM1b"    # ESM1b | ESM12 | Distilled | Both -- see module docstring
CHAIN_AGG = "min"       # min | mean -- a design is only as soluble as its worst chain
CONSTRUCT = "fv"        # fv | fab -- see below; the handbook says Fv, twice.

# THE HANDBOOK SPECIFIES THE Fv, AND THIS PROJECT FED IT THE Fab UNTIL 2026-09-20.
# S6.2.1: "NetSolP estimates the probability that the **Fv (VH + VL)** region will
# ..." and "NetSolP is run on the **Fv sequence** extracted from design_X.fasta";
# pipeline step 3: "Runs NetSolP on the **VH+VL** sequence". Every scoring script
# passed the full 219/217 aa Fab chains instead. The function parameters were even
# named fv_heavy/fv_light; the callers ignored that.
#
# It changes the numbers a lot, and it changes WHICH CHAIN IS LIMITING:
#     pembrolizumab   Fab heavy 0.623  Fab light 0.626   -> heavy limits, min 0.623
#                     Fv   VH   0.733  Fv   VL   0.569   -> LIGHT limits, min 0.569
# Measured across the 239 designs on the correct Fv input, the designed VH reaches
# 0.742 -- inside the Good band -- while VL is 0.5686 for every single design,
# because ProteinMPNN never touches the light chain. So the developability deficit
# is entirely one untouched chain, and the fix is to redesign the light-chain CDRs.
# On the Fab input that conclusion was invisible: the heavy chain looked limiting.


def _missing() -> str | None:
    """Return why NetSolP cannot run, or None if it can."""
    if not NETSOLP_PYTHON.exists():
        return f"NetSolP env not found at {NETSOLP_PYTHON}"
    if not (NETSOLP_DIR / "predict.py").exists():
        return f"NetSolP predict.py not found in {NETSOLP_DIR}"
    needed = [f"Solubility_{MODEL_TYPE}_{i}_quantized.onnx" for i in range(5)] \
        if MODEL_TYPE in ("ESM1b", "ESM12") else \
        [f"Solubility_ESM1b_distilled_quantized.onnx"]
    absent = [n for n in needed if not (NETSOLP_DIR / "models" / n).exists()]
    if absent:
        return f"NetSolP models missing from {NETSOLP_DIR/'models'}: {absent[0]} (+{len(absent)-1} more)"
    return None


def predict(seqs: dict[str, str], *, model_type: str = MODEL_TYPE,
            timeout: int = 1800) -> dict[str, float]:
    """Raw NetSolP solubility in [0,1] for each named sequence."""
    with tempfile.TemporaryDirectory() as td:
        fasta, out = Path(td) / "in.fasta", Path(td) / "out.csv"
        fasta.write_text("".join(f">{k}\n{v}\n" for k, v in seqs.items()))
        proc = subprocess.run(
            [str(NETSOLP_PYTHON), "predict.py",
             "--FASTA_PATH", str(fasta), "--OUTPUT_PATH", str(out),
             "--MODELS_PATH", str(NETSOLP_DIR / "models"),
             "--MODEL_TYPE", model_type, "--PREDICTION_TYPE", "S"],
            cwd=NETSOLP_DIR, capture_output=True, text=True, timeout=timeout,
        )
        # Assert on the artefact, never the exit code: boltz taught us that a
        # tool can print a traceback, write nothing, and still exit 0.
        if not out.exists():
            raise RuntimeError(
                f"NetSolP wrote no output (rc={proc.returncode}):\n"
                f"{(proc.stdout + proc.stderr)[-800:]}")
        rows = list(csv.DictReader(out.open()))

    got = {r["sid"]: r["predicted_solubility"] for r in rows}
    missing = set(seqs) - set(got)
    if missing:
        raise RuntimeError(f"NetSolP returned no prediction for {sorted(missing)}")
    vals = {}
    for k in seqs:
        v = got[k]
        if v in ("", "nan", None):
            raise RuntimeError(f"NetSolP returned an empty prediction for {k!r}")
        vals[k] = float(v)
    return vals


def _to_fv(seq: str, which: str) -> str:
    """Trim a Fab chain to its variable domain, located by ANARCII, not a fixed range."""
    from locksmith.numbering import number
    n = number(seq)
    if n is None:
        raise RuntimeError(f"could not number the {which} chain to find its V domain")
    return seq[n.query_start: n.query_end + 1]


def compute(fv_heavy: str, fv_light: str, *,
            construct: str = CONSTRUCT) -> dict[str, MetricResult]:
    """Developability gate input: the *less* soluble of the two chains.

    `construct="fv"` trims whatever it is given to the variable domain first, which
    is what the handbook specifies. Callers may pass full Fab chains; they will be
    trimmed. Pass construct="fab" to reproduce results from before 2026-09-20.
    """
    why = _missing()
    if why:
        return {"netsolp": MetricResult(None, skipped_reason=why)}

    if construct == "fv":
        fv_heavy, fv_light = _to_fv(fv_heavy, "heavy"), _to_fv(fv_light, "light")
    elif construct != "fab":
        raise ValueError(f"unknown netsolp construct {construct!r}")

    vals = predict({"heavy": fv_heavy, "light": fv_light})
    h, l = vals["heavy"], vals["light"]
    agg = min(h, l) if CHAIN_AGG == "min" else (h + l) / 2
    return {"netsolp": MetricResult(
        agg, detail=f"{MODEL_TYPE} {construct} {CHAIN_AGG}(H={h:.3f}, L={l:.3f})")}
