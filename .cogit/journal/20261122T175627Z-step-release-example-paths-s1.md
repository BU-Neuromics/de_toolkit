---
kind: step
time: 2026-11-22T17:56:27Z
by: DETK/developer
node: release/example-paths
step: s1
branch: node/141-example-paths
verdict: done
commits: [a27eed9, abc49c9, 3ced79b, 8e249d4, 9fb22a6, e22f1c9]
decisions: []
---

# Done: Regenerate docs/example/ from the airway tutorial's run on main, add the test that no absolute path appears in it (shown failing on the old files), fix the stale prepare_data.R comment in test_formula_pins.py; CHANGELOG; open the PR

## Summary

Done: docs/example/ regenerated through CI (Adam, 2026-11-22): new workflow_dispatch workflow .github/workflows/example.yml (test-r's bioconda env, runs examples/airway/run.sh, checks paths, uploads docs-example); run 45051592545 on this branch, artifact committed: workdir '..', argv[0] the command name, crate File @ids ../ (DETK-0280), outlier card 925 flagged (DETK-0200). New tests/report/test_example_paths.py walks the embedded module JSON and the crate for absolute or file:// path fields and scans raw text for /home/, /Users/, /tmp/, /private/, /root/, drive paths and file://; 48 findings on the 61bf890 files, fails on d201819's, passes on the regenerated ones. test_formula_pins.py airway comment names the tutorial's data step. CHANGELOG under Fixed. Scope extended with new:.github/workflows/example.yml citing Adam's decision. Decisions within the node: raw-text scan skips inline code <script> bodies (vendored Vega holds file:// and o:/[); workflow is dispatch-only. ruff, full pytest, mkdocs --strict pass. PR #143.

## Artifacts

## Findings

## Questions
