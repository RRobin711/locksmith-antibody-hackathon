#!/usr/bin/env python3
"""Is the designed interface ON THE PD-L1 EPITOPE, or merely on SOME patch of PD-1?

WHY THIS NULL AND NOT THE ONE WE RAN. The 2026-09-21 pilot compared conditioned
against UNCONDITIONED backbones and reported d=1.47, p=0.0016. Two problems, both
ours:

  1. It was optional stopping -- an interim look at n=10 v 5 (d=0.96, ambiguous),
     then extension to n=18 v 18 and a test at nominal alpha. No stopping rule was
     declared, so the p is not the true type-I rate and d is upward-biased by exactly
     the winner's-curse logic this project applies elsewhere.
  2. "No hotspots" is the wrong comparison. It asks whether conditioning does
     ANYTHING. The question that matters is whether it hits THE RIGHT FACE, and the
     control that could fail is a patch somewhere else on the same antigen.

This script runs the second one, on data already on disk, at zero marginal cost. For
each backbone we recompute `frac_iface_on_epitope` against N random CONTIGUOUS SURFACE
PATCHES of the same size (26 residues) drawn from the same chain, and ask where the
real epitope falls in that distribution.

A contiguous patch is the right null, not 26 residues drawn uniformly at random. Any
dock lands on some contiguous piece of surface, so a scattered 26-residue set is a
strawman the design would beat for geometric reasons that have nothing to do with
conditioning. Uniform draws are reported too, precisely to show that gap.

READ THE RESULT CAREFULLY. This tests TARGETING, not binding. A backbone can sit
squarely on the PD-L1 footprint and still not be an antibody that binds anything.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

POD = Path("runs/challenge2_pod/c2")
OUT = Path("results/challenge2_patch_null.md")
CUTOFF2 = 5.0 ** 2
EPITOPE = [33, 35, 37, 39, 42, 43, 44, 45, 46, 47, 48, 49, 50, 54,
           58, 59, 60, 92, 93, 95, 97, 101, 103, 104, 105, 108]
N_DRAWS = 2000
SEED = 20260922


def parse(path: Path):
    """chain -> {resnum: [xyz]}, plus the absolute-index CDR loop atom list.

    Same two invariants as `pod/check_backbone.py`: RFdiffusion renumbers continuously
    across chains so hotspots are ORDINALS within chain T, and the loop REMARK indices
    are 1-indexed ABSOLUTE across the whole file rather than per chain.
    """
    chains: dict[str, dict[int, list[tuple[float, float, float]]]] = {}
    order: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    loop_abs: list[int] = []
    for line in path.read_text().splitlines():
        if line.startswith("REMARK PDBinfo-LABEL:"):
            p = line.split()
            if len(p) >= 4 and p[-1] in ("H1", "H2", "H3", "L1", "L2", "L3"):
                loop_abs.append(int(p[-2]))
        elif line.startswith("ATOM") and line[76:78].strip() != "H":
            ch, num = line[21], int(line[22:26])
            if (ch, num) not in seen:
                seen.add((ch, num)); order.append((ch, num))
            chains.setdefault(ch, {}).setdefault(num, []).append(
                (float(line[30:38]), float(line[38:46]), float(line[46:54])))
    return chains, order, loop_abs


def centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n,
            sum(p[2] for p in pts) / n)


def analyse(path: Path, rng: random.Random):
    chains, order, loop_abs = parse(path)
    if not {"H", "L", "T"} <= set(chains) or not loop_abs:
        return None
    tnums = sorted(chains["T"])
    loop_pts = [p for i in loop_abs if 1 <= i <= len(order)
                for p in chains[order[i - 1][0]][order[i - 1][1]]]

    def near(pts):
        return any((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2 <= CUTOFF2
                   for q in pts for p in loop_pts)

    contacted = {n for n in tnums if near(chains["T"][n])}
    if not contacted:
        return None

    epi = {tnums[i] for i in EPITOPE if i < len(tnums)}
    real = len(contacted & epi) / len(contacted)

    cen = {n: centroid(chains["T"][n]) for n in tnums}
    k = len(epi)

    def patch_from(seed_res: int) -> set[int]:
        """The k residues whose centroids are nearest the seed's -- a contiguous
        surface patch of the same size as the real epitope."""
        s = cen[seed_res]
        d = sorted(tnums, key=lambda n: (cen[n][0] - s[0]) ** 2 +
                                        (cen[n][1] - s[1]) ** 2 +
                                        (cen[n][2] - s[2]) ** 2)
        return set(d[:k])

    contig, unif = [], []
    for _ in range(N_DRAWS):
        p = patch_from(rng.choice(tnums))
        contig.append(len(contacted & p) / len(contacted))
        u = set(rng.sample(tnums, k))
        unif.append(len(contacted & u) / len(contacted))
    return {"file": path.name, "n_contacted": len(contacted), "real": real,
            "contig": contig, "unif": unif,
            "k": k, "n_target": len(tnums)}


def pct(xs, q):
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, int(round(q * (len(ys) - 1)))))]


def mean(xs):
    return sum(xs) / len(xs)


def main() -> int:
    rng = random.Random(SEED)
    bbs = sorted((POD / "bb").glob("bb_*_0.pdb"))
    if not bbs:
        print(f"no backbones under {POD/'bb'} -- retrieve the pod volume first",
              file=sys.stderr)
        return 1

    rows = [r for r in (analyse(p, rng) for p in bbs) if r]
    L, w = [], None
    L = []; w = L.append
    w("# Is the interface on the PD-L1 epitope, or just on *a* patch of PD-1?")
    w("")
    w(f"`scripts/70_epitope_patch_null.py`, seed {SEED}, {N_DRAWS} draws per backbone, "
      f"{len(rows)} conditioned backbones retrieved from the pod volume.")
    w("")
    w("The pilot's published test compared conditioned against unconditioned backbones "
      "(d=1.47). That asks whether conditioning does anything at all. **This asks the "
      "question that can fail: does the interface sit on the epitope we AIMED at, "
      "rather than on an equally-sized patch somewhere else on the same antigen?** It "
      "costs nothing -- same files, no new folds.")
    w("")
    w("| backbone | iface res | real epitope | contiguous-patch null (mean, p95) | "
      "empirical p | uniform-26 null |")
    w("|---|---|---|---|---|---|")
    wins = 0
    for r in rows:
        p_emp = (sum(1 for x in r["contig"] if x >= r["real"]) + 1) / (len(r["contig"]) + 1)
        wins += p_emp < 0.05
        w(f"| `{r['file']}` | {r['n_contacted']} | **{r['real']:.3f}** | "
          f"{mean(r['contig']):.3f}, {pct(r['contig'], 0.95):.3f} | {p_emp:.4f} | "
          f"{mean(r['unif']):.3f} |")

    allreal = [r["real"] for r in rows]
    allcont = [mean(r["contig"]) for r in rows]
    allunif = [mean(r["unif"]) for r in rows]
    w("")
    w(f"**Pooled.** Real epitope mean **{mean(allreal):.3f}** against a contiguous "
      f"surface patch of the same size at **{mean(allcont):.3f}**, and 26 residues "
      f"drawn uniformly at **{mean(allunif):.3f}**. "
      f"{wins}/{len(rows)} backbones beat their own contiguous-patch null at p<0.05.")
    w("")
    w(f"The target chain has {rows[0]['n_target']} residues and the epitope is "
      f"{rows[0]['k']} of them, so a uniformly-drawn set captures about "
      f"{rows[0]['k']/rows[0]['n_target']:.3f} of any interface by construction. "
      f"**That is why the uniform column is the strawman and the contiguous column is "
      f"the test** -- a real dock lands on contiguous surface, so the null must too.")
    w("")
    w("## What this does and does not establish")
    w("")
    w("**Does:** the conditioning put the designed loops on the intended face of PD-1 "
      "rather than on an arbitrary patch of equal size, and the comparison is "
      "deterministic per backbone rather than a two-sample test with an undeclared "
      "stopping rule.")
    w("")
    w("**Does not:** that any of these backbones binds. Targeting is not affinity. "
      "The epitope is also the largest contiguous patch the loops could plausibly "
      "reach given where RFdiffusion was told to build, so a portion of this effect is "
      "mechanical rather than evidential.")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L[-14:]))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
