---
kind: task
objective: 'Cut 1.1.0 with the release machinery: version, CHANGELOG, CITATION.cff, tag, PyPI, GitHub Release, Zenodo version DOI'
acceptance:
  - 1.1.0 is on PyPI, published by release.yml through Trusted Publishing, and the wheel-ci job passed on it
  - the GitHub Release v1.1.0 carries the sdist and wheel, and Zenodo minted its version DOI
  - CITATION.cff names version 1.1.0, its release date and version DOI; the PyPI badge reads 1.1.0
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, CITATION.cff, README.md]
---

# Cut 1.1.0

## Implementation plan

## Notes
