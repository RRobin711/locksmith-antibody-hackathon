# Do the new tests actually fail when the bugs come back?

**2026-09-22.** A test suite that passes proves nothing on its own — it has to be shown
to *fail* on the defect it claims to pin. This is that check, run by reintroducing each
bug into the working tree, running the suite, and restoring from a backup copy.

| # | mutation | expected to fail | result |
|---|---|---|---|
| 1 | `surrogate.py`: restore hardcoded `ANCHOR_* = 2.5, 7.0, 9.5` and the literal anchors in `compute()` | anchor-agreement tests | **5 failed**, incl. all four `test_surrogate_equals_final_at_the_anchors` cases and `test_surrogate_anchors_match_config_band_values` |
| 2 | `dockq.py`: restore `interface_agg: str = "min"` signature default | `test_dockq_module_defaults_match_the_declared_conventions` | **1 failed**, that test |
| 3 | `fold/boltz.py`: delete the space check in `_stage()` | `test_msa_path_with_space_is_staged` | **1 failed**, that test |
| 4 | `io/pdb.py`: make `seq_for_folding` tolerate an internal gap | `test_seq_for_folding_refuses_a_spliced_chimera` | **1 failed**, that test |
| 5 | `config/metrics.yaml`: flip `strict_good: true -> false` on `cdrh3_identity` | strict-edge tests | **2 failed**: `test_strict_band_edges_are_exclusive` and `test_surrogate_diverges_only_at_strict_edges_and_only_upward` |

After each restore the suite returns to **17 passed**, verified between every mutation
and again at the end.

**What this establishes:** each test fails for the reason it was written, and the failure
is localised — mutating one invariant does not cascade into unrelated tests, which is what
makes a failure diagnostic rather than merely loud.

**What it does not establish:** that the suite covers everything worth covering. Five
invariants are pinned. `assert_artefacts()` and the artefact-keyed resume rule are named
in `LEARNINGS.md` as mechanisms still lacking tests, and nothing here touches the scoring
maths beyond the band edges.

*Transferable principle:* a green suite is a claim about the code; a suite shown to go red
on reintroduced defects is evidence about the suite. Only the second one is worth quoting.
