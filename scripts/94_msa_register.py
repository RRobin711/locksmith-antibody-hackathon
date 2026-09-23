#!/usr/bin/env python3
"""Was the shipped Challenge 2 structure folded with a MISALIGNED antigen alignment?

THE OBSERVATION. `data/msa_cache/pd1_5ggs.csv` is aligned to a **113-residue** PD-1 query
beginning `PWNPP`. The shipped Challenge 2 fold (`scripts/82`, the S->A sequon fix) passed
that cache alongside the handbook's **123-residue** antigen beginning `DSPDRP`. Boltz did
not complain. The processed alignment it wrote is **113 columns wide for a 123-residue
chain**, and the cached query sits at **offset 5** inside the folded sequence.

THE QUESTION. Does Boltz re-align the cached MSA to the input sequence, or map it
positionally from index 0? If positionally, every column is out of register by five
residues across the whole antigen, and the shipped structure was predicted with an antigen
alignment that points at the wrong residues.

WHY THIS CANNOT BE SETTLED BY READING. The processed npz records widths and offsets, not
the mapping policy; inferring the policy from the file is exactly the sort of reasoning
that has produced three wrong answers on this project in one night. An empirical
comparison settles it in three folds.

THE ARMS -- identical design, identical flags, identical sampling. Only the
antigen/alignment pairing changes:

  A `as_shipped`   123-residue antigen + the cached 113-column alignment.
                   Reproduces the shipped fold exactly.
  B `matched_113`  113-residue antigen + the same cached alignment.
                   Now query and input agree, so the alignment is in register by
                   construction. Isolates the REGISTER while holding the alignment fixed.
  C `matched_123`  123-residue antigen + a fresh MMseqs2 query for that exact sequence.
                   In register AND full-length. Isolates the CONSTRUCT.

READING THE RESULT, fixed before running:
  * A ~= B ~= C  -> Boltz re-aligns; the cached-MSA/long-antigen pairing is harmless and
    the shipped structure is sound. Report and move on.
  * A differs from BOTH B and C -> the pairing degrades the prediction. The shipped
    Challenge 2 structure was folded under a misaligned alignment and every metric derived
    from it inherits that. This would be the most serious defect found in the submission.
  * B ~= A but C differs -> the effect is the construct, not the register.

`~=` means within the diffusion envelope already measured for this design: composite 91.2
on all five samples, ipSAE 0.619-0.781. An ipSAE shift inside that band is noise; one that
moves the composite, or moves ipSAE outside 0.619-0.781, is signal.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold, PD1_MSA

OUT = Path("runs/msa_register")
PKG = Path("submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge2/sequences/design_1.fasta")
CORE113 = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRD"
           "FHMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")
RECYCLING = 10
SAMPLES = 5


def read_fasta(p: Path) -> dict[str, str]:
    out, k = {}, None
    for line in p.read_text().splitlines():
        if line.startswith(">"):
            k = line[1:].strip()
            out[k] = ""
        elif k:
            out[k] += line.strip()
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fa = read_fasta(PKG)
    heavy, light = fa["Heavy_Chain"], fa["Light_Chain"]
    ag123 = fa["Antigen"]
    assert len(ag123) == 123, f"packaged antigen is {len(ag123)} residues, expected 123"
    assert CORE113 in ag123, "the 113-mer is not a substring of the packaged antigen"
    print(f"packaged antigen {len(ag123)} aa; cached-MSA query sits at offset "
          f"{ag123.find(CORE113)}\n", flush=True)

    arms = [
        ("as_shipped",  ag123,   PD1_MSA, "123-mer antigen + cached 113-column MSA"),
        ("matched_113", CORE113, PD1_MSA, "113-mer antigen + cached 113-column MSA"),
        ("matched_123", ag123,   None,    "123-mer antigen + fresh MSA for that sequence"),
    ]
    log = {}
    for label, antigen, msa, what in arms:
        d = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(d, label, n_models=SAMPLES):
            print(f"{label:<14} already folded", flush=True)
            continue
        print(f"{label:<14} {what} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, heavy, light, antigen, out_root=OUT, antigen_msa=msa, seed=1,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1), "what": what}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300], "what": what}
            print(f"FAILED: {str(e)[:180]}", flush=True)
        (OUT / "fold_log.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
