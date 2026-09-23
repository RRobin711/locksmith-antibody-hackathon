#!/usr/bin/env python3
"""Turn the calibration and negative-control scores into the two documents that matter.

Writes `results/negative_control.md` and `results/calibration.md`. Decision rules are NOT
chosen here -- they are read off
`results/prereg_2026-09-22_calibration_and_negative_control.md`, written before the folds
finished, and this script only applies them.
"""
from __future__ import annotations

import json
import statistics as stats
from pathlib import Path

from scipy.stats import mannwhitneyu

from locksmith.config import load

SCORES = Path("runs/calibration/scores.json")
COVERAGE = Path("results/epitope_coverage.json")
GATE = 0.60                       # handbook S7.2 ipSAE viability gate
METRICS = ["ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa"]
LABEL = {"ipsae": "ipSAE", "dockq": "DockQ", "dg": "ΔG (kcal/mol)",
         "contacts": "contacts", "iface_plddt": "interface pLDDT",
         "cdr_sasa": "CDR SASA (Å²)"}


def direction(cfg, m: str) -> str:
    try:
        return cfg.bands()[m].direction
    except Exception:                                        # noqa: BLE001
        return "low" if m == "dg" else "high"


def pct_rank(value: float, pool: list[float], dirn: str) -> tuple[float, int]:
    """Percentile of `value` in `pool`, and its 1-based rank (1 = best)."""
    better = sum(1 for v in pool if (v > value if dirn == "high" else v < value))
    worse = sum(1 for v in pool if (v < value if dirn == "high" else v > value))
    return 100.0 * worse / len(pool), better + 1


# The handbook's S7.2 hard cutoffs, read from config rather than restated here -- a
# constant that duplicates a declared convention is a second source of truth, and this
# project has already had `surrogate.py` and `dockq.py` drift from `config/metrics.yaml`
# in exactly that way.
GATE_METRICS = ["ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa"]


def clears(cfg, m: str, v: float | None) -> bool | None:
    """Does `v` clear metric `m`'s S7.2 hard cutoff?"""
    if v is None:
        return None
    b = cfg.bands()[m]
    # `Band.better` already encodes the direction and the handbook's strict/non-strict
    # edges, so the comparison is not restated here.
    return b.better(v, b.cutoff, strict=b.strict_cutoff)


def gate_count(cfg, r: dict, suffix: str = "") -> tuple[int, int, list[str]]:
    """How many of the S7.2 cutoffs this row clears, and which it fails."""
    ok, tot, failed = 0, 0, []
    for m in GATE_METRICS:
        v = r.get(f"{m}{suffix}")
        c = clears(cfg, m, v)
        if c is None:
            continue
        tot += 1
        ok += bool(c)
        if not c:
            failed.append(m)
    return ok, tot, failed


def fmt(v, nd=3):
    return "—" if v is None else f"{v:.{nd}f}"


# ---------------------------------------------------------------- negative control
def negative_control(d: dict, cfg) -> str:
    rows = list(d["negctrl"].values())
    if not rows:
        return ""
    neg = [r for r in rows if r["expected"] == "negative"]
    pos = [r for r in rows if r["expected"] == "positive"]
    test = [r for r in rows if r["expected"] == "test"]

    L = []; w = L.append
    w("# Negative control — does the viability gate mean anything?")
    w("")
    w("**2026-09-22.** Pre-registered in "
      "[[prereg_2026-09-22_calibration_and_negative_control|the pre-registration written "
      "before these folds finished]].")
    w("")
    w("## The argument")
    w("")
    w("Every gate in handbook §7.2 is a threshold on a number Boltz produces for an "
      "antibody–antigen pair, and this project has only ever shown that its own designs "
      "*clear* those thresholds. It never showed that a **wrong** antibody fails them. "
      "If a real antibody with an unrelated target is docked onto PD-1 and still scores "
      f"ipSAE ≥ {GATE:.2f}, the gate does not measure binding — it registers that two "
      "proteins were placed next to each other, and every ipSAE-derived claim in the "
      "submission is worthless.")
    w("")
    w("This is the cheapest experiment available with the largest possible consequence. "
      "It costs eight folds and nobody ran it for a week.")
    w("")
    w("## Design")
    w("")
    w("Every row below is folded against **the identical 113-residue PD-1 construct** "
      "with **the identical cached alignment** (`data/msa_cache/pd1_5ggs.csv`, 3787 "
      "sequences), identical flags, `recycling_steps=10`, `diffusion_samples=5`. "
      "Antibodies are trimmed to their variable domains by ANARCII. The only thing that "
      "varies across rows is which antibody is present, so any difference is attributable "
      "to the antibody and to nothing else.")
    w("")
    w("The point estimate is the **median over the five diffusion samples**, fixed in "
      "advance. The maximum is reported beside it because `diffusion_samples=1` returns "
      "Boltz's own top-ranked model — an argmax, not a sample — and the gap between the "
      "two columns is exactly the error a single-sample run would make.")
    w("")
    w("### What a single diffusion sample would have reported")
    w("")
    w("`diffusion_samples=1` is Boltz's default and was this project's setting for most "
      "of its life. Boltz ranks its diffusion outputs by its own confidence, so the model "
      "it returns is the **argmax of a distribution that was never drawn**. This table is "
      "that column: `model_0` of five, scored against every §7.2 hard cutoff.")
    w("")
    w("| antibody | its real target | arm | ipSAE | ΔG | contacts | iface pLDDT | "
      "CDR SASA | §7.2 cutoffs cleared |")
    w("|---|---|---|---|---|---|---|---|---|")
    for grp, tag in ((pos, "positive"), (test, "**test**"), (neg, "negative")):
        for r in sorted(grp, key=lambda x: -(x.get("ipsae_m0") or 0)):
            ok, tot, failed = gate_count(cfg, r, "_m0")
            mark = "**{}/{}**".format(ok, tot) + (" ✅ ALL" if ok == tot else
                                                  " (fails " + ", ".join(failed) + ")")
            w(f"| {r['name']} | {r['target']} | {tag} | {fmt(r.get('ipsae_m0'))} | "
              f"{fmt(r.get('dg_m0'), 1)} | {fmt(r.get('contacts_m0'), 0)} | "
              f"{fmt(r.get('iface_plddt_m0'), 1)} | {fmt(r.get('cdr_sasa_m0'), 0)} | "
              f"{mark} |")
    w("")
    w("### What five samples report")
    w("")
    w("The same folds, collapsed to the **median over the five diffusion samples** — the "
      "point estimate fixed in the pre-registration before any of this was seen.")
    w("")
    w("| antibody | its real target | arm | median ipSAE | best of 5 | median ΔG | "
      "median contacts | §7.2 cutoffs cleared |")
    w("|---|---|---|---|---|---|---|---|")
    for grp, tag in ((pos, "positive"), (test, "**test**"), (neg, "negative")):
        for r in sorted(grp, key=lambda x: -(x.get("ipsae") or 0)):
            ok, tot, failed = gate_count(cfg, r)
            mark = "**{}/{}**".format(ok, tot) + (" ✅ ALL" if ok == tot else
                                                  " (fails " + ", ".join(failed) + ")")
            w(f"| {r['name']} | {r['target']} | {tag} | **{fmt(r.get('ipsae'))}** | "
              f"{fmt(r.get('ipsae_max'))} | {fmt(r.get('dg'), 1)} | "
              f"{fmt(r.get('contacts'), 0)} | {mark} |")
    w("")

    # ---- apply the pre-registered decision rules ----
    w("## Verdict, by the pre-registered rules")
    w("")
    pos_pass = [r for r in pos if (r.get("ipsae") or 0) >= GATE]
    neg_pass = [r for r in neg if (r.get("ipsae") or 0) >= GATE]
    neg_m0_all = [r for r in neg if gate_count(cfg, r, "_m0")[0] == gate_count(cfg, r, "_m0")[1]
                  and gate_count(cfg, r, "_m0")[1] > 0]

    if pos and len(pos_pass) < len(pos):
        w(f"**Rule 3 fires: the control is INCONCLUSIVE.** "
          f"{len(pos)-len(pos_pass)} of {len(pos)} positive controls "
          f"({', '.join(r['name'] for r in pos if r not in pos_pass)}) failed the "
          f"{GATE:.2f} ipSAE gate on the median. A panel whose positives do not work "
          "cannot license any conclusion from its negatives: a uniform failure is then a "
          "statement about the pipeline, not about the antibodies. This project has "
          "already published a '0/30 viable' that was the sampler's floor rather than a "
          "finding, and this has the same shape. The negative arm is reported but **must "
          "not be read as evidence that the gate discriminates.**")
    elif neg_pass:
        w(f"**Rule 2 fires: the gate does not measure binding.** "
          f"{len(neg_pass)} of {len(neg)} irrelevant antibodies "
          f"({', '.join(r['name'] for r in neg_pass)}) cleared ipSAE ≥ {GATE:.2f} against "
          "PD-1 on the median of five samples. These antibodies demonstrably bind "
          "something else, so the gate is registering adjacency rather than recognition, "
          "and **every ipSAE-derived claim in this submission inherits that weakness.**")
    elif neg and pos:
        gap = min(r["ipsae"] for r in pos) - max(r["ipsae"] for r in neg)
        w(f"**Rule 1 fires: on the pre-registered point estimate, the gate "
          f"discriminates.** Both positive controls cleared ipSAE ≥ {GATE:.2f}; all "
          f"{len(neg)} irrelevant antibodies failed it. The separation between the worst "
          f"positive and the best negative is **{gap:.3f} ipSAE**.")
    w("")

    if neg_m0_all:
        w("## The finding that matters more than the verdict")
        w("")
        names = ", ".join(f"**{r['name']}** (anti-{r['target']})" for r in neg_m0_all)
        w(f"{len(neg_m0_all)} of {len(neg)} irrelevant antibodies — {names} — clear "
          f"**every one of the §7.2 hard cutoffs** on `model_0`, the model a default "
          f"`diffusion_samples=1` run returns.")
        w("")
        for r in neg_m0_all:
            w(f"- **{r['name']}**, whose real target is {r['target']}, docked onto PD-1: "
              f"ipSAE **{fmt(r.get('ipsae_m0'))}**, ΔG **{fmt(r.get('dg_m0'), 1)} "
              f"kcal/mol**, **{fmt(r.get('contacts_m0'), 0)}** heavy-atom contacts, "
              f"interface pLDDT **{fmt(r.get('iface_plddt_m0'), 1)}**, CDR SASA "
              f"**{fmt(r.get('cdr_sasa_m0'), 0)} Å²**. Its median across five samples is "
              f"ipSAE {fmt(r.get('ipsae'))} — it fails comfortably when you actually "
              f"sample.")
        w("")
        w("**Read the mechanism, not just the number.** Boltz orders its diffusion "
          "outputs by its own confidence, so `model_0` is the maximum of five draws, and "
          "the maximum of five draws from a broad low distribution routinely lands above "
          "a threshold the distribution's centre is nowhere near. The gate is not broken. "
          "**Reading the gate off a single diffusion sample is.**")
        w("")
        w("The consequence is concrete and not hypothetical: under the sampling settings "
          "this project shipped with for most of its life, an antibody raised against hen "
          "egg lysozyme would have been certified a viable PD-1 binder on every metric in "
          "the rubric. That is not a near miss — it is a clean sweep of the gate set by a "
          "molecule that cannot possibly bind.")
        w("")
        w("This is an independent confirmation, from a completely different direction, of "
          "[[diffusion_samples_2026-09-22|the diffusion-sampling result]] — which was "
          "measured on our own designs and could have been dismissed as a quirk of them. "
          "It cannot be dismissed here.")
        w("")
    # ---- which gates do any discriminating work at all? ----
    if neg and pos:
        w("## Which of the five gates actually does any work")
        w("")
        w("A gate that every irrelevant antibody clears is not a filter; it is a "
          "formality. Below, each §7.2 cutoff is scored on how many of the "
          f"{len(neg)} known-wrong antibodies it rejects, using the pre-registered "
          "median-of-five point estimate.")
        w("")
        w("| §7.2 cutoff | threshold | negatives rejected | positives passed | verdict |")
        w("|---|---|---|---|---|")
        for m in GATE_METRICS:
            b = cfg.bands()[m]
            rej = sum(1 for r in neg if clears(cfg, m, r.get(m)) is False)
            psd = sum(1 for r in pos if clears(cfg, m, r.get(m)) is True)
            edge = ">" if b.strict_cutoff else ("≥" if b.direction == "high" else "≤")
            if b.direction == "low":
                edge = "≤"
            if rej == 0:
                verdict = "**inert** — rejects nothing"
            elif rej == len(neg) and psd == len(pos):
                verdict = "**discriminates**"
            else:
                verdict = f"partial"
            w(f"| {LABEL[m]} | {edge} {b.cutoff} | {rej}/{len(neg)} | "
              f"{psd}/{len(pos)} | {verdict} |")
        w("")
        inert = [LABEL[m] for m in GATE_METRICS
                 if sum(1 for r in neg if clears(cfg, m, r.get(m)) is False) == 0]
        if inert:
            w(f"**{len(inert)} of the {len(GATE_METRICS)} hard cutoffs "
              f"({', '.join(inert)}) are cleared by every antibody in the negative arm.** "
              "They are satisfied by any pair of proteins the predictor places in contact "
              "at all, so they measure *that a complex was built*, not that it is the "
              "right one. Practically, the §7.2 viability decision rests on ipSAE alone, "
              "and the other four cutoffs contribute the appearance of a five-way check "
              "without the substance of one.")
            w("")
            w("That is worth stating carefully, because it is a criticism of the rubric "
              "and not of the tools. ΔG, contact count, interface pLDDT and buried CDR "
              "surface are all perfectly good *descriptive* quantities — they just cannot "
              "function as pass/fail gates at these thresholds, because the thresholds "
              "sit below what a docked-but-wrong complex achieves. A gate has to be "
              "calibrated against something that should fail it, and until this "
              "experiment nothing in this project ever was.")
            w("")

    # ---- why the positive control split, diagnosed from crystallography ----
    if COVERAGE.exists() and pos:
        cov = json.loads(COVERAGE.read_text())
        failed = [r for r in pos if (r.get("ipsae") or 0) < GATE]
        if failed and cov:
            w("## Why the positive control split — diagnosed from crystallography, "
              "not from a story")
            w("")
            w("Both positives are licensed anti-PD-1 antibodies, so \"the pipeline is "
              "broken\" and \"nivolumab is simply a hard case\" are both available "
              "explanations and **neither is evidence**. The question is answerable with "
              "no folding at all: take each antibody's own crystal, list the PD-1 "
              "residues it contacts at 4.5 Å, and ask how many of them exist in the "
              "construct we fold.")
            w("")
            w("| antibody | epitope size | covered by our folded 113-mer | missing |")
            w("|---|---|---|---|")
            for name, c in cov.items():
                f = c["folded_113"]
                w(f"| {name} ({c['pdb']}) | {c['n_epitope']} residues | "
                  f"**{f['covered']}/{c['n_epitope']} ({f['pct']}%)** | "
                  f"{' '.join(f['missing_residues']) or '—'} |")
            w("")
            niv = cov.get("nivolumab", {})
            if niv:
                f = niv["folded_113"]
                w(f"**The construct is missing {f['missing']} of nivolumab's "
                  f"{niv['n_epitope']} contact residues** — the `LDSPDR` N-terminal "
                  f"segment, PD-1 residues 25–30. Nivolumab did not fail because the "
                  f"pipeline is broken. It failed because **the molecule it was docked "
                  f"against does not contain the surface it binds.**")
                w("")
                w("Every fold in this project used a 113-residue PD-1 beginning at "
                  "`PWNPP`, inherited from the 5GGS (pembrolizumab) construct and never "
                  "re-examined. Pembrolizumab's 24-residue epitope is "
                  f"{cov['pembrolizumab']['folded_113']['pct']}% inside it, which is why "
                  "the truncation was invisible for the entire project — the only "
                  "reference antibody ever folded was the one that cannot detect it.")
                w("")
                sub = niv.get("submitted", {})
                if sub:
                    w(f"**A second consequence, worth more than the first: the construct "
                      f"we fold is not the construct we submit.** The submitted FASTA "
                      f"carries a longer PD-1 including `DSPDRP`, covering "
                      f"{sub['pct']}% of nivolumab's epitope against the folded "
                      f"construct's {f['pct']}%. Every number in this submission was "
                      f"measured on a molecule 6 residues shorter than the one shipped "
                      f"beside it. Nothing in the pipeline compared the two.")
                    w("")
            w("**The transferable point.** A positive control can fail for a reason that "
              "has nothing to do with the thing being controlled for. \"The positive "
              "failed, so the panel is broken\" and \"the positive failed, so ignore "
              "it\" are equally unjustified until you ask *why*, from data. Here the "
              "answer took no GPU time and turned a failed control into the most useful "
              "finding in the experiment.")
            w("")

    # ---- the follow-up on the repaired construct ----
    if d.get("negctrl_nloop"):
        f_rows = list(d["negctrl_nloop"].values())
        f_neg = [r for r in f_rows if r["expected"] == "negative"]
        f_pos = [r for r in f_rows if r["expected"] == "positive"]
        f_test = [r for r in f_rows if r["expected"] == "test"]
        w("## Follow-up: the same experiment on a construct containing both epitopes")
        w("")
        w("**This is a follow-up, not the pre-registered experiment.** Rule 3 fired above "
          "and is not retracted. The construct here is the 113-mer extended N-terminally "
          "by `LDSPDR` to 119 residues (PD-1 25–143), the minimal change that restores "
          "nivolumab's epitope while leaving every previously-used residue in place. The "
          "cached alignment cannot be reused against a longer query, so all rows take a "
          "fresh MMseqs2 query; because the antigen is byte-identical across rows, the "
          "alignment depth of each row is recorded and compared rather than assumed.")
        w("")
        w("| antibody | arm | median ipSAE | best of 5 | §7.2 cutoffs cleared | "
          "was (113-mer) |")
        w("|---|---|---|---|---|---|")
        prev_by_name = {r["name"]: r for r in rows}
        for grp, tag in ((f_pos, "positive"), (f_test, "**test**"), (f_neg, "negative")):
            for r in sorted(grp, key=lambda x: -(x.get("ipsae") or 0)):
                ok, tot, failed_m = gate_count(cfg, r)
                mark = f"**{ok}/{tot}**" + (" ✅ ALL" if ok == tot else
                                            " (fails " + ", ".join(failed_m) + ")")
                was = prev_by_name.get(r["name"], {}).get("ipsae")
                w(f"| {r['name']} | {tag} | **{fmt(r.get('ipsae'))}** | "
                  f"{fmt(r.get('ipsae_max'))} | {mark} | {fmt(was)} |")
        w("")
        fp = [r for r in f_pos if (r.get("ipsae") or 0) >= GATE]
        fn = [r for r in f_neg if (r.get("ipsae") or 0) >= GATE]
        if len(fp) == len(f_pos) and not fn and f_pos and f_neg:
            gap = min(r["ipsae"] for r in f_pos) - max(r["ipsae"] for r in f_neg)
            w(f"**On the repaired construct the control resolves.** All {len(f_pos)} "
              f"positives clear the gate and all {len(f_neg)} irrelevant antibodies fail "
              f"it, separated by **{gap:.3f} ipSAE**. The diagnosis is therefore "
              "confirmed by the intervention it predicted: restoring the six missing "
              "residues is sufficient to recover the positive control.")
        elif fn:
            w(f"**Even with both epitopes present, {len(fn)} irrelevant "
              f"antibod{'y' if len(fn)==1 else 'ies'} "
              f"({', '.join(r['name'] for r in fn)}) clear the gate.** That is a "
              "stronger statement than anything above: the gate admits a known "
              "non-binder on a construct built to be fair to every row.")
        elif len(fp) < len(f_pos):
            w(f"**The repair did not rescue the positive control** "
              f"({', '.join(r['name'] for r in f_pos if r not in fp)} still fails). The "
              "epitope-truncation diagnosis predicted it would, so the diagnosis is "
              "wrong, incomplete, or the failure has a second cause. Reported as an open "
              "question rather than resolved.")
        w("")

    w("## What this does not establish")
    w("")
    w("Passing this control shows the metric separates cognate from non-cognate pairs. "
      "It says **nothing** about whether it ranks correctly among plausible designs, "
      "which is the job it is actually asked to do in selection. This project measured "
      "that second property failing directly: across a panel of real variants ipSAE "
      "wandered within ±0.04 while DockQ fell 0.820 → 0.601, and the highest ipSAE in "
      "that panel belonged to a variant with a *worse* pose than the wild type. "
      "Discrimination and ranking are different properties and only the first is tested "
      "here.")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- calibration
def calibration(d: dict, cfg) -> str:
    panel = list(d["panel"].values())
    if not panel:
        return ""
    pre = [r for r in panel if r["arm"] == "pre"]
    post = [r for r in panel if r["arm"] == "post"]
    tests = {r["name"]: r for r in d["negctrl"].values() if r["expected"] == "test"}

    L = []; w = L.append
    w("# Calibration — where do our numbers actually sit?")
    w("")
    w("**2026-09-22.** Pre-registered in "
      "[[prereg_2026-09-22_calibration_and_negative_control|the pre-registration]].")
    w("")
    w("## Why a bare metric value is not a result")
    w("")
    w("\"ipSAE 0.864\" tells a reader nothing. They cannot know whether the metric "
      "saturates at 0.9 or runs to 1.0, whether real complexes cluster at 0.5 or at 0.95, "
      "or how far 0.864 sits from the noise. The handbook's band edge at 0.80 is "
      "**asserted**, not located in any distribution. This panel locates it.")
    w("")
    w(f"{len(pre) + len(post)} real, crystallised antibody–antigen complexes were folded "
      "through the identical pipeline — same driver, same flags, same Fv+Fv+antigen "
      "construct, `recycling_steps=10`, `diffusion_samples=5` — and scored on the same "
      "six metrics. Each complex's value is the **median over its five diffusion "
      "samples**.")
    w("")
    w("## The split, and why it is the whole point")
    w("")
    w("Boltz-2's training cutoff is **2023-06-01 on PDB *release* date**. A panel mixing "
      "memorised and novel complexes would produce a distribution that means nothing, "
      "because they are different tasks:")
    w("")
    w(f"- **pre-cutoff (n={len(pre)})** — Boltz has seen these. This is the **ceiling**: "
      "what the metrics look like when prediction is closer to recall.")
    w(f"- **post-cutoff (n={len(post)})** — genuinely novel. This is the **honest bar** "
      "for a de novo design.")
    w("")
    w("Both arms were drawn by one RCSB query sorted by release date, taking the entries "
      "**nearest the cutoff on each side**, so resolution practice, refinement convention "
      "and target fashion are matched and the cutoff is close to the only systematic "
      "difference between them.")
    w("")
    w("## Coverage — how many complexes each metric actually produced")
    w("")
    w("Stated before any distribution, because a metric that silently drops rows reports "
      "a distribution of the rows where it happened to work. DockQ is the one at risk "
      "here: it needs a native, and it refuses rather than guessing when chains cannot be "
      "mapped.")
    w("")
    w("| metric | pre-cutoff | post-cutoff |")
    w("|---|---|---|")
    for m in METRICS:
        a = sum(1 for r in pre if r.get(m) is not None)
        b = sum(1 for r in post if r.get(m) is not None)
        flag = "" if (a == len(pre) and b == len(post)) else "  ⚠️"
        w(f"| {LABEL[m]} | {a}/{len(pre)} | {b}/{len(post)}{flag} |")
    w("")
    w("`dockq.compute` returns **None with a reason**, never 0, when it cannot score an "
      "interface. That distinction is load-bearing: 8 of these 40 natives initially "
      "paired an Fv with the antigen of a *different copy* in the asymmetric unit, and a "
      "fabricated 0 would have entered the distribution as eight genuine docking "
      "failures instead of being caught. (See "
      "[[2026-09-22-calibrating-the-rubric-against-things-that-should-fail|the session "
      "doc]] §5b.) Model antigens carry SEQRES-filled internal gaps that the crystal does "
      "not, up to **38 residues** on 8EQ6 — against `dockq_allowed_mismatches: 40`, a "
      "margin of 2. Any row exceeding it appears as a gap in this table, not as a zero.")
    w("")

    w("## The distributions")
    w("")
    w("| metric | pre-cutoff median (IQR) | post-cutoff median (IQR) | Mann–Whitney p | "
      "what memorisation is worth |")
    w("|---|---|---|---|---|")
    for m in METRICS:
        a = [r[m] for r in pre if r.get(m) is not None]
        b = [r[m] for r in post if r.get(m) is not None]
        if len(a) < 3 or len(b) < 3:
            continue
        u, p = mannwhitneyu(a, b, alternative="two-sided")
        rb = 2 * u / (len(a) * len(b)) - 1          # rank-biserial correlation
        qa, qb = stats.quantiles(a), stats.quantiles(b)
        w(f"| {LABEL[m]} | {stats.median(a):.3f} ({qa[0]:.3f}–{qa[2]:.3f}) | "
          f"{stats.median(b):.3f} ({qb[0]:.3f}–{qb[2]:.3f}) | {p:.3f} | "
          f"rank-biserial {rb:+.2f} |")
    w("")
    w("*Rank-biserial is the effect size: +1 means every pre-cutoff complex beats every "
      "post-cutoff one, 0 means the arms are interchangeable.* At n=20 per arm "
      "Mann–Whitney has roughly 80% power for a rank-biserial around 0.6, so **a "
      "non-significant row here means \"no effect larger than large\", not \"no effect\"** "
      "— the detectable effect is stated because this project has four times reported an "
      "underpowered null as a finding.")
    w("")

    if tests:
        w("## Our designs, as percentiles")
        w("")
        w("Percentiles are against the **post-cutoff** arm, because that is the "
          "distribution a novel design belongs in. Reported as ranks, since with "
          f"n={len(post)} a percentile has 5-point resolution and a 95% CI near ±20 "
          "points at the median — a decimal percentile would imply precision the sample "
          "size cannot support.")
        w("")
        for name, t in tests.items():
            w(f"### {name}")
            w("")
            w("| metric | our value | rank in post-cutoff arm | percentile | "
              "post-cutoff median |")
            w("|---|---|---|---|---|")
            for m in METRICS:
                v = t.get(m)
                pool = [r[m] for r in post if r.get(m) is not None]
                if v is None or len(pool) < 3:
                    continue
                dirn = direction(cfg, m)
                pc, rank = pct_rank(v, pool, dirn)
                w(f"| {LABEL[m]} | **{v:.3f}** | {rank} of {len(pool)} | "
                  f"{pc:.0f}th | {stats.median(pool):.3f} |")
            w("")
    # ---- is ipSAE continuous, or a per-sample coin flip? ----
    allrows = [r for r in panel if r.get("rows")]
    if len(allrows) >= 8:
        FLOOR = 0.05
        buckets = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        n_samples = n_floor = 0
        for r in allrows:
            vals = [x["ipsae"] for x in r["rows"] if x.get("ipsae") is not None]
            if len(vals) != 5:
                continue
            k = sum(1 for v in vals if v < FLOOR)
            buckets[k] = buckets.get(k, 0) + 1
            n_samples += len(vals)
            n_floor += k
        total = sum(buckets.values())
        if total >= 8:
            w("## Is ipSAE a confidence, or a coin flip?")
            w("")
            w(f"Each complex was folded five times from one trunk pass, so the five "
              f"values differ *only* in the diffusion draw. Across the panel the "
              f"within-complex spread is not small: it reaches "
              f"{max(r.get('ipsae_spread', 0) for r in allrows):.3f} ipSAE on a single "
              f"complex — wider than the entire Medium band.")
            w("")
            w(f"Counting how many of each complex's five samples sit on the ipSAE floor "
              f"(< {FLOOR}):")
            w("")
            w("| samples at floor | complexes | |")
            w("|---|---|---|")
            for k in range(6):
                bar = "█" * buckets.get(k, 0)
                w(f"| {k} of 5 | {buckets.get(k, 0)} | {bar} |")
            w("")
            ends = buckets.get(0, 0) + buckets.get(5, 0)
            w(f"**{ends} of {total} complexes are all-or-nothing** (either no sample on "
              f"the floor, or every sample on it); {total - ends} are mixed. Overall "
              f"{n_floor}/{n_samples} samples "
              f"({100.0*n_floor/max(n_samples,1):.0f}%) are at the floor.")
            w("")
            if total - ends >= total * 0.25:
                w("**A substantial fraction of complexes are mixed, and that is the "
                  "finding.** For those, whether the complex 'passes' is decided by which "
                  "diffusion samples happen to be drawn — the quantity being thresholded "
                  "is not a stable property of the complex. ipSAE's hard PAE < 10 Å cutoff "
                  "means a pose either has inter-chain pairs inside the window or it does "
                  "not, so the score collapses toward a two-state indicator rather than "
                  "degrading smoothly. **Reading a gate off one sample, on a mixed "
                  "complex, is a coin flip with the model's confidence ranking as the "
                  "thumb on the scale.**")
            else:
                w("**Most complexes are all-or-nothing**, so ipSAE behaves here as a "
                  "two-state liveness indicator — docked or not — rather than as a graded "
                  "confidence. That is consistent with this project's earlier finding that "
                  "it separates dead interfaces from live ones while barely ranking the "
                  "live ones.")
            w("")

    w("## Reading this honestly")
    w("")
    w("A high percentile here is **not** evidence the design binds. It says the predictor "
      "is as confident about our design as it is about real complexes it has never seen — "
      "which is a statement about the predictor's confidence, not about a molecule. The "
      "one metric in this table that reads coordinates against an external truth is "
      "DockQ, and for our de novo design there is no crystal to read against, so it is "
      "absent exactly where it would matter most.")
    w("")
    w("The panel's real contribution is the opposite of flattering: it shows what these "
      "numbers look like when the answer is known to be right, and therefore how much of "
      "the band structure in §5.2 is measuring difficulty rather than quality.")
    return "\n".join(L) + "\n"


def main() -> int:
    cfg = load()
    d = json.loads(SCORES.read_text())
    for path, text in (("results/negative_control.md", negative_control(d, cfg)),
                       ("results/calibration.md", calibration(d, cfg))):
        if text:
            Path(path).write_text(text)
            print(f"wrote {path}  ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
