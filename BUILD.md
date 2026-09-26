# Build skeleton

Concrete structure for the code. Companion to [the delivery plan](PLAN.md); read §14 of that
first — several decisions here exist to fix problems found in review.

**Status:** M0 complete — `io/`, `numbering.py`, `metrics/`, `score.py`, `config/` and
`scripts/00–02` exist and Gate 0 is green. The rest is scoped, not written.

**Revised 2026-09-15:** we are not submitting (see PLAN.md §15). `submit/` is demoted from a
gate to an output convenience — we still emit the canonical layout because it makes results
directly comparable to what the hackathon would have scored, and because it forces artefacts to
exist rather than living in notebooks. It drives no technical decision. Team name is the fixed
placeholder `RYAN_BINNY`.

---

## 1. Design principles, and the problem each one solves

| Principle | Problem it solves |
|---|---|
| **Metrics derived on demand, never stored** | Four scoring conventions are still unresolved. A convention change must cost a 10-second re-run, not a re-fold. |
| **Bands and cutoffs live in YAML, not Python** | Same reason. Changing a threshold is a config edit, reviewable in a diff. |
| **Every expensive artefact keyed by content hash** | Resumability by construction. A killed overnight batch loses only the in-flight job. |
| **Conflicting tools in isolated envs behind subprocess** | `prodigy-prot` needs numpy≥2, `DockQ` needs numpy<2. Not optional. |
| **Predictors behind one Protocol** | Tracks A/B (ColabFold / Boltz / Chai) must be swappable on a day's notice when one fails on Blackwell. |
| **One flat design table, provenance stamped at creation** | Group identity and run parameters cannot be reconstructed after aggregation. |

---

## 2. Layout

```
locksmith-antibody-hackathon/
├── pyproject.toml              # uv; torch pinned to cu128 index
├── uv.lock
├── config/
│   ├── metrics.yaml            # bands, cutoffs, weights, conventions  ← the rubric, as data
│   ├── run.yaml                # paths, predictor tiers, batch sizes
│   └── versions.lock.yaml      # exact tool versions + ipSAE commit, copied into submission
├── src/locksmith/
│   ├── config.py               # typed loaders for the YAMLs
│   ├── types.py                # Design, FoldResult, MetricSet, Verdict
│   ├── io/
│   │   ├── pdb.py              # chain relabel→A/B/C, Fab↔Fv slicing, interface residues
│   │   ├── fasta.py            # the exact 3-header format, read + write
│   │   ├── pae.py              # AF2 / AF3 / Boltz PAE → canonical; canonical → AF-style JSON
│   │   └── store.py            # content-hash artefact store
│   ├── numbering.py            # ANARCI → IMGT CDR ranges; CDR-H3 extraction
│   ├── metrics/                # each returns raw values only; no banding, no opinions
│   │   ├── registry.py         # name → callable, so score.py stays generic
│   │   ├── ipsae.py            # vendored script, pinned commit, subprocess
│   │   ├── dockq.py            # isolated env (numpy<2)
│   │   ├── prodigy.py          # isolated env (numpy>=2) → ΔG, contacts
│   │   ├── plddt.py            # interface pLDDT, in-process
│   │   ├── sasa.py             # CDR SASA — computes BOTH bound and unbound
│   │   ├── netsolp.py          # ESM-based, GPU, batched
│   │   └── novelty.py          # CDR-H3 identity vs Keytruda | germline
│   ├── score.py                # raw → bands → categories → final; viability + margins
   ├── submit/                 # ADDED 2026-09-20 — the handbook's §4.1 tree, asserted
   │   ├── pae.py              # Boltz .npz → AlphaFold-style design_X_pae.json
   │   └── package.py          # FASTA/PDB writers that assert on the BYTES they wrote
│   ├── liabilities.py          # N-X-S/T, NG/DG motifs, exposed Met, pI, net charge
│   ├── design/
│   │   ├── mpnn.py             # ProteinMPNN / LigandMPNN wrapper
│   │   ├── graft.py            # germline framework transplant onto 5GGS geometry (Ch2-B)
│   │   ├── epitope.py          # PD-L1 footprint on PD-1 from 5IUS -> RFdiffusion hotspots
│   │   ├── baseline.py         # plain MPNN at defaults: the control the funnel must beat
│   │   └── diversity.py        # CDR-identity clustering for batch selection
│   ├── fold/
│   │   ├── base.py             # Predictor Protocol
│   │   ├── boltz.py            # PRIMARY (torch-cu128, verified on this GPU)
│   │   ├── colabfold.py        # consensus (JAX-on-Blackwell unproven)
│   │   ├── batch.py            # BUILT 2026-09-19: N complexes per boltz invocation (1.16x)
│   │   ├── chai.py             # consensus third
│   │   └── msa_cache.py        # PD-1 MSA fetched once, reused forever
│   ├── select/
│   │   ├── surrogate.py        # BUILT 2026-09-19 — but NOT what this line first meant.
│   │   │                       # Planned: a ranker over cheap PRE-FOLD features.
│   │   │                       # Built: a continuous stand-in for the BANDED rubric score,
│   │   │                       # same metrics and weights, step replaced by interpolation
│   │   │                       # through the same anchors. The cheap-feature ranker was
│   │   │                       # overtaken — aromatic content became a filter, not a ranker.
│   │   └── rules.py            # margin filter → max-min-binding → novelty tiebreak
│   ├── validate/
│   │   ├── consensus.py        # cross-predictor pose RMSD + ipSAE spread
│   │   ├── ensemble.py         # CDR-H3 conformational spread  ← the pitch differentiator
│   │   ├── specificity.py      # decoy antigens
│   │   ├── ablation.py         # hotspot → Ala, ΔG should collapse
│   │   └── epitope.py          # PD-L1 footprint overlap from 5IUS
│   └── submit/
│       ├── build.py            # assemble TEAM_NAME/ tree
│       └── check.py            # every format invariant from the handbook
├── scripts/                    # thin CLIs; all logic lives in src/
│   ├── 00_doctor.py            # env + GPU + tool versions + numpy isolation check
│   ├── 01_fetch_refs.py
│   ├── 02_calibrate.py         # the four-way ground-truth study → Gate 0
│   ├── 03_generate.py          # --challenge {1,2}
│   ├── 04_prefilter.py         # S1–S3
│   ├── 05_fold.py              # --tier {screen,confirm}; resumable
│   ├── 06_score.py             # re-runnable over the whole corpus
│   ├── 07_select.py
│   ├── 08_validate.py
│   └── 09_package.py
├── data/
│   ├── refs/                   # 5GGS, 5DK3, 5IUS, 5WT9
│   ├── msa_cache/              # keyed by sequence hash
│   └── germline/               # IGHV3-23, IGKV1-39, … + germline CDR-H3 reference set
├── runs/<hash>/                # complex.pdb, pae.json, meta.json  ← the expensive artefacts
└── results/
    ├── calibration.csv
    └── designs.parquet         # one row per candidate, the spine of the analysis
```

---

## 3. The environment split (forced by the numpy conflict)

```
~/.venvs/locksmith          main: torch-cu128, MPNN, boltz, chai, ESM, pandas, biotite
~/.venvs/locksmith-dockq    DockQ only              (numpy<2)
~/.venvs/locksmith-prodigy  prodigy-prot, freesasa  (numpy>=2)
~/.venvs/netsolp            onnxruntime, fair-esm, torch-CPU   (numpy 2)
~/.venvs/colabfold          colabfold 1.6.3, alphafold-colabfold 2.3.20, jax[cuda12] 0.10.2
```

Model weights, also outside the vault (6 GB of ONNX and 5.3 GB of AF2 params must not
sync to the Windows machine):

```
~/.local/share/locksmith/netsolp/   predict.py, data.py, models/*.onnx   (4.7 GB)
~/.cache/colabfold/params/          18 AF2 weight files                   (5.3 GB)
```

NetSolP's torch is the **CPU** wheel deliberately: the models are quantized ONNX, torch is
used only for `DataLoader` and the tokeniser, so solubility runs on CPU *concurrently with
GPU folding* and never contends for the fold queue.

The 6.05 GB source tarball still sits at `vendor/netsolp/` inside the vault, but is now
**excluded from Syncthing** via `/.stignore` at the vault root. Scoped to `vendor/netsolp`
and NOT to `vendor/`, because `vendor/ipsae/ipsae.py` is load-bearing and must keep syncing.
`.stignore` is per-device and is itself not synced, so any new device needs its own copy.

`uv tool install` each conflicting tool into its own environment; `metrics/dockq.py` and
`metrics/prodigy.py` shell out and parse stdout. The subprocess boundary is not a workaround to
apologise for — it is what lets us pin each tool to the organisers' likely version independently,
which is the §14-C1 mitigation.

Every venv outside the vault; `UV_PROJECT_ENVIRONMENT` re-exported in every shell.

---

## 4. Core types

```python
# types.py
@dataclass(frozen=True)
class Design:
    design_id: str
    challenge: Literal[1, 2]
    h_seq: str; l_seq: str; ag_seq: str
    # provenance — stamped at creation, unreconstructable later
    parent: str            # "5GGS" | germline id
    generator: str         # "ligandmpnn-1.0"
    seed: int; temperature: float
    mpnn_logprob: float

@dataclass(frozen=True)
class FoldResult:
    pdb: Path; pae: Path
    predictor: str; params_hash: str
    plddt_mean: float; ptm: float; iptm: float
    runtime_s: float
    seed: int; model_idx: int

class Predictor(Protocol):
    name: str
    def predict(self, d: Design, *, tier: Tier, seed: int) -> list[FoldResult]: ...
```

Metric signature — deliberately returns **raw values only**, so banding stays in one place:

```python
# metrics/registry.py
MetricFn = Callable[[Design, FoldResult, Context], dict[str, float]]
```

`sasa.py` returns **both** `cdr_sasa_bound` and `cdr_sasa_unbound`; `config/metrics.yaml` decides
which one the rubric means. That is the §14-C1 lesson made structural.

---

## 5. `config/metrics.yaml` — the rubric as data

```yaml
conventions:
  cdr_sasa: bound          # unresolved — flip and re-run 06_score.py, costs seconds
  submission_form: fab     # unresolved — their example FASTA is Fab-length
  numbering: imgt
  # ADDED 2026-09-20 after reading the handbook directly. Each is a place the handbook
  # is genuinely silent; each carries its quote in metrics.yaml. See
  # results/handbook_conformance.md for the finalist's score under every reading.
  band_value: top          # bottom | midpoint | top. §5.2 gives RANGES ("Good (9-10)")
                           # and never says how to pick inside one. Finalist scores
                           # 81.0 / 87.5 / 94.0 (was 84.0/90.0/96.0 before the
                           # 2026-09-25 DockQ unrounding fix). Default `top` because §7.3 states the
                           # range as 0-100 and only `top` attains it. A uniform monotone
                           # relabelling: moves the number, never the ranking.
  dockq_interface_agg: global   # min | mean | max | global. A 3-chain complex has three
                           # interfaces; §6.1.2 names no rule. Finalist: 0.755 / 0.805 /
                           # 0.855 / 0.850 — `min` alone is a band lower. `global` is
                           # DockQ v2's own Total DockQ, what an evaluator actually gets.
  netsolp_construct: fv    # §6.2.1 says "the Fv (VH + VL)" twice; the code fed it Fab
                           # chains until 2026-09-20. Fv FLIPS which chain limits:
                           # pembrolizumab VH 0.733 / VL 0.569 (light limits) vs
                           # Fab 0.623 / 0.626 (heavy limits).
  cdr_sasa_chains: AB      # all six CDRs vs heavy-only; §6.1.6 says "loops (paratope)".
                           # Costs 0 points here — Good either way.
weights: {binding: 0.60, developability: 0.20, novelty: 0.20}
margin_fraction: 0.20      # clear each gate by 20% of band width  (§14-C1)
metrics:
  ipsae:    {good: [0.80, inf], medium: [0.60, 0.80], min: 0.60, challenges: [1, 2]}
  dockq:    {good: [0.80, inf], medium: [0.49, 0.80], min: 0.23, challenges: [1]}
  dg:       {good: [-inf, -12], medium: [-12, -10],   max: -6,   challenges: [1, 2]}
  contacts: {good: [25, inf],   medium: [15, 25],     min: 10,   challenges: [1, 2]}
  iface_plddt: {good: [80, inf], medium: [70, 80],    min: 65,   challenges: [1, 2]}
  cdr_sasa: {good: [600, inf],  medium: [300, 600],   min: 250,  challenges: [1, 2]}
  netsolp:  {good: [0.70, inf], medium: [0.50, 0.70], min: 0.50, challenges: [1, 2]}
  cdrh3_id: {good: [0, 70],     medium: [70, 90],     max: 95,   challenges: [1, 2]}
```

---

## 6. `designs.parquet` schema

One row per candidate. Wide and flat — this is an analysis table, not a normalised store.

```
design_id challenge parent generator seed temperature mpnn_logprob
h_seq l_seq ag_seq cdr_h1 cdr_h2 cdr_h3 cdrh3_len
cdrh3_identity netsolp pi net_charge liability_flags n_glyc_sequons
fastfold_cdrh3_rmsd                       # cheap surrogate feature
fold_hash predictor predictor_tier model_idx runtime_s
ipsae dockq dg contacts iface_plddt cdr_sasa_bound cdr_sasa_unbound
band_* (8 cols) binding_cat dev_cat novelty_cat final_score
viable min_margin failing_gates
```

---

## 7. Build order, mapped to the plan's gates

| # | Build | Unblocks | Gate |
|---|---|---|---|
| 1 | `00_doctor.py`, `pyproject.toml`, the three venvs | everything | — |
| 2 | `io/`, `numbering.py`, `config.py`, `types.py` | all metrics | — |
| 3 | `metrics/*`, `score.py`, `config/metrics.yaml` | selection, calibration | — |
| 4 | `01_fetch_refs.py`, `02_calibrate.py` | trust in the harness | **Gate 0** |
| 5 | `submit/check.py` + **dummy-file dry run** | de-risks the fatal failure | §14-C7 |
| 6 | `fold/base.py` + `fold/boltz.py`, `msa_cache.py` | everything downstream | **G1a/G1b** |
| 6b | *(concurrent, no GPU contention)* `metrics/netsolp.py` real impl; DockQ divergence test; `design/epitope.py` | `viable=True`; Ch2 hotspots | **G1e** |
| 7 | `fold/colabfold.py` | ipSAE cross-calibration | **G1d** |
| 8 | `design/mpnn.py`, `design/baseline.py`, `liabilities.py` | the control | **G2** |
| 9 | `05_fold.py` (resumable), `06_score.py` | batch campaigns | — |
| 10 | `select/rules.py` → `select/surrogate.py` | Ch1 shortlist | **G3** |
| 11 | `design/graft.py` + RFantibody attempt | Ch2 | **G4** |
| 12 | `validate/*` | the dossier — *the deliverable* | **G5** |
| 13 | `submit/build.py` | clean output artefacts (not a gate) | — |

Note items 9 and 10: **rules before surrogate**, and the germline graft only after Challenge 1 is
locked. Both are deliberate — a working dumb selector beats a broken clever one, and Challenge 1
is the design with a safety net.

---

## 7b. Packaging and the artifact-only validator (2026-09-20)

`scripts/57_build_submission.py` writes the handbook's tree; `scripts/58_validate_submission.py`
checks it. **The validator takes only the packaged folder** — it imports nothing from `runs/`,
reads no cached score, and re-derives all eight metrics from the three files per design. Its one
external input is the DockQ reference (PDB 5GGS, public, named in §3.1), passed as a CLI
argument so it cannot silently fall back to ours.

The rule behind both: **validate the artifacts, not the pipeline that produced them.** A check
that reuses our own intermediate state proves nothing about what an evaluator sees. Concretely
the FASTA is verified against the bytes on disk (six lines, three records, headers exactly
`>Heavy_Chain`/`>Light_Chain`/`>Antigen` in order) and every PDB chain is compared
residue-by-residue to the FASTA, not merely by length.

Verified both directions: a correct package exits **0**; lowercasing one FASTA header exits
**1** and names the violation with its handbook section.

Extra dependency: `python-pptx==1.0.2`, for the pitch deck slot.

---

## 8. Two invariants worth asserting in code

**A program that runs without error is not evidence it did what you intended.** Two asserts earn
their place:

1. `score.py` on the native 5GGS **must** return viable. Wire it as a test, not a manual check —
   if a refactor breaks the harness, the pembrolizumab canary fails immediately.
2. Every fold job that exits non-zero **deletes its artefact directory**. A half-written PDB that
   still parses is worse than no PDB: it produces plausible numbers from broken data.

3. **Exit code is NOT a success signal — verify the artefacts.** Measured 2026-09-15: Boltz hit
   `ModuleNotFoundError: No module named 'cuequivariance_torch'` inside its prediction loop,
   swallowed the exception, printed a traceback to stdout, and **exited 0**. It produced no
   structure and no PAE.

   A resumable batch keyed on exit status would have recorded that design as complete and moved
   on, leaving a silent hole in the campaign that only surfaces much later as "why do I have 200
   designs and 40 scores?". So `05_fold.py` must treat a run as successful only when the expected
   `*_model_0.pdb` **and** PAE file both exist and parse — never when the process merely returned.

   This is the same lesson as the mislabelled-telemetry incident in LEARNINGS.md, one level up:
   there the workload subprocess died and the collector carried on; here the subprocess *reports*
   that it succeeded. Assert on the artefact, not on the exit code.
