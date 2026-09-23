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
import os
import statistics as stats
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gemmi

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, plddt, prodigy, sasa
from locksmith.io.pdb import contacting_residues, pick_contacting_chain
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
    it a full Fab native against an Fv model leaves ~110 unmatched residues per antibody
    chain, which is exactly when DockQ prints `no identical corresponding chain was found`
    and exits 1. Trimming the native to the same variable domains removes that at source
    rather than by raising `--allowed_mismatches` until something comes out. The Fv span
    comes from ANARCII's `query_start`/`query_end`, indices into the sequence handed to it.

    THE ANTIGEN COPY MUST BE THE ONE THIS Fv ACTUALLY BINDS. `classify()` takes the first
    heavy, first light and first non-antibody chain it meets, with nothing requiring them
    to belong to the same copy. In a crystal with two complexes in the asymmetric unit
    that silently pairs an Fv from one copy with the antigen of the other, and the
    resulting "native" has no antibody-antigen interface at all.

    Measured on 7ST5: DockQ reported `Total DockQ over 1 native interfaces` -- only the
    heavy-light framework -- and `compute()` correctly returned None rather than 0. The
    tell was ipSAE **0.819** alongside a missing DockQ: a high confidence score means the
    chains ARE in contact, so a missing interface had to be the native's fault, not the
    prediction's. A silent zero here would have been far worse than a missing value,
    because it would have entered the distribution as a genuine docking failure.

    So the antigen chain is re-chosen here as the copy with the most contacts to the
    selected Fv, and a native with no antibody-antigen interface is refused outright.
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
    chains = {c.name: [r for r in c if r.find_atom("CA", "*")] for c in st[0]}

    hname, lname = entry["chains"]["H"], entry["chains"]["L"]
    if hname not in chains or lname not in chains:
        return None

    def fv(name):
        res = chains[name]
        n = number(gemmi.one_letter_code([r.name for r in res]).upper())
        return None if n is None else res[n.query_start:n.query_end + 1]

    hres, lres = fv(hname), fv(lname)
    if not hres or not lres:
        return None

    # pick the antigen COPY this Fv actually binds, not the first one in the file
    ag_seq = entry["antigen"]
    cands = {}
    for name, res in chains.items():
        if name in (hname, lname) or not (0.5 * len(ag_seq) <= len(res) <= 2 * len(ag_seq)):
            continue
        sq = gemmi.one_letter_code([r.name for r in res]).upper()
        if number(sq) is not None:
            continue                       # an antibody chain, not the antigen
        cands[name] = res
    best, best_n = pick_contacting_chain(cands, hres + lres)
    if best is None:
        print(f"    {entry['pdb_id']}: no antigen chain contacts the selected Fv; "
              f"refusing to build a native with no interface", file=sys.stderr)
        return None
    if best != entry["chains"]["A"]:
        print(f"    {entry['pdb_id']}: antigen copy {entry['chains']['A']} -> {best} "
              f"({best_n} contacting residues)", file=sys.stderr)

    new = gemmi.Structure()
    new.add_model(gemmi.Model("1"))
    for dest, res in (("A", hres), ("B", lres), ("C", chains[best])):
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


# Scoring one complex means 5 DockQ invocations plus PRODIGY, freeSASA and ipSAE: 40
# complexes take roughly an hour serially. Every one of those is either a subprocess or
# pure Python over per-model paths, so THREADS are safe here where processes would be
# awkward -- subprocess calls release the GIL, `sasa` uses a fresh TemporaryDirectory per
# call, DockQ takes explicit paths, and ipsae keys its output off the PAE path, which is
# unique per (complex, model). Nothing shares a mutable structure.
#
# Processes would be the wrong tool anyway: this project has already killed 239/239
# workers with `Cannot re-initialize CUDA in forked subprocess` by adding a
# ProcessPoolExecutor to a script that had touched CUDA in the parent.
WORKERS = int(os.environ.get("LOCKSMITH_SCORE_WORKERS", "6"))


def main() -> int:
    cfg = load()
    panel = json.loads(PANEL.read_text())
    results: dict = {"panel": {}, "negctrl": {}, "negctrl_nloop": {}}

    print(f"=== calibration panel ({WORKERS} workers) ===", flush=True)

    def one(e: dict):
        label = f"cal_{e['arm']}_{e['pdb_id'].lower()}"
        pred = FOLDS / label / f"boltz_results_{label}" / "predictions" / label
        if not pred.is_dir():
            return None
        native = build_native(e)
        rows = score_models(pred, label, cfg, native)
        if not rows:
            return None
        return collapse(rows) | {"arm": e["arm"], "pdb_id": e["pdb_id"],
                                 "n_res": e["n_res"], "rows": rows,
                                 "native": str(native) if native else None}

    # natives are built serially first: build_native writes a shared cache directory and
    # two threads racing on the same output path is a real collision, unlike the metrics
    for e in panel:
        try:
            build_native(e)
        except Exception:                                    # noqa: BLE001
            pass

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for e, c in zip(panel, ex.map(one, panel)):
            if c is None:
                print(f"  {e['pdb_id']}: no scorable models", flush=True)
                continue
            results["panel"][e["pdb_id"]] = c
            print(f"  {e['pdb_id']:<6} {e['arm']:<5} "
                  f"ipSAE {c.get('ipsae', float('nan')):.3f} "
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
