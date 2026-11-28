---
kind: step
time: 2026-11-27T23:33:10Z
by: DETK/developer
node: release-1-0-1/test-tmp-output
step: s1
branch: node/210-test-tmp-output
verdict: done
commits: [94ef9d8]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Reproduced on v1.0.0 with DESeq2: pytest tests/de/test_de.py::test_R_check_names_nonsense leaves tmp_output/ (counts.csv, counts_out.csv, meta_in/out.csv, params_in/out.json, script.R, stdout, stderr) in the cwd. Fix: routput_dir and -o go under tmp_path. Guard: session-scoped autouse fixture repository_left_clean in tests/conftest.py (git status --porcelain --untracked-files=all before/after; fails naming new files; off outside a git work tree); shown to fail on v1.0.0 (ERROR at teardown listing the 9 files). tests/ci/test_repository_clean.py tests the helper. CHANGELOG 1.0.1 Tests entry. Full suite with R + coverage locally: 2818 passed, 23 skipped, tree clean. README (Development) not edited: outside scope.

## Artifacts

## Findings

## Questions
