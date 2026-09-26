---
date: 2026-09-22
tags:
  - session
  - locksmith-antibody-hackathon
status: living
---

Tags: [[Learning]], [[locksmith-antibody-hackathon]]

# Session 2026-09-22 (third) — Fixing liabilities, and refuting our own advice

## 0. Session at a glance

**Before:** both challenges packaged and validated, but Challenge 1 still failed handbook
§9.2 while Challenge 2 had just been fixed — an inconsistency we created ourselves. Three
smaller reviewer findings were outstanding. The submission's top "next step" recommendation
had never been tested.

**Now:** **both challenges pass §9.2.** Challenge 1 96.0, Challenge 2 91.2, both viable
across all five diffusion samples. Two experiments ran, and both changed what the
submission says.

**The two results:**

1. **The contact-count rule is confirmed in both directions.** Challenge 1's `N55Q` fix is
   free where Challenge 2's `N→Q` was fatal — and the difference is exactly the number of
   antigen contacts the mutated residue carries (3 vs 10/19).
2. **"Redesign the light chain" — our own top recommendation, repeated in three documents
   and by two independent reviewers — is refuted.** It cannot work, for two independent
   reasons, and finding that out cost zero GPU folds.

**Prerequisites:** the liability scanner and the first sequon fix —
[the previous
session](2026-09-22-published-withdrawn-and-the-fix-that-killed-the-antibody.md). The rubric and its bands —
[the spec extraction](2026-09-14-antibody-hackathon-spec-and-scoring.md).

---

## 1. Concepts, from first principles

### 1.1 Asparagine deamidation, and why the neighbour matters

**Deamidation** is the spontaneous, non-enzymatic loss of the amide group from an
asparagine (Asn, N) side chain, converting it to aspartate or isoaspartate. It changes
charge (+0 → −1) and, for isoAsp, inserts an extra backbone methylene — both potentially
fatal to binding. It is one of the standard chemical-stability liabilities screened in
antibody development.

The rate depends strongly on the **following residue (n+1)**, because the mechanism goes
through a five-membered **succinimide** intermediate formed when the n+1 backbone nitrogen
attacks the Asn side-chain carbonyl. A small, flexible n+1 residue lets that ring close
easily:

| motif | relative rate | why |
|---|---|---|
| **N-G** | fastest, by roughly an order of magnitude | glycine has no side chain at all, so nothing hinders ring closure |
| N-S, N-T | moderate | small polar side chains, some hindrance |
| N-A | slower | a methyl group hinders it |
| N-(bulky) | slow | steric blocking |

Handbook §9.2 lists *"No NG/DG deamidation/isomerisation motifs in CDRs"* as a checklist
item. §9 Pillar 4 gives the remedies.

**So there are two ways to remove an `NG`:** mutate the **asparagine** (N→Q — glutamine's
side chain is one methylene longer and cannot form the five-membered ring, so it deamidates
orders of magnitude slower), or mutate the **glycine** (G→A — adds a methyl and slows ring
closure). *Only the first eliminates the chemistry; the second slows it.*

### 1.2 Glycine is not an ordinary residue to mutate

Glycine has no Cβ. That frees its backbone to occupy regions of Ramachandran space no other
amino acid can reach — in particular positive φ. Glycines in CDR loops are frequently there
because the loop conformation *requires* that freedom.

So `G→A` is not obviously the safe choice even when the glycine makes **zero** antigen
contacts: it may be doing conformational work rather than binding work. This is the same
mechanism we invoked (untested) last session to explain why Challenge 2's zero-contact
`S→A` still cost 0.1 ipSAE.

> **Transferable principle.** "Makes no contacts" and "can be mutated freely" are different
> claims. A residue can be load-bearing for the *shape* that positions other residues. The
> contact count tells you about the first-order effect only.

### 1.3 `min()` as an aggregator creates a hard ceiling

Challenge 1's NetSolP score is `min(VH, VL)` — a design is only as soluble as its worse
chain. The consequence is not symmetric with a mean: **improving the better chain does
nothing at all, and improving the worse chain helps only until it crosses the other.**

Formally, for the aggregate to reach a threshold `t`, you need `VH ≥ t` **and** `VL ≥ t`.
Our VH is **0.699** against `t = 0.70`. So

```
max over all possible light chains of  min(0.699, VL)  =  0.699  <  0.70
```

**The band cannot move by redesigning the light chain, by 0.001.** That is a two-line
calculation available at any point in the past week, and it invalidates a recommendation
we had made in three documents.

> **Transferable principle.** Before optimising a component, check the aggregator. Under
> `min`, effort spent on anything but the current argmin is wasted, and effort on the
> argmin is wasted past the point where it stops being the argmin.

---

## 2. What was done

### 2.1 Challenge 1's deamidation motif — `scripts/83_ch1_ng_fix.py`

`metrics/liabilities.py` (written last session) found that Challenge 1 also fails §9.2:
`NG` at heavy **55–56**, inside CDR-H2. It is pembrolizumab's own motif — but **both
positions sat inside the 29 IMGT positions ProteinMPNN was allowed to design**, so keeping
it was a choice nobody knew they were making. Our redesign changed CDR-H2 at exactly one
position (S54L) and left `N55-G56` intact.

**Contacts measured first**, on the submitted complex at 4.5 Å heavy-atom:

| residue | contacts to PD-1 |
|---|---|
| H L54 | 5 |
| **H N55** | **3** |
| **H G56** | **0** |
| H G57 | 14 |

Both arms folded at Challenge 1's exact submitted settings — Fab construct, `recycling_steps=3`,
seed 71, `--use_msa_server` — with `diffusion_samples=5`, so arms are compared on envelopes
rather than on a single argmax (see [last session §1.3](2026-09-22-published-withdrawn-and-the-fix-that-killed-the-antibody.md) for why `model_0` is an order statistic).

### 2.2 The light-chain redesign — `scripts/84_light_chain_redesign.py`

24 light chains from ProteinMPNN at T=0.1, seed 4242, designing chain B with chains A and C
as context, screened on NetSolP. **No folds at all** — NetSolP is sequence-only, so the
entire experiment is CPU and costs nothing on the GPU.

### 2.3 Three smaller fixes

- **PDB chain termination.** Boltz writes `TER` after the first two chains then goes
  straight from the last chain-C atom to `END`. Nothing in our stack minds, but a stricter
  parser may merge chains B and C — which would silently score the wrong interface.
  `submit/package.py` now emits a `TER` after the final polymer and strips the trailing
  whitespace line. Both PDBs now carry **3** `TER` records.
- **Challenge 2 reproduction doc.** Challenge 1 shipped `reproducing_our_numbers.md` and
  Challenge 2 did not. It now does, and records the germline-novelty convention explicitly
  alongside a reviewer's alternative reading (40.0% by global alignment vs our 30.0% by
  V-prefix/D-substring/J-suffix coverage — both defensible against §6.3.1's silence, both
  far inside the Good band).

---

## 3. Results

### 3.1 Challenge 1: both fixes work, one is free

| | mutation | §9.2 | ipSAE over 5 samples (span) | DockQ | `model_0` final | viable |
|---|---|---|---|---|---|---|
| baseline | — | **FAIL** | 0.822–0.861 (0.039) | 0.711–0.820 | 96.0 | 5/5 |
| **N55Q — SUBMITTED** | remove the acceptor | **PASS** | **0.791–0.836 (0.044)** | 0.682–0.815 | **96.0** | **5/5** |
| G56A | remove the fast n+1 | PASS | 0.779–0.868 (0.089) | 0.695–0.820 | 94.0 | 5/5 |

**Chosen: N55Q.** Three reasons, in order of weight:

1. **Composite 96.0 vs G56A's 94.0** at `model_0` — G56A's DockQ lands lower on the
   submitted sample.
2. **Envelope 0.044 vs 0.089**, against a baseline of 0.039. G56A more than doubles the
   diffusion-sample spread; N55Q barely moves it. Given §1.2, this is consistent with the
   glycine doing conformational work.
3. **Better chemistry** (§1.1): N→Q eliminates the succinimide route; G→A only slows it.

**Cost to reverse:** trivial — one line in `scripts/57_build_submission.py`, which reads the
variant from `runs/ch1_ng_fix/results.json` if present.

### 3.2 The same rule, measured in both directions

| | mutated residue's antigen contacts | ipSAE before → after |
|---|---|---|
| Challenge 2 `N→Q` | **10 and 19** | 0.864 → **0.014** (dead, ±0.001 over 5 samples) |
| Challenge 1 `N55Q` | **3** | 0.822 → **0.821** (unchanged) |

**`N→Q` is not inherently dangerous and `S→A` is not inherently safe.** The handbook lists
both remedies on one line as interchangeable. What actually predicts the outcome is how
much of the interface the mutated residue is carrying — a one-minute calculation on a
structure already in hand.

> **Transferable principle, now confirmed twice.** A developability fix is a *design
> change*. Prescribed remedies are not interchangeable, and the structure adjudicates
> between them faster than any amount of reasoning about chemistry.

### 3.3 The light-chain recommendation is refuted, twice over

| | value |
|---|---|
| pembrolizumab VL (baseline) | 0.5690 |
| best of 24 ProteinMPNN redesigns | **0.5920** (+0.0230) |
| designs reaching VL ≥ 0.70 | **0 / 24** |
| improvement required | **+0.131** |
| improvement achieved | **+0.023** — short by a factor of **5.7** |
| designs introducing new CDR liabilities | **24 / 24** (3–5 each) |

**Reason one (§1.3):** the ceiling is the heavy chain. `min(0.699, anything) ≤ 0.699 < 0.70`.

**Reason two:** even ignoring the ceiling, plain ProteinMPNN gets nowhere near. It optimises
**sequence recovery given a fixed backbone** — solubility is simply not in its loss
function, so there is no reason it should improve NetSolP except by accident.

**And it makes things worse elsewhere:** every one of the 24 introduces new CDR liabilities,
the same behaviour that put two glycosylation sequons into the Challenge 2 paratope.
Unconstrained ProteinMPNN adds developability problems at a high rate and nothing in the
rubric penalises it.

**What the deficit actually needs:** a solubility-aware objective — a filter over sampled
sequences, or a different sampler. Corrected in the shipped Challenge 1 doc and on the deck,
where the wrong advice had been repeated.

---

## 4. What went wrong

### 4.1 The session crashed mid-flight and both GPU jobs died

Neither had checkpointed output, so both restarted from zero. Both scripts *were* written
to resume on artefacts (`if pred.exists() and list(pred.glob(...))`), which is why the
restart was a one-line relaunch rather than a rebuild — but neither had produced an artefact
yet, so resume bought nothing this time. Two uncommitted local fixes survived because they
were on disk.

**Lesson:** resume-on-artefact protects against losing *completed* work. It does nothing for
work in flight, and a long first fold is exactly the window where a crash costs most.

### 4.2 `MpnnDesign` names its fields by ROLE, not by chain

`mpnn.generate(..., design_chain="B")` returns objects whose `.heavy` attribute holds the
**designed light chain**, because inside `generate()` the local is named for its role:

```python
heavy = seq_for_folding(pdb, design_chain)        # "B" -> the LIGHT chain
light = seq_for_folding(pdb, context_chains[0])   # "A" -> the HEAVY chain
```

Reading `d.light` — the obvious thing — would have screened the *heavy* chain for 24
variants and reported that light-chain redesign changes nothing. **A silent wrong answer
that confirms the hypothesis under test.** Caught only because the first attempt crashed on
an unrelated unpacking error and forced a read of the signature.

> **Transferable principle.** A parameterised function whose internals are named for the
> *default* use of each parameter will mislead every non-default caller. Name them
> `designed` and `context`, or return a mapping keyed by chain.

### 4.3 The designed chain and the submitted construct are different lengths

ProteinMPNN designs against the **coordinate** sequence of 5GGS chain B (217 aa); the
handbook §4.2.2 light chain is **218**. Comparing them directly would have compared two
different molecules. Fixed by locating the coordinate sequence inside the handbook construct
(offset 0) and grafting only the positions that changed.

### 4.4 A variable-shadowing bug I introduced

I added `c = cfg.conventions` to `scripts/75_challenge2_package.py` for the new reproduction
doc. The selection loop already contains:

```python
for r in viable:
    c = cond.get(bb)      # the conditioning record for this backbone
```

so by the time the f-string evaluated, `c` was a per-backbone dict and the lookup raised
`KeyError: 'ipsae_pae_cutoff'`. Renamed to `conv`.

**It failed loudly, which was luck.** Had the conditioning record happened to contain a key
of the same name, the document would have shipped a plausible wrong number. Single-letter
names in a function long enough to need them are how that happens.

---

## 5. Verification

```bash
uv run python scripts/83_ch1_ng_fix.py          # both arms, 5 diffusion samples each
uv run python scripts/84_light_chain_redesign.py # 24 light chains, zero folds
uv run --with python-pptx python scripts/57_build_submission.py
uv run python scripts/75_challenge2_package.py
uv run python scripts/58_validate_submission.py submission/LOCKSMITH_DEV
uv run --with pytest pytest tests/ -q            # 29 passed
```

**Healthy output, concretely:**

- `VALIDATION PASSED`, Challenge 1 **96.0 viable**, Challenge 2 **91.2 viable**
- Challenge 1 heavy 54–57 reads **`LQGG`** (was `LNGG`)
- Challenge 2 heavy 52–54 reads **`NVA`**, light 49–51 **`NAA`**
- `liabilities.compute(...).handbook_9_2_pass()` returns **PASS for both challenges**
- **3** `TER` records in each PDB
- both `docs/` folders contain `methods_and_limitations.md` *and*
  `reproducing_our_numbers.md`

**What a plausible-but-wrong result looks like here:** the light-chain screen reporting
"redesign changes nothing" — which is what you get from reading `MpnnDesign.light` (§4.2)
and screening the heavy chain 24 times. It would have *confirmed* the null we were testing,
looked entirely reasonable, and been completely wrong. The tell is that VL would be
identical across all 24 rather than varying by ±0.02.

---

## 6. Honest assessment

**Solid.** Both challenges now pass a handbook developability checklist item that neither
passed this morning, and Challenge 1's fix cost nothing. The contact-count rule has now
been confirmed on two independent designs in opposite directions, which is the difference
between an anecdote and a usable heuristic.

**The best thing here is a negative result.** We tested our own most-repeated
recommendation and it failed for two independent reasons, one of which was a two-line
calculation available all week. That correction is worth more to a reader than the fix.

**Crude.** The light-chain screen is 24 sequences at a single temperature from a single
sampler. "ProteinMPNN cannot do this" is supported; "nothing can" is not tested. A
solubility-aware objective was not attempted.

**Unresolved.** Why Challenge 2's zero-contact `S→A` cost 0.1 ipSAE while Challenge 1's
zero-contact-adjacent `N55Q` cost nothing. The conformational explanation (§1.2) fits both
but remains untested.

**Not established.** That either antibody binds anything. Removing a deamidation motif and
a glycosylation sequon improves the *molecule's developability profile*; it says nothing
about affinity, and this project's SKEMPI work showed the metric stack does not track
affinity in either direction.

---

## 7. Glossary

**Deamidation** — spontaneous loss of the Asn amide, via a succinimide intermediate; rate
set largely by the n+1 residue, fastest at Gly.
**Succinimide** — the cyclic five-membered intermediate; its formation is what the n+1
residue hinders or permits.
**Isoaspartate** — a deamidation product with an extra backbone methylene, structurally
disruptive.
**Sequon** — `N-X-S/T` (X ≠ P), the N-linked glycosylation recognition motif.
**`min` aggregator** — takes the worse of two chain scores; creates a hard ceiling at the
better chain's value.
**Diffusion sample** — one draw from the structure module; Boltz returns them ranked, so
`model_0` is an argmax rather than a sample.
**Ramachandran space** — the φ/ψ backbone dihedral plane; glycine, lacking a Cβ, accesses
regions no other residue can.
