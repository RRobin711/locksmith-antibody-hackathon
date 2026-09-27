---
tags:
  - session
  - locksmith-antibody-hackathon
---

Tags: [the retraction register](../../results/retractions.md), [the session index](README.md)

# Session 2026-09-26 (second) — Publishing a repository, and the five things a clean check cannot see

## 0. Session at a glance

The project went from a private vault folder to a GitHub repository, was reviewed
adversarially by five agents, and had roughly forty defects fixed — including a shipped
document that described the wrong molecule and a data leak that survived a history rewrite,
a force-push, and a verification I had declared clean.

**Prerequisites.** Git's object model (commits, trees, blobs, reachability), enough
`uv`/`pyproject` to know what a lockfile does, and the project's scoring vocabulary. Terms
used here are defined in §9; earlier concepts are restated briefly and linked rather than
re-taught — see the [first 2026-09-26 doc](2026-09-26-enumerating-the-retractions-and-what-grep-hid.md)
for the retraction register and the newline-tolerant-search lesson this session builds on.

**State at the end:** 17 commits, 34/34 tests, package validating at 94.0 / 93.6, **no
remote** — the GitHub repository was created, found to be leaking, and deleted. Nothing is
public.

---

## 1. The problem this session addressed

Two problems, and the second was discovered by solving the first.

**Publishing.** A vault folder is not a repository. It carried a placeholder team name in
every path, three organisers' email addresses, the organisers' copyrighted handbook, no
licence, 708 Obsidian wikilinks that GitHub renders as literal text, and a README whose
layout table said `scripts/` was "Empty" when it held 102 Python files.

**Verification.** Every check I ran to confirm the cleanup was *methodologically incapable*
of seeing what it was asked about. That happened three times in one session, on three
different tools, and it is the reason this doc exists.

---

## 2. Concepts, from first principles

### 2.1 Removing a file from a repository ≠ removing it from its history

Git stores every version of every file as an immutable **blob**, addressed by the SHA-1 of
its contents. A **commit** points to a **tree**, which maps paths to blobs. `git rm --cached
foo` writes a *new* commit whose tree omits `foo`. The blob is untouched and remains
reachable from every earlier commit.

So `HEAD` no longer contains the file and the repository still does. Every tool that reads
*files* — `git grep`, `find`, `cat`, any script that opens paths — inspects the working tree
or a single commit, and reports the first condition as though it were the second.

To ask the real question you must traverse history:

```bash
git log --all --diff-filter=A --name-only -- '<path>'   # was it ever added?
git log -p --all | grep -c '<secret>'                   # is it in any diff?
```

**Transferable principle:** *a question about a repository is not a question about a
directory, and no error tells you which one you asked.*

### 2.2 Reachability, and why a fresh clone proves nothing

`git clone` performs a **reachability walk**: it starts from the remote's refs (branches,
tags) and transitively fetches only objects those refs can reach. Objects no ref points to
are **unreachable** and are never sent.

A history rewrite plus a force-push makes the old commits unreachable *from the branch*. It
does not delete them from the server. GitHub retains unreachable objects indefinitely and
will serve any of them **by SHA** through the API and the web UI.

Therefore: cloning the remote and finding nothing is exactly what you would see whether the
objects were deleted or merely orphaned. The clone cannot distinguish the two cases. This is
not a subtle failure — it is a *structural* one, and I did not see it until an agent pointed
at it.

The only probe that answers the question interrogates the remote for a **known old SHA**:

```bash
gh api repos/<owner>/<repo>/commits/<old-sha>      # 200 => still retained
gh api repos/<owner>/<repo>/commits/<never-pushed> # 422 => control
```

The negative control is essential: without it, a 200 might be an API quirk. Old SHAs are
handed to you by `git filter-repo` in `.git/filter-repo/commit-map`, which makes that the
highest-value directory in a repo about to go public.

### 2.3 A rate is a property of every parameter it was computed under

Three times now this project has quoted a rate as if it were a property of a molecule:

| axis | claim | true at | false at |
|---|---|---|---|
| **threshold** (§C1) | 0% FP / 25% FN | neither — mixes DockQ ≥0.23 and ≥0.49 | — |
| **estimator** (§C8) | "clears all five gates" | `model_0` = argmax of 5 draws (0.609) | median of 5 (0.219) |
| **construct** (§C9) | "clears all five gates" | truncated 113-mer | repaired 119-mer (0.409, fails) |

Each time the axis was fixed and the job assumed finished. The general statement:

> A rate is meaningless without the full parameter set it was computed under, and *which*
> parameter is a different question each time. Fixing one axis is not evidence you have
> found them all.

### 2.4 Diff by blob hash, not by path

Comparing old and new *file lists* finds additions and deletions. It cannot find an
**in-place redaction**, because the path exists on both sides. Comparing `path → blob SHA`
maps finds both. That distinction is what made this session's leak inventory complete rather
than partial: the handbook was a path deletion, but the three email addresses were in-place
edits to `README.md`, which a path diff reports as unchanged.

---

## 3. What was built

### 3.1 The leak, and why three checks missed it

Timeline, all 2026-09-26:

| time | event |
|---|---|
| 15:46 | repo created on GitHub, **private** |
| ~15:50 | pushed — history still contained the handbook and the emails |
| 16:10 | `git filter-repo` scrubbed both; force-pushed |
| 16:15 | I verified with a **fresh clone**: five checks, all zero. Reported clean. |
| ~19:00 | an agent probed the **remote by old SHA**: HTTP 200 |

What was retrievable from the remote at 19:00, on a repo I had declared clean:

```
gh api ".../contents/README.md?ref=8930022..."  -> 3 organiser email addresses
gh api ".../git/trees/8930022...?recursive=1"   -> handbook.pdf, 727,284 bytes
```

Negative control (`04cbac2e…`, never pushed) returned 422, so the 200s were real retention.

**Three checks, three different blind spots:**

1. `git grep` over tracked files — reads the *working tree* (§2.1).
2. `git log --all`, `git rev-list --all`, `git cat-file --batch-all-objects` — read the
   *local* object database, which after `filter-repo` genuinely was clean.
3. A fresh clone — performs a *reachability walk* (§2.2).

Each answered truthfully. None answered the question. And `filter-repo` **deletes the
`origin` remote**, which resets the remote-tracking reflog, erasing the local evidence that
a pre-rewrite push ever happened.

**Remediation.** Force-pushing does not help. The repository was one day old with 0 forks,
0 stars, 0 issues and 0 releases, so deletion was strictly better than requesting a GitHub
Support garbage-collection: it is immediate and independently verifiable. The user deleted
it; the old tip and the emails-bearing commit both now return **404** where they returned
200 and a base64 payload an hour earlier.

### 3.2 The shipped package described the wrong molecule

`submission/…/Challenge1/docs/methods_and_limitations.md` shipped an entire §9.2
developability section stating:

> "This design carries `NG` at heavy chain position 55 … our redesign changed CDR-H2 at
> exactly one position (S54L) and **left `N55-G56` intact**."

The shipped chain reads `LQGG` at heavy 54–57. **Position 55 is Q** — the `N55Q` fix is the
whole point of the submitted variant, and line 133 of the same file says so. The section
described the pre-fix molecule.

The novelty table beside it was wrong in four ways. Verified by positional diff of the
shipped heavy chain against the handbook's 232-aa wild type (`scripts/55::HB_HEAVY`):

| quantity | shipped doc said | true |
|---|---|---|
| substitutions | 15 | **16** |
| whole-chain identity | 93.5% | **93.1%** |
| designable positions changed | 15 of 29 | **16 of 29** |
| CDR-H2 | `INPSNGGT -> INPLNGGT` (1 change) | `INPSNGGT -> INPLQGGT` (**2**) |

`INPLNGGT` appears **nowhere in the package** — it is the pre-fix loop with the N55Q edit
never applied to the prose. Three other things in the same package already said 16,
including the `--allowed_mismatches 16` minimum, which *is* the substitution count.

**The fix is computation, not correction.** `src/locksmith/submit/docs.py` now exposes:

```python
challenge1_novelty_table(heavy) -> str     # substitutions, identity, per-CDR changes
deamidation_motifs(heavy) -> [(motif, pos)]  # NG/DG inside any CDR window
```

CDR windows, 1-based inclusive on that construct: **H1 26–33, H2 51–58, H3 97–109** — chosen
because they reproduce the loop strings the submission has always quoted. The motif scanner
settles §9.2 mechanically: shipped heavy → `NONE`; wild type → `[('NG', 55)]`.

**Invariant, and what breaks without it.** `challenge1_novelty_table` raises if
`len(heavy) != len(wt)`, because a positional diff between differently-lengthed chains is
meaningless. That guard fired immediately (§5.2).

### 3.3 The headline finding was weaker than stated

"An anti-lysozyme antibody clears all five of the rubric's hard gates" was the project's
most-quoted result. It is true only on the **113-residue** antigen construct — the one whose
own positive control **failed** (nivolumab ipSAE 0.017, because the construct was missing 6
of its 14 epitope residues), for which the panel was pre-registered **INCONCLUSIVE** with the
explicit words "must not be read as evidence that the gate discriminates."

On the repaired **119-mer** (113-mer extended N-terminally by `LDSPDR`, PD-1 25–143):

| | median ipSAE | best of 5 | gates cleared |
|---|---|---|---|
| pembrolizumab (positive) | 0.843 | 0.889 | 5/5 |
| nivolumab (positive) | 0.691 | 0.840 | 5/5 |
| HyHEL-10 (negative) | 0.228 | **0.409** | **4/5 — fails ipSAE** |

2/2 positives clear, 6/6 negatives fail, separated by **0.184 ipSAE**. The flattering result
and the broken positive control had the **same cause**: a truncated antigen.

**What survives is still strong and is now the headline:** four of the five gates reject
**0 of 6** on *both* constructs. ΔG, contacts, interface pLDDT and CDR SASA are satisfied by
any two proteins the predictor places in contact, so §7.2 rests on ipSAE alone.

### 3.4 Reproducibility: the README promised what the code could not do

| defect | evidence | fix |
|---|---|---|
| `pytest` unreachable | declared under `[project.optional-dependencies]`; `uv sync` installs **groups** by default and **extras** only on request | moved to `[dependency-groups]` |
| stale lockfile | `uv lock --check` failed; `uv sync --locked` errored, so a clone resolved a *different* stack | relocked; `--check` now passes |
| `gemmi` undeclared | imported directly by 7 tracked files incl. `io/pdb.py`, on the validator's own path; arrived only as an `anarcii` transitive | declared `gemmi>=0.6` |
| no prerequisites | `prodigy-prot` needs `numpy>=2`, `DockQ`/`boltz` need `numpy<2` — they **cannot** share an env | documented as `uv tool install` + a pinned ipSAE clone |
| false claim | README said the DockQ reference is "passed as an argument so it cannot silently fall back on ours"; `scripts/58:271` has `default=Path("data/refs/prepared/5ggs_ABZ.pdb")` | replaced with the truth |

### 3.5 The validator broke the packager

`ipsae.py` derives its output paths from its **input** path, writing
`<pdb-stem>_<pae>_<dist>.txt`, `_byres.txt` and a `.pml` beside whatever it is pointed at.
Pointed at the packaged submission — which `scripts/58` does — it dropped three files into
`structures/`, and `submit/package.py` then refused to rebuild, because §4.2.1 specifies
exactly `design_X_complex.pdb` and `design_X_pae.json`. **Running the validator broke the
packager.**

`metrics/ipsae.py` now stages into a `TemporaryDirectory`. **Basenames are preserved
exactly**, because ipsae.py locates the pLDDT array by string-substituting `pae`→`plddt` in
the PAE path; rename or relocate either file and it writes an empty table and exits 0.

Verified: `VALIDATION PASSED`, 94.0 / 93.6, ipSAE unchanged at 0.820 / 0.904, **zero strays**.

### 3.6 Everything else, briefly

Renamed `LOCKSMITH_DEV` → `RYAN_BINNY` (rebuilt from generators, not renamed on disk); MIT
licence; handbook untracked; **558 wikilinks** converted to markdown (0 of 582 targets
broken); README rewritten as a landing page with a **Stack** table (a recruiter grepping
`rfdiffusion|rfantibody` previously got **zero** hits in both entry documents); 77 commits
re-authored to a noreply identity so the work email never reaches a public repo; case-
duplicate PDBs removed (three byte-identical pairs differing only in case would make every
macOS/Windows clone permanently dirty); `config/metrics.yaml`'s withdrawn triple and its
refuted "never [changes] the ranking" claim; banners on three superseded results files; a
private company-context note unpublished (tagged `job-search`, names a private channel,
identifies a co-founder) with all five inbound links delinked.

---

## 4. Design decisions

| decision | chosen | alternatives | why | cost to reverse |
|---|---|---|---|---|
| Leak remediation | delete + recreate | force-push; GitHub Support GC | only action that reliably destroys orphans, and independently verifiable. Repo was 1 day old, 0 forks | high — the repo must be recreated |
| Novelty table | **compute** from the shipped sequence | re-hardcode correct values | hardcoding is what drifted; a computed table cannot describe a different molecule | low |
| Commit identity | GitHub noreply address | real email; leave the work email | attributes correctly, publishes no address, keeps work identity out | high after publishing |
| Wikilinks | convert to markdown | leave; convert all | markdown renders in **both** Obsidian and GitHub, so it is strictly better; tag-hub links can't resolve either way | low |
| Company-context note | untrack + gitignore, keep on disk | redact further; publish; delete | redaction already failed once; it is a private assessment of named people | trivial |
| Batch-padding cause | **withdraw, offer nothing** | keep it; invent a new mechanism | the folds ran 94 s apart, so no batch formed. A corruption with no explanation beats a refuted one | low |
| `$2.77` vs `$2.82` | **FLAG**, don't pick | reconcile to either | neither is derivable — no rate is recorded anywhere | n/a |
| Historical docs | never retro-edit; banner + register | sweep and rewrite | rewriting destroys the evidence that understanding changed | high |

---

## 5. What went wrong

### 5.1 I declared a leak fixed using a check that could not see it

Covered mechanically in §3.1. The behavioural failure is the part worth keeping: I ran a
fresh clone, got five zeros, and wrote *"verified from a fresh clone"* as though it settled
the question. It was the **third** instance of the same defect in one day — after `grep`
under-reporting in wrapped prose, and `git grep` reading the working tree.

**The general lesson:** when a check returns the answer you hoped for, the next question is
*what would this check do if the answer were no?* A clone would look identical either way.
A check that cannot fail is not evidence — which is a rule this project already had, about
controls, and which I did not apply to my own verification.

### 5.2 I typed a protein sequence from memory

Writing `HANDBOOK_WT_HEAVY` into `docs.py`, I transcribed the 232-residue wild-type chain
instead of reading it from `scripts/55`. I produced 218 residues.

Caught immediately by the length guard I had just written (§3.2), which refused to emit a
table rather than emitting a wrong one. Fixed by extracting the literal programmatically.

**Lesson:** the session's whole subject was copied-versus-computed values, and I introduced a
copied value while building the machine that computes them. Guards earn their cost on the
author, not just on the successor.

### 5.3 A syntax error, and why it was the good failure

Adding the ipSAE-precision disclosure, I left a stray `)`, giving
`SyntaxError: closing parenthesis ')' does not match opening parenthesis '['`. The rebuild
aborted, the package kept its last good content, and nothing shipped. Contrast with §3.2 and
§3.5, where the failure was silent and shipped. *A build that dies is cheaper than a build
that lies.*

### 5.4 I mis-dated six stamps

I wrote `2026-09-26` corrections stamped **2026-09-27** across five files. Caught during
this wrap-up by grepping for tomorrow's date. Trivial, and exactly the class of small false
fact that the register exists to catch — so it is recorded rather than quietly fixed.

### 5.5 Keystroke-simulated input dropped three characters

Typing a 196-character repo description into a browser form field stored **193** —
`stress-test`→`stres-test`, `ProteinMPNN`→`ProtenMPNN`. Noticed only because the corruption
appeared in the browser tab title. Rewritten via the API and verified byte-identical
(226/226 on the second attempt). This **corrected** an existing `LEARNINGS.md` entry that
implied inputs under ~1 KB are safe: they are not.

### 5.6 A bulk rewrite destroyed the example of the bug it was fixing

The wikilink converter rewrote a fenced code block in an earlier session doc that
*demonstrates* a split wikilink, turning the illustration into a working link. Caught by
grepping **inside fences** for the pattern just introduced — exactly one hit. Restored, fence
tagged `text`.

**Lesson:** *a source-rewriting tool must skip fenced blocks; a documentation repo's fences
hold deliberately-wrong examples.*

---

## 6. Degenerate and failure cases

- **`filter-repo` rewrites every ref, including your backup branch.** `-- --branches` caught
  `backup-pre-author-rewrite` too. Originals survive under `refs/original/`, which is why
  that namespace must be checked and deleted rather than assumed absent.
- **`refs/original/*` still held all 34 work-email commits** after the authorship rewrite.
  Such a repo must never be pushed with `--mirror` or `--all`.
- **Deleting a remote is only cheap while the repo is young.** 0 forks, 0 stars, 0 issues.
  With a single fork, the orphans live in the fork and deletion does not reach them.
- **`.gitignore` patterns do not recurse the way people assume.** `data/refs/*.pdb` does not
  match `data/refs/prepared/5ggs_ABZ.pdb`, which is the *only* reason the DockQ reference
  ships. That was luck; it is now pinned with an explicit negation and a comment.
- **A guard that cannot fail.** `scripts/00_doctor.py` marks every external tool
  `required=False`, so a machine missing all four prints "All required checks passed."
  Known, not yet fixed.

---

## 7. Verification

| check | command | result |
|---|---|---|
| tests | `uv run pytest tests/` | **34 passed**, ~2.3 s |
| package | `scripts/58_validate_submission.py submission/RYAN_BINNY` | **VALIDATION PASSED**, 94.0 / 93.6 |
| lockfile | `uv lock --check` | passes (was failing) |
| dangling links | resolve every `](*.md)` against the filesystem | **0** of 583 |
| case collisions | `git ls-files \| tr A-Z a-z \| sort \| uniq -d` | **0** |
| third-party email | newline-tolerant regex over all tracked text | **0** |
| leak | `gh api …/commits/<old-sha>` | **404** (was 200) |
| package strays | `find submission -type f ! -name '*.pdb' …` | **0** |

**Healthy looks like:** the validator re-deriving both composites from the package alone,
and the old-SHA probe 404-ing *with* a never-pushed control also 404-ing after deletion.

**Plausible-but-wrong looks like:** a fresh clone reporting zero hits — which it will
whether or not the remote retains the objects. That is the trap this session fell into.

---

## 8. Honest assessment

**Solid.** The leak is closed and verified against the remote. The shipped package no longer
contradicts its own molecule, and the two worst numbers are computed rather than copied. The
headline finding is weaker and now survives a re-run, which is the trade this project exists
to make.

**Weak, and named.** `scripts/00_doctor.py` cannot fail. There is **no CI**, which is the
sharpest structural criticism available of a repo arguing "mechanise the lesson" — a 10-line
Action would have caught the undeclared `pytest` and the stale lock on the commits that
introduced them. Roughly 18 `96.0` derivations remain in the lecture body, indexed under C3
rather than rewritten. `docs/sessions/README.md` is 5,065 words under a line promising "one
line per working session".

**Not claimed.** No design changed, no metric was recomputed from a structure, and no new
measurement was taken. Scores are what they were: 94.0 and 93.6.

**Untested.** The `uv sync` → prerequisites → validator path was never run end to end on a
genuinely clean machine; it was reasoned about from `git ls-files` and `--dry-run`.

---

## 9. Glossary

- **Blob / tree / commit** — git's three object types: file contents, a directory listing,
  and a snapshot pointing at a tree.
- **Reachability** — whether an object can be walked to from a ref. Clones fetch only
  reachable objects; unreachable ones persist server-side.
- **Orphaned commit** — unreachable from any ref, still retained and servable by SHA.
- **`git filter-repo`** — history-rewriting tool; `--invert-paths` drops paths,
  `--replace-text` substitutes blob contents. Writes `.git/filter-repo/commit-map`.
- **`model_0`** — a predictor's first returned model. Under `diffusion_samples=1` it is an
  **argmax by construction**, not a sample.
- **Construct** — the exact residue range of the antigen folded. The 113-mer and 119-mer
  here differ by six N-terminal residues and disagree about whether the gate works.
- **Deamidation motif** — `N-G` or `D-G`; chemically labile, and §9.2 forbids it in CDRs.
- **Dependency group vs extra** — `uv sync` installs `[dependency-groups]` by default and
  `[project.optional-dependencies]` only when asked. Putting `pytest` in the latter makes
  `uv run pytest` fail on a clean clone.
- **FLAGGED** — the register's status for a figure known not to reproduce and deliberately
  not replaced by a guess.
