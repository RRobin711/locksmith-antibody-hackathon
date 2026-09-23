#!/usr/bin/env python3
"""Score the calibration panel and the negative control, and turn our numbers into
percentiles.

WHAT A PERCENTILE BUYS THAT A VALUE DOES NOT. "ipSAE 0.864" is meaningless on its own:
nobody reading it knows whether the metric saturates at 0.9 or runs to 1.0, whether real
complexes cluster at 0.5 or 0.95, or how far 0.864 is from the noise. "ipSAE 0.864 --
78th percentile of genuinely novel real antibody-antigen complexes folded by the same
pipeline" is a claim a reader can check and a reviewer can attack. It is also the only
honest way to present a threshold the handbook simply asserted.

THREE REFERENCE DISTRIBUTIONS, and they answer different questions:

  * **pre-cutoff panel**  -- the ceiling. Real complexes Boltz has seen in training.
    Beating this would be suspicious, not impressive.
  * **post-cutoff panel** -- the honest bar. Real complexes Boltz has NOT seen. This is
    the distribution a de novo design should be compared against.
  * **negative control**  -- the floor. Real antibodies docked onto the WRONG antigen
    (PD-1). This is what "no binding" looks like through this pipeline, and without it
    the other two have no zero point.

Every fold contributes five diffusion samples, because `diffusion_samples=1` reports an
argmax rather than a sample. Per-complex we report the **median across the five**, which
is the honest point estimate, and carry the full spread so a reader can see how much of
any gap is diffusion noise. Reporting `model_0` -- Boltz's own top pick -- would compare
our maximum against other complexes' maxima, which is self-consistent but inflates every
number and hides the variance that matters.
"""
from __future__ import annotations

import json
import statistics as stats
import sys
from pathlib import Path

import gemmi

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.numbering import number
from locksmith.types import Provenance, Structure

PANEL = Path("runs/calibration/panel.json")
FOLDS = Path("runs/calibration/folds")
NEG = Path("runs/negctrl")
NEG_NLOOP = Path("runs/negctrl_nloop")
NATIVES = Path("runs/calibration/natives")
OUTJ = Path("runs/calibration/scores.json")


# ---------------------------------------------------------------- native construction
def build_native(entry: dict) -> Path | None:
    """Write an Fv+Fv+antigen native as chains A/B/C, matching the folded construct.

    DockQ compares a model to a native by sequence-aligned chain correspondence. Handing
    it a full Fab native against an Fv model means ~110 unmatched residues per antibody
    chain, which is exactly the situation where DockQ prints
    `no identical corresponding chain was found` and exits 1 with no output. Trimming the
    native to the same variable domains removes the problem at its source rather than by
    raising `--allowed_mismatches` until something comes out.

    The Fv span comes from ANARCII's `query_start`/`query_end`, which are indices into the
    sequence handed to it -- here the coordinate-derived sequence of CA-bearing residues,
    so they index that same residue list.
    """
    NATIVES.mkdir(parents=True, exist_ok=True)
    out = NATIVES / f"{entry['pdb_id'].lower()}_ABC.pdb"
    if out.exists():
        return out
    src = Path(entry["pdb"])
    if not src.exists():
        return None
    st = gemmi.read_structure(str(src))
    st.setup_entities()
    st.remove_ligands_and_waters()
    want = {entry["chains"]["H"]: "A", entry["chains"]["L"]: "B",
            entry["chains"]["A"]: "C"}
    new = gemmi.Structure()
    new.add_model(gemmi.Model("1"))
    for orig, dest in want.items():
        ch = next((c for c in st[0] if c.name == orig), None)
        if ch is None:
            return None
        res = [r for r in ch if r.find_atom("CA", "*")]
        if dest in ("A", "B"):
            n = number(gemmi.one_letter_code([r.name for r in res]).upper())
            if n is None:
                return None
            res = res[n.query_start:n.query_end + 1]
        nc = gemmi.Chain(dest)
        for r in res:
            nc.add_residue(r)
        new[0].add_chain(nc)
    new.setup_entities()
    new.write_pdb(str(out))
    return out


# ---------------------------------------------------------------- scoring
def score_models(pred_dir: Path, label: str, cfg, native: Path | None) -> list[dict]:
    c = cfg.conventions
    rows = []
    for pdb in sorted(pred_dir.glob(f"{label}_model_*.pdb")):
        tag = pdb.stem
        pae = pdb.parent / f"pae_{tag}.npz"
        st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae, label=tag)
        r: dict = {"model": int(tag.rsplit("_", 1)[1])}
        try:
            r |= {k: v.value for k, v in prodigy.compute(st).items()}
            r["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                       dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
            r["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
            r["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
        except Exception as e:                               # noqa: BLE001
            print(f"    {tag}: metric failure {type(e).__name__}: {e}", file=sys.stderr)
            continue
        if native is not None:
            try:
                nat = Structure(pdb=native, provenance=Provenance.EXPERIMENT,
                                label=native.stem)
                r["dockq"] = dockq.compute(st, nat)["dockq"].value
            except Exception as e:                           # noqa: BLE001
                print(f"    {tag}: dockq failed {e}", file=sys.stderr)
        rows.append(r)
    return rows


METRICS = ["ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa"]


def collapse(rows: list[dict]) -> dict:
    """Per-complex point estimate = MEDIAN over the five diffusion samples, plus spread."""
    out: dict = {"n_models": len(rows)}
    m0 = next((r for r in rows if r.get("model") == 0), None)
    for m in METRICS:
        vals = [r[m] for r in rows if r.get(m) is not None]
        if not vals:
            continue
        out[m] = stats.median(vals)
        out[f"{m}_spread"] = max(vals) - min(vals)
        out[f"{m}_max"] = max(vals)
        out[f"{m}_min"] = min(vals)
        # model_0 is what `diffusion_samples=1` returns: Boltz ranks its own outputs by
        # confidence, so this column is an ARGMAX, not a draw. Kept separately because the
        # gap between it and the median is the error a single-sample run makes.
        if m0 is not None and m0.get(m) is not None:
            out[f"{m}_m0"] = m0[m]
    return out


def main() -> int:
    cfg = load()
    panel = json.loads(PANEL.read_text())
    results: dict = {"panel": {}, "negctrl": {}, "negctrl_nloop": {}}

    print("=== calibration panel ===", flush=True)
    for e in panel:
        label = f"cal_{e['arm']}_{e['pdb_id'].lower()}"
        pred = FOLDS / label / f"boltz_results_{label}" / "predictions" / label
        if not pred.is_dir():
            continue
        native = build_native(e)
        rows = score_models(pred, label, cfg, native)
        if not rows:
            print(f"  {e['pdb_id']}: no scorable models", flush=True)
            continue
        c = collapse(rows) | {"arm": e["arm"], "pdb_id": e["pdb_id"],
                              "n_res": e["n_res"], "rows": rows,
                              "native": str(native) if native else None}
        results["panel"][e["pdb_id"]] = c
        print(f"  {e['pdb_id']:<6} {e['arm']:<5} ipSAE {c.get('ipsae', float('nan')):.3f} "
              f"(spread {c.get('ipsae_spread', 0):.3f})  "
              f"DockQ {c.get('dockq', float('nan')):.3f}", flush=True)

    for key, root, title in (("negctrl", NEG, "negative control"),
                             ("negctrl_nloop", NEG_NLOOP,
                              "negative control -- full-epitope construct")):
        print(f"\n=== {title} ===", flush=True)
        arms_path = root / "arms.json"
        if not arms_path.exists():
            continue
        for label, a in json.loads(arms_path.read_text()).items():
            pred = root / label / f"boltz_results_{label}" / "predictions" / label
            if not pred.is_dir():
                continue
            rows = score_models(pred, label, cfg, None)
            if not rows:
                continue
            c = collapse(rows) | {"name": a["name"], "target": a["target"],
                                  "expected": a["expected"], "pdb": a["pdb"],
                                  "rows": rows}
            results[key][label] = c
            print(f"  {a['name']:<15} {a['expected']:<9} target {a['target']:<28} "
                  f"ipSAE {c.get('ipsae', float('nan')):.3f} "
                  f"(max {c.get('ipsae_max', float('nan')):.3f})", flush=True)

    OUTJ.write_text(json.dumps(results, indent=1))
    print(f"\nwrote {OUTJ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
