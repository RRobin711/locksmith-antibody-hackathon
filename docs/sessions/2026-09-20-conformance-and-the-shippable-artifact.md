# Conformance, and turning the work into a shippable artifact

**2026-09-20, evening.** The handbook read directly for the first time, every rubric
choice audited against its own words, and the result packaged into the submission tree the
handbook specifies — with a validator that reads only the package.

Self-contained. The event's deadline (14 Dec 2025) has passed; nothing is being submitted.
The goal is a correct artifact, which makes conformance a quality bar rather than a race.

---

## 1. The premise that had never been tested

Every encoding of this rubric — `config/metrics.yaml` included — was written from a
second-hand summary of the handbook. An earlier audit had already found four errors in it.
So this session treated `metrics.yaml` as a *hypothesis about* the handbook and checked
each field against the PDF.

**Result: the transcription is better than expected.** All eight band triples, all eight
minimums, the 60/20/20 weights, the aggregation formula, the ipSAE selection rule, the
chain convention and the Challenge 2 DockQ exclusion are all **MATCH**. Twenty-four
boundary checks — every band edge and every minimum, at its exact value — all MATCH,
including the four Good edges made strict earlier in the day and, importantly, the four the
handbook writes as *inclusive*, which that earlier fix did not flip by accident.

What remains is not error but **ambiguity the handbook genuinely does not resolve**, and
the job was to name each one rather than let a default stand in silently.

---

## 2. Four ambiguities, now explicit

### 2.1 Band → score is undefined, and it is worth 12 points

§5.2 gives **ranges** — "Good (9-10)", "Medium (6-8)", "Poor (0-5)" — and nowhere says how
to pick a value inside one. Three readings are implementable from the text:

| reading | Good/Medium/Poor | finalist scores | attainable max |
|---|---|---|---|
| bottom | 9 / 6 / 0 | **84.0** | 90 |
| midpoint | 9.5 / 7 / 2.5 | **90.0** | 95 |
| **top** (now default) | 10 / 8 / 5 | **96.0** | 100 |

`top` is the default because §7.3 states the Challenge score range as "0 – 100" and only
`top` attains it. **That is weaker evidence than it looks**, and the report says so: "0–100"
is a scale label rather than a claim of attainability; `top` is also the most flattering
reading, awarding 10/10 to a metric that merely clears the Good edge; and within-band
*interpolation* is a fourth reading the text permits equally, left unimplemented because it
needs an upper anchor the handbook never gives.

> The saving grace: the choice is a **uniform monotone relabelling**, so it moves the
> headline number and can never reorder two designs. A convention that changes the score by
> 12 points and the ranking by nothing is a reporting decision, not a scientific one — and
> should be labelled as such wherever the number appears.

### 2.2 DockQ over three interfaces

A three-chain complex has three interfaces; §6.1.2 says only that DockQ "returns a docking
quality score between 0 and 1". The hardcoded `min()` over the two binding interfaces
appears nowhere in the handbook. Default is now **`global`** — DockQ v2's own `Total DockQ`,
what an evaluator gets by running the tool and reading its summary line. `min`/`mean`/`max`
remain selectable and all four are tabulated.

### 2.3 and 2.4 NetSolP chain combination, CDR SASA scope

§6.2.1 says per-chain scores "are combined into a single value" without saying how; §6.1.6
says SASA of "the CDR loops (paratope)" without saying heavy-only or all six. Both are now
named fields. **Both cost zero points here** — the finalist lands in the same band under
either reading — but they are recorded because they would not be free for a design whose
VH and VL straddle 0.70.

---

## 3. The input check that could have invalidated everything, and didn't

§4.2.2 prints an example FASTA whose antigen is **123 aa**; this project folded 5GGS chain C
at **113 aa**. The instruction that prompted the check called these "a different complex"
and warned that every binding metric was computed on the wrong thing.

**They are the same complex.** Character-by-character, ours is a contiguous substring at
offset 5, and the shared core is byte-identical. Verified against the RCSB entity API, the
handbook's antigen **is 5GGS's SEQRES verbatim**; ours is 5GGS's *coordinate* sequence, five
residues unresolved at each terminus. All three chains follow the same pattern — heavy
`[1:220]` of 232, light `[0:217]` of 218, antigen `[5:118]` of 123.

This is the project's own SEQRES-versus-coordinates lesson arriving in its benign form: the
case `seq_for_folding()` deliberately *permits* (terminal truncation) rather than the
internal deletion it refuses.

Re-folding was still correct — the shipped PDB and FASTA must correspond, or the submission
has the same internal inconsistency as the coordinate-substitution exploit this project
declined in PLAN §13.6. The prediction was recorded before the folds ran: the added termini
are far from the epitope, so the metrics should barely move.

| metric | 5GGS coords | handbook constructs | Δ | band change |
|---|---|---|---|---|
| ipSAE | 0.849 | 0.864 ± 0.037 | +0.015 | none |
| DockQ | 0.850 | 0.816 ± 0.004 | −0.034 | none |
| ΔG | −12.30 | −12.83 ± 0.32 | −0.53 | none |
| interface pLDDT | 90.38 | 87.39 ± 2.07 | −2.99 | none |
| NetSolP | 0.569 | 0.569 | 0.000 | none |

**No metric crosses a band edge.** The prediction held; the premise did not.

---

## 4. A discrepancy I invented, and withdrew

Earlier the same day I reported that ipSAE from our AlphaFold-style JSON (0.8491) differed
from the Boltz `.npz` route (0.8560) and called it a code-path difference inside
`ipsae.py`. Run properly, both routes agree to five decimals per chain pair — A–C gives
0.823561 against 0.823574, the residual being the 2-dp rounding the PAE writer applies.

The 0.8560 was the **8-seed mean** from `results/m3_winner.md`. Seed 1 alone is 0.8491,
exactly what the JSON reproduces. **I compared an aggregate to a single observation and
called the gap a bug.**

That is the fourth overstatement in one day, and the fourth pointing toward a more
interesting finding. The direction is now the most predictable feature of my own reporting
on this project, and it is the reason the independent audits earned their cost.

> **A number quoted from a results table is an aggregate until proven otherwise. Read its n
> before you explain its mechanism.**

---

## 5. The artifact

`submission/LOCKSMITH_DEV/` in the handbook's §4.1 tree, plus `LOCKSMITH_DEV.zip`.

The packager asserts rather than assumes: the FASTA is checked on the **bytes written** —
six lines, three records, headers exactly `>Heavy_Chain`, `>Light_Chain`, `>Antigen` in that
order — and the PDB's chains are checked residue-by-residue against the FASTA, not merely by
length, with the first-ten-residue check the instruction asked for subsumed by a full
comparison. Prefixes across `structures/` and `sequences/` must agree or packaging raises.

The **validator** (`scripts/58_validate_submission.py`) takes only the packaged folder. It
imports nothing from `runs/`, consults no cached score, and re-derives all eight metrics
from the three files. Its one external input is the DockQ reference — PDB 5GGS, public and
named in §3.1 — passed as a CLI argument so it cannot silently fall back to ours. It exits
non-zero on any missing file, any format violation, any hard-cutoff failure. It passes:

```
VIABLE: True    FINAL: 96.0
```

`docs/methods_and_limitations.md` leads with the caveats rather than burying them: the
epitope-knockout split (ipSAE and interface pLDDT respond; PRODIGY ΔG and contacts do not,
and ΔG carries the largest share of our ranking), the SKEMPI null against measured ΔΔG, the
TIM-3 cross-reactivity signal, and the plain statement that **ranking within the viable pool
is not supported by our own metrics**. That disclosure is the strongest content in the
package and is written as such.

---

## 6. Challenge 2 — scoped and declined

`results/challenge2_scope.md`. Route A (RFdiffusion/RFantibody) is 1–3 days of install at
high risk on Blackwell; Route B (germline framework + MPNN CDR design) is ~1.5 days with no
new installs, but is not "blank canvas" and would have to be labelled germline-framework.

Recommendation: **build the germline novelty metric (~half a day, it does not exist), run
neither campaign.** Challenge 2 removes DockQ, the only metric that can detect a wrong pose;
the predictor's measured median DockQ on post-cutoff complexes is 0.291; and SKEMPI showed
no metric in the stack tracks measured affinity, with ΔG failing the epitope-knockout
control outright. A Challenge 2 score would be 100 points attached to no evidence. The
honest artifact is the characterised absence.

---

## 7. What is crude, stubbed or unproven

- **`band_value: top` is a choice, not a finding.** Every previously reported `final` in
  this repo was computed under midpoint + `min` DockQ and is superseded; the ranking is
  unaffected by `band_value` but *can* be affected by the DockQ aggregation, since designs
  may cross the 0.80 edge differently.
- **The pitch deck is five slides of content, not a designed deck.** It carries the right
  argument and would need real work to present.
- **The germline novelty metric still does not exist**, so Challenge 2 could not be scored
  even if a design appeared.
- **One design, one seed, in the package.** The shipped PDB is seed 71 of three; the other
  two are in `runs/handbook_construct/` and agree within 0.004 DockQ.
- **The validator's DockQ reference is our prepared 5GGS**, chain-relabelled to A/B/C. An
  evaluator using the raw PDB entry would need the same mapping, which `--mapping ABC:ABC`
  pins.

---

## 8. Glossary

**Band** — the Good/Medium/Poor bucket a raw metric falls into (§5.2).
**`band_value`** — this project's name for the undefined choice of where inside a band the
0–10 sub-score sits.
**Global DockQ** — DockQ v2's `Total DockQ` summary over all interfaces in the complex.
**Fv** — the variable fragment, VH + VL, without the constant domains.
**SEQRES** — the full polymer sequence deposited with a PDB entry, including residues not
resolved in the coordinates.
**Terminal truncation vs internal deletion** — a coordinate sequence missing residues at the
ends is harmless to fold; one missing residues in the middle silently fuses the flanks and
predicts a protein that does not exist.
**Viability** — clearing every §7.2 minimum; a non-viable design ranks below all viable ones
and its final score is not comparable.
