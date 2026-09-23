#!/usr/bin/env python3
"""Remove the two paratope N-glycosylation sequons and measure what it costs.

Pre-registered in `results/prereg_2026-09-22_sequon_fix.md`.

Two arms, both prescribed by handbook §9 Pillar 4:
    SA   H S54A + L S51A   -- the serines make ZERO antigen contacts
    NQ   H N52Q + L N49Q   -- the asparagines make 10 and 19

Folded at the submitted settings with `diffusion_samples=5`, because `model_0` is an
argmax by construction: these are compared on envelopes, not points.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import ipsae, liabilities, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

BOLTZ = str(Path.home() / ".local/bin/boltz")
OUT = Path("runs/sequon_fix")
PD1_MSA = Path("data/msa_cache/pd1_5ggs.csv")
N_SAMPLES, RECYCLING, SEED = 5, 10, 1

ARMS = {
    "sq_sa": [("heavy", 54, "S", "A"), ("light", 51, "S", "A")],
    "sq_nq": [("heavy", 52, "N", "Q"), ("light", 49, "N", "Q")],
}


def mutate(heavy: str, light: str, muts) -> tuple[str, str]:
    seqs = {"heavy": list(heavy), "light": list(light)}
    for chain, pos, frm, to in muts:
        got = seqs[chain][pos - 1]
        if got != frm:
            raise ValueError(f"{chain} {pos}: expected {frm}, found {got} — "
                             f"the sequence is not what the mutation was designed against")
        seqs[chain][pos - 1] = to
    return "".join(seqs["heavy"]), "".join(seqs["light"])


def fold(label: str, heavy: str, light: str, antigen: str) -> list[Path]:
    out_dir = OUT / label
    pred = out_dir / f"boltz_results_{label}" / "predictions" / label
    if pred.exists() and list(pred.glob(f"{label}_model_*.pdb")):
        return sorted(pred.glob(f"{label}_model_*.pdb"))
    from locksmith.fold.boltz import write_input
    fasta = write_input(out_dir / f"{label}.fasta", heavy, light, antigen,
                        antigen_msa=PD1_MSA)
    subprocess.run([BOLTZ, "predict", str(fasta), "--out_dir", str(out_dir),
                    "--output_format", "pdb", "--write_full_pae",
                    "--diffusion_samples", str(N_SAMPLES),
                    "--recycling_steps", str(RECYCLING), "--seed", str(SEED),
                    "--accelerator", "gpu", "--num_workers", "0",
                    "--no_kernels", "--max_msa_seqs", "1024"],
                   timeout=7200, check=False)
    models = sorted(pred.glob(f"{label}_model_*.pdb"))
    if not models:
        raise RuntimeError(f"{label}: boltz produced no models")
    return models


def score_model(pdb: Path, heavy: str, light: str, cfg) -> dict:
    c = cfg.conventions
    tag = pdb.stem
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION,
                   pae=pdb.parent / f"pae_{tag}.npz", label=tag)
    r = {k: v.value for k, v in prodigy.compute(st).items()}
    r["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                               dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    r["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    r["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    r["netsolp"] = netsolp.compute(heavy, light,
                                   construct=c.get("netsolp_construct", "fv"))["netsolp"].value
    r["cdrh3_identity"] = novelty.compute(heavy, challenge=2).value
    r["model"] = int(tag.rsplit("_", 1)[1])
    return r


def main() -> int:
    cfg = load()
    OUT.mkdir(parents=True, exist_ok=True)
    designs = json.loads(Path("runs/challenge2_fold_r10/designs.json").read_text())
    win = [json.loads(l) for l in
           Path("runs/challenge2_fold_r10/scores.jsonl").read_text().splitlines()
           if l.strip() and json.loads(l).get("viable") is True][0]["design_id"]
    d = {x["design_id"]: x for x in designs}[win]
    print(f"baseline design: {win}\n", flush=True)

    results = {}
    for arm, muts in ARMS.items():
        h, l = mutate(d["heavy"], d["light"], muts)
        rep = liabilities.compute(h, l)
        ok, fails = rep.handbook_9_2_pass()
        muts_str = ", ".join(f"{c[0].upper()}{f}{p}{t}" for c, p, f, t in muts)
        print(f"=== {arm}: {muts_str} ===", flush=True)
        print(f"  sequons remaining: "
              f"{len([x for x in rep.liabilities if x.kind=='glycosylation'])}   "
              f"§9.2 {'PASS' if ok else 'FAIL: ' + '; '.join(fails)}", flush=True)

        rows = []
        for m in fold(arm, h, l, d["antigen"]):
            try:
                rows.append(score_model(m, h, l, cfg))
            except Exception as e:                       # noqa: BLE001
                print(f"  {m.name}: SCORING FAILED {e}", file=sys.stderr, flush=True)
        rows.sort(key=lambda r: r["model"])
        metrics = ["ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa", "netsolp"]
        print(f"  {'model':<7}" + "".join(f"{m:>13}" for m in metrics) +
              f"{'viable':>8}{'final':>7}", flush=True)
        for r in rows:
            sc = evaluate({k: r[k] for k in metrics} |
                          {"cdrh3_identity": r["cdrh3_identity"]}, challenge=2, cfg=cfg)
            r["viable"], r["final"], r["failing"] = sc.viable, sc.final, sc.failing
            print(f"  {r['model']:<7}" + "".join(f"{r[m]:>13.3f}" for m in metrics) +
                  f"{str(sc.viable):>8}{str(sc.final):>7}"
                  + (f"  fails {sc.failing}" if sc.failing else ""), flush=True)
        lo, hi = min(r["ipsae"] for r in rows), max(r["ipsae"] for r in rows)
        allv = all(r["viable"] for r in rows)
        print(f"  ipSAE envelope {lo:.3f}-{hi:.3f} (spread {hi-lo:.3f}); "
              f"viable on all 5: {allv}\n", flush=True)
        results[arm] = {"rows": rows, "lo": lo, "hi": hi, "all_viable": allv,
                        "sequons_left": len([x for x in rep.liabilities
                                             if x.kind == "glycosylation"]),
                        "heavy": h, "light": l, "muts": muts_str}

    (OUT / "results.json").write_text(json.dumps(
        {k: {kk: vv for kk, vv in v.items()} for k, v in results.items()}, indent=1))

    # ---- pre-registered decision rule ----
    BASE_LO, BASE_HI = 0.736, 0.864
    print("=" * 74)
    print(f"baseline (submitted, unfixed): ipSAE {BASE_LO:.3f}-{BASE_HI:.3f}, "
          f"2 sequons, §9.2 FAIL")
    sa, nq = results["sq_sa"], results["sq_nq"]
    if sa["all_viable"] and sa["sequons_left"] == 0:
        print(f"VERDICT: SUBMIT THE S->A VARIANT. Viable on all 5 samples "
              f"({sa['lo']:.3f}-{sa['hi']:.3f}), both sequons removed, zero interface "
              f"contacts touched. Strictly better than what is currently packaged.")
    elif nq["all_viable"] and nq["sequons_left"] == 0:
        print(f"VERDICT: S->A failed; SUBMIT THE N->Q VARIANT "
              f"({nq['lo']:.3f}-{nq['hi']:.3f}) and report that the fix cost contacts.")
    else:
        print("VERDICT: NEITHER FIX SURVIVES. Keep the original and report that the "
              "glycosylation acceptor and the binding residue are the same atom — the "
              "liability is not removable without losing the design.")
    for arm, r in results.items():
        if r["hi"] - r["lo"] > (BASE_HI - BASE_LO) * 1.5:
            print(f"         NOTE: {arm}'s envelope ({r['hi']-r['lo']:.3f}) is much wider "
                  f"than the baseline's ({BASE_HI-BASE_LO:.3f}) — compliance bought at "
                  f"the cost of stability.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
