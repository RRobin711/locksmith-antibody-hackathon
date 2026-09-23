#!/usr/bin/env python3
"""How often can a backbone yield a §9.2-clean sequence under CONSTRAINED re-design?

THE QUESTION THIS ANSWERS, AND WHY THE OBVIOUS NUMBER IS THE WRONG ONE.

Measured on the existing pool, a hard liability gate keeps **5 of 30** sequences (17%) and
every one of those five scores ipSAE **0.000** under a correct alignment, while the dropped
group scores significantly higher (p=0.015, rank-biserial +0.68). That looks like the gate
selecting against binding -- Asn is a workhorse paratope residue and the motifs form cheaply
by chance.

But 17% is the rate at which **unconstrained** generation happens to avoid these motifs. It
is not the quantity that matters. The quantity that matters is: **given a backbone, can
ProteinMPNN produce a clean sequence at all if you forbid the offending residue and let it
re-pick the neighbourhood?** That is a different number and probably a much higher one,
because the network re-optimises jointly rather than having one residue swapped underneath it.

WHY CONSTRAINED RE-DESIGN IS NOT THE SAME OPERATION AS THE FIX ARMS. The fix arms
(`results/liability_fix_arms.md`) changed ONE residue in a sequence ProteinMPNN had already
optimised jointly -- 3 of 3 fatal, including at zero contacts. That result is about
**post-hoc point mutation breaking a joint optimisation**. It says nothing about whether a
liability-free sequence exists on that backbone. This script asks the second question.

METHOD, and it is the same code path that produced the originals:
  * RFantibody's ProteinMPNN, its weights, its HLT loop parsing, framework held fixed via
    `fixed_positions_dict` -- only the labelled CDR loops are designed.
  * Attempt 1 is unconstrained, exactly as the pilot ran it.
  * Any sequence carrying an N-X-S/T sequon or an NG/DG motif **inside a CDR** is scanned,
    the offending positions are collected, and the next attempt forbids that residue AT
    THOSE POSITIONS ONLY, via `arg_dict['omit_AA_dict']`. Constraints accumulate across
    attempts.
  * Up to MAX_ATTEMPTS. Report per backbone: clean or not, and at which attempt.

Crucially this is a per-position constraint, NOT the CLI's global `-omit_AAs`, which would
ban asparagine from every loop and reintroduce the very anti-selection the measurement
exists to avoid.

Sequence-only, CPU, no folds, no GPU, no money.
"""
from __future__ import annotations

import json, sys, time
from pathlib import Path

sys.path.insert(0, "/home/rrobin711/.cache/rfantibody/src")

BB = Path("runs/challenge2_pod/c2/bb")
OUT = Path("runs/redesign_yield")
WEIGHTS = Path("/home/rrobin711/.cache/rfantibody/weights/ProteinMPNN_v48_noise_0.2.pt")
LOOPS = "H1,H2,H3,L1,L2,L3"
SEQS_PER_ATTEMPT = 8
MAX_ATTEMPTS = 5
TEMPERATURE = 0.2
CDR = ("CDR-H1", "CDR-H2", "CDR-H3", "CDR-L1", "CDR-L2", "CDR-L3")


# `liabilities` labels chains 'heavy'/'light'; ProteinMPNN's omit_AA_dict is keyed by the
# PDB chain LETTER. Getting this wrong does not raise -- tied_featurize finds no entry for
# 'H', applies no constraint, and the loop silently degrades into plain RESAMPLING while
# still printing plausible per-backbone results. That happened on the first run here and
# was caught only by asserting the constraint bound, below.
CHAIN_LETTER = {"heavy": "H", "light": "L"}


def split_chains(seq: str, lengths: dict) -> dict:
    """Split ProteinMPNN's returned sequence into chains BY LENGTH.

    `generate_sequences` returns the masked chains **concatenated with no separator** --
    a single 231-character string for a 122+109 Fv, not 'heavy/light'. Assuming a '/'
    silently skipped every sequence in this loop, so nothing was ever scanned and the
    yield read 0/18 for a reason that had nothing to do with the backbones.
    """
    out, i = {}, 0
    for ch, n in lengths.items():
        out[ch] = seq[i:i + n]
        i += n
    if i != len(seq):
        raise SystemExit(f"chain lengths {lengths} sum to {i} but the sequence is "
                         f"{len(seq)} residues; the split convention is wrong.")
    return out


def offending(heavy: str, light: str) -> list[tuple[str, int, str]]:
    """(chain, 1-based position within that chain, residue to forbid) for each CDR violation."""
    from locksmith.metrics import liabilities
    out = []
    rep = liabilities.compute(heavy, light)
    for x in rep.liabilities:
        region = getattr(x, "region", "") or ""
        if region not in CDR:
            continue
        kind, motif = getattr(x, "kind", ""), getattr(x, "motif", "")
        ch, pos = getattr(x, "chain", ""), getattr(x, "position", None)
        if pos is None:
            continue
        ch = CHAIN_LETTER.get(ch, ch)
        if kind == "glycosylation":
            out.append((ch, int(pos), "N"))          # forbid the acceptor
        elif motif in ("NG", "DG"):
            out.append((ch, int(pos), motif[0]))     # forbid N or D at the acceptor
    return out


def main() -> int:
    import torch
    from rfantibody.proteinmpnn import util_protein_mpnn as mpnn_util
    from rfantibody.proteinmpnn.sample_features import SampleFeatures
    from rfantibody.util.pose import Pose

    OUT.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")          # small model; avoids the Blackwell/torch-2.3 issue
    model = mpnn_util.init_seq_optimize_model(
        device, hidden_dim=128, num_layers=3, backbone_noise=0.0,
        num_connections=48, checkpoint_path=str(WEIGHTS))

    backbones = sorted(BB.glob("*.pdb"))
    print(f"{len(backbones)} backbones, up to {MAX_ATTEMPTS} attempts x "
          f"{SEQS_PER_ATTEMPT} sequences, loops {LOOPS}\n", flush=True)

    results = []
    for n, bb in enumerate(backbones, 1):
        pose = Pose.from_pdb(str(bb))
        sf = SampleFeatures(pose, bb.stem)
        sf.loop_string2fixed_res(LOOPS)

        import numpy as _np
        _chain_arr = sf.pose.chain
        lengths = {c: int((_chain_arr == c).sum()) for c in sf.chains[:-1]}

        constraints: dict[str, dict[int, str]] = {}
        clean_at, clean_seq = None, None
        t0 = time.time()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            tmp = OUT / "temp.pdb"
            sf.pose.dump_pdb(str(tmp))
            feats = mpnn_util.generate_seqopt_features(str(tmp), sf.chains)
            tmp.unlink(missing_ok=True)
            args = mpnn_util.set_default_args(SEQS_PER_ATTEMPT, omit_AAs=["C", "X"])
            args["temperature"] = TEMPERATURE
            # tied_featurize keys both dicts on feature_dict['name'], which generate_
            # seqopt_features derives from the dump PATH, not the basename. Hardcoding
            # "temp" works only if you dump into the cwd as the original script does.
            key = feats["name"]
            if constraints:
                # tied_featurize indexes omit_AA_dict[name][letter] for EVERY chain in
                # the structure without guarding, so a chain with no constraints needs an
                # explicit empty list rather than being absent. Omitting it raises
                # KeyError deep inside featurisation on the first backbone whose
                # violations happen to fall on only one chain.
                args["omit_AA_dict"] = {key: {
                    ch: [[[pos], aas] for pos, aas in sorted(constraints.get(ch, {}).items())]
                    for ch in sf.chains}}
            seqs = mpnn_util.generate_sequences(
                model, device, feats, args, sf.chains[:-1], [sf.chains[-1]],
                fixed_positions_dict={key: sf.fixed_res})
            # POSITIVE ASSERTION that the constraint actually bound. Absence of an error
            # is not evidence a constraint applied -- this loop ran a full unconstrained
            # pass before anyone noticed. Same principle the campaign plan demands for the
            # MSA: verify the thing was USED, do not infer it from nothing having failed.
            if constraints:
                for s_chk, _sc in seqs:
                    by_letter = split_chains(s_chk, lengths)
                    for ch_c, d_c in constraints.items():
                        seqc = by_letter.get(ch_c)
                        if seqc is None:
                            raise SystemExit(
                                f"{bb.stem}: constraint chain {ch_c!r} is not one of "
                                f"{sorted(by_letter)}; the chain-label convention is wrong.")
                        for pos_c, aas_c in d_c.items():
                            if pos_c <= len(seqc) and seqc[pos_c - 1] in aas_c:
                                raise SystemExit(
                                    f"{bb.stem}: constraint did NOT bind -- forbade "
                                    f"{aas_c!r} at {ch_c}{pos_c}, ProteinMPNN returned "
                                    f"{seqc[pos_c-1]!r}. Refusing to report a yield "
                                    f"measured without constraints.")

            for s, _score in seqs:
                chains_d = split_chains(s, lengths)
                h, l = chains_d["H"], chains_d["L"]
                bad = offending(h, l)
                if not bad:
                    clean_at, clean_seq = attempt, (h, l)
                    break
                for ch, pos, aa in bad:
                    constraints.setdefault(ch, {})
                    constraints[ch][pos] = "".join(sorted(set(constraints[ch].get(pos, "") + aa)))
            if clean_at:
                break
        dt = time.time() - t0
        results.append({"backbone": bb.stem, "clean": clean_at is not None,
                        "attempt": clean_at, "seconds": round(dt, 1),
                        "constraints": {c: {str(k): v for k, v in d.items()}
                                        for c, d in constraints.items()},
                        "heavy": clean_seq[0] if clean_seq else None,
                        "light": clean_seq[1] if clean_seq else None})
        status = f"clean at attempt {clean_at}" if clean_at else f"NO clean sequence in {MAX_ATTEMPTS}"
        print(f"[{n}/{len(backbones)}] {bb.stem:<12} {status:<34} {dt:.0f}s", flush=True)
        (OUT / "yield.json").write_text(json.dumps(results, indent=1))

    ok = sum(1 for r in results if r["clean"])
    print(f"\nCONSTRAINED RE-DESIGN YIELD: {ok}/{len(results)} backbones "
          f"({100*ok/max(len(results),1):.0f}%) produced a §9.2-clean sequence")
    if ok:
        att = [r["attempt"] for r in results if r["clean"]]
        print(f"  attempts needed: {sorted(att)}  (median {sorted(att)[len(att)//2]})")
    print(f"  compare: unconstrained generation avoided these motifs in 5/30 sequences (17%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
