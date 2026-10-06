# Session index

One line per working session. The teaching lives in the per-session docs; this file
only makes them findable.

*Rewritten 2026-09-28.* It previously held 5,448 words — a table whose "What it covers"
cells ran to 416 words each, restating the docs it links to rather than indexing them. It
failed the promise in its own first line and rendered as an unreadable wall on GitHub.
Checked before trimming: **93.4%** of the distinctive tokens in those cells (numbers,
identifiers) already appear in the doc each row links to, and every one of the 26 docs opens
with its own summary, so the long form was derivative. The remaining 6.4% were quoting
artefacts — a string containing a literal newline, spacing variants of a formula — not
unique content. The long version is in git history at the preceding commit.

| Date | Doc | One line |
|---|---|---|
| 2026-09-14 | [Reading the hackathon spec: what is actually being scored](2026-09-14-antibody-hackathon-spec-and-scoring.md) | The handbook extracted end to end — both challenge specs, the scoring formula, all eight cutoffs, and the contradictions inside it. |
| 2026-09-15 | [Standing up the environment, and two traps that produce plausible wrong answers](2026-09-15-environment-and-imgt-numbering-foundations.md) | Blackwell verified by arithmetic rather than `is_available()`; two silent-failure traps found on day one. |
| 2026-09-16 | [The first real prediction, and the four attempts it took](2026-09-16-first-prediction-and-the-four-attempt-fold.md) | Pembrolizumab–PD-1 recovered untemplated at DockQ 0.820 — after four fold failures, three of which exited 0. |
| 2026-09-16 | [Installing the last two M1 dependencies, and the control that changed the answer](2026-09-16-netsolp-colabfold-and-the-control-that-changed-the-answer.md) | A positive control, not the defaults, chose which NetSolP variant the project scores with. |
| 2026-09-17 | [The Fv screen fails, and ipSAE turns out to be a liveness test](2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test.md) | A confidence metric separates dead from live and barely ranks the live — until proven otherwise. |
| 2026-09-17 | [The memorisation test, and what it cost Challenge 2](2026-09-17-the-memorisation-test-and-what-it-cost-challenge-2.md) | Generalisation tested on post-cutoff structures; full-chain identity is a useless novelty screen for antibodies. |
| 2026-09-17 | [Validating the inputs, and withdrawing a result](2026-09-17-validating-the-inputs-and-withdrawing-a-result.md) | Sequences built from coordinates were spliced chimeras; a near-zero DockQ was our prep, not the model. |
| 2026-09-17 | [The sweep came back clean, and what to build next](2026-09-17-the-sweep-came-back-clean-and-what-to-build-next.md) | What a clean sweep does and does not license, written down before moving on. |
| 2026-09-18 | [M2: the design path, and a baseline that passes everything](2026-09-18-m2-the-design-path-and-a-baseline-that-passes-everything.md) | The design path built end to end, with the gates enforced structurally rather than by convention. |
| 2026-09-18 | [Re-seeding, and the CDR-H3 ensemble](2026-09-18-reseeding-and-the-cdr-h3-ensemble.md) | A residue's own confidence is blind to conformational heterogeneity; spread across seeds is not. |
| 2026-09-18 | [The ensemble axis loses to a free sequence feature](2026-09-18-the-ensemble-axis-loses-to-a-free-sequence-feature.md) | Before buying an expensive measurement, check a free feature does not already explain it — by partial correlation. |
| 2026-09-18 | [What a pre-fold filter has to beat](2026-09-18-what-a-pre-fold-filter-has-to-beat.md) | A selection rule must beat the same rule applied at random, at equal budget — not the unfiltered pool. |
| 2026-09-19 | [Three seeds is the worst allocation](2026-09-19-three-seeds-is-the-worst-allocation.md) | Depth versus breadth priced by simulating the whole procedure, including the final argmax. |
| 2026-09-20 | [Spread is not a mean, and the rubric has a ceiling](2026-09-20-spread-is-not-a-mean-and-the-rubric-has-a-ceiling.md) | The error of a spread obeys a different law from the error of a mean, so the same budget inverts. |
| 2026-09-20 | [Auditing the judge: reliability is not validity](2026-09-20-auditing-the-judge-reliability-is-not-validity.md) | Two independent audits, four overstatements withdrawn in a day, and three controls that had never been run. |
| 2026-09-20 | [Conformance, and turning the work into a shippable artifact](2026-09-20-conformance-and-the-shippable-artifact.md) | The handbook read directly at last, with `config/metrics.yaml` treated as a hypothesis about it. |
| 2026-09-20 | [Why RFantibody cannot run on this GPU, measured](2026-09-20-why-rfantibody-cannot-run-on-blackwell.md) | A vendor's version squeeze reappears one layer down when the hardware changes. |
| 2026-09-21 | [Renting a GPU, and what three independent judges found](2026-09-21-renting-a-gpu-and-what-three-judges-found.md) | $2.82 of the right hardware deleted the entire workaround stack the wrong hardware had forced. |
| 2026-09-22 | [The first test file, and the winner that changed](2026-09-22-the-first-test-file-and-the-winner-that-changed.md) | Tests and git arrive; a config value and a hardcoded constant had already diverged, moving the winner. |
| 2026-09-22 | [Published, withdrawn, re-measured; and the fix that killed the antibody](2026-09-22-published-withdrawn-and-the-fix-that-killed-the-antibody.md) | An under-converged predictor gives a compressed ranking, not a noisy one — a unanimous null was a diagnosis. |
| 2026-09-22 | [Fixing liabilities, and refuting our own advice](2026-09-22-fixing-liabilities-and-refuting-our-own-advice.md) | Under a `min()` aggregator, effort spent anywhere but the current argmin is wasted — refuted for zero GPU folds. |
| 2026-09-22 | [Calibrating the rubric against things that should fail](2026-09-22-calibrating-the-rubric-against-things-that-should-fail.md) | A negative control and a calibration panel: the two experiments owed since week one. |
| 2026-09-23 | [Building a twelve-chapter course, and the three defects that fell out](2026-09-23-building-the-course-and-three-defects-it-found.md) | Writing the record up as teaching found three defects the work itself had not. |
| 2026-09-25 | [Correcting documents at their generator](2026-09-25-correcting-documents-at-their-generator.md) | A packaged file is owned by a generator; hand-editing it makes the correction silently vanish. |
| 2026-09-26 | [Enumerating the retractions, and what a line-oriented grep hid](2026-09-26-enumerating-the-retractions-and-what-grep-hid.md) | Every withdrawal in one register — and `grep` under-reports in hard-wrapped prose. |
| 2026-09-26 | [Publishing a repository, and the five things a clean check cannot see](2026-09-26-publishing-a-repo-and-what-five-reviewers-found.md) | A leak survived a history rewrite, a force-push and a fresh clone; a clone cannot tell deleted from orphaned. |
| 2026-09-28 | [Clearing the backlog, and three guards that could not see](2026-09-28-clearing-the-backlog-and-three-guards-that-could-not-see.md) | Seven open items closed, the decoy control run and passed — and five guards found unable to see their own corpus. |
| 2026-09-29 | [Publishing it, and the sweep that converged](2026-09-29-publishing-it-and-the-sweep-that-converged.md) | Taken public after a verified history rewrite — and three more sweeps for one retracted claim, each finding what the last called clean. |
| 2026-10-03 | [A null with 23% power, and a blocker that was never real](2026-10-03-a-null-with-23-percent-power-and-a-blocker-that-was-never-real.md) | A spending decision rested on a test with a 23% chance of seeing what it looked for — and a rental blocker that was never real. |
| 2026-10-05 | [Teaching the audit period, and the clause that outlived its correction](2026-10-05-teaching-the-audit-period-and-the-clause-that-outlived-its-correction.md) | The course stopped at day 9; a thirteenth chapter teaches the eleven days after it — and a corrected sentence had left a stale clause four words later. |
