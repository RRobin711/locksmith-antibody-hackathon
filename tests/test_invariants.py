"""Executable versions of lessons this project had only written down.

WHY THIS FILE EXISTS. Every correction this project made between 2026-09-14 and
2026-09-21 went into prose, and prose cannot fail a build. Four independent audits
then found four conventions that had silently drifted out of sync -- the surrogate's
band anchors, the DockQ aggregator's default, a reliability figure, and a claim about
seed allocation -- in a codebase that is otherwise obsessive about silent failure.
`LEARNINGS.md` named "no test suite" as the blocker on promoting four entries out of
prose. This is that file.

The rule for what belongs here: an invariant whose violation is INVISIBLE. A crash
does not need a test. A number that quietly becomes wrong does.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from locksmith.config import load
from locksmith.metrics import dockq
from locksmith.score import evaluate
from locksmith.select import surrogate

CFG = load()


# --------------------------------------------------------------------------------
# 1. A config value and a hardcoded constant encoding the same convention.
# --------------------------------------------------------------------------------
# `config/metrics.yaml:7` was switched from `midpoint` to `top` on 2026-09-20.
# `select/surrogate.py` kept the midpoint anchors (2.5/7.0/9.5) because it never reads
# the config. The submitted winner was selected on the surrogate. Nothing failed.

def test_surrogate_anchors_match_config_band_values():
    bs = CFG.band_scores
    assert (surrogate.ANCHOR_POOR, surrogate.ANCHOR_MEDIUM, surrogate.ANCHOR_GOOD) == (
        bs["poor"], bs["medium"], bs["good"]
    ), (
        f"surrogate anchors {(surrogate.ANCHOR_POOR, surrogate.ANCHOR_MEDIUM, surrogate.ANCHOR_GOOD)} "
        f"disagree with config band_value={CFG.band_value} -> "
        f"{(bs['poor'], bs['medium'], bs['good'])}. The surrogate is what we RANK on; "
        f"`final` is what we REPORT. When they disagree the ranking is on a scale "
        f"nobody declared."
    )


def _on_anchor(challenge: int, which: str) -> dict[str, float]:
    """Raw metrics placed exactly on one band anchor for every scored metric.

    `good` anchors are nudged one resolution step INTO the Good band for the four
    metrics whose good-edge the handbook writes strictly -- otherwise the design is
    Medium by the rubric and we would be asserting the wrong thing. See
    `test_surrogate_diverges_only_at_strict_edges` for that case on its own.
    """
    out = {}
    for n, b in CFG.bands().items():
        if challenge not in b.challenges:
            continue
        v = getattr(b, which)
        if which == "good" and b.strict_good:
            v += 1e-6 if b.direction == "high" else -1e-6
        out[n] = v
    return out


@pytest.mark.parametrize("challenge", [1, 2])
@pytest.mark.parametrize("which", ["good", "medium"])
def test_surrogate_equals_final_at_the_anchors(challenge: int, which: str):
    """The surrogate's whole contract: interpolate BETWEEN anchors, agree ON them.

    This is the behavioural form of the test above -- it fails even if someone
    reintroduces the divergence somewhere other than the three module constants.
    """
    raw = _on_anchor(challenge, which)
    sc = evaluate(raw, challenge=challenge, cfg=CFG)
    sg = surrogate.compute(raw, challenge=challenge, cfg=CFG)
    assert sc.final == pytest.approx(sg.value, abs=1e-4), (
        f"challenge {challenge}, every metric exactly on its `{which}` anchor: "
        f"reported final={sc.final} but surrogate={sg.value}"
    )


def test_surrogate_diverges_only_at_strict_edges_and_only_upward():
    """No continuous function agrees with a step function AT the step.

    `contacts` is an integer count with a `> 25` Good edge, so "exactly 25" is an
    ordinary outcome: the rubric calls it Medium, the surrogate has already reached
    the Good anchor. Documented rather than fixed, because the alternative is a
    non-monotone surrogate. What must stay true is the DIRECTION and the SET.
    """
    strict = {n for n, b in CFG.bands().items() if b.strict_good}
    assert strict == {"contacts", "iface_plddt", "cdr_sasa", "cdrh3_identity"}
    anchors = surrogate._anchors(CFG)
    for n, b in CFG.bands().items():
        s = surrogate._interp(b.good, b.cutoff, b.medium, b.good, anchors)
        reported = CFG.band_scores[b.band_of(b.good)]
        if n in strict:
            assert s > reported, f"{n}: expected the known upward divergence at its edge"
            assert (s, reported) == (anchors[2], CFG.band_scores["medium"])
        else:
            assert s == pytest.approx(reported, abs=1e-9), f"{n} must agree at its anchor"


# --------------------------------------------------------------------------------
# 2. A missing metric must never improve a design's rank.
# --------------------------------------------------------------------------------
# `score.evaluate` refuses to produce `final` when any metric is unknown. The
# surrogate averaged over whatever was present, so dropping the worst metric RAISED
# the score -- and selection ran on the surrogate.

def test_surrogate_refuses_a_design_with_a_missing_metric():
    raw = _on_anchor(1, "good")
    worst = "netsolp"
    raw[worst] = CFG.bands()[worst].cutoff          # its poor anchor
    full = surrogate.compute(raw, challenge=1, cfg=CFG).value
    del raw[worst]
    pruned = surrogate.compute(raw, challenge=1, cfg=CFG)
    assert pruned.value != pruned.value or pruned.value <= full, (
        f"deleting the limiting metric moved the surrogate {full} -> {pruned.value}. "
        f"A design we could not measure must not outrank one we could."
    )


def test_score_and_surrogate_agree_on_which_metrics_challenge2_scores():
    """DockQ is Challenge 1 only (§5.2). Both paths must apply that identically."""
    ch2 = {n for n, b in CFG.bands().items() if 2 in b.challenges}
    assert "dockq" not in ch2, "DockQ must be excluded from Challenge 2 (§5.2)"
    raw = _on_anchor(2, "good")
    assert set(surrogate.compute(raw, challenge=2, cfg=CFG).sub) == ch2


# --------------------------------------------------------------------------------
# 3. A tool default that silently disagrees with the declared convention.
# --------------------------------------------------------------------------------
# `dockq.compute` defaults to interface_agg="min" while config says `global`. Every
# caller currently passes the config value explicitly; the next one to forget gets a
# different number with no error.

def test_dockq_module_defaults_match_the_declared_conventions():
    sig = inspect.signature(dockq.compute).parameters
    assert sig["interface_agg"].default is None, (
        "the aggregator must be resolved from config at call time, not restated as a "
        "signature default -- a default that copies a convention is a second source "
        "of truth and the second one rots"
    )
    assert sig["allowed_mismatches"].default is None
    assert dockq._convention("dockq_interface_agg", "min") == \
        CFG.conventions["dockq_interface_agg"]
    assert dockq._convention("dockq_allowed_mismatches", 0) == \
        CFG.conventions["dockq_allowed_mismatches"]


def test_dockq_is_invoked_with_the_flags_the_submission_documents():
    """At its DEFAULTS DockQ exits 1 on our package. The flags are load-bearing."""
    src = Path(dockq.__file__).read_text()
    assert "--allowed_mismatches" in src and "--mapping" in src
    assert '"ABC:ABC"' in src, (
        "chain mapping must be pinned; left free, DockQ searches and a wrong mapping "
        "scores a good design badly"
    )


# --------------------------------------------------------------------------------
# 4. Reliability arithmetic. A quoted figure that no longer follows from its inputs.
# --------------------------------------------------------------------------------
# Spearman-Brown: r_k = k*r_1 / (1 + (k-1)*r_1). The project quoted single-seed
# reliability 0.689 alongside a 3-seed 0.849. Those two are not consistent; 0.653 is
# the r_1 that reproduces 0.849. The tell was free and went unchecked for two days.

def spearman_brown(r1: float, k: int) -> float:
    return k * r1 / (1 + (k - 1) * r1)


@pytest.mark.parametrize("r1,k,rk", [(0.653, 3, 0.849), (0.602, 3, 0.819)])
def test_spearman_brown_roundtrip(r1: float, k: int, rk: float):
    assert spearman_brown(r1, k) == pytest.approx(rk, abs=0.002)


def test_the_published_single_seed_reliability_is_the_consistent_one():
    """0.689 does not reproduce the published 3-seed 0.849; 0.653 does."""
    assert spearman_brown(0.689, 3) == pytest.approx(0.869, abs=0.002)
    assert spearman_brown(0.653, 3) == pytest.approx(0.849, abs=0.002)


# --------------------------------------------------------------------------------
# 5. Band-edge strictness. Worth 5 final points on one metric.
# --------------------------------------------------------------------------------
# The handbook writes four band edges and two cutoffs with STRICT inequalities. A
# 10-residue CDR-H3 with 7 matches lands on exactly 70.0%.

def test_strict_band_edges_are_exclusive():
    b = CFG.bands()["cdrh3_identity"]
    assert b.strict_good, "§6.3.1 writes '< 70%'"
    assert b.band_of(70.0) == "medium", "70.0 is NOT Good; that edge is worth 5 points"
    assert b.band_of(69.9) == "good"
    assert not b.passes_cutoff(95.0), "§7.2 writes '< 95%'"


def test_every_metric_band_is_monotone_in_its_direction():
    """cutoff -> medium -> good must improve, or band_of() silently misclassifies."""
    for name, b in CFG.bands().items():
        order = [b.cutoff, b.medium, b.good]
        assert order == (sorted(order) if b.direction == "high"
                         else sorted(order, reverse=True)), f"{name}: {order}"


# --------------------------------------------------------------------------------
# 6. Two LEARNINGS entries whose mechanism already existed but was unfindable.
# --------------------------------------------------------------------------------

def test_msa_path_with_space_is_staged(tmp_path, monkeypatch):
    """A path inside a FASTA field splits on whitespace; argv does not. The vault
    lives under '.../Obsidian Personal/...', so this fires on every real fold."""
    from locksmith.fold import boltz
    spaced = tmp_path / "a dir with spaces"
    spaced.mkdir()
    msa = spaced / "pd1.a3m"
    msa.write_text(">q\nPEPTIDE\n")
    monkeypatch.setattr(boltz, "MSA_STAGE", tmp_path / "stage")
    staged = boltz._stage(msa)
    assert " " not in str(staged)
    assert staged.read_bytes() == msa.read_bytes()


def test_seq_for_folding_refuses_a_spliced_chimera(tmp_path):
    """Folding a coordinate-derived sequence with an internal gap predicts a protein
    that does not exist. It moved one DockQ 0.064 -> 0.370 and flipped a verdict."""
    from locksmith.io import pdb as pdbio

    def atom(i: int, resi: int) -> str:
        return (f"ATOM  {i:5d}  CA  ALA A{resi:4d}    "
                f"{0.0:8.3f}{0.0:8.3f}{float(i):8.3f}  1.00  0.00           C")

    gapped = tmp_path / "gapped.pdb"
    gapped.write_text("\n".join(atom(i, r) for i, r in
                                enumerate([1, 2, 3, 40, 41, 42], 1)) + "\nEND\n")
    with pytest.raises(pdbio.SplicedSequenceError):
        pdbio.seq_for_folding(gapped, "A")

    contiguous = tmp_path / "ok.pdb"
    contiguous.write_text("\n".join(atom(i, r) for i, r in
                                    enumerate([1, 2, 3, 4, 5, 6], 1)) + "\nEND\n")
    assert pdbio.seq_for_folding(contiguous, "A") == "AAAAAA"


# --------------------------------------------------------------------------------
# 7. Challenge 2 must not be scored against Challenge 1's reference.
# --------------------------------------------------------------------------------
# §6.3.1 gives ONE metric with TWO references: Keytruda's CDR-H3 for Challenge 1, human
# germline for Challenge 2. Until 2026-09-22 every caller got Keytruda, so a Challenge 2
# design would have been scored against the wrong reference and produced a perfectly
# plausible number for the wrong question -- the failure mode with no error message.

PEMBRO_CDRH3_IN_CONTEXT = (
    "QVQLVQSGVEVKKPGASVKVSCKASGYTFTNYYMYWVRQAPGQGLEWMGGINPSNGGTNFNEKFKN"
    "RVTLTTDSSTTTAYMELKSLQFDDTAVYYCARRDYRFDMGFDYWGQGTTVTVSS"
)


def test_novelty_uses_a_different_reference_per_challenge():
    from locksmith.metrics import novelty
    c1 = novelty.compute(PEMBRO_CDRH3_IN_CONTEXT, challenge=1)
    c2 = novelty.compute(PEMBRO_CDRH3_IN_CONTEXT, challenge=2)
    assert c1.value == pytest.approx(100.0), (
        "pembrolizumab against its own CDR-H3 must be 100% identical; got "
        f"{c1.value} -- the Challenge 1 reference is wrong"
    )
    assert c2.value != c1.value, (
        "Challenge 2 returned the Challenge 1 number, so the germline reference is not "
        "wired in and a de novo design would be scored against Keytruda"
    )
    assert "vdj_coverage" in (c2.detail or ""), \
        "Challenge 2 must route through metrics/germline.py"


def test_pembrolizumab_fails_challenge1_novelty_and_passes_challenge2():
    """The positive control, in both directions.

    Keytruda is 100% identical to itself, so it must FAIL Challenge 1's <95% cutoff --
    that is the gate doing its job. Against germline it scores 53.8% and PASSES, which is
    why `results/germline_metric_validation.md` calls the Challenge 2 novelty gate free.
    """
    from locksmith.metrics import novelty
    b = CFG.bands()["cdrh3_identity"]
    c1 = novelty.compute(PEMBRO_CDRH3_IN_CONTEXT, challenge=1).value
    c2 = novelty.compute(PEMBRO_CDRH3_IN_CONTEXT, challenge=2).value
    assert not b.passes_cutoff(c1), f"Ch1: {c1}% must fail the <95% cutoff"
    assert b.passes_cutoff(c2), f"Ch2: {c2}% must pass the <95% cutoff"


def test_challenge2_scores_seven_metrics_not_eight():
    """§5.2 excludes DockQ from Challenge 2 — there is no reference structure."""
    ch2 = {n for n, b in CFG.bands().items() if 2 in b.challenges}
    ch1 = {n for n, b in CFG.bands().items() if 1 in b.challenges}
    assert len(ch2) == 7 and len(ch1) == 8
    assert ch1 - ch2 == {"dockq"}


# --------------------------------------------------------------------------------
# 8. Viability must never be silently optimistic.
# --------------------------------------------------------------------------------
# §7.2: a design failing ANY minimum is non-viable and ranks below every viable one.
# `scripts/75_challenge2_package.py` refuses to build a folder unless a design is
# viable, so `viable` is what stands between us and packaging a non-viable design in
# the handbook's tree -- which would look like a submission and score below nothing.

def test_a_single_failed_cutoff_makes_a_design_non_viable():
    for name, b in CFG.bands().items():
        if 1 not in b.challenges:
            continue
        raw = _on_anchor(1, "good")
        # push exactly this one metric just past its cutoff, in the failing direction
        raw[name] = b.cutoff + (-1.0 if b.direction == "high" else 1.0)
        sc = evaluate(raw, challenge=1, cfg=CFG)
        assert sc.viable is False, f"{name} below its cutoff must make the design non-viable"
        assert name in sc.failing


def test_an_unmeasurable_metric_leaves_viability_UNKNOWN_not_true():
    """`None`, never `True`. A metric we could not compute is not a metric that passed."""
    raw = _on_anchor(1, "good")
    del raw["ipsae"]
    sc = evaluate(raw, challenge=1, cfg=CFG)
    assert sc.viable is None, "a missing metric must not yield viable=True"
    assert sc.final is None, "and must not yield a final score"
    assert "ipsae" in sc.unknown


# --------------------------------------------------------------------------------
# 9. The liability scan BUILD.md promised and nobody wrote.
# --------------------------------------------------------------------------------
# `BUILD.md:62` specified `liabilities.py — N-X-S/T, NG/DG motifs, exposed Met, pI, net
# charge`. It was never written, and two N-glycosylation sequons went out in the
# Challenge 2 submission on antigen-contacting CDR residues, against a handbook §9.2
# checklist item. These tests pin the scanner against the exact defect it failed to
# catch, so "the module exists" can never again be confused with "the check runs".

from locksmith.metrics import liabilities as liab

CH2_HEAVY = ("EVQLVESGGGLVQPGGSLRLSCAASGFNLKDHYIHWVRQAPGKGLEWVARINVSTGATRYADSVKGRFTI"
             "SADTSKNTAYLQMNSLRAEDTAVYYCSRSFAGSHLLWGQGTLVTVSS")
CH2_LIGHT = ("DIQMTQSPSSLSASVGDRVTITCKSSRVVDVVSWYQQKPGKAPKLLIYNASTRPAGVPSRFSGSRSGTDF"
             "TLTISSLQPEDFATYYCQGYDYETDTLVFGQGTKVEIK")


def test_scanner_finds_the_two_sequons_that_actually_shipped():
    """The regression test for the defect. Exact motifs, exact positions."""
    rep = liab.compute(CH2_HEAVY, CH2_LIGHT)
    glyc = {(l.chain, l.position, l.motif) for l in rep.liabilities
            if l.kind == "glycosylation"}
    assert ("heavy", 52, "NVS") in glyc, "CDR-H2 sequon missed"
    assert ("light", 49, "NAS") in glyc, "CDR-L2 sequon missed"
    assert all(l.severity == "high" for l in rep.liabilities
               if l.kind == "glycosylation"), "a CDR sequon is not 'high'"
    ok, fails = rep.handbook_9_2_pass()
    assert ok is False and len(fails) == 2


def test_proline_blocks_the_sequon():
    """N-P-S/T is NOT a sequon — proline blocks the transferase. The commonest
    false positive in a naive regex, and the one that would make the scan cry wolf."""
    assert liab.SEQUON.findall("AAANPSAAA") == []
    assert liab.SEQUON.findall("AAANPTAAA") == []
    assert liab.SEQUON.findall("AAANASAAA") == ["NAS"]


def test_cdr_context_raises_severity_over_framework():
    """A framework NG is tolerated in marketed antibodies; a paratope NG is not.
    The scan must distinguish them or it is just a grep."""
    rep = liab.compute(CH2_HEAVY, CH2_LIGHT)
    assert rep.cdr_hits, "no CDR-located liabilities found at all — region mapping broken"
    assert all(l.region.startswith("CDR-") for l in rep.cdr_hits)
    assert any(l.region == "framework" for l in rep.liabilities), \
        "everything landed in a CDR — region mapping is not discriminating"


def test_charge_and_pi_are_self_consistent():
    """Net charge must be zero at the pI, by construction."""
    for seq in (CH2_HEAVY, CH2_LIGHT):
        pi = liab.isoelectric_point(seq)
        assert abs(liab.net_charge(seq, pi)) < 1e-3
        assert liab.net_charge(seq, pi - 2) > 0 and liab.net_charge(seq, pi + 2) < 0


def test_build_md_promise_is_now_kept():
    """`BUILD.md:62` names five scans. All five must be reachable."""
    src = Path(liab.__file__).read_text()
    for token in ("glycosylation", "deamidation", "isomerisation", "oxidation",
                  "free_cysteine", "net_charge", "isoelectric_point"):
        assert token in src, f"BUILD.md promises {token} and it is absent"
