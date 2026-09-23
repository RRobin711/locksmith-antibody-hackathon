#!/usr/bin/env python3
"""Follow-up to the negative control, on a PD-1 construct that contains BOTH epitopes.

THIS IS A FOLLOW-UP, NOT THE PRE-REGISTERED EXPERIMENT. The pre-registration
(`results/prereg_2026-09-22_calibration_and_negative_control.md`) fixed three decision
rules before any fold completed, and Rule 3 fired: nivolumab, a licensed anti-PD-1
antibody used as a positive control, scored ipSAE **0.017** against the 0.60 gate. By the
rule written in advance, that makes the negative arm *uninterpretable* rather than
reassuring, and it is reported that way. Nothing below retracts it. This script runs a
second, separate experiment whose result is quoted as a follow-up.

--------------------------------------------------------------------------------------
WHY THE POSITIVE CONTROL FAILED -- diagnosed from geometry, not from the literature
--------------------------------------------------------------------------------------
Measuring the actual crystal contacts (heavy-atom, 4.5 A) in each antibody's own structure:

  * **Nivolumab (5WT9)** has a 14-residue epitope:
    `L25 D26 S27 P28 D29 R30 P31 T59 S60 L128 A129 P130 K131 A132`.
    **Six of those fourteen -- L25 through R30 -- are the `LDSPDR` N-terminal segment.**
  * **Pembrolizumab (5GGS)** has a 24-residue epitope, every residue of which lies inside
    our construct. It scored ipSAE 0.874.

Every fold in this project used a **113-residue PD-1 beginning at `PWNPP`** (residue P31),
inherited from the 5GGS construct. That start point **deletes 43% of nivolumab's binding
site.** Nivolumab did not fail because the pipeline is broken; it failed because the
molecule it was docked against does not contain the surface it binds.

Two things follow, and the second is the one worth keeping:

1. A positive control can fail for a reason that has nothing to do with the thing being
   controlled for. "The positive failed, so the panel is broken" would have been the wrong
   conclusion, and so would "the positive failed, so ignore it". The right move is to ask
   *why*, from data, before deciding which.
2. **The construct we fold is not the construct we submit.** The submitted FASTA carries a
   123-residue PD-1 including `DSPDRP`; every fold used the 113-mer without it. That
   discrepancy was invisible for the whole project because pembrolizumab -- the only
   reference ever folded -- does not touch the missing region.

--------------------------------------------------------------------------------------
THE CONSTRUCT USED HERE
--------------------------------------------------------------------------------------
`LDSPDR` (residues 25-30) prepended to the existing 113-mer, giving **119 residues
spanning PD-1 25-143**. This is the minimal change that restores nivolumab's epitope while
leaving every residue the previous run used in place.

**MSA.** The cached alignment `pd1_5ggs.csv` is aligned to the 113-mer query and cannot be
reused against a longer one. All rows here therefore take a fresh MMseqs2 query. That is
acceptable *because the antigen is byte-identical across all ten rows*, so the server
returns the same alignment to each -- unlike the situation the cache was built for, where
different antigens would have drawn different alignments into a ranking. The assumption is
not assumed: the depth of each row's alignment is recorded and compared at the end, and a
mismatch is reported rather than swallowed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold
from locksmith.numbering import number

OUT = Path("runs/negctrl_nloop")
PDBDIR = Path("runs/calibration/pdb")
LOG = OUT / "fold_log.json"
RECYCLING = 10
SAMPLES = 5

NLOOP = "LDSPDR"                  # PD-1 25-30, nivolumab's N-terminal epitope
CORE = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRDF"
        "HMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")
PD1 = NLOOP + CORE                # 119 residues, PD-1 25-143


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prev = json.loads(Path("runs/negctrl/arms.json").read_text())
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    meta = {}

    assert len(PD1) == 119, f"construct is {len(PD1)} residues, expected 119"

    for label, a in prev.items():
        new = label.replace("neg_", "nl_")
        meta[new] = dict(a) | {"construct": "PD-1 25-143 (119 aa, N-loop restored)"}
        d = OUT / new / f"boltz_results_{new}" / "predictions" / new
        if fold_is_complete(d, new, n_models=SAMPLES):
            print(f"{new:<24} already folded", flush=True)
            continue
        print(f"{new:<24} {a['expected']:<8} vs PD-1(119) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            fold(new, a["heavy"], a["light"], PD1, out_root=OUT, antigen_msa=None,
                 seed=1, diffusion_samples=SAMPLES, recycling_steps=RECYCLING,
                 timeout=5400)
            log[new] = {"ok": True, "seconds": round(time.time() - t0, 1)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[new] = {"ok": False, "error": str(e)[:300]}
            print(f"FAILED: {str(e)[:180]}", flush=True)
        LOG.write_text(json.dumps(log, indent=1))
        (OUT / "arms.json").write_text(json.dumps(meta, indent=1))

    # ---- verify the fresh alignments really did agree across rows ----
    depths = {}
    for new in meta:
        a3m = list((OUT / new).rglob("uniref.a3m"))
        if a3m:
            depths[new] = sum(1 for l in a3m[0].read_text().splitlines()
                              if l.startswith(">"))
    if depths:
        uniq = sorted(set(depths.values()))
        print(f"\nMSA depth per row: {depths}")
        print(f"distinct depths: {uniq}" +
              ("  <- IDENTICAL, alignment did not drift" if len(uniq) == 1 else
               "  <- DIFFER: the alignment drifted between rows, which is exactly what "
               "the cached-MSA policy exists to prevent. Treat cross-row comparisons "
               "with caution and say so in the write-up."))
        (OUT / "msa_depths.json").write_text(json.dumps(depths, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
