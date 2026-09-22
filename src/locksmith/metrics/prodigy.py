"""Binding free energy and intermolecular contacts, via PRODIGY.

PRODIGY lives in its own environment (it requires numpy>=2, DockQ requires
numpy<2) and is invoked as a subprocess.

Selection is ALWAYS explicit: `--selection A,B C` scores antibody-vs-antigen.
Run without --selection on a 3-chain file, PRODIGY silently scores a different
interface -- on 5GGS it returns the heavy/light interface, which is large,
plausible, and not what any of the rubric's bands mean.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from locksmith.types import MetricResult, Structure

PRODIGY = shutil.which("prodigy") or "prodigy"
_AFFINITY = re.compile(r"Predicted binding affinity \(kcal\.mol-1\):\s*(-?[\d.]+)")
_CONTACTS = re.compile(r"No\. of intermolecular contacts:\s*(\d+)")
_KD = re.compile(r"Predicted dissociation constant \(M\).*?:\s*([\d.eE+-]+)")


def compute(struct: Structure, *, temperature: float = 25.0) -> dict[str, MetricResult]:
    proc = subprocess.run(
        [PRODIGY, str(struct.pdb), "--selection", "A,B", "C",
         "--temperature", str(temperature)],
        capture_output=True, text=True, timeout=300,
    )
    out = proc.stdout + proc.stderr
    if "No contacts found" in out:
        return {
            "dg": MetricResult(None, skipped_reason="no antibody-antigen contacts"),
            "contacts": MetricResult(0, detail="no interface"),
        }
    dg = _AFFINITY.search(out)
    nc = _CONTACTS.search(out)
    kd = _KD.search(out)
    if not dg:
        raise RuntimeError(f"PRODIGY failed on {struct.pdb}:\n{out[-800:]}")
    return {
        "dg": MetricResult(float(dg.group(1)),
                           detail=f"Kd {kd.group(1)} M" if kd else ""),
        "contacts": MetricResult(int(nc.group(1)) if nc else None),
    }
