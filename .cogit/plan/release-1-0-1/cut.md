---
kind: task
objective: 'Cut 1.0.1 with the release machinery of 1.0.0: version, CHANGELOG, CITATION.cff, tag, PyPI, GitHub Release, Zenodo version DOI'
acceptance:
  - 1.0.1 is on PyPI, published by release.yml through Trusted Publishing
  - the GitHub Release v1.0.1 carries the sdist and wheel, and Zenodo minted its version DOI under the concept DOI 10.5281/zenodo.24539251
  - CITATION.cff names version 1.0.1, its release date and version DOI; the PyPI badge reads 1.0.1
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, CITATION.cff, README.md]
prev: [release, release-1-0-1/sample-match, release-1-0-1/fgsea-statcol, release-1-0-1/fgsea-input, release-1-0-1/run-identity, release-1-0-1/lineage-test, release-1-0-1/count-checks, release-1-0-1/count-checks-readers, release-1-0-1/skill-guidance, release-1-0-1/quickstart-deseq2, release-1-0-1/r-test-skips, release-1-0-1/crate-inputs, release-1-0-1/outlier-entropy-p, release-1-0-1/outlier-shrink-int, release-1-0-1/test-tmp-output, release-1-0-1/tidy-wrapr-checks, release-1-0-1/outlier-shrink-axis]
issue: 228
visited: 424b5e5
---

# Cut 1.0.1

## Implementation plan

- [ ] @developer Bump `version.py` to 1.0.1, date the CHANGELOG's 1.0.1 heading and read its entries against the code: a "Behaviour changes" list first (DETK-0600's two errors, the count checks of DETK-0601), each naming what a 1.0.0 user must change; open the PR <!-- s1 -->
- [ ] @reviewer Review the version-bump PR against the outcome's acceptance: every other 1.0.1 node done, each audit reproduction test present, no command or option added and the schema unchanged, packaging (`uv build`, `twine check`), CI green including the R job <!-- s2 -->
- [ ] @human Accept the PR and say to cut the release <!-- s3 -->
- [ ] @developer Push the `v1.0.1` tag, create the GitHub Release, check PyPI, the attached artifacts and the Zenodo version DOI <!-- s4 -->
- [ ] @developer Update CITATION.cff (version 1.0.1, date-released, the version DOI beside the concept DOI); open the PR <!-- s5 -->
- [ ] @reviewer Review the s5 change and the node's acceptance (PyPI 1.0.1 by release.yml, the Release with sdist and wheel, the DOI) <!-- s6 -->
- [ ] @human Accept <!-- s7 -->

## Notes

Modelled on release/cut. Every `@human` step is Adam's own: the release is not
ticked under DETK-0063's delegation. After `release` (Adam's "1.0.0 is out").
