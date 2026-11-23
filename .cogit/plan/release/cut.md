---
kind: task
objective: 'Cut 1.0.0 with the release machinery of #35: version, CHANGELOG, tag, PyPI, GitHub Release, DOI (tracks #20)'
acceptance:
  - 1.0.0 is on PyPI, published by release.yml through Trusted Publishing
  - the GitHub Release v1.0.0 carries the sdist and wheel, and Zenodo minted a DOI
  - the README shows the concept-DOI badge and the PyPI badge reads 1.0.0
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, README.md]
prev: [DETK-0001, release/tpm-cpm, release/annotate, release/gather, release/agent-skills, release/fpkm, release/escape-json, release/padded-ids, release/single-column, release/deps, release/view-text, release/skill-update, release/quickstart-figure, release/r-ids, release/ci-lock, release/cli-pin, release/formula-pin, release/cli-migrate, release/formula-migrate, release/cli-docs, release/statsmodels-test, release/formula-rename, release/cli-gaps, release/size-factors, release/record, release/r-design-names, release/dep-guards, release/help-options, release/tidy-output, release/parse-errors, release/strict-json, release/outlier-entropy, release/cli-messages, release/record-help, release/report-paths, release/example-paths, release/short-header, release/recipe-notes, release/ci-jsdom, release/ragged-sheet, release/jsdom-summary, release/crate-stdout, release/record-program]
---

# Cut 1.0.0

## Implementation plan

- [ ] @human Confirm PyPI Trusted Publishing (environment `pypi`) and the Zenodo integration are set up (the account steps on #20) <!-- s1 -->
- [ ] @developer Bump `version.py` to 1.0.0, set `Development Status :: 5 - Production/Stable`, date the CHANGELOG heading, and read the 1.0 entries against the released CLI: the option-names entry (about line 109) still lists `detk-filter --column-data` and `detk-stats --column-data` among renamed metavars, which 1.0 removes (DETK-0030); drop them there, as the entry on their removal already says; open the PR <!-- s2 -->
- [ ] @human Answer DETK-0002 (deferred by Adam on 2026-11-20): leave the PCA_tester data in history, or rewrite it out before the tag <!-- s7 -->
- [ ] @human Accept the PR and say to cut the release <!-- s3 -->
- [ ] @developer Push the `v1.0.0` tag, create the GitHub Release, check PyPI, the attached artifacts and the DOI <!-- s4 -->
- [ ] @developer Add the concept-DOI badge to the README <!-- s5 -->
- [ ] @human Accept <!-- s6 -->

## Notes

The machinery is merged (#35, `release.yml`); the sequence is on #20.
Step s1 is account work only Adam can do (PyPI, Zenodo), written as a confirmation.
DETK-0002 was in `prev:` until 2026-11-20, which kept this node waiting on a
question Adam has deferred; it is now step s7, his to answer with the go-ahead
to tag (DETK-0063 item 6), so the work before the cut is not held by it. A
rewrite (DETK-0002 Option B) changes every later commit hash and must come
before the tag. Every `@human` step here is Adam's own: the release is not
ticked under the delegation of DETK-0063.
