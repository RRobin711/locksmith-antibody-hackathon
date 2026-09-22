# Validity experiments — do the binding metrics report the interface?

Two controls run 2026-09-20 after an independent audit found that six days had gone
into ranking precision and none into whether the ranked quantities mean anything.

## 1. Epitope knockout — destroy the binding site, keep the antigen

The decoy panel varied the antigen; this holds PD-1 fixed and removes only its
binding face, so antigen identity cannot confound the answer. `ctrl6` is the same
number of alanines placed on non-contacting surface, which is what makes any drop
interpretable. Mutant antigens get a fresh MSA — reusing the wild-type alignment
would leak the native residues back through the alignment.

| arm | antigen contacts removed | ipSAE | ΔG | contacts | iface pLDDT |
|---|---|---|---|---|---|
| `wt` | **0** | 0.869 ± 0.014 | -12.9 | 99 | 89.9 |
| `ctrl6` | **0** | 0.823 ± 0.026 | -13.0 | 97 | 89.1 |
| `ko6` | **349** | 0.720 ± 0.090 | -13.6 | 97 | 79.2 |
| `ko12` | **527** | 0.625 ± 0.091 | -12.5 | 94 | 71.0 |

### Which metrics actually see the epitope?

`ko12 - wt` is the epitope effect; `ctrl6 - wt` is the same number of alanines placed off the interface, and both mutant arms share the fresh-MSA treatment, so the control absorbs the MSA asymmetry as well as the mutation burden.

| metric | wt | ctrl6 (off-interface) | ko12 (epitope) | epitope effect | in seed sd | control effect | verdict |
|---|---|---|---|---|---|---|---|
| ipSAE | 0.869 ± 0.014 | 0.823 | 0.625 | -0.245 | **17.1×** | -0.046 | **sees it** |
| interface pLDDT | 89.920 ± 0.296 | 89.113 | 70.963 | -18.957 | **64.0×** | -0.807 | **sees it** |
| PRODIGY ΔG | -12.867 ± 0.351 | -13.000 | -12.533 | +0.333 | **0.9×** | -0.133 | **blind** |
| contacts | 99.000 ± 4.000 | 97.000 | 94.333 | -4.667 | **1.2×** | -2.000 | **blind** |

A metric counts as seeing the epitope only if the effect clears **3x its own seed sd on this complex** *and* **3x the matched off-interface control**. Both bars matter: the first stops noise being read as signal, the second stops "any mutation degrades it" being read as "the interface degrades it".

ipSAE and interface pLDDT fall **monotonically with the number of epitope contacts removed** (0 → 349 → 527), and the off-interface control barely moves. That is a dose–response against a matched control, which is as close to a clean positive as this kind of experiment gets.

**Sees the epitope: ipSAE, interface pLDDT. Blind to it: PRODIGY ΔG, contacts.**

This **cuts against the harsher reading** of the specificity and ablation results and should be said plainly: the predictor's *confidence* metrics do report the interface.

PRODIGY ΔG does not. Deleting 527 antigen-side contacts moves it by +0.333 kcal/mol — smaller than its own seed sd, and in a study where it carries **the largest single share of the ranking variance**. Taken with its scoring the named design better against TIM-3 (−14.1) than against PD-1 (−12.5), the metric the selection leaned on hardest is the one that fails every specificity check put to it.

Note the asymmetry with the antibody-side ablation, which removed 158 contacts for no effect: here 527 antigen-side contacts move ipSAE by 0.245. The likely reason is that the antibody-side mutants let Boltz re-dock a memorised paratope, whereas a mutated antigen has no memorised partner to fall back on.

ipSAE drop, wild-type → 12 epitope residues removed: **+0.245**; wild-type → 6 non-contacting controls: **+0.046**.


## 2. Composition-matched scramble — the proper null

Each scramble permutes its source design's CDR-H3 **order**: identical length,
identical composition, identical aromatic count, identical charge — and no design
rationale. Every cheap sequence feature this project used as a predictor is held
constant by construction.

| | n | DockQ mean | sd | range |
|---|---|---|---|---|
| source designs | 30 | **0.706** | 0.040 | 0.624 – 0.766 |
| their scrambles | 30 | **0.565** | 0.153 | 0.037 – 0.708 |
| the full 239 pool | 239 | 0.706 | 0.039 | 0.596 – 0.777 |

Paired difference source − scramble: **+0.141** (Wilcoxon p=2.35e-06). The scramble mean sits at the **0th percentile** of the 239 designs actually shipped.

**Designs beat their own scrambles by far more than the noise floor: 28 of 30 paired
wins, median difference +0.118, Wilcoxon p = 2.4e-06.** CDR-H3 *order* carries
information that its composition does not, so the pool is not a bag of interchangeable
loops and the ranking is measuring something real — though still pose retention against
the parent crystal, not binding.

**The precise version, which matters more than the headline.** The effect is not that
scrambles fail; it is *where* they land:

| | count |
|---|---|
| scrambles inside the 239-pool's DockQ range (0.596–0.777) | **15 / 30 (50%)** |
| scrambles above the pool **median** | **0 / 30** |
| scrambles that collapsed below 0.40 | 2 / 30 |
| source designs beating their own scramble | 28 / 30 |

So **half of all random permutations score like a real design, and none scores like a
good one.** A scramble can pass for a mediocre member of the pool but never reaches the
upper half. Two consequences, pulling in opposite directions and both worth stating:

- The pool's *upper* range is genuinely design-dependent. Selecting within the top of
  the distribution is not selecting noise, which is the strongest defence of the M3
  ranking apparatus produced by any experiment here.
- The pool's *lower* range is not discriminative — a design scoring near 0.62 is
  indistinguishable from a scrambled loop, so nothing below the median should be
  described as a design result at all.

