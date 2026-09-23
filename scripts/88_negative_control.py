#!/usr/bin/env python3
"""The control that could have sunk this project: does an IRRELEVANT antibody score well?

--------------------------------------------------------------------------------------
THE ARGUMENT
--------------------------------------------------------------------------------------
Every gate in the handbook (§7.2) is a threshold on a number Boltz produces for an
antibody-antigen pair. We have shown our designs clear those thresholds. We have never
shown that a *wrong* antibody fails them.

If a real antibody with a completely unrelated target -- an anti-lysozyme, an anti-HER2 --
is docked onto PD-1 and still scores ipSAE >= 0.60, then the gate does not measure binding.
It measures "two proteins were placed next to each other", and every number in this
submission is worthless. That is a one-line falsification of the entire rubric, and it
costs eight folds.

This is the single cheapest experiment with the largest possible consequence, and nobody
on this project ran it for a week.

--------------------------------------------------------------------------------------
WHY THIS IS A TIGHTER CONTROL THAN THE CALIBRATION PANEL
--------------------------------------------------------------------------------------
In the calibration panel (scripts/86-87) every complex has a different antigen, so the
antigen MSA differs between rows and is a nuisance variable. Here the antigen is **the
identical PD-1 sequence our designs were folded against, with the identical cached
alignment** (`data/msa_cache/pd1_5ggs.csv`, 3787 sequences). Construct, flags, recycling
depth and diffusion samples are all unchanged. The *only* thing that varies across rows
is which antibody is on the other side. Any difference in score is therefore attributable
to the antibody and to nothing else.

--------------------------------------------------------------------------------------
THE ARMS
--------------------------------------------------------------------------------------
**Negative (should FAIL):** six real, crystallised, clinically or historically famous
antibodies whose targets are not PD-1 and share no fold with it.

**Positive (should PASS):** pembrolizumab and nivolumab -- two independent, licensed
anti-PD-1 antibodies. If these fail, the pipeline is broken and the negatives prove
nothing. A control panel needs both ends or a uniform result is uninterpretable: this
project has already published a "0/30 viable" that was the sampler's floor, not a finding.

**Note the direction of the memorisation bias, because it makes the negatives STRONGER.**
Every antibody here is pre-cutoff, so Boltz has seen all of them -- but it has seen them
bound to *their own* antigens. If memorisation leaked into scoring we would expect it to
help a familiar antibody look confident wherever it is put. A memorised antibody that
still fails on the wrong antigen is a harder negative than an unfamiliar one would be.

**Also note what a negative control canNOT do.** Passing this tells us the metric
discriminates cognate from non-cognate pairs. It does not tell us the metric ranks
correctly *among* plausible designs -- this project measured exactly that failure
(ipSAE wandered within +/-0.04 while DockQ fell 0.820 -> 0.601). Discrimination and
ranking are different properties and this experiment only tests the first.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import gemmi

from locksmith.fold import FoldFailed, fold_is_complete
from locksmith.fold.boltz import fold, PD1_MSA
from locksmith.numbering import number

OUT = Path("runs/negctrl")
PDBDIR = Path("runs/calibration/pdb")
LOG = OUT / "fold_log.json"
RECYCLING = 10
SAMPLES = 5

# The exact PD-1 construct every design in this project was folded against.
PD1 = ("PWNPPTFSPALLVVTEGDNATFTCSFSNTSESFVLNWYRMSPSNQTDKLAAFPEDRSQPGQDSRFRVTQLPNGRDF"
       "HMSVVRARRNDSGTYLCGAISLAPKAQIKESLRAELR")

ARMS = [
    # (pdb, name, target, expected)
    ("3HFM", "HyHEL-10",      "hen egg lysozyme",            "negative"),
    ("1N8Z", "trastuzumab",   "HER2 extracellular domain",   "negative"),
    ("1BJ1", "bevacizumab",   "VEGF-A",                      "negative"),
    ("1YY9", "cetuximab",     "EGFR domain III",             "negative"),
    ("4FQI", "CR9114",        "influenza haemagglutinin",    "negative"),
    ("1IQD", "BO2C11",        "coagulation factor VIII C2",  "negative"),
    ("5GGS", "pembrolizumab", "PD-1",                        "positive"),
    ("5WT9", "nivolumab",     "PD-1",                        "positive"),
]


def fetch(pdb_id: str) -> Path:
    PDBDIR.mkdir(parents=True, exist_ok=True)
    p = PDBDIR / f"{pdb_id.lower()}.pdb"
    if not (p.exists() and p.stat().st_size > 2000):
        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
        with urllib.request.urlopen(url, timeout=90) as r:
            p.write_bytes(r.read())
    return p


def fv_pair(pdb: Path) -> tuple[str, str]:
    """Heavy and light VARIABLE DOMAINS, typed by ANARCII rather than by chain letter.

    Trimming to Fv is what makes these comparable to our designs, and it also sidesteps
    the constant-domain disorder that makes many of these coordinate sequences unfoldable
    as written -- the Fv is almost always fully resolved because it is the part the
    crystallographer cared about.
    """
    st = gemmi.read_structure(str(pdb))
    st.setup_entities()
    heavy = light = None
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
        if n.chain_type == "H" and heavy is None:
            heavy = n.fv
        elif n.chain_type in ("K", "L") and light is None:
            light = n.fv
    if not (heavy and light):
        raise RuntimeError(f"{pdb.name}: could not extract an Fv pair")
    return heavy, light


def already_done(label: str) -> bool:
    return fold_is_complete(
        OUT / label / f"boltz_results_{label}" / "predictions" / label,
        label, n_models=SAMPLES)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    meta_path = OUT / "arms.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    for pid, name, target, expected in ARMS:
        label = f"neg_{name.lower()}"
        heavy, light = fv_pair(fetch(pid))
        meta[label] = {"pdb": pid, "name": name, "target": target,
                       "expected": expected, "heavy": heavy, "light": light,
                       "n_res": len(heavy) + len(light) + len(PD1)}
        meta_path.write_text(json.dumps(meta, indent=1))
        if already_done(label):
            print(f"{label:<22} already folded", flush=True)
            continue
        print(f"{label:<22} {expected:<8} H{len(heavy)} L{len(light)} vs PD-1 ...",
              end=" ", flush=True)
        t0 = time.time()
        try:
            fold(label, heavy, light, PD1, out_root=OUT, antigen_msa=PD1_MSA, seed=1,
                 diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
            log[label] = {"ok": True, "seconds": round(time.time() - t0, 1)}
            print(f"ok in {(time.time()-t0)/60:.1f} min", flush=True)
        except Exception as e:                               # noqa: BLE001
            log[label] = {"ok": False, "error": str(e)[:300]}
            print(f"FAILED: {str(e)[:160]}", flush=True)
        LOG.write_text(json.dumps(log, indent=1))
    print(f"\n{sum(1 for v in log.values() if v.get('ok'))}/{len(ARMS)} folded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
