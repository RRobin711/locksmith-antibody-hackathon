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
import argparse, json, re, shutil, sys, tempfile
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.submit.package import HEADERS
from locksmith.types import Provenance, Structure

FAIL: list[str] = []

# Metrics whose value a packaged document is allowed to assert. Any table row naming
# one of these must carry a number matching what we just recomputed from the package.
_DOC_METRICS = ("ipsae", "dockq", "dg", "contacts", "iface_plddt", "cdr_sasa",
                "netsolp", "cdrh3_identity")

# Strings that were wrong once and must never come back. Each is a real regression:
# a document describing something the package does not contain. Keyed to the reason so a
# future reader knows what they are looking at rather than deleting an opaque list.
# Convention keys, read from the live config so this cannot drift away from it.
try:
    _CONVENTION_KEYS = set(load().conventions) | {"band_value"}
except Exception:  # config unreadable -- fall back to checking every row
    _CONVENTION_KEYS = {"band_value"}

_BANNED = {
    "works is 15": "DockQ's minimum --allowed_mismatches is 16, measured; 15 exits 1",
    "our 15 substitutions": "the 15 was never verified and is not the design's count",
    "the identical 0.816": "0.816 belongs to the pre-N55Q diffusion sweep, not the submission",
    "A,B  DockQ 0.931": "0.931/0.723/0.794 are the pre-N55Q sweep model_0, not the submitted design",
    "0 (submitted)": "mislabelled the diffusion sweep's model 0 as the submitted structure",
}


def check_docs_against_scores(base, ch: int, raw: dict, name: str,
                              per_iface: dict | None = None) -> None:
    """Every metric a packaged doc asserts must match the recomputed value.

    This guards a class of failure, not one typo. The class: a package file is written
    by a GENERATOR, so correcting the file by hand is silently undone the next time
    anything rebuilds -- measured 2026-09-24, a corrected DockQ instruction reverted
    **+11 -61** by the next packaging run, restoring text telling a grader to pass
    `--allowed_mismatches 15`, which exits 1 and prints nothing under a SS7.2 hard cutoff
    (a route to 0 instead of 94). The template lived in TWO regions of
    `scripts/57_build_submission.py` -- a `metrics_md` list ~line 125 and a `repro_md`
    f-string ~line 384 -- and one line of the second had been edited during the same pass,
    four lines below the paragraph left wrong. Fix at the generator; verify from the
    REBUILT artefact, never from the edit.

    CHEAPEST DETECTOR, needing no knowledge of the code: a modification-time spread inside
    one generated directory. The orphan below sat a full day older than its siblings --
        stat -c '%y %n' submission/*/*/docs/*.md submission/*/*/metrics/scores.md
    Healthy is all timestamps within seconds of each other.

    A WARNING ABOUT EXPLANATIONS, from the same incident. The per-interface values
    0.931/0.723/0.794 were first "explained" as the AB **LRMSD** column misread as DockQ.
    AB's LRMSD genuinely IS 0.931, so the story is self-consistent -- and wrong. All three
    match `model_0` of the pre-N55Q diffusion sweep (**0.9307 / 0.7229 / 0.7945**), a
    structure differing from the shipped one at a single position (heavy 55, N->Q). It was
    caught only because the LRMSD story accounted for ONE of three numbers. A coincidence
    that explains part of the evidence terminates the search; require an explanation to
    cover every observation before accepting it -- and a document can also simply be orphaned, left behind by an
    earlier generator after the design it describes was replaced. Both happened here.
    Challenge 2's reproducing_our_numbers.md was written by scripts/75 and never rewritten
    by scripts/105 when the bb_8_0 design was swapped in, so it shipped asserting
    ipSAE 0.781 and NetSolP 0.570 while the structure beside it scored 0.904 and 0.555.
    Nothing caught it, because every per-file check passed: the file existed, parsed and
    was internally consistent. Only a cross-check against recomputed numbers finds it.

    Covers THREE contexts, not just tables. Table rows were the first version and were
    the weak half: every number that has actually burned this project lived in prose or a
    fenced block -- 0.816, the per-interface 0.931/0.723/0.794, and a hardcoded "40.0%"
    alternative-convention figure sitting beside a parameterised one. So:

      * table rows        -- any line starting with '|'
      * prose             -- a sentence naming a metric in backticks AND carrying a number
      * fenced blocks     -- TOTALS ONLY (a line containing "total"), because a command
                            line carries the reference filename's digits and a
                            per-interface row legitimately differs from the aggregate

    Read a pass narrowly. A number is accepted if ANY figure on the line matches, since
    prose legitimately carries section refs and cutoffs beside the value, so this catches
    a value being flatly WRONG rather than proving every number in a sentence is right.
    And it cannot catch a number that is a VALID value of a different structure -- which
    is what 0.931/0.723/0.794 were. `_BANNED` covers those by name, and being a grep it
    only ever catches a repeat of a mistake already made once.
    """
    docs = sorted((base / "docs").glob("*.md")) + sorted((base / "metrics").glob("*.md"))
    for doc in docs:
        try:
            text = doc.read_text()
        except OSError as e:
            FAIL.append(f"Challenge {ch}: cannot read {doc.name}: {e}")
            continue
        in_fence = False
        for ln_no, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            is_row = line.lstrip().startswith("|")
            has_metric_tick = any(f"`{m}`" in line for m in _DOC_METRICS)
            # A fenced line is tool output: check it whenever it carries a metric name at
            # all, backticked or not, because pasted output prints bare names.
            if in_fence:
                # A fence is pasted tool output. Most of its lines cannot be checked
                # against the aggregate: a shell command line carries the reference
                # filename's digits, and a PER-INTERFACE row legitimately differs from
                # the global aggregate (A-B 0.8716 vs global 0.7996 -- both correct).
                # Only an explicit total is comparable, so only totals are checked here.
                # This is a real gap: the 0.931/0.723/0.794 regression lived in exactly
                # those per-interface rows and a numeric check CANNOT catch it, because
                # the numbers were valid values of a different structure. `_BANNED` is
                # what covers that case, and it is a grep, not a recomputation.
                if line.lstrip().startswith("$"):
                    continue
                if "total" not in line.lower():
                    continue
                if not any(m in line.lower() for m in _DOC_METRICS):
                    continue
            elif not (is_row or has_metric_tick):
                continue
            # A conventions table names a metric but asserts a SETTING, not a value
            # (`netsolp` / `netsolp_chain_agg` / `min`). Those rows carry unrelated
            # numbers -- section refs, dates, the other chain's score -- so checking
            # them produces nothing but false alarms. Identified from the live config
            # rather than a hand-kept list, so a new convention cannot silently
            # reintroduce the noise.
            if any(f"`{k}`" in line for k in _CONVENTION_KEYS):
                continue
            for m in _DOC_METRICS:
                if f"`{m}`" not in line and not (in_fence and m in line.lower()):
                    continue
                truth = raw.get(m)
                if truth is None:
                    continue
                nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", line)]
                if not nums:
                    continue
                t = float(truth)
                # Match at whatever precision the document chose to print, so a doc
                # showing 0.904 for a true 0.9041 passes and one showing 0.781 does not.
                ok = any(abs(n - t) <= max(5e-4, abs(t) * 1e-3)
                         or round(n, 3) == round(t, 3)
                         or (abs(t) >= 10 and round(n, 1) == round(t, 1))
                         for n in nums)
                if not ok:
                    FAIL.append(
                        f"Challenge {ch} {doc.name}:{ln_no}: asserts `{m}` = "
                        f"{nums} but the package recomputes {t:.4f}. A packaged document "
                        f"is describing a design this package does not contain -- most "
                        f"likely left behind by an earlier generator."
                    )

    # ---- per-interface DockQ -------------------------------------------------
    # The blind spot this closes: "A,B  DockQ 0.931" is not wrong ARITHMETICALLY -- it is
    # a real measurement of a different structure (model_0 of the pre-N55Q diffusion
    # sweep), so no comparison against the GLOBAL aggregate can reject it. Only comparing
    # each interface against its own recomputed value can. Matches lines of the shape
    # "A,B  DockQ 0.931" or "A-B = 0.723" anywhere in the document, fences included.
    for doc in docs:
        text = doc.read_text()
        for ln_no, line in enumerate(text.splitlines(), 1):
            for m in re.finditer(r"\b([A-Z])\s*[,\-]\s*([A-Z])\b[^0-9\n]{0,24}?(\d\.\d+)", line):
                key = "".join(sorted((m.group(1), m.group(2))))
                if key not in (per_iface or {}):
                    continue
                claimed, truth = float(m.group(3)), per_iface[key]
                if abs(claimed - truth) > max(5e-4, abs(truth) * 1e-3):
                    FAIL.append(
                        f"Challenge {ch} {doc.name}:{ln_no}: claims interface {key} "
                        f"DockQ {claimed} but this package recomputes {truth:.4f}. "
                        f"Per-interface values are not comparable to the aggregate, so "
                        f"only this check can catch them -- and a wrong one here is "
                        f"typically a real measurement of a DIFFERENT structure."
                    )

    for doc in docs:
        text = doc.read_text()
        for bad, why in _BANNED.items():
            if bad in text:
                FAIL.append(f"Challenge {ch} {doc.name}: contains retracted text "
                            f"{bad!r} -- {why}. It was corrected at the generator; if it "
                            f"is back, something regenerated from a stale template.")




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
    # S6.3.1: Keytruda for Ch1, human germline for Ch2. Passing the challenge through
    # is the whole point -- validating a Ch2 package against Keytruda's CDR-H3 would
    # produce a plausible number for the wrong question.
    raw["cdrh3_identity"] = novelty.compute(seqs["heavy"], challenge=challenge).value
    # Which metrics a challenge scores is a property of the RUBRIC, so read it from
    # config rather than hardcoding `challenge == 1`. S5.2 excludes DockQ from
    # Challenge 2 (there is no reference structure for a de novo design).
    per_iface: dict[str, float] = {}
    if challenge in cfg.bands()["dockq"].challenges:
        native = Structure(pdb=ref, provenance=Provenance.EXPERIMENT, label="reference")
        _dq = dockq.compute(st, native,
                            allowed_mismatches=c["dockq_allowed_mismatches"],
                            interface_agg=c["dockq_interface_agg"])["dockq"]
        raw["dockq"] = _dq.value
        # Per-interface truth, parsed back out of the detail string
        # ("agg=global AB=0.8716 AC=0.7308 BC=0.7963 (unrounded; ...)").
        # Needed because a per-interface value legitimately DIFFERS from the aggregate,
        # so the aggregate check cannot validate it -- see check_docs_against_scores.
        per_iface = {m.group(1): float(m.group(2))
                     for m in re.finditer(r"\b([A-Z]{2})=(\d+\.\d+)", _dq.detail or "")}
    sc = evaluate(raw, challenge=challenge, cfg=cfg)
    return {"raw": raw, "scored": sc, "per_iface": per_iface}


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
            check_docs_against_scores(cdir, ch, res["raw"], name,
                                      per_iface=res.get("per_iface") or {})
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
