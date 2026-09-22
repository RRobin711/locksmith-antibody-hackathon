# Route A on cloud GPU — concrete plan

Written 2026-09-20 after Gate 0 failed locally (see `results/rfantibody_risk_scope.md` §1a:
both the shipped cu118 stack and the best modified cu124 stack fail on `sm_120` with
"no kernel image", no PTX shipped, and DGL's exact `torch==2.4.0` pin closing the
bring-your-own-torch workaround).

The point of moving off this machine is narrow: **RFantibody's stack is fine, our GPU is
the problem.** On any Turing/Ampere/Ada card the shipped environment installs as documented
with zero porting.

---

## 1. Division of labour, stated plainly

**I cannot run this myself.** Colab needs your Google account and a browser session. So:

| who | what |
|---|---|
| me | write the notebook, build and validate the input files, hand you a folder to upload |
| you | open the notebook, run it, leave it running, download one results archive |
| me | everything downstream — fold with Boltz-2 here, score, select, package |

The cloud part is one notebook and one download. Everything requiring judgement stays here.

---

## 2. Which service — and free Colab is probably the wrong choice

| option | GPU | session limit | cost | verdict |
|---|---|---|---|---|
| **Colab free** | T4 16 GB, *not guaranteed* | ~4 h typical, 90 min idle kill | £0 | works, but see §4 — one disconnect costs the run |
| **Kaggle Notebooks** | T4×2 or P100 | **12 h**, 30 GPU-h/week | £0 | **better free option** — longer sessions, persistent `/kaggle/working` |
| **Colab Pro** | L4/A100 | 24 h | ~£9/mo | removes the timeout risk |
| **RunPod / Vast.ai** | A10 / 3090 / 4090 | none | **~£0.25/h, so ~£3 for the whole job** | most reliable; a real terminal, not a notebook |

**Recommendation: RunPod or Kaggle, not free Colab.** Three pounds of rented A10 removes
every session-limit risk in §4, and a plain SSH box is a far better fit for a three-stage
CLI pipeline than a notebook that dies when the tab sleeps. If it must be free, Kaggle's
12-hour session beats Colab's.

---

## 3. What actually runs

RFantibody is three CLI stages. Real commands from its README:

```bash
# 0. install (~10-15 min, once per session unless weights are cached)
git clone https://github.com/RosettaCommons/RFantibody.git && cd RFantibody
bash include/download_weights.sh          # 4 checkpoints from files.ipd.uw.edu + Zenodo
uv sync                                   # provisions Python 3.10 itself

# 1. backbone diffusion, CDR loops conditioned on the epitope
rfdiffusion -t pd1_T.pdb -f hu-4D5-8_Fv.pdb -q backbones.qv -n 30 \
    -l "H1:7,H2:6,H3:5-13,L1:8-13,L2:7,L3:9-11" \
    -h "T64,T66,T68,T70,T74,T76,T78,T81,T85,T90"

# 2. sequence design on those backbones
proteinmpnn -q backbones.qv --output-quiver seqs.qv -n 4 -t 0.2

# 3. structure prediction / filter
rf2 -q seqs.qv --output-quiver preds.qv -r 10
```

**Inputs, and we already have two of the three:**

- **Target** `-t`: PD-1 from 5GGS chain C, renamed to chain **T** (HLT convention). Trivial
  conversion; we do the same relabelling in the packager already.
- **Hotspots** `-h`: the **PD-L1 competitive footprint on PD-1**, 26 residues, already
  extracted from 5IUS on 2026-09-15 and mapped across to 5GGS by explicit alignment
  (`results/epitope.md` — the two entries are only 90.1% identical, so the mapping was not
  assumed). Targeting this rather than pembrolizumab's epitope is the right call: it is the
  one that actually blocks the checkpoint, and §3.2 explicitly permits either.
- **Framework** `-f`: **`hu-4D5-8_Fv.pdb`, shipped with the repo** — a humanised scFv
  scaffold. Using their framework rather than pembrolizumab's is deliberate: it makes the
  Challenge 2 design independent of Challenge 1's scaffold, so "de novo" is defensible.

---

## 4. Runtime, and the number that decides the plan

RFdiffusion and RF2 scale **O(N²)** in residues (stated in the README; no benchmark given).
Our system is Fv ~230 + PD-1 ~113 ≈ **345 residues**, comparable to standard binder runs.

**Estimate, and it is an estimate:** ~1–2 min/backbone on an A100, so roughly **8–15 min on
a T4**. That gives:

| N backbones | T4 | A10/3090 |
|---|---|---|
| 30 | **4–8 h** | 1–2 h |
| 100 | 13–25 h | 3–6 h |

**So free Colab (≈4 h) fits about 20–30 backbones and nothing more.** That is the binding
constraint, and it is why the service choice matters more than anything else here.

**The very first thing the notebook does after install is time one backbone** and print the
projected total. If it lands far from the estimate, N is adjusted before committing the
session rather than discovering it at hour three.

Is 30 enough? RFantibody's own docs describe pilot runs at 95 designs and campaigns "in the
10k range". Thirty is a **pilot**, and the write-up will call it that. We need one design
for the folder; thirty backbones × 4 sequences = 120 candidates into RF2 is a defensible
pilot and an indefensible campaign, and the docs will not blur the two.

---

## 5. Cloud-specific risks

| risk | mitigation |
|---|---|
| **Session dies mid-run** | Write every backbone to Drive / `/kaggle/working` as produced, and make the notebook resumable — count finished designs and skip them. Same rule as our overnight jobs: a disconnect costs one design, not the run. |
| Re-install cost each session | Cache the 4 weight files on Drive (they are static); reinstall the env each time (~10 min). Do **not** try to persist a venv — they do not relocate. |
| No GPU allocated (free tier) | Check `nvidia-smi` in cell 1 and stop if it is CPU-only rather than silently running for hours. |
| Quiver files opaque on return | Export to plain PDB/FASTA before download — do not bring `.qv` back and hope our tooling reads it. |
| **Verifying it worked** | Same rule as everywhere here: assert on the artefact. The notebook's last cell counts output structures and refuses to package if the count is zero, rather than exiting 0 on an empty run. |

---

## 6. What comes back, and what happens here

**Download:** one archive of designed **sequences** (VH/VL) plus their RF2 backbones and
confidence scores. A few hundred MB at most.

**Then, locally and with no new dependencies:**

1. Fold each candidate as a **Fab–PD-1 complex with Boltz-2** — the same predictor as
   Challenge 1, so the two challenges are scored on one footing. RF2 is used as the cloud
   *filter*, not as the final structure.
2. Score with our harness; apply the §7.2 cutoffs (ipSAE ≥ 0.60, ΔG ≤ −6, NetSolP ≥ 0.50,
   contacts ≥ 10, interface pLDDT ≥ 65, CDR SASA > 250, **germline CDR-H3 identity < 95%**).
3. **Build the germline novelty metric** — it does not exist, it blocks any Challenge 2
   score, and it is needed whichever route runs. ~half a day.
4. Package into `TEAM_NAME_Challenge2/` with the existing builder and validator, which
   already handle `challenge=2` (DockQ correctly excluded, binding averages five metrics).

Chain naming is handled: RFantibody uses **H/L/T**, the handbook uses **A/B/C**, and
`submit/package.py` compares every chain residue-by-residue against the FASTA and raises on
a mismatch.

---

## 7. Time and cost

| | |
|---|---|
| my prep (inputs, notebook, germline metric) | **~1 day** |
| your cloud session | 4–8 h wall clock, mostly unattended |
| my downstream (fold ~100, score, select, package) | **~0.5 day** |
| **total** | **~1.5–2 days**, plus ~£3 if you take RunPod |

---

## 8. The caveat that ships with whatever this produces

Unchanged by the route. Challenge 2 has **no DockQ**, so nothing in its rubric can detect a
wrong pose. Boltz-2's median DockQ on post-cutoff complexes is **0.291**. SKEMPI showed no
metric in the stack tracks measured affinity, and PRODIGY ΔG failed the epitope-knockout
control outright.

So the Challenge 2 entry will read: *produced by target-conditioned backbone diffusion
against the PD-L1 competitive epitope, clears the §7.2 cutoffs, and is not supported by
evidence that it binds.* That is the same honesty the Challenge 1 docs carry. Route A buys
a design made the way the handbook asks for. It does not buy confidence in it.
