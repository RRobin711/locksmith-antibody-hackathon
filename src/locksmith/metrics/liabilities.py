"""Sequence-derived developability liabilities: the scan `BUILD.md:62` promised.

WHY THIS EXISTS, AND WHY IT EXISTS LATE. `BUILD.md:62` specified
`liabilities.py — N-X-S/T, NG/DG motifs, exposed Met, pI, net charge` as part of the
build. It was never written. On 2026-09-22 an independent reviewer found **two N-linked
glycosylation sequons in the Challenge 2 design's CDRs, both on antigen-contacting
residues** — `N-V-S` at heavy 52 and `N-A-S` at light 49, neither present in the parent
scaffold, both introduced by ProteinMPNN. Handbook §9.2 lists *"No N-glycosylation
sequons (N-X-S/T) in Fv region"* as an explicit checklist item. The design shipped with
them.

A planned check that does not exist is indistinguishable from a check that passed. That
is this project's own thesis and this module is the counterexample being closed.

WHAT IT DOES NOT DO. This is a **sequence** scan. It finds motifs that are *capable* of
becoming liabilities; it does not tell you whether they will. Occupancy of a glycosylation
sequon, the rate of an NG deamidation, whether an exposed Met actually oxidises — all
depend on structure, expression system and formulation. Where a structure is supplied the
scan adds solvent accessibility, which is the one cheap thing that genuinely separates a
buried motif from an exposed one. Treat a hit as "look at this", never as "this fails".

SEVERITY is assigned by two things only, both defensible from §9:
  * the motif's own risk class, and
  * whether it sits in a CDR. A framework NG in a marketed antibody is tolerated every
    day; the same motif in a paratope is a different object.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from locksmith.numbering import IMGT_CDR, number

# --- motif definitions -------------------------------------------------------------
# X != P in the glycosylation sequon: proline at position 2 blocks the oligosaccharyl
# transferase, so NPS/NPT are not sequons. This is the single most common way a naive
# regex over-reports.
SEQUON = re.compile(r"(?=(N[^P][ST]))")
# Deamidation: NG is the fast one by an order of magnitude; NS/NT/NN/NH are slower.
DEAMIDATION = {"NG": "high", "NS": "moderate", "NT": "moderate", "NN": "low", "NH": "low"}
# Isomerisation / fragmentation at Asp. DG is the fast one; DP is an acid-cleavage site.
ISOMERISATION = {"DG": "high", "DS": "moderate", "DT": "moderate", "DD": "low", "DP": "low"}
OXIDATION = set("MW")          # Met and Trp, only reported when exposed or in a CDR
FREE_CYS = "C"

# Henderson-Hasselbalch pKa set (Bjellqvist). Used for pI/charge only; any standard set
# moves pI by <0.3 and nothing here turns on that precision.
PKA_POS = {"K": 10.54, "R": 12.48, "H": 6.04}
PKA_NEG = {"D": 3.90, "E": 4.07, "C": 8.18, "Y": 10.46}
PKA_NTERM, PKA_CTERM = 9.69, 2.34


@dataclass(frozen=True)
class Liability:
    kind: str                  # 'glycosylation' | 'deamidation' | 'isomerisation' | ...
    motif: str
    chain: str                 # 'heavy' | 'light'
    position: int              # 1-based index into the supplied chain sequence
    region: str                # 'CDR-H1' ... 'framework'
    severity: str              # 'high' | 'moderate' | 'low'
    sasa: float | None = None  # A^2, only when a structure was supplied
    note: str = ""

    def __str__(self) -> str:
        s = f"{self.severity.upper():8s} {self.kind:15s} {self.motif:4s} " \
            f"{self.chain} {self.position:>3d} ({self.region})"
        if self.sasa is not None:
            s += f"  SASA {self.sasa:.0f} A^2"
        return s + (f"  -- {self.note}" if self.note else "")


@dataclass
class Report:
    liabilities: list[Liability] = field(default_factory=list)
    charge: dict[str, float] = field(default_factory=dict)
    pi: dict[str, float] = field(default_factory=dict)

    @property
    def cdr_hits(self) -> list[Liability]:
        return [l for l in self.liabilities if l.region != "framework"]

    @property
    def high(self) -> list[Liability]:
        return [l for l in self.liabilities if l.severity == "high"]

    def handbook_9_2_pass(self) -> tuple[bool, list[str]]:
        """The two §9.2 checklist items this scan can actually adjudicate.

        §9.2: "No N-glycosylation sequons (N-X-S/T) in Fv region" and
              "No NG/DG deamidation/isomerisation motifs in CDRs".
        Returns (passes, reasons-it-does-not).
        """
        fails = []
        for l in self.liabilities:
            if l.kind == "glycosylation":
                fails.append(f"N-glycosylation sequon {l.motif} at {l.chain} {l.position} "
                             f"({l.region})")
            elif l.motif in ("NG", "DG") and l.region != "framework":
                fails.append(f"{l.motif} motif at {l.chain} {l.position} ({l.region})")
        return (not fails), fails

    def summary(self) -> str:
        ok, fails = self.handbook_9_2_pass()
        lines = [f"{len(self.liabilities)} liabilities, {len(self.cdr_hits)} in CDRs, "
                 f"{len(self.high)} high severity",
                 f"handbook 9.2 (sequons + CDR NG/DG): {'PASS' if ok else 'FAIL'}"]
        lines += [f"  - {f}" for f in fails]
        lines += [f"  {l}" for l in sorted(self.liabilities,
                                           key=lambda x: (x.severity != "high",
                                                          x.region == "framework"))]
        for ch in sorted(self.charge):
            lines.append(f"  {ch}: net charge {self.charge[ch]:+.1f} at pH 7.4, "
                         f"pI {self.pi[ch]:.2f}")
        return "\n".join(lines)


def net_charge(seq: str, ph: float = 7.4) -> float:
    q = 1 / (1 + 10 ** (ph - PKA_NTERM)) - 1 / (1 + 10 ** (PKA_CTERM - ph))
    for aa, pka in PKA_POS.items():
        q += seq.count(aa) / (1 + 10 ** (ph - pka))
    for aa, pka in PKA_NEG.items():
        q -= seq.count(aa) / (1 + 10 ** (pka - ph))
    return q


def isoelectric_point(seq: str) -> float:
    lo, hi = 0.0, 14.0
    for _ in range(100):                      # bisection; 1e-4 pH is far beyond need
        mid = (lo + hi) / 2
        if net_charge(seq, mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _regions(seq: str) -> dict[int, str]:
    """1-based position -> 'CDR-H1'|'CDR-L2'|...|'framework'.

    Regions come from the project's IMGT numbering, so they agree with every other
    metric here rather than introducing a third CDR definition.
    """
    n = number(seq)
    if n is None:
        return {}
    tag = "H" if n.chain_type == "H" else "L"
    out: dict[int, str] = {}
    idx = n.query_start                       # position of the first numbered residue
    for (pos, _), aa in n.numbering:
        if aa == "-":
            continue
        idx += 1
        region = "framework"
        for name, (lo, hi) in IMGT_CDR.items():
            if lo <= pos <= hi:
                region = f"CDR-{tag}{name[-1]}"
        out[idx] = region
    return out


def scan_chain(seq: str, chain: str, sasa: dict[int, float] | None = None
               ) -> list[Liability]:
    reg = _regions(seq)

    def region_of(i: int) -> str:
        return reg.get(i, "framework")

    def acc(i: int) -> float | None:
        return None if sasa is None else sasa.get(i)

    out: list[Liability] = []

    # --- N-glycosylation sequons. The §9.2 item this module exists for. ---
    for m in SEQUON.finditer(seq):
        i = m.start() + 1
        r = region_of(i)
        out.append(Liability(
            "glycosylation", m.group(1), chain, i, r,
            "high" if r != "framework" else "moderate", acc(i),
            "N-X-S/T; oligosaccharyl transferase site. In a CDR a glycan sits in the "
            "paratope. Fix: N->Q or S/T->A (handbook 9, Pillar 4)."))

    # --- deamidation / isomerisation dipeptides ---
    for i in range(len(seq) - 1):
        d = seq[i:i + 2]
        pos, r = i + 1, region_of(i + 1)
        for table, kind in ((DEAMIDATION, "deamidation"), (ISOMERISATION, "isomerisation")):
            if d in table:
                sev = table[d]
                if r != "framework" and sev == "moderate":
                    sev = "high" if d in ("NG", "DG") else "moderate"
                out.append(Liability(kind, d, chain, pos, r, sev, acc(pos)))

    # --- oxidation-prone residues, reported only in CDRs or when exposed ---
    for i, aa in enumerate(seq, 1):
        if aa in OXIDATION:
            r = region_of(i)
            a = acc(i)
            if r != "framework" or (a is not None and a > 30):
                out.append(Liability("oxidation", aa, chain, i, r,
                                     "moderate" if r != "framework" else "low", a,
                                     "Met/Trp oxidation; matters when solvent exposed."))

    # --- unpaired cysteine ---
    if seq.count(FREE_CYS) % 2:
        i = seq.rfind(FREE_CYS) + 1
        out.append(Liability("free_cysteine", "C", chain, i, region_of(i), "high", acc(i),
                             f"odd cysteine count ({seq.count(FREE_CYS)}); "
                             f"possible unpaired thiol -> disulfide scrambling"))
    return out


def compute(heavy: str, light: str, *,
            sasa_heavy: dict[int, float] | None = None,
            sasa_light: dict[int, float] | None = None) -> Report:
    """Scan an Fv (or Fab) pair. Structure-derived SASA is optional and additive."""
    rep = Report()
    rep.liabilities += scan_chain(heavy, "heavy", sasa_heavy)
    rep.liabilities += scan_chain(light, "light", sasa_light)
    for name, seq in (("heavy", heavy), ("light", light), ("Fv", heavy + light)):
        rep.charge[name] = round(net_charge(seq), 2)
        rep.pi[name] = round(isoelectric_point(seq), 2)
    return rep
