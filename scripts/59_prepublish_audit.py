#!/usr/bin/env python
"""Pre-publication audit: does this repository leak anything, ANYWHERE it can be read?

PROMOTED FROM LEARNINGS.md 2026-09-26. The mechanism IS the memory; the prose is deleted.
Two entries became this script, and both were about the same defect -- ASKING THE WRONG
CORPUS -- so the script exists to make the corpus explicit.

=============================================================================
INSTANCE 1: a file-reading scan answers for the WORKING TREE.
=============================================================================
Before publishing this repo, a sweep grepped all 354 tracked files for third-party email
addresses, credentials, cloud keys and a copyrighted handbook, and reported CLEAN on all
four. Both the handbook (712 KB PDF) and three organisers' email addresses were still IN
THE REPOSITORY -- reachable from 77 earlier commits -- and were pushed.

Both removals had been ordinary commits: `git rm --cached` for the handbook, a text edit
for the emails. That changes what HEAD contains and NOTHING about what the repository
contains. Measured before fixing:
    git log --all --diff-filter=A --name-only -- 'source/...handbook.*'  -> 2 files, 4 commits
    git log -p --all -- README.md | grep -c 'locksmithbio\\.org|diagnobacs\\.com'  -> 12

  *Removing a file from a repo and removing it from a repo's HISTORY are different
   operations, and every tool that greps files reports the first as if it were the second.*

=============================================================================
INSTANCE 2: a fresh clone answers for REACHABILITY, not for what the remote holds.
=============================================================================
After `git filter-repo` + `git push --force`, a fresh clone of the remote returned five
clean checks and it was reported verified. THREE HOURS LATER the old tip still answered:
    gh api .../commits/3a0cc1846fd3681011ebb9612afb51382ecab331         -> HTTP 200
    gh api ".../contents/README.md?ref=893002240cd3bcec030a585c302e4ce8891d6815"
                                                                        -> 3 email addresses
    gh api ".../git/trees/8930022...?recursive=1"  -> handbook.pdf, 727,284 bytes
Control: 04cbac2eed78cb8bfb23bfb9413a1a61ab6cbb23, never pushed -> HTTP 422.

`git clone` performs a REACHABILITY WALK: it fetches only objects the refs can reach. So it
returns identical output whether the objects were deleted or merely orphaned. `git log
--all`, `git rev-list --all` and `git cat-file --batch-all-objects` were clean too, because
`filter-repo` DELETES THE `origin` REMOTE, resetting the remote-tracking reflog and erasing
the local evidence that a pre-rewrite push ever happened.

Fix: DELETE the repository (cheap only while young -- 0 forks). A force-push does not
remove the objects; GitHub retains unreachable objects and serves them by SHA.

=============================================================================
INSTANCE 3: grep is line-oriented; hard-wrapped prose is not.
=============================================================================
`grep -rn "0% false-positive"` returned 2 hits where there were 3 -- two in the same file.
The missed one wrapped as `with a 0%\\nfalse-positive rate`, so no single line contained it.
It fails QUIETLY: two hits looks like a complete answer, and the miss rate scales with
phrase length x wrap hardness, i.e. it is worst on exactly the long quotable claims you are
sweeping for. Every pattern here is therefore matched with `\\s+` for inter-word space over
the whole file text, never line by line.

Related, same syntax, different tool: `[[a|b]]` split across a newline is what
`.claude/hooks/wikilink-guard.sh` exists for, and the first draft of the retraction
register contained exactly that.

=============================================================================
USAGE
=============================================================================
    uv run python scripts/59_prepublish_audit.py                 # local checks only
    uv run python scripts/59_prepublish_audit.py --remote OWNER/REPO   # + orphan probe

Exit 0 = clean. Exit 1 = at least one finding. Never "fixes" anything.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Patterns are NEWLINE-TOLERANT by construction: every literal space becomes \s+.
def _nl(pattern_words: str) -> str:
    return r"\s+".join(re.escape(w) for w in pattern_words.split())


SECRET_PATTERNS: dict[str, str] = {
    "AWS access key":      r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}",
    "GitHub token":        r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}",
    "OpenAI/Anthropic key": r"sk-(?:ant-)?[A-Za-z0-9_\-]{20,}",
    "HuggingFace token":   r"\bhf_[A-Za-z0-9]{20,}",
    "Google API key":      r"AIza[0-9A-Za-z_\-]{35}",
    "Slack token":         r"xox[abprs]-[A-Za-z0-9-]{10,}",
    "private key block":   r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "jupyter token value": r"token=[0-9a-f]{32,}",
}

TEXT_SUFFIXES = {".md", ".py", ".txt", ".toml", ".yaml", ".yml", ".json", ".cfg",
                 ".ini", ".sh", ".csv", ".fasta"}


def _run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout


def _tracked() -> list[str]:
    return [f for f in _run("git", "ls-files").splitlines() if f]


def _all_blob_texts():
    """Yield (sha, text) for every blob in the object database, reachable or not.

    This is the corpus `git grep` does NOT search. A blob that only an old commit points
    at is invisible to every file-reading tool and fully present here.
    """
    listing = _run("git", "cat-file", "--batch-all-objects", "--batch-check=%(objecttype) %(objectname)")
    shas = [ln.split()[1] for ln in listing.splitlines() if ln.startswith("blob ")]
    for sha in shas:
        raw = subprocess.run(["git", "cat-file", "blob", sha],
                             capture_output=True).stdout
        if b"\x00" in raw[:1024]:          # binary; skip text matching
            continue
        yield sha, raw.decode("utf-8", errors="replace")


def check_history_paths(banned_globs: list[str]) -> list[str]:
    """Was a banned path EVER added, in any commit? (not: is it in HEAD)"""
    out = []
    for g in banned_globs:
        hits = _run("git", "log", "--all", "--diff-filter=A", "--name-only",
                    "--pretty=format:", "--", g).split()
        for h in sorted(set(hits)):
            out.append(f"path ever committed: {h}  (matches banned glob {g!r})")
    return out


def check_blob_contents(extra_patterns: dict[str, str]) -> list[str]:
    """Search EVERY blob, reachable or not, newline-tolerantly."""
    pats = {**SECRET_PATTERNS, **extra_patterns}
    compiled = {k: re.compile(v, re.I) for k, v in pats.items()}
    out, seen = [], set()
    for sha, text in _all_blob_texts():
        for name, rx in compiled.items():
            m = rx.search(text)
            if m and (name, m.group(0)[:40]) not in seen:
                seen.add((name, m.group(0)[:40]))
                out.append(f"{name} in blob {sha[:10]}: {m.group(0)[:60]!r}")
    return out


def check_case_collisions() -> list[str]:
    """Two tracked paths differing only in case make every macOS/Windows clone dirty."""
    seen: dict[str, str] = {}
    out = []
    for f in _tracked():
        k = f.lower()
        if k in seen:
            out.append(f"case collision: {seen[k]} vs {f}")
        seen[k] = f
    return out


def check_authors(allowed_email_substr: str | None) -> list[str]:
    if not allowed_email_substr:
        return []
    out = []
    for line in set(_run("git", "log", "--all", "--format=%ae|%ce").splitlines()):
        for addr in line.split("|"):
            if addr and allowed_email_substr not in addr:
                out.append(f"commit identity not allowed: {addr}")
    return sorted(set(out))


def check_remote_orphans(remote: str) -> list[str]:
    """Ask the REMOTE for pre-rewrite SHAs. A clone cannot answer this (see INSTANCE 2).

    Old SHAs come from .git/filter-repo/commit-map, which filter-repo writes and which is
    the highest-value file in a repo about to go public.
    """
    cmap = Path(".git/filter-repo/commit-map")
    if not cmap.exists():
        return ["NOTE: no .git/filter-repo/commit-map -- no rewrite recorded locally, so "
                "orphan probing has no SHAs to test. If history WAS rewritten by other "
                "means, collect the old SHAs yourself: a clone cannot find them."]
    olds = []
    for ln in cmap.read_text().splitlines()[1:]:
        parts = ln.split()
        if len(parts) == 2 and parts[0] != parts[1] and not set(parts[1]) == {"0"}:
            olds.append(parts[0])
    out = []
    probe = olds[:8]
    for sha in probe:
        r = subprocess.run(["gh", "api", f"repos/{remote}/commits/{sha}"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            out.append(f"ORPHAN RETAINED on remote: {sha[:12]} still returns HTTP 200 -- "
                       f"a force-push did NOT remove it. Delete and recreate the repo.")
    if probe and not out:
        # negative control: a SHA that cannot exist must 404/422, else the probe is useless
        fake = "0" * 39 + "1"
        r = subprocess.run(["gh", "api", f"repos/{remote}/commits/{fake}"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            out.append("PROBE INVALID: a nonexistent SHA returned success, so the 404s "
                       "above prove nothing. Do not trust this check.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--remote", help="OWNER/REPO to probe for retained orphaned commits")
    ap.add_argument("--banned-path", action="append", default=[],
                    help="glob that must never appear in ANY commit (repeatable)")
    ap.add_argument("--banned-text", action="append", default=[],
                    help="phrase that must not appear in any blob; matched "
                         "newline-tolerantly (repeatable)")
    ap.add_argument("--author-email-contains", default=None,
                    help="every commit author/committer address must contain this")
    a = ap.parse_args()

    extra = {f"banned text {p!r}": _nl(p) for p in a.banned_text}
    findings: list[str] = []
    findings += check_history_paths(a.banned_path)
    findings += check_blob_contents(extra)
    findings += check_case_collisions()
    findings += check_authors(a.author_email_contains)
    if a.remote:
        findings += check_remote_orphans(a.remote)

    notes = [f for f in findings if f.startswith("NOTE:")]
    real = [f for f in findings if not f.startswith("NOTE:")]
    for n in notes:
        print(f"  {n}")
    if real:
        print(f"\nPRE-PUBLICATION AUDIT: {len(real)} finding(s)\n")
        for f in real:
            print(f"  - {f}")
        print("\nNothing was changed. Fix, then re-run.")
        return 1
    print("\nPRE-PUBLICATION AUDIT: clean "
          "(history paths, all blobs incl. unreachable, case collisions, authors"
          + (", remote orphans" if a.remote else "") + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
