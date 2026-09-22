#!/usr/bin/env python3
"""Re-derive every headline number in `results/audit_response_2026-09-22.md` from the
files, and check the patch-null script does what its docstring claims.

WHY. The pattern this project keeps hitting is that the NEWEST claims carry the errors
the audits exist to catch -- four overstatements in one day on 2026-09-20, an inverted
germline claim on 2026-09-21, a dangling file reference written into the shipped
submission on 2026-09-22. There is no reason to assume last night's corrections are
exempt, and they were written by the same process that produced the errors.

Every check prints PASS or FAIL with both numbers. Nothing is taken on trust; where a
claim cannot be checked from the files, it is reported as UNVERIFIABLE rather than
quietly assumed.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import numpy as np
from scipy.stats import spearmanr

RESULTS: list[tuple[str, bool | None, str]] = []


def check(name: str, ok: bool | None, detail: str) -> None:
    # COERCE. numpy comparisons return np.bool_, and `np.True_ is True` is False, so an
    # `ok is True` summary silently reports genuine passes as UNVERIFIABLE and json.dumps
    # refuses to serialise them. Found by this script auditing itself on first run --
    # which is the same failure class it exists to catch, one level up.
    ok = None if ok is None else bool(ok)
    RESULTS.append((name, ok, detail))
    tag = "PASS" if ok else ("FAIL" if ok is False else "UNVERIFIABLE")
    print(f"[{tag:12s}] {name}: {detail}", flush=True)


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


# ---------------------------------------------------------------- A1: DockQ
def audit_dockq() -> None:
    pkg = Path("submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge1")
    native = Path("data/refs/prepared/5ggs_ABZ.pdb")
    model = pkg / "structures" / "design_1_complex.pdb"
    if not model.exists():
        check("A1 DockQ", None, "package not built")
        return
    r = subprocess.run(["DockQ", str(model), str(native)],
                       capture_output=True, text=True)
    check("A1 DockQ refuses at defaults",
          r.returncode == 1 and not r.stdout.strip(),
          f"exit={r.returncode}, stdout={len(r.stdout.strip())} chars "
          f"(claim: exit 1, no output)")

    r2 = subprocess.run(["DockQ", str(model), str(native),
                         "--allowed_mismatches", "40", "--mapping", "ABC:ABC"],
                        capture_output=True, text=True)
    tot = None
    per = {}
    for line in r2.stdout.splitlines():
        if "Total DockQ" in line:
            tot = float(line.split("Total DockQ over 3 native interfaces:")[1].split()[0])
    blocks = r2.stdout.split("Native chains:")
    for b in blocks[1:]:
        key = "".join(sorted(b.split("\n")[0].replace(" ", "").split(",")))
        for l in b.splitlines():
            if l.strip().startswith("DockQ:"):
                per[key] = float(l.split(":")[1]); break
    check("A1 DockQ reproduces 0.816 with flags", tot is not None and close(tot, 0.816, 0.001),
          f"measured {tot} (claim 0.816)")
    check("A1 A-C interface = 0.723", "AC" in per and close(per["AC"], 0.723, 0.001),
          f"measured {per.get('AC')} (claim 0.723)")
    check("A1 A-B framework interface = 0.931",
          "AB" in per and close(per["AB"], 0.931, 0.001),
          f"measured {per.get('AB')} (claim 0.931)")


# ---------------------------------------------------------------- A2: retrieval
def audit_retrieval() -> None:
    summ = Path("runs/challenge2_pod/CHECKSUM_SUMMARY.json")
    if not summ.exists():
        check("A2 checksum pass", None, "no summary on disk")
    else:
        d = json.loads(summ.read_text())
        check("A2 checksum pass complete",
              d["complete"] and d["verified"] == d["total"] and not d["mismatched"],
              f"{d['verified']}/{d['total']} verified, {len(d['mismatched'])} mismatched")

    c = [json.loads(l) for l in Path("runs/challenge2_pod/c2/cond_all.jsonl").read_text().splitlines() if l.strip()]
    u = [json.loads(l) for l in Path("runs/challenge2_pod/c2/uncond_all.jsonl").read_text().splitlines() if l.strip()]
    fc = [x["frac_iface_on_epitope"] for x in c]
    fu = [x["frac_iface_on_epitope"] for x in u]
    n1, n2 = len(fc), len(fu)
    sp = math.sqrt(((n1-1)*stdev(fc)**2 + (n2-1)*stdev(fu)**2) / (n1+n2-2))
    d_ = (mean(fc) - mean(fu)) / sp
    se = math.sqrt((n1+n2)/(n1*n2) + d_*d_/(2*(n1+n2-2)))
    lo, hi = d_-1.96*se, d_+1.96*se
    check("A2 conditioned mean 0.7119", close(mean(fc), 0.7119, 0.0002), f"{mean(fc):.4f}")
    check("A2 unconditioned mean 0.5005", close(mean(fu), 0.5005, 0.0002), f"{mean(fu):.4f}")
    check("A2 Cohen d = 1.4747", close(d_, 1.4747, 0.001), f"{d_:.4f}")
    check("A2 CI = [0.733, 2.216]", close(lo, 0.733, 0.002) and close(hi, 2.216, 0.002),
          f"[{lo:.3f}, {hi:.3f}]")


# ---------------------------------------------------------------- B0: the winner
def audit_winner() -> None:
    import copy
    from locksmith.config import Config, load
    from locksmith.select import surrogate
    METRICS = ["ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa"]
    seq = {json.loads(l)["design_id"]: json.loads(l)
           for l in Path("runs/designs_temp/seq_scores.jsonl").read_text().splitlines() if l.strip()}
    per = defaultdict(dict)
    for src in ("runs/designs_temp/fold_scores.jsonl", "runs/designs_reseed7/fold_scores.jsonl"):
        for l in Path(src).read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if "dockq" in r:
                per[r["design_id"]][r["seed"]] = r
    base = load()

    def cfg_with(bv):
        raw = copy.deepcopy(base.raw); raw["conventions"]["band_value"] = bv
        return Config(raw)

    def rank(cfg):
        rows = []
        for did, seeds in per.items():
            if len(seeds) < 2 or did not in seq:
                continue
            vals = []
            for s in sorted(seeds):
                raw = {m: seeds[s].get(m) for m in METRICS}
                raw["netsolp"] = seq[did]["netsolp"]
                raw["cdrh3_identity"] = seq[did]["cdrh3_identity"]
                vals.append(surrogate.compute(raw, 1, cfg).value)
            v = np.array(vals)
            rows.append({"d": did, "mean": v.mean(), "sd": v.std(ddof=1), "n": len(v)})
        rows.sort(key=lambda r: -r["mean"])
        return rows

    old, new = rank(cfg_with("midpoint")), rank(cfg_with("top"))
    check("B0 old winner = mpnn_T0.5_s104_036", old[0]["d"] == "mpnn_T0.5_s104_036", old[0]["d"])
    check("B0 new winner = mpnn_T0.2_s102_032", new[0]["d"] == "mpnn_T0.2_s102_032", new[0]["d"])
    pos = [i for i, r in enumerate(new) if r["d"] == "mpnn_T0.5_s104_036"][0] + 1
    check("B0 shipped design falls to 4th", pos == 4, f"rank {pos}")
    ro = {r["d"]: i for i, r in enumerate(old)}
    rn = {r["d"]: i for i, r in enumerate(new)}
    moved = sum(1 for d in ro if ro[d] != rn[d])
    check("B0 18/20 designs change rank", moved == 18, f"{moved}/{len(ro)}")
    sp_ = spearmanr([ro[d] for d in ro], [rn[d] for d in ro]).statistic
    check("B0 Spearman 0.755", close(sp_, 0.755, 0.002), f"{sp_:.4f}")
    gap = new[0]["mean"] - new[3]["mean"]
    within = math.sqrt(np.mean([r["sd"]**2 for r in new]))
    between = float(np.std([r["mean"] for r in new], ddof=1))
    check("B0 1st-4th gap 0.191", close(gap, 0.191, 0.002), f"{gap:.4f}")
    check("B0 within-design sd 0.226", close(within, 0.226, 0.002), f"{within:.4f}")
    rel = between**2 / (between**2 + within**2)
    check("B0 shortlist reliability ~0.28", close(rel, 0.28, 0.02), f"{rel:.4f}")

    oldrows = rank(cfg_with("midpoint"))
    w_mid = math.sqrt(np.mean([r["sd"]**2 for r in oldrows]))
    check("B0 cross-check: midpoint within-sd reproduces the recorded 0.467",
          close(w_mid, 0.467, 0.002), f"{w_mid:.4f}")


# ---------------------------------------------------------------- B1: patch null
def audit_patch_null() -> None:
    """Does scripts/70 do what its docstring says?"""
    sys.path.insert(0, "scripts")
    import importlib.util
    spec = importlib.util.spec_from_file_location("pn", "scripts/70_epitope_patch_null.py")
    pn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pn)

    check("B1 docstring claims 2000 draws", pn.N_DRAWS == 2000, f"N_DRAWS={pn.N_DRAWS}")
    check("B1 epitope is 26 residues", len(pn.EPITOPE) == 26, f"{len(pn.EPITOPE)}")

    bb = sorted((pn.POD / "bb").glob("bb_*_0.pdb"))
    rng = random.Random(pn.SEED)
    r = pn.analyse(bb[0], rng)
    check("B1 patch size equals epitope size", r["k"] == 26, f"k={r['k']}")
    check("B1 target chain is 113 residues", r["n_target"] == 113, f"{r['n_target']}")

    # Are the "contiguous patches" actually spatially compact relative to random draws?
    chains, order, loop_abs = pn.parse(bb[0])
    tnums = sorted(chains["T"])
    cen = {n: pn.centroid(chains["T"][n]) for n in tnums}

    def spread(group):
        pts = [cen[n] for n in group]
        cx = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
        return math.sqrt(sum(sum((p[i]-cx[i])**2 for i in range(3)) for p in pts) / len(pts))

    def patch_from(seed_res):
        s = cen[seed_res]
        d = sorted(tnums, key=lambda n: sum((cen[n][i]-s[i])**2 for i in range(3)))
        return set(d[:26])

    contig = [spread(patch_from(rng.choice(tnums))) for _ in range(200)]
    unif = [spread(rng.sample(tnums, 26)) for _ in range(200)]
    epi = [tnums[i] for i in pn.EPITOPE if i < len(tnums)]
    check("B1 contiguous patches are compact vs uniform draws",
          mean(contig) < mean(unif) * 0.85,
          f"contiguous RMS spread {mean(contig):.2f} A vs uniform {mean(unif):.2f} A")
    check("B1 the real epitope is itself compact (same family as the null)",
          spread(epi) < mean(unif),
          f"epitope spread {spread(epi):.2f} A vs uniform mean {mean(unif):.2f} A")

    # headline reproduction
    rows = [x for x in (pn.analyse(p, rng) for p in bb) if x]
    real = mean([x["real"] for x in rows])
    cont = mean([mean(x["contig"]) for x in rows])
    unifm = mean([mean(x["unif"]) for x in rows])
    wins = sum(1 for x in rows
               if (sum(1 for y in x["contig"] if y >= x["real"]) + 1) / (len(x["contig"]) + 1) < 0.05)
    check("B1 real epitope pooled 0.712", close(real, 0.712, 0.002), f"{real:.4f}")
    check("B1 contiguous null 0.154", close(cont, 0.154, 0.004), f"{cont:.4f}")
    check("B1 uniform null ~0.231", close(unifm, 0.231, 0.006), f"{unifm:.4f}")
    check("B1 17/18 backbones beat their null", wins == 17, f"{wins}/{len(rows)}")


# ---------------------------------------------------------------- B2/B3/B4: RF2
def audit_rf2() -> None:
    import glob, re
    recs = []
    for f in sorted(glob.glob("runs/challenge2_pod/c2/rf2/*_best.pdb")):
        name = Path(f).name.replace("_best.pdb", "")
        d = {}
        for l in open(f):
            if l.startswith("SCORE "):
                k, v = l[6:].split(":")
                d[k.strip()] = float(v)
            elif l.startswith("ATOM") and d:
                break
        d["name"] = name
        d["bb"] = re.match(r"(bb_\d+_0)_dldesign_(\d+)", name).group(1)
        recs.append(d)
    groups = defaultdict(list)
    for r in recs:
        groups[r["bb"]].append(r)

    def icc(metric):
        gs = [np.array([x[metric] for x in g]) for g in groups.values() if len(g) >= 2]
        n = len(gs); k = float(np.mean([len(g) for g in gs]))
        allv = np.concatenate(gs); gm = allv.mean()
        msb = sum(len(g)*(g.mean()-gm)**2 for g in gs)/(n-1)
        msw = sum(((g-g.mean())**2).sum() for g in gs)/(len(allv)-n)
        return (msb-msw)/(msb+(k-1)*msw)

    check("B2 interaction_pae ICC = -0.113", close(icc("interaction_pae"), -0.113, 0.002),
          f"{icc('interaction_pae'):+.4f}")
    check("B4 pred_lddt ICC = +0.836", close(icc("pred_lddt"), 0.836, 0.002),
          f"{icc('pred_lddt'):+.4f}")
    from scipy.stats import f as fdist
    fc = fdist.ppf(0.95, len(groups)-1, len(groups)*2)
    floor = (fc-1)/(fc+2)
    check("B2 detectable ICC floor = 0.317", close(floor, 0.317, 0.002), f"{floor:.4f}")

    ip = np.array([r["interaction_pae"] for r in recs])
    rm = np.array([r["target_aligned_antibody_rmsd"] for r in recs])
    check("B3 mean rmsd 24.87", close(rm.mean(), 24.87, 0.02), f"{rm.mean():.4f}")
    check("B3 exactly 1 of 30 passes interaction_pae<10", int((ip < 10).sum()) == 1,
          f"{int((ip<10).sum())}/30")
    check("B3 that design sits at 32.86 A", close(float(rm[ip < 10][0]), 32.86, 0.02),
          f"{float(rm[ip<10][0]):.2f}")
    check("B3 median rmsd 28.94", close(float(np.median(rm)), 28.94, 0.02),
          f"{np.median(rm):.4f}")
    s = spearmanr(ip, rm)
    check("B3 Spearman +0.415 (p=0.023)",
          close(s.statistic, 0.415, 0.002) and close(s.pvalue, 0.023, 0.002),
          f"rho={s.statistic:+.4f} p={s.pvalue:.4f}")


# ---------------------------------------------------------------- B6/B7/B8: sequence
def audit_sequence() -> None:
    import gemmi
    from locksmith.numbering import number
    hbc = json.loads(Path("data/refs/handbook_constructs.json").read_text())
    st = gemmi.read_structure("data/refs/prepared/5ggs_ABZ.pdb"); st.setup_entities()
    wt = {ch.name: gemmi.one_letter_code(
        [r.name for r in ch if r.find_atom("CA", "*")]).upper() for ch in st[0]}
    des_h, wt_h, off = hbc["heavy"], wt["A"], hbc["heavy_offset"]
    L = min(len(des_h)-off, len(wt_h))
    diff = [(i+off, wt_h[i], des_h[i+off]) for i in range(L) if wt_h[i] != des_h[i+off]]
    ident = 100*(len(des_h)-len(diff))/len(des_h)
    check("B6 15 substitutions", len(diff) == 15, f"{len(diff)}")
    check("B6 93.5% whole-chain identity", close(ident, 93.5, 0.05), f"{ident:.2f}%")

    nd, nw = number(des_h), number(wt_h)
    h2diff = sum(1 for a, b in zip(nd.cdr2, nw.cdr2) if a != b)
    check("B6 CDR-H2 differs by exactly 1", h2diff == 1, f"{h2diff} ({nw.cdr2} -> {nd.cdr2})")

    def charge(s):
        return sum(c in "RK" for c in s) - sum(c in "DE" for c in s)
    check("B8 design CDR-H3 net charge +2", charge(nd.cdr3) == 2,
          f"{charge(nd.cdr3)} ({nd.cdr3})")
    check("B8 pembrolizumab CDR-H3 net charge 0", charge(nw.cdr3) == 0,
          f"{charge(nw.cdr3)} ({nw.cdr3})")
    arom = lambda s: sum(c in "FWY" for c in s)
    check("B5 design CDR-H3 has 2 aromatics", arom(nd.cdr3) == 2, f"{arom(nd.cdr3)}")
    check("B5 pembrolizumab CDR-H3 has 4 aromatics", arom(nw.cdr3) == 4, f"{arom(nw.cdr3)}")

    from locksmith.metrics import netsolp
    r = netsolp.compute(hbc["heavy"], hbc["light"], construct="fv")["netsolp"]
    vh = float(r.detail.split("H=")[1].split(",")[0])
    vl = float(r.detail.split("L=")[1].rstrip(")"))
    check("B7 shipped design VH = 0.699", close(vh, 0.699, 0.001), f"{vh:.3f}")
    check("B7 shipped design VL = 0.569", close(vl, 0.569, 0.001), f"{vl:.3f}")
    check("B7 VH is BELOW the 0.70 Good edge", vh < 0.70, f"{vh:.3f} < 0.70")


def main() -> int:
    for fn in (audit_dockq, audit_retrieval, audit_winner, audit_patch_null,
               audit_rf2, audit_sequence):
        print(f"\n--- {fn.__name__} ---", flush=True)
        try:
            fn()
        except Exception as e:                       # noqa: BLE001
            check(fn.__name__, False, f"raised {type(e).__name__}: {e}")

    npass = sum(1 for _, ok, _ in RESULTS if ok is True)
    nfail = sum(1 for _, ok, _ in RESULTS if ok is False)
    nunk = sum(1 for _, ok, _ in RESULTS if ok is None)
    print(f"\n{'='*70}\nPASS {npass}   FAIL {nfail}   UNVERIFIABLE {nunk}\n{'='*70}")
    for n, ok, d in RESULTS:
        if ok is not True:
            print(f"  {'FAIL' if ok is False else 'UNVERIFIABLE'}: {n} -- {d}")

    Path("results/audit_of_audit_2026-09-22.json").write_text(json.dumps(
        [{"check": n, "ok": ok, "detail": d} for n, ok, d in RESULTS], indent=1))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
