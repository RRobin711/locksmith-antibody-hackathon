#!/usr/bin/env python3
"""Fold real antibody-antigen complexes through OUR pipeline, so our numbers get a scale.

THE GAP THIS CLOSES. Every metric this project reports is uncalibrated. Is ipSAE 0.864
good? Is DockQ 0.816? We have exactly one external reference point -- pembrolizumab -- and
every other number floats relative to nothing. The band edge at 0.80 is a number the
handbook asserts; it is not a number anyone here has ever located in a distribution.

This script builds the distribution. It folds N real, crystallised antibody-antigen
complexes through the identical pipeline and scores them on the same metrics, so every
number in the submission can be quoted as a PERCENTILE of real complexes.

--------------------------------------------------------------------------------------
THE SPLIT THAT MAKES IT MEANINGFUL
--------------------------------------------------------------------------------------
Boltz-2's training cutoff is **2023-06-01 on PDB *release* date** -- release, not
deposition, read from the paper rather than a search summary. A panel mixing memorised
and novel complexes produces a distribution that means nothing, because they are
different tasks:

  * **pre-cutoff**  -- the model has seen the answer. This is the CEILING: what these
    metrics look like when prediction is closer to recall.
  * **post-cutoff** -- genuinely novel. This is the honest reference for a de novo design.

Quoting a de novo design against the pre-cutoff distribution would flatter it. The
comparison that means something is against post-cutoff.

--------------------------------------------------------------------------------------
WHY THE ARMS ARE SAMPLED THE WAY THEY ARE
--------------------------------------------------------------------------------------
Both arms are drawn by the SAME RCSB query, sorted by release date, taking the entries
*closest to the cutoff on each side*. That is deliberate. If the pre arm were classic
1990s structures and the post arm 2025 ones, the arms would differ in resolution,
refinement practice, target fashion and construct design as well as in memorisation, and
any gap between them would be uninterpretable. Sampling from either side of one date
makes the cutoff the only systematic difference -- as close to a natural experiment as
this gets.

Filters (identical for both arms): >=3 protein entities, resolution <= 3.0 A.

--------------------------------------------------------------------------------------
CONSTRUCT AND SEQUENCE DISCIPLINE
--------------------------------------------------------------------------------------
  * **Chains are typed by ANARCII, never by chain letter.** Whatever numbers as `H` is
    heavy, `K`/`L` is light, anything that does not number and is 60-400 residues is the
    antigen. Chain IDs are not a convention anyone in the PDB agreed to -- 5GGS puts a
    second heavy chain in 'C'.
  * **Antibodies are trimmed to the variable domain (Fv).** Our designs are Fv, and a
    panel folded as Fab is not the same pipeline: this project already measured the two
    differing on the same real pair (Fab ipSAE 0.776 vs Fv 0.842). Trimming also discards
    the constant domain, where most of the crystallographic disorder lives.
  * **The antigen is rebuilt from SEQRES, trimmed to the resolved span.** A
    coordinate-derived sequence with an internal deletion is a chimera: folding it
    predicts a protein with a loop excised and the ends fused. This project measured that
    error moving one DockQ **0.064 -> 0.370**. Terminal truncation is harmless (the
    crystal simply did not resolve the ends) and is left truncated, so we do not pay GPU
    time folding tags nobody observed.
  * **Deduplicated on antigen sequence**, so ten Fabs against one spike protein cannot
    masquerade as ten independent calibration points.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import gemmi

from locksmith.numbering import number

OUT = Path("runs/calibration")
REFDIR = OUT / "pdb"
CUTOFF = "2023-06-01"          # Boltz-2 training cutoff, PDB *release* date
TARGET_PER_ARM = 20
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

# Already prepared by scripts/13 with SEQRES-derived sequences; seeded into the post arm
# so the existing novelty work and this panel refer to the same structures.
PREPARED = Path("data/refs/postcutoff/prepared/manifest_seqres.json")


def discover(arm: str, rows: int = 120) -> list[str]:
    """Candidate PDB IDs on one side of the cutoff, nearest the cutoff first."""
    op, direction = ("greater", "asc") if arm == "post" else ("less", "desc")
    q = {
        "query": {"type": "group", "logical_operator": "and", "nodes": [
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_accession_info.initial_release_date",
                "operator": op, "value": CUTOFF}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_entry_info.polymer_entity_count_protein",
                "operator": "greater_or_equal", "value": 3}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_entry_info.resolution_combined",
                "operator": "less_or_equal", "value": 3.0}},
            {"type": "terminal", "service": "full_text",
             "parameters": {"value": "Fab complex antigen"}}]},
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": rows},
            "sort": [{"sort_by": "rcsb_accession_info.initial_release_date",
                      "direction": direction}]},
    }
    req = urllib.request.Request(
        SEARCH, data=json.dumps(q).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return [x["identifier"] for x in d.get("result_set", [])]


def fetch(pdb_id: str) -> Path | None:
    REFDIR.mkdir(parents=True, exist_ok=True)
    p = REFDIR / f"{pdb_id.lower()}.pdb"
    if p.exists() and p.stat().st_size > 2000:
        return p
    try:
        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
        with urllib.request.urlopen(url, timeout=90) as r:
            p.write_bytes(r.read())
        return p
    except Exception:                                        # noqa: BLE001
        return None                # large entries are cif-only; skipping them is fine


def seqres_map(pdb: Path) -> dict[str, str]:
    """Chain -> full SEQRES sequence, parsed from the raw fixed-column records.

    gemmi exposes SEQRES through entities, but `setup_entities()` reassigns subchains and
    the entity<->chain correspondence is not something to guess at when a wrong answer is
    silent. The records are unambiguous: chain id at column 12, residue names from 20 on.
    """
    out: dict[str, list[str]] = {}
    for line in pdb.read_text(errors="ignore").splitlines():
        if line.startswith("SEQRES"):
            out.setdefault(line[11], []).extend(line[19:].split())
    return {k: gemmi.one_letter_code(v).upper() for k, v in out.items()}


def resolved_span(coord: str, full: str) -> str | None:
    """SEQRES trimmed to the span between the first and last RESOLVED residue.

    `coord` is `full` with residues deleted. Internal deletions are fatal to fold; terminal
    truncation is harmless. So fill the interior from SEQRES and do not extend past what
    the crystal resolved. A global alignment locates `coord` inside `full`; the span from
    the first to the last aligned SEQRES index is the answer.
    """
    from Bio import Align

    if not full or len(full) < len(coord):
        return None
    aligner = Align.PairwiseAligner(mode="global", match_score=1, mismatch_score=-1,
                                    open_gap_score=-2, extend_gap_score=-0.1)
    try:
        aln = aligner.align(full, coord)[0]
    except Exception:                                        # noqa: BLE001
        return None
    blocks = aln.aligned[0]
    if len(blocks) == 0:
        return None
    span = full[blocks[0][0]:blocks[-1][1]]
    # The resolved span must contain every coordinate residue, or the alignment put them
    # somewhere they are not and the "fill" would be fiction.
    return span if len(span) >= len(coord) else None


def classify(pdb: Path) -> dict | None:
    """Type every chain by ANARCII and return one Fv/Fv/antigen triple, or None."""
    st = gemmi.read_structure(str(pdb))
    st.setup_entities()
    seqres = seqres_map(pdb)
    heavy = light = antigen = None
    hname = lname = aname = None
    for ch in st[0]:
        res = [r for r in ch if r.find_atom("CA", "*")]
        if len(res) < 50:
            continue
        coord = gemmi.one_letter_code([r.name for r in res]).upper()
        if "X" in coord or len(coord) > 900:
            continue
        n = number(coord)
        t = n.chain_type if n else None
        if t == "H" and heavy is None:
            heavy, hname = n.fv, ch.name
        elif t in ("K", "L") and light is None:
            light, lname = n.fv, ch.name
        elif t is None and antigen is None and 60 <= len(coord) <= 400:
            filled = resolved_span(coord, seqres.get(ch.name, ""))
            if filled is None:
                continue          # cannot repair -> refuse rather than fold a chimera
            antigen, aname = filled, ch.name
    if not (heavy and light and antigen):
        return None
    return {"heavy": heavy, "light": light, "antigen": antigen,
            "chains": {"H": hname, "L": lname, "A": aname},
            "n_res": len(heavy) + len(light) + len(antigen)}


def build_arm(arm: str, seed: list[dict] | None = None) -> list[dict]:
    accepted: list[dict] = list(seed or [])
    seen_ag = {x["antigen"] for x in accepted}
    reasons: dict[str, int] = {}
    for pid in discover(arm):
        if len(accepted) >= TARGET_PER_ARM:
            break
        p = fetch(pid)
        if p is None:
            reasons["no pdb-format file"] = reasons.get("no pdb-format file", 0) + 1
            continue
        try:
            info = classify(p)
        except Exception as e:                               # noqa: BLE001
            reasons[f"parse: {type(e).__name__}"] = reasons.get(f"parse: {type(e).__name__}", 0) + 1
            continue
        if info is None:
            reasons["no Fv/Fv/antigen triple"] = reasons.get("no Fv/Fv/antigen triple", 0) + 1
            continue
        if info["antigen"] in seen_ag:
            reasons["duplicate antigen"] = reasons.get("duplicate antigen", 0) + 1
            continue
        seen_ag.add(info["antigen"])
        info |= {"pdb_id": pid, "arm": arm, "pdb": str(p)}
        accepted.append(info)
        print(f"  {pid}  H{len(info['heavy']):>4} L{len(info['light']):>4} "
              f"Ag{len(info['antigen']):>4}  total {info['n_res']:>4}", flush=True)
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"    rejected {v:>3}: {k}", flush=True)
    return accepted


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "panel.json"
    if manifest.exists() and "--rebuild" not in sys.argv:
        panel = json.loads(manifest.read_text())
        print(f"reusing cached panel of {len(panel)} complexes")
    else:
        seed = []
        if PREPARED.exists():
            for pid, v in json.loads(PREPARED.read_text()).items():
                seed.append({"pdb_id": pid, "arm": "post", "pdb": v["prepared"],
                             "heavy": v["heavy_fv"], "light": v["light_fv"],
                             "antigen": v["antigen"],
                             "chains": {"H": "A", "L": "B", "A": "C"},
                             "n_res": len(v["heavy_fv"]) + len(v["light_fv"])
                                      + len(v["antigen"])})
            print(f"seeded post arm with {len(seed)} already-prepared complexes\n")

        print(f"--- post-cutoff arm (released after {CUTOFF}) ---", flush=True)
        post = build_arm("post", seed=seed)
        print(f"\n--- pre-cutoff arm (released before {CUTOFF}) ---", flush=True)
        pre = build_arm("pre")
        panel = pre + post
        manifest.write_text(json.dumps(panel, indent=1))

    pre = [x for x in panel if x["arm"] == "pre"]
    post = [x for x in panel if x["arm"] == "post"]
    sizes = sorted(x["n_res"] for x in panel)
    print(f"\npanel: {len(pre)} pre-cutoff + {len(post)} post-cutoff = {len(panel)}")
    print(f"construct size: median {sizes[len(sizes)//2]} residues, "
          f"range {sizes[0]}-{sizes[-1]}")
    print(f"wrote {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
