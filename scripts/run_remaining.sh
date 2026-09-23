#!/usr/bin/env bash
# All remaining fold stages, resumable. Every stage keys resume on ARTEFACTS
# (locksmith.fold.fold_is_complete), so re-running costs only unfinished work.
#
# RUN THIS UNDER `systemd-run --user`, NOT `nohup setsid`.
# 2026-09-23 01:06:59: systemd-oomd killed 27 processes in the terminal's
# vte-spawn-*.scope under memory pressure, taking the fold chain with it at 31/40.
# `setsid` detaches a process from its TERMINAL but leaves it in the terminal's
# CGROUP, and systemd-oomd kills by cgroup. A transient systemd unit gets its own
# cgroup under user@.service and survives the terminal dying.
set -u
cd "/home/rrobin711/Obsidian Personal/7- Projects/locksmith-antibody-hackathon" || exit 1
LOG=runs/calibration/runall.log
{
  echo "=== RESTART $(date -Is) (after systemd-oomd kill at 01:06:59) ==="
  echo "--- stage: calibration panel ---";   uv run python scripts/87_calibration_fold.py
  echo "--- stage: test articles ---";       uv run python scripts/90_test_articles.py
  echo "--- stage: negctrl follow-up ---";   uv run python scripts/92_negctrl_full_epitope.py
  echo "--- stage: msa register test ---";   uv run python scripts/94_msa_register.py
  echo "=== ALL EXPERIMENTS DONE $(date -Is) ==="
} >> "$LOG" 2>&1
