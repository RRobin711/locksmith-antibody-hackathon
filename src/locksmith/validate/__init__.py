"""Pre-flight checks on a design before any GPU time is spent on it.

Every check here exists because the failure it catches is SILENT -- it produces a
plausible number rather than an exception, which is the recurring shape of this
project's bugs (boltz exiting 0 on a fatal error; ipsae writing an empty table on
a renamed file; a spliced sequence folding confidently as a protein that does not
exist).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from locksmith.io.pdb import SplicedSequenceError, chains

AA = set("ACDEFGHIKLMNPQRSTVWY")


@dataclass
class Validation:
    design_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def check_sequence(design_id: str, heavy: str, light: str, antigen: str,
                   *, reference_heavy: str | None = None) -> Validation:
    """Refuse a design that cannot mean what it claims to."""
    v = Validation(design_id)
    for name, s in (("heavy", heavy), ("light", light), ("antigen", antigen)):
        if not s:
            v.errors.append(f"{name} chain is empty")
            continue
        bad = sorted(set(s) - AA)
        if bad:
            v.errors.append(f"{name} contains non-standard residues {bad}")
        if "X" in s:
            v.errors.append(f"{name} contains unknown residue X")
    # A design is a mutant of its parent, so a length change means the CDR graft
    # or the MPNN output was misaligned -- not a design, a bug.
    if reference_heavy is not None and len(heavy) != len(reference_heavy):
        v.errors.append(
            f"heavy chain length {len(heavy)} != reference {len(reference_heavy)}; "
            f"an indel here means the design was built against the wrong frame")
    return v


def check_reference_foldable(pdb: Path) -> Validation:
    """A structure whose chains carry internal deletions must not seed a design.

    Delegates to the io.pdb guard so there is one definition of 'spliced'.
    """
    v = Validation(str(pdb))
    for cid in chains(pdb):
        try:
            from locksmith.io.pdb import seq_for_folding
            seq_for_folding(pdb, cid)
        except SplicedSequenceError as e:
            v.errors.append(str(e))
    return v
