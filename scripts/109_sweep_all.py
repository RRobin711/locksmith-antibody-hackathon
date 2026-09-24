#!/usr/bin/env python3
"""The whole depth sweep in ONE process: all strata, scoring, readout. Runs unattended.

WHY ONE SCRIPT. If strata are launched one at a time from an interactive session, that
session dying leaves the unit idle after the first stratum -- the same failure as the
systemd-oomd kill, in a different shape. Everything from generation to the final readout
happens inside the unit.

WRITES INCREMENTALLY. After every stratum, and after every fold's score, results go to
disk. A run stopped at 4 a.m. still leaves usable curve points.

RESUME KEYS ON ARTEFACTS via `fold_is_complete`, so a restart loses only folds in flight.

PROGRESS IS WRITTEN TO BE READ COLD: stratum, fold index, ISO timestamp, elapsed, and a
running tally, so a stop can be located without reconstructing anything.

STALL CHECK IS INTERNAL. No watchdog outside the unit: a fold exceeding STALL_S is logged
loudly and the run continues to the next, rather than depending on a session that may be
gone.
"""
from __future__ import annotations

import json, os, statistics as st, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/home/rrobin711/.cache/rfantibody/src")

ROOT = Path("runs/sweep")
LOG = ROOT / "progress.log"
MSA = Path("data/msa_cache/pd1_123_handbook.csv")
BB = Path("runs/challenge2_pod/c2/bb")
RECYCLING, SAMPLES, SEED = 10, 5, 1
STALL_S = 900
CDR = ("CDR-H1", "CDR-H2", "CDR-H3", "CDR-L1", "CDR-L2", "CDR-L3")
STRATA = [("A", 4), ("B", 8), ("C", 16)]          # cumulative sequences per backbone
MODE = os.environ.get("SWEEP_MODE", "serial")      # serial | batch
BATCH = int(os.environ.get("SWEEP_BATCH", "6"))
MAX_STRATUM = os.environ.get("SWEEP_MAX", "C")


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(line + "\n")


def offending(heavy: str, light: str):
    from locksmith.metrics import liabilities
    LET = {"heavy": "H", "light": "L"}
    out = []
    for x in liabilities.compute(heavy, light).liabilities:
        if (getattr(x, "region", "") or "") not in CDR:
            continue
        k, m = getattr(x, "kind", ""), getattr(x, "motif", "")
        ch, pos = LET.get(getattr(x, "chain", ""), ""), getattr(x, "position", None)
        if pos is None:
            continue
        if k == "glycosylation":
            out.append((ch, int(pos), "N"))
        elif m in ("NG", "DG"):
            out.append((ch, int(pos), m[0]))
    return out


def generate(target_depth: int) -> dict:
    """Constrained sequences per backbone, cumulative to `target_depth`. CPU, free."""
    import torch
    from rfantibody.proteinmpnn import util_protein_mpnn as mu
    from rfantibody.proteinmpnn.sample_features import SampleFeatures
    from rfantibody.util.pose import Pose

    store = ROOT / "sequences.json"
    have = json.loads(store.read_text()) if store.exists() else {}
    dev = torch.device("cpu")
    model = mu.init_seq_optimize_model(
        dev, hidden_dim=128, num_layers=3, backbone_noise=0.0, num_connections=48,
        checkpoint_path="/home/rrobin711/.cache/rfantibody/weights/ProteinMPNN_v48_noise_0.2.pt")
    for bb in sorted(BB.glob("*.pdb")):
        got = have.get(bb.stem, [])
        if len(got) >= target_depth:
            continue
        sf = SampleFeatures(Pose.from_pdb(str(bb)), bb.stem)
        sf.loop_string2fixed_res("H1,H2,H3,L1,L2,L3")
        lengths = {c: int((sf.pose.chain == c).sum()) for c in sf.chains[:-1]}
        cons: dict = {}
        tries = 0
        while len(got) < target_depth and tries < 12:
            tries += 1
            tmp = ROOT / "tmp.pdb"
            sf.pose.dump_pdb(str(tmp))
            feats = mu.generate_seqopt_features(str(tmp), sf.chains)
            tmp.unlink(missing_ok=True)
            args = mu.set_default_args(8, omit_AAs=["C", "X"])
            args["temperature"] = 0.2
            key = feats["name"]
            if cons:
                args["omit_AA_dict"] = {key: {c: [[[p], a] for p, a in sorted(cons.get(c, {}).items())]
                                              for c in sf.chains}}
            for seq, _ in mu.generate_sequences(model, dev, feats, args, sf.chains[:-1],
                                                [sf.chains[-1]],
                                                fixed_positions_dict={key: sf.fixed_res}):
                i, ch = 0, {}
                for c, n in lengths.items():
                    ch[c] = seq[i:i + n]; i += n
                bad = offending(ch["H"], ch["L"])
                if not bad:
                    if [ch["H"], ch["L"]] not in [[g[0], g[1]] for g in got]:
                        got.append([ch["H"], ch["L"]])
                else:
                    for c, p, a in bad:
                        cons.setdefault(c, {})
                        cons[c][p] = "".join(sorted(set(cons[c].get(p, "") + a)))
                if len(got) >= target_depth:
                    break
        have[bb.stem] = got
        store.write_text(json.dumps(have, indent=1))
    return have


def score_one(pred: Path, label: str, cfg, net_cache: dict, heavy: str, light: str):
    from locksmith.metrics import ipsae, plddt, prodigy, sasa, netsolp, novelty
    from locksmith.types import Provenance, Structure
    c = cfg.conventions
    key = heavy + "|" + light
    if key not in net_cache:
        net_cache[key] = netsolp.compute(heavy, light)["netsolp"].value
    ident = novelty.compute(heavy, challenge=2).value
    vals = []
    for p in sorted(pred.glob(f"{label}_model_*.pdb")):
        pae = p.parent / f"pae_{p.stem}.npz"
        if not pae.exists():
            continue
        s = Structure(pdb=p, provenance=Provenance.PREDICTION, pae=pae, label=p.stem)
        pr = prodigy.compute(s)
        vals.append({"ipsae": ipsae.compute(s, pae_cutoff=c["ipsae_pae_cutoff"],
                                            dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value,
                     "dg": pr["dg"].value, "contacts": pr["contacts"].value,
                     "iface_plddt": plddt.compute(s, cutoff=c["interface_dist_cutoff"]).value,
                     "cdr_sasa": sasa.compute(s)[f"cdr_sasa_{c['cdr_sasa_state']}"].value,
                     "netsolp": net_cache[key], "cdrh3_identity": ident})
    if not vals:
        return None
    return {k: st.median([v[k] for v in vals]) for k in vals[0]} | {"n": len(vals)}


def main() -> int:
    from locksmith.config import load
    from locksmith.fold import fold_is_complete
    from locksmith.fold.boltz import fold
    from locksmith.score import evaluate

    cfg = load()
    ROOT.mkdir(parents=True, exist_ok=True)
    ag = json.loads(Path("data/refs/handbook_constructs.json").read_text())["antigen"]
    scores_path = ROOT / "scores.json"
    scores = json.loads(scores_path.read_text()) if scores_path.exists() else {}
    net_cache: dict = {}
    log(f"=== SWEEP START  mode={MODE} batch={BATCH} max_stratum={MAX_STRATUM} ===")

    for name, depth in STRATA:
        if name > MAX_STRATUM:
            log(f"stratum {name} not authorised (max={MAX_STRATUM}); stopping")
            break
        log(f"--- stratum {name}: cumulative depth {depth} sequences/backbone ---")
        t0 = time.time()
        seqs = generate(depth)
        log(f"stratum {name}: sequences ready for {len(seqs)} backbones "
            f"({time.time()-t0:.0f}s CPU)")

        todo = []
        for bb, lst in sorted(seqs.items()):
            for i, (h, l) in enumerate(lst[:depth]):
                lab = f"sw_{bb}_s{i}"
                pred = ROOT / lab / f"boltz_results_{lab}" / "predictions" / lab
                if not fold_is_complete(pred, lab, n_models=SAMPLES):
                    todo.append((lab, bb, i, h, l))
        log(f"stratum {name}: {len(todo)} folds to run")

        done = 0
        for lab, bb, i, h, l in todo:
            t = time.time()
            try:
                fold(lab, h, l, ag, out_root=ROOT, antigen_msa=MSA, seed=SEED,
                     diffusion_samples=SAMPLES, recycling_steps=RECYCLING, timeout=5400)
                el = time.time() - t
                done += 1
                flag = "  *** SLOW ***" if el > STALL_S else ""
                log(f"  [{name} {done}/{len(todo)}] {lab} ok {el:.0f}s{flag}")
            except Exception as e:                                    # noqa: BLE001
                log(f"  [{name} {done}/{len(todo)}] {lab} FAILED {str(e)[:160]}")
                continue
            pred = ROOT / lab / f"boltz_results_{lab}" / "predictions" / lab
            m = score_one(pred, lab, cfg, net_cache, h, l)
            if m:
                sc = evaluate({k: m[k] for k in ("ipsae", "dg", "contacts", "iface_plddt",
                                                 "cdr_sasa", "netsolp", "cdrh3_identity")},
                              challenge=2, cfg=cfg)
                scores[lab] = m | {"backbone": bb, "seq_index": i, "stratum": name,
                                   "final": sc.final, "viable": sc.viable}
                scores_path.write_text(json.dumps(scores, indent=1))

        # ---- stratum readout, written incrementally ----
        cur = {k: v for k, v in scores.items() if v["seq_index"] < depth}
        by_bb: dict = {}
        for v in cur.values():
            by_bb.setdefault(v["backbone"], []).append(v)
        clear = sum(1 for v in cur.values() if v["ipsae"] >= 0.60)
        bb_best = {b: max(x["ipsae"] for x in g) for b, g in by_bb.items()}
        bb_clear = sum(1 for v in bb_best.values() if v >= 0.60)
        five = sum(1 for v in cur.values() if v.get("n") == 5 and v["ipsae"] >= 0.60)
        rep = {"stratum": name, "depth": depth, "sequences_scored": len(cur),
               "backbones": len(by_bb),
               "per_sequence_clear_rate": round(clear / max(len(cur), 1), 4),
               "sequences_clearing": clear,
               "backbones_with_a_clearing_sequence": bb_clear,
               "best_overall": max(bb_best.values()) if bb_best else None,
               "best_backbone": max(bb_best, key=bb_best.get) if bb_best else None,
               "elapsed_s": round(time.time() - t0, 1)}
        (ROOT / f"readout_{name}.json").write_text(json.dumps(rep, indent=1))
        log(f"STRATUM {name} DONE: {clear}/{len(cur)} sequences clear "
            f"({100*rep['per_sequence_clear_rate']:.1f}%), "
            f"{bb_clear}/{len(by_bb)} backbones have one, best "
            f"{rep['best_overall']:.3f} on {rep['best_backbone']}, "
            f"{rep['elapsed_s']/3600:.2f} h")

    log("=== SWEEP COMPLETE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
