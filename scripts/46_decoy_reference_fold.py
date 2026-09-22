#!/usr/bin/env python3
"""The control that makes the TIM-3 result interpretable. Added 2026-09-20 ~01:40
AFTER seeing the specificity panel, and labelled as such.

WHAT PROMPTED IT. The named design scored ipSAE 0.624 / 0.612 / 0.469 against TIM-3
with dG -13.8 / -14.4 / -14.0, i.e. two of three seeds clear the rubric's 0.60
viability cutoff with strongly favourable dG. Against PD-L1 and ULBP6 ipSAE collapsed
to 0.000-0.012, so the metric demonstrably CAN go to zero -- which makes the TIM-3
number hard to dismiss and hard to interpret.

Two explanations fit equally well and they have opposite consequences:

  (a) OUR DESIGN is cross-reactive with TIM-3. TIM-3 is a human checkpoint receptor
      with the same Ig V-set fold as PD-1, so this is the realistic off-target risk
      and it would be a genuine problem with the molecule.
  (b) BOLTZ places ANY antibody on TIM-3 with a plausible-looking interface. Then the
      number says nothing about our design at all.

Nothing in the panel as run can separate them, because the panel varies the antigen
while holding the antibody fixed. Separating them needs the opposite: hold the
ANTIGEN fixed at TIM-3 and vary the antibody.

TWO REFERENCE ANTIBODIES AGAINST TIM-3, three seeds each:

  PEMBROLIZUMAB  -- a licensed, clinically specific anti-PD-1 antibody that certainly
                    does not bind TIM-3. This is the NEGATIVE reference. If
                    pembrolizumab also scores ~0.62 against TIM-3, explanation (b) is
                    correct and the finding is about the predictor.
  8TBB Fab       -- the antibody from the deposited Fab-TIM-3 complex, i.e. a REAL
                    TIM-3 binder. POSITIVE reference: it shows what a true binder
                    scores under this exact protocol, which sets the scale the 0.62
                    has to be read against. Without it a "low" score has no referent.

This is the control named as missing in the specificity pre-registration ("a positive
decoy control ... 8TBB is exactly that complex, already on disk") plus the negative
reference the panel turned out to need. It is being run because the data demanded it,
which is a different thing from a pre-registered hypothesis, and the writeup says so:
**the reference folds are exploratory, run after seeing the result they interpret.**
The pre-registered comparison remains the one in the specificity prereg.

Interpretation fixed in advance of these folds, which is the part that keeps it honest:

  pembrolizumab ~ 0.62 and 8TBB Fab ~ 0.62   -> the metric cannot discriminate on
                                                TIM-3 at all; our 0.62 means nothing.
  pembrolizumab << our design <= 8TBB Fab    -> our design really is TIM-3-reactive
                                                relative to a specific antibody.
  pembrolizumab ~ our design << 8TBB Fab     -> 0.62 is the predictor's floor for a
                                                non-binder against this antigen; our
                                                design is NOT implicated.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from locksmith.fold import FoldFailed
from locksmith.fold import boltz as drv
from locksmith.io.pdb import seq_for_folding

OUT = Path("runs/specificity_ref")
INDEX = OUT / "index.jsonl"
TIM3_MSA = Path("data/msa_cache/v2/8tbb_antigen.csv")
MANIFEST = Path("data/refs/postcutoff/prepared/manifest_seqres.json")
PARENT = Path("data/refs/prepared/5ggs_ABZ.pdb")
SEEDS = (51, 52, 53)


def done() -> set[str]:
    if not INDEX.exists():
        return set()
    return {json.loads(l)["label"] for l in INDEX.read_text().splitlines()
            if l.strip() and json.loads(l).get("ok")}


def main() -> int:
    man = json.loads(MANIFEST.read_text())["8TBB"]
    tim3 = man["antigen"]
    panel = [
        ("pembro", "pembrolizumab (negative reference: licensed, specific)",
         seq_for_folding(PARENT, "A"), seq_for_folding(PARENT, "B")),
        ("8tbbfab", "8TBB Fab (positive reference: a real TIM-3 binder)",
         man["heavy_full"], man["light_full"]),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    have = done()
    print(f"TIM-3 antigen {len(tim3)} aa; {len(panel)} reference antibodies "
          f"x {len(SEEDS)} seeds", flush=True)
    for k, d, h, l in panel:
        print(f"  {k:8s} H={len(h)} L={len(l)}  {d}", flush=True)

    t0, ok, bad = time.time(), 0, 0
    for key, desc, heavy, light in panel:
        for seed in SEEDS:
            label = f"ref_{key}_tim3__s{seed}"
            if label in have:
                print(f"skip {label}", flush=True); continue
            try:
                r = drv.fold(label, heavy, light, tim3, out_root=OUT,
                             construct="fab", seed=seed, antigen_msa=TIM3_MSA)
            except FoldFailed as e:
                bad += 1
                print(f"FAILED {label}: {e}", file=sys.stderr, flush=True)
                rec = {"label": label, "antibody": key, "desc": desc, "seed": seed,
                       "ok": False, "error": str(e)[:400]}
            else:
                ok += 1
                print(f"  [{ok}] {label}: {r.seconds:.0f}s", flush=True)
                rec = {"label": label, "antibody": key, "desc": desc, "seed": seed,
                       "ok": True, "pdb": str(r.pdb), "pae": str(r.pae),
                       "plddt": str(r.plddt), "seconds": r.seconds}
            with INDEX.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"\nreferences: {ok} folded, {bad} failed, {(time.time()-t0)/60:.0f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
