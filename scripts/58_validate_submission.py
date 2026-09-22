#!/usr/bin/env python3
"""Validate a PACKAGED submission from the files alone. §11.4 step 4.

    python scripts/58_validate_submission.py <TEAM_NAME dir> [--reference 5ggs.pdb]

Reads ONLY the packaged folder. It does not import anything from `runs/`, does not
consult any cached score, and re-derives every number from the three files per design.
That is the whole point: the evaluator has the package and nothing else, so a check
that reuses our own intermediate state proves nothing about what they will see.

The one unavoidable external input is the DockQ reference, PDB 5GGS, which is public
and named in §3.1. It is a CLI argument so the validator cannot silently fall back to
anything of ours.

FAILS LOUDLY. Any structural problem, any missing file, any hard-cutoff failure exits
non-zero with the reason. Nothing here warns.
"""
from __future__ import annotations
import argparse, json, shutil, sys, tempfile
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.submit.package import HEADERS
from locksmith.types import Provenance, Structure

FAIL: list[str] = []


def check(cond: bool, msg: str) -> bool:
    if not cond:
        FAIL.append(msg)
    return cond


def read_fasta(p: Path) -> dict[str, str]:
    lines = p.read_text().splitlines()
    check(len(lines) == 6, f"{p.name}: expected exactly 3 records (6 lines), got {len(lines)}")
    got = tuple(lines[0::2])
    check(got == HEADERS, f"{p.name}: headers {got} != required {HEADERS} (§4.2.2)")
    return dict(zip(("heavy", "light", "antigen"), lines[1::2])) if len(lines) == 6 else {}


def validate_design(struct_dir: Path, seq_dir: Path, name: str, ref: Path,
                    challenge: int) -> dict:
    cfg = load(); c = cfg.conventions
    pdb = struct_dir / f"{name}_complex.pdb"
    pae = struct_dir / f"{name}_pae.json"
    fa = seq_dir / f"{name}.fasta"
    for f in (pdb, pae, fa):
        check(f.is_file(), f"MISSING REQUIRED FILE: {f.relative_to(struct_dir.parents[1])} "
                           f"(§7.1 step 1: 'Missing files = disqualification')")
    if FAIL:
        return {}
    seqs = read_fasta(fa)
    if not seqs:
        return {}

    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae,
                   label=name, predictor="unknown")
    raw = {k: v.value for k, v in prodigy.compute(st).items()}
    raw["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                 dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    raw["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    raw["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    raw["netsolp"] = netsolp.compute(seqs["heavy"], seqs["light"],
                                     construct=c.get("netsolp_construct", "fv"))["netsolp"].value
    raw["cdrh3_identity"] = novelty.compute(seqs["heavy"]).value
    if challenge == 1:
        native = Structure(pdb=ref, provenance=Provenance.EXPERIMENT, label="reference")
        raw["dockq"] = dockq.compute(st, native,
                                     allowed_mismatches=c["dockq_allowed_mismatches"],
                                     interface_agg=c["dockq_interface_agg"])["dockq"].value
    sc = evaluate(raw, challenge=challenge, cfg=cfg)
    return {"raw": raw, "scored": sc}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("--reference", type=Path,
                    default=Path("data/refs/prepared/5ggs_ABZ.pdb"))
    ap.add_argument("--keep-in-place", action="store_true",
                    help="validate the package where it sits (will litter structures/ "
                         "with ipSAE scratch files); default is an isolated copy")
    a = ap.parse_args()
    team = a.package.name

    # VALIDATE A COPY, NEVER THE ARTEFACT. `ipsae.py` writes its scratch .txt/.pml
    # next to the PDB it is handed, so validating the real package used to leave three
    # stray files in `structures/` -- which §4.2.1 does not list and which the packager
    # now refuses. Reading a thing must not modify it. The copy is also a better test:
    # it proves the package works somewhere other than where it was built.
    _scratch = None
    if a.package.is_dir() and not a.keep_in_place:
        _scratch = Path(tempfile.mkdtemp(prefix="validate_"))
        shutil.copytree(a.package, _scratch / team)
        a.package = _scratch / team
        print(f"(validating an isolated copy at {a.package})")
    cfg = load()

    print(f"validating {a.package}  (team '{team}')")
    print(f"conventions: band_value={cfg.band_value}, "
          f"dockq_interface_agg={cfg.conventions['dockq_interface_agg']}, "
          f"netsolp_construct={cfg.conventions.get('netsolp_construct')}, "
          f"netsolp_chain_agg={cfg.conventions['netsolp_chain_agg']}")
    print()
    check(a.package.is_dir(), f"{a.package} is not a directory")
    if FAIL:
        print("FAIL:", *FAIL, sep="\n  "); return 1

    any_design = False
    for ch in (1, 2):
        cdir = a.package / f"{team}_Challenge{ch}"
        if not cdir.is_dir():
            print(f"Challenge {ch}: no folder — skipped (not submitted)")
            continue
        sdir, qdir = cdir / "structures", cdir / "sequences"
        check(sdir.is_dir(), f"Challenge {ch}: missing structures/")
        check(qdir.is_dir(), f"Challenge {ch}: missing sequences/")
        if FAIL:
            break
        names = sorted(p.name.replace("_complex.pdb", "") for p in sdir.glob("*_complex.pdb"))
        check(len(names) == 1,
              f"Challenge {ch}: {len(names)} designs found; the handbook allows one per "
              f"challenge")
        for name in names:
            any_design = True
            print(f"--- Challenge {ch}: {name} ---")
            res = validate_design(sdir, qdir, name, a.reference, ch)
            if not res:
                continue
            sc = res["scored"]
            print(sc.summary() if hasattr(sc, "summary") else "")
            for m, v in sorted(res["raw"].items()):
                band = sc.bands.get(m, "-")
                print(f"  {m:16s} {v:>10.3f}   band={band:6s} sub={sc.sub.get(m, float('nan')):.1f}")
            print(f"  categories: " + ", ".join(f"{k}={v:.3f}" for k, v in sc.categories.items()))
            print(f"  VIABLE: {sc.viable}    FINAL: {sc.final}")
            if sc.failing:
                FAIL.append(f"Challenge {ch} {name}: NON-VIABLE — fails hard cutoffs "
                            f"{sc.failing} (§7.2)")
            if sc.unknown:
                FAIL.append(f"Challenge {ch} {name}: metrics could not be computed: "
                            f"{sc.unknown}")
            # §7.2: a non-viable design is ranked below all viable ones, so its final
            # score is not comparable and must never be quoted bare.
            if sc.viable is not True and sc.final is not None:
                print(f"  NOTE: final {sc.final} is NOT comparable to a viable design's "
                      f"score (§7.2)")
    check(any_design, "no designs found in the package")

    pitch = a.package / "pitch"
    if not (pitch.is_dir() and any(pitch.glob("*.pptx"))):
        FAIL.append(f"missing {team}/pitch/{team}_presentation.pptx (§4.4, worth 50 points)")

    print()
    if FAIL:
        print(f"VALIDATION FAILED ({len(FAIL)}):")
        for f in FAIL:
            print(f"  - {f}")
        return 1
    print("VALIDATION PASSED")
    if _scratch:
        shutil.rmtree(_scratch, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
