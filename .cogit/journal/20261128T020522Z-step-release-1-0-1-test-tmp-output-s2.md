---
kind: step
time: 2026-11-28T02:05:22Z
by: DETK/reviewer
node: release-1-0-1/test-tmp-output
step: s2
branch: review/test-tmp-output
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved at 3899dd0: both changes asked in the first review are fixed with tests, the optional message clause is in, and the README sentence is in (scope widened in e825feb under the delegation); CI 12/12 green on 3899dd0, including test with R (bioconda).

## Artifacts

## Findings

1. Enclosing repository fixed: untracked_files returns None unless realpath(git rev-parse --show-toplevel) equals realpath(root). test_inside_another_repository_the_guard_is_off covers it. My repro (the tree copied into outer/sub of a fresh repo, plus a test writing outer/someone_else.txt) now passes with the guard off: 22 passed, no false failure. 2. git failing at the end fixed: files_left_behind returns [] with a UserWarning ('git status failed at the end of the test run ...; the check ... is off') instead of a TypeError. test_git_failing_at_the_end_turns_the_guard_off_with_a_warning covers it (PATH emptied, so OSError gives None). 3. The guard still bites. In a clean scratch clone at 3899dd0, a test writing leak_from_cwd.txt into the cwd fails the session ('ERROR at teardown of <last test>'), naming the file. The message now adds 'This is reported at the teardown of the last test run; any test may have written them'. Files untracked before the run are still not counted (test_a_new_file_is_left_behind_and_one_there_before_is_not, and my run with a pre-existing file). 4. README Development has one sentence after the R paragraph: 'A test run that leaves a new untracked file in the repository fails (tests/conftest.py); write test output under tmp_path.' README.md was added to the node scope in e825feb (DETK-0063 delegation via the driver), so the change is in scope. 5. CHANGELOG 1.0.1 Tests entry updated: off unless the project root is a work tree's top level (sdist, copy inside another repository), warns if git fails at the end, and the README says so. It matches the code. 6. Scope: tests/conftest.py, tests/ci/test_repository_clean.py, tests/de/test_de.py, CHANGELOG, README.md and .cogit records, all within the node's (widened) scope. 7. Checks: ruff check and format clean on tests/. CI on 3899dd0: 12/12 pass, including test with R (bioconda) (27m03s) and combined coverage. Acceptance 1 (the R test writes under tmp_path, nothing left) is unchanged from the first review and passes in the R job with the guard on. No decisions needed.

## Questions
