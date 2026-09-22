#!/usr/bin/env python3
"""Gate 0 -- calibrate the scoring harness against structures we know the answer to.

Build the judge before the contestant.  We cannot choose between designs without
reproducing the organisers' scoring, and we cannot trust our reproduction until it
has been run on molecules whose answers are already known.

Four subjects:
  5GGS A/B/Z   native pembrolizumab-PD-1      the reference: a real, approved drug
  5GGS C/D/Y   the second copy in the ASU     same molecule -> measures crystallographic spread
  5WT9         nivolumab-PD-1                 an independent real anti-PD-1
  DECOY        pembrolizumab Fab + the PD-1   a non-interface: the harness MUST reject it
               copy it does not bind

ipSAE and interface pLDDT are UNDEFINED on experimental structures (no PAE; the
B-factor column is thermal displacement, not pLDDT) and are reported as skipped
rather than computed.  They are exercised in Phase 1 on predicted structures.
"""
from __future__ import annotations

import sys
from pathlib import Path

from locksmith.config import load
from locksmith.io.pdb import chains, extract_complex
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.numbering import number
from locksmith.score import evaluate
from locksmith.types import Provenance, Structure

PREP = Path("data/refs/prepared")
# Verified by contact analysis: in 5GGS, Fab A/B binds antigen Z and Fab C/D binds
# antigen Y.  The obvious A/B/Y + C/D/Z reading is WRONG and yields complexes with
# zero interface -- see the session doc for 2026-09-15.
SUBJECTS = {
    "5GGS_ABZ": ("data/refs/5ggs.pdb", "A", "B", "Z"),
    "5GGS_CDY": ("data/refs/5ggs.pdb", "C", "D", "Y"),
    "5WT9":     ("data/refs/5wt9.pdb", "H", "L", "G"),
    "DECOY":    ("data/refs/5ggs.pdb", "A", "B", "Y"),   # non-binding antigen copy
}


def build() -> dict[str, Structure]:
    PREP.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, (src, h, l, a) in SUBJECTS.items():
        dest = PREP / f"{name}.pdb"
        cmap = extract_complex(src, dest, heavy=h, light=l, antigen=a)
        out[name] = Structure(pdb=dest, provenance=Provenance.EXPERIMENT,
                              label=name, chain_map=cmap)
    return out


def measure(s: Structure, native: Structure | None, cfg) -> dict:
    conv = cfg.conventions
    raw: dict = {}
    raw.update(prodigy.compute(s))
    raw.update(ipsae.compute(s, pae_cutoff=conv["ipsae_pae_cutoff"],
                             dist_cutoff=conv["ipsae_dist_cutoff"]))
    raw["iface_plddt"] = plddt.compute(s, cutoff=conv["interface_dist_cutoff"])
    sa = sasa.compute(s)
    raw["cdr_sasa"] = sa[f"cdr_sasa_{conv['cdr_sasa_state']}"]
    raw["_cdr_sasa_unbound"] = sa["cdr_sasa_unbound"]
    raw["_cdr_sasa_buried"] = sa["cdr_sasa_buried"]
    heavy = chains(str(s.pdb))["A"].seq
    raw["cdrh3_identity"] = novelty.compute(heavy)
    raw.update(netsolp.compute(heavy, chains(str(s.pdb))["B"].seq))
    if native is not None:
        raw.update(dockq.compute(s, native))
    return raw


def main() -> int:
    cfg = load()
    structs = build()
    native = structs["5GGS_ABZ"]
    print(f"conventions: {dict(cfg.conventions)}\n")

    results = {}
    for name, s in structs.items():
        raw = measure(s, native, cfg)
        scored = evaluate({k: v for k, v in raw.items() if not k.startswith("_")},
                          challenge=1, cfg=cfg)
        results[name] = (raw, scored)
        print(f"\033[1m=== {name} ===\033[0m")
        print(scored.table())
        print(f"  CDR SASA unbound {raw['_cdr_sasa_unbound'].value}  "
              f"buried on binding {raw['_cdr_sasa_buried'].value} A^2")
        for k, v in raw.items():
            if hasattr(v, "skipped_reason") and v.skipped_reason:
                print(f"  skipped {k}: {v.skipped_reason}")
        print(f"  viable={scored.viable}  failing={scored.failing or '-'}  "
              f"thin margin={scored.thin_margin or '-'}")
        print()

    # ---- Gate 0 assertions -------------------------------------------------
    print("\033[1m=== GATE 0 ===\033[0m")
    checks: list[tuple[str, bool, str]] = []

    self_dockq = dockq.compute(native, native)["dockq"].value
    checks.append(("DockQ(5GGS, 5GGS) == 1.000", self_dockq == 1.0, str(self_dockq)))

    h = chains(str(native.pdb))["A"].seq
    ident = novelty.compute(h).value
    checks.append(("CDR-H3 identity(5GGS, Keytruda) == 100%", ident == 100.0, f"{ident}%"))

    # Pembrolizumab MUST fail the novelty gate: its CDR-H3 is 100% identical to
    # Keytruda's because it IS Keytruda.  The novelty gate exists to reject
    # trivial clones, so the reference failing it is the metric working, not
    # the harness breaking.  Exclude it and require every other gate to pass.
    ref_raw, ref_scored = results["5GGS_ABZ"]
    binding_fail = [f for f in ref_scored.failing if f != "cdrh3_identity"]
    checks.append(("native pembrolizumab passes every binding gate",
                   not binding_fail, f"failing: {binding_fail or 'none'}"))
    checks.append(("native pembrolizumab FAILS novelty (it is the clone)",
                   "cdrh3_identity" in ref_scored.failing,
                   f"identity {ref_raw['cdrh3_identity'].value}%"))

    _, decoy = results["DECOY"]
    checks.append(("decoy is rejected", bool(decoy.failing),
                   f"failing: {decoy.failing or 'NONE - harness does not discriminate!'}"))

    a = results["5GGS_ABZ"][0]["dg"].value
    b = results["5GGS_CDY"][0]["dg"].value
    checks.append((f"two ASU copies agree on dG (spread {abs(a-b):.2f} kcal/mol)",
                   abs(a - b) < 1.0, f"{a} vs {b}"))

    ok = True
    for label, passed, detail in checks:
        print(f"  [{'\033[32m ok \033[0m' if passed else '\033[31mFAIL\033[0m'}] "
              f"{label:<52} {detail}")
        ok &= passed

    print(f"\n  unknown metrics (not yet implemented / undefined here): "
          f"{ref_scored.unknown}")
    print("\n" + ("\033[32mGate 0 checks passed.\033[0m" if ok
                  else "\033[31mGate 0 FAILED.\033[0m"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
