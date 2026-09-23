#!/usr/bin/env python3
"""Does the diffusion draw move the submitted numbers? Pre-registered in
`results/prereg_2026-09-22_diffusion_samples.md`.

Both submissions rest on `--diffusion_samples 1`, Boltz's default, inherited and never
examined. Recycling depth -- a different axis -- moved Challenge 2's ipSAE by 0.601. This
varies the axis we never varied.

ONE run per challenge at `--diffusion_samples 5`, everything else at the submitted
settings, scoring all five emitted models. Within one invocation the MSA is fetched once
and shared, so the spread is pure diffusion variability; five separate runs would
confound it with MSA variation (Challenge 1's submitted fold used a live MMseqs2 query).

`fold()` returns only `model_0`, so this drives Boltz directly and scores every model.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

BOLTZ = str(Path.home() / ".local/bin/boltz")
OUT = Path("runs/diffusion_samples")
N_SAMPLES = 5
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")

ARMS = {
    # label            recycling seed  msa                                   challenge
    "ds_ch1": dict(recycling=3, seed=71, msa=None, challenge=1,
                   src="data/refs/handbook_constructs.json"),
    "ds_ch2": dict(recycling=10, seed=1, msa="data/msa_cache/pd1_5ggs.csv", challenge=2,
                   src="runs/challenge2_fold_r10/designs.json"),
}


def sequences(arm: str, cfg) -> tuple[str, str, str]:
    if arm == "ds_ch1":
        h = json.loads(Path(ARMS[arm]["src"]).read_text())
        return h["heavy"], h["light"], h["antigen"]
    designs = json.loads(Path(ARMS[arm]["src"]).read_text())
    win = [json.loads(l) for l in
           Path("runs/challenge2_fold_r10/scores.jsonl").read_text().splitlines()
           if l.strip() and json.loads(l).get("viable") is True][0]["design_id"]
    d = {x["design_id"]: x for x in designs}[win]
    return d["heavy"], d["light"], d["antigen"]


def run(arm: str, cfg) -> list[Path]:
    a = ARMS[arm]
    heavy, light, antigen = sequences(arm, cfg)
    out_dir = OUT / arm
    pred = out_dir / f"boltz_results_{arm}" / "predictions" / arm
    if pred.exists() and list(pred.glob(f"{arm}_model_*.pdb")):
        print(f"  {arm}: reusing existing fold", flush=True)
        return sorted(pred.glob(f"{arm}_model_*.pdb"))

    from locksmith.fold.boltz import write_input
    fasta = write_input(out_dir / f"{arm}.fasta", heavy, light, antigen,
                        antigen_msa=Path(a["msa"]) if a["msa"] else None)
    cmd = [BOLTZ, "predict", str(fasta), "--out_dir", str(out_dir),
           "--output_format", "pdb", "--write_full_pae",
           "--diffusion_samples", str(N_SAMPLES),
           "--recycling_steps", str(a["recycling"]),
           "--seed", str(a["seed"]),
           "--accelerator", "gpu", "--num_workers", "0",
           "--no_kernels", "--max_msa_seqs", "1024"]
    if a["msa"] is None:
        cmd.append("--use_msa_server")
    print(f"  {arm}: folding {N_SAMPLES} diffusion samples "
          f"(recycling {a['recycling']}, seed {a['seed']})", flush=True)
    subprocess.run(cmd, timeout=7200, check=False)
    models = sorted(pred.glob(f"{arm}_model_*.pdb"))
    if not models:
        raise RuntimeError(f"{arm}: boltz produced no models")
    return models


def score(pdb: Path, challenge: int, cfg) -> dict:
    c = cfg.conventions
    tag = pdb.stem                                  # <arm>_model_<n>
    pae = pdb.parent / f"pae_{tag}.npz"
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae, label=tag)
    r = {k: v.value for k, v in prodigy.compute(st).items()}
    r["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                               dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    r["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    r["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    if challenge == 1:
        r["dockq"] = dockq.compute(st, NATIVE)["dockq"].value
    r["model"] = int(tag.rsplit("_", 1)[1])
    return r


def main() -> int:
    cfg = load()
    OUT.mkdir(parents=True, exist_ok=True)
    verdicts = {}

    for arm, a in ARMS.items():
        print(f"\n=== {arm} (challenge {a['challenge']}) ===", flush=True)
        models = run(arm, cfg)
        rows = []
        for m in models:
            try:
                rows.append(score(m, a["challenge"], cfg))
            except Exception as e:                        # noqa: BLE001
                print(f"  {m.name}: SCORING FAILED {e}", file=sys.stderr, flush=True)
        rows.sort(key=lambda r: r["model"])
        (OUT / f"{arm}_scores.json").write_text(json.dumps(rows, indent=1))

        metrics = [k for k in ("ipsae", "dockq", "dg", "contacts", "iface_plddt",
                               "cdr_sasa") if k in rows[0]]
        print(f"  {'model':<7}" + "".join(f"{m:>14}" for m in metrics) +
              f"{'band(ipsae)':>13}{'final':>8}", flush=True)
        for r in rows:
            sc = evaluate({k: r[k] for k in metrics}
                          | {"netsolp": 0.60, "cdrh3_identity": 30.0},
                          challenge=a["challenge"], cfg=cfg)
            print(f"  {r['model']:<7}" + "".join(f"{r[m]:>14.3f}" for m in metrics) +
                  f"{sc.bands.get('ipsae','-'):>13}{str(sc.final):>8}", flush=True)
        spread = {m: max(r[m] for r in rows) - min(r[m] for r in rows) for m in metrics}
        verdicts[arm] = {"rows": rows, "spread": spread}
        print("  spread  " + "".join(f"{spread[m]:>14.3f}" for m in metrics), flush=True)

    # ---- pre-registered decision rule ----
    print("\n" + "=" * 72)
    ch2 = verdicts["ds_ch2"]["rows"]
    lo2 = min(r["ipsae"] for r in ch2)
    b = cfg.bands()["ipsae"]
    bands2 = {evaluate({"ipsae": r["ipsae"]}, challenge=2, cfg=cfg).bands.get("ipsae")
              for r in ch2}
    ch1 = verdicts["ds_ch1"]["rows"]
    bands1 = {k: {evaluate({k: r[k]}, challenge=1, cfg=cfg).bands.get(k) for r in ch1}
              for k in ("ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa")
              if k in ch1[0]}

    if lo2 < b.cutoff:
        print(f"VERDICT: Challenge 2 VIABILITY is diffusion-sample dependent "
              f"(lowest ipSAE {lo2:.3f} < {b.cutoff}). Disclose at the top of the Ch2 "
              f"docs and the deck; re-examine the '1 of 30 clears' framing.")
    elif len(bands2) > 1:
        print(f"VERDICT: Challenge 2 crosses a BAND edge across diffusion samples "
              f"({sorted(bands2)}). Fold into the existing 93.6-96.0 envelope and widen it.")
    else:
        print(f"VERDICT: Challenge 2 stable within band ({bands2.pop()}), "
              f"ipSAE spread {verdicts['ds_ch2']['spread']['ipsae']:.3f}.")

    moved1 = {k: v for k, v in bands1.items() if len(v) > 1}
    if moved1:
        print(f"         Challenge 1 ALSO crosses band edges: {moved1}. The claim that "
              f"Challenge 1 survives must be qualified.")
    else:
        print(f"         Challenge 1 stable in every band; ipSAE spread "
              f"{verdicts['ds_ch1']['spread']['ipsae']:.3f}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
