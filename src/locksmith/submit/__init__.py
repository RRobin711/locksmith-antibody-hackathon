"""Submission packaging and artifact validation for the handbook's §4 layout."""
from locksmith.submit.pae import write_pae_json
from locksmith.submit.package import (
    HEADERS, Design, PackagingError, build_challenge, build_zip, write_fasta,
    write_structure,
)

__all__ = ["write_pae_json", "Design", "PackagingError", "HEADERS",
           "build_challenge", "build_zip", "write_fasta", "write_structure"]


def packaged_scores(challenge: int, team: str = "LOCKSMITH_DEV") -> dict:
    """The scores as they appear IN THE PACKAGE, parsed from the shipped `scores.md`.

    WHY THE PACKAGE AND NOT A RUN DIRECTORY. The deck is a scored deliverable, and it has
    now drifted from the package twice by reading a run artefact instead of the thing
    being shipped:

      1. 2026-09-22: the shipped .pptx said "No design submitted" for Challenge 2 while
         the package contained a Challenge 2 design. The fix then was to build the deck
         from "the same run that packages", which addressed the symptom.
      2. 2026-09-23: **the same class of defect, live in the deck** -- slide 1 read
         "Challenge 2 96.0/100" while slide 8 read "91.2/100", in one file. `scripts/57`
         took the first viable row of `runs/challenge2_fold_r10/scores.jsonl`, which is
         the design BEFORE the S->A sequon fix; the package ships the fixed design at
         91.2. A run directory holds every candidate ever scored, including the ones
         superseded. Only the package holds what is being submitted.

    So the deck now reads the deliverable. The rule generalises: **a document about an
    artefact must be generated from that artefact, not from the pipeline that produced
    it**, because a pipeline keeps its intermediates and a reader only ever sees the
    output.

    Returns {metric: value, ..., "final": float, "viable": bool}.
    Raises FileNotFoundError if that challenge is not packaged.
    """
    import re
    from pathlib import Path

    p = (Path("submission") / team / f"{team}_Challenge{challenge}"
         / "metrics" / "scores.md")
    if not p.exists():
        raise FileNotFoundError(
            f"challenge {challenge} is not packaged at {p}; the deck cannot state a "
            f"score for a challenge that is not in the submission")
    text = p.read_text()
    out: dict = {}
    for m in re.finditer(r"^\|\s*`([a-z_0-9]+)`\s*\|\s*(-?[\d.]+)\s*\|", text, re.M):
        out[m.group(1)] = float(m.group(2))
    fm = re.search(r"\*\*Final:\s*([\d.]+)\s*/\s*100\.\s*Viable:\s*(True|False)",
                   text)
    if not fm:
        raise ValueError(f"{p}: no 'Final: X / 100. Viable: Y' line found")
    out["final"] = float(fm.group(1))
    out["viable"] = fm.group(2) == "True"
    if not out:
        raise ValueError(f"{p}: parsed no metrics")
    return out
