---
kind: step
time: 2026-11-28T01:26:08Z
by: DETK/reviewer
node: release-1-0-1/outlier-entropy-p
step: s2
branch: review/outlier-entropy-p
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction fails on v1.0.0 as stated and passes here; DETK-0860 default 0.05 in effect and documented; -p given unchanged (DETK-0200); scope clean; CI green including R.

## Artifacts

## Findings

- Reproduction: the two new tests (test_entropy_cli_without_percentile, test_entropy_help_states_percentile_default) copied onto a v1.0.0 worktree fail with 'UsageError: argument -p/--percentile: invalid float value: None' (the CLI's exit 2); both pass at 3cc8556.
- AC1: entropy without -p runs (rc 0 on tests/de/R_check_names_counts.csv) and gives the same output file, column entropy_p0_05 and module JSON params/properties as -p 0.05 (asserted by the test). --help, docs/tools/outlier.md and skills/detk/references/commands.md say '(default: 0.05)'. The CLI options table records the default.
- AC2: -p 0.05 rc 0; -p 5, -p 0, -p x rc 2 (DETK-0200 tests pass); no option added; shrink's -p/--p-max untouched; CHANGELOG 1.0.1 Fixed entry cites #222 and DETK-0860.
- DETK-0940: rerunning python -m de_toolkit.completions._generate leaves detk.zsh/.bash/.tcsh unchanged, so the committed zsh completion is current.
- Scope: changed files are outlier.py, detk.zsh, tests/outlier, tests/cli/cli_tables.py, the docs page, the skill reference, CHANGELOG and .cogit records. Nothing outside the scope changed.
- Checks: full local suite 2844 passed, 160 skipped (R not installed). PR #224 CI all green, including 'test with R (bioconda)' (28m), docs build (strict), ruff, py3.11-3.13 and coverage.
- No changes asked; no decision needed.

## Questions
