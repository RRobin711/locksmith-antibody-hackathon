#!/usr/bin/env python3
"""Pembrolizumab under EXACTLY the conditions that produced 0.859.

WHY. `bb_8_0` scores ipSAE 0.859, which is the 100th percentile of the post-cutoff panel
(0 of 20 novel real crystals score above it) and the 95th of the pre-cutoff arm. A de novo
design outscoring real crystallised complexes is the precise shape of the MSA artefact this
project already fell for once, when the old design read 0.864 against pembrolizumab's 0.842.

The alignment is verified USED here (processed MSA width 123 = antigen length 123, depth
1024), so that specific artefact is excluded. What remains is whether 0.859 is a plausible
number for this task at all.

THE CONFOUND IN THE PERCENTILE COMPARISON. Our design has a **memorised antigen and a novel
antibody**. The post-cutoff panel has **novel antigens and novel antibodies** -- a strictly
harder task. PD-1 is pre-cutoff, deeply represented, and carries a 3407-sequence alignment.
Comparing a memorised-antigen prediction against novel-antigen complexes is not
apples-to-apples, and this project has a standing rule to screen antibody and antigen
novelty SEPARATELY for exactly this reason.

THE FIX IS A MATCHED CONTROL, not an argument. Pembrolizumab is a real, licensed anti-PD-1
antibody with a solved structure against this antigen. Folded under **identical**
conditions -- same 123-residue handbook antigen, same `pd1_123_handbook.csv` alignment,
recycling 10, 5 diffusion samples, seed 1 -- it is the correct reference for what a *known
true binder on this exact target* scores through this exact pipeline.

Existing pembrolizumab numbers are NOT comparable: 0.874 came from the 113-mer with the old
cached alignment, 0.843 from the 119-mer with a server alignment. Different construct,
different alignment, different run.

READING IT, fixed before folding:
  * pembrolizumab lands near or above 0.859 -> 0.859 is what a true binder on a memorised
    antigen scores here. The design is in credible company and the percentile against
    novel-antigen complexes was the wrong comparison.
  * pembrolizumab lands well below 0.859 -> our de novo design outscores a licensed
    antibody on its own target under identical conditions. That is not credible on its
    face and the number needs a mechanism before it goes anywhere near a slide.
"""
from __future__ import annotations

import json, time
from pathlib import Path

import gemmi

from locksmith.fold import fold_is_complete
from locksmith.fold.boltz import fold
from locksmith.numbering import number

OUT = Path("runs/matched_control")
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
RECYCLING, SAMPLES, SEED = 10, 5, 1


def fv_pair(pdb: Path) -> tuple[str, str]:
    st = gemmi.read_structure(str(pdb)); st.setup_entities()
    h = l = None
    for ch in st[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        if len(res) < 50:
            continue
        s = gemmi.one_letter_code([r.name for r in res]).upper()
        if "X" in s:
            continue
        n = number(s)
        if n is None:
            continue
        if n.chain_type == "H" and h is None:
            h = n.fv
        elif n.chain_type in ("K", "L") and l is None:
            l = n.fv
    if not (h and l):
        raise RuntimeError(f"{pdb.name}: no Fv pair")
    return h, l


def main() -> int:
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    arms = [("mc_pembrolizumab", "data/refs/5ggs.pdb", "licensed anti-PD-1, true binder"),
            ("mc_nivolumab",     "data/refs/5wt9.pdb", "licensed anti-PD-1, true binder"),
            ("mc_trastuzumab",   "runs/calibration/pdb/1n8z.pdb",
             "anti-HER2 -- NEGATIVE, must not score high")]
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    print(f"antigen {len(ag)} aa, alignment {MSA.name}, recycling {RECYCLING}, "
          f"{SAMPLES} samples -- identical to the run that produced 0.859\n", flush=True)
    for label, pdb, what in arms:
        h, l = fv_pair(Path(pdb))
        pred = OUT / label / f"boltz_results_{label}" / "predictions" / label
        if fold_is_complete(pred, label, n_models=SAMPLES):
            print(f"{label:<20} already folded", flush=True)
            continue
        print(f"{label:<20} {what:<36} H{len(h)} L{len(l)} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, h, l, ag, out_root=OUT, antigen_msa=MSA, seed=SEED,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                                   # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300]}
            print(f"FAILED: {str(e)[:170]}", flush=True)
        (OUT / "fold_log.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
