#!/usr/bin/env python3
"""Package Challenge 2 to §4.3 — but ONLY if a design clears every §7.2 cutoff.

THE GUARD IS THE POINT. This script refuses to build a folder unless at least one
design is viable on all seven metrics. Packaging a non-viable design in the handbook's
tree would make it *look* like a submission, and §7.2 ranks a non-viable design below
every viable one, so the folder would be worse than no folder. `scripts/57` already
states that reasoning for the absent Challenge 2 folder; this enforces it.

SELECTION IS PRE-REGISTERED AND IS NOT THE COMPOSITE. From
`results/prereg_2026-09-21_challenge2.md`, fixed before any score existed:

    hotspot contact count, tie-broken on frac_iface_on_epitope

That rule was chosen because `interaction_pae` cannot rank docks (ICC -0.113 against a
0.317 detectable floor) and because the project has repeatedly shown its metric stack
cannot order intact designs. It must NOT be revisited now that scores are in view --
re-deriving a selection rule after seeing the outcomes is the definition of the thing
this project keeps catching in others' work.

The conditioning numbers come from the RETRIEVED pod artefacts, every byte of which is
sha256-verified against the server (`runs/challenge2_pod/CHECKSUM_SUMMARY.json`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.submit import Design, build_challenge, build_zip

TEAM = "LOCKSMITH_DEV"
CHALLENGE = 2
ROOT = Path("submission")
# THE RECYCLING-10 RUN, not the original. The first pass folded at recycling_steps=3
# and returned 0/30; re-folding the whole pool at recycling 10 returns 1/30. Pointing
# this at the old directory would package a structure whose ipSAE is 0.263 while the
# metrics table said 0.864 -- the artefact and the number coming from different files.
FOLD = Path("runs/challenge2_fold_r10")
SCORES = FOLD / "scores.jsonl"
POD = Path("runs/challenge2_pod/c2")


def conditioning_by_backbone() -> dict[str, dict]:
    """bb_N_0 -> the pilot's conditioning record for that backbone."""
    out = {}
    for line in (POD / "cond_all.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["file"].replace(".pdb", "")] = r
    return out


def main() -> int:
    cfg = load()
    rows = [json.loads(l) for l in SCORES.read_text().splitlines()
            if l.strip() and "ipsae" in json.loads(l)]
    viable = [r for r in rows if r.get("viable") is True]

    print(f"{len(rows)} scored, {len(viable)} clear every §7.2 cutoff")
    if not viable:
        print("\nNO DESIGN CLEARS EVERY HARD CUTOFF.\n"
              "Refusing to package. §7.2 ranks a non-viable design below every viable "
              "one, so a folder here would be worse than no folder. This is a legitimate "
              "end state, not a failure of this script.", file=sys.stderr)
        return 2

    # ---- pre-registered selection ----
    cond = conditioning_by_backbone()
    ranked = []
    for r in viable:
        bb = r["design_id"].split("_dldesign_")[0]
        c = cond.get(bb)
        if c is None:
            print(f"  WARNING: no conditioning record for {bb}; cannot apply the "
                  f"pre-registered rule to {r['design_id']}", file=sys.stderr)
            continue
        ranked.append({**r, "backbone": bb,
                       "hotspots_contacted": c["hotspots_contacted"],
                       "frac_iface_on_epitope": c["frac_iface_on_epitope"]})
    if not ranked:
        print("viable designs exist but none has a conditioning record; the "
              "pre-registered rule cannot be applied", file=sys.stderr)
        return 3

    ranked.sort(key=lambda r: (-r["hotspots_contacted"], -r["frac_iface_on_epitope"]))
    win = ranked[0]
    print(f"\nPRE-REGISTERED SELECTION (hotspot contacts, then frac_iface_on_epitope):")
    for i, r in enumerate(ranked[:5], 1):
        print(f"  {i}. {r['design_id']:28s} hotspots={r['hotspots_contacted']:2d} "
              f"frac={r['frac_iface_on_epitope']:.3f} final={r['final']}")
    print(f"\nselected: {win['design_id']}")

    higher = [r for r in ranked if (r["final"] or 0) > (win["final"] or 0)]

    designs = {d["design_id"]: d for d in json.loads((FOLD / "designs.json").read_text())}
    folds = {json.loads(l)["design_id"]: json.loads(l)
             for l in (FOLD / "index.jsonl").read_text().splitlines()
             if l.strip() and json.loads(l).get("ok")}
    d = designs[win["design_id"]]
    f = folds[win["design_id"]]
    pdb = Path(f["pdb"])
    conf = pdb.parent / f"confidence_{pdb.stem.replace('_model_0','')}_model_0.json"

    metrics_md = [
        "# Our own recomputation of the seven scored metrics",
        "",
        f"Design `{win['design_id']}`, folded with Boltz-2 on the handbook's §4.2.2 "
        f"antigen.",
        f"Conventions: `band_value={cfg.band_value}`, "
        f"`netsolp_construct={cfg.conventions.get('netsolp_construct')}`, "
        f"`netsolp_chain_agg={cfg.conventions['netsolp_chain_agg']}`.",
        "",
        "**Seven, not eight — DockQ is excluded.** §5.2 applies DockQ to Challenge 1 "
        "only, because a de novo design has no reference structure. Note what that "
        "removes: DockQ was the only metric that compares the prediction to anything "
        "external. Every metric below is computed from the two files in `structures/`, "
        "which we generated. **A confidently wrong pose scores exactly like a right one.**",
        "",
        "| metric | value | band | sub-score |", "|---|---|---|---|",
    ]
    for m in sorted(k for k in win if k in cfg.bands() and CHALLENGE in cfg.bands()[k].challenges):
        metrics_md.append(f"| `{m}` | {win[m]:.3f} | {win['bands'].get(m,'-')} | "
                          f"{cfg.band_scores[win['bands'][m]]:.1f} |")
    metrics_md += ["", f"**Final: {win['final']} / 100. Viable: {win['viable']}.**"]

    docs_md = f"""# Methods and limitations — {TEAM}, Challenge 2

## What this design is, and what we can support

A complete VH/VL antibody designed **de novo** against PD-1 with RFdiffusion (via
RFantibody), sequence-designed with ProteinMPNN, and folded as a complex with Boltz-2.
It clears all seven §7.2 cutoffs and scores {win['final']}/100 as folded and submitted.

**THAT SCORE IS NOT STABLE, and the instability is the most important thing in this
document.** The submitted structure was folded at Boltz `recycling_steps=10`. Re-folding
the identical input at other sampling depths moves the headline metric across a band edge:

| Boltz recycling | ipSAE (seeds) | ipSAE band | composite |
|---|---|---|---|
| 3 | 0.263 / 0.354 / 0.474 | poor | **non-viable** |
| 10 (submitted) | 0.864 / 0.842 / 0.856 | good | **96.0** |
| 20 | 0.795 / 0.883 / 0.731 | medium / good / medium | **93.6 / 96.0 / 93.6** |

Convergence is **non-monotone**, and 96.0 reproduces in one of three recycling-20 seeds.
For contrast, measured on the same machine: a real crystallised complex (pembrolizumab +
PD-1, PDB 5GGS) moves 0.842 → 0.835 → 0.885 across the same depths — a range of 0.050 —
and our Challenge 1 design moves 0.824 → 0.850 → 0.859, a range of 0.036. **This de novo
design swings 0.601, twelve to seventeen times more.** A near-native complex is
essentially invariant in sampling depth; this one is not converged at any depth we tested.

**A second axis, measured the same day and cheaper still.** Boltz's `--diffusion_samples`
defaults to 1, so this and every other pose-derived number here came from a single
diffusion draw. Asking for five (2m54s against ~2m — the MSA, trunk and recycling are
shared, only the diffusion head reruns):

| diffusion sample | 0 (submitted) | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| ipSAE | **0.864** | 0.773 | 0.757 | 0.859 | 0.736 |
| composite | **96.0** | 93.6 | 91.2 | 96.0 | 91.2 |

**Three of five fall to the Medium band.** No sample goes near the 0.60 viability cutoff —
the lowest is 0.736 — so the design is viable under every draw we took. What moves is the
score.

**And the submitted model is the best of the five.** Boltz orders its output by its own
confidence, so `model_0` is the argmax *by construction*. With one diffusion sample you do
not get a draw from the distribution, you get the model's best guess reported as if it
were the estimate. That is true of every pose-derived number in this submission and, we
suspect, of most submissions scored this way.

Read the headline as **91.2–96.0 across diffusion samples and 93.6–96.0 across recycling
depth**, on a design that is viable throughout. The variance is the real result about de
novo design; the score is a point on it.

**We can support exactly one claim about this molecule, and it is not binding.**

### Supported: the design is aimed at the right epitope

RFdiffusion was conditioned on the 26-residue PD-L1 competitive footprint of PD-1. For
each backbone we recomputed the fraction of the designed interface lying on that
footprint, against **2000 random contiguous surface patches of the same size on the same
chain**. Across the 18 conditioned backbones: mean **0.712**, patch null **0.154**, and
**17 of 18 beat their own null at p<0.05**. Deterministic per backbone, so there is no
stopping rule to violate, and a control that could have failed.

**THIS DESIGN SPECIFICALLY — because a pool mean is not a property of one member.**
Its own backbone scores **0.625**, *below* the pool median of 0.684, on 5 of 26 hotspots.
And the number above is measured on the RFdiffusion backbone, not on the Boltz re-dock
that is actually in `structures/`: recomputed on the submitted complex, **0.581 of the
interface lies on the conditioned epitope, contacting 18 of the 26 epitope residues**.
Still far above the 0.154 null, and the honest number to quote for this molecule.

*Limitation, stated because we measured it:* the null patches are more compact than the
real epitope (RMS spread 7.73 Å vs 10.08 Å), so the null is the right family but is not
shape-matched. That plausibly makes the test anti-conservative by an unquantified amount.

### NOT supported: that this is the best of 30

`interaction_pae` — the only per-design ranking signal the pipeline produced — has
**ICC −0.113 against a detectable floor of 0.317** at n=10 backbones × 3 designs. We
cannot rank these designs. A rule was **pre-registered before any score existed** —
highest hotspot contact count, ties broken
on `frac_iface_on_epitope`, applied only to gate-clearing designs.

**The rule was then inapplicable, and we will not pretend otherwise.** Exactly one design
cleared the gates, so the rule sorted a list of length one and made no choice at all.
Worse for us: applied to the pool as a *ranking*, this design's backbone scores 5 hotspot
contacts against a pool mean of 6.33 — **12 of 18 backbones score higher**, and the rule
would have chosen a different one. The accurate statement is not "chosen by a fixed rule"
but: **this is the only design that cleared, and under our own pre-registered key it
would have ranked near the bottom.**

{"**Designs with a HIGHER final score that we did not select: "
 + ", ".join(f"`{r['design_id']}` ({r['final']})" for r in higher[:5])
 + ". Selecting on the composite after seeing the scores would be exactly the "
   "post-hoc rule-fitting this project spends its evidence criticising.**"
 if higher else
 "No viable design scored higher on the composite than the one the pre-registered rule "
 "selected, so nothing was given up by following it."}

### NOT supported: agreement between predictors

RF2 re-predicted these designs and sits a mean **24.87 Å** from the designed dock
(median 28.94 Å). We tested the charitable reading — that this reflects an *unfiltered*
pool failing a standard filter rather than RF2 being unreliable — and it does not hold:
exactly **1 of 30** designs passes the conventional `interaction_pae < 10` filter, and
**that design sits at 32.86 Å**, worse than the median. Model agreement is not evidence
here, and we do not offer it as any.

### NOT supported: binding

Nothing in this submission is evidence that this antibody binds PD-1. On 45 point
mutants with measured ΔΔG (SKEMPI 2.0, 3HFM), **no metric in this stack tracks affinity**
— a mutation that abolishes binding scored ipSAE 0.917 against the wild type's 0.903.
The seven metrics above separate a destroyed interface from an intact one. They do not
rank intact interfaces, and they do not measure binding.

## What is designed, and what is not — scaffold disclosure

**The framework is not ours and is not designed.** This design was produced with
RFantibody, whose stock antibody scaffold is the humanised **4D5-8 (trastuzumab) Fv**.
All six CDRs of BOTH chains were designed de novo onto it; the frameworks were carried
over unchanged. Measured against trastuzumab: **VH framework 86/86 identical, VL
framework 80/80 identical**.

Using a fixed humanised framework is standard practice and is what "de novo antibody
design" operationally means with current tooling — the novelty lives in the CDRs and the
pose. But "designed de novo" without this sentence would let a reader assume more was
designed than was, so the sentence belongs here. It also explains why the humanness and
framework metrics look excellent: they are a marketed antibody's.

## Developability liabilities we found in our own design

**Two N-linked glycosylation sequons are present in the CDRs, and both sit on
antigen-contacting residues.** Handbook §9.2 lists "No N-glycosylation sequons (N-X-S/T)
in Fv region" as an explicit checklist item, and this design fails it:

| chain | motif | position | contacts to PD-1 |
|---|---|---|---|
| VH, CDR-H2 | **N-V-S** | N52 | 10 heavy-atom contacts |
| VL, CDR-L2 | **N-A-S** | N49 | 19 heavy-atom contacts |

Neither exists in the parent 4D5-8 scaffold (`RIYPTNGYT`, `SASFLYS`) — **ProteinMPNN
introduced both**. In a CHO expression system these sites would plausibly be occupied, and
a glycan at either would sit in the middle of the paratope. §9 gives the fix (N→Q or
S→A); we have not applied it, because changing the sequence after scoring it is precisely
what the rest of this document argues against.

**Why we did not catch this ourselves, and what we did about it.** Our own build plan
(`BUILD.md:62`) specifies a `liabilities.py` scanner for exactly this — N-X-S/T, NG/DG
motifs, exposed Met, pI, net charge. It was never written. A planned check that does not
exist is indistinguishable from a check that passed, which is the failure mode this
project spent a week cataloguing and then committed.

**It exists now** (`src/locksmith/metrics/liabilities.py`), it reproduces both sequons at
the exact positions above, and it is pinned by regression tests against this specific
defect — including that `N-P-S/T` is *not* a sequon, the commonest way such a scan cries
wolf. Running it also found a liability in our **Challenge 1** design that no reviewer had
flagged as a §9.2 failure (an `NG` deamidation motif in CDR-H2), which is the argument for
mechanisms over prose in one line.

Also present, lower severity: CDR-H3 `SRSFAGSHLL` is short (8 residues by Kabat) and its
exposed surface is ~88% hydrophobic, a recognised aggregation and polyreactivity risk.

## Novelty

CDR-H3 identity is measured **against human germline** per §6.3.1, not against Keytruda.
CDR-H3 spans the V(D)J junction and the N-region insertions have no germline counterpart
at all, so there is no single string to compare to: the metric is a best-match search
over IGHV/IGHD/IGHJ segments (V as an exact prefix, J as an exact suffix, D as a
substring in any of 3 reading frames). Validated on four derivable cases — a verbatim
germline junction scores 100.0%, and 242 of 249 IGHV alleles return themselves.

**Worth knowing: this gate is free.** Pembrolizumab's own CDR-H3 scores 53.8% to germline
against a <95% cutoff, so no de novo design can plausibly fail it.

## Provenance

Backbones and sequences were generated on a rented RTX 3090 and retrieved to local disk;
**every one of the 258 artefact files is sha256-verified against the server** — see
`results/checksum_pass_2026-09-22.md`. The structure and PAE here were folded locally.
"""

    dsn = Design(name="design_1", heavy=d["heavy"], light=d["light"],
                 antigen=d["antigen"], pdb=pdb, pae_npz=Path(f["pae"]),
                 plddt_npz=Path(f["plddt"]),
                 confidence_json=conf if conf.exists() else None)
    base = build_challenge(ROOT, TEAM, CHALLENGE, dsn,
                           metrics_md="\n".join(metrics_md), docs_md=docs_md)
    print(f"built {base}")
    z = build_zip(ROOT, TEAM)
    print(f"built {z} ({z.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
