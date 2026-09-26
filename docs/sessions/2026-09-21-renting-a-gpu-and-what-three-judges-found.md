---
tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [[Learning]], [[locksmith-antibody-hackathon]]

# Session 2026-09-21 — Renting a GPU, and what three independent judges found

## 0. Session at a glance

**Before:** Challenge 2 had been declined on 2026-09-20 (`results/challenge2_scope.md`)
and then re-opened; RFantibody was proven unable to run on this laptop's Blackwell GPU.
Challenge 1 was packaged. The germline novelty metric — required for any Challenge 2 score —
did not exist.

**Now:** the germline metric exists and is validated; RFantibody was run end to end on a
**rented RTX 3090** (~5.5 h, **$2.82**) producing 36 backbones, 30 sequences and 30 RF2
predictions; hotspot conditioning was shown to work (**d=1.47, p=0.0016**); and three
independent judges audited the whole project, finding **one inversion in our own prose, one
bug that touches the shipped submission, and one issue that could mark Challenge 1
non-viable.**

**Unfinished and important:** every Challenge 2 artefact sits on a **stopped RunPod volume
and was never retrieved**. None of the seven Challenge 2 metrics has a value. Nothing is
submittable for Challenge 2.

**Prerequisites:** antibody CDR architecture and the PD-1/PD-L1 axis — see
[the spec extraction](2026-09-14-antibody-hackathon-spec-and-scoring.md). Why RFantibody
cannot run locally — see [the Blackwell
measurement](2026-09-20-why-rfantibody-cannot-run-on-blackwell.md).

## 1. The problem this session addressed

Challenge 2 asks for a complete VH/VL antibody designed *de novo* against PD-1. Three things
blocked it:

1. **No germline novelty metric.** §6.3.1 scores Challenge 2 novelty as CDR-H3 identity to
   *human germline*, not to Keytruda. `metrics/novelty.py` knew only pembrolizumab.
2. **No hardware.** RFantibody pins CUDA 11.8; this laptop is `sm_120` (Blackwell).
3. **No selection rule.** The project had already shown its metric stack cannot rank intact
   designs, so "pick the best of N" had no defensible implementation.

## 2. Concepts introduced (first principles)

### 2.1 Why CDR-H3 has no germline template

An antibody heavy chain is assembled by **V(D)J recombination**: one V, one D and one J gene
segment are cut from the genome and spliced, and the joining enzyme inserts **non-templated
(N-region) nucleotides** at both junctions. CDR-H3 sits exactly across that junction.

Consequence, measured from the assembled reference (`data/germline/human_igh.json`):

- **IGHV** contributes 2–3 residues to CDR-H3 (`AR` in **173 of 249** human alleles)
- **IGHJ** contributes 3 (`FDY`, `MDV`, `FDP`, …; 14 alleles)
- **IGHD** contributes 3–12 (76 peptides = alleles × 3 forward reading frames)
- the N regions have **no germline counterpart at all**

So for a 13-residue CDR-H3, roughly 5 positions are germline-templated before any D match.
**There is no single string to compare against**; the metric must be a best-match search over
segment families.

*Transferable principle:* when a spec says "identity to X" and X is a *process output* rather
than a sequence, the metric is a reconstruction problem, not a string comparison. Say which
reconstruction you chose and why, because the spec does not.

### 2.2 Intraclass correlation (ICC) as a selection test

For a grouped measurement, `ICC = σ²_between / (σ²_between + σ²_within)`. It answers: **does
knowing the group predict the value?** ICC→1 means all variation is real between-group signal;
ICC→0 means all of it is within-group.

Computed by one-way ANOVA over k groups with m members:

```
ICC = (MS_between − MS_within) / (MS_between + (m−1)·MS_within)
```

At k=10, m=3 the F-test has df=(9, 20) and F_crit(0.05)=2.39, which corresponds to
**ICC ≈ 0.32**. That is the smallest effect this design can detect, and it was pre-registered
**before** any score existed.

*Transferable principle:* an ICC near zero is only informative if you state the detectable
floor alongside it. "ICC = 0" without "at k=10 this detects ≥0.32" is a null read as absence.

### 2.3 Cohen's d and the cost of an interim look

`d = (mean₁ − mean₂) / s_pooled`. At n₁=n₂=18, `SE(d) ≈ √(2/18 + d²/68)`, so d=1.47 carries a
95% CI of roughly **[0.73, 2.22]**.

**The design flaw in this session's headline:** we looked at n=10 vs 5, got an ambiguous
d=0.96, then extended to n=18 vs 18 and tested at nominal α=0.05. That is **optional
stopping**. No alpha-spending was declared, so the reported p=0.0016 is not the true type-I
rate, and d=1.47 is **upward-biased** by exactly the winner's-curse logic this project applies
elsewhere: sampling continued until the effect crossed a threshold.

## 3. What was built — mechanism, not narrative

### 3.1 The germline reference (`scripts/60_build_germline_db.py`)

Assembles `data/germline/human_igh.json` **once**, so the metric has no new runtime dependency.

Sources, both harvested into a scratch directory without installing into any working venv:

| family | source | form |
|---|---|---|
| IGHV, IGHJ | ANARCI's `germlines.py` (`uv pip install --target <scratch> anarci --no-deps`) | IMGT-gapped amino acid, **128 columns** |
| IGHD | riot-na `databases/gene_db/d_genes/human/igh.fasta` | **nucleotide** |

IMGT numbering places the conserved Cys at **104** and CDR3 at **105–117** inclusive. The V
alignment ends `…TAVYYCAR----…`, so slicing columns 105–117 and dropping gaps yields the V
contribution; the J alignment is 114 gaps then `FDYWGQGTLVTVSS`, so the same slice yields
`FDY` (positions 115–117) and leaves FR4 at 118+ untouched.

D segments are translated in **all 3 forward reading frames** and truncated at the first stop
codon — biologically correct, because a D read through a stop cannot be in a productive
rearrangement.

### 3.2 The metric (`src/locksmith/metrics/germline.py`)

Two conventions, both computed, because the handbook says only "aligned … and percent identity
is calculated":

- **`vdj_coverage`** (primary): best **exact V prefix** + best **D substring** + best **exact
  J suffix**, non-overlapping, scored as `covered / len(query)`. V is matched as a prefix and
  J as a suffix because exonuclease trimming removes segment *ends*, never their interiors
  relative to the junction; D is matched as an arbitrary substring because it is trimmed at
  both ends and read in any frame.
- **`best_segment`** (literal): best global-alignment identity against any single segment.
  Bounded low by construction — a 13-mer against a 3-mer `FDY` cannot exceed 3/13.

`assign_v()` is a separate function doing full V-gene assignment over IMGT 1–104. **It is not
the scored metric**; it exists because it is the only germline quantity with published ground
truth to validate against. The V allele printed by `vdj_coverage` is **arbitrary among ties**
(173/249 alleles share `AR`) and must never be read as a call.

### 3.3 The conditioning check (`pod/check_backbone.py`)

Answers the only question that detects silent mis-conditioning: **do the designed CDR loops
make heavy-atom contact (5.0 Å) with the conditioned hotspot residues?**

Two invariants that were violated by the first version and are now load-bearing:

1. **RFdiffusion renumbers output continuously across chains.** Measured on `gate0b_0.pdb`:
   H = 1–115, L = 116–219, **T = 220–332**, where the input PD-1 was numbered 31–143.
   Matching hotspots by residue *number* therefore finds nothing. **Hotspots are passed as
   0-based ordinal positions within the target chain**, which survive any renumbering.
2. **The CDR loop REMARKs are 1-indexed ABSOLUTE indices across the whole file**, not
   per-chain residue numbers (README says so; observed range 26–209 over 332 residues).

Outputs one JSON line per backbone: `iface_residues`, `hotspots_contacted`,
`frac_iface_on_epitope`, plus NaN / duplicate-coordinate / collapsed-chain checks.

### 3.4 The pod pipeline

`pod/00_setup.sh` → `pod/01_run.sh`, transferred as `pod/BOOTSTRAP.sh` (three heredocs).

Setup order matters: **preflight aborts in seconds if `compute_cap ≥ 120`** before any
download, then installs upstream's own pins, then verifies **by arithmetic** (GPU matmul vs
CPU, a relu, a DGL message-pass with inspected output values), then downloads weights and
**loads each one** to check tensor counts, then rebuilds the target from the crystal.

## 4. Design decisions

| Decision | Chosen | Alternatives | Why | Cost to reverse |
|---|---|---|---|---|
| Hardware | Rented RTX 3090 (`sm_86`), $0.50/hr | A5000 ($0.27, **showed "No instances available"**), A40, local CPU (48 min/backbone) | cu118 is native on pre-Blackwell; CPU measured at 19.5 min/backbone for diffusion alone | trivial — scripts are hardware-agnostic |
| Germline reference | Static JSON harvested once | live ANARCI/IgBLAST dependency | metric then needs only ANARCII + Biopython, both already present; no new env | rebuild is one script |
| Primary novelty convention | `vdj_coverage` | `best_segment` | `best_segment` is near-constant by construction and cannot discriminate | one config line; both are always computed |
| Conditioning instrument | per-backbone contact check | conditioned-vs-unconditioned two-arm test | deterministic, usable at n=1; the two-arm test has poor power at pilot n | both were run |
| Target source | `data/refs/prepared/5ggs_ABZ.pdb` chain C (PD-1, from crystal chain **Z**) | raw `5ggs.pdb` chain C | **chain C of the crystal is a second pembrolizumab heavy chain** | catastrophic if wrong; now asserted in `pod/00_setup.sh` |

## 5. What went wrong

### 5.1 The germline claim was inverted — our own prose, on a pitch slide

**What happened.** `results/germline_metric_validation.md` §2 reports scrambled pembrolizumab
CDR-H3 (n=2000) as **mean 21.5%, sd 6.1%, p95 30.8%, max 53.8%**, and pembrolizumab itself at
**53.8%**. The write-up concluded the metric *"cannot distinguish a licensed therapeutic's loop
from a permutation of its own residues"* and put it on slide 4 of the pitch.

**Why it was dangerous.** It is exactly backwards. Pembrolizumab sits at the **maximum of 2000
draws**, ~**+5.3 sd** above the scramble mean — empirical p ≈ **1/2000**. The metric
discriminates about as decisively as 2000 samples permit.

**How it was caught.** An adversarial reviewer read the source distribution rather than the
summary sentence.

**The general lesson.** Comparing a single observation to the **maximum** of an aggregate and
concluding equivalence is the project's own catalogued error ("never diff a single observation
against an aggregate"). The surviving true claim — **the <95% gate is free** — is untouched.

### 5.2 The selection surrogate silently diverged from the score it stands in for

`src/locksmith/select/surrogate.py:46` hardcodes `ANCHOR_POOR, ANCHOR_MEDIUM, ANCHOR_GOOD =
2.5, 7.0, 9.5` (midpoints). `config/metrics.yaml:7` was switched to `band_value: top` on
2026-09-20. **The surrogate never reads the config.** An all-medium design gives final=80.0,
surrogate=70.0; segment slopes change non-uniformly (1.8 → 1.5), so rankings can invert — and
**the submitted winner was selected on this surrogate.**

*General lesson:* when a config value and a hardcoded constant encode the same convention, the
constant will rot. One assertion (`surrogate anchors == config band values`) makes it
impossible.

### 5.3 Three self-inflicted run failures, all caught in seconds

| Failure | Cause | Caught by |
|---|---|---|
| `uv: command not found` | `00_setup.sh` exports `$HOME/.local/bin` to PATH; `01_run.sh` did not | artefact assertion — all 10 logged `FAILED after 0s, no artefact`, none entered the pool |
| `Could not override 'inference.seed'` | **RFantibody has no `seed` key**; the key was invented, not read from the schema | Hydra aborted immediately |
| ICC read "0 backbones with ≥2 designs" | parser broke at the first `ATOM`; RF2 writes `SCORE` lines at **line 5190**, after the coordinates | the count was implausible |

*General lesson:* the first two are the same error — **inventing an interface instead of
reading the schema** — and it is the same shape as assuming crystal chain C was PD-1.

### 5.4 Two transfer methods failed, silently in one case

Typing 11,096 base64 characters into the web terminal delivered **11,092** — four dropped,
detected **only by md5**. Pasting the 20 KB bootstrap **truncated mid-word** inside a heredoc.
A JupyterLab file upload transferred it byte-exact (md5 `6176130587ba…`).

*General lesson:* keystroke-simulated input drops data under volume. A checksum is the only
thing that separates "arrived" from "arrived intact"; length alone looked fine.

### 5.5 ~2.5 hours of idle pod billing

The pilot finished at 01:36; nothing happened until 04:08 because the session ended its turn
and waited to be prompted instead of polling. **~$1.25 — more than the pilot's own compute.**
No assertion existed to catch it, because none had been built for it.

### 5.6 The pod was stopped without retrieving the data

Every Challenge 2 artefact — 36 backbones, 30 sequences, 30 RF2 predictions, 443 MB — remains
on the stopped volume. **d=1.47, ICC=0.000 and 24.9 Å exist only as prose in a markdown file.**
Nothing can be re-analysed, corrected, or checked without restarting the pod.

## 6. Degenerate and failure cases

- **Unmatched hotspots are silently ignored.** `ab_pose.parse_hotspots` matches
  `(chain, pdb_resnum)` and skips misses without error. Wrong numbering ⇒ zero hotspots ⇒
  unconditioned generation wearing the target's name. Mitigated by asserting the count is 26.
- **Blackwell substitution.** If a pod is provisioned with `sm_120`, setup aborts in seconds.
- **`frac_iface_on_epitope` is a ratio of small integers** — conditioned ≈ 6.33/8.9,
  unconditioned ≈ 3.56/7.1. Its sd is dominated by that granularity; a Mann-Whitney on such a
  ratio is defensible but a clustered permutation on counts would be better. **Known-crude.**
- **Volume survival across a pod stop is asserted by the provider's dialog, not verified.**

## 7. Verification — how we know it works

```bash
# germline metric, all four derivable cases
uv run scripts/61_validate_germline.py
```

Healthy output: verbatim germline junction → **100.0%**; scrambles (n=2000) → mean **21.5%**;
uniform-random 13-mers → mean **21.3%**; **242 of 249** IGHV alleles return themselves (the 7
others are ties at 100.0% identity over IMGT 1–104, not errors).

Pod arithmetic gate — the number that matters is not a flag:

```
[ ok ] torch 2.3.1+cu118 | dgl 2.4.0+cu118 | arch NVIDIA GeForce RTX 3090
[ ok ] matmul, relu and DGL message-pass all correct ON GPU
```

Conditioning, n=18 vs 18: conditioned `frac_iface_on_epitope` **0.712** (sd 0.110), hotspots
**6.33/26**; unconditioned **0.501** (sd 0.164), hotspots **3.56/26**.

**What a plausible-but-wrong result looks like:** *"26/26 hotspots resolved"* on every
backbone. That proves RFdiffusion **received** the hotspots; it says nothing about whether
they changed the output. Only the unconditioned arm separates those.

## 8. Honest assessment

**Solid.** The route runs end to end on rented hardware with zero failures across 36
backbones. The germline metric is validated on cases whose answers are derivable. The target
assertion catches the chain-C error mechanically.

**Weak.** The d=1.47 headline is optional stopping without alpha-spending, its CI is
[0.73, 2.22], and the "no hotspots" arm is the wrong null — the control that could *fail* is
hotspots swapped to a **decoy patch on the opposite face**, which costs the same and was not
run. A free permutation null against random 26-residue patches was also available and skipped.

**Crude.** `frac_iface_on_epitope` is a small-integer ratio on a side-chain-free backbone.

**Not established.** Whether any design clears the seven Challenge 2 gates — no metric has
been computed. Whether Boltz places these sensibly (post-cutoff median Fab DockQ **0.291**).
NetSolP on de novo VH/VL. **Whether the pod volume survived.**

**Does not support.** That any design is better than another (ICC 0.000). That RF2 agrees
(mean **24.87 Å** from the designed dock — though the parsimonious reading is that unfiltered
designs failed the standard filter, not that RF2 is unreliable). That anything binds.

## 9. Next steps

1. **Retrieve the pod volume** (~20 min, ~$0.20). Everything else is moot while the newest
   claims are unfalsifiable. **Blocked on: restarting a paid pod.**
2. **Write the test file.** Four verified bugs are ~4 lines of pytest each: surrogate anchors
   vs config, surrogate refuses a missing metric, rel1/rel3 Spearman-Brown consistency,
   `dockq_interface_agg` a required argument. LEARNINGS has named this the unlock for months.
3. **Document the DockQ flags inside the submission package.** At defaults DockQ **refuses**
   this submission (`ERROR: For chains ['A'] no identical corresponding chain was found`); it
   needs `--allowed_mismatches 40 --mapping ABC:ABC`. If the organisers run defaults,
   Challenge 1 is **non-viable**.
4. **Set the real team name** — `LOCKSMITH_DEV` is a placeholder and §4.1 requires exact match.
5. **Re-examine the G3 aromatic filter's direction** before it is presented as validated: it
   keeps CDR-H3s with **≤1 aromatic**, which selects *against* Tyr/Trp — among the most robust
   priors in antibody biology.
6. **Add CDR net charge to the design table.** The winner's CDR-H3 is **+2** (4 basic, 2
   acidic) where pembrolizumab is **0**; high CDR positive charge is a leading predictor of
   polyreactivity, and we independently measured TIM-3 cross-reactivity without connecting it.

## 10. Glossary

**V(D)J recombination** — the genomic cut-and-paste that builds an antibody variable gene from
V, D and J segments, with non-templated nucleotides added at the junctions.
**N region** — those non-templated insertions; they have no germline counterpart.
**IMGT numbering** — a scheme assigning fixed position numbers across antibodies of different
lengths; CDR3 is positions 105–117, the conserved Cys is 104.
**ICC** — intraclass correlation; between-group variance as a fraction of total.
**Optional stopping** — extending a sample after an interim look, then testing at nominal α;
inflates type-I error and biases the effect estimate upward.
**Hotspot conditioning** — supplying RFdiffusion with target residues the designed loops should
build against.
**`sm_86` / `sm_120`** — NVIDIA compute capabilities; cu118 ships kernels for the former, none
for the latter.
**Cohen's d** — standardised mean difference, `(μ₁−μ₂)/s_pooled`.
