#!/usr/bin/env python3
"""Score every folded Challenge 2 design on the seven metrics §7.2 applies, and report
how many clear EVERY hard cutoff.

SEVEN, NOT EIGHT. `config/metrics.yaml` gives DockQ `challenges: [1]`, matching §5.2 --
Challenge 2 is de novo, so there is no reference structure to compare a pose against.
That is read from config here rather than hardcoded, so the two places cannot drift.

Note what that removes: DockQ is the only metric in the rubric that compares the
prediction to something EXTERNAL. Every remaining metric is computed from the files we
generate ourselves, so a confidently wrong pose scores exactly like a right one. The
pass rate below is therefore a statement about self-consistency, not about binding.

Resumes on the artefact (`'ipsae' in row`), never on the row existing: a row recording
an error is not completed work, and keying resume on row-existence once let this project
treat 239 error rows as finished.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

FOLD = Path("runs/challenge2_fold")
DESIGNS = FOLD / "designs.json"
INDEX = FOLD / "index.jsonl"
SCORES = FOLD / "scores.jsonl"
CHALLENGE = 2


def main() -> int:
    cfg = load()
    c = cfg.conventions
    scored_metrics = sorted(n for n, b in cfg.bands().items()
                            if CHALLENGE in b.challenges)
    print(f"Challenge {CHALLENGE} scores {len(scored_metrics)} metrics: "
          f"{scored_metrics}", flush=True)

    designs = {d["design_id"]: d for d in json.loads(DESIGNS.read_text())}
    folds = [json.loads(l) for l in INDEX.read_text().splitlines()
             if l.strip() and json.loads(l).get("ok")]
    print(f"{len(folds)} successful folds of {len(designs)} designs", flush=True)

    done = set()
    if SCORES.exists():
        done = {json.loads(l)["design_id"] for l in SCORES.read_text().splitlines()
                if l.strip() and "ipsae" in json.loads(l)}

    for i, f in enumerate(folds, 1):
        did = f["design_id"]
        if did in done:
            continue
        d = designs[did]
        pdb, pae = Path(f["pdb"]), Path(f["pae"])
        st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae, label=did)
        rec: dict = {"design_id": did}
        try:
            rec.update({k: v.value for k, v in prodigy.compute(st).items()})
            rec["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                         dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
            rec["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
            rec["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
            rec["netsolp"] = netsolp.compute(
                d["heavy"], d["light"],
                construct=c.get("netsolp_construct", "fv"))["netsolp"].value
            rec["cdrh3_identity"] = novelty.compute(
                d["heavy"], challenge=CHALLENGE).value
        except Exception as e:                     # noqa: BLE001 - record and continue
            rec["error"] = f"{type(e).__name__}: {e}"[:400]
            print(f"[{i}/{len(folds)}] ERROR {did}: {rec['error']}",
                  file=sys.stderr, flush=True)
        else:
            sc = evaluate(rec, challenge=CHALLENGE, cfg=cfg)
            rec["final"] = sc.final
            rec["viable"] = sc.viable
            rec["failing"] = sc.failing
            rec["bands"] = sc.bands
            print(f"[{i}/{len(folds)}] {did}: viable={sc.viable} final={sc.final} "
                  f"failing={sc.failing}", flush=True)
        with SCORES.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")

    # ---- report ----
    rows = [json.loads(l) for l in SCORES.read_text().splitlines()
            if l.strip() and "ipsae" in json.loads(l)]
    viable = [r for r in rows if r.get("viable") is True]
    print(f"\n{'='*66}")
    print(f"scored {len(rows)} designs; CLEAR EVERY §7.2 CUTOFF: {len(viable)}")
    print(f"{'='*66}")

    bands = cfg.bands()
    fails: dict[str, list[float]] = {}
    for r in rows:
        for m in r.get("failing", []):
            fails.setdefault(m, []).append(r[m])
    for m, vals in sorted(fails.items(), key=lambda kv: -len(kv[1])):
        b = bands[m]
        worst = max(vals) if b.direction == "low" else min(vals)
        best = min(vals) if b.direction == "low" else max(vals)
        sign = "<=" if b.direction == "low" else ">="
        print(f"  {m:16s} failed on {len(vals):2d}/{len(rows)}  cutoff {sign} {b.cutoff}"
              f"   range {min(vals):.3f}..{max(vals):.3f}"
              f"   closest {best:.3f}  worst {worst:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
