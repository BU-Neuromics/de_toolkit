---
kind: step
time: 2026-11-25T18:52:43Z
by: DETK/developer
node: release/cut
step: s4
branch: node/168-cut
verdict: done
commits: []
decisions: []
---

# Done: Push the `v1.0.0` tag, create the GitHub Release, check PyPI, the attached artifacts and the DOI

## Summary

v1.0.0 tagged (annotated) on merge commit 66628a8 and pushed; GitHub Release v1.0.0 published with the CHANGELOG 1.0.0 notes and the wheel and sdist attached by release.yml (run 45664275247). PyPI publish succeeded on attempt 2 after Adam fixed the Trusted Publisher; PyPI serves 1.0.0 (wheel + sdist, requires-python >=3.11). pip install de_toolkit==1.0.0 in a clean venv: de_toolkit 1.0.0, detk --version 1.0.0, every entry point's --help exits 0. Zenodo minted concept DOI 10.5281/zenodo.24539251 (version DOI 10.5281/zenodo.24539252).

## Artifacts

## Findings

## Questions
