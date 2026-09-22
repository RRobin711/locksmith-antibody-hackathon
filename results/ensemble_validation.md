# Does ensemble tightness earn a place in selection?

Analysis exactly as fixed in [[prereg_ensemble_validation|the pre-registration]], written before these designs were generated. **40 designs**, ProteinMPNN `v_48_020` at temperature 0.1, each folded as a Fab on **3 Boltz seeds**. No gating and no shortlisting before the correlation was measured.

CDR-H3 ensemble RMSD is the pairwise CA deviation of positions 96–108 after superposing on the **framework** — never on the loop, which would hide what is being measured.

## 1. The pool

| quantity | min | median | max |
|---|---|---|---|
| CDR-H3 ensemble RMSD | 0.28 Å | 0.71 Å | 2.23 Å |
| 3-seed mean DockQ | 0.628 | 0.722 | 0.747 |
| `final` (3-seed mean inputs) | 82.5 | 85.0 | 87.5 |
| viable | 40/40 | | |

Ensemble spread varies **7.9×** across the pool.

## 2. PRIMARY — ensemble RMSD vs 3-seed mean DockQ

> **Spearman rho = -0.387**, 95% CI [-0.62, -0.09], p = 0.014, n = 40

Pre-registered verdict: **WORTH REPORTING ONLY**

## 3. Ensemble RMSD vs every rubric metric

| metric | Spearman | p |
|---|---|---|
| `dockq` | -0.387 | 0.014 |
| `ipsae` | -0.387 | 0.014 |
| `dg` | +0.054 | 0.740 |
| `contacts` | +0.279 | 0.081 |
| `iface_plddt` | -0.496 | 0.001 |
| `cdr_sasa` | +0.126 | 0.438 |
| `netsolp` | +0.285 | 0.074 |
| `cdrh3_identity` | +0.052 | 0.751 |
| `final` | -0.263 | 0.101 |

## 4. SECONDARY — can a cheap PRE-FOLD feature predict ensemble spread?

A feature reaching |rho| >= 0.50 at Bonferroni alpha = 0.0083 (6 tests) would be a screen for conformational stability costing **zero folds** — worth more than the primary result.

| pre-fold feature | Spearman | p | passes Bonferroni? |
|---|---|---|---|
| `mpnn_score` | +0.090 | 0.582 | no |
| `cdrh3_len` | +nan | nan | no |
| `net_charge` | -0.015 | 0.927 | no |
| `hydrophobic_frac` | +0.297 | 0.063 | no |
| `aromatic_frac` | +0.621 | 0.000 | **yes** |
| `gly_frac` | +0.137 | 0.398 | no |

Screens found: **['aromatic_frac']**

## 5. Co-measurement check (already known, not the question)

- ensemble RMSD vs DockQ sd across seeds: **+0.718** (p=0.000)
  Both are computed from the same three structures, so this is partly mechanical, and it cannot drive selection: knowing the ensemble spread requires the 3 folds that would give the score variance directly.


## 6. The confound — and the verdict it overturns

The pre-registered primary verdict was "worth reporting only" (rho = −0.387, inside the
0.30–0.50 band). The secondary analysis changes it to **drop from selection**, for a reason the
thresholds alone could not express.

**Aromatic fraction in CDR-H3 predicts both the ensemble spread and the design quality, and it
fully accounts for the link between them.**

| relationship | Spearman | p |
|---|---|---|
| aromatic fraction → CDR-H3 ensemble RMSD | **+0.621** | 0.00002 |
| aromatic fraction → 3-seed mean DockQ | **−0.536** | 0.00036 |
| ensemble RMSD → 3-seed mean DockQ | −0.387 | 0.014 |
| **partial: ensemble → DockQ, controlling for aromatic fraction** | **−0.081** | **0.621** |
| **partial: aromatic fraction → DockQ, controlling for ensemble RMSD** | **−0.410** | 0.0086 |

Controlling for aromatic content, the ensemble↔quality correlation collapses from −0.387 to
**−0.081 (p = 0.62)** — it disappears. Controlling for ensemble spread, the aromatic↔quality
correlation **survives** at −0.410 (p = 0.009). The direction of explanation is unambiguous.

And the cost comparison settles it:

| predictor of 3-seed mean DockQ | Spearman | folds required |
|---|---|---|
| CDR-H3 ensemble RMSD | −0.387 | **3 per design** |
| **CDR-H3 aromatic fraction** | **−0.536** | **0** |

**The free sequence feature predicts design quality better than the measurement costing three
folds, and it explains away the expensive one.** Ensemble tightness is therefore dropped from
selection — not because it carries no signal, but because every bit of signal it carries about
quality is already available from the sequence, before any GPU time is spent.

### What this does not say

- **Not that CDR-H3 ensembles are uninteresting.** Spread still varies **7.9×** across the pool
  (0.28–2.23 Å) and still tells you how well-determined a prediction is. It remains worth
  reporting as characterisation in a dossier; it is not worth *selecting* on.
- **Not causation.** Aromatic content may be a marker for something else. It is chemically
  plausible — F/W/Y are bulky with many packing arrangements, and aromatic-rich CDR-H3 is a known
  correlate of polyreactivity and poor developability — but this is 40 designs from one
  generator, and the mechanism is not established here.
- **Not generalisable to varied loop lengths.** Every design here has a **13-residue CDR-H3**,
  fixed by the backbone ProteinMPNN was redesigning onto (which is why the `cdrh3_len` test
  returned `nan` — the variable is constant). Length is the main determinant of loop flexibility,
  so the aromatic effect is measured with that dimension held still.
- Aromatic fraction spans only **0.08–0.31** here. Extrapolating outside that is unsupported.

### One more thing the table shows

`iface_plddt` is the rubric metric most correlated with ensemble spread (**−0.496, p = 0.001**) —
noticeably better than `ipsae` (−0.387). The n=8 re-seed found *mean loop pLDDT* blind to
heterogeneity (rho = −0.168); at n=40 the *interface* pLDDT does partly see it. So the confidence
signal is not uniformly blind — it depends which pLDDT you read, and the interface one carries
more information about loop stability than the loop's own mean does.
