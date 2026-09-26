#!/usr/bin/env python3
"""Fold OUR submitted designs under the calibration panel's exact settings.

Without this the comparison is invalid. Challenge 1's submitted fold ran at
`recycling_steps=3` and `diffusion_samples=1`; the panel and the negative control run at
10 and 5. Quoting a percentile for a design measured under different sampling depth would
compare the design's *settings* with the panel's, not the design with the panel --  and
this project has already measured recycling depth moving a single ipSAE by 0.601, which is
larger than any effect being discussed.

So both designs are refolded here at recycling 10, 5 diffusion samples, against the same
113-residue PD-1 construct and the same cached alignment used by every other row. Three
arms -- negative controls, positive controls, test articles -- now differ in exactly one
thing: which antibody is present.

CONSTRUCT NOTE. The submitted Challenge 1 FASTA carries a full IgG1 heavy chain with a
C-terminal His-tag (232 residues) and a full kappa light chain (218). The panel is Fv, so
the submitted chains are trimmed to their variable domains by ANARCII -- the same
operation applied to every antibody in the panel. Challenge 2 was designed as an Fv
already (116/108) and is used as-is.

The submitted FASTA also carries a longer PD-1 (123 residues, with the `DSPDRP` and
`VTERR` flanks). Every fold in this project used the 113-residue core, and that is what is
used here, so the antigen is byte-identical across all three arms.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold, PD1_MSA
from locksmith.numbering import number

OUT = Path("runs/negctrl")                 # same tree: one axis, one scorer
LOG = OUT / "fold_log.json"
RECYCLING = 10
SAMPLES = 5
PD1 = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRDF"
       "HMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")

ARMS = [
    ("neg_ch1-design", "Challenge 1 design", "PD-1 (ours)",
     "submission/RYAN_BINNY/RYAN_BINNY_Challenge1/sequences/design_1.fasta"),
    ("neg_ch2-design", "Challenge 2 design", "PD-1 (ours)",
     "submission/RYAN_BINNY/RYAN_BINNY_Challenge2/sequences/design_1.fasta"),
]


def read_fasta(p: Path) -> dict[str, str]:
    out, key = {}, None
    for line in p.read_text().splitlines():
        if line.startswith(">"):
            key = line[1:].strip()
            out[key] = ""
        elif key:
            out[key] += line.strip()
    return out


def to_fv(seq: str) -> str:
    n = number(seq)
    if n is None:
        raise RuntimeError(f"ANARCII did not number a {len(seq)}-residue chain")
    return n.fv


def already_done(label: str) -> bool:
    return fold_is_complete(
        OUT / label / f"boltz_results_{label}" / "predictions" / label,
        label, n_models=SAMPLES)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    meta_path = OUT / "arms.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    for label, name, target, fasta in ARMS:
        f = read_fasta(Path(fasta))
        heavy, light = to_fv(f["Heavy_Chain"]), to_fv(f["Light_Chain"])
        meta[label] = {"pdb": "-", "name": name, "target": target,
                       "expected": "test", "heavy": heavy, "light": light,
                       "n_res": len(heavy) + len(light) + len(PD1)}
        meta_path.write_text(json.dumps(meta, indent=1))
        if already_done(label):
            print(f"{label:<22} already folded", flush=True)
            continue
        print(f"{label:<22} test     H{len(heavy)} L{len(light)} vs PD-1 ...",
              end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, heavy, light, PD1, out_root=OUT, antigen_msa=PD1_MSA, seed=1,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300]}
            print(f"FAILED: {str(e)[:200]}", flush=True)
        LOG.write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
