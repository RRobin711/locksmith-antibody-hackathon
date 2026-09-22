#!/usr/bin/env python3
"""Analyse the 2026-09-20 overnight characterisation run. Three independent parts.

Each part is guarded: a missing or empty run directory prints a line and moves on,
so a truncated night still produces the results it earned. Nothing here re-ranks or
re-selects; M3's named design is fixed.

Writes results/specificity.md, results/ablation.md, results/ensemble_wide.md.
"""
from __future__ import annotations
import itertools, json, sys
from collections import defaultdict
from pathlib import Path

import gemmi
import numpy as np
from scipy import stats

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.types import Provenance, Structure

CDRH3 = range(95, 108)
WINNER = "mpnn_T0.5_s104_036"
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")
V1_PAIR = 0.0628      # A^2, sampling variance of a single-pair spread; see 36_ensemble_power


# ----------------------------------------------------------------- shared helpers
def ca_and_b(pdb: Path, chain="A"):
    st = gemmi.read_structure(str(pdb)); st.remove_hydrogens()
    ch = [c for c in st[0] if c.name == chain][0]
    ca, b = [], []
    for r in ch:
        a = r.find_atom("CA", "*")
        if a:
            ca.append([a.pos.x, a.pos.y, a.pos.z]); b.append(a.b_iso)
    return np.array(ca), np.array(b)


def superpose_on_framework(ref_ca, mob_ca, loop_idx):
    mask = np.array([i not in set(loop_idx) for i in range(len(ref_ca))])
    P, Q = ref_ca[mask], mob_ca[mask]
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Qc.T @ Pc)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return (mob_ca - Q.mean(0)) @ R + P.mean(0)


def pair_dev(ca_a, ca_b, loop):
    n = min(len(ca_a), len(ca_b))
    moved = superpose_on_framework(ca_a[:n], ca_b[:n], loop)
    d = np.sqrt(((moved[loop] - ca_a[loop]) ** 2).sum(1))
    return float(np.sqrt((d ** 2).mean()))


def rows_of(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def score_fold(pdb: Path, pae: Path, label: str, cfg, with_dockq: bool) -> dict:
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae,
                   label=label, predictor="boltz2")
    c = cfg.conventions
    out = {}
    out.update({k: v.value for k, v in prodigy.compute(st).items()})
    out["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                 dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    out["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    out["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    if with_dockq:
        out["dockq"] = dockq.compute(
            st, NATIVE, allowed_mismatches=c["dockq_allowed_mismatches"])["dockq"].value
    return out


def cached_scores(cache: Path, index: list[dict], cfg, with_dockq: bool) -> dict[str, dict]:
    have = {r["label"]: r for r in rows_of(cache)}
    for r in index:
        if not r.get("ok") or r["label"] in have:
            continue
        try:
            sc = score_fold(Path(r["pdb"]), Path(r["pae"]), r["label"], cfg, with_dockq)
        except Exception as e:                                        # noqa: BLE001
            sc = {"error": str(e)[:300]}
        rec = {"label": r["label"], **sc}
        with cache.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        have[r["label"]] = rec
        print(f"  scored {r['label']}: ipsae={sc.get('ipsae')} dg={sc.get('dg')}", flush=True)
    return have


def msd(vals):
    a = np.array(vals, float)
    return a.mean(), (a.std(ddof=1) if len(a) > 1 else 0.0)


# ---------------------------------------------------------------- 1. specificity
def specificity(cfg) -> None:
    idx = rows_of(Path("runs/specificity/index.jsonl"))
    ok = [r for r in idx if r.get("ok")]
    if not ok:
        print("specificity: nothing on disk, skipping"); return
    sc = cached_scores(Path("runs/specificity/scores.jsonl"), ok, cfg, with_dockq=False)

    by = defaultdict(list)
    meta = {}
    for r in ok:
        s = sc.get(r["label"], {})
        if "ipsae" in s:
            by[r["antigen"]].append(s)
            meta[r["antigen"]] = (r["desc"], r.get("antigen_len"))

    L, w = [], lambda s="": L.append(s)
    w("# Specificity controls on the named design")
    w("")
    w(f"`scripts/37_specificity_fold.py` + `42_analyse_tonight.py`. Design **`{WINNER}`**, "
      "unchanged, folded against five antigens at three fresh seeds (31–33) each.")
    w("Pre-registered in [[prereg_2026-09-20_specificity|the specificity pre-registration]] "
      "before any fold ran.")
    w("")
    w("| antigen | role | len | ipSAE | ΔG (kcal/mol) | contacts | iface pLDDT |")
    w("|---|---|---|---|---|---|---|")
    order = ["pd1", "pdl1", "tim3", "ulbp6", "pcrv"]
    stat = {}
    for k in order:
        if k not in by:
            continue
        g = by[k]
        ip = msd([x["ipsae"] for x in g]); dg = msd([x["dg"] for x in g])
        ct = msd([x["contacts"] for x in g]); pl = msd([x["iface_plddt"] for x in g])
        stat[k] = dict(ipsae=ip, dg=dg, contacts=ct, plddt=pl, n=len(g))
        desc, ln = meta[k]
        w(f"| `{k}` | {desc} | {ln} | **{ip[0]:.3f}** ± {ip[1]:.3f} | {dg[0]:+.1f} ± {dg[1]:.1f} "
          f"| {ct[0]:.0f} ± {ct[1]:.0f} | {pl[0]:.1f} ± {pl[1]:.1f} |")
    w("")
    if "pd1" in stat:
        pos = stat["pd1"]["ipsae"][0]
        w("## Verdict against the pre-registered thresholds")
        w("")
        w(f"**H2 — positive control reproduces (ipSAE ≥ 0.80):** PD-1 at fresh seeds scores "
          f"**{pos:.3f}** → {'PASS' if pos >= 0.80 else '**FAIL — the control did not reproduce, so nothing below is interpretable**'}.")
        w("")
        # THE RULE IS PER-SEED, NOT ON THE MEAN. As pre-registered: "any decoy scoring
        # ipSAE >= 0.60 AND dG <= -10 on 2 of 3 seeds". An earlier version of this
        # function tested the arm MEAN, which passes TIM-3 (0.568) while the rule as
        # written fails it (0.624, 0.612 at dG -13.8, -14.4). Quietly reformulating a
        # pre-registered rule into a more convenient one is exactly what pre-registration
        # exists to prevent, so the code implements the rule as written.
        fails = []
        w("| decoy | ipSAE per seed | mean | seeds \u22650.60 **and** \u0394G \u2264\u221210 | gap to PD-1 | >0.20? |")
        w("|---|---|---|---|---|---|")
        for k in order[1:]:
            if k not in stat:
                continue
            g = by[k]
            per = [(x["ipsae"], x["dg"]) for x in g]
            hits = sum(1 for ip, dg in per if ip >= 0.60 and dg <= -10)
            v = stat[k]["ipsae"][0]; gap = pos - v
            if hits >= 2:
                fails.append((k, hits, len(per)))
            w(f"| `{k}` | {', '.join(f'{ip:.3f}' for ip, _ in per)} | {v:.3f} "
              f"| **{hits} / {len(per)}**{' \u26a0' if hits >= 2 else ''} | {gap:+.3f} "
              f"| {'yes' if gap > 0.20 else '**no**'} |")
        w("")
        if fails:
            names = ", ".join(f"`{k}` ({h}/{n} seeds)" for k, h, n in fails)
            w(f"**PRE-DECLARED FAILURE CONDITION TRIGGERED** on {names} \u2014 ipSAE \u2265 0.60 "
              "with \u0394G \u2264 \u221210 on at least 2 of 3 seeds.")
            w("")
            w("Per the pre-registration, **this design does not go into a pitch as a PD-1 "
              "binder without that sentence attached.** Note the arm *mean* would have passed; "
              "the rule was written per-seed before the data existed and is applied as written.")
        else:
            w("**No decoy triggered the pre-declared failure condition.**")
        w("")
        _reference_controls(cfg, w, stat, by)
        w("## What this does and does not license")
        w("")
        w("A decoy scoring high is strong evidence of a problem; a decoy scoring low is **weak** "
          "evidence of its absence, because a predictor that is unreliable at novel placement "
          "scores novel pairings low whether or not they would bind. This predictor's measured "
          "post-cutoff median DockQ is 0.291. So the supported sentence is *no evidence of gross "
          "promiscuity, from a test that could only have detected gross promiscuity* — not "
          "*the design is specific*.")
        w("")
        if rows_of(Path("runs/specificity_ref/index.jsonl")):
            w("The positive-decoy control named as missing in the pre-registration **was run** "
              "(see the reference table above), so that gap is closed.")
        else:
            w("The missing control is a **positive decoy**: an antibody known to bind TIM-3 "
              "(8TBB is exactly that complex, already on disk), folded the same way, to show "
              "the pipeline can produce a high score against that antigen at all. ~3 folds.")
        w("")
    Path("results/specificity.md").write_text("\n".join(L) + "\n")
    print("wrote results/specificity.md")



def _reference_controls(cfg, w, stat, by_panel) -> None:
    """TIM-3 with the ANTIGEN held fixed and the ANTIBODY varied.

    EXPLORATORY: these folds were added after seeing the panel, because the panel as
    designed cannot distinguish "our design is cross-reactive" from "Boltz docks any
    antibody onto TIM-3". Labelled as post-hoc everywhere it is reported.
    """
    idx = [r for r in rows_of(Path("runs/specificity_ref/index.jsonl")) if r.get("ok")]
    w("### Reference controls on TIM-3 \u2014 antigen fixed, antibody varied")
    w("")
    if not idx:
        w("`scripts/46_decoy_reference_fold.py` folds **pembrolizumab** (licensed, specific, "
          "certainly not a TIM-3 binder) and the **8TBB Fab** (a real TIM-3 binder) against the "
          "same antigen under the same protocol. Not yet on disk.")
        w("")
        return
    sc = cached_scores(Path("runs/specificity_ref/scores.jsonl"), idx, cfg, with_dockq=False)
    by, desc = defaultdict(list), {}
    for r in idx:
        x = sc.get(r["label"], {})
        if "ipsae" in x:
            by[r["antibody"]].append(x)
            desc[r["antibody"]] = r["desc"]
    if not by:
        w("(reference folds present but unscored)")
        w("")
        return
    w("**Exploratory, not pre-registered** \u2014 added after seeing the panel. The panel varies "
      "the antigen with the antibody fixed; this varies the antibody with the antigen fixed, "
      "which is the only way to tell a property of the design from a property of the predictor.")
    w("")
    # BUG FIXED 2026-09-20: this used stat["tim3"], the 3-seed panel arm, and iterated
    # only ("pembro","8tbbfab") -- so the five ref_ours_tim3__s54..58 folds made
    # specifically to power this comparison sat in the same scores.jsonl and were never
    # read. The table then printed 0.568 (n=3) while the chat report quoted 0.513 (n=8).
    # Pool the panel arm with the reference arm so the doc cannot disagree with the data.
    panel_ours = [x["ipsae"] for x in by_panel.get("tim3", [])]
    ours_all = [x["ipsae"] for x in by.get("ours", [])] + panel_ours
    ours = float(np.mean(ours_all)) if ours_all else float("nan")
    w("| antibody | role | n | ipSAE per seed | mean | \u0394G mean |")
    w("|---|---|---|---|---|---|")
    if ours_all:
        w(f"| **our design** | `{WINNER}` | **{len(ours_all)}** | "
          f"{', '.join(f'{v:.3f}' for v in sorted(ours_all))} | **{ours:.3f}** | \u2014 |")
    for k in ("pembro", "8tbbfab"):
        if k not in by:
            continue
        ips = [x["ipsae"] for x in by[k]]
        w(f"| `{k}` | {desc[k]} | {len(ips)} | {', '.join(f'{v:.3f}' for v in sorted(ips))} "
          f"| **{np.mean(ips):.3f}** | {np.mean([x['dg'] for x in by[k]]):+.1f} |")
    w("")
    if ours_all and "pembro" in by:
        pv = [x["ipsae"] for x in by["pembro"]]
        d = np.array(ours_all, float); q = np.array(pv, float)
        rng = np.random.default_rng(0)
        bs = [d[rng.integers(0, len(d), len(d))].mean() - q[rng.integers(0, len(q), len(q))].mean()
              for _ in range(10000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        uu = stats.mannwhitneyu(ours_all, pv, alternative="two-sided")
        w(f"Difference (ours \u2212 pembrolizumab): **{np.mean(d)-np.mean(q):+.3f}**, "
          f"bootstrap 95% CI **[{lo:+.3f}, {hi:+.3f}]**, Mann\u2013Whitney p = **{uu.pvalue:.3f}** "
          f"(n={len(d)} vs {len(q)}). Report the interval, not a branch: the point estimate sits "
          f"about one standard error from the threshold that would reverse the reading.")
    w("")
    pem = float(np.mean([x["ipsae"] for x in by["pembro"]])) if "pembro" in by else None
    tb = float(np.mean([x["ipsae"] for x in by["8tbbfab"]])) if "8tbbfab" in by else None
    if pem is None or tb is None:
        w("(one reference missing \u2014 no interpretation)")
        w("")
        return
    if abs(pem - ours) < 0.10 and tb - ours > 0.15:
        w(f"**Reading: 0.62 is the predictor's floor for a non-binder against a same-fold "
          f"antigen, not a property of our design.** Pembrolizumab scores {pem:.3f}, alongside "
          f"our {ours:.3f}, while a real TIM-3 binder reaches {tb:.3f}. The specificity alarm is "
          f"**withdrawn**; what the panel measured is that ipSAE has a high floor here.")
    elif ours - pem > 0.15:
        w(f"**Reading: the design is TIM-3-reactive relative to a specific antibody.** "
          f"Pembrolizumab {pem:.3f} against our {ours:.3f}, real binder {tb:.3f}. The "
          f"pre-declared failure condition stands and travels with the design.")
    elif abs(tb - pem) < 0.10:
        w(f"**Reading: ipSAE cannot discriminate on this antigen at all** \u2014 a real binder "
          f"({tb:.3f}) and a certain non-binder ({pem:.3f}) score alike. No conclusion about our "
          f"design can be drawn from the TIM-3 column; the honest report is that the test "
          f"failed, not that the design passed.")
    else:
        w(f"Pembrolizumab {pem:.3f}, real binder {tb:.3f}, our design {ours:.3f} \u2014 these do "
          f"not fall into any pattern fixed in advance. Report the numbers; do not force an "
          f"interpretation.")
    w("")

# ------------------------------------------------------------------- 2. ablation
def ablation(cfg) -> None:
    idx = rows_of(Path("runs/ablation/index.jsonl"))
    ok = [r for r in idx if r.get("ok")]
    if not ok:
        print("ablation: nothing on disk, skipping"); return
    sc = cached_scores(Path("runs/ablation/scores.jsonl"), ok, cfg, with_dockq=True)

    # parent reference: the winner's 7 selection seeds + fresh seed 23
    par = defaultdict(list)
    for src in ("runs/designs_temp/fold_scores.jsonl", "runs/designs_reseed7/fold_scores.jsonl"):
        for r in rows_of(Path(src)):
            if r.get("design_id") == WINNER and "ipsae" in r:
                for k in ("ipsae", "dg", "contacts", "dockq", "iface_plddt"):
                    if k in r:
                        par[k].append(r[k])

    by = defaultdict(list); kind = {}; removed = {}
    for r in ok:
        s = sc.get(r["label"], {})
        if "ipsae" in s:
            by[r["mutant"]].append(s)
            kind[r["mutant"]] = r["kind"]
            removed[r["mutant"]] = r.get("contacts_removed")

    L, w = [], lambda s="": L.append(s)
    w("# Hotspot ablation on the named design")
    w("")
    w(f"`scripts/38_ablation_fold.py` + `42_analyse_tonight.py`. Alanine substitutions in "
      f"**`{WINNER}`**, two seeds each (41, 42), re-folded from scratch. Pre-registered in "
      "[[prereg_2026-09-20_ablation|the ablation pre-registration]], hotspots chosen from "
      "measured 5 Å heavy-atom contacts **before** folding.")
    w("")
    if par:
        pm = {k: float(np.mean(v)) for k, v in par.items()}
        w(f"Parent over {len(par['ipsae'])} seeds: ipSAE **{pm.get('ipsae',float('nan')):.3f}**, "
          f"ΔG **{pm.get('dg',float('nan')):+.1f}**, contacts **{pm.get('contacts',float('nan')):.0f}**, "
          f"DockQ **{pm.get('dockq',float('nan')):.3f}**.")
        w("")
    else:
        pm = {}
    w("Δ columns are mutant − parent. Seed noise on the parent: DockQ sd 0.018, ipSAE sd ~0.02; "
      "the pre-registered bar for a real change is **3×** the relevant sd.")
    w("")
    w("| mutant | kind | contacts removed | ipSAE (Δ) | ΔG (Δ) | contacts (Δ) | DockQ (Δ) |")
    w("|---|---|---|---|---|---|---|")
    order = sorted(by, key=lambda m: (kind[m] != "hotspot", kind[m] != "triple", m))
    res = {}
    for m in order:
        g = by[m]
        f = {k: msd([x[k] for x in g if k in x]) for k in ("ipsae", "dg", "contacts", "dockq")}
        res[m] = f
        def d(k, fmt):
            # fmt may already carry a sign flag (e.g. "+.1f"); the delta always wants
            # one, so build the delta spec from the bare precision rather than
            # concatenating another "+" onto it.
            if k not in pm:
                return "—"
            bare = fmt.lstrip("+")
            return f"{f[k][0]:{fmt}} ({f[k][0]-pm[k]:+{bare}})"
        w(f"| `{m}` | {kind[m]} | {removed[m]} | {d('ipsae','.3f')} | {d('dg','+.1f')} "
          f"| {d('contacts','.0f')} | {d('dockq','.3f')} |")
    w("")
    hs = [m for m in res if kind[m] == "hotspot"]
    ct = [m for m in res if kind[m] == "control"]
    if hs and ct and pm:
        dh = float(np.mean([res[m]["contacts"][0] - pm["contacts"] for m in hs]))
        dc = float(np.mean([res[m]["contacts"][0] - pm["contacts"] for m in ct]))
        w("## Verdict")
        w("")
        w(f"Mean contact change: hotspots **{dh:+.1f}**, negative controls **{dc:+.1f}**.")
        w("")
        if dh < dc - 5:
            w("**Hotspots degrade and controls hold** — the contact readout is reporting the "
              "interface, not punishing mutation as such. The ablation is informative.")
        elif abs(dh - dc) <= 5:
            w("**Controls degrade about as much as hotspots.** The readout is mutation-sensitive "
              "rather than interface-sensitive, so per the pre-registration this ablation is "
              "**uninformative** and must be reported as such rather than spun.")
        else:
            w("**Controls degrade more than hotspots** — an inverted result; treat the whole "
              "ablation as unreliable and investigate before quoting any of it.")
        w("")
        if "ipsae" in pm:
            ri = float(np.mean([abs(res[m]["ipsae"][0] - pm["ipsae"]) / max(abs(pm["ipsae"]), 1e-9)
                                for m in hs]))
            rc = float(np.mean([abs(res[m]["contacts"][0] - pm["contacts"]) / max(abs(pm["contacts"]), 1e-9)
                                for m in hs]))
            w(f"**H3 — ipSAE blunter than the physical metrics?** Mean relative change on "
              f"hotspots: ipSAE **{ri*100:.1f}%**, contacts **{rc*100:.1f}%**. "
              + ("Consistent with ipSAE behaving as a liveness test rather than a ranking "
                 "metric — a fourth instance." if ri < rc else
                 "ipSAE moved at least as much as the physical metrics here, which cuts against "
                 "the liveness-test reading; note it."))
            w("")
    w("## Limit that must travel with this table")
    w("")
    w("Boltz **re-predicts** every mutant from scratch, so a mutant is not the parent minus a "
      "side chain — the model may re-dock. This is the right question for a scored pipeline "
      "(*does the pipeline's verdict survive losing the hotspots*) but it is **not** an "
      "in-silico ΔΔG and must never be called one.")
    w("")
    Path("results/ablation.md").write_text("\n".join(L) + "\n")
    print("wrote results/ablation.md")


# ------------------------------------------------------------- 3. ensemble widening
def ensemble(cfg) -> None:
    ens = [r for r in rows_of(Path("runs/designs_ens/index.jsonl")) if r.get("ok")]
    if not ens:
        print("ensemble: nothing on disk, skipping"); return
    base = {r["design_id"]: r for r in rows_of(Path("runs/designs_temp/index.jsonl"))
            if r.get("ok")}
    pool = {d["design_id"]: d for d in json.loads(Path("designs/wide_temp/designs.json").read_text())}
    seed1 = {r["design_id"]: r for r in rows_of(Path("runs/designs_temp/fold_scores.jsonl"))
             if "ipsae" in r}

    paths = defaultdict(dict)
    for r in ens:
        paths[r["design_id"]][r["seed"]] = Path(r["pdb"])
    for d in paths:
        if d in base:
            paths[d][1] = Path(base[d]["pdb"])

    recs = []
    for d, ps in sorted(paths.items()):
        seeds = sorted(ps)
        if len(seeds) < 2 or d not in seed1:
            continue
        cas, bs = {}, {}
        try:
            for s in seeds:
                cas[s], bs[s] = ca_and_b(ps[s])
        except Exception as e:                                        # noqa: BLE001
            print(f"  skip {d}: {str(e)[:100]}"); continue
        loop = [i for i in CDRH3 if i < len(cas[seeds[0]])]
        pairs = [pair_dev(cas[a], cas[b], loop) for a, b in itertools.combinations(seeds, 2)]
        spread = float(np.sqrt(np.mean(np.square(pairs))))
        lp = [float(np.mean([bs[s][i] for i in loop])) for s in seeds]
        recs.append(dict(design_id=d, k=len(seeds), spread=spread,
                         max_dev=float(max(pairs)),
                         loop_plddt=float(np.mean(lp)), loop_plddt_sd=float(np.std(lp, ddof=1)) if len(lp) > 1 else 0.0,
                         iface_plddt=seed1[d]["iface_plddt"], dockq=seed1[d]["dockq"],
                         ipsae=seed1[d]["ipsae"],
                         arom=pool[d]["arom_count"], temp=float(pool[d]["arm_temperature"]),
                         identity=pool[d]["cdrh3_identity"]))
    if len(recs) < 10:
        print(f"ensemble: only {len(recs)} designs usable, skipping analysis"); return

    Path("runs/designs_ens/ensemble_table.json").write_text(json.dumps(recs, indent=1))
    n = len(recs)
    sp = np.array([r["spread"] for r in recs])
    var_obs = float(np.var(sp, ddof=1))
    k2 = [r for r in recs if r["k"] == 2]
    var_between = max(var_obs - V1_PAIR, 0.0) if len(k2) > n * 0.5 else var_obs
    rel = var_between / (var_between + V1_PAIR) if var_between > 0 else 0.0
    att = float(np.sqrt(rel))

    def rho(xk, yk="spread", sub=None):
        g = sub if sub is not None else recs
        x = np.array([r[xk] for r in g]); y = np.array([r[yk] for r in g])
        r = stats.spearmanr(x, y)
        bs = []
        rng = np.random.default_rng(0)
        for _ in range(10000):
            i = rng.integers(0, len(g), len(g))
            if len(set(x[i])) > 2 and len(set(y[i])) > 2:
                bs.append(stats.spearmanr(x[i], y[i]).statistic)
        lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (np.nan, np.nan)
        return r.statistic, r.pvalue, lo, hi

    L, w = [], lambda s="": L.append(s)
    w("# The CDR-H3 ensemble, widened from 40 designs to the pool")
    w("")
    w("`scripts/39_ensemble_wide_fold.py` + `42_analyse_tonight.py`. Pre-registered in "
      "[[prereg_2026-09-20_ensemble_wide|the ensemble pre-registration]]; sizing argued in "
      "[[ensemble_power|the seeds-versus-designs power analysis]], which is why this is a wide "
      "shallow design rather than the deep narrow one originally proposed.")
    w("")
    w(f"**n = {n} designs**, {sum(1 for r in recs if r['k']==2)} at k=2 and "
      f"{sum(1 for r in recs if r['k']>=3)} at k≥3, spanning "
      f"{len(set(r['temp'] for r in recs))} temperature arms "
      f"({dict(sorted(__import__('collections').Counter(r['temp'] for r in recs).items()))}).")
    w("")
    w("Estimator: RMS Cα deviation over CDR-H3 (heavy 96–108) across all C(k,2) seed pairs, "
      "each superposed on the **framework**. Reference-free — **not comparable** to the "
      "0.33–1.45 Å quoted on 2026-09-18, which measured every seed against `seed[0]`.")
    w("")
    w("## 1. How much does CDR-H3 actually move, and is the variation real?")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| spread, range | {sp.min():.2f} – {sp.max():.2f} Å ({sp.max()/max(sp.min(),1e-9):.1f}×) |")
    w(f"| spread, median | {np.median(sp):.2f} Å |")
    w(f"| largest single pairwise deviation | {max(r['max_dev'] for r in recs):.2f} Å |")
    w(f"| observed variance of the spread estimate | {var_obs:.5f} Å² |")
    w(f"| sampling variance of one pair (V1, from the 20×7 shortlist) | {V1_PAIR:.5f} Å² |")
    w(f"| **between-design variance, identified** | **{var_between:.5f} Å²** |")
    w(f"| **reliability of a k=2 spread** | **{rel:.3f}** |")
    w(f"| attenuation √r applied to every ρ below | **{att:.3f}** |")
    w("")
    w("**H5 — is the between-design variation carried by one outlier?** On the 20-design "
      "shortlist, dropping one design at 1.77 Å moved k=2 reliability from 0.591 to 0.265. "
      "Here, over the full pool:")
    hi = sorted(recs, key=lambda r: -r["spread"])[:3]
    w("")
    for r in hi:
        w(f"- `{r['design_id']}` — {r['spread']:.2f} Å (T={r['temp']}, aromatics {r['arom']}, "
          f"loop pLDDT {r['loop_plddt']:.1f})")
    sp_no = np.sort(sp)[:-3]
    var_no = max(float(np.var(sp_no, ddof=1)) - V1_PAIR, 0.0)
    w("")
    w(f"Dropping the top 3, between-design variance goes {var_between:.5f} → **{var_no:.5f} Å²** "
      f"and reliability {rel:.3f} → **{var_no/(var_no+V1_PAIR):.3f}**. "
      + ("The variation survives, so it is a distribution, not an artefact of a few designs."
         if var_no / (var_no + V1_PAIR) > 0.4 else
         "**The variation does NOT survive** — it is carried by a handful of designs, and the "
         "honest reading is that CDR-H3 heterogeneity does not vary meaningfully across "
         "fixed-backbone redesigns of this one scaffold."))
    w("")
    w("## 2. Does confidence see the heterogeneity?")
    w("")
    w("Both pLDDT columns are read from the **seed-1** fold — the single structure a user would "
      "actually have — so this asks the practical question: does the confidence you get from one "
      "fold predict how much the loop moves between folds?")
    w("")
    w("| predictor of spread | ρ observed | 95% CI (bootstrap) | p | ρ disattenuated |")
    w("|---|---|---|---|---|")
    for key, lab in [("loop_plddt", "**H1** mean loop pLDDT (seed 1)"),
                     ("iface_plddt", "**H2** interface pLDDT (seed 1)"),
                     ("arom", "**H4** CDR-H3 aromatic count"),
                     ("loop_plddt_sd", "loop pLDDT sd across seeds"),
                     ("ipsae", "ipSAE (seed 1)"), ("dockq", "DockQ (seed 1)")]:
        r, p, lo, hlim = rho(key)
        w(f"| {lab} | {r:+.3f} | [{lo:+.3f}, {hlim:+.3f}] | {p:.2g} | {r/att if att>0 else float('nan'):+.3f} |")
    w("")
    z = 2.80 / np.sqrt(n - 3)
    w(f"**A null here is a bound, not an absence.** At n={n} and attenuation {att:.3f}, the "
      f"smallest true effect detectable at 80% power (α=0.05) is ρ_true ≈ "
      f"**{np.tanh(z)/max(att,1e-9):.3f}**. Any ρ reported as null means *no effect larger than "
      f"that*, and nothing stronger.")
    w("")
    w("## 3. Does it hold across sampling temperature? (H3)")
    w("")
    w("| arm | n | ρ(iface pLDDT, spread) | ρ(loop pLDDT, spread) | ρ(aromatics, spread) | median spread |")
    w("|---|---|---|---|---|---|")
    for t in sorted(set(r["temp"] for r in recs)):
        g = [r for r in recs if r["temp"] == t]
        if len(g) < 8:
            continue
        a = stats.spearmanr([r["iface_plddt"] for r in g], [r["spread"] for r in g]).statistic
        b = stats.spearmanr([r["loop_plddt"] for r in g], [r["spread"] for r in g]).statistic
        c = stats.spearmanr([r["arom"] for r in g], [r["spread"] for r in g]).statistic
        w(f"| T={t} | {len(g)} | {a:+.3f} | {b:+.3f} | {c:+.3f} | "
          f"{np.median([r['spread'] for r in g]):.2f} Å |")
    w("")
    w("## 4. Is interface pLDDT just reading aromatics? (H4)")
    w("")
    try:
        import pandas as pd
        df = pd.DataFrame(recs)
        def partial(x, y, z_):
            rxy = stats.spearmanr(df[x], df[y]).statistic
            rxz = stats.spearmanr(df[x], df[z_]).statistic
            ryz = stats.spearmanr(df[y], df[z_]).statistic
            den = np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
            r = (rxy - rxz * ryz) / den if den > 0 else np.nan
            t = r * np.sqrt((n - 3) / max(1 - r ** 2, 1e-12))
            return r, 2 * (1 - stats.t.cdf(abs(t), n - 3))
        r1, p1 = partial("iface_plddt", "spread", "arom")
        r2, p2 = partial("arom", "spread", "iface_plddt")
        w(f"- interface pLDDT → spread, controlling for aromatic count: **{r1:+.3f}** (p={p1:.2g})")
        w(f"- aromatic count → spread, controlling for interface pLDDT: **{r2:+.3f}** (p={p2:.2g})")
        w("")
        w("The 2026-09-18 pattern was that a *free sequence feature* explained away a "
          "*three-fold measurement*. Whichever survives here is the one worth carrying.")
    except Exception as e:                                            # noqa: BLE001
        w(f"(partial correlations unavailable: {str(e)[:120]})")
    w("")
    w("## 5. The claim boundary")
    w("")
    w("Spread across diffusion seeds measures **how well determined the prediction is** — a "
      "property of Boltz, not of the molecule. There is no experimental structure of any design "
      "and no binding data. The supported sentence is *the predictor does not place this loop "
      "consistently*; *this loop is flexible* is not supported by anything here.")
    w("")
    Path("results/ensemble_wide.md").write_text("\n".join(L) + "\n")
    print("wrote results/ensemble_wide.md")


def main() -> int:
    cfg = load()
    for name, fn in (("specificity", specificity), ("ablation", ablation),
                     ("ensemble", ensemble)):
        print(f"\n=== {name} ===", flush=True)
        try:
            fn(cfg)
        except Exception as e:                                        # noqa: BLE001
            import traceback
            print(f"{name} FAILED: {e}", file=sys.stderr)
            traceback.print_exc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
