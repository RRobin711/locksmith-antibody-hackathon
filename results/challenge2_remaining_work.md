# What is left to produce a complete Challenge 2 submission
**2026-09-22.** Read from the handbook text (§3.2, §4.3-4.5, §5.2, §7.2) and the repo as it
stands, not from any summary.

## 1. What the handbook requires, and whether we can satisfy it

### Structure (§4.3, §4.5 checklist)

```
TEAM_NAME/
├── TEAM_NAME_Challenge2/
│   ├── structures/   design_X_complex.pdb , design_X_pae.json   (prefixes must match)
│   ├── sequences/    design_X.fasta   (>Heavy_Chain, >Light_Chain, >Antigen)
│   ├── metrics/      optional
│   └── docs/         optional
└── pitch/            TEAM_NAME_presentation.pptx
```
**One design only per challenge.** Everything zipped as `TEAM_NAME.zip`.

| Requirement | Can we satisfy it? | With what |
|---|---|---|
| `design_X_complex.pdb`, chains A/B/C | **Yes** | `fold/boltz.py:write_input` already writes `A`=heavy, `B`=light, `C`=antigen — the submission convention, no relabelling needed |
| `design_X_pae.json` (AlphaFold style) | **Yes** | `submit/pae.py:write_pae_json(pdb, pae_npz, out)` exists and was round-tripped for Challenge 1 |
| `design_X.fasta`, 3 exact headers | **Yes** | `submit/package.py:write_fasta`, `HEADERS` constant |
| Folder tree + zip | **Yes, after a small fix** | `submit/package.py:build_challenge(root, team, challenge, ...)` is **generic in `challenge`**; only the driver scripts hardcode 1 (below) |
| `pitch/*.pptx` | **Not built** | outline exists (`results/pitch_outline.md`); no .pptx |

> **Handbook contradiction, unresolved:** §4.4 says *"Presentation Time: 3 minutes maximum"*;
> the §4.5 checklist says *"(5 min, PPT format)"*. Both are in the same document. The deck
> outline is built to 3 min, which is the safer reading. **Unestablished which is binding.**

### Hard cutoffs (§7.2) — Challenge 2 applies **seven**, not eight

| Metric | Minimum | Band Good (§5.2) | Have the code? | Have a number? |
|---|---|---|---|---|
| ipSAE | ≥ 0.60 | ≥ 0.80 | yes | **no** — needs Boltz fold |
| ΔG | ≤ −6 kcal/mol | ≤ −12 | yes | **no** |
| Contacts | ≥ 10 | > 25 | yes | **no** |
| Interface pLDDT | ≥ 65 | > 80 | yes | **no** |
| CDR SASA | > 250 Å² | > 600 | yes | **no** |
| NetSolP | ≥ 0.50 | ≥ 0.70 | yes | **no** |
| CDR-H3 identity **to germline** | < 95% | < 70% | **built, NOT wired** | **no** |
| DockQ | — | — | **excluded**: `config/metrics.yaml:99` `challenges: [1]`, matching §5.2 "Ch 1 only" | n/a |

## 2. What the pilot produced against that list

The pilot produced **36 backbones, 30 MPNN sequences, 30 RF2 predictions** — and **none of
the seven scored metrics**. RF2's `interaction_pae` / `pred_lddt` are RFantibody's own
outputs and appear nowhere in the handbook's rubric.

**The blocking gap is physical, not computational: nothing is on this machine.**
Every design lives on the stopped pod's volume disk (`/workspace/c2`, 443 MB). A local
`find` for `*dldesign*` / `bb_*.pdb` returns nothing. **To proceed at all, the 30 designed
heavy/light sequences must be retrieved from the pod.**

| Needed output | Status |
|---|---|
| Designed H/L sequences | **on the stopped pod only** — must retrieve |
| `design_X_complex.pdb` | does not exist — needs a **local Boltz-2 fold** |
| `design_X_pae.json` | does not exist — needs the fold, then `write_pae_json` |
| `design_X.fasta` | trivially derivable once sequences are local |
| Seven metric values | do not exist — need the fold, then the harness |
| Germline novelty number | **metric exists, not wired into scoring** |

### Format gaps, specifically
- **PAE converter:** exists and works. No gap.
- **Chain assignment:** no gap — Boltz already emits A/B/C in submission order.
- **Germline novelty:** `metrics/germline.py` is built and validated, but
  `config/metrics.yaml:153` still reads `novelty: [cdrh3_identity]`, which compares to
  **pembrolizumab**. Scoring a Challenge 2 design today would apply Challenge 1's reference.
  Needs a band entry + wiring in `score.py`.
- **Driver scripts:** `scripts/57_build_submission.py:98,190` hardcode `challenge=1`;
  `scripts/58_validate_submission.py:70` branches `if challenge == 1`. `build_challenge()`
  itself is generic.

## 3. What the pilot falsified in the original plan

**DELETED — selection by composite or `interaction_pae`.** ICC **0.000** (F=0.70,
between-dock variance below within-dock). The pre-registered fallback stands:
**selection is by hotspot contact count, tie-broken on `frac_iface_on_epitope`.** That rule
was fixed in `results/prereg_2026-09-21_challenge2.md` before any score existed and must not
be revisited now that scores are in view.

**DELETED — RF2 as validation.** Mean `target_aligned_antibody_rmsd` **24.87 Å** (CDR 19.20 Å)
between RF2's prediction and the designed dock. RF2 contradicts rather than confirms, so the
plan's "RF2 filtering → confidence the design is real" step produces no evidence. It may
still act as a crude liveness filter, but nothing it outputs can appear as support.

**DELETED — "best of N".** With no valid ranking metric, the submitted design is *a*
gate-clearing design chosen by a pre-registered rule, not the best of 30.

**SURVIVES:** Boltz-2 fold of candidates; the seven-metric harness and its gates; the
packager and artefact-only validator; the epitope knockout as the one control that
discriminated; the honest-deliverable framing in §7.4.

## 4. Remaining work

| # | Task | Time | Local? |
|---|---|---|---|
| 1 | **Restart pod, retrieve 30 sequences + 36 backbone PDBs, stop it again** | 20 min | **NO — pod** (~$0.20) |
| 2 | Wire germline novelty into `config/metrics.yaml` + `score.py`; band `< 70 / 70-90 / > 90`, cutoff `< 95` | 1.5 h | local |
| 3 | Un-hardcode `challenge` in `57_build_submission.py` and `58_validate_submission.py` | 30 min | local |
| 4 | **Boltz-2 fold 30 designs** (H/L designed + PD-1 antigen), 1 seed | 45 min | local **GPU** (RTX 5070 Ti; Boltz runs fine here — this is Challenge 1's proven path) |
| 5 | Run the seven-metric harness + gates over the 30 | 30 min | local |
| 6 | Apply the **pre-registered** selection rule; record why each higher-scoring design was not chosen | 20 min | local |
| 7 | Epitope knockout on the selected design (~8 folds) | 25 min | local GPU |
| 8 | Build + validate `LOCKSMITH_DEV_Challenge2/` with the artefact-only validator | 45 min | local |
| 9 | `docs/methods_and_limitations.md` for Challenge 2 | 1 h | local |
| 10 | Fill slide 5 of the deck; produce the .pptx | 1.5 h | local |
| | **Total** | **≈ 7 h** | all local except #1 |

**Only step 1 is off-machine**, and only because the designs were never pulled down before
the pod was stopped. That is a process failure, not a technical constraint: the retrieval is
a file copy, and the pod must be restarted solely to serve it.

## 5. Unestablished — flagged rather than assumed

- **Whether any of the 30 designs clears the seven gates.** No metric has been computed. The
  gate pass rate is completely unknown, and it is possible that **zero** designs pass.
- **Whether Boltz-2 will place these de novo antibodies sensibly.** The post-cutoff test
  measured median Fab DockQ **0.291** on novel antibody-antigen complexes. These are more
  novel than that test set.
- **NetSolP on de novo VH/VL.** Every prior NetSolP number in this project came from
  pembrolizumab-derived sequences. Untested on this sequence space.
- **Germline CDR-H3 identity of the MPNN designs.** Expected low (the <95% gate is free —
  see `results/germline_metric_validation.md`), but not computed.
- **Which presentation length is binding** (§4.4 vs §4.5).
- **Whether the volume disk survived the stop intact.** Asserted by RunPod's dialog
  ("data not in your volume disk will be lost", ours is in `/workspace`), not verified.
