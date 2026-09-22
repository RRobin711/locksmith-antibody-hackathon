#!/usr/bin/env python3
"""Novelty probe: how much of the rubric's novelty score can be earned WITHOUT
touching the paratope?  CPU-only generation (no GPU contention).

THE OBSERVATION THAT MOTIVATES IT
----------------------------------
Pembrolizumab's CDR-H3 is `ARRDYRFDMGFDY` (13 aa). Measured against the antigen in
the 5GGS crystal (heavy-atom pairs within 5.0 A), its positions are wildly unequal:

    idx  95  A    0 contacts        idx 102  D    6
    idx  96  R    0                 idx  97  R   23
    idx  98  D    0                 idx 103  M   29
    idx 104  G    0                 idx  99  Y   42
    idx 105  F    0                 idx 101  F   52
    idx 107  Y    0                 idx 100  R   81
    idx 106  D    3

**Six of thirteen positions touch the antigen not at all.** The rubric's novelty
metric is CDR-H3 sequence identity to the parent, banded: < 70% scores Good, and at
13 residues that needs only 4 substitutions. Four substitutions can be taken entirely
from the zero-contact set.

So the rubric's novelty axis can be maximised while leaving the entire paratope
intact. This arm measures that, and measures the contrast that makes it a finding
rather than a trick.

THE THREE ARMS

    A  k=4, zero-contact positions {95, 96, 98, 104}          identity 69.2%  (Good)
    B  k=6, ALL zero-contact positions {95,96,98,104,105,107} identity 53.8%  (Good)
    C  k=6, the six HIGHEST-contact positions {100,101,99,103,97,106}
                                                              identity 53.8%  (Good)

**B and C score IDENTICALLY on the rubric's novelty metric — 53.8%, Good band, same
sub-score, same contribution to `final` — while differing by 233 antigen contacts in
what they are allowed to change.** If B retains the pose and C does not, then the
scored novelty axis is blind to the distinction that determines whether the molecule
still binds. That is the same shape of result as the pLDDT/ensemble finding: a scored
metric that does not measure the thing its name implies.

Note the consequence for **Challenge 2**, which has no DockQ: there, nothing in the
rubric would catch the difference between B and C at all.

WHAT IS DESIGNED, AND WHY H1/H2 ARE HELD NATIVE HERE
-----------------------------------------------------
Only the chosen CDR-H3 positions. The 239-design pool redesigns H1, H2 and H3
together, which is right for a design campaign and wrong for this measurement: H1 and
H2 also contact the antigen, so redesigning them would confound "changed the paratope
via H3" with "changed it via H1/H2". Holding them native isolates the variable. These
are therefore **rubric probes, not design candidates.**

THIS IS NOT A SUBMISSION STRATEGY, AND MUST NOT BECOME ONE.
An arm-A design is a near-copy of pembrolizumab that scores Good on novelty. Proposing
it as "our design" would be gaming a metric we have just demonstrated to be gameable,
and the project's whole position is that the numbers should mean something. The output
of this arm is a measurement about the rubric. M3's named design does not change.

Writes designs/novelty_probe/designs.json. Runs ProteinMPNN on CPU
(CUDA_VISIBLE_DEVICES="") so it cannot contend with the overnight folds for the GPU.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

from locksmith.design.mpnn import MPNN_DIR, MPNN_RUN, _parse_fasta, cdr_positions
from locksmith.io.pdb import seq_for_folding
from locksmith.metrics import novelty

PARENT = Path("data/refs/prepared/5ggs_ABZ.pdb")
OUT = Path("designs/novelty_probe")
WORK = Path("runs/novelty_probe_mpnn")
TEMP = 0.3          # diversity comes from omit_AA_jsonl, not from temperature
N_PER_ARM = 14

ARMS = {
    "A_k4_nocontact":   [95, 96, 98, 104],
    "B_k6_nocontact":   [95, 96, 98, 104, 105, 107],
    "C_k6_paratope":    [97, 99, 100, 101, 103, 106],
}


def generate(designable: list[int], n: int, seed: int, tag: str) -> list[dict]:
    heavy = seq_for_folding(PARENT, "A")
    light = seq_for_folding(PARENT, "B")
    antigen = seq_for_folding(PARENT, "C")
    fixed = [i + 1 for i in range(len(heavy)) if i not in set(designable)]
    name = PARENT.stem
    # FORBID THE NATIVE RESIDUE AT EVERY DESIGNED POSITION.
    # Measured 2026-09-20: without this, MPNN at T=0.3 recovers the native residue at
    # most of these positions and arm A came back at 92.3% identity instead of the
    # intended 69.2% -- the arm would have silently tested nothing. ProteinMPNN is a
    # sequence-RECOVERY model, so "designable" does not mean "will change". omit_AA_jsonl
    # takes [[1-based positions], "AAs to forbid"] per chain, and every chain in the
    # complex must appear or the featuriser raises a KeyError on the missing letter.
    omit = {name: {"A": [[[i + 1], heavy[i]] for i in designable], "B": [], "C": []}}
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chains.jsonl").write_text(json.dumps({name: [["A"], ["B", "C"]]}) + "\n")
        (td / "fixed.jsonl").write_text(json.dumps({name: {"A": fixed}}) + "\n")
        (td / "omit.jsonl").write_text(json.dumps(omit) + "\n")
        env = dict(os.environ, CUDA_VISIBLE_DEVICES="")     # CPU: never race the folds
        cmd = [sys.executable, str(MPNN_RUN),
               "--pdb_path", str(PARENT.resolve()),
               "--pdb_path_chains", "A",
               "--chain_id_jsonl", str(td / "chains.jsonl"),
               "--fixed_positions_jsonl", str(td / "fixed.jsonl"),
               "--omit_AA_jsonl", str(td / "omit.jsonl"),
               "--omit_AAs", "XC",          # no new unpaired cysteines (S1 liability rule)
               "--out_folder", str(work.resolve()),
               "--num_seq_per_target", str(n * 3),          # oversample, dedupe below
               "--sampling_temp", str(TEMP),
               "--seed", str(seed), "--batch_size", "1"]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=MPNN_DIR, env=env, timeout=3600)

    fa = work / "seqs" / f"{name}.fa"
    if not fa.exists():
        raise SystemExit(f"ProteinMPNN wrote nothing (rc={proc.returncode}):\n"
                         f"{(proc.stdout + proc.stderr)[-1200:]}")
    recs = _parse_fasta(fa)
    native_h3 = "".join(heavy[i] for i in cdr_positions(heavy)["cdr3"])

    seen, out = set(), []
    for seq, meta in recs[1:]:
        h = seq.split("/")[0]
        if len(h) != len(heavy):
            raise SystemExit(f"MPNN returned {len(h)} aa, expected {len(heavy)}")
        # every position outside `designable` must be untouched -- the whole point
        for i in range(len(heavy)):
            if i not in set(designable) and h[i] != heavy[i]:
                raise SystemExit(f"{tag}: position {i} changed but was not designable")
        h3 = "".join(h[i] for i in cdr_positions(h)["cdr3"])
        # Every designed position must actually differ, or the arm is not what it says.
        for i in designable:
            if h[i] == heavy[i]:
                raise SystemExit(
                    f"{tag}: position {i} kept its native {heavy[i]} despite omit_AA_jsonl")
        if h3 in seen or h3 == native_h3:
            continue
        seen.add(h3)
        out.append({"heavy": h, "light": light, "antigen": antigen,
                    "cdrh3": h3, "score": meta.get("score", float("nan")),
                    "n_designable": len(designable),
                    "designable": designable})
        if len(out) >= n:
            break
    return out


def main() -> int:
    heavy = seq_for_folding(PARENT, "A")
    native_h3 = "".join(heavy[i] for i in cdr_positions(heavy)["cdr3"])
    print(f"parent CDR-H3: {native_h3}")
    OUT.mkdir(parents=True, exist_ok=True)

    designs = []
    for k, (tag, pos) in enumerate(ARMS.items()):
        got = generate(pos, N_PER_ARM, seed=700 + k, tag=tag)
        for j, d in enumerate(got, 1):
            d["design_id"] = f"probe_{tag}_{j:03d}"
            d["arm"] = tag
            d["cdrh3_identity"] = novelty.compute(d["heavy"]).value
            designs.append(d)
        ids = sorted({d["cdrh3_identity"] for d in designs if d["arm"] == tag})
        print(f"  {tag:18s} {len(got):3d} designs, positions {pos}, "
              f"identity {ids}")
    (OUT / "designs.json").write_text(json.dumps(designs, indent=1))
    print(f"\nwrote {OUT/'designs.json'}: {len(designs)} designs")

    # The claim this arm rests on: B and C are indistinguishable on the scored axis.
    for a in ("B_k6_nocontact", "C_k6_paratope"):
        v = sorted({d["cdrh3_identity"] for d in designs if d["arm"] == a})
        print(f"  {a}: cdrh3_identity {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
