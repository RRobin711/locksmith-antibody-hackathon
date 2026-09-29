#!/usr/bin/env python3
"""Select a DECOY epitope on the far face of PD-1 — the control that can falsify.

WHY THIS IS THE ONLY OUTSTANDING WAY TO BE WRONG. `scripts/70` and `scripts/94` ask
whether a conditioned backbone's interface lands on the PD-L1 epitope rather than on some
other patch, and answer yes (real 0.712, shape-matched null 0.172, 18/18 at p<0.05 after
2026-09-28). Both are *observational*: they compare one arm against a resampled null on the
same structures. Neither can distinguish

    (a) "the hotspots steered RFdiffusion to the face we named"     from
    (b) "RFdiffusion docks antibodies on that face of PD-1 anyway",

because nothing in either test ever ASKED for a different face. This does. Condition on 26
residues on the opposite side and measure where the interfaces land. If they follow the
decoy, conditioning works. If they still land on the PD-L1 footprint, the published result
was reading RFdiffusion's prior, not our conditioning, and the claim collapses.

Stated before the run, per standing rule: the informative outcome is
`frac_iface_on_decoy` >> `frac_iface_on_epitope` for decoy-conditioned backbones. The
conditioned arm's own value is 0.712 on its target, so a decoy arm landing near that on the
DECOY is a pass; a decoy arm landing near 0.712 on the REAL EPITOPE is a refutation.

WHAT MAKES A FAIR DECOY, and why each constraint is here:

  same size (26)        the statistic is a fraction of interface residues captured, which
                        scales with patch size
  matched RMS spread    §D4: an unmatched null was worth +0.019 on the mean. A decoy that
                        is more compact than the real epitope is a different experiment
  surface-exposed       a buried patch cannot be docked onto, so it would fail for
                        geometry rather than for conditioning — an unfalsifiable control
  zero overlap          any shared residue lets a single dock satisfy both patches
  maximally opposite    measured as the angle between (patch centroid − protein centroid)
                        and the same vector for the real epitope

NUMBERING, AND THE TRAP IT HIDES. RFdiffusion renumbers its output continuously across
chains, so hotspots passed to the tool use the TARGET PDB's own author numbering (5GGS
chain Z, relabelled T by `pod/00_setup.sh`), while `check_backbone.py` wants 0-BASED
ORDINALS within chain T. A check keyed on the wrong one returns a clean, believable zero.
This script emits BOTH forms and prints them side by side.

    uv run python scripts/95_decoy_patch_control.py              # select + verify (CPU)
    uv run python scripts/95_decoy_patch_control.py --analyse runs/challenge2_decoy/bb
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

REF = Path("data/refs/5ggs.pdb")
OUT_MD = Path("results/decoy_patch.md")
OUT_JSON = Path("results/decoy_patch.json")
OUT_HOT = Path("pod/inputs_decoy_hotspots.txt")

# The PD-L1 footprint on PD-1, in 5GGS author numbering. Copied from pod/00_setup.sh,
# which is the file that actually produced the conditioned run's hotspots.
FOOT = [64, 66, 68, 70, 73, 74, 75, 76, 77, 78, 79, 80, 81, 85, 89, 90, 91,
        123, 124, 126, 128, 132, 134, 135, 136, 139]
SEED = 20260928
N_TRIES = 40000
SPREAD_TOL = 0.5     # Å
MIN_SASA = 15.0      # Å², on the isolated chain; below this a residue is buried


def load_target() -> dict[int, np.ndarray]:
    """Chain Z of 5GGS -- the PD-1 copy. pod/00_setup.sh relabels it to T."""
    if not REF.exists():
        sys.exit(f"{REF} not found -- run scripts/01_fetch_refs.py")
    res: dict[int, list] = {}
    for line in REF.read_text().splitlines():
        if line.startswith("ATOM") and line[21] == "Z" and line[76:78].strip() != "H":
            res.setdefault(int(line[22:26]), []).append(
                (float(line[30:38]), float(line[38:46]), float(line[46:54])))
    return {k: np.array(v) for k, v in sorted(res.items())}


def sasa_per_residue(nums: list[int]) -> dict[int, float]:
    """Absolute SASA of each residue on the ISOLATED target chain."""
    try:
        import freesasa
    except ImportError:
        print("freesasa not installed -- skipping the exposure filter", file=sys.stderr)
        return {n: 1e9 for n in nums}
    tmp = Path("/tmp/_decoy_target.pdb")
    keep = [l for l in REF.read_text().splitlines()
            if l.startswith("ATOM") and l[21] == "Z"]
    tmp.write_text("\n".join(keep) + "\nTER\nEND\n")
    s = freesasa.Structure(str(tmp))
    r = freesasa.calc(s)
    out: dict[int, float] = {}
    for i in range(s.nAtoms()):
        out[int(s.residueNumber(i))] = out.get(int(s.residueNumber(i)), 0.0) + r.atomArea(i)
    return out


def rms_spread(c: np.ndarray) -> float:
    return float(np.sqrt(((c - c.mean(0)) ** 2).sum(1).mean()))


def _baseline_on_existing(decoy: list[int], foot: list[int]):
    """Score the ALREADY-GENERATED conditioned backbones against the decoy.

    If an arm aimed at the real epitope also scores highly on the decoy, the two patches
    are not behaviourally distinct and the control cannot be read. Free, so it runs before
    the GPU is rented rather than after.
    """
    bb = Path("runs/challenge2_pod/c2/bb")
    if not bb.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_pn", Path(__file__).resolve().parent / "70_epitope_patch_null.py")
    pn = importlib.util.module_from_spec(spec); spec.loader.exec_module(pn)
    ds, es = [], []
    for p in sorted(bb.glob("*_0.pdb")):
        chains, order, loop_abs = pn.parse(p)
        if not {"H", "L", "T"} <= set(chains) or not loop_abs:
            continue
        tnums = sorted(chains["T"])
        loop_pts = np.array([q for i in loop_abs if 1 <= i <= len(order)
                             for q in chains[order[i - 1][0]][order[i - 1][1]]])
        con = set()
        for n in tnums:
            pts = np.array(chains["T"][n])
            if (((pts[:, None, :] - loop_pts[None, :, :]) ** 2).sum(-1) <= pn.CUTOFF2).any():
                con.add(n)
        if not con:
            continue
        # both patches expressed as ordinals into this backbone's chain T
        nums_ref = sorted({int(l[22:26]) for l in REF.read_text().splitlines()
                           if l.startswith("ATOM") and l[21] == "Z"})
        dset = {tnums[nums_ref.index(r)] for r in decoy if nums_ref.index(r) < len(tnums)}
        eset = {tnums[nums_ref.index(r)] for r in foot if nums_ref.index(r) < len(tnums)}
        ds.append(len(con & dset) / len(con)); es.append(len(con & eset) / len(con))
    if not ds:
        return None
    return len(ds), sum(ds) / len(ds), sum(es) / len(es)


def select() -> int:
    res = load_target()
    nums = list(res)
    cen = {n: res[n].mean(0) for n in nums}
    missing = [r for r in FOOT if r not in res]
    if missing:
        sys.exit(f"FATAL: footprint residues absent from chain Z: {missing}")

    prot_c = np.array([cen[n] for n in nums]).mean(0)
    epi_c = np.array([cen[n] for n in FOOT]).mean(0)
    epi_spread = rms_spread(np.array([cen[n] for n in FOOT]))
    epi_dir = (epi_c - prot_c) / np.linalg.norm(epi_c - prot_c)

    sasa = sasa_per_residue(nums)
    surface = [n for n in nums if sasa.get(n, 0.0) >= MIN_SASA and n not in FOOT]
    k = len(FOOT)
    if len(surface) < k:
        sys.exit(f"only {len(surface)} exposed non-epitope residues, need {k}")

    rng = random.Random(SEED)
    arr = np.array([cen[n] for n in surface])
    best = None
    for _ in range(N_TRIES):
        s = rng.randrange(len(surface))
        alpha = rng.uniform(1.0, 4.0)
        m = min(len(surface), max(k, int(round(k * alpha))))
        near = np.argsort(((arr - arr[s]) ** 2).sum(1))[:m]
        pick = rng.sample(list(near), k)
        c = arr[pick]
        sp = rms_spread(c)
        if abs(sp - epi_spread) > SPREAD_TOL:
            continue
        d = c.mean(0) - prot_c
        n_ = np.linalg.norm(d)
        if n_ < 1e-6:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d / n_, epi_dir))))))
        if best is None or ang > best[0]:
            best = (ang, sorted(surface[i] for i in pick), sp)

    if best is None:
        sys.exit("no spread-matched decoy patch found -- widen SPREAD_TOL")
    ang, decoy, sp = best

    ordinals = [nums.index(r) for r in decoy]
    epi_ord = [nums.index(r) for r in FOOT]
    dist = float(np.linalg.norm(np.array([cen[n] for n in decoy]).mean(0) - epi_c))

    OUT_HOT.parent.mkdir(exist_ok=True)
    OUT_HOT.write_text(",".join(f"T{r}" for r in decoy))
    OUT_JSON.write_text(json.dumps(
        {"decoy_resnums_5ggs": decoy, "decoy_ordinals_chainT": ordinals,
         "epitope_resnums_5ggs": FOOT, "epitope_ordinals_chainT": epi_ord,
         "angle_deg": ang, "centroid_separation_A": dist,
         "decoy_rms_spread_A": sp, "epitope_rms_spread_A": epi_spread,
         "overlap": sorted(set(decoy) & set(FOOT)), "seed": SEED}, indent=2))

    L = []; w = L.append
    w("# A decoy epitope on the far face of PD-1")
    w("")
    w(f"`scripts/95_decoy_patch_control.py`, seed {SEED}. CPU only — selection and "
      f"verification run before any GPU is rented.")
    w("")
    w("This is the control that can **falsify** the conditioning result. Every test run so "
      "far compares one conditioned arm against a resampled null on the same structures, "
      "so none of them can separate *\"the hotspots steered RFdiffusion\"* from "
      "*\"RFdiffusion docks antibodies on that face of PD-1 anyway\"*. Nothing has ever "
      "asked it for a different face.")
    w("")
    w("## The patch, and why it is fair")
    w("")
    w("| property | epitope (PD-L1 footprint) | decoy | constraint |")
    w("|---|---|---|---|")
    w(f"| residues | {k} | **{len(decoy)}** | equal — the statistic scales with size |")
    w(f"| RMS spread | {epi_spread:.2f} Å | **{sp:.2f} Å** | matched ±{SPREAD_TOL} Å (§D4) |")
    w(f"| overlap | — | **{len(set(decoy) & set(FOOT))} residues** | zero, or one dock satisfies both |")
    w(f"| min SASA (isolated chain) | — | **≥ {MIN_SASA:.0f} Å²** | a buried patch fails for geometry, not conditioning |")
    w(f"| angle from epitope, about the centroid | 0° | **{ang:.1f}°** | maximised |")
    w(f"| centroid separation | — | **{dist:.1f} Å** | |")
    w("")
    w("## The two numberings — do not mix them")
    w("")
    w("RFdiffusion renumbers its output continuously across chains, so a check keyed on the "
      "wrong form returns a clean, believable **zero**. Both are emitted:")
    w("")
    w("```")
    w(f"hotspots for RFdiffusion (5GGS chain Z author numbering, relabelled T):")
    w(f"  {','.join(f'T{r}' for r in decoy)}")
    w(f"ordinals for pod/check_backbone.py (0-based within chain T):")
    w(f"  {','.join(str(o) for o in ordinals)}")
    w("```")
    w("")
    w(f"Written to `{OUT_HOT}` and `{OUT_JSON}`.")
    w("")

    # Two checks that need no GPU and would each invalidate the control.
    D = np.array([cen[n] for n in decoy]); E = np.array([cen[n] for n in FOOT])
    mind = float(np.sqrt(((D[:, None, :] - E[None, :, :]) ** 2).sum(-1)).min())
    meand = float(np.sqrt(((D[:, None, :] - E[None, :, :]) ** 2).sum(-1)).mean())
    w("## Two pre-run checks, both free")
    w("")
    w(f"**Separation.** Nearest decoy↔epitope residue pair: **{mind:.1f} Å** centroid to "
      f"centroid (mean {meand:.1f} Å). The sets are disjoint by construction, but they "
      f"share an *edge*, so a dock straddling the boundary could partially satisfy both. "
      f"Recorded as a limitation rather than designed away — pushing the patches further "
      f"apart on a 113-residue IgV domain costs either the size match or the spread match.")
    w("")
    base = _baseline_on_existing(decoy, FOOT)
    if base:
        n, md_, me_ = base
        w(f"**Behavioural disjointness.** The {n} EXISTING conditioned backbones, scored "
          f"against this decoy: mean `frac_iface_on_decoy` = **{md_:.3f}**, against "
          f"`frac_iface_on_epitope` = **{me_:.3f}**. So an arm aimed at the real epitope "
          f"never touches the decoy, and the two patches separate cleanly in practice and "
          f"not merely on paper. *This is what makes the decoy run interpretable: the "
          f"measurement already distinguishes the two faces before any new backbone exists.*")
        w("")
    w("## Pre-registered reading of the outcome")
    w("")
    w("Measured on the decoy-conditioned backbones, against the **decoy** and against the "
      "**real epitope**:")
    w("")
    w("| outcome | meaning |")
    w("|---|---|")
    w("| `frac_iface_on_decoy` high, `frac_iface_on_epitope` low | conditioning works; the "
      "published result is about our hotspots |")
    w("| both low | the decoy face is simply not dockable — **inconclusive**, not a pass |")
    w("| `frac_iface_on_epitope` still ≈ 0.712 | **the published result is refuted**: it was "
      "reading RFdiffusion's prior, not our conditioning |")
    w("")
    w("The conditioned arm's own value is **0.712** on its target and **0.172** against a "
      "shape-matched null, so those are the two reference points. Note the middle row: a "
      "null result here does not rescue the claim, and saying so before the run is the "
      "point of writing it down now.")
    w("")
    OUT_MD.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT_MD}, {OUT_JSON}, {OUT_HOT}")
    return 0


def analyse(bb_dir: Path) -> int:
    """After the pod run: score decoy-conditioned backbones on BOTH patches."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_pn", Path(__file__).resolve().parent / "70_epitope_patch_null.py")
    pn = importlib.util.module_from_spec(spec); spec.loader.exec_module(pn)
    meta = json.loads(OUT_JSON.read_text())
    nodock: list[str] = []
    # Accept BOTH naming schemes. The pod ran one invocation per backbone, giving
    # `bb_7_0.pdb`; the local CPU run uses a single invocation with num_designs=K, giving
    # `dec_0.pdb` ... `dec_17.pdb`. A `*_0.pdb` glob silently matches ONE of eighteen --
    # it would have reported n=1 and looked like a working analysis.
    cands = sorted(set(bb_dir.glob("*.pdb")) - set(bb_dir.glob("*_traj*.pdb")))
    rows = []
    for p in cands:
        chains, order, loop_abs = pn.parse(p)
        if not {"H", "L", "T"} <= set(chains) or not loop_abs:
            continue
        tnums = sorted(chains["T"])
        loop_pts = np.array([q for i in loop_abs if 1 <= i <= len(order)
                             for q in chains[order[i - 1][0]][order[i - 1][1]]])
        contacted = set()
        for n in tnums:
            pts = np.array(chains["T"][n])
            if (((pts[:, None, :] - loop_pts[None, :, :]) ** 2).sum(-1) <= pn.CUTOFF2).any():
                contacted.add(n)
        if not contacted:
            # NOT a parse failure: the antibody docked nowhere on the antigen, so
            # frac_iface_on_* is undefined (0/0). Recorded and reported rather than
            # skipped -- an unexplained drop from n=18 to n=16 is how a silent
            # exclusion looks exactly like a working analysis.
            nodock.append(p.name)
            continue
        dec = {tnums[i] for i in meta["decoy_ordinals_chainT"] if i < len(tnums)}
        epi = {tnums[i] for i in meta["epitope_ordinals_chainT"] if i < len(tnums)}
        rows.append((p.name, len(contacted),
                     len(contacted & dec) / len(contacted),
                     len(contacted & epi) / len(contacted)))
    if not rows:
        print(f"no usable backbones under {bb_dir}", file=sys.stderr); return 1
    print(f"{'backbone':<18}{'iface':>6}{'on_decoy':>10}{'on_epitope':>12}")
    for n, c, d, e in rows:
        print(f"{n:<18}{c:>6}{d:>10.3f}{e:>12.3f}")
    md = sum(r[2] for r in rows) / len(rows)
    me = sum(r[3] for r in rows) / len(rows)
    total = len(rows) + len(nodock)
    print(f"\nbackbones generated        {total}")
    if nodock:
        print(f"no antigen contact at all  {len(nodock)}  ({', '.join(nodock)})"
              f"  -- frac undefined, EXCLUDED")
    print(f"n analysed                 {len(rows)}")
    sizes = [r[1] for r in rows]
    print(f"interface size, analysed   median {sorted(sizes)[len(sizes)//2]}, "
          f"range {min(sizes)}-{max(sizes)}  (conditioned arm: median 9, range 4-15)")
    print(f"mean frac_iface_on_decoy    {md:.3f}")
    print(f"mean frac_iface_on_epitope  {me:.3f}")
    print(f"reference — conditioned arm: 0.712 on its own target, 0.000 on this decoy")
    print(f"reference — unconditioned arm: 0.500 on the epitope; shape-matched null: 0.172")

    # ---- PRE-REGISTERED DECISION RULE, AMENDED 2026-09-28 ----------------------
    # AMENDMENT, made BEFORE any decoy backbone was read and justified ONLY by the
    # UNCONDITIONED arm, which already existed:
    #
    #   The first version used BAR = 0.500 for both faces and called it "symmetric, and
    #   not arbitrary". It is symmetric in NUMBER and badly asymmetric in EVIDENCE,
    #   because the unconditioned baselines differ enormously. Measured over the 18
    #   unconditioned backbones (scripts/96 and the check below):
    #
    #       unconditioned frac_iface_on_epitope = 0.500   (sd 0.168, max 0.714)
    #       unconditioned frac_iface_on_decoy   = 0.000   (0 of 18, max 0.000)
    #
    #   RFdiffusion left to itself NEVER touches the decoy face. So "decoy > 0.500"
    #   demanded that conditioning beat a baseline of zero by half the interface, while
    #   "epitope > 0.500" only demanded it match a baseline it already sits at. A real
    #   but partial steering effect would have been scored as failure.
    #
    # Each bar is now tied to the reference that makes it mean something:
    #   DECOY_NULL   0.172  the shape-matched random-patch null -- the SAME bar the
    #                       original conditioning claim had to beat (results/…_shape_matched)
    #   DECOY_STRONG 0.500  half the interface, i.e. comparable to what conditioning
    #                       achieved on its own target (0.712)
    #   EPI_BASE     0.500  the unconditioned arm's own epitope occupancy: at or above
    #                       this, conditioning did NOT move the interface off the default
    DECOY_NULL, DECOY_STRONG, EPI_BASE = 0.172, 0.500, 0.500

    import statistics as _st
    def ci95(xs):
        if len(xs) < 2: return 0.0
        return 1.96 * _st.stdev(xs) / (len(xs) ** 0.5)
    dvals = [r[2] for r in rows]; evals = [r[3] for r in rows]
    print(f"  95% CI on decoy   ±{ci95(dvals):.3f}")
    print(f"  95% CI on epitope ±{ci95(evals):.3f}")
    print(f"  backbones with ANY decoy contact: {sum(1 for x in dvals if x > 0)}/{len(dvals)}"
          f"   (unconditioned arm: 0/18)")

    if md >= DECOY_STRONG and me < EPI_BASE:
        row, verdict = 1, ("CONDITIONING WORKS, strongly. The interfaces followed the "
                           "hotspots onto a face the unconditioned arm never touches (0/18). "
                           "The published result is about our conditioning.")
    elif md > DECOY_NULL and me < EPI_BASE:
        row, verdict = 2, ("PARTIAL. Decoy occupancy beats the random-patch null (0.172) but "
                           "falls short of what conditioning achieved on its own target "
                           "(0.712). Conditioning steers, but weakly, and the headline "
                           "should say so rather than claim clean targeting.")
    elif me >= EPI_BASE and md <= DECOY_NULL:
        row, verdict = 3, ("REFUTED. Asked for a different face, the backbones still land on "
                           "the PD-L1 epitope at or above the UNCONDITIONED baseline (0.500), "
                           "and never on the decoy. frac_iface_on_epitope = 0.712 was reading "
                           "RFdiffusion's prior, not our hotspots. Propagate everywhere.")
    elif md <= DECOY_NULL and me < EPI_BASE:
        row, verdict = 4, ("INCONCLUSIVE / third region. The interfaces left the default "
                           "epitope but did not arrive at the decoy. Conditioning perturbed "
                           "something, but this cannot separate 'steers imprecisely' from "
                           "'the decoy face is undockable' -- the unconditioned arm never "
                           "docks there either (0/18). NOT specificity for the real epitope.")
    else:
        row, verdict = 5, ("AMBIGUOUS, unregistered. Both faces above their bars -- consistent "
                           "with docks straddling the 4.9 A shared edge between the patches. "
                           "Report as ambiguous; do not pick the flattering half.")
    print(f"\nPRE-REGISTERED ROW {row} FIRED")
    print(f"  bars: decoy null {DECOY_NULL}, decoy strong {DECOY_STRONG}, epitope baseline {EPI_BASE}")
    print(f"  {verdict}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyse", type=Path, help="directory of decoy-conditioned backbones")
    a = ap.parse_args()
    raise SystemExit(analyse(a.analyse) if a.analyse else select())
