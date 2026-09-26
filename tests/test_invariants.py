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


# --------------------------------------------------------------------------------
# 10. A program that runs without error is not evidence it did what you intended.
# --------------------------------------------------------------------------------
# `boltz predict` EXITS 0 after fatal errors -- seen four times: a missing
# `cuequivariance_torch` import, a host-RAM kill, a CUDA OOM printing "Number of failed
# examples: 1" under a 100% progress bar, and an MSA path truncated at a space which
# printed a traceback, then initialised the GPU and carried on. A batch keyed on exit
# status marks all of them complete and skips them for ever. `assert_artefacts` is the
# rule as code; these are the cases it has to catch.

def test_assert_artefacts_rejects_every_way_a_fold_lies(tmp_path):
    import numpy as np
    from locksmith.fold import FoldFailed, assert_artefacts

    def good_pdb(p):
        p.write_text("ATOM      1  CA  ALA A   1       0.000   0.000   0.000"
                     "  1.00  0.00           C\nEND\n")
        return p

    def good_npz(p):
        np.savez(p, pae=np.zeros((4, 4)))
        return p

    pdb, pae = good_pdb(tmp_path / "m.pdb"), good_npz(tmp_path / "pae.npz")
    assert_artefacts(pdb, pae, None, label="ok")          # the happy path must pass

    # 1. the artefact is simply absent -- the commonest silent exit-0 failure
    with pytest.raises(FoldFailed, match="produced no"):
        assert_artefacts(tmp_path / "nope.pdb", pae, None, label="missing")

    # 2. present but EMPTY. `.exists()` is satisfied; nothing was written.
    empty = tmp_path / "empty.pdb"
    empty.write_text("")
    with pytest.raises(FoldFailed, match="empty"):
        assert_artefacts(empty, pae, None, label="empty")

    # 3. present, non-empty, and contains no coordinates at all
    noatoms = tmp_path / "noatoms.pdb"
    noatoms.write_text("REMARK boltz wrote a header and then died\nEND\n")
    with pytest.raises(FoldFailed, match="no ATOM"):
        assert_artefacts(noatoms, pae, None, label="noatoms")

    # 4. truncated .npz -- exists, right name, unreadable. The failure mode that
    #    survives every existence check anyone writes.
    trunc = tmp_path / "trunc.npz"
    trunc.write_bytes(good_npz(tmp_path / "src.npz").read_bytes()[:40])
    with pytest.raises(FoldFailed, match="will not load"):
        assert_artefacts(pdb, trunc, None, label="trunc")

    # 5. a PAE that loads but is not a square matrix
    notsquare = tmp_path / "ns.npz"
    np.savez(notsquare, pae=np.zeros((4, 7)))
    with pytest.raises(FoldFailed, match="not a square matrix"):
        assert_artefacts(pdb, notsquare, None, label="notsquare")

    # 6. the plddt sibling missing -- ipsae.py locates it by string-substituting the
    #    PAE path, and without it writes an EMPTY table and exits 0.
    with pytest.raises(FoldFailed, match="produced no"):
        assert_artefacts(pdb, pae, tmp_path / "absent_plddt.npz", label="noplddt")


def test_resume_keys_on_the_artefact_not_on_the_row_existing():
    """A scorer that skipped any design with A ROW in its output treated 239 error
    rows as completed work, so the obvious re-run would have skipped all 239 for ever
    and left a file that looks finished. Every resume in this repo must test for the
    VALUE, not for the row."""
    for script in ("scripts/72_challenge2_fold.py", "scripts/73_challenge2_score.py",
                   "scripts/80_challenge2_score_r10.py"):
        src = Path(script).read_text()
        assert 'get("ok")' in src or '"ipsae" in' in src, (
            f"{script}: resume does not key on an artefact field")
        assert "design_id" in src


def test_fold_is_complete_distinguishes_absent_from_broken(tmp_path):
    """A resume predicate must not report 'not done' when the CHECK is broken.

    The bug this pins, measured 2026-09-22: four driver scripts called
    `assert_artefacts(dir, label)`, which is not its signature. The `TypeError` was caught
    by a bare `except Exception` and read as "not folded yet", so a finished 40-complex
    panel would have been silently refolded from scratch on any restart. Re-doing finished
    work looks exactly like doing work, so nothing would have reported it.

    Note the asymmetry: had the swallowed exception meant "done" instead, the same bug
    would have SKIPPED every fold and produced an empty panel that looked complete. So the
    predicate must be false only because the ARTEFACTS say so.
    """
    import numpy as np
    from locksmith.fold import fold_is_complete

    d = tmp_path / "predictions" / "x"
    d.mkdir(parents=True)
    assert fold_is_complete(tmp_path / "nope", "x", n_models=1) is False

    def write(i, *, atoms=True, square=True):
        tag = f"x_model_{i}"
        (d / f"{tag}.pdb").write_text(
            "ATOM      1  N   ALA A   1      0.000   0.000   0.000  1.00 50.00\n"
            if atoms else "REMARK nothing\n")
        arr = np.zeros((4, 4)) if square else np.zeros((4, 5))
        np.savez(d / f"pae_{tag}.npz", pae=arr)
        np.savez(d / f"plddt_{tag}.npz", plddt=np.zeros(4))

    write(0)
    assert fold_is_complete(d, "x", n_models=1) is True
    # asking for more models than were produced must be False, not a crash
    assert fold_is_complete(d, "x", n_models=5) is False
    for i in range(1, 5):
        write(i)
    assert fold_is_complete(d, "x", n_models=5) is True

    # a broken artefact is False...
    (d / "x_model_3.pdb").write_text("")
    assert fold_is_complete(d, "x", n_models=5) is False

    # ...but a broken CHECK must propagate, never read as "not done"
    import locksmith.fold as F
    real = F.assert_artefacts
    F.assert_artefacts = lambda *a, **k: (_ for _ in ()).throw(TypeError("wrong args"))
    try:
        with pytest.raises(TypeError):
            fold_is_complete(d, "x", n_models=1)
    finally:
        F.assert_artefacts = real


def test_pick_contacting_chain_rejects_the_wrong_copy():
    """Two copies of an antigen; only one touches the antibody. Pick that one.

    The bug this pins, measured 2026-09-22: `classify()` took the first heavy chain, the
    first light chain and the first non-antibody chain in the file, with nothing requiring
    them to belong to the same copy of the complex. On a 40-entry calibration panel
    **8 of 40 (20%)** paired an Fv with the antigen of a *different* copy, producing a
    DockQ native whose only interface was the heavy-light framework.

    Every chain is present and every sequence is correct in that file -- it is simply not
    a complex. Nothing raises. The number that comes out is about the wrong pair.
    """
    import gemmi
    from locksmith.io.pdb import contacting_residues, pick_contacting_chain

    def chain(name, positions):
        ch = gemmi.Chain(name)
        for i, (x, y, z) in enumerate(positions, start=1):
            r = gemmi.Residue()
            r.name, r.seqid = "ALA", gemmi.SeqId(i, " ")
            a = gemmi.Atom()
            a.name, a.element, a.pos = "CA", gemmi.Element("C"), gemmi.Position(x, y, z)
            r.add_atom(a)
            ch.add_residue(r)
        return ch

    antibody = chain("A", [(0, 0, 0), (0, 0, 3), (0, 0, 6)])
    near = chain("C", [(3, 0, 0), (3, 0, 3), (3, 0, 6)])     # 3 Å away: touching
    far = chain("D", [(60, 0, 0), (60, 0, 3), (60, 0, 6)])   # another copy, 60 Å away

    ab = list(antibody)
    assert contacting_residues(list(near), ab) == 3
    assert contacting_residues(list(far), ab) == 0

    name, n = pick_contacting_chain({"C": list(near), "D": list(far)}, ab)
    assert name == "C" and n == 3

    # order must not decide it -- the bug was "first one wins"
    name, n = pick_contacting_chain({"D": list(far), "C": list(near)}, ab)
    assert name == "C" and n == 3

    # nothing touching => refuse, rather than returning a chain that is not a partner
    assert pick_contacting_chain({"D": list(far)}, ab) == (None, 0)


def test_write_input_refuses_an_msa_that_boltz_would_discard(tmp_path):
    """A cached alignment whose query length differs from the antigen must RAISE.

    The bug this pins, measured 2026-09-23 on the shipped Challenge 2 structure: Boltz's
    featurizer compares `len(residues) == len(first_residues)` and, on mismatch, prints
    `Warning: MSA does not match input sequence, creating dummy.` to stdout and replaces
    the alignment with a dummy. No exception, no non-zero exit, nothing in any output file.

    The check is on LENGTH ALONE, so a query that is an exact substring of the input at
    offset 5 -- which is precisely our case, a 113-residue cached query against the
    123-residue handbook antigen -- is treated like an unrelated sequence. The antigen was
    folded single-sequence and nothing said so.

    Worse for detection: the processed `msa/*.npz` still records the full alignment,
    because the discard happens at featurisation AFTER that file is written. Inspecting
    the artefact suggests the alignment was used.
    """
    from locksmith.fold import FoldFailed
    from locksmith.fold.boltz import write_input

    msa = tmp_path / "cached.csv"
    query = "PWNPPTFSPALL"                      # 12 residues
    msa.write_text("key,sequence\n-1," + query + "\n-1,PWSPLTFSPAQL\n")

    # exact match: accepted
    out = write_input(tmp_path / "ok.fasta", "QVQ", "DIQ", query, antigen_msa=msa)
    assert out.exists() and query in out.read_text()

    # the real shape of the bug: query is a SUBSTRING of a longer antigen
    longer = "DSPDR" + query
    with pytest.raises(FoldFailed, match="would DISCARD|DISCARD this alignment"):
        write_input(tmp_path / "bad.fasta", "QVQ", "DIQ", longer, antigen_msa=msa)

    # a shorter antigen is equally wrong
    with pytest.raises(FoldFailed):
        write_input(tmp_path / "bad2.fasta", "QVQ", "DIQ", query[:-3], antigen_msa=msa)

    # the deliberate-reproduction escape hatch still works
    out = write_input(tmp_path / "forced.fasta", "QVQ", "DIQ", longer,
                      antigen_msa=msa, allow_msa_mismatch=True)
    assert longer in out.read_text()

    # no cached MSA at all => nothing to check, server query is fine
    out = write_input(tmp_path / "server.fasta", "QVQ", "DIQ", longer, antigen_msa=None)
    assert "|protein|\n" in out.read_text()


def test_fold_raises_on_a_boltz_warning_that_only_reaches_stdout(monkeypatch, tmp_path):
    """Boltz reports some meaning-fatal problems only on stdout, while exiting 0.

    Measured 2026-09-23: every Challenge 2 fold this project ran printed
    `Warning: MSA does not match input sequence, creating dummy.` -- a 113-residue cached
    alignment passed with a 123-residue antigen -- and Boltz silently substituted a dummy.
    With the alignment actually used the same design scores ipSAE 0.012 rather than 0.773.

    Three layers hid it: `fold()` captures stdout and surfaces it only when
    `assert_artefacts` raises, so a SUCCESSFUL fold discards its own warnings
    (`runs/challenge2_refold_r10.log` is 34 lines with zero boltz output); the processed
    `msa/*.npz` still records the full alignment because the discard happens later at
    featurisation; and the run exits 0. A warning nobody reads is not a warning, so this
    is a hard failure.
    """
    import subprocess
    from locksmith.fold import FoldFailed
    from locksmith.fold import boltz as B

    class FakeProc:
        returncode = 0
        stdout = ("Predicting DataLoader 0: 100%\n"
                  "Warning: MSA does not match input sequence, creating dummy. 2 [..]\n")
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    monkeypatch.setattr(B, "_stage", lambda p: p)

    with pytest.raises(FoldFailed, match="MSA does not match input sequence"):
        B.fold("t", "QVQ", "DIQ", "PWNPP", out_root=tmp_path, antigen_msa=None,
               diffusion_samples=1, recycling_steps=1)

    # and the other exit-0 failure this project has hit
    class FailedExamples(FakeProc):
        stdout = "Predicting: 100%\nNumber of failed examples: 1\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FailedExamples())
    with pytest.raises(FoldFailed, match="failed example"):
        B.fold("t2", "QVQ", "DIQ", "PWNPP", out_root=tmp_path, antigen_msa=None,
               diffusion_samples=1, recycling_steps=1)

    # `writer.py` prints that line UNCONDITIONALLY, including ": 0" on success, so the
    # COUNT is the signal and the prefix is not. Keying on the prefix made this guard fire
    # on every fold; it reached a real run before the mistake was caught.
    class Healthy(FakeProc):
        stdout = "Predicting: 100%\nNumber of failed examples: 0\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Healthy())
    with pytest.raises(FoldFailed, match="fold produced no"):
        # reaches assert_artefacts (no files on disk) rather than the stdout guard
        B.fold("t3", "QVQ", "DIQ", "PWNPP", out_root=tmp_path, antigen_msa=None,
               diffusion_samples=1, recycling_steps=1)


def test_every_process_pool_uses_spawn_not_fork():
    """PROMOTED FROM LEARNINGS.md 2026-09-26. The mechanism IS the memory.

    `ProcessPoolExecutor` defaults to **fork** on Linux, and a forked child cannot
    re-initialise CUDA. Merging a serial NetSolP stage (which touches CUDA in the parent)
    into the same script as a 6-worker parallel scorer killed **239/239** workers with
    `RuntimeError: Cannot re-initialize CUDA in forked subprocess`.

    The original code kept the two stages in separate *processes*, and that boundary was
    load-bearing with nothing recording it. General rule the incident bought:
    **a refactor that removes a process boundary must say what was crossing it.**

    This test greps source rather than behaviour, which is weaker than a behavioural test
    -- but the failure only reproduces on a CUDA-initialised parent with real workers, so
    a behavioural version would not run in CI. Stated plainly rather than oversold.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    offenders = []
    for py in sorted(list((root / "scripts").glob("*.py")) + list((root / "src").rglob("*.py"))):
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"ProcessPoolExecutor\s*\(", text):
            # Look at the call site: the argument list, up to the matching depth-0 ')'.
            depth, j = 0, m.end() - 1
            while j < len(text):
                if text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            call = text[m.end():j]
            if "mp_context" not in call:
                line = text[:m.start()].count("\n") + 1
                offenders.append(f"{py.relative_to(root)}:{line}")

    assert not offenders, (
        "ProcessPoolExecutor without an explicit mp_context defaults to fork on Linux, "
        "and a forked child cannot re-initialise CUDA (239/239 workers died once). "
        "Pass mp_context=multiprocessing.get_context('spawn'). Offenders: " + ", ".join(offenders)
    )
