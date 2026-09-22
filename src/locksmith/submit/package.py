"""Build the handbook's submission tree (§4.1-§4.2) and assert on the bytes.

The rule throughout: **validate the artifacts, not the pipeline that produced them.**
Everything here checks the files as they will be read by someone who has never seen
`runs/`, because that is the only thing the evaluator sees. §4.1 warns that submissions
not following the exact structure "will fail automated validation and may be
disqualified", so every requirement is an assertion rather than a convention.

Layout, verbatim from §4.1:

    TEAM_NAME/
      TEAM_NAME_Challenge1/
        structures/  design_X_complex.pdb , design_X_pae.json
        sequences/   design_X.fasta
        metrics/     (optional)
        docs/        (optional)
      TEAM_NAME_Challenge2/
      pitch/         TEAM_NAME_presentation.pptx

`design_X` prefixes must match between the PDB and the PAE JSON. §4.2.2 fixes the three
FASTA headers exactly and §4.2.2's chain note fixes A=heavy, B=light, C=antigen.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import gemmi

from locksmith.submit.pae import write_pae_json

HEADERS = (">Heavy_Chain", ">Light_Chain", ">Antigen")
CHAIN_OF = {">Heavy_Chain": "A", ">Light_Chain": "B", ">Antigen": "C"}


class PackagingError(RuntimeError):
    """Raised loudly. A packaging problem must never degrade to a warning."""


@dataclass(frozen=True)
class Design:
    name: str                 # e.g. "design_1"
    heavy: str
    light: str
    antigen: str
    pdb: Path
    pae_npz: Path
    plddt_npz: Path | None = None
    confidence_json: Path | None = None


def _chains(pdb: Path) -> dict[str, list[str]]:
    st = gemmi.read_structure(str(pdb))
    st.remove_hydrogens()
    out: dict[str, list[str]] = {}
    for ch in st[0]:
        seq = []
        for r in ch:
            if r.find_atom("CA", "*"):
                seq.append(gemmi.find_tabulated_residue(r.name).one_letter_code.upper())
        if seq:
            out[ch.name] = seq
    return out


def write_fasta(design: Design, path: Path) -> Path:
    """Exactly three records, exact headers, in the handbook's order."""
    body = "".join(f"{h}\n{s}\n" for h, s in
                   zip(HEADERS, (design.heavy, design.light, design.antigen)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    # Assert on the bytes we just wrote, not on the intent above.
    lines = path.read_text().splitlines()
    if len(lines) != 6:
        raise PackagingError(f"{path.name}: expected 6 lines (3 records), got {len(lines)}")
    got = tuple(lines[0::2])
    if got != HEADERS:
        raise PackagingError(f"{path.name}: headers are {got}, must be exactly {HEADERS} "
                             f"in that order (§4.2.2)")
    for h, s in zip(HEADERS, lines[1::2]):
        if not s or not s.isalpha() or not s.isupper():
            raise PackagingError(f"{path.name}: {h} sequence is not a bare uppercase "
                                 f"amino-acid string")
    return path


def write_structure(design: Design, path: Path) -> Path:
    """Copy the predicted complex and assert chain identity against the FASTA."""
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(design.pdb, path)
    have = _chains(path)
    want = {"A": design.heavy, "B": design.light, "C": design.antigen}
    if set(have) != set(want):
        raise PackagingError(f"{path.name}: chains are {sorted(have)}, must be exactly "
                             f"A=heavy, B=light, C=antigen (§4.2.2)")
    for ch, seq in want.items():
        got = "".join(have[ch])
        if len(got) != len(seq):
            raise PackagingError(f"{path.name}: chain {ch} has {len(got)} residues, "
                                 f"FASTA has {len(seq)}")
        if got[:10] != seq[:10]:
            raise PackagingError(f"{path.name}: chain {ch} starts {got[:10]!r}, "
                                 f"FASTA starts {seq[:10]!r}")
        if got != seq:
            n = next(i for i in range(len(got)) if got[i] != seq[i])
            raise PackagingError(f"{path.name}: chain {ch} differs from the FASTA at "
                                 f"position {n} ({got[n]!r} vs {seq[n]!r})")
    return path


def build_challenge(root: Path, team: str, challenge: int, design: Design,
                    metrics_md: str | None = None, docs_md: str | None = None,
                    extra_docs: dict[str, str] | None = None) -> Path:
    """One TEAM_NAME_ChallengeN folder, fully asserted."""
    base = root / team / f"{team}_Challenge{challenge}"
    (base / "structures").mkdir(parents=True, exist_ok=True)
    (base / "sequences").mkdir(parents=True, exist_ok=True)

    write_fasta(design, base / "sequences" / f"{design.name}.fasta")
    write_structure(design, base / "structures" / f"{design.name}_complex.pdb")
    write_pae_json(design.pdb, design.pae_npz,
                   base / "structures" / f"{design.name}_pae.json",
                   plddt_npz=design.plddt_npz, confidence_json=design.confidence_json)

    # Prefixes must match, which is a thing a human gets wrong and a machine should not.
    pdbs = sorted(p.name for p in (base / "structures").glob("*_complex.pdb"))
    paes = sorted(p.name for p in (base / "structures").glob("*_pae.json"))
    fas = sorted(p.name for p in (base / "sequences").glob("*.fasta"))
    pre = {p.replace("_complex.pdb", "") for p in pdbs}
    if pre != {p.replace("_pae.json", "") for p in paes} or pre != {f[:-6] for f in fas}:
        raise PackagingError(f"prefix mismatch: pdb={pdbs} pae={paes} fasta={fas}")

    if metrics_md:
        (base / "metrics").mkdir(exist_ok=True)
        (base / "metrics" / "scores.md").write_text(metrics_md)
    if docs_md:
        (base / "docs").mkdir(exist_ok=True)
        (base / "docs" / "methods_and_limitations.md").write_text(docs_md)
    for name, body in (extra_docs or {}).items():
        (base / "docs").mkdir(exist_ok=True)
        (base / "docs" / name).write_text(body)

    # §4.2.1 lists exactly two files per design. Anything else in structures/ is ours,
    # not the handbook's -- and ipsae.py writes its scratch .txt/.pml NEXT TO the PDB
    # it is given, so merely VALIDATING a built package used to litter it. Assert on
    # the directory, because a stray file is the kind of thing nobody looks for.
    allowed = {f"{design.name}_complex.pdb", f"{design.name}_pae.json"}
    stray = {p.name for p in (base / "structures").iterdir()} - allowed
    if stray:
        raise PackagingError(
            f"structures/ contains files the handbook does not list: {sorted(stray)}. "
            f"§4.2.1 specifies exactly design_X_complex.pdb and design_X_pae.json."
        )
    return base


def build_zip(root: Path, team: str) -> Path:
    """TEAM_NAME.zip containing the TEAM_NAME/ tree."""
    src = root / team
    if not src.is_dir():
        raise PackagingError(f"{src} does not exist")
    out = root / f"{team}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(root))
    return out
