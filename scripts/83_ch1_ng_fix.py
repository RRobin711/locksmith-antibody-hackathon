#!/usr/bin/env python3
"""Remove Challenge 1's CDR-H2 deamidation motif, and measure what it costs.

THE INCONSISTENCY THIS CLOSES. We spent 4.8 composite points removing Challenge 2's
§9.2 violation (two glycosylation sequons) and left Challenge 1's in place: an `NG`
deamidation motif at heavy 55-56, inside CDR-H2. §9.2 asks for neither. Fixing one and
not the other is not a position.

CONTACTS FIRST, as on Challenge 2 -- measured on the submitted complex, 4.5 A heavy-atom:

    H L54   5 contacts       H N55   3 contacts
    H G56   0 contacts       H G57  14 contacts

So `G56A` mutates a non-contacting residue and `N55Q` mutates one making 3 contacts --
far milder than Challenge 2, where the acceptors carried 10 and 19 and `N->Q` produced a
dead interface.

BUT THE GLYCINE IS NOT OBVIOUSLY THE SAFE CHOICE HERE, and that is why both arms run.
Glycine has no C-beta and accesses backbone dihedrals no other residue can. `G56A` adds a
side chain to a position that may be doing conformational work in a CDR loop, which is
precisely the mechanism we invoked (untested) to explain why Challenge 2's zero-contact
`S->A` still cost 0.1 ipSAE. Contact count predicted the Challenge 2 outcome; it may not
predict this one.

Folded at Challenge 1's exact submitted settings (Fab, recycling 3, seed 71, live MSA)
with `diffusion_samples=5`, so arms are compared on envelopes rather than on an argmax.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import (dockq, ipsae, liabilities, netsolp, novelty, plddt,
                               prodigy, sasa)
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

BOLTZ = str(Path.home() / ".local/bin/boltz")
OUT = Path("runs/ch1_ng_fix")
N_SAMPLES, RECYCLING, SEED = 5, 3, 71
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")

ARMS = {
    "ng_g56a": [("heavy", 56, "G", "A")],   # zero antigen contacts, but Gly is special
    "ng_n55q": [("heavy", 55, "N", "Q")],   # 3 contacts; removes the deamidation acceptor
}


def mutate(heavy, light, muts):
    seqs = {"heavy": list(heavy), "light": list(light)}
    for chain, pos, frm, to in muts:
        got = seqs[chain][pos - 1]
        if got != frm:
            raise ValueError(f"{chain} {pos}: expected {frm}, found {got}")
        seqs[chain][pos - 1] = to
    return "".join(seqs["heavy"]), "".join(seqs["light"])


def fold(label, heavy, light, antigen):
    out_dir = OUT / label
    pred = out_dir / f"boltz_results_{label}" / "predictions" / label
    if pred.exists() and list(pred.glob(f"{label}_model_*.pdb")):
        return sorted(pred.glob(f"{label}_model_*.pdb"))
    from locksmith.fold.boltz import write_input
    fasta = write_input(out_dir / f"{label}.fasta", heavy, light, antigen,
                        antigen_msa=None)
    subprocess.run([BOLTZ, "predict", str(fasta), "--out_dir", str(out_dir),
                    "--output_format", "pdb", "--write_full_pae",
                    "--diffusion_samples", str(N_SAMPLES),
                    "--recycling_steps", str(RECYCLING), "--seed", str(SEED),
                    "--accelerator", "gpu", "--num_workers", "0",
                    "--no_kernels", "--max_msa_seqs", "1024", "--use_msa_server"],
                   timeout=7200, check=False)
    models = sorted(pred.glob(f"{label}_model_*.pdb"))
    if not models:
        raise RuntimeError(f"{label}: no models")
    return models


def score_model(pdb, heavy, light, cfg):
    c = cfg.conventions
    tag = pdb.stem
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION,
                   pae=pdb.parent / f"pae_{tag}.npz", label=tag)
    r = {k: v.value for k, v in prodigy.compute(st).items()}
    r["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                               dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    r["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    r["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    r["dockq"] = dockq.compute(st, NATIVE)["dockq"].value
    r["netsolp"] = netsolp.compute(heavy, light,
                                   construct=c.get("netsolp_construct", "fv"))["netsolp"].value
    r["cdrh3_identity"] = novelty.compute(heavy, challenge=1).value
    r["model"] = int(tag.rsplit("_", 1)[1])
    return r


def main() -> int:
    cfg = load()
    OUT.mkdir(parents=True, exist_ok=True)
    hbc = json.loads(Path("data/refs/handbook_constructs.json").read_text())
    base_h, base_l, ag = hbc["heavy"], hbc["light"], hbc["antigen"]

    METRICS = ["ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa", "netsolp"]
    results = {}
    for arm, muts in ARMS.items():
        h, l = mutate(base_h, base_l, muts)
        rep = liabilities.compute(h, l)
        ok, fails = rep.handbook_9_2_pass()
        print(f"\n=== {arm}: {', '.join(f'{c[0].upper()}{f}{p}{t}' for c,p,f,t in muts)} ===",
              flush=True)
        print(f"  §9.2 {'PASS' if ok else 'FAIL: ' + '; '.join(fails)}", flush=True)
        rows = []
        for m in fold(arm, h, l, ag):
            try:
                rows.append(score_model(m, h, l, cfg))
            except Exception as e:                       # noqa: BLE001
                print(f"  {m.name}: SCORING FAILED {e}", file=sys.stderr, flush=True)
        rows.sort(key=lambda r: r["model"])
        print(f"  {'model':<7}" + "".join(f"{m:>12}" for m in METRICS) +
              f"{'viable':>8}{'final':>7}", flush=True)
        for r in rows:
            sc = evaluate({k: r[k] for k in METRICS} |
                          {"cdrh3_identity": r["cdrh3_identity"]}, challenge=1, cfg=cfg)
            r["viable"], r["final"], r["failing"] = sc.viable, sc.final, sc.failing
            print(f"  {r['model']:<7}" + "".join(f"{r[m]:>12.3f}" for m in METRICS) +
                  f"{str(sc.viable):>8}{str(sc.final):>7}"
                  + (f"  fails {sc.failing}" if sc.failing else ""), flush=True)
        results[arm] = {"rows": rows, "heavy": h, "light": l,
                        "ng_left": sum(1 for x in rep.liabilities
                                       if x.motif in ("NG", "DG") and x.region != "framework"),
                        "lo": min(r["ipsae"] for r in rows),
                        "hi": max(r["ipsae"] for r in rows),
                        "dq_lo": min(r["dockq"] for r in rows),
                        "dq_hi": max(r["dockq"] for r in rows),
                        "finals": sorted({r["final"] for r in rows}),
                        "all_viable": all(r["viable"] for r in rows)}
        print(f"  ipSAE {results[arm]['lo']:.3f}-{results[arm]['hi']:.3f}  "
              f"DockQ {results[arm]['dq_lo']:.3f}-{results[arm]['dq_hi']:.3f}  "
              f"finals {results[arm]['finals']}  viable 5/5: "
              f"{results[arm]['all_viable']}", flush=True)

    (OUT / "results.json").write_text(json.dumps(results, indent=1))
    print("\n" + "=" * 76)
    print("baseline (submitted, unfixed): ipSAE 0.822-0.861, DockQ 0.711-0.820, "
          "final 94.0-96.0, CDR-H2 NG present")
    best = [a for a, r in results.items() if r["all_viable"] and r["ng_left"] == 0]
    if best:
        pick = max(best, key=lambda a: min(results[a]["finals"]))
        print(f"VERDICT: {pick} clears §9.2 and stays viable 5/5 "
              f"(finals {results[pick]['finals']}). Candidate for submission.")
        for a in best:
            if a != pick:
                print(f"         {a} also works (finals {results[a]['finals']}).")
    else:
        print("VERDICT: NEITHER FIX SURVIVES. Keep the original and report that the "
              "deamidation motif is not removable without losing the design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
