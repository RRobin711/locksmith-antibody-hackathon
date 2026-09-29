#!/usr/bin/env python3
"""The calibration figure: predictor confidence against pose accuracy, on real crystals.

WHY A SCRIPT AND NOT AN IMAGE. A hand-made figure is a number that lives in a PNG and
nowhere else -- the same defect as a figure that lives in prose, which is how this project
lost the provenance of 7.73/10.08 and of the 0.276/0.296 reliability pair. This reads the
committed results files and regenerates, so if a number changes the figure changes with it.

WHAT IT PLOTS. Left panel: the 40-crystal calibration panel, ipSAE (Boltz's interface
confidence) against DockQ (pose accuracy vs the deposited structure). The §7.2 gate at
ipSAE >= 0.60 is drawn horizontally; the DockQ quality thresholds at 0.23 (Acceptable) and
0.49 (Medium) vertically. The four quadrants those lines cut are the gate's error classes.

Right strip: the six known-wrong antibodies from the negative control. **They carry no
DockQ and never can** -- each is docked onto PD-1, which is not its target, so no reference
complex exists to score a pose against. Plotting them at a fabricated x would invent the
very quantity the panel exists to measure, so they get their own axis-free strip at the
same y scale. Their values are medians over five diffusion samples on the REPAIRED
119-residue construct (results/negative_control.md), not the 113-mer -- see register §C9.

    uv run --extra analysis python scripts/98_calibration_figure.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

CAL = Path("runs/calibration/scores.json")
OUT = Path("figures")

# Validated with the dataviz palette validator (light surface #fcfcfb):
# CVD separation ΔE 24.7 protan / 32.7 tritan, normal-vision ΔE 33.6, contrast >= 3:1.
# Marker SHAPE carries the same distinction, so identity is never colour-alone.
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#1a1a19", "#6b6b68"
GATE, ACCEPTABLE, MEDIUM = 0.60, 0.23, 0.49
RHO = 0.702

# The six antibodies whose real target is not PD-1. Named explicitly rather than inferred
# by exclusion: `negctrl_nloop` also holds two positive controls and our own two designs,
# and "everything that isn't a positive" would silently absorb a future arm.
WRONG = ["hyhel-10", "cetuximab", "cr9114", "bevacizumab", "bo2c11", "trastuzumab"]


def load():
    d = json.loads(CAL.read_text())
    panel = d["panel"]
    xs = [(k, float(v["dockq"]), float(v["ipsae"]))
          for k, v in panel.items()
          if v.get("dockq") is not None and v.get("ipsae") is not None]
    # `negctrl_nloop` is the REPAIRED 119-residue construct, not the 113-mer `negctrl`.
    # Register §C9: on the 113-mer HyHEL-10 clears all five gates; on this one it does not.
    nl = d["negctrl_nloop"]
    negs = []
    for name in WRONG:
        key = f"nl_{name}"
        if key not in nl:
            raise SystemExit(f"expected {key} in negctrl_nloop; got {sorted(nl)}")
        negs.append((name, float(nl[key]["ipsae"])))
    return xs, sorted(negs, key=lambda kv: -kv[1])


def main() -> int:
    if not CAL.exists():
        print(f"{CAL} missing", file=sys.stderr); return 1
    xs, negs = load()
    if not xs or not negs:
        print("no data parsed", file=sys.stderr); return 1
    print(f"crystals parsed: {len(xs)}   negatives parsed: {len(negs)}")

    OUT.mkdir(exist_ok=True)
    fig = plt.figure(figsize=(9.2, 5.6), facecolor="#fcfcfb")
    gs = GridSpec(1, 2, width_ratios=[5.2, 1.0], wspace=0.06, figure=fig)
    ax = fig.add_subplot(gs[0, 0]); ax.set_facecolor("#fcfcfb")
    sx = fig.add_subplot(gs[0, 1], sharey=ax); sx.set_facecolor("#fcfcfb")

    # recessive grid, behind the marks
    ax.grid(True, color="#e6e6e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    # threshold lines -- 2px, recessive, labelled in the margin not on the data
    ax.axhline(GATE, color=MUTED, lw=1.6, ls="--", zorder=2)
    for v, lbl in ((ACCEPTABLE, "Acceptable 0.23"), (MEDIUM, "Medium 0.49")):
        ax.axvline(v, color=MUTED, lw=1.6, ls=":", zorder=2)
        ax.text(v, 1.02, lbl, rotation=0, ha="center", va="bottom",
                fontsize=8, color=MUTED, transform=ax.get_xaxis_transform())
    ax.text(0.012, GATE + 0.022, "§7.2 gate · ipSAE ≥ 0.60", fontsize=8.5, color=MUTED,
            bbox=dict(boxstyle="square,pad=0.18", fc="#fcfcfb", ec="none"))

    ax.scatter([d for _, d, _ in xs], [i for _, _, i in xs],
               s=58, marker="o", facecolor=BLUE, edgecolor="#fcfcfb", linewidth=1.2,
               zorder=3, label=f"real antibody–antigen crystals (n={len(xs)})")

    # negatives: own strip, NO x meaning
    sx.scatter([0.5] * len(negs), [v for _, v in negs],
               s=58, marker="^", facecolor=ORANGE, edgecolor="#fcfcfb", linewidth=1.2,
               zorder=3, label=f"known-wrong antibodies (n={len(negs)})")
    # De-collide the strip labels. hyhel-10 (0.228) and cr9114 (0.217) are 0.011 apart
    # and overprinted each other in the first render; the validator checks colour, not
    # layout, so this is the eyeball pass made mechanical. Labels move, MARKS DO NOT --
    # a nudged mark would be a falsified data point.
    MIN_GAP = 0.033
    label_y = [v for _, v in negs]           # negs is sorted high -> low
    for i in range(1, len(label_y)):
        if label_y[i - 1] - label_y[i] < MIN_GAP:
            label_y[i] = label_y[i - 1] - MIN_GAP
    for (name, v), ly in zip(negs, label_y):
        sx.annotate(name, xy=(0.5, v), xytext=(0.78, ly),
                    textcoords="data", fontsize=7.5, color=MUTED, va="center",
                    arrowprops=dict(arrowstyle="-", color="#d8d8d4", lw=0.8,
                                    shrinkA=0, shrinkB=4) if abs(ly - v) > 1e-9 else None)
    sx.axhline(GATE, color=MUTED, lw=1.6, ls="--", zorder=2)
    sx.set_xlim(0, 2.6); sx.set_xticks([])
    sx.set_xlabel("no DockQ\n(non-native target)", fontsize=8.5, color=MUTED)
    for s in ("top", "right", "bottom"):
        sx.spines[s].set_visible(False)
    sx.spines["left"].set_color("#d8d8d4")
    plt.setp(sx.get_yticklabels(), visible=False)

    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0)
    ax.set_xlabel("DockQ — pose accuracy against the deposited crystal", fontsize=10, color=INK)
    ax.set_ylabel("ipSAE — Boltz-2 interface confidence", fontsize=10, color=INK)
    ax.set_title("Predictor confidence tracks pose accuracy — and that is all it does",
                 fontsize=11.5, color=INK, loc="left", pad=26)
    ax.annotate(f"Spearman ρ = +{RHO:.3f}   n = {len(xs)}\n95% CI ≈ ±0.32 (Fisher-z, n=40)",
                xy=(0.985, 0.03), xycoords="axes fraction", ha="right", va="bottom",
                fontsize=9, color=INK,
                bbox=dict(boxstyle="round,pad=0.45", fc="#fcfcfb", ec="#d8d8d4", lw=1))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d8d8d4")
    ax.tick_params(colors=MUTED, labelsize=9)

    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = sx.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=9,
              labelcolor=INK, handletextpad=0.5)

    for ext in ("png", "svg"):
        p = OUT / f"calibration_ipsae_vs_dockq.{ext}"
        fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="#fcfcfb")
        print(f"wrote {p}  ({p.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
