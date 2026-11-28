---
kind: step
time: 2026-11-28T01:34:04Z
by: DETK/reviewer
node: release-1-0-1/test-tmp-output
step: s2
branch: review/test-tmp-output
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Changes asked at 2d6786f: the fix and the reproduction hold and CI is 12/12 green (test with R (bioconda) ran test_R_check_names_nonsense with the guard on), but the repository_left_clean guard has two edge cases to close before merge: it watches an enclosing repository when the tree is not its own work tree, and it crashes with TypeError if git fails at teardown.

## Artifacts

## Findings

1. Acceptance 1 holds: test_R_check_names_nonsense now writes routput_dir and -o under tmp_path (tests/de/test_de.py). In CI, test with R (bioconda) ran it (not in the -rs skip list; 2982 passed, 23 skipped) and the guard passed, so nothing was left. I could not run the v1.0.0 reproduction myself (no R here); the developer's journal reports it failing on v1.0.0 with the 9 tmp_output files listed. 2. Acceptance 2 holds in a scratch clone: a test that writes leak_from_cwd.txt into the cwd makes the session fail with 'the test suite left untracked files in the repository (<root>); write them under tmp_path instead:' and the file name; ignored files (.venv, .coverage, *.pyc, .pytest_cache) and modified tracked files are not counted; CI's COVERAGE_FILE=.coverage.py3.x/.coverage.r are written after session teardown, so they are not counted either. CHANGELOG 1.0.1 has the Tests entry. 3. Change asked (tests/conftest.py, untracked_files): when root is not a git work tree's top level but sits inside another repository (an unpacked sdist or a copy inside some other checkout), git -C root status succeeds for the enclosing repository. The guard is then not off as CHANGELOG says. It runs status -uall over the whole enclosing repository, and anything written anywhere in that repository during the run fails the session. Paths are also reported relative to the enclosing root but labelled with <root>: I reproduced a file at outer/someone_else.txt reported as '(.../outer/sub) ... someone_else.txt'. Fix: return None unless 'git -C root rev-parse --show-toplevel' resolves to root (compare realpaths), plus a test like test_outside_a_git_work_tree_the_guard_is_off with tmp_path nested in the fixture repo. 4. Change asked (tests/conftest.py, repository_left_clean): if the teardown call to untracked_files returns None (git fails or vanishes mid-session), 'untracked_files(root) - before' raises TypeError, an unexplained teardown error. Treat a None after-snapshot as guard off (or fail with a clear message). 5. Optional: pytest reports the failure as 'ERROR at teardown of <last test>', which may not be the culprit. A clause in the message such as 'reported on the last test; any test may have written them' would save a hunt. 6. Parallel pytest: pytest-xdist is not a dependency and CI does not use it. Under xdist each worker runs its own session fixture, so a file one worker's test writes and removes could be seen by another worker's after-snapshot. A test that does that is already wrong, so this is not a false failure in practice; no change asked. 7. Scope: tests/conftest.py, tests/ci/test_repository_clean.py, tests/de/test_de.py, CHANGELOG and .cogit records only; within scope. 8. README Development: one sentence would help contributors and is outside this node's scope, for example 'A test run that leaves a new untracked file in the repository fails (tests/conftest.py); write test output under tmp_path.' It can be added after the 'Tests that require R' paragraph, in a follow-up or by widening scope; I'm not proposing a decision. No decisions recorded.

## Questions
