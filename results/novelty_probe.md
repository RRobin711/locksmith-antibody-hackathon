# What does the rubric's novelty metric actually measure?

`scripts/43_novelty_probe_generate.py` → `44_novelty_probe_fold.py` → this. Pre-registered in [the novelty-probe pre-registration](prereg_2026-09-20_novelty_probe.md) before any fold ran.

Only the listed CDR-H3 positions are redesigned; H1, H2, the light chain and the antigen are native, so the **paratope is the only thing that varies between arms**. The native residue is forbidden at each designed position, so identity is exact.

| arm | positions | antigen contacts touched | CDR-H3 identity | novelty band | n | DockQ mean | 95% CI | ipSAE | ΔG |
|---|---|---|---|---|---|---|---|---|---|
| **A — 4 zero-contact positions** | 14 designs | **0** | **69.2%** | Good | 14 | **0.691** | [0.674, 0.707] | 0.761 | -12.5 |
| **B — 6 zero-contact positions** | 14 designs | **0** | **53.8%** | Good | 14 | **0.689** | [0.663, 0.713] | 0.744 | -12.3 |
| **C — 6 paratope positions** | 14 designs | **227** | **53.8%** | Good | 14 | **0.657** | [0.652, 0.662] | 0.825 | -11.5 |

Reference points: 239-design pool mean DockQ **0.705**, pool max **0.777**, pembrolizumab self-refold **0.818**.

## The comparison the whole arm exists for

Arms B and C carry **identical** `cdrh3_identity` of 53.8%, the same Good band, the same novelty sub-score and the same contribution to `final`. They differ only in *which* CDR-H3 positions were allowed to change.

| | B (paratope intact) | C (paratope redesigned) | difference |
|---|---|---|---|
| DockQ mean | **0.689** | **0.657** | **+0.032** |
| ipSAE mean | 0.744 | 0.825 | |
| `cdrh3_identity` | 53.8% | 53.8% | **0.0 — the rubric sees nothing** |
| Mann–Whitney U | | | U=155, p=0.0094 |

**H2 not confirmed** — the gap is only +0.032. Either the predictor is insensitive to paratope identity on this complex (a finding about Boltz that would undercut DockQ as evidence here), or CDR-H3 contributes less to this interface than the contact counts imply. Report as a null, not as support.

## H3 — does this reach the Good DockQ band?

Best single design: **0.757** (B_k6_nocontact). Good needs ≥ 0.80.

**Not reached** — 0.043 short. The extrapolation in the headroom audit predicted identity in this band would get there; it did not, so that extrapolation is **withdrawn as a prediction** and the observed relationship is reported instead.

## Declaration

**These are rubric probes, not design candidates.** An arm-A molecule is a near-copy of pembrolizumab with four substitutions at positions that touch nothing. Proposing one because it scores well would be gaming a metric this experiment exists to show is gameable. M3 is closed and `mpnn_T0.5_s104_036` remains the named design whatever the numbers above say.

**Note for Challenge 2:** its binding mean has no DockQ — no metric compares against a reference structure. Nothing in the Challenge 2 rubric could have detected the B-versus-C difference at all.

