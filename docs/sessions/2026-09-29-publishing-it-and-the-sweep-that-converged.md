---
tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [the project's guiding idea — build the evaluator before the thing evaluated](../../knowledge/Build%20the%20Judge%20Before%20the%20Contestant.md), [the session index](README.md)

# Session 2026-09-29 — Publishing it, and the sweep that converged

## 0. Session at a glance

**Before:** the project was finished scientifically and existed only on one laptop. A
correction (register §C9) had been written on 2026-09-26 and never propagated out of the
register. There was no remote, no public artefact, and no images.

**Now:** public at `RRobin711/locksmith-antibody-hackathon`, 107 commits, CI green,
history audited and rewritten once before the first push. §C9 propagated to 14 live sites
across 10 files. The repo's first figure exists and regenerates from committed data. The
front page carries the project's own sharpest criticism of itself.

**Unfinished:** one empty stray repository that needs a token scope only the user can
grant; and the unconditioned-arm sequencing, which needs a rented GPU.

This doc continues from
[the previous session's doc](2026-09-28-clearing-the-backlog-and-three-guards-that-could-not-see.md),
which covers the backlog items and the decoy-patch control. Everything from the §C9
propagation onward is here. Concepts are defined from first principles; where an earlier
doc covers one more fully it is restated briefly and linked.

**Prerequisites:** basic git (commits, history, remotes); what a regular expression is.
No biology is required to follow §2–§6.

---

## 1. The problem this session addressed

Three problems, and they are different in kind.

**(a) A correction that reached its register and nothing else.** On 2026-09-26 the project
withdrew its most-quoted finding — *"an anti-lysozyme antibody clears all five of the
rubric's hard gates"* — because the result holds only on a **truncated 113-residue** form
of the antigen. On the repaired 119-residue form the same antibody clears nothing. The
withdrawal was recorded in `results/retractions.md` §C9. It was not propagated. A
retraction that lives only in the retraction register is a retraction nobody reads.

**(b) The repo had never been public, and the last attempt leaked.** In September a push
of this project exposed a copyrighted PDF and three third-party email addresses; a
`filter-repo` scrub plus force-push *appeared* to fix it and did not, because GitHub
retains unreachable objects and serves them by SHA. The repository was deleted. Publishing
again therefore required proving the history was clean against the remote, not against a
clone.

**(c) The project's own harshest criticism was buried.** The critique chapter says the
validation programme proved further validation could not help, and the project kept
validating anyway. That belonged on the front page, not in chapter nine.

---

## 2. Concepts introduced, from first principles

### 2.1 A *claim* is a predicate with a subject — and that is what you must search for

Searching prose for a withdrawn claim looks like a string-matching problem and is not. The
claim here is *"a wrong antibody clears all five gates"*. Three naive searches and why each
fails:

| search | fails because |
|---|---|
| `grep "all five"` | matches "all five **samples**" (diffusion draws) and "all five **external tools**" — different claims entirely |
| `grep` + *is the word* `construct` *nearby?* | **proximity is not qualification**; an unrelated sentence can contain the word |
| require the predicate only | a *correct* statement of the claim contains the predicate too |

What worked: require the **subject** (`hyhel|lysozyme|cetuximab|wrong antibody`) within a
window, *then* ask whether a qualifier (`113|119|C6|C9|truncat|repaired`) is present. A
claim is subject + predicate; searching for half of it returns the wrong set in both
directions.

**Transferable principle:** when sweeping a corpus for a retracted claim, encode *what the
claim asserts about what*, not the memorable phrase. The memorable phrase is why it spread;
it is not what makes it the claim.

### 2.2 Three ways a text search silently under-reports

Each was hit for real in this project. All three fail *quietly* — a search returning fewer
hits looks exactly like a cleaner corpus.

1. **Hard-wrapped prose.** `grep` is line-oriented; `with a 0%\nfalse-positive rate`
   contains the phrase but no single line does. Fix: build the pattern with `\s+` between
   words — `r"\s+".join(re.escape(w) for w in phrase.split())`.
2. **Inline markup.** `\s+` bridges whitespace and nothing else, so `**0%** false-positive`
   defeats it: the separator is `**` then a space. Fix: search the text a *reader* sees as
   well as the bytes — strip `*`, `` ` ``, `~` and search both forms. Deliberately **not**
   `_`, which in this codebase is an identifier (`scores_v2.json`) far more often than
   emphasis.
3. **Corpus scope.** `git grep` answers for the *working tree*. "Is it in the repository?"
   needs `git log --all --diff-filter=A`; "does the remote still hold it?" needs the remote
   asked by SHA. Three questions, three tools; the one people reach for answers the first.

**Transferable principle:** every search answers a narrower question than the one you
asked, and it answers it truthfully. Before believing a clean result, ask what the search
would have done had the answer been *no*.

### 2.3 Reachability, and why a fresh clone cannot audit a remote

`git clone` performs a **reachability walk**: it fetches only objects the refs can reach.
After a history rewrite the old commits are unreachable but **not deleted** — GitHub keeps
them and serves them by SHA. So a clone returns identical output whether the objects were
removed or merely orphaned. The only test is to ask the *remote* for a known old SHA:

```bash
gh api repos/<owner>/<repo>/commits/<old-sha>     # 200 = still retained
```

and that probe is worthless without **two** controls:

- a **negative control** — a never-pushed SHA, which must 404. Without it a 200 might just
  mean "the API returns 200 for anything".
- a **positive control** — a SHA known to be present, which must 200. Without it, a 404
  might mean "the probe is broken" rather than "nothing is there". *This session added the
  positive control; September had only the negative one.*

**Transferable principle:** a probe needs a control in **both** directions. One control
tells you the instrument can say "no"; the other tells you it can say "yes".

### 2.4 A converging series is not a proof of termination

Five sweeps were run for §C9. Sweeps 1→3 each found sites the previous had marked clean.
That the finds are decreasing (13 → 0 → 1 → 0 → 0) is evidence of convergence; it is not
evidence that zero remain. The honest claim is **"no known unqualified occurrences after
five sweeps, with the per-sweep counts shown"**, which lets a reader judge the trend, not
**"zero"**, which asserts termination that was never demonstrated.

**Transferable principle:** when a search process keeps finding what the last pass missed,
report the series rather than its last term.

---

## 3. What was built — mechanism

### 3.1 The §C9 sweep

```python
SUBJ  = re.compile(r"hyhel|lysozyme|cetuximab|wrong antibody|irrelevant antibod|negative control", re.I)
QUAL  = re.compile(r"113|119|C6|C9|C8|truncat|repaired", re.I)
CLAIM = {"all five": r"all\s+(?:five|5)\b", "5/5": r"\b5\s*/\s*5\b",
         "0.609": r"0\.609", "0.006": r"0\.006\b"}
```

Procedure per match: require `SUBJ` within **±260 characters** (a paragraph), then require
`QUAL` within **−350/+550** (asymmetric: a qualifier usually *follows* the claim it
qualifies). Both windows are in characters, measured on the **markup-stripped** text.

Corpus: every `.md` and `.py` in the repo plus the built `.pptx` (text extracted via
`python-pptx`), excluding `.venv`, `vendor`, `node_modules`, `.git`.

Three file classes are excluded from the "live" count **by name, with a reason**:
`docs/sessions/` (historical — they record what was believed then), `results/retractions.md`
and `docs/lecture/CORRECTIONS.md` (they quote the claim in order to correct it).

### 3.2 The calibration figure

`scripts/98_calibration_figure.py` reads `runs/calibration/scores.json`, a nested dict:

| top-level key | contents |
|---|---|
| `panel` | 40 real antibody–antigen crystals, each with `ipsae` and `dockq` |
| `negctrl` | 10 rows on the **113-mer** antigen |
| `negctrl_nloop` | 10 rows on the repaired **119-mer** — the one used here |

**Invariant that matters:** the six known-wrong antibodies are named explicitly
(`WRONG = ["hyhel-10", "cetuximab", "cr9114", "bevacizumab", "bo2c11", "trastuzumab"]`)
rather than selected by exclusion. `negctrl_nloop` also holds two positive controls and the
project's own two designs; "everything that isn't a positive" would silently absorb a
future arm. The script raises if a named key is absent.

**Why the negatives have no x coordinate.** DockQ scores a predicted pose against a
*deposited reference complex*. Each negative is docked onto PD-1, which is not its target,
so no such complex exists and DockQ is undefined — not missing, undefined. They are drawn
on a separate strip sharing the y-axis, x-axis removed and labelled "no DockQ (non-native
target)". Plotting them at any x would fabricate the quantity the panel exists to measure.

**Parameter values, all with their source:**

| value | what | source |
|---|---|---|
| `GATE = 0.60` | §7.2 ipSAE viability cutoff | the handbook |
| `ACCEPTABLE = 0.23`, `MEDIUM = 0.49` | DockQ quality thresholds | DockQ's own convention |
| `RHO = 0.702` | Spearman ipSAE↔DockQ, n=40 | `results/calibration.md:78` |
| ±0.32 | 95% CI on ρ | Fisher-z SE `1/√(n−3)` = 0.16 at n=40 |
| `MIN_GAP = 0.033` | minimum label separation, y-axis units | set from the observed 0.011 collision |
| `#2a78d6` / `#eb6834` | categorical slots 1 and 2 | dataviz palette, validator-checked |

**Label de-collision.** Strip labels are nudged apart greedily top-down; **the marks are
never moved**, only the text, with a leader line drawn when text and mark separate. A
nudged mark would be a falsified data point.

### 3.3 File map, in reading order

| file | owns |
|---|---|
| `scripts/98_calibration_figure.py` | the figure; reads committed scores, writes `figures/*.{png,svg}` |
| `docs/lecture/CORRECTIONS.md` **C6** | the course-side §C9 correction, its index, and the five-sweep table |
| `results/negative_control.md` | the panel; now carries an inline construct banner on its `model_0` table |
| `README.md` | front page; gained the figure and the thin-campaign limitation |
| `.github/workflows/ci.yml` | clean-clone install + tests; header corrected by its own first run |

---

## 4. Design decisions

| decision | chosen | alternatives | why | cost to reverse |
|---|---|---|---|---|
| Where a *passing* control is recorded | `results/decoy_patch_control.md` + `STATE.md` §4 "Verified" | a register entry under §B | the register has **no confirmations section** — A–D are all withdrawals and every B entry is WITHDRAWN/REFUTED | trivial; it is one file |
| Negatives on the figure | separate strip, no x axis | omit them; plot at x=0; plot at a jittered x | DockQ is *undefined*, not missing; any x invents the measured quantity | trivial, but would be wrong |
| Run artefacts in git | removed from **history** with `filter-repo` | `git rm --cached`; leave them | not yet pushed, so the rewrite was free; `rm --cached` leaves blobs in every commit that added them | expensive after a push — that is the September lesson |
| Figure generation | committed script reading committed data | hand-made image; notebook | a hand-made image is a number living in a PNG and nowhere else | trivial |
| Sweep claim wording | "no known unqualified after five sweeps" + counts | "zero live unqualified" | three sweeps each found what the last marked clean | trivial |
| Repo account | `RRobin711` | `RyanB-raekis` | owns the identity on all commits **and** has the `workflow` scope | a repo move |

---

## 5. What went wrong

**(a) `git add -A` committed 7.8 MB of generated artefacts.** The decoy job runs with
`cwd` = repo root, so Hydra wrote `outputs/` and RFdiffusion cached a noise-schedule
`.pkl` there while I was committing. *Dangerous because:* it would have shipped in the
first public push and bloated history permanently. *Caught by:* auditing tracked file sizes
before publishing — the `.pkl` was the largest tracked file. *Lesson:* **never `git add -A`
while a job is writing into the working tree**; add paths explicitly, or `.gitignore` the
job's output directory before starting it.

**(b) I killed my own shell.** `pgrep -f '97_decoy_cpu.sh'` matched the subshell running
that very command, exit 144. This project has `.claude/hooks/pkill-guard.sh` *because of
five previous instances*. *Lesson:* the bracketed form (`'[9]7_decoy_cpu'`) prevents
self-match; better still, gate on artefacts rather than process tables.

**(c) A decision bar that used a measured number and was still wrong.** The decoy rule used
`BAR = 0.500` for both faces, justified as "symmetric, and not arbitrary". It is symmetric
in *number* and asymmetric in *evidence*: the unconditioned baselines are **0.500 on the
epitope and 0.000 on the decoy**, so the decoy side demanded conditioning beat zero by half
an interface while the epitope side demanded only that it match a baseline it already sat
at. A genuine partial effect would have been scored as failure. *Caught by* measuring the
unconditioned arm against the decoy patch before the run. *Lesson:* **using data does not
make a threshold principled; using the right comparison does.**

**(d) A silent exclusion, in code written that day to prevent silent exclusion.** The decoy
analysis printed `n = 16` from 18 backbones. Two produced *no antigen contact at all*,
making the fraction 0/0 — a real observation, not a parse failure — and the loop
`continue`d past them. *Caught by* asking why n wasn't 18. *Lesson:* **a mean without its
denominator is a silent exclusion**; report `n` and name what was dropped.

**(e) A glob that would have reported 1 of 18 as a working analysis.** `--analyse` globbed
`*_0.pdb`, correct for the pod's `bb_7_0.pdb` naming, which matches exactly one of eighteen
`dec_N.pdb` files. *Lesson:* a filename convention is an interface; changing how outputs
are produced changes it.

**(f) Clearing a sweep hit with the argument I had just declared invalid.** Sweep 4 cleared
`negative_control.md`'s HyHEL-10 row because "the file names the 113-mer in its §Design
section" — file-level proximity, a weaker version of the ±400-character proximity I had
written up as invalid two screens above. *Caught by* the user reading both and noticing
they contradicted. *Lesson:* **a rule you just wrote applies to you first**, and the place
it is most likely to be broken is the next paragraph.

**(g) Two bad time estimates, the same way both times.** 19.5 min/backbone (from the
project's own record) measured **26**; "done by 20:20" became **21:20**. Both came from
quoting a figure for a configuration other than the one being run — the record's figure was
for a different thread count, and 20:20 ignored that 8-thread workers are slower per
backbone than 11-thread ones. *Lesson:* a measured number is measured **under conditions**;
re-measure when the conditions change.

---

## 6. Degenerate and failure cases

| case | status |
|---|---|
| backbone with **zero** antigen contacts (0/0 fraction) | **handled** — excluded, named, counted separately (2 of 18) |
| negatives with no DockQ | **handled by design** — own strip, no x axis |
| two strip labels within 0.011 y-units | **handled** — greedy de-collision at `MIN_GAP = 0.033`, marks unmoved |
| a sixth sweep finding a new site | **expected, not excluded** — C6 claims a series, not termination |
| `negctrl_nloop` missing a named antibody | **handled** — `SystemExit` with the key list, rather than a short plot |
| `gh` active account flipping mid-session | **handled** — remote pinned to `https://RRobin711@…` so the credential helper cannot pick the wrong account |
| CI runner out of disk | **not a risk** — first run reported `/dev/root 72G, 31G avail`; the reclaim step is cheap insurance, not load-bearing |

---

## 7. Verification

```bash
uv run pytest -q                                      # 42 passed
uv run python scripts/59_prepublish_audit.py --author-email-contains 'RRobin711' --banned-path '*.pdf'
uv run --extra analysis python scripts/98_calibration_figure.py   # 40 crystals, 6 negatives
git log --all --diff-filter=A --name-only | grep -c outputs       # 0
```

Observed, publicly and anonymously (no token):

| check | result |
|---|---|
| repo visibility | `PUBLIC`, `isPrivate=false` |
| CI | success, 2m42s–3m20s, `42 passed` |
| `README.md` | HTTP 200, 15,635 bytes |
| `figures/…png` | HTTP 200, 137,130 bytes, `image/png` |
| `results/retractions.md` | HTTP 200, 36,706 bytes |
| history: `outputs/`, `cached_schedules/`, the `.pkl` | **0 additions in any commit** |
| emails in all blobs | only `@users.noreply.github.com` |

**What a plausible-but-wrong result looks like here.** A sweep reporting **0** live
occurrences on its first run — that is what an over-narrow pattern produces, and it is
indistinguishable from a clean corpus. Likewise a SHA probe returning 404 for everything:
without the positive control that reads as "nothing retained" when it may mean "the probe
is broken". Both were observed this session and both were caught by a control.

---

## 8. Honest assessment

**Solid.** The history is clean and was verified against the remote with controls in both
directions. The figure regenerates from committed data. The sweep method is sound and its
limits are stated in the artefact itself.

**Weak or stubbed.** The sweep's subject list is **hand-written** — a claim phrased without
any of those six words would be missed, and that is precisely how sweeps 1 and 2 failed in
their own way. `MIN_GAP = 0.033` is a layout constant with no principle behind it beyond
"larger than the collision observed". The figure is light-mode only; this project has no
dark-mode requirement, but the dataviz standard would want one.

**Not supported by the evidence.** That the corpus is now clean of §C9 — only that five
sweeps found nothing further. And the figure shows pose accuracy against predictor
confidence; **nothing in it is a binding measurement**.

---

## 9. Next steps

1. **Delete the stray `RyanB-raekis/locksmith-antibody-hackathon`** — blocked on
   `gh auth refresh -h github.com -s delete_repo`, which only the user can run. Probed and
   confirmed empty (`isEmpty: true`, no retained objects), so this is tidiness, not exposure.
2. **Sequence the 18 unconditioned backbones** — needs ProteinMPNN on a rented sm_86 card
   (RFantibody pins `torch==2.3.*`, no PTX, so nothing reaches `sm_120`). Folding and
   scoring then run locally for free. Separates range restriction from a dead
   `interaction_pae`; does not bear on the conditioning result.
3. **`/migrate-learnings`** — `LEARNINGS.md` is at its 40-bullet cap with at least three
   promotable entries waiting. Deliberately not started at session end.

---

## 10. Glossary

| term | meaning |
|---|---|
| **blob** | a file's contents as git stores it, addressed by hash |
| **DockQ** | 0–1 score of a predicted complex against a deposited reference; **undefined** without one |
| **ipSAE** | Boltz-2's interface confidence, derived from its predicted aligned error |
| **orphaned object** | a git object no ref reaches; still stored, still served by SHA |
| **pre-receive hook** | server-side check that runs *after* the client uploads a pack and can still reject it |
| **reachability walk** | how `clone`/`fetch` decide what to transfer — follow refs, take only what they reach |
| **sweep** | one pass of a corpus search for a retracted claim |
| **113-mer / 119-mer** | the truncated and repaired PD-1 antigen constructs; the 113-mer is missing 6 of nivolumab's 14 epitope residues |
