---
kind: step
time: 2026-11-22T18:15:51Z
by: DETK/reviewer
node: release/example-paths
step: s2
branch: review/example-paths
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: open docs/example/detk_report.html and the crate, grep them for absolute paths, run the new test against the old files from 61bf890, and confirm the R job ran the tutorial

## Summary

Changes asked at fd81814, for one reason: CodeQL #11 is real. .github/workflows/example.yml needs `permissions: contents: read`. CodeQL #12 (py/bad-tag-filter, test_example_paths.py:34) is a false positive: the regex only picks out vendored code for the scan to skip, and it fails closed. Dismiss it as "used in tests"; no code change. Everything else passes:
- docs/example/ matches the docs-example artifact of "Regenerate example" run 45051592545 byte for byte (`diff -r` is empty). The run was a workflow_dispatch at 8e249d4, whose base d201819 includes the merges of report-paths #134, tutorial-airway #117, outlier-entropy #125 and cli-messages #127. 9fb22a6 changes only the workflow's trigger.
- Relative paths (report-paths, DETK-0280): all 12 modules record workdir `..` and argv[0] as the bare command name (detk-stats, detk-outlier, ...). The crate sits beside the report, and its File @ids are `../counts.csv` and so on. A grep finds no /home/, /Users/, /tmp/, /private/, /root/ or drive path. The only `file://` and `o:/` matches are inside the vendored Vega `<script>`.
- Outlier card (DETK-0200): `-p 0.05` gives threshold 1.332 with 925 flagged; the old files had 0.849 and 13. num_kept (24706) counts every feature in both, so it stays the same.
- New test: 21 passed on the regenerated files. Against the 61bf890 files it fails with 48 findings (24 workdir/argv fields plus the raw-text matches), and with 48 against d201819's files.
- docs/example.md links both files. The pins comment names the tutorial's data step. The CHANGELOG entry is under Fixed.
- CI on fd81814: everything is green except CodeQL. "test with R (bioconda)" passed (2633 passed, 23 skipped), with DETK_TUTORIALS_REQUIRE_ALL=1. tests/tutorials/test_airway.py ran 4 of 4, and test_example_paths ran there too. The docs build (strict) and ruff pass.

## Artifacts

## Findings

1. **.github/workflows/example.yml, CodeQL #11 (actions/missing-workflow-permissions): change asked.** This is a real alert, not a false positive. The new workflow does not declare permissions, so its GITHUB_TOKEN gets the repository's default scopes. The job only checks the repository out, runs the tutorial and uploads an artifact; upload-artifact@v4 uses the runtime token, not GITHUB_TOKEN. Add a top-level `permissions: {contents: read}` block (or `permissions:` / `contents: read` under `on:`). This does not affect the generated files, so docs/example/ does not need regenerating.
2. **tests/report/test_example_paths.py:34, CodeQL #12 (py/bad-tag-filter): false positive; dismiss it as "used in tests".** `CODE` is not an HTML sanitizer. It picks out the bodies of the report's bare inline `<script>` tags so the raw-text scan can skip vendored Vega code. The regex fails closed: a `<SCRIPT>`, a `<script ...>` with attributes or a `</script >` is not matched, so its body is still scanned, which makes the check stricter. It reads only a report detk itself generates, and nothing untrusted flows through it. Adding `re.I` or widening the pattern would make the scan skip more, not less. No code change is asked. CodeQL stays red until the alert is dismissed, so the developer, or Adam, should dismiss #12 with the reason "used in tests: selects vendored code to skip; fails closed".

Everything else meets the acceptance criteria (see the summary). There are no other findings.

## Questions
