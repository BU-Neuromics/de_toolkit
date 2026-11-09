---
kind: task
objective: 'Cut 1.0.0 with the release machinery of #35: version, CHANGELOG, tag, PyPI, GitHub Release, DOI (tracks #20)'
acceptance:
  - 1.0.0 is on PyPI, published by release.yml through Trusted Publishing
  - the GitHub Release v1.0.0 carries the sdist and wheel, and Zenodo minted a DOI
  - the README shows the concept-DOI badge and the PyPI badge reads 1.0.0
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, README.md]
prev: [DETK-0001, DETK-0002, release/tpm-cpm, release/annotate, release/gather, release/agent-skills, release/fpkm]
---

# Cut 1.0.0

## Implementation plan

- [ ] @human Confirm PyPI Trusted Publishing (environment `pypi`) and the Zenodo integration are set up (the account steps on #20) <!-- s1 -->
- [ ] @developer Bump `version.py` to 1.0.0, set `Development Status :: 5 - Production/Stable`, date the CHANGELOG heading; open the PR <!-- s2 -->
- [ ] @human Accept the PR and say to cut the release <!-- s3 -->
- [ ] @developer Push the `v1.0.0` tag, create the GitHub Release, check PyPI, the attached artifacts and the DOI <!-- s4 -->
- [ ] @developer Add the concept-DOI badge to the README <!-- s5 -->
- [ ] @human Accept <!-- s6 -->

## Notes

The machinery is merged (#35, `release.yml`); the sequence is on #20.
Step s1 is account work only Adam can do (PyPI, Zenodo), written as a confirmation.
