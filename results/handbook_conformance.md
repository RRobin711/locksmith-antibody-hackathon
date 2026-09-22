# Handbook conformance audit

Read directly from `source/antibody-design-hackathon-handbook.pdf` (text extraction
cross-checked against the rendered pages). Every prior encoding of this rubric was
written from a second-hand summary, so `config/metrics.yaml` is treated here as a
*hypothesis about* the handbook rather than as the handbook.

## 1. Bands and cutoffs (§5.2, §7.2)

| metric | handbook Good / Medium / Poor / Min | config | verdict |
|---|---|---|---|
| `ipsae` | >= 0.80 / 0.60 - 0.80 / < 0.60 / >= 0.60 | good 0.8, medium 0.6, cutoff 0.6 | **MATCH** |
| `dockq` | >= 0.80 / 0.49 - 0.80 / < 0.49 / >= 0.23 | good 0.8, medium 0.49, cutoff 0.23 | **MATCH** |
| `dg` | <= -12 / -10 to -12 / > -10 / <= -6 | good -12, medium -10, cutoff -6 | **MATCH** |
| `contacts` | > 25 / 15 - 25 / < 15 / >= 10 | good 25, medium 15, cutoff 10 | **MATCH** |
| `iface_plddt` | > 80 / 70 - 80 / < 70 / >= 65 | good 80, medium 70, cutoff 65 | **MATCH** |
| `cdr_sasa` | > 600 / 300 - 600 / < 300 / > 250 | good 600, medium 300, cutoff 250 | **MATCH** |
| `netsolp` | >= 0.70 / 0.50 - 0.70 / < 0.50 / >= 0.50 | good 0.7, medium 0.5, cutoff 0.5 | **MATCH** |
| `cdrh3_identity` | < 70% / 70 - 90% / > 90% / < 95% | good 70, medium 90, cutoff 95 | **MATCH** |

All eight band triples and all eight minimums are transcribed correctly.

## 2. Boundary inclusivity (§5.2) — the band assigned at each exact edge

The handbook mixes inclusive and exclusive edges within one table, and four of its
bands **overlap at the edge** (DockQ 0.80 is in both `>= 0.80` and `0.49 - 0.80`;
likewise ipSAE 0.80, ΔG −12, NetSolP 0.70). Overlaps resolve to the better band,
which is what `band_of` does by testing Good first.

| metric | edge | handbook text | expected band | code gives | verdict |
|---|---|---|---|---|---|
| `ipsae` | 0.8 | `ipSAE >= 0.80 vs 0.60-0.80` | good | **good** | MATCH |
| `ipsae` | 0.6 | `Min Required >= 0.60` | medium | **medium** | MATCH |
| `dockq` | 0.8 | `DockQ >= 0.80 vs 0.49-0.80` | good | **good** | MATCH |
| `dockq` | 0.49 | `0.49 - 0.80` | medium | **medium** | MATCH |
| `dg` | -12 | `dG <= -12 vs -10 to -12` | good | **good** | MATCH |
| `dg` | -10 | `-10 to -12 vs > -10 poor` | medium | **medium** | MATCH |
| `contacts` | 25 | `Contacts > 25 vs 15-25` | medium | **medium** | MATCH |
| `contacts` | 15 | `15-25 vs < 15 poor` | medium | **medium** | MATCH |
| `iface_plddt` | 80 | `Interface pLDDT > 80 vs 70-80` | medium | **medium** | MATCH |
| `iface_plddt` | 70 | `70-80 vs < 70 poor` | medium | **medium** | MATCH |
| `cdr_sasa` | 600 | `CDR SASA > 600 vs 300-600` | medium | **medium** | MATCH |
| `cdr_sasa` | 300 | `300-600 vs < 300 poor` | medium | **medium** | MATCH |
| `netsolp` | 0.7 | `NetSolP >= 0.70 vs 0.50-0.70` | good | **good** | MATCH |
| `netsolp` | 0.5 | `0.50-0.70 vs < 0.50 poor` | medium | **medium** | MATCH |
| `cdrh3_identity` | 70 | `CDR-H3 Identity < 70% vs 70-90%` | medium | **medium** | MATCH |
| `cdrh3_identity` | 90 | `70-90% vs > 90% poor` | medium | **medium** | MATCH |

| metric | minimum | strict? | value exactly at it | verdict |
|---|---|---|---|---|
| `ipsae` | 0.6 | inclusive | passes | MATCH |
| `dockq` | 0.23 | inclusive | passes | MATCH |
| `dg` | -6 | inclusive | passes | MATCH |
| `contacts` | 10 | inclusive | passes | MATCH |
| `iface_plddt` | 65 | inclusive | passes | MATCH |
| `cdr_sasa` | 250 | **strict** | FAILS | MATCH |
| `netsolp` | 0.5 | inclusive | passes | MATCH |
| `cdrh3_identity` | 95 | **strict** | FAILS | MATCH |

**All boundaries conform.** Today's earlier session made four Good edges strict; this audit confirms it did not also flip the four the handbook writes as inclusive, nor the six inclusive minimums.

## 3. Band -> score mapping (§5.1, §5.2, §7.3) — AMBIGUOUS-IN-HANDBOOK

§5.2 gives ranges only: **"Good (9-10)", "Medium (6-8)", "Poor (0-5)"**. Nothing
states how to pick a value inside a band. Now `conventions.band_value`.

| construct | DockQ agg | DockQ | bottom (9/6/0) | midpoint (9.5/7/2.5) | **top (10/8/5)** |
|---|---|---|---|---|---|
| 5GGS coordinates (what the project folded) | `min` | 0.755 | 81.0 | 87.5 | **94.0** |
| 5GGS coordinates (what the project folded) | `mean` | 0.805 | 84.0 | 90.0 | **96.0** |
| 5GGS coordinates (what the project folded) | `max` | 0.855 | 84.0 | 90.0 | **96.0** |
| 5GGS coordinates (what the project folded) | `global` | 0.850 | 84.0 | 90.0 | **96.0** |
| handbook SEQRES constructs (what §4.2.2 prints) | `min` | 0.723 | 81.0 | 87.5 | **94.0** |
| handbook SEQRES constructs (what §4.2.2 prints) | `mean` | 0.758 | 81.0 | 87.5 | **94.0** |
| handbook SEQRES constructs (what §4.2.2 prints) | `max` | 0.794 | 81.0 | 87.5 | **94.0** |
| handbook SEQRES constructs (what §4.2.2 prints) | `global` | 0.816 | 84.0 | 90.0 | **96.0** |

**Why `top` is the default, and why that is not a strong argument.** §7.3 states the
Challenge score range as "0 - 100"; midpoint caps the attainable maximum at 95 and
bottom at 90, so only `top` reaches the stated range. Against that: "0 - 100" is a
*scale label*, not a claim that 100 is attainable; `top` is also the most flattering
reading, awarding 10/10 to a metric that merely clears the Good edge; and within-band
**interpolation** is a fourth reading the text permits equally, not implemented here
because it needs an upper anchor the handbook never gives. **The choice is a uniform
monotone relabelling, so it moves the headline number and can never reorder two
designs.** Reported under all three; nothing downstream should quote one alone.

## 4. ipSAE selection rule (§6.1.1) — MATCH

Handbook: *"reads rows with Type = max for antibody vs antigen chains, and takes the
best ipSAE among them"*. `metrics/ipsae.py:78` keeps only `Type == "max"` rows whose
chain pair intersects {A,B} and contains C, and takes `max()` over them — not the
minimum, not A–C alone. Verified against a real vendored-script output.

## 5. DockQ aggregation (§6.1.2) — AMBIGUOUS-IN-HANDBOOK, default changed

Handbook: *"compares your complex to the reference ... and returns a docking quality
score between 0 and 1"*. A three-chain complex has three interfaces and the handbook
names no rule. The previous hardcoded `min()` over the two binding interfaces appears
nowhere in the text. **Default is now `global`** — DockQ v2's own `Total DockQ`, i.e.
what an evaluator gets by running the tool and reading its summary line. `min`, `mean`
and `max` remain selectable; all four are tabulated in §3 above.

## 6. NetSolP (§6.2.1) — Fv confirmed in the scoring path; chain_agg AMBIGUOUS

Handbook: *"run on the Fv sequence extracted from design_X.fasta"* and *"Per-chain
scores are combined into a single value per design"* — the combination rule is not
given. `netsolp.compute()` now trims to the V domain by ANARCII before scoring, and
the report path uses it (not only the ad-hoc script).

- **5GGS coordinates (what the project folded)**: VH 0.7036, VL 0.5686 -> `min` **0.5686** (Medium), `mean` **0.6361** (Medium)
- **handbook SEQRES constructs (what §4.2.2 prints)**: VH 0.6989, VL 0.5686 -> `min` **0.5686** (Medium), `mean` **0.6337** (Medium)

Both readings land in the same band for the finalist, so this ambiguity costs **0
points** here — but it is recorded because it would not be free for a design whose
VH and VL straddle 0.70.

## 7. CDR SASA (§6.1.6) — AMBIGUOUS-IN-HANDBOOK, costs 0 points

Handbook: SASA of *"the CDR loops (paratope) on the antibody"*. Plural loops and
"paratope" favour all six CDRs; heavy-only is not excluded. The code uses chains A+B
(all six).

- **5GGS coordinates (what the project folded)**: all six CDRs **1544.6 Å²** — Good band (>600) either way, since the heavy chain alone already exceeds 600.
- **handbook SEQRES constructs (what §4.2.2 prints)**: all six CDRs **1565.0 Å²** — Good band (>600) either way, since the heavy chain alone already exceeds 600.

## 8. Novelty (§6.3.1) — Challenge 1 MATCH, Challenge 2 NOT IMPLEMENTED

Handbook: *"Challenge 1: Compared to Keytruda's CDR-H3 / Challenge 2: Compared to
human germline CDR sequences"*. `metrics/novelty.py` hardcodes the pembrolizumab
CDR-H3 as its only reference and `data/germline/` is empty. Correct for Challenge 1,
**absent for Challenge 2**; scoped in `results/challenge2_scope.md`.

## 9. Category aggregation (§7.1 step 6) — MATCH

Handbook: *"Averages metric scores within each category"*, and §5.1 footnote:
*"DockQ is only computed for Challenge 1"*. `score.py:57` skips any metric whose
`challenges` list excludes the current challenge, and `score.py:77` averages only the
metrics actually present — so Challenge 2 binding averages **five**, and a missing
DockQ is never counted as a zero. Verified:

- Challenge 1: binding category averages **6** metrics
- Challenge 2: binding category averages **5** metrics

## 10. Viability (§7.2) — MATCH, with a reporting rule added

Handbook: *"Designs failing ANY minimum threshold are marked non-viable and ranked
below all viable designs"*. `score.py:74` sets `viable = not failing`, and `= None`
when any metric is missing rather than guessing. The gap was in *reporting*: a
non-viable design still gets a `final` number, and nothing stopped that number being
quoted beside a viable one. The packaged validator now refuses to emit a final score
for a non-viable design without the non-viable flag attached.

---

# B. Input conformance

## B1. The antigen construct (§4.2.2) — AMBIGUOUS, and the difference is terminal only

The handbook's example antigen is **123 aa**; this project folded 5GGS chain C at **113 aa**.
Character-by-character, ours is a **contiguous substring at offset 5**:

```
handbook  DSPDR PWNPPTFSPALLVV...ESLRAELR VTERR
ours            PWNPPTFSPALLVV...ESLRAELR
```

The shared 113-residue core is byte-identical. Verified against the RCSB entity API: the
handbook's antigen **is 5GGS's SEQRES, verbatim**. Ours is 5GGS's *coordinate* sequence —
five residues unresolved at each terminus. All three chains follow the same pattern:

| chain | ours | handbook | relation |
|---|---|---|---|
| heavy | 219 aa | 232 aa | ours == handbook[1:220]; adds `Q`- and `...DKTHHHHHH` |
| light | 217 aa | 218 aa | ours == handbook[0:217] |
| antigen | 113 aa | 123 aa | ours == handbook[5:118] |

**The instruction that prompted this check said the two were 'a different complex' and that
every binding metric was therefore computed on the wrong thing. That overstates it** — it is
the same complex with unresolved termini restored, which is precisely the case
`seq_for_folding()` permits (terminal truncation) as opposed to the internal deletion it
refuses. Re-folding was still the right call, because the shipped PDB and FASTA must
correspond; but the premise was wrong and the measured effect is small.

Finalist re-folded on the handbook constructs, 3 seeds, against the previous single-seed value:

| metric | 5GGS coords | handbook constructs (mean ± sd) | Δ | band change |
|---|---|---|---|---|
| ipSAE | 0.849 | 0.864 ± 0.037 | +0.015 | none |
| DockQ | 0.850 | 0.816 ± 0.004 | -0.034 | none |
| ΔG | -12.300 | -12.833 ± 0.321 | -0.533 | none |
| contacts | 100.000 | 97.667 ± 3.215 | -2.333 | none |
| interface pLDDT | 90.380 | 87.390 ± 2.065 | -2.990 | none |
| CDR SASA | 1544.600 | 1556.300 ± 35.167 | +11.700 | none |
| NetSolP | 0.569 | 0.569 ± 0.000 | +0.000 | none |
| CDR-H3 identity | 38.500 | 38.500 ± 0.000 | +0.000 | none |

**No metric crosses a band edge.** The prediction recorded in `scripts/55`'s docstring
before the folds ran — that the added termini are far from the epitope and the metrics would
barely move — held. The shipped package uses the handbook constructs regardless, so the PDB
and FASTA correspond exactly.

## B2. The antibody constructs (§4.2.2) — now MATCH

The handbook's example heavy chain is the full Fab heavy including CH1 and a C-terminal
**His-tag** (`...VEPKSCDKTHHHHHH`); the light chain is full-length with CL. We now fold and
ship exactly those, with our designed CDRs transplanted into the 29 IMGT heavy positions
(15 of which actually differ from wild type; ProteinMPNN recovered the native residue at the
other 14).

**The His-tag is included**, because the handbook prints it in the construct it expects and
because §6.2.1 says NetSolP runs on the Fv *extracted from* the FASTA — so a full-length
chain is what the pipeline anticipates, and the tag never reaches the solubility calculation.
It does enter the folded structure, where it sits disordered at the CH1 terminus, far from
the interface.

## B3. Predictor provenance (§8.1) — deviation declared; the reported discrepancy WITHDRAWN

§8.1 lists AlphaFold-Multimer as *"required for PAE"*. We used **Boltz-2** and convert its
`.npz` to AlphaFold-style JSON. The deviation is declared in the submission's `docs/`, with
the reason: AF2 cannot fold these complexes without an MSA (measured: pLDDT 37, ipTM 0.11,
interpenetrating chains), and a public MSA server would disclose an unpublished design.

**Earlier today I reported ipSAE 0.8491 from our JSON against 0.8560 from the npz and called
it a code-path difference. That is withdrawn.** Both routes agree to five decimals:

| chain pair | npz route | our JSON route |
|---|---|---|
| A–B | 0.898372 | 0.898371 |
| A–C | 0.823561 | 0.823574 |
| B–C | 0.804935 | 0.804978 |

The 1e-5 residual is the 2-dp rounding the PAE writer applies. The 0.8560 was the **8-seed
mean** from `results/m3_winner.md`; seed 1 alone is 0.8491, exactly what the JSON gives. I
compared an aggregate to a single observation. **The converter round-trips exactly**, and the
number an evaluator computes from our package is the number our own pipeline computes.

