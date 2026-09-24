#!/usr/bin/env python3
"""Check 3: has `bb_8_0` drifted toward a known anti-PD-1, and the full §5.2 breakdown.

WHY THIS IS NOT THE MATCHED CONTROL. That answered "is 0.859 a plausible score for this
task?" This answers a different question: "does it score well because it has become
something Boltz already knows?" A de novo design that has converged toward pembrolizumab's
or nivolumab's paratope would score highly for a reason that is not novelty, and the
rubric's own novelty metric reads **CDR-H3 only**, so it cannot see drift in the other
five loops.

`cdrh3_identity` is computed with `challenge=2` -- human germline, which is the reference
§6.3.1 specifies for this challenge. Calling `novelty.compute()` without it silently uses
Challenge 1's Keytruda reference and puts the wrong number in the package, which happened
once already.
"""
from __future__ import annotations

import json, statistics as st
from pathlib import Path

import gemmi

from locksmith.config import load
from locksmith.metrics import ipsae, plddt, prodigy, sasa, novelty, netsolp, liabilities
from locksmith.numbering import number
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

METS = ["ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa", "netsolp", "cdrh3_identity"]
LOOPS = ["cdr1", "cdr2", "cdr3"]


def pct_identity(a: str, b: str) -> float:
    from Bio import Align
    if not a or not b:
        return 0.0
    al = Align.PairwiseAligner(mode="global", match_score=1, mismatch_score=0,
                               open_gap_score=-1, extend_gap_score=-0.5)
    best = al.align(a, b)[0]
    m = sum(1 for x, y in zip(best[0], best[1]) if x == y and x != "-")
    return 100.0 * m / max(len(a), len(b))


def fv_pair(pdb: Path):
    st_ = gemmi.read_structure(str(pdb)); st_.setup_entities()
    h = l = None
    for ch in st_[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        if len(res) < 50:
            continue
        s = gemmi.one_letter_code([r.name for r in res]).upper()
        if "X" in s:
            continue
        n = number(s)
        if n is None:
            continue
        if n.chain_type == "H" and h is None:
            h = s
        elif n.chain_type in ("K", "L") and l is None:
            l = s
    return h, l


def main() -> int:
    cfg = load(); c = cfg.conventions
    y = {r["backbone"]: r for r in json.loads(
        Path("runs/redesign_yield/yield.json").read_text()) if r["clean"]}
    d = y["bb_8_0"]
    heavy, light = d["heavy"], d["light"]

    # ---------- memorisation ----------
    refs = {"pembrolizumab": Path("data/refs/5ggs.pdb"),
            "nivolumab": Path("data/refs/5wt9.pdb")}
    ours = {"H": number(heavy), "L": number(light)}
    print("=== CDR comparison against known anti-PD-1 antibodies ===\n")
    print(f"{'loop':<8}{'bb_8_0':<20}" + "".join(f"{k:<22}" for k in refs) + "identity")
    worst = 0.0
    table = {}
    for name, p in refs.items():
        rh, rl = fv_pair(p)
        refs[name] = {"H": number(rh), "L": number(rl)}
    for chain in ("H", "L"):
        for loop in LOOPS:
            mine = getattr(ours[chain], loop)
            row = f"{chain}{loop[-1]:<7}{mine:<20}"
            ids = []
            for name in refs:
                theirs = getattr(refs[name][chain], loop)
                pid = pct_identity(mine, theirs)
                ids.append(pid)
                row += f"{theirs + f' ({pid:.0f}%)':<22}"
            worst = max(worst, max(ids))
            table[f"{chain}{loop[-1]}"] = {"ours": mine,
                                           **{k: getattr(refs[k][chain], loop) for k in refs},
                                           "max_identity": round(max(ids), 1)}
            print(row)
    print(f"\nhighest identity of ANY bb_8_0 CDR to ANY known anti-PD-1 CDR: {worst:.1f}%")

    ident = novelty.compute(heavy, challenge=2)
    print(f"\nscored novelty metric (§6.3.1, challenge=2 -> human germline):")
    print(f"  cdrh3_identity = {ident.value}   {ident.detail or ''}")
    ident_c1 = novelty.compute(heavy, challenge=1)
    print(f"  (for reference, the Challenge 1 metric vs Keytruda: {ident_c1.value})")

    # ---------- full §5.2 breakdown ----------
    label = "cf_bb_8_0"
    pred = Path("runs/constrained_fold") / label / f"boltz_results_{label}" / "predictions" / label
    net = netsolp.compute(heavy, light)["netsolp"].value
    per = []
    for p in sorted(pred.glob(f"{label}_model_*.pdb")):
        pae = p.parent / f"pae_{p.stem}.npz"
        s = Structure(pdb=p, provenance=Provenance.PREDICTION, pae=pae, label=p.stem)
        pr = prodigy.compute(s)
        per.append({"model": int(p.stem.rsplit("_", 1)[1]),
            "ipsae": ipsae.compute(s, pae_cutoff=c["ipsae_pae_cutoff"],
                                   dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value,
            "dg": pr["dg"].value, "contacts": pr["contacts"].value,
            "iface_plddt": plddt.compute(s, cutoff=c["interface_dist_cutoff"]).value,
            "cdr_sasa": sasa.compute(s)[f"cdr_sasa_{c['cdr_sasa_state']}"].value,
            "netsolp": net, "cdrh3_identity": ident.value})
    per.sort(key=lambda x: x["model"])
    med = {k: st.median([x[k] for x in per]) for k in METS}
    scs = [evaluate({k: x[k] for k in METS}, challenge=2, cfg=cfg) for x in per]
    scm = evaluate(med, challenge=2, cfg=cfg)

    print("\n=== §5.2 breakdown, per diffusion sample ===")
    print("metric".ljust(16) + "".join(f"model_{i}".rjust(11) for i in range(len(per))) + "MEDIAN".rjust(11))
    for k in METS:
        print(f"{k:<16}" + "".join(f"{x[k]:>11.3f}" for x in per) + f"{med[k]:>11.3f}")
    print("\nband / sub-score per sample")
    for x, sc in zip(per, scs):
        parts = " ".join("{}={}({:.0f})".format(k, sc.bands.get(k, "-"), sc.sub.get(k, 0)) for k in METS)
        print(f"  model_{x['model']}  final={sc.final:>6.1f}  viable={sc.viable}   {parts}")
    print(f"\nmedian-of-metrics composite {scm.final} | per-sample finals "
          f"{[s.final for s in scs]} | viable {sum(1 for s in scs if s.viable)}/5")
    rep = liabilities.compute(heavy, light)
    print(f"§9.2 pass: {rep.handbook_9_2_pass()[0]}")

    Path("runs/constrained_fold/bb_8_0_check3.json").write_text(json.dumps(
        {"cdr_table": table, "max_identity_to_known": round(worst, 1),
         "cdrh3_identity_germline": ident.value, "per_sample": per, "median": med,
         "finals": [s.final for s in scs],
         "viable": sum(1 for s in scs if s.viable)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
