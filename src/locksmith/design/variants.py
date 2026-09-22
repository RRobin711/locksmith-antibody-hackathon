"""Hand-mutated pembrolizumab variants, for testing the SCORING protocol.

These are deliberately NOT designs. Gate 1c asks whether Fv ipSAE *ranking*
predicts Fab ipSAE ranking; that needs a set of molecules spanning a range of
interface quality, and it does not care how they were produced. Mutating CDR
positions is ~30 lines and decouples G1c from the design pipeline entirely.

SPANNING THE RANGE IS THE POINT, AND ALSO THE TRAP
--------------------------------------------------
A rank correlation over molecules that are all equally good measures noise. So
the panel spans 0 -> 13 substitutions in CDR-H3 plus poly-Gly anchors.

But the opposite error is subtler and worse: the Fv screen's real job is
separating designs that have ALREADY passed earlier filters, so its operating
regime is the narrow, high-quality band. A panel spanning "perfect" to "poly-Gly
garbage" makes ranking trivial and will report a flattering rho for a task that
never occurs. Hence the analysis reports rho over the full panel AND over the
subset clearing the ipSAE cutoff, and leads with the second.

SUBSTITUTION ALPHABET: all 20 minus cysteine. A stray Cys can form a spurious
disulfide, which is a structural failure of a different kind from "this loop no
longer complements the epitope" -- it would add cliff-edge outliers to what
should be a graded series. Proline is KEPT: it is a legitimate backbone
disruptor and real designers do produce it.
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from locksmith.numbering import IMGT_CDR, number

SUB_ALPHABET = "ADEFGHIKLMNPQRSTVWY"        # 20 minus C -- see module docstring
SEED = 20260916


@dataclass(frozen=True)
class Variant:
    name: str
    heavy_fv: str
    light_fv: str
    n_subs: int
    regions: str                 # which CDRs were touched
    cdrh3: str
    cdrh3_identity: float        # % identity to pembrolizumab CDR-H3
    kind: str                    # 'wt' | 'substitution' | 'destructive'


def _cdr_indices(seq: str, cdr: str) -> list[int]:
    """Indices into `seq` of the residues occupying an IMGT CDR range."""
    n = number(seq)
    if n is None:
        raise ValueError("sequence is not a recognisable V domain")
    lo, hi = IMGT_CDR[cdr]
    idx, i = [], 0
    for (pos, _), aa in n.numbering:
        if aa == "-":
            continue
        if lo <= pos <= hi:
            idx.append(i)
        i += 1
    return idx


def _substitute(seq: str, idx: list[int], n_subs: int, rng: random.Random) -> str:
    chosen = rng.sample(idx, n_subs)
    out = list(seq)
    for i in chosen:
        out[i] = rng.choice([a for a in SUB_ALPHABET if a != out[i]])
    return "".join(out)


def _identity(a: str, b: str) -> float:
    if len(a) != len(b):
        return 100.0 * sum(x == y for x, y in zip(a, b)) / max(len(a), len(b))
    return 100.0 * sum(x == y for x, y in zip(a, b)) / len(a)


def build_panel(heavy_fv: str, light_fv: str, *, seed: int = SEED) -> list[Variant]:
    rng = random.Random(seed)
    h3 = _cdr_indices(heavy_fv, "cdr3")
    h1 = _cdr_indices(heavy_fv, "cdr1")
    h2 = _cdr_indices(heavy_fv, "cdr2")
    wt_h3 = "".join(heavy_fv[i] for i in h3)

    def mk(name, hv, n_subs, regions, kind):
        cdr3 = "".join(hv[i] for i in h3)
        return Variant(name=name, heavy_fv=hv, light_fv=light_fv, n_subs=n_subs,
                       regions=regions, cdrh3=cdr3,
                       cdrh3_identity=round(_identity(cdr3, wt_h3), 1), kind=kind)

    panel = [mk("v00_wt", heavy_fv, 0, "-", "wt")]

    # Graded series in CDR-H3: the loop that dominates antigen contact.
    for k, n in enumerate([1, 2, 3, 4, 6, 8, 10, 13], start=1):
        n = min(n, len(h3))
        panel.append(mk(f"v{k:02d}_h3_{n}", _substitute(heavy_fv, h3, n, rng),
                        n, "H3", "substitution"))

    # A few outside H3, to check the ranking is not an H3-only artefact.
    panel.append(mk("v09_h1_4", _substitute(heavy_fv, h1, min(4, len(h1)), rng),
                    min(4, len(h1)), "H1", "substitution"))
    panel.append(mk("v10_h2_4", _substitute(heavy_fv, h2, min(4, len(h2)), rng),
                    min(4, len(h2)), "H2", "substitution"))
    hv = _substitute(heavy_fv, h1, 3, rng)
    hv = _substitute(hv, h2, 3, rng)
    hv = _substitute(hv, h3, 3, rng)
    panel.append(mk("v11_h1h2h3_9", hv, 9, "H1+H2+H3", "substitution"))

    # Destructive anchors: fix the bottom of the range so the gradient is real.
    # Same length, so numbering and DockQ alignment are unaffected.
    gly = list(heavy_fv)
    for i in h3:
        gly[i] = "G"
    panel.append(mk("v12_h3_polyG", "".join(gly), len(h3), "H3", "destructive"))
    gly2 = list(heavy_fv)
    for i in h1 + h2 + h3:
        gly2[i] = "G"
    panel.append(mk("v13_allcdr_polyG", "".join(gly2), len(h1) + len(h2) + len(h3),
                    "H1+H2+H3", "destructive"))
    return panel


def save(panel: list[Variant], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(v) for v in panel], indent=2))


def load(path: Path) -> list[Variant]:
    return [Variant(**d) for d in json.loads(Path(path).read_text())]
