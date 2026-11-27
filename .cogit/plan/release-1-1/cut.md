---
kind: task
objective: 'Cut 1.1.0 with the release machinery: version, CHANGELOG, CITATION.cff, tag, PyPI, GitHub Release, Zenodo version DOI'
acceptance:
  - 1.1.0 is on PyPI, published by release.yml through Trusted Publishing, and the wheel-ci job passed on it
  - the GitHub Release v1.1.0 carries the sdist and wheel, and Zenodo minted its version DOI
  - CITATION.cff names version 1.1.0, its release date and version DOI; the PyPI badge reads 1.1.0
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, CITATION.cff, README.md]
prev: [release-1-0-1/cut, release-1-1/fgsea-seed, release-1-1/crate-versions, release-1-1/crate-checksums, release-1-1/preflight, release-1-1/wheel-ci]
---

# Cut 1.1.0

## Implementation plan

- [ ] @developer Bump `version.py` to 1.1.0, date the CHANGELOG's 1.1.0 heading and read its entries against the code: the additions listed under 1.1.0; open the PR <!-- s1 -->
- [ ] @reviewer Review the version-bump PR against the outcome's acceptance: every other 1.1.0 node done, every addition additive (DETK-0001), the wheel-ci job in release.yml, packaging (`uv build`, `twine check`), CI green including the R job <!-- s2 -->
- [ ] @human Accept the PR and say to cut the release <!-- s3 -->
- [ ] @developer Push the `v1.1.0` tag, create the GitHub Release, check PyPI, the attached artifacts and the Zenodo version DOI <!-- s4 -->
- [ ] @developer Update CITATION.cff (version 1.1.0, date-released, the version DOI beside the concept DOI); open the PR <!-- s5 -->
- [ ] @reviewer Review the s5 change and the node's acceptance (PyPI 1.1.0 by release.yml, the Release with sdist and wheel, the DOI) <!-- s6 -->
- [ ] @human Accept <!-- s7 -->

## Notes

Modelled on release/cut and release-1-0-1/cut. Every `@human` step is Adam's own.
