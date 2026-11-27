---
kind: task
objective: 'Cut 1.0.1 with the release machinery of 1.0.0: version, CHANGELOG, CITATION.cff, tag, PyPI, GitHub Release, Zenodo version DOI'
acceptance:
  - 1.0.1 is on PyPI, published by release.yml through Trusted Publishing
  - the GitHub Release v1.0.1 carries the sdist and wheel, and Zenodo minted its version DOI under the concept DOI 10.5281/zenodo.24539251
  - CITATION.cff names version 1.0.1, its release date and version DOI; the PyPI badge reads 1.0.1
scope: [de_toolkit/version.py, pyproject.toml, CHANGELOG, CITATION.cff, README.md]
---

# Cut 1.0.1

## Implementation plan

## Notes
